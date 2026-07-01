"""Paper-trade engine (JSON state). Long-only, equal-weight, no leverage.

Execution discipline (no lookahead):
  signal is computed on a CLOSED bar  ->  order goes PENDING  ->  filled at the
  NEXT bar's OPEN. The same primitives drive the live loop (process_cycle) and
  the historical replay (scripts/backtest.py).

Each cycle: (1) fill prior pending at next-bar-open, (2) mark-to-market,
(3) decide new orders — EXITS first (sell/stop/invalidation), THEN entries.
Costs: round_trip_cost_pct split half on entry, half on exit.
Per-trade we store the entry rules so Phase E can attribute P&L per rule.
"""
from __future__ import annotations
import json
import math
from datetime import datetime

from . import paths

# execution defaults (mirrors config.py; used if config omits the block)
EXEC_DEFAULTS = {
    "entry_kinds": ["entry"], "entry_min_rules": 3, "downtrend_blocks_buys": True,
    "exit_on_opposing_min": 2, "min_hold_days": 3,
    "exit_mode": "ema18",        # ema18 | chandelier | rule_only (ema18 best in/out-of-sample)
    "chandelier_atr": 3.0,       # ATR multiple below the running peak
    "stop_loss_pct": 0.08,
}


def _exec(cfg):
    return {**EXEC_DEFAULTS, **cfg.get("execution", {})}


def _days(a_iso, b_iso):
    try:
        return (datetime.fromisoformat(str(a_iso)) - datetime.fromisoformat(str(b_iso))).days
    except Exception:
        return 999


def new_state(cfg: dict) -> dict:
    return {
        "starting_capital": cfg["starting_capital"],
        "cash": float(cfg["starting_capital"]),
        "realized_pnl": 0.0,
        "positions": {},     # sym -> position dict
        "pending": [],       # list of order dicts
        "trade_log": [],     # closed round-trips
        "last_cycle": None,
    }


def load_state(cfg: dict) -> dict:
    if paths.PORTFOLIO_FILE.exists():
        return json.loads(paths.PORTFOLIO_FILE.read_text(encoding="utf-8"))
    return new_state(cfg)


def save_state(state: dict) -> None:
    paths.ensure_dirs()
    paths.PORTFOLIO_FILE.write_text(json.dumps(state, indent=2, default=str),
                                    encoding="utf-8")


def _half_cost(cfg: dict) -> float:
    return float(cfg["round_trip_cost_pct"]) / 100.0 / 2.0


def alloc_per_slot(cfg: dict) -> float:
    return float(cfg["starting_capital"]) / int(cfg["max_positions"])


# ---------------- order execution ----------------
def fill_buy(state, order, price, fill_ts, cfg, log=None):
    hc = _half_cost(cfg)
    alloc = alloc_per_slot(cfg)
    shares = math.floor(alloc / price) if price > 0 else 0
    if shares <= 0:
        return None
    value = shares * price
    cost = value * hc
    if state["cash"] < value + cost:                      # no leverage
        if log:
            log.info("Skip BUY %s: insufficient cash (need %.0f, have %.0f)",
                     order["sym"], value + cost, state["cash"])
        return None
    state["cash"] -= value + cost
    state["positions"][order["sym"]] = {
        "sym": order["sym"], "entry_ts": str(fill_ts), "entry_price": price,
        "shares": shares, "entry_value": value, "entry_cost": cost,
        "entry_rules": order.get("reason", []), "entry_regime": order.get("regime"),
        "stop": price * (1 - _exec(cfg)["stop_loss_pct"]),
        "peak": price,
    }
    return {"event": "BUY", "sym": order["sym"], "ts": str(fill_ts),
            "price": price, "shares": shares}


def fill_sell(state, order, price, fill_ts, cfg, log=None):
    pos = state["positions"].get(order["sym"])
    if not pos:
        return None
    hc = _half_cost(cfg)
    shares = pos["shares"]
    value = shares * price
    cost = value * hc
    state["cash"] += value - cost
    net = (value - cost) - (pos["entry_value"] + pos["entry_cost"])
    state["realized_pnl"] += net
    trade = {
        "sym": order["sym"], "side": "long",
        "entry_ts": pos["entry_ts"], "exit_ts": str(fill_ts),
        "entry_price": pos["entry_price"], "exit_price": price, "shares": shares,
        "gross_pnl": round((price - pos["entry_price"]) * shares, 2),
        "costs": round(pos["entry_cost"] + cost, 2),
        "net_pnl": round(net, 2),
        "ret_pct": round((price / pos["entry_price"] - 1) * 100, 2),
        "entry_rules": pos["entry_rules"], "exit_reason": order.get("reason", []),
        "hold_days": order.get("hold_days"),
    }
    state["trade_log"].append(trade)
    del state["positions"][order["sym"]]
    return {"event": "SELL", "sym": order["sym"], "ts": str(fill_ts),
            "price": price, "net_pnl": trade["net_pnl"]}


def fill_pending(state, price_after, cfg, log=None) -> list:
    """price_after(sym, signal_ts) -> (fill_ts, open_price) or None (no bar yet)."""
    events, still = [], []
    for order in state["pending"]:
        res = price_after(order["sym"], order["signal_ts"])
        if res is None:
            still.append(order)            # next bar hasn't printed yet
            continue
        fill_ts, price = res
        ev = (fill_sell if order["side"] == "sell" else fill_buy)(
            state, order, float(price), fill_ts, cfg, log)
        if ev:
            events.append(ev)
    state["pending"] = still
    return events


