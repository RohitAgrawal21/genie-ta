"""Signal engine: one cycle = fetch universe -> compute indicators -> evaluate
every rule on the LAST COMPLETED bar -> blend into a net signal -> write
signals.json. Also computes benchmark market-regime (CAN SLIM M) and
cross-sectional relative strength (CAN SLIM L), which are portfolio-level.

No lookahead: in intraday mode the still-forming last bar is dropped; the signal
bar is the most recently CLOSED bar. Fills (next bar open) are Phase D's job.
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from . import paths
from .datafeed import DataFeed, to_yf
from .indicators import compute_indicators
from .rules import REGISTRY, RuleResult
from .market_calendar import MarketCalendar
from .logutil import get_logger

# net-signal blending: weight each fired directional rule by conviction
STRENGTH_W = {"high": 3.0, "med": 2.0, "low": 1.0}
IMPL_W = {"clean": 1.0, "heuristic": 0.5, "fundamental": 0.0, "context": 0.0}
NET_THRESHOLD = 2.0   # |net score| must exceed this to call buy/sell


def _interval_minutes(feed: DataFeed) -> int:
    if feed.mode == "eod":
        return 24 * 60
    return int("".join(ch for ch in feed.interval if ch.isdigit()) or "15")


def last_completed_pos(df: pd.DataFrame, feed: DataFeed, cal: MarketCalendar) -> int:
    """Integer position of the last CLOSED bar. Drops a forming intraday bar."""
    if len(df) == 0:
        return -1
    if feed.mode == "eod":
        return len(df) - 1
    bar_ts = df.index[-1].to_pydatetime()
    bar_end = bar_ts + timedelta(minutes=_interval_minutes(feed))
    now_naive = cal.now().replace(tzinfo=None)
    return len(df) - 2 if now_naive < bar_end else len(df) - 1


def _net_signal(fired: list[RuleResult]) -> dict:
    buy = sum(STRENGTH_W[r.extra["strength"]] * IMPL_W[r.extra["impl"]]
              for r in fired if r.signal == "buy")
    sell = sum(STRENGTH_W[r.extra["strength"]] * IMPL_W[r.extra["impl"]]
               for r in fired if r.signal == "sell")
    net = buy - sell
    if net >= NET_THRESHOLD:
        sig = "buy"
    elif net <= -NET_THRESHOLD:
        sig = "sell"
    else:
        sig = "neutral"
    return {"net_signal": sig, "buy_score": round(buy, 2), "sell_score": round(sell, 2),
            "net_score": round(net, 2),
            "n_buy": sum(1 for r in fired if r.signal == "buy"),
            "n_sell": sum(1 for r in fired if r.signal == "sell")}


def market_regime(bench: pd.DataFrame | None) -> dict:
    """CAN SLIM M: index regime + distribution-day count from the benchmark."""
    if bench is None or len(bench) < 60:
        return {"regime": "unknown", "reason": "no benchmark data"}
    d = compute_indicators(bench)
    i = len(d) - 1
    c, s50, s200 = d["Close"].iat[i], d["sma50"].iat[i], d["sma200"].iat[i]
    dist = 0
    for j in range(max(1, i - 24), i + 1):
        down = (d["Close"].iat[j] - d["Close"].iat[j - 1]) / d["Close"].iat[j - 1] <= -0.002
        higher_vol = d["Volume"].iat[j] > d["Volume"].iat[j - 1]
        if down and higher_vol:
            dist += 1
    up = pd.notna(s200) and c > s50 > s200
    if up and dist < 5:
        regime = "confirmed_uptrend"
    elif up:
        regime = "uptrend_under_pressure"
    elif pd.notna(s200) and c < s200:
        regime = "downtrend"
    else:
        regime = "neutral"
    return {"regime": regime, "distribution_days": int(dist),
            "price": round(float(c), 2),
            "above_50dma": bool(pd.notna(s50) and c > s50),
            "above_200dma": bool(pd.notna(s200) and c > s200)}


def _rs_ratings(enriched: dict[str, pd.DataFrame], bench: pd.DataFrame | None) -> dict[str, int]:
    """CAN SLIM L: 1-99 relative-strength rating = percentile of 252d (or max
    available) return across the universe, lightly tilted vs the benchmark."""
    rets = {}
    bench_ret = 0.0
    if bench is not None and len(bench) > 2:
        n = min(252, len(bench) - 1)
        bench_ret = bench["Close"].iat[-1] / bench["Close"].iat[-1 - n] - 1
    for s, d in enriched.items():
        n = min(252, len(d) - 1)
        if n < 20:
            continue
        rets[s] = (d["Close"].iat[-1] / d["Close"].iat[-1 - n] - 1) - 0.0 * bench_ret
    if not rets:
        return {}
    ser = pd.Series(rets)
    pct = ser.rank(pct=True) * 99
    return {s: int(round(max(1, v))) for s, v in pct.items()}


def run_cycle(feed: DataFeed, symbols: list[str], cfg: dict, cal: MarketCalendar,
              logger=None) -> dict:
    log = logger or get_logger("signal_engine")
    bench_sym = cfg.get("benchmark", "^NSEI")

    data, failed = feed.fetch_universe(symbols)
    bench_data, _ = feed.fetch_universe([bench_sym])
    bench = bench_data.get(bench_sym)

    enriched = {s: compute_indicators(df) for s, df in data.items() if len(df) > 60}
    rs = _rs_ratings(enriched, bench)
    mkt = market_regime(bench)

    signals = {}
    for s, d in enriched.items():
        i = last_completed_pos(d, feed, cal)
        if i < 1:
            continue
        fired = []
        for rdef in REGISTRY:
            try:
                res = rdef["fn"](d, i)
            except Exception:
                continue
            if res.fired:
                res.extra.update(impl=rdef["impl"], strength=rdef["strength"],
                                 category=rdef["category"], kind=rdef["kind"])
                fired.append(res)
        net = _net_signal(fired)
        trail = d["ema_slow"].iat[i]  # 18-EMA trailing reference
        signals[s] = {
            "symbol": s,
            "as_of": d.index[i].isoformat(),
            "price": round(float(d["Close"].iat[i]), 2),
            "ema_trail": round(float(trail), 2) if pd.notna(trail) else None,
            "atr": round(float(d["atr"].iat[i]), 2) if pd.notna(d["atr"].iat[i]) else None,
            "rs_rating": rs.get(s),
            "leader": bool(rs.get(s, 0) >= 80),   # CAN SLIM L pass
            **net,
            "fired": [{"rule_id": r.rule_id, "name": r.name, "signal": r.signal,
                       "strength": r.extra["strength"], "impl": r.extra["impl"],
                       "kind": r.extra["kind"], "detail": r.detail} for r in fired],
        }

    out = {
        "generated_at": cal.now().isoformat(timespec="seconds"),
        "mode": feed.mode,
        "interval": feed.interval,
        "market": mkt,
        "universe_count": len(symbols),
        "evaluated": len(signals),
        "failures": failed,
        "signals": signals,
    }
    paths.ensure_dirs()
    paths.SIGNALS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    n_buy = sum(1 for v in signals.values() if v["net_signal"] == "buy")
    n_sell = sum(1 for v in signals.values() if v["net_signal"] == "sell")
    log.info("Cycle done: %d evaluated, %d net-BUY, %d net-SELL, regime=%s, "
             "%d failed -> %s", len(signals), n_buy, n_sell, mkt.get("regime"),
             len(failed), paths.SIGNALS_FILE.name)
    return out
