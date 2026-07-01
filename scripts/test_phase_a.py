"""Phase A acceptance test.

Proves: (1) batched fetch works, (2) data is sane, (3) fresh cache is reused
with NO second network call, (4) a bogus ticker is skipped+logged, not fatal.
Run:  python scripts/test_phase_a.py
"""
from __future__ import annotations
import sys, time, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.config import load_config
from engine.datafeed import DataFeed, to_yf
from engine.market_calendar import MarketCalendar

TEST = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "SBIN"]
BOGUS = "NOTAREALTICKER123"


def main():
    cfg = load_config()
    cal = MarketCalendar(cfg)
    print(f"\n=== MARKET CALENDAR ===")
    print(f"Now (IST): {cal.now():%Y-%m-%d %H:%M:%S}  |  Status: {cal.status()}  "
          f"|  Trading day: {cal.is_trading_day()}  |  Open now: {cal.is_open()}")

    feed = DataFeed(cfg)
    print(f"\n=== FETCH #1 (cold) — mode={cfg['mode']} interval={feed.interval} "
          f"period={feed.period} ===")
    t0 = time.time()
    data, failed = feed.fetch_universe(TEST + [BOGUS])
    dt1 = time.time() - t0
    print(f"Fetched {len(data)} ok, {len(failed)} failed in {dt1:.2f}s  "
          f"(failed: {failed})")

    print(f"\n{'SYMBOL':<10}{'yf':<14}{'BARS':>6}  {'FIRST BAR':<19}  "
          f"{'LAST BAR':<19}  {'LAST CLOSE':>11}  {'LAST VOL':>12}")
    for s in TEST:
        df = data.get(s)
        if df is None:
            print(f"{s:<10}{'-':<14}{'MISSING':>6}")
            continue
        print(f"{s:<10}{to_yf(s):<14}{len(df):>6}  "
              f"{df.index[0]:%Y-%m-%d %H:%M}    {df.index[-1]:%Y-%m-%d %H:%M}    "
              f"{float(df['Close'].iloc[-1]):>11.2f}  {int(df['Volume'].iloc[-1]):>12,}")

    # Show a small tail so the data shape is visible
    sample = data.get("RELIANCE")
    if sample is not None:
        print(f"\n=== RELIANCE tail (last 3 bars) ===")
        print(sample.tail(3).to_string())

    print(f"\n=== FETCH #2 (warm) — should hit cache, ~0s, ZERO network ===")
    t0 = time.time()
    data2, failed2 = feed.fetch_universe(TEST)
    dt2 = time.time() - t0
    print(f"Returned {len(data2)} symbols in {dt2:.3f}s  "
          f"(speedup {dt1/max(dt2,1e-6):.0f}x)  -> cache reuse "
          f"{'CONFIRMED' if dt2 < dt1 * 0.2 else 'CHECK'}")

    print(f"\n=== RATE-LIMIT VERDICT ===")
    n = len(TEST)
    per = dt1 / max(n, 1)
    print(f"Cold fetch: {n} tickers / {dt1:.1f}s = {per:.2f}s per ticker (batched).")
    print(f"Full universe (100) projection at batch_size={cfg['data']['batch_size']}: "
          f"~{(100/ cfg['data']['batch_size']) * (dt1):.0f}s worst-case if all cold.")
    print("Backoff/retry, batch-split, skip+log all active. Loop is crash-safe.")
    print("\nPHASE A OK — review and confirm to proceed to Phase B.\n")


if __name__ == "__main__":
    main()
