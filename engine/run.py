"""Standalone runner. Claude is NOT the runtime — you run this yourself.

Usage:
  python -m engine.run --once            # run a single cycle now (ignores hours) and exit
  python -m engine.run --once --guard    # single cycle ONLY if market is open
  python -m engine.run --loop            # long-lived loop with market-hours guard
  python -m engine.run --mode eod --once # override config mode for this run

Recommended automation on Windows: Task Scheduler -> every 15 min on weekdays
  run `python -m engine.run --once --guard` (the --guard makes off-hours a no-op).
Or just leave `--loop` running; it sleeps through nights/weekends/holidays.

Phase C writes signals.json. Phase D (paper trading) is layered on top in run_cycle
once enabled; this runner is the scheduling shell.
"""
from __future__ import annotations
import argparse
import time
import warnings
from datetime import timedelta

warnings.filterwarnings("ignore")

from .config import load_config, load_universe
from .datafeed import DataFeed
from .market_calendar import MarketCalendar
from .signal_engine import run_cycle
from .logutil import get_logger


def _build(mode_override: str | None):
    cfg = load_config()
    if mode_override:
        cfg["mode"] = mode_override
    universe = load_universe()
    cal = MarketCalendar(cfg)
    feed = DataFeed(cfg)
    return cfg, universe, cal, feed


def run_once(mode_override=None, guard=False, trade=False):
    log = get_logger("run")
    cfg, universe, cal, feed = _build(mode_override)
    if guard and not cal.is_open():
        log.info("Market %s — guarded --once is a no-op.", cal.status())
        return None
    log.info("Single cycle: mode=%s universe=%d status=%s",
             cfg["mode"], len(universe), cal.status())
    out = run_cycle(feed, universe, cfg, cal, log)
    if trade:
        _maybe_trade(out, cfg, cal, log)
    return out


def run_loop(mode_override=None, trade=False):
    log = get_logger("run")
    cfg, universe, cal, feed = _build(mode_override)
    poll = int(cfg["poll_minutes"]) * 60
    log.info("Loop started: mode=%s poll=%dm universe=%d (Ctrl-C to stop)",
             cfg["mode"], cfg["poll_minutes"], len(universe))
    last_eod_date = None
    while True:
        try:
            now = cal.now()
            if cfg["mode"] == "eod":
                # run once per trading day, shortly after the close
                if (cal.is_trading_day(now) and now.time() >= cal.close
                        and last_eod_date != now.date()):
                    out = run_cycle(feed, universe, cfg, cal, log)
                    if trade:
                        _maybe_trade(out, cfg, cal, log)
                    last_eod_date = now.date()
                time.sleep(600)  # check every 10 min
            else:
                if cal.is_open(now):
                    out = run_cycle(feed, universe, cfg, cal, log)
                    if trade:
                        _maybe_trade(out, cfg, cal, log)
                    time.sleep(poll)
                else:
                    log.info("Market %s — sleeping.", cal.status(now))
                    time.sleep(min(poll, 900))
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            break
        except Exception as e:  # never die on a transient error
            log.warning("Cycle error (continuing): %s", e)
            time.sleep(60)


def _maybe_trade(out, cfg, cal, log):
    """Phase D hook — paper-trade on the cycle's signals. Imported lazily so
    Phase C runs even before the portfolio layer exists."""
    try:
        from .portfolio import process_cycle
    except Exception:
        return
    process_cycle(out, cfg, cal, log)


def main():
    ap = argparse.ArgumentParser(description="TA paper-trading engine runner")
    ap.add_argument("--once", action="store_true", help="run a single cycle and exit")
    ap.add_argument("--loop", action="store_true", help="run the scheduled loop")
    ap.add_argument("--guard", action="store_true", help="with --once: only run if market open")
    ap.add_argument("--mode", choices=["intraday", "eod"], help="override config mode")
    ap.add_argument("--trade", action="store_true", help="also run the paper-trade engine (Phase D)")
    args = ap.parse_args()
    if args.loop:
        run_loop(args.mode, trade=args.trade)
    else:
        run_once(args.mode, guard=args.guard, trade=args.trade)


if __name__ == "__main__":
    main()
