"""Rule layer: ONE function per STRATEGY.md rule, evaluated at bar position i on
an indicator-enriched dataframe. Each returns a RuleResult (fired + direction).

Honesty tags (impl):
  clean       — deterministic from OHLCV+indicators; high confidence.
  heuristic   — codifies a discretionary/pattern rule via swing/threshold logic;
                approximate by nature (chart patterns, divergences, confluence).
  fundamental — needs data NOT in OHLCV (quarterly/annual EPS); NOT evaluated here.
  context     — needs cross-sectional/benchmark data (relative strength, market
                regime); evaluated by the engine with the benchmark, not standalone.

No rule looks past bar i. 'sell' on a long-only book is used as an exit/avoid by
the portfolio layer (Phase D), not as a new short.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from ta.trend import MACD

from . import patterns as P


@dataclass
class RuleResult:
    rule_id: str
    name: str
    signal: str = "neutral"      # buy | sell | neutral
    fired: bool = False
    detail: str = ""
    extra: dict = field(default_factory=dict)


# ---------- small cross helpers ----------
def _xa_val(s, i, lvl):  # series crosses ABOVE scalar level at i
    a, b = s.iat[i - 1], s.iat[i]
    return pd.notna(a) and pd.notna(b) and a <= lvl < b


def _xb_val(s, i, lvl):  # crosses BELOW
    a, b = s.iat[i - 1], s.iat[i]
    return pd.notna(a) and pd.notna(b) and a >= lvl > b


def _xa_ser(a, b, i):    # a crosses ABOVE b
    return (pd.notna(a.iat[i - 1]) and pd.notna(b.iat[i - 1])
            and a.iat[i - 1] <= b.iat[i - 1] and a.iat[i] > b.iat[i])


def _xb_ser(a, b, i):    # a crosses BELOW b
    return (pd.notna(a.iat[i - 1]) and pd.notna(b.iat[i - 1])
            and a.iat[i - 1] >= b.iat[i - 1] and a.iat[i] < b.iat[i])


def _rising(s, i, n=1):
    return pd.notna(s.iat[i]) and pd.notna(s.iat[i - n]) and s.iat[i] > s.iat[i - n]


def _falling(s, i, n=1):
    return pd.notna(s.iat[i]) and pd.notna(s.iat[i - n]) and s.iat[i] < s.iat[i - n]


def _ok(d, i, *cols):
    return all(pd.notna(d[c].iat[i]) for c in cols)


# thresholds shared across oscillator rules (mirrors STRATEGY conflicts; tunable)
LV = {"rsi_os": 30, "rsi_ob": 70, "stoch_os": 20, "stoch_ob": 80,
      "vol_spike": 1.5, "power_spike": 2.0, "level_tol": 0.02}


# =====================================================================
# 1-2. CANDLESTICKS (clean)
# =====================================================================
def _candle(rid, name, det, sig, strength="high"):
    def fn(d, i):
        f = det(d, i)
        return RuleResult(rid, name, sig if f else "neutral", f)
    return dict(rule_id=rid, name=name, category="candlestick", kind="entry",
                impl="clean", strength=strength, fn=fn)


# =====================================================================
# 3. OSCILLATORS
# =====================================================================
def r_3_1(d, i):
    f = _ok(d, i, "rsi") and _xa_val(d["rsi"], i, LV["rsi_os"])
    return RuleResult("3.1", "RSI Oversold Reversal", "buy" if f else "neutral", f,
                      f"RSI {d['rsi'].iat[i]:.1f}" if f else "")


def r_3_2(d, i):
    f = _ok(d, i, "rsi") and _xb_val(d["rsi"], i, LV["rsi_ob"])
    return RuleResult("3.2", "RSI Overbought Reversal", "sell" if f else "neutral", f,
                      f"RSI {d['rsi'].iat[i]:.1f}" if f else "")


def r_3_3(d, i):
    div = P._indicator_divergence(d, i, "rsi", "bull")
    return RuleResult("3.3", "RSI Bullish Divergence", "buy" if div else "neutral",
                      bool(div), "lower price low, higher RSI low" if div else "")


def r_3_4(d, i):
    div = P._indicator_divergence(d, i, "rsi", "bear")
    return RuleResult("3.4", "RSI Bearish Divergence", "sell" if div else "neutral",
                      bool(div), "higher price high, lower RSI high" if div else "")


def r_3_5(d, i):
    f = (_ok(d, i, "stoch_k", "stoch_d") and _xa_ser(d["stoch_k"], d["stoch_d"], i)
         and d["stoch_k"].iat[i] < LV["stoch_os"] and d["stoch_d"].iat[i] < LV["stoch_os"])
    return RuleResult("3.5", "Stochastic Oversold Buy", "buy" if f else "neutral", f,
                      f"%K {d['stoch_k'].iat[i]:.0f}" if f else "")


def r_3_6(d, i):
    f = (_ok(d, i, "stoch_k", "stoch_d") and _xb_ser(d["stoch_k"], d["stoch_d"], i)
         and d["stoch_k"].iat[i] > LV["stoch_ob"] and d["stoch_d"].iat[i] > LV["stoch_ob"])
    return RuleResult("3.6", "Stochastic Overbought Sell", "sell" if f else "neutral", f,
                      f"%K {d['stoch_k'].iat[i]:.0f}" if f else "")


def r_3_7(d, i):
    div = P._indicator_divergence(d, i, "stoch_k", "bull")
    return RuleResult("3.7", "Stochastic Bullish Divergence", "buy" if div else "neutral",
                      bool(div))


def r_3_8(d, i):
    f = _ok(d, i, "macd", "macd_signal") and _xa_ser(d["macd"], d["macd_signal"], i)
    below0 = f and d["macd"].iat[i] < 0
    return RuleResult("3.8", "MACD Bullish Crossover", "buy" if f else "neutral", f,
                      "below zero (stronger)" if below0 else ("above zero" if f else ""))


def r_3_9(d, i):
    f = _ok(d, i, "macd", "macd_signal") and _xb_ser(d["macd"], d["macd_signal"], i)
    return RuleResult("3.9", "MACD Bearish Crossover", "sell" if f else "neutral", f,
                      "above zero (stronger)" if (f and d["macd"].iat[i] > 0) else "")


def r_3_10(d, i):
    div = P._indicator_divergence(d, i, "macd_hist", "bull")
    return RuleResult("3.10", "MACD-Histogram Bullish Divergence",
                      "buy" if div else "neutral", bool(div))


def r_3_11(d, i):
    div = P._indicator_divergence(d, i, "macd_hist", "bear")
    return RuleResult("3.11", "MACD-Histogram Bearish Divergence",
                      "sell" if div else "neutral", bool(div))


def r_3_12(d, i):
    f = _ok(d, i, "macd_hist") and _xa_val(d["macd_hist"], i, 0.0)
    return RuleResult("3.12", "MACD Zero-Line Bullish Cross", "buy" if f else "neutral", f)


# =====================================================================
# 4. ELDER PROPRIETARY
# =====================================================================
def r_4_1(d, i):
    f = (_ok(d, i, "ema_trend", "bear_power") and _rising(d["ema_trend"], i)
         and d["bear_power"].iat[i] < 0 and _rising(d["bear_power"], i))
    return RuleResult("4.1", "Elder-Ray Bull Power Buy", "buy" if f else "neutral", f,
                      f"BearPwr {d['bear_power'].iat[i]:.1f} rising" if f else "")


def r_4_2(d, i):
    f = (_ok(d, i, "ema_trend", "bull_power") and _falling(d["ema_trend"], i)
         and d["bull_power"].iat[i] > 0 and _falling(d["bull_power"], i))
    return RuleResult("4.2", "Elder-Ray Bear Power Sell", "sell" if f else "neutral", f)


def r_4_3(d, i):
    f = (_ok(d, i, "force_ema2", "ema_trend") and _rising(d["ema_trend"], i, 3)
         and _xb_val(d["force_ema2"], i, 0.0))
    return RuleResult("4.3", "Force Index 2-Day Buy", "buy" if f else "neutral", f,
                      "FI(2) dipped <0 in uptrend" if f else "")


def r_4_4(d, i):
    if not _ok(d, i, "force_ema13"):
        return RuleResult("4.4", "Force Index 13-Day Trend", "neutral", False)
    if _xa_val(d["force_ema13"], i, 0.0):
        return RuleResult("4.4", "Force Index 13-Day Trend", "buy", True, "FI(13) turned positive")
    if _xb_val(d["force_ema13"], i, 0.0):
        return RuleResult("4.4", "Force Index 13-Day Trend", "sell", True, "FI(13) turned negative")
    return RuleResult("4.4", "Force Index 13-Day Trend", "neutral", False)


# =====================================================================
# 5. TRIPLE SCREEN (composite / heuristic)
# =====================================================================
def _weekly_hist_slope(d, i):
    sub = d["Close"].iloc[:i + 1]
    wk = sub.resample("W-FRI").last().dropna()
    if len(wk) < 40:
        return None
    h = MACD(wk, window_slow=26, window_fast=12, window_sign=9).macd_diff()
    if len(h) < 2 or pd.isna(h.iloc[-1]) or pd.isna(h.iloc[-2]):
        return None
    return h.iloc[-1] - h.iloc[-2]


def r_5_1(d, i):
    slope = _weekly_hist_slope(d, i)
    if slope is None or not _ok(d, i, "stoch_k"):
        return RuleResult("5.1", "Elder Triple Screen", "neutral", False)
    k, hi1, lo1 = d["stoch_k"].iat[i], d["High"].iat[i - 1], d["Low"].iat[i - 1]
    c = d["Close"].iat[i]
    if slope > 0 and k < 30 and c > hi1:           # weekly up + daily oversold + entry trigger
        return RuleResult("5.1", "Elder Triple Screen", "buy", True, "wk up / daily oversold / trigger")
    if slope < 0 and k > 70 and c < lo1:
        return RuleResult("5.1", "Elder Triple Screen", "sell", True, "wk down / daily overbought / trigger")
    return RuleResult("5.1", "Elder Triple Screen", "neutral", False)


# =====================================================================
# 6. MOVING AVERAGES
# =====================================================================
def r_6_1(d, i):
    if not _ok(d, i, "sma50"):
        return RuleResult("6.1", "MA Support Bounce", "neutral", False)
    sma = d["sma50"]
    f = (_rising(sma, i) and d["Low"].iat[i] <= sma.iat[i] * 1.01
         and d["Close"].iat[i] > sma.iat[i] and d["Close"].iat[i - 1] <= d["Close"].iat[i])
    return RuleResult("6.1", "MA Support Bounce", "buy" if f else "neutral", f,
                      "bounce off rising 50MA" if f else "")


def r_6_2(d, i):
    f = _ok(d, i, "sma50", "sma200") and _xa_ser(d["sma50"], d["sma200"], i)
    return RuleResult("6.2", "Golden Cross", "buy" if f else "neutral", f)


def r_6_3(d, i):
    f = _ok(d, i, "sma50", "sma200") and _xb_ser(d["sma50"], d["sma200"], i)
    return RuleResult("6.3", "Death Cross", "sell" if f else "neutral", f)


def _aligned_up(d, i):
    return (d["ema_fast"].iat[i] > d["ema_mid"].iat[i] > d["ema_slow"].iat[i])


def _aligned_dn(d, i):
    return (d["ema_fast"].iat[i] < d["ema_mid"].iat[i] < d["ema_slow"].iat[i])


def r_6_4(d, i):
    if not _ok(d, i, "ema_fast", "ema_mid", "ema_slow"):
        return RuleResult("6.4", "Triple MA Crossover (3/9/18)", "neutral", False)
    if _aligned_up(d, i) and not _aligned_up(d, i - 1) and _rising(d["ema_slow"], i):
        return RuleResult("6.4", "Triple MA Crossover (3/9/18)", "buy", True, "3>9>18 newly aligned up")
    if _aligned_dn(d, i) and not _aligned_dn(d, i - 1) and _falling(d["ema_slow"], i):
        return RuleResult("6.4", "Triple MA Crossover (3/9/18)", "sell", True, "3<9<18 newly aligned down")
    return RuleResult("6.4", "Triple MA Crossover (3/9/18)", "neutral", False)


def r_6_5(d, i):
    if not _ok(d, i, "ema_trend"):
        return RuleResult("6.5", "13-Day EMA Trend Filter", "neutral", False)
    up_now, up_prev = _rising(d["ema_trend"], i), _rising(d["ema_trend"], i - 1)
    if up_now and not up_prev:
        return RuleResult("6.5", "13-Day EMA Trend Filter", "buy", True, "13EMA slope turned up")
    if (not up_now) and up_prev:
        return RuleResult("6.5", "13-Day EMA Trend Filter", "sell", True, "13EMA slope turned down")
    return RuleResult("6.5", "13-Day EMA Trend Filter", "neutral", False)


# =====================================================================
# 7. BOLLINGER / ENVELOPE
# =====================================================================
def r_7_1(d, i):
    if not _ok(d, i, "bb_bw") or i < 126:
        return RuleResult("7.1", "Bollinger Band Squeeze", "neutral", False)
    win = d["bb_bw"].iloc[i - 125:i + 1]
    f = pd.notna(win.iloc[-1]) and win.iloc[-1] <= win.min() * 1.0001
    return RuleResult("7.1", "Bollinger Band Squeeze", "neutral", f,
                      "6-mo narrowest bandwidth (breakout pending)" if f else "")


def r_7_2(d, i):
    f = (_ok(d, i, "bb_up", "bb_bw") and d["Close"].iat[i] > d["bb_up"].iat[i]
         and _rising(d["bb_bw"], i))
    return RuleResult("7.2", "Bollinger Band Upper Walk", "buy" if f else "neutral", f)


def r_7_3(d, i):
    f = (_ok(d, i, "bb_dn", "bb_bw") and d["Close"].iat[i] < d["bb_dn"].iat[i]
         and _rising(d["bb_bw"], i))
    return RuleResult("7.3", "Bollinger Band Lower Walk", "sell" if f else "neutral", f)


def r_7_4(d, i):
    if not _ok(d, i, "bb_mid", "bb_dn", "bb_up") or i < 5:
        return RuleResult("7.4", "Bollinger Band Target", "neutral", False)
    touched_low = any(d["Low"].iat[j] <= d["bb_dn"].iat[j] for j in range(i - 5, i))
    touched_up = any(d["High"].iat[j] >= d["bb_up"].iat[j] for j in range(i - 5, i))
    if touched_low and _xa_ser(d["Close"], d["bb_mid"], i):
        return RuleResult("7.4", "Bollinger Band Target", "buy", True, "off lower band, crossed mid -> target upper")
    if touched_up and _xb_ser(d["Close"], d["bb_mid"], i):
        return RuleResult("7.4", "Bollinger Band Target", "sell", True, "off upper band, crossed mid -> target lower")
    return RuleResult("7.4", "Bollinger Band Target", "neutral", False)


def r_7_5(d, i):
    if not _ok(d, i, "env_up", "env_dn"):
        return RuleResult("7.5", "Envelope Overextension", "neutral", False)
    if d["High"].iat[i] >= d["env_up"].iat[i]:
        return RuleResult("7.5", "Envelope Overextension", "sell", True, "touched +3% envelope (overbought)")
    if d["Low"].iat[i] <= d["env_dn"].iat[i]:
        return RuleResult("7.5", "Envelope Overextension", "buy", True, "touched -3% envelope (oversold)")
    return RuleResult("7.5", "Envelope Overextension", "neutral", False)


# =====================================================================
# 8. PIVOT POINTS
# =====================================================================
def _pivots(d, i):
    h, l, c = d["High"].iat[i - 1], d["Low"].iat[i - 1], d["Close"].iat[i - 1]
    pp = (h + l + c) / 3.0
    return dict(PP=pp, R1=2 * pp - l, S1=2 * pp - h, R2=pp + (h - l), S2=pp - (h - l))


def r_8_1(d, i):
    if i < 1:
        return RuleResult("8.1", "Daily Pivot Levels", "neutral", False)
    pv = _pivots(d, i)
    return RuleResult("8.1", "Daily Pivot Levels", "neutral", False,
                      "PP {PP:.1f} S1 {S1:.1f} R1 {R1:.1f}".format(**pv), extra=pv)


def r_8_2(d, i):
    if i < 1:
        return RuleResult("8.2", "Pivot Support Bounce", "neutral", False)
    pv = _pivots(d, i)
    near = d["Low"].iat[i] <= pv["S1"] * (1 + LV["level_tol"]) and d["Low"].iat[i] >= pv["S2"] * (1 - LV["level_tol"])
    f = near and P.any_bullish_candle(d, i) is not None
    return RuleResult("8.2", "Pivot Support Bounce", "buy" if f else "neutral", f,
                      "bullish candle at S1/S2" if f else "")


def r_8_3(d, i):
    if i < 1:
        return RuleResult("8.3", "Pivot Resistance Rejection", "neutral", False)
    pv = _pivots(d, i)
    near = d["High"].iat[i] >= pv["R1"] * (1 - LV["level_tol"]) and d["High"].iat[i] <= pv["R2"] * (1 + LV["level_tol"])
    f = near and P.any_bearish_candle(d, i) is not None
    return RuleResult("8.3", "Pivot Resistance Rejection", "sell" if f else "neutral", f,
                      "bearish candle at R1/R2" if f else "")


# =====================================================================
# 9. CHART PATTERNS (heuristic, swing-based)
# =====================================================================
def _approx(a, b, tol=None):
    tol = tol or P.PARAMS["level_tol"]
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-9)


def r_9_1(d, i):  # Head & Shoulders Top
    highs, lows = P.swing_points(d, i, 160)
    if len(highs) < 3 or len(lows) < 2:
        return RuleResult("9.1", "Head and Shoulders Top", "neutral", False)
    (pL, ls), (pH, head), (pR, rs) = highs[-3], highs[-2], highs[-1]
    troughs = [lv for (pp, lv) in lows if pL < pp < pR]
    if head > ls and head > rs and _approx(ls, rs, 0.05) and troughs:
        neckline = min(troughs)
        if d["Close"].iat[i] < neckline < d["Close"].iat[i - 1]:
            return RuleResult("9.1", "Head and Shoulders Top", "sell", True, "neckline break")
    return RuleResult("9.1", "Head and Shoulders Top", "neutral", False)


def r_9_2(d, i):  # Inverse H&S
    highs, lows = P.swing_points(d, i, 160)
    if len(lows) < 3 or len(highs) < 2:
        return RuleResult("9.2", "Inverse Head and Shoulders", "neutral", False)
    (pL, ls), (pH, head), (pR, rs) = lows[-3], lows[-2], lows[-1]
    peaks = [lv for (pp, lv) in highs if pL < pp < pR]
    if head < ls and head < rs and _approx(ls, rs, 0.05) and peaks:
        neckline = max(peaks)
        if d["Close"].iat[i] > neckline > d["Close"].iat[i - 1]:
            return RuleResult("9.2", "Inverse Head and Shoulders", "buy", True, "neckline break")
    return RuleResult("9.2", "Inverse Head and Shoulders", "neutral", False)


def r_9_3(d, i):  # Double Top
    highs, lows = P.swing_points(d, i, 160)
    if len(highs) < 2 or not lows:
        return RuleResult("9.3", "Double Top", "neutral", False)
    (p1, h1), (p2, h2) = highs[-2], highs[-1]
    troughs = [lv for (pp, lv) in lows if p1 < pp < p2]
    if _approx(h1, h2) and troughs:
        sup = min(troughs)
        if d["Close"].iat[i] < sup < d["Close"].iat[i - 1]:
            return RuleResult("9.3", "Double Top", "sell", True, "broke trough support")
    return RuleResult("9.3", "Double Top", "neutral", False)


def r_9_4(d, i):  # Double Bottom
    highs, lows = P.swing_points(d, i, 160)
    if len(lows) < 2 or not highs:
        return RuleResult("9.4", "Double Bottom", "neutral", False)
    (p1, l1), (p2, l2) = lows[-2], lows[-1]
    peaks = [lv for (pp, lv) in highs if p1 < pp < p2]
    if _approx(l1, l2) and peaks:
        res = max(peaks)
        if d["Close"].iat[i] > res > d["Close"].iat[i - 1]:
            return RuleResult("9.4", "Double Bottom", "buy", True, "broke peak resistance")
    return RuleResult("9.4", "Double Bottom", "neutral", False)


def r_9_5(d, i):  # Ascending triangle
    highs, lows = P.swing_points(d, i, 120)
    if len(highs) < 2 or len(lows) < 2:
        return RuleResult("9.5", "Ascending Triangle", "neutral", False)
    flat = _approx(highs[-1][1], highs[-2][1], 0.02)
    rising = lows[-1][1] > lows[-2][1]
    res = max(highs[-1][1], highs[-2][1])
    if flat and rising and d["Close"].iat[i] > res > d["Close"].iat[i - 1]:
        return RuleResult("9.5", "Ascending Triangle", "buy", True, "breakout over flat resistance")
    return RuleResult("9.5", "Ascending Triangle", "neutral", False)


def r_9_6(d, i):  # Descending triangle
    highs, lows = P.swing_points(d, i, 120)
    if len(highs) < 2 or len(lows) < 2:
        return RuleResult("9.6", "Descending Triangle", "neutral", False)
    flat = _approx(lows[-1][1], lows[-2][1], 0.02)
    falling = highs[-1][1] < highs[-2][1]
    sup = min(lows[-1][1], lows[-2][1])
    if flat and falling and d["Close"].iat[i] < sup < d["Close"].iat[i - 1]:
        return RuleResult("9.6", "Descending Triangle", "sell", True, "breakdown under flat support")
    return RuleResult("9.6", "Descending Triangle", "neutral", False)


def _pole(d, i, n=5, up=True):
    if i - n < 0:
        return False
    move = (d["Close"].iat[i] - d["Close"].iat[i - n]) / d["Close"].iat[i - n]
    atrmove = abs(d["Close"].iat[i] - d["Close"].iat[i - n]) > 2 * d["atr"].iat[i] if _ok(d, i, "atr") else True
    return (move > 0.06 if up else move < -0.06) and atrmove


def r_9_7(d, i):  # Bull flag
    if i < 10:
        return RuleResult("9.7", "Bull Flag", "neutral", False)
    if _pole(d, i - 4, 5, up=True):
        flag_hi = max(d["High"].iat[j] for j in range(i - 4, i))
        if d["Close"].iat[i] > flag_hi >= d["Close"].iat[i - 1] * 0.999:
            return RuleResult("9.7", "Bull Flag", "buy", True, "breakout above flag")
    return RuleResult("9.7", "Bull Flag", "neutral", False)


def r_9_8(d, i):  # Bear flag
    if i < 10:
        return RuleResult("9.8", "Bear Flag", "neutral", False)
    if _pole(d, i - 4, 5, up=False):
        flag_lo = min(d["Low"].iat[j] for j in range(i - 4, i))
        if d["Close"].iat[i] < flag_lo:
            return RuleResult("9.8", "Bear Flag", "sell", True, "breakdown below flag")
    return RuleResult("9.8", "Bear Flag", "neutral", False)


# =====================================================================
# 10. BROOKS PRICE ACTION
# =====================================================================
def _bull_trend_bar(d, i):
    return P.is_white(d, i) and P.is_long_body(d, i) and P.closes_near_high(d, i)


def _bear_trend_bar(d, i):
    return P.is_black(d, i) and P.is_long_body(d, i) and P.closes_near_low(d, i)


def r_10_1(d, i):
    if i < 1:
        return RuleResult("10.1", "Trend Bar Momentum", "neutral", False)
    if _bull_trend_bar(d, i) and _bull_trend_bar(d, i - 1):
        return RuleResult("10.1", "Trend Bar Momentum", "buy", True, "2 bull trend bars")
    if _bear_trend_bar(d, i) and _bear_trend_bar(d, i - 1):
        return RuleResult("10.1", "Trend Bar Momentum", "sell", True, "2 bear trend bars")
    return RuleResult("10.1", "Trend Bar Momentum", "neutral", False)


def r_10_2(d, i):
    if i < 1:
        return RuleResult("10.2", "Two-Bar Reversal", "neutral", False)
    if _bear_trend_bar(d, i - 1) and _bull_trend_bar(d, i) and d["Close"].iat[i] > d["Open"].iat[i - 1]:
        return RuleResult("10.2", "Two-Bar Reversal", "buy", True, "bear then bull")
    if _bull_trend_bar(d, i - 1) and _bear_trend_bar(d, i) and d["Close"].iat[i] < d["Open"].iat[i - 1]:
        return RuleResult("10.2", "Two-Bar Reversal", "sell", True, "bull then bear")
    return RuleResult("10.2", "Two-Bar Reversal", "neutral", False)


def _inside(d, j):
    return d["High"].iat[j] < d["High"].iat[j - 1] and d["Low"].iat[j] > d["Low"].iat[j - 1]


def r_10_3(d, i):
    if i < 2 or not _inside(d, i - 1):
        return RuleResult("10.3", "Inside Bar Breakout", "neutral", False)
    up_trend = d["Close"].iat[i - 1] > d["ema_trend"].iat[i - 1] if _ok(d, i - 1, "ema_trend") else True
    if d["Close"].iat[i] > d["High"].iat[i - 1] and up_trend:
        return RuleResult("10.3", "Inside Bar Breakout", "buy", True, "break above inside bar")
    if d["Close"].iat[i] < d["Low"].iat[i - 1] and not up_trend:
        return RuleResult("10.3", "Inside Bar Breakout", "sell", True, "break below inside bar")
    return RuleResult("10.3", "Inside Bar Breakout", "neutral", False)


def r_10_4(d, i):
    if i < 1:
        return RuleResult("10.4", "Outside Bar Reversal", "neutral", False)
    outside = d["High"].iat[i] > d["High"].iat[i - 1] and d["Low"].iat[i] < d["Low"].iat[i - 1]
    if outside and P.closes_near_high(d, i):
        return RuleResult("10.4", "Outside Bar Reversal", "buy", True, "outside up-close")
    if outside and P.closes_near_low(d, i):
        return RuleResult("10.4", "Outside Bar Reversal", "sell", True, "outside down-close")
    return RuleResult("10.4", "Outside Bar Reversal", "neutral", False)


def r_10_5(d, i):  # Breakout pullback
    if i < 8 or not _ok(d, i, "roll_high20"):
        return RuleResult("10.5", "Breakout Pullback", "neutral", False)
    broke = any(d["Close"].iat[j] >= d["roll_high20"].iat[j - 1] for j in range(i - 5, i - 1))
    level = max(d["High"].iat[j] for j in range(i - 8, i - 4)) if i >= 8 else np.nan
    pulled = d["Low"].iat[i] <= level * 1.01
    resumed = _bull_trend_bar(d, i) or (P.any_bullish_candle(d, i) is not None)
    f = broke and pulled and resumed and d["Close"].iat[i] > level
    return RuleResult("10.5", "Breakout Pullback", "buy" if f else "neutral", f,
                      "pullback to breakout held" if f else "")


def r_10_6(d, i):  # Measured move (level)
    highs, lows = P.swing_points(d, i, 120)
    if len(lows) < 1 or len(highs) < 1:
        return RuleResult("10.6", "Measured Move", "neutral", False)
    leg_start = lows[-1][1]
    leg_end = highs[-1][1] if highs[-1][0] > lows[-1][0] else d["Close"].iat[i]
    target = d["Close"].iat[i] + (leg_end - leg_start)
    return RuleResult("10.6", "Measured Move", "neutral", False,
                      f"MM target ~{target:.1f}", extra={"target": float(target)})


def r_10_7(d, i):  # Micro channel break
    if i < 6:
        return RuleResult("10.7", "Micro Channel Break", "neutral", False)
    micro_up = all(d["Low"].iat[j] >= d["Low"].iat[j - 1] for j in range(i - 4, i))
    brk = d["Low"].iat[i] < d["Low"].iat[i - 1]
    f = micro_up and brk and (d["Close"].iat[i] > d["ema_trend"].iat[i] if _ok(d, i, "ema_trend") else True)
    return RuleResult("10.7", "Micro Channel Break", "buy" if f else "neutral", f,
                      "first pullback in bull micro channel" if f else "")


# =====================================================================
# 11. FARLEY SWING
# =====================================================================
def _is_nr7(d, j):
    if j < 6:
        return False
    rngs = [d["High"].iat[k] - d["Low"].iat[k] for k in range(j - 6, j + 1)]
    return (d["High"].iat[j] - d["Low"].iat[j]) == min(rngs)


def r_11_1(d, i):
    if i < 7 or not _is_nr7(d, i - 1):
        return RuleResult("11.1", "NR7 Breakout", "neutral", False)
    if d["High"].iat[i] > d["High"].iat[i - 1]:
        return RuleResult("11.1", "NR7 Breakout", "buy", True, "breakout above NR7")
    if d["Low"].iat[i] < d["Low"].iat[i - 1]:
        return RuleResult("11.1", "NR7 Breakout", "sell", True, "breakdown below NR7")
    return RuleResult("11.1", "NR7 Breakout", "neutral", False)


def r_11_2(d, i):  # First Rise / First Failure
    if i < 22 or not _ok(d, i, "roll_high20", "roll_low20"):
        return RuleResult("11.2", "First Rise / First Failure", "neutral", False)
    base = (d["High"].iloc[i - 20:i].max() - d["Low"].iloc[i - 20:i].min()) / d["Close"].iat[i] < 0.12
    new_hi = d["Close"].iat[i] > d["roll_high20"].iat[i - 1]
    new_lo = d["Close"].iat[i] < d["roll_low20"].iat[i - 1]
    if base and new_hi:
        return RuleResult("11.2", "First Rise / First Failure", "buy", True, "first rise out of base")
    if base and new_lo:
        return RuleResult("11.2", "First Rise / First Failure", "sell", True, "first failure out of base")
    return RuleResult("11.2", "First Rise / First Failure", "neutral", False)


def r_11_3(d, i):  # Power spike
    if not _ok(d, i, "vol_sma50"):
        return RuleResult("11.3", "Power Spike", "neutral", False)
    spike = d["Volume"].iat[i] >= LV["power_spike"] * d["vol_sma50"].iat[i]
    if spike and P.closes_near_high(d, i) and P.is_white(d, i):
        return RuleResult("11.3", "Power Spike", "buy", True, f"vol {d['Volume'].iat[i]/d['vol_sma50'].iat[i]:.1f}x")
    if spike and P.closes_near_low(d, i) and P.is_black(d, i):
        return RuleResult("11.3", "Power Spike", "sell", True, f"vol {d['Volume'].iat[i]/d['vol_sma50'].iat[i]:.1f}x")
    return RuleResult("11.3", "Power Spike", "neutral", False)


def r_11_4(d, i):  # Cross-verification (confluence count)
    if i < 30 or not _ok(d, i, "sma50"):
        return RuleResult("11.4", "Cross-Verification", "neutral", False)
    price = d["Close"].iat[i]
    pv = _pivots(d, i)
    highs, lows = P.swing_points(d, i, 120)
    sup_levels = [d["sma50"].iat[i], pv["S1"]] + [lv for _, lv in lows[-2:]]
    res_levels = [d["sma50"].iat[i], pv["R1"]] + [lv for _, lv in highs[-2:]]
    sup_hits = sum(1 for lv in sup_levels if _approx(price, lv, 0.01))
    res_hits = sum(1 for lv in res_levels if _approx(price, lv, 0.01))
    if sup_hits >= 2 and P.any_bullish_candle(d, i):
        return RuleResult("11.4", "Cross-Verification", "buy", True, f"{sup_hits} support methods confluent")
    if res_hits >= 2 and P.any_bearish_candle(d, i):
        return RuleResult("11.4", "Cross-Verification", "sell", True, f"{res_hits} resistance methods confluent")
    return RuleResult("11.4", "Cross-Verification", "neutral", False)


# =====================================================================
# 12. VOLUME
# =====================================================================
def r_12_1(d, i):
    if not _ok(d, i, "sma50", "vol_sma20"):
        return RuleResult("12.1", "Volume-Trend Confirmation", "neutral", False)
    up = d["Close"].iat[i] > d["sma50"].iat[i]
    up_day = d["Close"].iat[i] > d["Close"].iat[i - 1]
    high_vol = d["Volume"].iat[i] > d["vol_sma20"].iat[i]
    if up and up_day and high_vol:
        return RuleResult("12.1", "Volume-Trend Confirmation", "buy", True, "up day, high vol, uptrend")
    if (not up) and (not up_day) and high_vol:
        return RuleResult("12.1", "Volume-Trend Confirmation", "sell", True, "down day, high vol, downtrend")
    return RuleResult("12.1", "Volume-Trend Confirmation", "neutral", False)


def r_12_2(d, i):
    if not _ok(d, i, "vol_sma50", "roll_high20", "roll_low20"):
        return RuleResult("12.2", "Volume Precedes Breakout", "neutral", False)
    spike = d["Volume"].iat[i] >= LV["vol_spike"] * d["vol_sma50"].iat[i]
    if spike and d["Close"].iat[i] >= d["roll_high20"].iat[i - 1] and P.closes_near_high(d, i):
        return RuleResult("12.2", "Volume Precedes Breakout", "buy", True, "vol spike + 20d breakout")
    if spike and d["Close"].iat[i] <= d["roll_low20"].iat[i - 1] and P.closes_near_low(d, i):
        return RuleResult("12.2", "Volume Precedes Breakout", "sell", True, "vol spike + 20d breakdown")
    return RuleResult("12.2", "Volume Precedes Breakout", "neutral", False)


def r_12_3(d, i):
    if i < 20 or not _ok(d, i, "vol_sma50"):
        return RuleResult("12.3", "Volume Dry-Up", "neutral", False)
    base = (d["High"].iloc[i - 15:i].max() - d["Low"].iloc[i - 15:i].min()) / d["Close"].iat[i] < 0.10
    dry = d["Volume"].iat[i] < 0.6 * d["vol_sma50"].iat[i]
    f = base and dry
    return RuleResult("12.3", "Volume Dry-Up", "neutral", f,
                      "low-range base + volume dry-up (breakout pending)" if f else "")


# =====================================================================
# 13. CAN SLIM
# =====================================================================
def _na_rule(rid, name, impl, reason):
    def fn(d, i):
        return RuleResult(rid, name, "neutral", False, reason)
    return dict(rule_id=rid, name=name, category="canslim", kind="filter",
                impl=impl, strength="high", fn=fn)


def r_13_3(d, i):  # N — new high from base
    if i < 60 or not _ok(d, i, "roll_high252", "vol_sma50"):
        return RuleResult("13.3", "CAN SLIM N (New High Breakout)", "neutral", False)
    base = (d["High"].iloc[i - 35:i].max() - d["Low"].iloc[i - 35:i].min()) / d["Close"].iat[i] < 0.33
    breakout = d["Close"].iat[i] >= d["roll_high252"].iat[i - 1]
    vol = d["Volume"].iat[i] >= 1.5 * d["vol_sma50"].iat[i]
    f = base and breakout and vol
    return RuleResult("13.3", "CAN SLIM N (New High Breakout)", "buy" if f else "neutral", f,
                      "52wk-high breakout from base on volume" if f else "")


def r_13_4(d, i):  # S — supply/demand via volume
    if i < 20 or not _ok(d, i, "vol_sma50"):
        return RuleResult("13.4", "CAN SLIM S (Supply/Demand)", "neutral", False)
    up_vol = sum(d["Volume"].iat[j] for j in range(i - 10, i + 1) if d["Close"].iat[j] > d["Close"].iat[j - 1])
    dn_vol = sum(d["Volume"].iat[j] for j in range(i - 10, i + 1) if d["Close"].iat[j] < d["Close"].iat[j - 1])
    breakout_vol = d["Volume"].iat[i] >= 1.5 * d["vol_sma50"].iat[i]
    f = up_vol > dn_vol and breakout_vol and d["Close"].iat[i] > d["Close"].iat[i - 1]
    return RuleResult("13.4", "CAN SLIM S (Supply/Demand)", "buy" if f else "neutral", f,
                      "demand>supply + breakout vol" if f else "")


def r_13_7(d, i):  # Cup-with-handle (heuristic)
    if i < 60:
        return RuleResult("13.7", "Cup-with-Handle Breakout", "neutral", False)
    seg = d.iloc[i - 60:i + 1]
    lip = seg["High"].iloc[:10].max()
    bottom = seg["Low"].min()
    depth = (lip - bottom) / lip
    handle_hi = seg["High"].iloc[-10:].max()
    breakout = d["Close"].iat[i] > handle_hi and d["Close"].iat[i - 1] <= handle_hi
    vol = d["Volume"].iat[i] >= 1.5 * d["vol_sma50"].iat[i] if _ok(d, i, "vol_sma50") else False
    f = 0.12 <= depth <= 0.40 and breakout and vol
    return RuleResult("13.7", "Cup-with-Handle Breakout", "buy" if f else "neutral", f,
                      f"cup depth {depth:.0%}, handle breakout on vol" if f else "")


# =====================================================================
# 14. ROSENBLOOM MOMENTUM
# =====================================================================
def r_14_1(d, i):  # Impulse buy
    if i < 8 or not _ok(d, i, "ema20", "atr"):
        return RuleResult("14.1", "Impulse Buy", "neutral", False)
    burst = sum(1 for j in range(i - 6, i - 1) if _bull_trend_bar(d, j)) >= 3
    pulled = d["Low"].iat[i] <= d["ema20"].iat[i] * 1.01 and d["Low"].iat[i] >= d["ema20"].iat[i] * 0.97
    resumed = P.any_bullish_candle(d, i) is not None or _bull_trend_bar(d, i)
    f = burst and pulled and resumed
    return RuleResult("14.1", "Impulse Buy", "buy" if f else "neutral", f,
                      "first pullback to 20EMA after burst" if f else "")


def r_14_2(d, i):  # Multi-indicator momentum divergence
    bear = P._indicator_divergence(d, i, "rsi", "bear") and P._indicator_divergence(d, i, "macd_hist", "bear")
    bull = P._indicator_divergence(d, i, "rsi", "bull") and P._indicator_divergence(d, i, "macd_hist", "bull")
    if bear:
        return RuleResult("14.2", "Momentum Divergence Warning", "sell", True, "RSI+MACD bearish divergence")
    if bull:
        return RuleResult("14.2", "Momentum Divergence Warning", "buy", True, "RSI+MACD bullish divergence")
    return RuleResult("14.2", "Momentum Divergence Warning", "neutral", False)


def r_14_3(d, i):  # Fibonacci confluence
    highs, lows = P.swing_points(d, i, 160)
    if len(highs) < 2 or len(lows) < 2:
        return RuleResult("14.3", "Fibonacci Confluence Zone", "neutral", False)
    price = d["Close"].iat[i]
    zones = []
    for (ph, hv) in highs[-2:]:
        for (pl, lv) in lows[-2:]:
            if hv > lv:
                for r in (0.382, 0.5, 0.618):
                    zones.append(hv - r * (hv - lv))
    hits = sum(1 for z in zones if _approx(price, z, 0.01))
    if hits >= 2 and P.any_bullish_candle(d, i):
        return RuleResult("14.3", "Fibonacci Confluence Zone", "buy", True, f"{hits} fib levels cluster")
    return RuleResult("14.3", "Fibonacci Confluence Zone", "neutral", False)


# =====================================================================
# 15. COMBINED CANDLE + WESTERN
# =====================================================================
def r_15_1(d, i):
    if not _ok(d, i, "sma20", "sma50"):
        return RuleResult("15.1", "Bullish Candle at MA Support", "neutral", False)
    for ma in ("sma20", "sma50"):
        rising = _rising(d[ma], i)
        near = d["Low"].iat[i] <= d[ma].iat[i] * 1.01 and d["Close"].iat[i] > d[ma].iat[i]
        if rising and near and P.any_bullish_candle(d, i):
            return RuleResult("15.1", "Bullish Candle at MA Support", "buy", True,
                              f"{P.any_bullish_candle(d, i)} at rising {ma}")
    return RuleResult("15.1", "Bullish Candle at MA Support", "neutral", False)


def r_15_2(d, i):  # Candle reversal at trendline (2-point swing line)
    highs, lows = P.swing_points(d, i, 120)
    if len(lows) >= 2:
        (p1, v1), (p2, v2) = lows[-2], lows[-1]
        if p2 > p1:
            slope = (v2 - v1) / (p2 - p1)
            proj = v2 + slope * (i - p2)
            if abs(d["Low"].iat[i] - proj) <= 0.01 * proj and P.any_bullish_candle(d, i):
                return RuleResult("15.2", "Candle Reversal at Trendline", "buy", True, "bullish candle at support TL")
    if len(highs) >= 2:
        (p1, v1), (p2, v2) = highs[-2], highs[-1]
        if p2 > p1:
            slope = (v2 - v1) / (p2 - p1)
            proj = v2 + slope * (i - p2)
            if abs(d["High"].iat[i] - proj) <= 0.01 * proj and P.any_bearish_candle(d, i):
                return RuleResult("15.2", "Candle Reversal at Trendline", "sell", True, "bearish candle at resistance TL")
    return RuleResult("15.2", "Candle Reversal at Trendline", "neutral", False)


def r_15_3(d, i):  # Candle + oscillator confluence
    bull_c = P.any_bullish_candle(d, i)
    bear_c = P.any_bearish_candle(d, i)
    if not _ok(d, i, "rsi", "stoch_k", "stoch_d"):
        return RuleResult("15.3", "Candle + Oscillator Confluence", "neutral", False)
    osc_bull = (d["rsi"].iat[i] < 40 and _rising(d["rsi"], i)) or _xa_ser(d["stoch_k"], d["stoch_d"], i)
    osc_bear = (d["rsi"].iat[i] > 60 and _falling(d["rsi"], i)) or _xb_ser(d["stoch_k"], d["stoch_d"], i)
    if bull_c and osc_bull:
        return RuleResult("15.3", "Candle + Oscillator Confluence", "buy", True, f"{bull_c} + osc")
    if bear_c and osc_bear:
        return RuleResult("15.3", "Candle + Oscillator Confluence", "sell", True, f"{bear_c} + osc")
    return RuleResult("15.3", "Candle + Oscillator Confluence", "neutral", False)


# =====================================================================
# 16-18.
# =====================================================================
def r_16_1(d, i):  # Parabolic SAR flip
    if not _ok(d, i, "psar"):
        return RuleResult("16.1", "Parabolic SAR", "neutral", False)
    below_now = d["Close"].iat[i] > d["psar"].iat[i]
    below_prev = d["Close"].iat[i - 1] > d["psar"].iat[i - 1]
    if below_now and not below_prev:
        return RuleResult("16.1", "Parabolic SAR", "buy", True, "SAR flipped below price")
    if (not below_now) and below_prev:
        return RuleResult("16.1", "Parabolic SAR", "sell", True, "SAR flipped above price")
    return RuleResult("16.1", "Parabolic SAR", "neutral", False)


def r_17_1(d, i):  # Channel boundary fade (Donchian proxy)
    if i < 21 or not _ok(d, i, "roll_high20", "roll_low20"):
        return RuleResult("17.1", "Channel Boundary Fade", "neutral", False)
    near_up = d["High"].iat[i] >= d["roll_high20"].iat[i - 1] * (1 - 0.005)
    near_dn = d["Low"].iat[i] <= d["roll_low20"].iat[i - 1] * (1 + 0.005)
    if near_dn and P.any_bullish_candle(d, i):
        return RuleResult("17.1", "Channel Boundary Fade", "buy", True, "reversal at lower channel")
    if near_up and P.any_bearish_candle(d, i):
        return RuleResult("17.1", "Channel Boundary Fade", "sell", True, "reversal at upper channel")
    return RuleResult("17.1", "Channel Boundary Fade", "neutral", False)


def r_18_1(d, i):  # Trend following (200MA regime)
    if not _ok(d, i, "sma200"):
        return RuleResult("18.1", "Trend Following", "neutral", False)
    if _xa_ser(d["Close"], d["sma200"], i):
        return RuleResult("18.1", "Trend Following", "buy", True, "close crossed above 200MA")
    if _xb_ser(d["Close"], d["sma200"], i):
        return RuleResult("18.1", "Trend Following", "sell", True, "close crossed below 200MA")
    return RuleResult("18.1", "Trend Following", "neutral", False)


# =====================================================================
# REGISTRY
# =====================================================================
def _r(rid, name, cat, kind, impl, strength, fn):
    return dict(rule_id=rid, name=name, category=cat, kind=kind, impl=impl,
                strength=strength, fn=fn)


REGISTRY = [
    # 1. candlestick reversals
    _candle("1.1", "Hammer", P.hammer, "buy"),
    _candle("1.2", "Hanging Man", P.hanging_man, "sell"),
    _candle("1.3", "Bullish Engulfing", P.bullish_engulfing, "buy"),
    _candle("1.4", "Bearish Engulfing", P.bearish_engulfing, "sell"),
    _candle("1.5", "Dark Cloud Cover", P.dark_cloud, "sell"),
    _candle("1.6", "Piercing Pattern", P.piercing, "buy"),
    _candle("1.7", "Morning Star", lambda d, i: P.morning_star(d, i, False), "buy"),
    _candle("1.8", "Evening Star", lambda d, i: P.evening_star(d, i, False), "sell"),
    _candle("1.9", "Morning Doji Star", lambda d, i: P.morning_star(d, i, True), "buy"),
    _candle("1.10", "Evening Doji Star", lambda d, i: P.evening_star(d, i, True), "sell"),
    _candle("1.11", "Shooting Star", P.shooting_star, "sell", "med"),
    _candle("1.12", "Inverted Hammer", P.inverted_hammer, "buy", "med"),
    _candle("1.13", "Bullish Harami", lambda d, i: P.bullish_harami(d, i, False), "buy", "med"),
    _candle("1.14", "Bearish Harami", lambda d, i: P.bearish_harami(d, i, False), "sell", "med"),
    _candle("1.15", "Bullish Harami Cross", lambda d, i: P.bullish_harami(d, i, True), "buy"),
    _candle("1.16", "Bearish Harami Cross", lambda d, i: P.bearish_harami(d, i, True), "sell"),
    _candle("1.17", "Tweezers Top", P.tweezers_top, "sell", "med"),
    _candle("1.18", "Tweezers Bottom", P.tweezers_bottom, "buy", "med"),
    _candle("1.19", "Three White Soldiers", P.three_white_soldiers, "buy"),
    _candle("1.20", "Three Black Crows", P.three_black_crows, "sell"),
    _candle("1.21", "Doji at Top", P.doji_top, "sell", "med"),
    _candle("1.22", "Dragonfly Doji", P.dragonfly_doji, "buy"),
    _candle("1.23", "Gravestone Doji", P.gravestone_doji, "sell"),
    _candle("1.24", "Tri-Star", lambda d, i: P.tri_star(d, i, True), "buy", "med"),
    _candle("1.25", "Bullish Belt-Hold", P.bullish_belt_hold, "buy", "med"),
    _candle("1.26", "Bearish Belt-Hold", P.bearish_belt_hold, "sell", "med"),
    # 2. continuation
    _candle("2.1", "Rising Three Methods", P.rising_three, "buy"),
    _candle("2.2", "Falling Three Methods", P.falling_three, "sell"),
    _candle("2.3", "Window Up", P.window_up, "buy", "med"),
    _candle("2.4", "Window Down", P.window_down, "sell", "med"),
    # 3. oscillators
    _r("3.1", "RSI Oversold Reversal", "oscillator", "entry", "clean", "high", r_3_1),
    _r("3.2", "RSI Overbought Reversal", "oscillator", "exit", "clean", "high", r_3_2),
    _r("3.3", "RSI Bullish Divergence", "oscillator", "entry", "heuristic", "high", r_3_3),
    _r("3.4", "RSI Bearish Divergence", "oscillator", "exit", "heuristic", "high", r_3_4),
    _r("3.5", "Stochastic Oversold Buy", "oscillator", "entry", "clean", "high", r_3_5),
    _r("3.6", "Stochastic Overbought Sell", "oscillator", "exit", "clean", "high", r_3_6),
    _r("3.7", "Stochastic Bullish Divergence", "oscillator", "entry", "heuristic", "high", r_3_7),
    _r("3.8", "MACD Bullish Crossover", "oscillator", "entry", "clean", "high", r_3_8),
    _r("3.9", "MACD Bearish Crossover", "oscillator", "exit", "clean", "high", r_3_9),
    _r("3.10", "MACD-Histogram Bullish Divergence", "oscillator", "entry", "heuristic", "high", r_3_10),
    _r("3.11", "MACD-Histogram Bearish Divergence", "oscillator", "exit", "heuristic", "high", r_3_11),
    _r("3.12", "MACD Zero-Line Bullish Cross", "oscillator", "entry", "clean", "med", r_3_12),
    # 4. elder
    _r("4.1", "Elder-Ray Bull Power Buy", "elder", "entry", "clean", "high", r_4_1),
    _r("4.2", "Elder-Ray Bear Power Sell", "elder", "exit", "clean", "high", r_4_2),
    _r("4.3", "Force Index 2-Day Buy", "elder", "entry", "clean", "high", r_4_3),
    _r("4.4", "Force Index 13-Day Trend", "elder", "filter", "clean", "med", r_4_4),
    # 5. triple screen
    _r("5.1", "Elder Triple Screen", "system", "entry", "heuristic", "high", r_5_1),
    # 6. moving averages
    _r("6.1", "MA Support Bounce", "ma", "entry", "clean", "high", r_6_1),
    _r("6.2", "Golden Cross", "ma", "entry", "clean", "high", r_6_2),
    _r("6.3", "Death Cross", "ma", "exit", "clean", "high", r_6_3),
    _r("6.4", "Triple MA Crossover (3/9/18)", "ma", "entry", "clean", "med", r_6_4),
    _r("6.5", "13-Day EMA Trend Filter", "ma", "filter", "clean", "med", r_6_5),
    # 7. bollinger
    _r("7.1", "Bollinger Band Squeeze", "bollinger", "level", "clean", "high", r_7_1),
    _r("7.2", "Bollinger Band Upper Walk", "bollinger", "entry", "clean", "med", r_7_2),
    _r("7.3", "Bollinger Band Lower Walk", "bollinger", "exit", "clean", "med", r_7_3),
    _r("7.4", "Bollinger Band Target", "bollinger", "entry", "clean", "med", r_7_4),
    _r("7.5", "Envelope Overextension", "bollinger", "entry", "clean", "med", r_7_5),
    # 8. pivots
    _r("8.1", "Daily Pivot Levels", "pivot", "level", "clean", "high", r_8_1),
    _r("8.2", "Pivot Support Bounce", "pivot", "entry", "clean", "high", r_8_2),
    _r("8.3", "Pivot Resistance Rejection", "pivot", "exit", "clean", "high", r_8_3),
    # 9. chart patterns
    _r("9.1", "Head and Shoulders Top", "chart", "exit", "heuristic", "high", r_9_1),
    _r("9.2", "Inverse Head and Shoulders", "chart", "entry", "heuristic", "high", r_9_2),
    _r("9.3", "Double Top", "chart", "exit", "heuristic", "high", r_9_3),
    _r("9.4", "Double Bottom", "chart", "entry", "heuristic", "high", r_9_4),
    _r("9.5", "Ascending Triangle", "chart", "entry", "heuristic", "high", r_9_5),
    _r("9.6", "Descending Triangle", "chart", "exit", "heuristic", "high", r_9_6),
    _r("9.7", "Bull Flag", "chart", "entry", "heuristic", "high", r_9_7),
    _r("9.8", "Bear Flag", "chart", "exit", "heuristic", "high", r_9_8),
    # 10. brooks
    _r("10.1", "Trend Bar Momentum", "price_action", "entry", "clean", "high", r_10_1),
    _r("10.2", "Two-Bar Reversal", "price_action", "entry", "clean", "high", r_10_2),
    _r("10.3", "Inside Bar Breakout", "price_action", "entry", "clean", "med", r_10_3),
    _r("10.4", "Outside Bar Reversal", "price_action", "entry", "clean", "med", r_10_4),
    _r("10.5", "Breakout Pullback", "price_action", "entry", "heuristic", "high", r_10_5),
    _r("10.6", "Measured Move", "price_action", "level", "heuristic", "med", r_10_6),
    _r("10.7", "Micro Channel Break", "price_action", "entry", "heuristic", "med", r_10_7),
    # 11. farley
    _r("11.1", "NR7 Breakout", "swing", "entry", "clean", "high", r_11_1),
    _r("11.2", "First Rise / First Failure", "swing", "entry", "heuristic", "med", r_11_2),
    _r("11.3", "Power Spike", "swing", "entry", "clean", "high", r_11_3),
    _r("11.4", "Cross-Verification", "swing", "entry", "heuristic", "high", r_11_4),
    # 12. volume
    _r("12.1", "Volume-Trend Confirmation", "volume", "filter", "clean", "high", r_12_1),
    _r("12.2", "Volume Precedes Breakout", "volume", "entry", "clean", "high", r_12_2),
    _r("12.3", "Volume Dry-Up", "volume", "level", "clean", "high", r_12_3),
    # 13. can slim
    _na_rule("13.1", "CAN SLIM C (Current Earnings)", "fundamental",
             "needs quarterly EPS (not in OHLCV) — not evaluated"),
    _na_rule("13.2", "CAN SLIM A (Annual Earnings)", "fundamental",
             "needs annual EPS (not in OHLCV) — not evaluated"),
    _r("13.3", "CAN SLIM N (New High Breakout)", "canslim", "entry", "clean", "high", r_13_3),
    _r("13.4", "CAN SLIM S (Supply/Demand)", "canslim", "filter", "clean", "high", r_13_4),
    _na_rule("13.5", "CAN SLIM L (Relative Strength)", "context",
             "needs cross-sectional RS vs benchmark — engine computes with benchmark"),
    _na_rule("13.6", "CAN SLIM M (Market Direction)", "context",
             "needs index regime/distribution days — engine computes on benchmark"),
    _r("13.7", "Cup-with-Handle Breakout", "canslim", "entry", "heuristic", "high", r_13_7),
    # 14. rosenbloom
    _r("14.1", "Impulse Buy", "momentum", "entry", "heuristic", "high", r_14_1),
    _r("14.2", "Momentum Divergence Warning", "momentum", "exit", "heuristic", "high", r_14_2),
    _r("14.3", "Fibonacci Confluence Zone", "momentum", "entry", "heuristic", "high", r_14_3),
    # 15. combined
    _r("15.1", "Bullish Candle at MA Support", "combined", "entry", "clean", "high", r_15_1),
    _r("15.2", "Candle Reversal at Trendline", "combined", "entry", "heuristic", "high", r_15_2),
    _r("15.3", "Candle + Oscillator Confluence", "combined", "entry", "clean", "high", r_15_3),
    # 16-18
    _r("16.1", "Parabolic SAR", "trailing", "exit", "clean", "med", r_16_1),
    _r("17.1", "Channel Boundary Fade", "channel", "entry", "heuristic", "med", r_17_1),
    _r("18.1", "Trend Following", "trend", "filter", "clean", "high", r_18_1),
]

REGISTRY_BY_ID = {r["rule_id"]: r for r in REGISTRY}


def evaluate_all(d, i=-1, disabled=None) -> list[RuleResult]:
    """Run every rule at position i (default last bar). Returns only FIRED results.
    `disabled` is a set/list of rule_ids to skip (pruned rules)."""
    if i < 0:
        i = len(d) + i
    disabled = set(disabled or ())
    out = []
    for r in REGISTRY:
        if r["rule_id"] in disabled:
            continue
        try:
            res = r["fn"](d, i)
            if res.fired:
                res.extra["impl"] = r["impl"]
                res.extra["strength"] = r["strength"]
                res.extra["category"] = r["category"]
                res.extra["kind"] = r["kind"]
                out.append(res)
        except Exception:
            continue
    return out
