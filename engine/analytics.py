"""Performance + per-rule attribution. Reads portfolio.json (trade log) and
performance.csv (equity curve). NEVER modifies STRATEGY.md — strategy edits are
the user's call. This only measures.

Per-rule attribution is by PARTICIPATION: a closed trade's net P&L is credited to
EVERY entry rule that fired on the buy. A rule's win rate = share of its trades
that were profitable. Multi-rule trades count for each contributing rule.
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd

from . import paths
from .rules import REGISTRY_BY_ID


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min() * 100)


def compute(state: dict, cfg: dict) -> dict:
    trades = state.get("trade_log", [])
    start = float(state.get("starting_capital", cfg["starting_capital"]))

    perf = None
    if paths.PERFORMANCE_FILE.exists():
        perf = pd.read_csv(paths.PERFORMANCE_FILE, parse_dates=["timestamp"])

    # ---- equity-curve metrics ----
    if perf is not None and len(perf):
        eq = perf["equity"]
        final_eq = float(eq.iloc[-1])
        total_ret = (final_eq / start - 1) * 100
        mdd = _max_drawdown(eq)
        avg_pos = float(perf["n_positions"].mean())
        exposure = avg_pos / int(cfg["max_positions"]) * 100
        bench = perf["benchmark"].dropna()
        if len(bench) > 1 and bench.iloc[0] > 0:
            bench_ret = (bench.iloc[-1] / bench.iloc[0] - 1) * 100
        else:
            bench_ret = None
        days = max((perf["timestamp"].iloc[-1] - perf["timestamp"].iloc[0]).days, 1)
    else:
        final_eq, total_ret, mdd, exposure, bench_ret, days = start, 0, 0, 0, None, 1

    # ---- trade stats ----
    n = len(trades)
    pnls = [t["net_pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    win_rate = len(wins) / n * 100 if n else 0
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    expectancy = float(np.mean(pnls)) if pnls else 0.0
    avg_hold = float(np.mean([t["ret_pct"] for t in trades])) if trades else 0.0

    summary = {
        "starting_capital": start,
        "final_equity": round(final_eq, 2),
        "total_return_pct": round(total_ret, 2),
        "benchmark_return_pct": round(bench_ret, 2) if bench_ret is not None else None,
        "alpha_vs_nifty_pct": round(total_ret - bench_ret, 2) if bench_ret is not None else None,
        "realized_pnl": round(state.get("realized_pnl", 0.0), 2),
        "max_drawdown_pct": round(mdd, 2),
        "num_trades": n,
        "win_rate_pct": round(win_rate, 1),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "expectancy_per_trade": round(expectancy, 2),
        "avg_trade_return_pct": round(avg_hold, 2),
        "avg_exposure_pct": round(exposure, 1),
        "open_positions": len(state.get("positions", {})),
        "trading_days": days,
    }

    # ---- per-rule attribution (entry participation) ----
    by_rule = {}
    for t in trades:
        for rid in t.get("entry_rules", []):
            r = by_rule.setdefault(rid, {"trades": 0, "wins": 0, "net_pnl": 0.0,
                                         "rets": []})
            r["trades"] += 1
            r["wins"] += 1 if t["net_pnl"] > 0 else 0
            r["net_pnl"] += t["net_pnl"]
            r["rets"].append(t["ret_pct"])
    rule_rows = []
    for rid, r in by_rule.items():
        meta = REGISTRY_BY_ID.get(rid, {})
        rule_rows.append({
            "rule_id": rid,
            "name": meta.get("name", rid),
            "impl": meta.get("impl", "?"),
            "trades": r["trades"],
            "win_rate_pct": round(r["wins"] / r["trades"] * 100, 1),
            "net_pnl": round(r["net_pnl"], 2),
            "avg_pnl": round(r["net_pnl"] / r["trades"], 2),
            "avg_ret_pct": round(float(np.mean(r["rets"])), 2),
        })
    rule_rows.sort(key=lambda x: x["net_pnl"], reverse=True)

    # ---- exit-reason tally ----
    exit_tally = {}
    for t in trades:
        reason = t.get("exit_reason") or []
        first = reason[0] if reason else ""
        if first == "stop_loss":
            key = "stop_loss"
        elif first.startswith("trail_"):
            key = "trailing_stop"
        else:
            key = "rule_exit"
        e = exit_tally.setdefault(key, {"trades": 0, "net_pnl": 0.0})
        e["trades"] += 1
        e["net_pnl"] += t["net_pnl"]

    return {"summary": summary, "per_rule": rule_rows, "exit_reasons": exit_tally}
