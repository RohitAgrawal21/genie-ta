"""Indicator layer. compute_indicators(df) attaches EVERY indicator column the
rule layer needs, in ONE pass, so rules never recompute. Pure functions of past
+ current bar only (no lookahead).

Input df columns: Open, High, Low, Close, Volume (Adj Close optional).
All indicator params live in DEFAULTS so they can be tuned in one place.
Stochastic is computed as the SLOW stochastic explicitly to avoid ta-library
%K/%D ambiguity: slow_%K = SMA3(fast_%K), slow_%D = SMA3(slow_%K).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from ta.momentum import RSIIndicator
from ta.trend import MACD, PSARIndicator
from ta.volatility import BollingerBands, AverageTrueRange

DEFAULTS = {
    "rsi": 14,
    "stoch_k": 14, "stoch_smooth": 3,
    "macd_fast": 12, "macd_slow": 26, "macd_sig": 9,
    "bb_window": 20, "bb_std": 2,
    "ema_fast": 3, "ema_mid": 9, "ema_slow": 18,   # triple-MA system
    "ema_trend": 13,                                # Elder 13-EMA / Elder-ray / Force Index
    "sma_short": 20, "sma_mid": 50, "sma_long": 200,
    "atr": 14,
    "force_fast": 2, "force_slow": 13,
    "vol_short": 20, "vol_long": 50,
    "env_ma": 21, "env_pct": 0.03,                  # Murphy envelope
    "body_avg_window": 10,                          # for "small"/"long" body context
}


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def compute_indicators(df: pd.DataFrame, p: dict | None = None) -> pd.DataFrame:
    p = {**DEFAULTS, **(p or {})}
    d = df.copy()
    o, h, l, c, v = d["Open"], d["High"], d["Low"], d["Close"], d["Volume"]

    # --- candle anatomy (drives every candlestick rule) ---
    d["body"] = (c - o).abs()
    d["rng"] = (h - l)
    d["upper_sh"] = h - o.combine(c, max)
    d["lower_sh"] = o.combine(c, min) - l
    d["is_white"] = (c > o)
    d["is_black"] = (c < o)
    d["body_top"] = o.combine(c, max)
    d["body_bot"] = o.combine(c, min)
    # average real body of the PRIOR n bars (shift to exclude current -> no lookahead)
    d["avg_body"] = d["body"].rolling(p["body_avg_window"]).mean().shift(1)

    # --- moving averages ---
    d["ema_trend"] = _ema(c, p["ema_trend"])            # 13 EMA
    d["ema_fast"] = _ema(c, p["ema_fast"])              # 3
    d["ema_mid"] = _ema(c, p["ema_mid"])               # 9
    d["ema_slow"] = _ema(c, p["ema_slow"])             # 18
    d["sma20"] = c.rolling(p["sma_short"]).mean()
    d["sma50"] = c.rolling(p["sma_mid"]).mean()
    d["sma200"] = c.rolling(p["sma_long"]).mean()
    d["ema20"] = _ema(c, p["sma_short"])               # for impulse/MA-support variants

    # --- RSI ---
    d["rsi"] = RSIIndicator(c, window=p["rsi"], fillna=False).rsi()

    # --- Slow Stochastic (explicit, unambiguous) ---
    ll = l.rolling(p["stoch_k"]).min()
    hh = h.rolling(p["stoch_k"]).max()
    denom = (hh - ll).replace(0, np.nan)
    fast_k = 100 * (c - ll) / denom
    d["stoch_k"] = fast_k.rolling(p["stoch_smooth"]).mean()      # slow %K
    d["stoch_d"] = d["stoch_k"].rolling(p["stoch_smooth"]).mean()  # %D

    # --- MACD(12,26,9) ---
    macd = MACD(c, window_slow=p["macd_slow"], window_fast=p["macd_fast"],
                window_sign=p["macd_sig"])
    d["macd"] = macd.macd()
    d["macd_signal"] = macd.macd_signal()
    d["macd_hist"] = macd.macd_diff()

    # --- Bollinger(20,2) ---
    bb = BollingerBands(c, window=p["bb_window"], window_dev=p["bb_std"])
    d["bb_up"] = bb.bollinger_hband()
    d["bb_mid"] = bb.bollinger_mavg()
    d["bb_dn"] = bb.bollinger_lband()
    d["bb_bw"] = (d["bb_up"] - d["bb_dn"]) / d["bb_mid"]

    # --- ATR ---
    d["atr"] = AverageTrueRange(h, l, c, window=p["atr"]).average_true_range()

    # --- Elder-ray ---
    d["bull_power"] = h - d["ema_trend"]
    d["bear_power"] = l - d["ema_trend"]

    # --- Force Index ---
    fi = (c - c.shift(1)) * v
    d["force_raw"] = fi
    d["force_ema2"] = _ema(fi.fillna(0), p["force_fast"])
    d["force_ema13"] = _ema(fi.fillna(0), p["force_slow"])

    # --- Volume baselines ---
    d["vol_sma20"] = v.rolling(p["vol_short"]).mean()
    d["vol_sma50"] = v.rolling(p["vol_long"]).mean()

    # --- Murphy envelope around 21-MA ---
    ma_env = c.rolling(p["env_ma"]).mean()
    d["env_ma"] = ma_env
    d["env_up"] = ma_env * (1 + p["env_pct"])
    d["env_dn"] = ma_env * (1 - p["env_pct"])

    # --- Parabolic SAR ---
    try:
        psar = PSARIndicator(h, l, c, step=0.02, max_step=0.2)
        d["psar"] = psar.psar()
    except Exception:
        d["psar"] = np.nan

    # --- rolling extremes for breakouts / 52wk-style logic ---
    d["roll_high20"] = h.rolling(20).max()
    d["roll_low20"] = l.rolling(20).min()
    d["roll_high252"] = h.rolling(252).max()
    d["roll_low252"] = l.rolling(252).min()

    return d
