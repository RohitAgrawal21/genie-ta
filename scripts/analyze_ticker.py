"""Deep single-ticker read through the engine: indicator snapshot + every rule
firing on the last closed bar + trend/regime + relative strength vs benchmark.

Run:  python scripts/analyze_ticker.py M&M
      python scripts/analyze_ticker.py RELIANCE --period 2y
"""
from __future__ import annotations
import argparse, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from engine.config import load_config
from engine.datafeed import DataFeed, to_yf
from engine.indicators import compute_indicators
from engine.rules import REGISTRY
from engine.signal_engine import _net_signal, market_regime
from engine.rules import evaluate_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--period", default="1y")
    args = ap.parse_args()

    cfg = load_config(); cfg["mode"] = "eod"; cfg["data"]["eod_period"] = args.period
    feed = DataFeed(cfg)
    sym = args.symbol.upper()
    data, failed = feed.fetch_universe([sym])
    bench_data, _ = feed.fetch_universe([cfg["benchmark"]])
    if sym not in data:
        print(f"Could not fetch {sym} ({to_yf(sym)}). Failed: {failed}"); return
    d = compute_indicators(data[sym])
    bench = bench_data.get(cfg["benchmark"])
    i = len(d) - 1
    g = lambda c: d[c].iat[i]

    print(f"\n===== {sym}  ({to_yf(sym)})  as of {d.index[i]:%Y-%m-%d} =====")
    print(f"Close {g('Close'):.1f}   O {g('Open'):.1f}  H {g('High'):.1f}  L {g('Low'):.1f}   "
          f"Vol {g('Volume'):,.0f} (50d avg {g('vol_sma50'):,.0f}, {g('Volume')/g('vol_sma50'):.2f}x)")

    print("\n-- TREND / MAs --")
    for c, lbl in [("sma20", "20-DMA"), ("sma50", "50-DMA"), ("sma200", "200-DMA"), ("ema_trend", "13-EMA")]:
        v = g(c)
        pos = "above" if g("Close") > v else "below"
        print(f"  {lbl:<8} {v:>9.1f}   price {pos}")
    reg_stock = ("UPTREND" if g("Close") > g("sma50") > g("sma200")
                 else "DOWNTREND" if g("Close") < g("sma50") < g("sma200")
                 else "MIXED/RANGE")
    print(f"  Stock structure: {reg_stock}")

    print("\n-- MOMENTUM / VOLATILITY --")
    print(f"  RSI(14)      {g('rsi'):.1f}   ({'overbought' if g('rsi')>70 else 'oversold' if g('rsi')<30 else 'neutral'})")
    print(f"  Stoch %K/%D  {g('stoch_k'):.0f} / {g('stoch_d'):.0f}")
    print(f"  MACD/sig/hist {g('macd'):.1f} / {g('macd_signal'):.1f} / {g('macd_hist'):+.1f}")
    print(f"  Bollinger    up {g('bb_up'):.0f}  mid {g('bb_mid'):.0f}  dn {g('bb_dn'):.0f}   "
          f"bandwidth {g('bb_bw'):.3f}")
    pctb = (g('Close') - g('bb_dn')) / (g('bb_up') - g('bb_dn')) * 100
    print(f"  %B {pctb:.0f}% of band   ATR(14) {g('atr'):.1f} ({g('atr')/g('Close')*100:.1f}% of price)")
    w = min(252, len(d))
    hi52, lo52 = d["High"].iloc[-w:].max(), d["Low"].iloc[-w:].min()
    print(f"  {w}-bar range   {lo52:.0f} – {hi52:.0f}   "
          f"(now {(g('Close')-lo52)/(hi52-lo52)*100:.0f}% of range)")

    if bench is not None and len(bench) > 60:
        n = min(252, len(d) - 1, len(bench) - 1)
        rs = (g('Close') / d['Close'].iat[-1 - n] - 1) - (bench['Close'].iat[-1] / bench['Close'].iat[-1 - n] - 1)
        print(f"\n-- RELATIVE STRENGTH -- vs {cfg['benchmark']} over {n}d: "
              f"{rs*100:+.1f}% ({'outperforming' if rs>0 else 'lagging'})")
        print(f"   Market regime: {market_regime(bench)['regime']}")

    fired = evaluate_all(d, i)
    net = _net_signal(fired)
    print(f"\n-- RULES FIRING ON LAST BAR ({len(fired)}) -- "
          f"NET: {net['net_signal'].upper()} (score {net['net_score']}, {net['n_buy']}B/{net['n_sell']}S)")
    for r in sorted(fired, key=lambda x: x.signal):
        k = r.extra.get("kind", "")
        print(f"  [{r.rule_id:<4}] {r.name[:34]:<34} {r.signal:<7} {r.extra.get('impl',''):<9} {k:<7} {r.detail}")

    # engine decision preview (what the paper-trader would do)
    from engine.portfolio import _exec, _buy_votes
    ex = _exec(cfg)
    sig = {"fired": [{"rule_id": r.rule_id, "name": r.name, "signal": r.signal,
                      "kind": r.extra.get("kind")} for r in fired]}
    votes = _buy_votes(sig, ex["entry_kinds"])
    regime = market_regime(bench)["regime"] if bench is not None else "unknown"
    regime_veto = ex["downtrend_blocks_buys"] and regime == "downtrend"
    confluence_ok = len(votes) >= ex["entry_min_rules"]
    if confluence_ok and not regime_veto:
        decision = "WOULD ENTER"
    elif confluence_ok and regime_veto:
        decision = f"STAND ASIDE (confluence met, but regime gate blocks longs in {regime})"
    else:
        decision = "STAND ASIDE (insufficient confluence)"
    print(f"\n-- ENGINE DECISION -- entry needs >={ex['entry_min_rules']} entry-rules agreeing; "
          f"got {len(votes)} buy entry-votes; market regime = {regime} -> {decision}")


if __name__ == "__main__":
    main()
