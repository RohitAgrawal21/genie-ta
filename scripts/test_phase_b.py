"""Phase B acceptance: rule -> function mapping + ONE worked example per rule.

Fetches daily history for a basket of liquid names, computes indicators once,
then scans every bar to find the most recent bar where each rule fired and
prints that bar's evidence. Rules that need fundamentals/benchmark are listed
with their status. Nothing here trades — it only validates the translations.

Run:  python scripts/test_phase_b.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from engine.config import load_config
from engine.datafeed import DataFeed
from engine.indicators import compute_indicators
from engine.rules import REGISTRY

BASKET = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "SBIN", "TATAMOTORS",
          "TATASTEEL", "ICICIBANK", "ADANIENT", "MARUTI", "AXISBANK", "ITC"]


def main():
    cfg = load_config()
    cfg["mode"] = "eod"  # validate on clean daily bars
    feed = DataFeed(cfg)
    print(f"Fetching daily history for {len(BASKET)} names...")
    raw, failed = feed.fetch_universe(BASKET)
    enriched = {s: compute_indicators(df) for s, df in raw.items() if len(df) > 60}
    print(f"Loaded {len(enriched)} symbols (failed: {failed})\n")

    # For each rule, find the most recent (symbol, bar) where it fired.
    examples: dict[str, tuple] = {}
    for rdef in REGISTRY:
        rid = rdef["rule_id"]
        if rdef["impl"] in ("fundamental", "context"):
            continue
        best = None
        for sym, d in enriched.items():
            n = len(d)
            for i in range(n - 1, max(60, n - 240), -1):  # last ~1y, newest first
                try:
                    res = rdef["fn"](d, i)
                except Exception as e:
                    best = ("ERROR", str(e)[:60]); break
                if res.fired:
                    best = (sym, d.index[i], res); break
            if best and best[0] != "ERROR" and not isinstance(best[1], str):
                break
        examples[rid] = best

    # ---- print mapping table ----
    impl_counts = {}
    fired_clean = fired_heur = 0
    print("=" * 100)
    print(f"{'RULE':<6}{'NAME':<34}{'IMPL':<11}{'EX?':<5}WORKED EXAMPLE (most recent firing)")
    print("=" * 100)
    for rdef in REGISTRY:
        rid, name, impl = rdef["rule_id"], rdef["name"], rdef["impl"]
        impl_counts[impl] = impl_counts.get(impl, 0) + 1
        if impl in ("fundamental", "context"):
            print(f"{rid:<6}{name[:33]:<34}{impl:<11}{'n/a':<5}{rdef['fn'](next(iter(enriched.values())),120).detail}")
            continue
        ex = examples.get(rid)
        if ex and ex[0] == "ERROR":
            print(f"{rid:<6}{name[:33]:<34}{impl:<11}{'ERR':<5}{ex[1]}")
        elif ex:
            sym, ts, res = ex
            tag = "OK"
            if impl == "clean":
                fired_clean += 1
            else:
                fired_heur += 1
            detail = res.detail or f"{res.signal}"
            print(f"{rid:<6}{name[:33]:<34}{impl:<11}{tag:<5}{sym} {ts:%Y-%m-%d} -> {res.signal.upper()} ({detail})")
        else:
            print(f"{rid:<6}{name[:33]:<34}{impl:<11}{'--':<5}(no firing in sample window)")

    print("=" * 100)
    print(f"Rules total: {len(REGISTRY)}  |  impl breakdown: {impl_counts}")
    print(f"Clean rules with a worked example: {fired_clean}  |  heuristic with example: {fired_heur}")

    # ---- one fully-worked example, in detail ----
    print("\n=== DETAILED WORKED EXAMPLE (audit one translation end-to-end) ===")
    for rid in ("3.8", "1.3", "6.2", "11.3"):
        ex = examples.get(rid)
        if not ex or ex[0] == "ERROR" or isinstance(ex[1], str):
            continue
        sym, ts, res = ex
        d = enriched[sym]
        i = d.index.get_loc(ts)
        print(f"\n[{rid}] {res.name}  on {sym} @ {ts:%Y-%m-%d}  =>  {res.signal.upper()}  ({res.detail})")
        cols = ["Open", "High", "Low", "Close", "Volume", "rsi", "macd", "macd_signal", "sma50", "sma200"]
        cols = [c for c in cols if c in d.columns]
        print(d[cols].iloc[i - 2:i + 1].round(2).to_string())

    print("\nPHASE B complete — review the mapping, then confirm to proceed to Phase C.\n")


if __name__ == "__main__":
    main()
