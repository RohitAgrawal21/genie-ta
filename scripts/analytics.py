"""Phase E report: overall performance + per-rule attribution table.
Reads state/portfolio.json + state/performance.csv. Writes state/analytics.json.
Does NOT touch STRATEGY.md.

Run:  python scripts/analytics.py
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import paths
from engine.config import load_config
from engine.portfolio import load_state
from engine.analytics import compute


def main():
    cfg = load_config()
    state = load_state(cfg)
    if not state.get("trade_log"):
        print("No trades yet. Run scripts/backtest.py (or run.py --trade) first.")
        return
    rep = compute(state, cfg)
    paths.SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    (paths.STATE_DIR / "analytics.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")

    s = rep["summary"]
    print("=" * 78)
    print("PHASE E — PERFORMANCE SUMMARY")
    print("=" * 78)
    rows = [
        ("Starting capital", f"{s['starting_capital']:,.0f}"),
        ("Final equity", f"{s['final_equity']:,.0f}"),
        ("Total return", f"{s['total_return_pct']:+.2f}%"),
        ("Nifty return (same window)", f"{s['benchmark_return_pct']:+.2f}%" if s['benchmark_return_pct'] is not None else "n/a"),
        ("Alpha vs Nifty", f"{s['alpha_vs_nifty_pct']:+.2f}%" if s['alpha_vs_nifty_pct'] is not None else "n/a"),
        ("Realized P&L", f"{s['realized_pnl']:,.0f}"),
        ("Max drawdown", f"{s['max_drawdown_pct']:.2f}%"),
        ("Trades (closed)", f"{s['num_trades']}"),
        ("Win rate", f"{s['win_rate_pct']:.1f}%"),
        ("Avg win / Avg loss", f"{s['avg_win']:,.0f} / {s['avg_loss']:,.0f}"),
        ("Profit factor", f"{s['profit_factor']}" if s['profit_factor'] is not None else "inf"),
        ("Expectancy / trade", f"{s['expectancy_per_trade']:,.0f}"),
        ("Avg trade return", f"{s['avg_trade_return_pct']:+.2f}%"),
        ("Avg exposure", f"{s['avg_exposure_pct']:.0f}% of max slots"),
        ("Open positions", f"{s['open_positions']}"),
        ("Trading days", f"{s['trading_days']}"),
    ]
    for k, v in rows:
        print(f"  {k:<28}{v:>18}")

    print("\n" + "=" * 78)
    print("PER-RULE ATTRIBUTION  (entry-rule participation; a trade credits every")
    print("entry rule that fired on its buy — rows can overlap)")
    print("=" * 78)
    print(f"{'RULE':<6}{'NAME':<30}{'IMPL':<10}{'TRD':>5}{'WIN%':>7}{'NET P&L':>12}{'AVG%':>8}")
    print("-" * 78)
    for r in rep["per_rule"]:
        print(f"{r['rule_id']:<6}{r['name'][:29]:<30}{r['impl']:<10}{r['trades']:>5}"
              f"{r['win_rate_pct']:>7.0f}{r['net_pnl']:>12,.0f}{r['avg_ret_pct']:>8.1f}")

    print("\nEXIT REASONS:")
    for k, v in rep["exit_reasons"].items():
        print(f"  {k:<12} trades={v['trades']:<4} net P&L {v['net_pnl']:>12,.0f}")

    print("\nWrote state/analytics.json")
    print("NOTE: STRATEGY.md was NOT modified. Strategy changes are yours to make.")


if __name__ == "__main__":
    main()
