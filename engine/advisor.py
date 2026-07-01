"""Plain-English advisor: turns the technical engine output into a verdict and
explanation a non-technical person can act on. Reused by the CLI and the web app.

Returns a structured dict: headline verdict (BUY/HOLD/WAIT/AVOID/SELL), a one-line
reason, jargon-free "what's going on" cards, key price levels, and the underlying
rules (for the curious). This is systematic analysis, NOT licensed advice.
"""
from __future__ import annotations
import pandas as pd

from .indicators import compute_indicators
from .rules import evaluate_all
from .signal_engine import _net_signal, market_regime


def _tone(good):
    return "good" if good else "bad"


def analyze(symbol: str, feed, cfg: dict, name: str | None = None) -> dict:
    data, failed = feed.fetch_universe([symbol])
    ndays = len(data[symbol]) if symbol in data else 0
    if ndays < 40:   # below this even short-term indicators (RSI/MACD) can't warm up
        return {"ok": False, "symbol": symbol,
                "error": (f"'{symbol}' has only {ndays} days of trading data (needs ~40+). "
                          "Likely a very recent listing — too new to analyze reliably.")
                if ndays else f"No data found for '{symbol}'. Check the ticker."}
    bench_data, _ = feed.fetch_universe([cfg.get("benchmark", "^NSEI")])
    bench = bench_data.get(cfg.get("benchmark", "^NSEI"))

    d = compute_indicators(data[symbol])
    i = len(d) - 1
    # history depth -> confidence flag. Under 200 bars the 200-day average doesn't
    # exist yet, so the stock is a recent listing with unreliable long-term signals.
    history_months = max(1, round(ndays / 21))
    limited_history = ndays < 200
    g = lambda c: float(d[c].iat[i])
    px = g("Close")

    sma20, sma50, sma200 = g("sma20"), g("sma50"), g("sma200")
    rsi, mhist = g("rsi"), g("macd_hist")
    bb_up, bb_dn = g("bb_up"), g("bb_dn")
    pctb = (px - bb_dn) / (bb_up - bb_dn) if bb_up > bb_dn else 0.5
    vol, vavg = g("Volume"), g("vol_sma50")
    vol_ratio = vol / vavg if vavg else 1.0

    above50, above200 = px > sma50, px > sma200
    mom_up = mhist > 0
    extended = pctb > 0.9 or rsi > 70
    oversold = pctb < 0.1 or rsi < 30
    vol_strong, vol_weak = vol_ratio > 1.3, vol_ratio < 0.7

    # relative strength vs benchmark
    rs = None
    if bench is not None and len(bench) > 60:
        n = min(252, len(d) - 1, len(bench) - 1)
        rs = (px / d["Close"].iat[-1 - n] - 1) - (bench["Close"].iat[-1] / bench["Close"].iat[-1 - n] - 1)
    regime = market_regime(bench)["regime"] if bench is not None else "unknown"

    fired = evaluate_all(d, i)
    net = _net_signal(fired)
    buy_entry = [f for f in fired if f.signal == "buy" and f.extra.get("kind") == "entry"]
    confluence = len(buy_entry) >= cfg.get("execution", {}).get("entry_min_rules", 3)
    regime_ok = regime != "downtrend"

    # ---------- verdict decision tree (long-only, lay-person) ----------
    if above200 and above50 and confluence and regime_ok and not extended:
        action, tone, conf = "BUY", "good", "high"
        headline = "Looks like a genuine buy setup."
        reason = ("The stock is in an uptrend (above its key averages), several signals "
                  "agree, and the overall market is supportive.")
    elif confluence and regime_ok and above50 and not extended:
        action, tone, conf = "BUY (with a stop)", "good", "medium"
        headline = "Buyable, but keep a safety net."
        reason = ("Signals are turning up and the market allows it, but the longer-term "
                  "trend isn't fully confirmed yet — use a stop-loss.")
    elif confluence and (not regime_ok):
        action, tone, conf = "WAIT / HOLD", "warn", "medium"
        headline = "Bullish, but the market is against it — wait."
        reason = ("The stock itself looks strong, but the broad market is falling. Buying "
                  "into a weak market lowers your odds. Wait for the market to steady.")
    elif confluence and extended:
        action, tone, conf = "WAIT (too hot)", "warn", "medium"
        headline = "Good stock, bad entry — it's run up too fast."
        reason = ("Signals are bullish but the price is stretched short-term. Chasing here "
                  "risks buying right before a pullback. Wait for a dip or a pause.")
    elif (not above200) and (not above50) and (not mom_up):
        action, tone, conf = "AVOID / SELL", "bad", "high"
        headline = "In a downtrend — stay away (or exit)."
        reason = ("Price is below its key averages and momentum is negative. The path of "
                  "least resistance is down. Not a place to buy; holders should have a stop.")
    elif oversold and not above50:
        action, tone, conf = "WATCH for a bottom", "warn", "low"
        headline = "Beaten down — possible bounce, but unproven."
        reason = ("The stock is oversold and could bounce, but it hasn't turned up yet. "
                  "Wait for a clear reversal before acting.")
    elif above50 and not confluence:
        action, tone, conf = "HOLD / NEUTRAL", "neutral", "medium"
        headline = "Holding up, but no clear trigger right now."
        reason = ("It's above short-term support with no strong buy or sell signal. Fine to "
                  "hold if you own it; no compelling reason to buy fresh.")
    else:
        action, tone, conf = "NEUTRAL / WAIT", "neutral", "low"
        headline = "No clear edge either way right now."
        reason = "Signals are mixed. Best to wait for a cleaner setup."

    # ---------- plain-English cards ----------
    def trend_txt():
        if above200 and above50:
            return ("Uptrend", "Trading above both its short- and long-term average price — healthy.", "good")
        if not above200 and not above50:
            return ("Downtrend", "Below both its short- and long-term averages — weak.", "bad")
        return ("Recovering / range", "Above its short-term average but below the long-term one — mid-recovery.", "warn")

    def mom_txt():
        if rsi > 70:
            return ("Overbought", f"Momentum very strong (RSI {rsi:.0f}) — stretched, may pause.", "warn")
        if rsi < 30:
            return ("Oversold", f"Momentum very weak (RSI {rsi:.0f}) — beaten down, may bounce.", "warn")
        d_ = "rising" if mom_up else "fading"
        return (f"Momentum {d_}", f"RSI {rsi:.0f} (neutral zone); short-term momentum is {d_}.", _tone(mom_up))

    def vol_txt():
        if vol_strong:
            return ("Strong volume", f"Trading at {vol_ratio:.1f}× normal — moves are backed by real buying/selling.", "good")
        if vol_weak:
            return ("Weak volume", f"Only {vol_ratio:.1f}× normal — the current move lacks conviction.", "warn")
        return ("Normal volume", f"Around {vol_ratio:.1f}× the usual — nothing unusual.", "neutral")

    def rs_txt():
        if rs is None:
            return ("Relative strength", "Not available.", "neutral")
        if rs > 0:
            return ("Beating the market", f"Up {rs*100:+.0f}% vs the Nifty over the past year — a leader.", "good")
        return ("Lagging the market", f"{rs*100:+.0f}% vs the Nifty over the past year — a laggard.", "bad")

    def mkt_txt():
        m = {"confirmed_uptrend": ("Market healthy", "The broad market is in an uptrend — supportive.", "good"),
             "uptrend_under_pressure": ("Market wobbling", "Uptrend but under some selling pressure.", "warn"),
             "downtrend": ("Market weak", "The broad market is falling — a headwind for any stock.", "bad"),
             "neutral": ("Market flat", "The broad market has no clear direction.", "neutral")}
        return m.get(regime, ("Market unknown", "Couldn't read the market regime.", "neutral"))

    cards = []
    for fn in (trend_txt, mom_txt, vol_txt, rs_txt, mkt_txt):
        label, meaning, t = fn()
        cards.append({"label": label, "meaning": meaning, "tone": t})

    # ---------- key levels (plain) ----------
    supports = sorted([v for v in (sma20, sma50, bb_dn) if v < px], reverse=True)
    resists = sorted([v for v in (bb_up, sma200) if v > px])
    stop = supports[0] if supports else px * 0.95
    support2 = supports[1] if len(supports) > 1 else bb_dn
    resist1 = resists[0] if resists else px * 1.05
    resist2 = resists[1] if len(resists) > 1 else sma200

    def _lvl(v):  # round, or None if not available (e.g. 200-DMA on a new listing)
        return round(float(v), 1) if pd.notna(v) else None

    levels = {
        "price": _lvl(px),
        "buy_above": _lvl(resist1),              # confirmed-breakout trigger
        "support": _lvl(stop),                   # nearest floor
        "stop_below": _lvl(support2),            # get-out level
        "resistance": _lvl(resist2),             # bigger overhead
    }

    # limited history downgrades confidence — long-term signals aren't reliable yet
    if limited_history and conf == "high":
        conf = "medium"

    return {
        "ok": True, "symbol": symbol, "name": name,
        "as_of": d.index[i].strftime("%Y-%m-%d"),
        "price": round(px, 1),
        "history_months": history_months,
        "limited_history": limited_history,
        "history_note": (
            f"Only ~{history_months} months of trading history available"
            f"{' (recent listing)' if history_months < 12 else ''}. Long-term signals "
            "(200-day trend, 52-week levels) aren't fully formed — treat this as a "
            "short-term read with lower confidence." if limited_history else None),
        "verdict": {"action": action, "tone": tone, "confidence": conf,
                    "headline": headline, "reason": reason},
        "cards": cards,
        "levels": levels,
        "net_signal": net["net_signal"],
        "rules": [{"id": f.rule_id, "name": f.name, "signal": f.signal} for f in fired],
        "disclaimer": "Educational technical analysis, not investment advice. "
                      "Do your own research; manage your own risk.",
    }
