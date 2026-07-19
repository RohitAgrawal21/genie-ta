"""Precompute validated fundamentals for the whole NSE universe -> web/fundamentals.json.

The live server (on Render) CANNOT fetch Yahoo's fundamentals endpoint — it's
blocked for datacenter IPs. So we compute them here (offline / CI, where it works),
with the same reconciliation gates, and commit the result. The server just reads it.

Writes incrementally so partial progress survives a throttle/interrupt.
Run:  python scripts/build_fundamentals.py
"""
from __future__ import annotations
import json, sys, time, warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.config import load_config
from engine.datafeed import DataFeed, to_yf
from engine.fundamentals import fetch as fetch_fund

OUT = ROOT / "web" / "fundamentals.json"


def main():
    cfg = load_config(); cfg["mode"] = "eod"; cfg["data"]["eod_period"] = "6mo"
    feed = DataFeed(cfg)
    full = json.loads((ROOT / "web" / "symbols_full.json").read_text(encoding="utf-8"))
    syms = [x["s"] for x in full]
    print(f"Fetching prices for {len(syms)} NSE names (for PE reconciliation)...")
    data, _ = feed.fetch_universe(syms)

    out = {"as_of": date.today().isoformat(), "source": "Yahoo Finance (yfinance)", "f": {}}
    ok = 0
    t0 = time.time()
    for n, s in enumerate(syms, 1):
        df = data.get(s)
        px = float(df["Close"].iloc[-1]) if df is not None and len(df) else None
        try:
            fu = fetch_fund(s, to_yf(s), price=px, force=True)
        except Exception:
            continue
        if fu.get("fields"):
            out["f"][s] = {"fields": fu["fields"], "as_of": fu["as_of"],
                           "value_raw": fu.get("value_raw"), "quality_raw": fu.get("quality_raw")}
            ok += 1
        if n % 100 == 0:
            OUT.write_text(json.dumps(out), encoding="utf-8")
            print(f"  {n}/{len(syms)}  ({ok} with data)  {time.time()-t0:.0f}s")
        time.sleep(0.15)   # be gentle with the endpoint

    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(f"\nDone: {ok}/{len(syms)} stocks with validated fundamentals in {time.time()-t0:.0f}s")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
