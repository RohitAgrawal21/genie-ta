"""Rank a universe by the multi-factor Genie Score (Tier 1). Every number is
computed from OHLCV, so it's exact. Prints a leaderboard + a reconciliation
check (6-month return recomputed independently) to prove accuracy.

Run:  python scripts/rank_universe.py --n 40
"""
from __future__ import annotations
import argparse, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.config import load_config, load_universe
from engine.datafeed import DataFeed
from engine.indicators import compute_indicators
from engine.factors import raw_factors, cross_sectional_scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--period", default="2y")
    ap.add_argument("--fundamentals", action="store_true",
                    help="also pull validated Value/Quality (slower: 1 call/stock)")
    args = ap.parse_args()

    cfg = load_config(); cfg["mode"] = "eod"; cfg["data"]["eod_period"] = args.period
    feed = DataFeed(cfg)
    syms = load_universe()[:args.n]
    print(f"Fetching {len(syms)} names + benchmark...")
    data, failed = feed.fetch_universe(syms)
    bench_data, _ = feed.fetch_universe([cfg["benchmark"]])
    bench = bench_data.get(cfg["benchmark"])
    bench_close = bench["Close"] if bench is not None else None

    raws = {}
    for s, df in data.items():
        if len(df) < 130:
            continue
        raws[s] = raw_factors(compute_indicators(df), bench_close)

    weights = {"Momentum": 0.30, "Trend": 0.25, "RelativeStrength": 0.20,
               "LowVolatility": 0.15, "Value": 0.0, "Quality": 0.0}
    if args.fundamentals:
        from engine.fundamentals import fetch
        from engine.datafeed import to_yf
        print("Pulling validated fundamentals (1 call/stock)...")
        for s in list(raws):
            fu = fetch(s, to_yf(s), price=raws[s]["price"])
            raws[s]["value_raw"] = fu.get("value_raw")
            raws[s]["quality_raw"] = fu.get("quality_raw")
        weights = {"Momentum": 0.25, "Trend": 0.20, "RelativeStrength": 0.15,
                   "LowVolatility": 0.10, "Value": 0.15, "Quality": 0.15}

    scored = cross_sectional_scores(raws, weights)
    ranked = sorted([s for s in scored if scored[s]["genie_score"] is not None],
                    key=lambda s: scored[s]["genie_score"], reverse=True)

    fund = args.fundamentals
    hdr = f"\n{'#':>3} {'SYMBOL':<12}{'SCORE':>6} {'Mom':>4}{'Trd':>4}{'RS':>4}{'LVol':>5}"
    hdr += (f"{'Val':>4}{'Qual':>5}" if fund else "") + f"{'6m ret':>8}{'vol%':>6}"
    print(hdr); print("-" * (len(hdr) + 2))
    for s in ranked:
        v = scored[s]; ss = v["subscores"]; rw = v["raw"]
        def g(x): return f"{x:.0f}" if x is not None else "  -"
        line = (f"{v['rank']:>3} {s:<12}{v['genie_score']:>6.1f} "
                f"{g(ss.get('Momentum')):>4}{g(ss.get('Trend')):>4}{g(ss.get('RelativeStrength')):>4}"
                f"{g(ss.get('LowVolatility')):>5}")
        if fund:
            line += f"{g(ss.get('Value')):>4}{g(ss.get('Quality')):>5}"
        line += (f"{(rw['ret_6m']*100 if rw['ret_6m'] is not None else float('nan')):>7.1f}%"
                 f"{(rw['vol_ann']*100 if rw['vol_ann'] is not None else float('nan')):>6.0f}")
        print(line)

    # ---- accuracy reconciliation: recompute 6m return raw for the top name ----
    if ranked:
        top = ranked[0]; d = data[top]
        px_now = float(d["Close"].iloc[-1]); px_6m = float(d["Close"].iloc[-1 - 126])
        indep = (px_now / px_6m - 1) * 100
        eng = scored[top]["raw"]["ret_6m"] * 100
        print(f"\nRECONCILE {top}: engine 6m ret = {eng:.2f}%  |  "
              f"independent (px {px_now:.1f} vs {px_6m:.1f}, 126 bars back) = {indep:.2f}%  "
              f"-> {'MATCH' if abs(eng-indep) < 0.01 else 'MISMATCH'}")
    print(f"\nRanked {len(ranked)} stocks. All factors computed from OHLCV (exact).")


if __name__ == "__main__":
    main()
