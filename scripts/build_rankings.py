"""Generate web/rankings.json — the daily Genie Score leaderboard + factor
distributions. Run offline / via a scheduled job (it makes 1 fundamentals call
per stock, so it's slow but only runs once a day).

Run:  python scripts/build_rankings.py            # full liquid universe
      python scripts/build_rankings.py --n 60      # smaller/faster
"""
from __future__ import annotations
import argparse, sys, time, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.config import load_config, load_universe
from engine.datafeed import DataFeed
from engine.universe_scan import scan, scan_liquid, save, RANKINGS_FILE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--period", default="2y")
    ap.add_argument("--no-fundamentals", action="store_true")
    ap.add_argument("--all", action="store_true", help="scan the full NSE list (web/symbols_full.json)")
    ap.add_argument("--liquid", type=int, default=0,
                    help="scan all NSE, keep the top-N most liquid by turnover (recommended)")
    args = ap.parse_args()

    cfg = load_config(); cfg["mode"] = "eod"; cfg["data"]["eod_period"] = args.period
    feed = DataFeed(cfg)
    t0 = time.time()
    if args.liquid:
        print(f"Liquidity-filtered scan: top {args.liquid} NSE names by turnover...")
        res = scan_liquid(feed, cfg, top_n=args.liquid)
    else:
        if args.all:
            import json
            full = json.loads((Path(__file__).resolve().parent.parent / "web" / "symbols_full.json").read_text(encoding="utf-8"))
            syms = [x["s"] for x in full]
        else:
            syms = load_universe()[:args.n]
        print(f"Scanning {len(syms)} names (fundamentals={not args.no_fundamentals})...")
        res = scan(feed, cfg, syms, with_fundamentals=not args.no_fundamentals)
    save(res)

    top = sorted([s for s in res["scores"] if res["scores"][s]["genie_score"] is not None],
                 key=lambda s: res["scores"][s]["genie_score"], reverse=True)
    print(f"\nDone in {time.time()-t0:.0f}s. {res['universe_size']} scored, "
          f"{len(res['failed'])} failed. as_of={res['as_of']}")
    print("Top 10:")
    for s in top[:10]:
        v = res["scores"][s]
        print(f"  #{v['rank']:>2} {s:<12} {v['genie_score']:>5.1f}  "
              f"P/E {v['fundamentals'].get('pe','n/a')}")
    print(f"\nWrote {RANKINGS_FILE}")


if __name__ == "__main__":
    main()
