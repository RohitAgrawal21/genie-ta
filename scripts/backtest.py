"""Historical replay — populates portfolio.json + performance.csv using the SAME
engine.portfolio primitives as the live loop, with identical no-lookahead fills
(signal on bar i -> order -> filled at bar i+1 OPEN).

This is a walk-forward paper-trade simulation, NOT a vectorized backtest: each day
we (1) fill yesterday's orders at today's open, (2) mark-to-market at today's close,
(3) decide tomorrow's orders from today's signals.

Run:  python scripts/backtest.py            # default 30-name subset, ~1y daily
      python scripts/backtest.py --all       # full universe (slower)
      python scripts/backtest.py --n 50
"""
from __future__ import annotations
import argparse, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from engine import paths
from engine.config import load_config, load_universe
from engine.datafeed import DataFeed
from engine.indicators import compute_indicators
from engine.rules import evaluate_all
from engine.signal_engine import _net_signal, market_regime
from engine import portfolio as PF


def mini_signal(d, i):
    fired = evaluate_all(d, i)
    net = _net_signal(fired)
    trail = d["ema_slow"].iat[i]
    atr = d["atr"].iat[i]
    return {
        "as_of": d.index[i].isoformat(),
        "price": float(d["Close"].iat[i]),
        "ema_trail": float(trail) if pd.notna(trail) else None,
        "atr": float(atr) if pd.notna(atr) else None,
        "rs_rating": None,
        **net,
        "fired": [{"rule_id": r.rule_id, "signal": r.signal,
                   "kind": r.extra.get("kind")} for r in fired],
    }


def regime_series(bench_enriched):
    """Precompute a cheap per-bar regime label from benchmark indicators."""
    d = bench_enriched
    out = {}
    for i in range(len(d)):
        c, s50, s200 = d["Close"].iat[i], d["sma50"].iat[i], d["sma200"].iat[i]
        if pd.isna(s200):
            out[d.index[i]] = "unknown"; continue
        dist = sum(1 for j in range(max(1, i - 24), i + 1)
                   if (d["Close"].iat[j] - d["Close"].iat[j - 1]) / d["Close"].iat[j - 1] <= -0.002
                   and d["Volume"].iat[j] > d["Volume"].iat[j - 1])
        if c > s50 > s200:
            out[d.index[i]] = "confirmed_uptrend" if dist < 5 else "uptrend_under_pressure"
        elif c < s200:
            out[d.index[i]] = "downtrend"
        else:
            out[d.index[i]] = "neutral"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--warmup", type=int, default=205)
    ap.add_argument("--period", default="2y", help="yfinance daily history window")
    ap.add_argument("--exit", choices=["ema18", "chandelier", "rule_only"],
                    help="override execution.exit_mode")
    ap.add_argument("--entry-min", type=int, help="override execution.entry_min_rules")
    ap.add_argument("--oos", type=float, default=0.0,
                    help="hold out the last fraction (e.g. 0.33) as out-of-sample")
    args = ap.parse_args()

    cfg = load_config(); cfg["mode"] = "eod"
    cfg["data"]["eod_period"] = args.period
    if args.exit:
        cfg["execution"]["exit_mode"] = args.exit
    if args.entry_min:
        cfg["execution"]["entry_min_rules"] = args.entry_min
    universe = load_universe()
    syms = universe if args.all else universe[:args.n]
    feed = DataFeed(cfg)
    print(f"Replay universe: {len(syms)} names + benchmark; fetching daily...")
    data, failed = feed.fetch_universe(syms)
    bench_data, _ = feed.fetch_universe([cfg["benchmark"]])
    bench = bench_data.get(cfg["benchmark"])
    enriched = {s: compute_indicators(df) for s, df in data.items() if len(df) > args.warmup}
    bench_en = compute_indicators(bench) if bench is not None else None
    regimes = regime_series(bench_en) if bench_en is not None else {}
    print(f"Loaded {len(enriched)} names (failed {len(failed)}); building timeline...")

    # union trading calendar
    all_dates = sorted(set().union(*[set(d.index) for d in enriched.values()]))
    bench_close = {ts: float(bench.loc[ts, "Close"]) for ts in bench.index} if bench is not None else {}

    # fresh state
    for p in (paths.PORTFOLIO_FILE, paths.PERFORMANCE_FILE):
        if p.exists():
            p.unlink()
    state = PF.new_state(cfg)
    pos_index = {s: {ts: k for k, ts in enumerate(d.index)} for s, d in enriched.items()}

    def price_after(sym, signal_ts):
        d = enriched.get(sym)
        if d is None:
            return None
        ts = pd.Timestamp(signal_ts)
        later = d.index[d.index > ts]
        return (later[0].isoformat(), float(d.loc[later[0], "Open"])) if len(later) else None

    start = all_dates[args.warmup] if len(all_dates) > args.warmup else all_dates[0]
    n_cycles = 0
    for t in all_dates:
        if t < start:
            continue
        # 1) fill yesterday's orders at today's open
        PF.fill_pending(state, price_after, cfg)
        # 2) signals for names having a (warmed-up) bar today
        signals_t = {}
        for s, d in enriched.items():
            i = pos_index[s].get(t)
            if i is None or i < args.warmup:
                continue
            signals_t[s] = mini_signal(d, i)
        market_t = {"regime": regimes.get(t, "unknown"), "price": bench_close.get(t)}
        # 3) mark-to-market at close + record equity
        last_close = {s: (float(enriched[s].loc[t, "Close"]) if t in pos_index[s] else None)
                      for s in state["positions"]}
        posval = PF.positions_value(state, lambda s: last_close.get(s))
        equity = state["cash"] + posval
        PF.append_performance(t.isoformat(), equity, state["cash"], posval,
                              state["realized_pnl"], len(state["positions"]),
                              bench_close.get(t))
        # 4) decide tomorrow's orders
        PF.decide_orders(state, signals_t, market_t, cfg)
        n_cycles += 1

    state["last_cycle"] = all_dates[-1].isoformat()
    PF.save_state(state)
    from engine.analytics import compute
    rep = compute(state, cfg)["summary"]
    ex = cfg["execution"]
    print(f"\nReplay done: {n_cycles} trading days, {len(state['trade_log'])} closed trades, "
          f"{len(state['positions'])} still open.")
    print(f"RESULT exit={ex['exit_mode']} entry_min={ex['entry_min_rules']} "
          f"trades={rep['num_trades']} return={rep['total_return_pct']:+.2f}% "
          f"alpha={rep['alpha_vs_nifty_pct']:+.2f}% maxDD={rep['max_drawdown_pct']:.1f}% "
          f"win={rep['win_rate_pct']:.0f}% PF={rep['profit_factor']}")

    if args.oos > 0:  # out-of-sample check: metrics on the held-out tail only
        perf = pd.read_csv(PF.paths.PERFORMANCE_FILE, parse_dates=["timestamp"])
        cut = int(len(perf) * (1 - args.oos))
        seg = perf.iloc[cut:]
        if len(seg) > 2:
            ret = (seg["equity"].iloc[-1] / seg["equity"].iloc[0] - 1) * 100
            bret = (seg["benchmark"].iloc[-1] / seg["benchmark"].iloc[0] - 1) * 100
            print(f"OOS (last {args.oos:.0%}): return={ret:+.2f}% nifty={bret:+.2f}% "
                  f"alpha={ret - bret:+.2f}%")
    print("Wrote state/portfolio.json and state/performance.csv")


if __name__ == "__main__":
    main()