# ---------------- decision logic ----------------
def _buy_votes(sig, kinds):
    return [f for f in sig["fired"] if f.get("kind") in kinds and f["signal"] == "buy"]


def _sell_votes(sig):
    # opposing pressure: sells from entry- or exit-kind rules (not filters/levels)
    return [f for f in sig["fired"]
            if f["signal"] == "sell" and f.get("kind") in ("entry", "exit")]


def decide_orders(state, signals: dict, market: dict, cfg: dict) -> list:
    """EXITS first, then entries. Entries require >= entry_min_rules genuine
    entry-rule agreement and a permissive regime; exits need a real reason
    (stop / trailing-EMA break / >= exit_on_opposing_min opposing signals) and
    respect a minimum hold. Returns new pending orders (filled next bar)."""
    ex = _exec(cfg)
    orders = []
    pend_syms = {o["sym"] for o in state["pending"]}

    # ---- exits / invalidation ----
    for sym, pos in list(state["positions"].items()):
        if sym in pend_syms:
            continue
        sig = signals.get(sym)
        if not sig:
            continue
        price = sig["price"]
        pos["peak"] = max(pos.get("peak", pos["entry_price"]), price)  # running high
        held_days = _days(sig["as_of"], pos["entry_ts"])
        reason = None
        if price <= pos["entry_price"] * (1 - ex["stop_loss_pct"]):
            reason = ["stop_loss"]                              # always honored
        elif held_days >= ex["min_hold_days"]:
            mode = ex["exit_mode"]
            sells = _sell_votes(sig)
            trail_hit = False
            if mode == "ema18":
                t = sig.get("ema_trail")
                trail_hit = bool(t and price < t)
            elif mode == "chandelier":
                atr = sig.get("atr")
                if atr:
                    trail_hit = price < pos["peak"] - ex["chandelier_atr"] * atr
            # mode == "rule_only" -> no trailing exit
            if trail_hit:
                reason = ["trail_" + mode]
            elif len(sells) >= ex["exit_on_opposing_min"]:
                reason = [f["rule_id"] for f in sells]
        if reason:
            orders.append({"sym": sym, "side": "sell", "signal_ts": sig["as_of"],
                           "reason": reason, "hold_days": held_days})

    # ---- entries (confluence + regime gate) ----
    held = set(state["positions"]) | pend_syms | {o["sym"] for o in orders}
    open_slots = int(cfg["max_positions"]) - len(state["positions"]) \
        - sum(1 for o in state["pending"] + orders if o["side"] == "buy")
    regime_ok = not (ex["downtrend_blocks_buys"] and market.get("regime") == "downtrend")
    if open_slots > 0 and regime_ok:
        cands = []
        for s, sig in signals.items():
            if s in held:
                continue
            votes = _buy_votes(sig, ex["entry_kinds"])
            if len(votes) >= ex["entry_min_rules"]:
                cands.append((s, len(votes), sig.get("net_score", 0)))
        cands.sort(key=lambda x: (x[1], x[2]), reverse=True)
        for s, _nv, _sc in cands[:open_slots]:
            sig = signals[s]
            orders.append({"sym": s, "side": "buy", "signal_ts": sig["as_of"],
                           "reason": [f["rule_id"] for f in _buy_votes(sig, ex["entry_kinds"])],
                           "regime": market.get("regime")})
    state["pending"].extend(orders)
    return orders


def positions_value(state, last_price) -> float:
    tot = 0.0
    for sym, pos in state["positions"].items():
        px = last_price(sym)
        tot += pos["shares"] * (px if px else pos["entry_price"])
    return tot


def append_performance(ts, equity, cash, posval, realized, npos, bench):
    new = not paths.PERFORMANCE_FILE.exists()
    with open(paths.PERFORMANCE_FILE, "a", encoding="utf-8") as f:
        if new:
            f.write("timestamp,equity,cash,positions_value,realized_pnl,n_positions,benchmark\n")
        f.write(f"{ts},{equity:.2f},{cash:.2f},{posval:.2f},{realized:.2f},"
                f"{npos},{bench if bench is not None else ''}\n")


# ---------------- live wrapper (called from run.py --trade) ----------------
def process_cycle(out: dict, cfg: dict, cal, log, feed) -> dict:
    state = load_state(cfg)
    signals = out["signals"]

    def price_after(sym, signal_ts):
        df = feed.load_cached(sym)
        if df is None:
            return None
        ts = datetime.fromisoformat(signal_ts)
        later = df.index[df.index > ts]
        if len(later) == 0:
            return None
        return later[0].isoformat(), float(df.loc[later[0], "Open"])

    def last_price(sym):
        s = signals.get(sym)
        return s["price"] if s else None

    events = fill_pending(state, price_after, cfg, log)
    decide_orders(state, signals, out["market"], cfg)

    posval = positions_value(state, last_price)
    equity = state["cash"] + posval
    state["last_cycle"] = out["generated_at"]
    save_state(state)
    append_performance(out["generated_at"], equity, state["cash"], posval,
                       state["realized_pnl"], len(state["positions"]),
                       out["market"].get("price"))
    if events:
        log.info("Fills: %s", "; ".join(f"{e['event']} {e['sym']}@{e['price']:.1f}"
                                        for e in events))
    log.info("Portfolio: equity %.0f cash %.0f positions %d pending %d realizedPnL %.0f",
             equity, state["cash"], len(state["positions"]), len(state["pending"]),
             state["realized_pnl"])
    return state
