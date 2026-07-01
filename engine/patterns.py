"""Pattern primitives: candle anatomy, trend context, candlestick detectors,
swing/pivot detection, and (heuristic) chart-pattern detectors.

Everything evaluates at integer position `i` against an indicator-enriched df
(see indicators.compute_indicators). Functions read precomputed columns; they
never look past bar `i`.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# Tunable thresholds — surfaced in the Phase B mapping for review.
PARAMS = {
    "doji_frac": 0.10,      # body <= 10% of range  -> doji
    "small_frac": 0.50,     # body <= 50% of avg prior-10 body -> "small" body
    "long_frac": 1.00,      # body >= 1.0x avg prior-10 body AND >=50% of range -> "long"
    "shadow_ratio": 2.0,    # hammer/shooting-star shadow vs body
    "near_extreme": 0.30,   # close within 30% of range from an extreme -> "near"
    "tiny_shadow": 0.10,    # shadow <= 10% of range -> "no/short" shadow
    "trend_k": 5,           # bars back used to define prior up/down context
    "tweezer_tol": 0.0015,  # 0.15% high/low match tolerance
    "level_tol": 0.02,      # 2% tolerance for "approximately equal" peaks/troughs
}


# ---------------- anatomy accessors ----------------
def _g(d, col, i):
    return float(d[col].iat[i])


def body(d, i): return _g(d, "body", i)
def rng(d, i): return _g(d, "rng", i)
def upsh(d, i): return _g(d, "upper_sh", i)
def dnsh(d, i): return _g(d, "lower_sh", i)
def is_white(d, i): return bool(d["is_white"].iat[i])
def is_black(d, i): return bool(d["is_black"].iat[i])
def avg_body(d, i):
    a = d["avg_body"].iat[i]
    return float(a) if pd.notna(a) else np.nan


def is_doji(d, i):
    r = rng(d, i)
    return r > 0 and body(d, i) <= PARAMS["doji_frac"] * r


def is_small_body(d, i):
    a = avg_body(d, i)
    return pd.notna(a) and a > 0 and body(d, i) <= PARAMS["small_frac"] * a


def is_long_body(d, i):
    a = avg_body(d, i)
    r = rng(d, i)
    return (pd.notna(a) and a > 0 and body(d, i) >= PARAMS["long_frac"] * a
            and r > 0 and body(d, i) >= 0.5 * r)


def closes_near_high(d, i):
    r = rng(d, i)
    return r > 0 and (_g(d, "High", i) - _g(d, "Close", i)) <= PARAMS["near_extreme"] * r


def closes_near_low(d, i):
    r = rng(d, i)
    return r > 0 and (_g(d, "Close", i) - _g(d, "Low", i)) <= PARAMS["near_extreme"] * r


# ---------------- trend context ----------------
def prior_downtrend(d, i, k=None):
    """Decline INTO bar i: close before the pattern is below close k bars earlier
    and below the 13-EMA. Robust, cheap proxy for 'after a decline'."""
    k = k or PARAMS["trend_k"]
    j = i - 1
    if j - k < 0:
        return False
    declined = _g(d, "Close", j) < _g(d, "Close", j - k)
    below = _g(d, "Close", j) < _g(d, "ema_trend", j) if pd.notna(d["ema_trend"].iat[j]) else declined
    return declined and below


def prior_uptrend(d, i, k=None):
    k = k or PARAMS["trend_k"]
    j = i - 1
    if j - k < 0:
        return False
    advanced = _g(d, "Close", j) > _g(d, "Close", j - k)
    above = _g(d, "Close", j) > _g(d, "ema_trend", j) if pd.notna(d["ema_trend"].iat[j]) else advanced
    return advanced and above


# ---------------- single/two/three-bar candlestick detectors ----------------
# Each returns True if the pattern completes AT bar i.

def hammer(d, i):
    if not prior_downtrend(d, i):
        return False
    b, r = body(d, i), rng(d, i)
    return (r > 0 and b > 0 and dnsh(d, i) >= PARAMS["shadow_ratio"] * b
            and upsh(d, i) <= PARAMS["tiny_shadow"] * r and is_small_body(d, i))


def hanging_man(d, i):
    if not prior_uptrend(d, i):
        return False
    b, r = body(d, i), rng(d, i)
    return (r > 0 and b > 0 and dnsh(d, i) >= PARAMS["shadow_ratio"] * b
            and upsh(d, i) <= PARAMS["tiny_shadow"] * r and is_small_body(d, i))


def shooting_star(d, i):
    if not prior_uptrend(d, i):
        return False
    b, r = body(d, i), rng(d, i)
    return (r > 0 and b > 0 and upsh(d, i) >= PARAMS["shadow_ratio"] * b
            and dnsh(d, i) <= PARAMS["tiny_shadow"] * r and is_small_body(d, i))


def inverted_hammer(d, i):
    if not prior_downtrend(d, i):
        return False
    b, r = body(d, i), rng(d, i)
    return (r > 0 and b > 0 and upsh(d, i) >= PARAMS["shadow_ratio"] * b
            and dnsh(d, i) <= PARAMS["tiny_shadow"] * r and is_small_body(d, i))


def bullish_engulfing(d, i):
    if i < 1 or not prior_downtrend(d, i):
        return False
    return (is_black(d, i - 1) and is_white(d, i)
            and _g(d, "Close", i) >= _g(d, "Open", i - 1)
            and _g(d, "Open", i) <= _g(d, "Close", i - 1)
            and body(d, i) > body(d, i - 1))


def bearish_engulfing(d, i):
    if i < 1 or not prior_uptrend(d, i):
        return False
    return (is_white(d, i - 1) and is_black(d, i)
            and _g(d, "Open", i) >= _g(d, "Close", i - 1)
            and _g(d, "Close", i) <= _g(d, "Open", i - 1)
            and body(d, i) > body(d, i - 1))


def _midpoint(d, i):
    return (_g(d, "Open", i) + _g(d, "Close", i)) / 2.0


def dark_cloud(d, i):
    if i < 1 or not prior_uptrend(d, i):
        return False
    return (is_white(d, i - 1) and is_long_body(d, i - 1) and is_black(d, i)
            and _g(d, "Open", i) > _g(d, "High", i - 1)
            and _g(d, "Close", i) < _midpoint(d, i - 1)
            and _g(d, "Close", i) > _g(d, "Open", i - 1))


def piercing(d, i):
    if i < 1 or not prior_downtrend(d, i):
        return False
    return (is_black(d, i - 1) and is_long_body(d, i - 1) and is_white(d, i)
            and _g(d, "Open", i) < _g(d, "Low", i - 1)
            and _g(d, "Close", i) > _midpoint(d, i - 1)
            and _g(d, "Close", i) < _g(d, "Open", i - 1))


def morning_star(d, i, doji=False):
    if i < 2 or not prior_downtrend(d, i - 1):
        return False
    star_ok = is_doji(d, i - 1) if doji else is_small_body(d, i - 1)
    return (is_black(d, i - 2) and is_long_body(d, i - 2) and star_ok
            and max(_g(d, "Open", i - 1), _g(d, "Close", i - 1)) < _g(d, "Close", i - 2)
            and is_white(d, i)
            and _g(d, "Close", i) > _midpoint(d, i - 2))


def evening_star(d, i, doji=False):
    if i < 2 or not prior_uptrend(d, i - 1):
        return False
    star_ok = is_doji(d, i - 1) if doji else is_small_body(d, i - 1)
    return (is_white(d, i - 2) and is_long_body(d, i - 2) and star_ok
            and min(_g(d, "Open", i - 1), _g(d, "Close", i - 1)) > _g(d, "Close", i - 2)
            and is_black(d, i)
            and _g(d, "Close", i) < _midpoint(d, i - 2))


def bullish_harami(d, i, cross=False):
    if i < 1 or not prior_downtrend(d, i):
        return False
    inside = (_g(d, "body_top", i) <= _g(d, "Open", i - 1)
              and _g(d, "body_bot", i) >= _g(d, "Close", i - 1))
    small = is_doji(d, i) if cross else is_small_body(d, i)
    return is_black(d, i - 1) and is_long_body(d, i - 1) and inside and small


def bearish_harami(d, i, cross=False):
    if i < 1 or not prior_uptrend(d, i):
        return False
    inside = (_g(d, "body_top", i) <= _g(d, "Close", i - 1)
              and _g(d, "body_bot", i) >= _g(d, "Open", i - 1))
    small = is_doji(d, i) if cross else is_small_body(d, i)
    return is_white(d, i - 1) and is_long_body(d, i - 1) and inside and small


def tweezers_top(d, i):
    if i < 1 or not prior_uptrend(d, i):
        return False
    h0, h1 = _g(d, "High", i - 1), _g(d, "High", i)
    return abs(h0 - h1) <= PARAMS["tweezer_tol"] * h0


def tweezers_bottom(d, i):
    if i < 1 or not prior_downtrend(d, i):
        return False
    l0, l1 = _g(d, "Low", i - 1), _g(d, "Low", i)
    return abs(l0 - l1) <= PARAMS["tweezer_tol"] * l0


def three_white_soldiers(d, i):
    if i < 2:
        return False
    for j in (i - 2, i - 1, i):
        if not (is_white(d, j) and is_long_body(d, j) and closes_near_high(d, j)):
            return False
    return (_g(d, "Close", i) > _g(d, "Close", i - 1) > _g(d, "Close", i - 2)
            and _g(d, "Open", i - 1) > _g(d, "Open", i - 2)
            and _g(d, "Open", i) > _g(d, "Open", i - 1))


def three_black_crows(d, i):
    if i < 2:
        return False
    for j in (i - 2, i - 1, i):
        if not (is_black(d, j) and is_long_body(d, j) and closes_near_low(d, j)):
            return False
    return (_g(d, "Close", i) < _g(d, "Close", i - 1) < _g(d, "Close", i - 2)
            and _g(d, "Open", i - 1) < _g(d, "Open", i - 2)
            and _g(d, "Open", i) < _g(d, "Open", i - 1))


def doji_top(d, i):
    return prior_uptrend(d, i) and is_doji(d, i)


def dragonfly_doji(d, i):
    r = rng(d, i)
    return (is_doji(d, i) and r > 0 and dnsh(d, i) >= 0.6 * r
            and upsh(d, i) <= PARAMS["tiny_shadow"] * r and prior_downtrend(d, i))


def gravestone_doji(d, i):
    r = rng(d, i)
    return (is_doji(d, i) and r > 0 and upsh(d, i) >= 0.6 * r
            and dnsh(d, i) <= PARAMS["tiny_shadow"] * r and prior_uptrend(d, i))


def tri_star(d, i, bullish=True):
    if i < 2:
        return False
    if not (is_doji(d, i - 2) and is_doji(d, i - 1) and is_doji(d, i)):
        return False
    if bullish:
        return (prior_downtrend(d, i - 1)
                and _g(d, "Low", i - 1) < _g(d, "Low", i - 2)
                and _g(d, "Low", i - 1) < _g(d, "Low", i))
    return (prior_uptrend(d, i - 1)
            and _g(d, "High", i - 1) > _g(d, "High", i - 2)
            and _g(d, "High", i - 1) > _g(d, "High", i))


def bullish_belt_hold(d, i):
    r = rng(d, i)
    return (prior_downtrend(d, i) and is_white(d, i) and is_long_body(d, i)
            and _g(d, "Open", i) == _g(d, "Low", i) and closes_near_high(d, i)) \
        or (prior_downtrend(d, i) and is_white(d, i) and is_long_body(d, i)
            and dnsh(d, i) <= PARAMS["tiny_shadow"] * r and closes_near_high(d, i))


def bearish_belt_hold(d, i):
    r = rng(d, i)
    return (prior_uptrend(d, i) and is_black(d, i) and is_long_body(d, i)
            and upsh(d, i) <= PARAMS["tiny_shadow"] * r and closes_near_low(d, i))


# continuation
def rising_three(d, i):
    if i < 4:
        return False
    d1 = i - 4
    if not (is_white(d, d1) and is_long_body(d, d1)):
        return False
    for j in (i - 3, i - 2, i - 1):  # three small pullback bars within day1 range
        if not (_g(d, "High", j) <= _g(d, "High", d1) and _g(d, "Low", j) >= _g(d, "Low", d1)):
            return False
    return is_white(d, i) and _g(d, "Close", i) > _g(d, "Close", d1)


def falling_three(d, i):
    if i < 4:
        return False
    d1 = i - 4
    if not (is_black(d, d1) and is_long_body(d, d1)):
        return False
    for j in (i - 3, i - 2, i - 1):
        if not (_g(d, "High", j) <= _g(d, "High", d1) and _g(d, "Low", j) >= _g(d, "Low", d1)):
            return False
    return is_black(d, i) and _g(d, "Close", i) < _g(d, "Close", d1)


def window_up(d, i):
    return i >= 1 and _g(d, "Low", i) > _g(d, "High", i - 1)


def window_down(d, i):
    return i >= 1 and _g(d, "High", i) < _g(d, "Low", i - 1)


# Registry of bullish/bearish candlestick reversal detectors for combo rules.
BULLISH_CANDLES = {
    "hammer": hammer, "inverted_hammer": inverted_hammer,
    "bullish_engulfing": bullish_engulfing, "piercing": piercing,
    "morning_star": lambda d, i: morning_star(d, i, False),
    "bullish_harami": lambda d, i: bullish_harami(d, i, False),
    "dragonfly_doji": dragonfly_doji, "tweezers_bottom": tweezers_bottom,
    "bullish_belt_hold": bullish_belt_hold,
}
BEARISH_CANDLES = {
    "hanging_man": hanging_man, "shooting_star": shooting_star,
    "bearish_engulfing": bearish_engulfing, "dark_cloud": dark_cloud,
    "evening_star": lambda d, i: evening_star(d, i, False),
    "bearish_harami": lambda d, i: bearish_harami(d, i, False),
    "gravestone_doji": gravestone_doji, "tweezers_top": tweezers_top,
    "bearish_belt_hold": bearish_belt_hold,
}


def any_bullish_candle(d, i):
    return next((n for n, f in BULLISH_CANDLES.items() if f(d, i)), None)


def any_bearish_candle(d, i):
    return next((n for n, f in BEARISH_CANDLES.items() if f(d, i)), None)


# ---------------- swing / pivot detection ----------------
def swing_points(d, i, lookback=120, left=3, right=3):
    """Confirmed pivots within [i-lookback, i]. A pivot needs `left` lower/higher
    bars before and `right` after, so the newest possible pivot is at i-right.
    Returns (highs, lows) as lists of (pos, price), oldest first."""
    start = max(left, i - lookback)
    highs, lows = [], []
    H, L = d["High"], d["Low"]
    for j in range(start, i - right + 1):
        hj, lj = H.iat[j], L.iat[j]
        if all(hj >= H.iat[j - k] for k in range(1, left + 1)) and \
           all(hj >= H.iat[j + k] for k in range(1, right + 1)):
            highs.append((j, float(hj)))
        if all(lj <= L.iat[j - k] for k in range(1, left + 1)) and \
           all(lj <= L.iat[j + k] for k in range(1, right + 1)):
            lows.append((j, float(lj)))
    return highs, lows


def _indicator_divergence(d, i, col, kind, lookback=120):
    """kind='bull': price lower-low but indicator higher-low (buy).
       kind='bear': price higher-high but indicator lower-high (sell)."""
    highs, lows = swing_points(d, i, lookback)
    pts = lows if kind == "bull" else highs
    if len(pts) < 2:
        return None
    (p1, v1), (p2, v2) = pts[-2], pts[-1]
    ind1, ind2 = d[col].iat[p1], d[col].iat[p2]
    if pd.isna(ind1) or pd.isna(ind2):
        return None
    if kind == "bull" and v2 < v1 and ind2 > ind1:
        return (p1, p2)
    if kind == "bear" and v2 > v1 and ind2 < ind1:
        return (p1, p2)
    return None
