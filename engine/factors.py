"""Multi-factor engine (Tier 1). Every value here is COMPUTED from OHLCV — no
third-party numbers, so it is exact and auditable. Produces raw factor values
per stock; cross_sectional_scores() then percentile-ranks them across the
universe into 0-100 sub-scores and a composite Genie Score.

Factors (Tier 1, price-only):
  Momentum          risk-adjusted 3/6/12-month return
  Trend             alignment vs 20/50/200 MAs + 200-slope (absolute 0-100)
  RelativeStrength  excess return vs the benchmark (Nifty)
  LowVolatility     annualised volatility (inverted — low-vol anomaly)
Tier 2 adds Value & Quality from validated fundamentals (see fundamentals.py).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _ret(close: pd.Series, n: int):
    if len(close) <= n or close.iat[-1 - n] <= 0:
        return np.nan
    return float(close.iat[-1] / close.iat[-1 - n] - 1)


def raw_factors(d: pd.DataFrame, bench_close: pd.Series | None = None) -> dict:
    """Raw (un-normalised) factor values for one enriched dataframe `d`
    (output of compute_indicators). All exact, from price/volume only."""
    c = d["Close"]
    n = len(d)
    px = float(c.iat[-1])
    logret = np.log(c / c.shift(1)).dropna()

    r1, r3, r6, r12 = _ret(c, 21), _ret(c, 63), _ret(c, 126), _ret(c, 252)
    vol_ann = float(logret.iloc[-126:].std() * np.sqrt(TRADING_DAYS)) if len(logret) >= 60 else np.nan

    # risk-adjusted momentum blend (6m weighted most; scaled by volatility)
    mom_blend = np.nan
    parts = [(r6, 0.5), (r12, 0.3), (r3, 0.2)]
    if all(pd.notna(v) for v, _ in parts):
        mom_blend = sum(v * w for v, w in parts)
        if pd.notna(vol_ann) and vol_ann > 0:
            mom_blend = mom_blend / vol_ann      # Sharpe-like

    # trend alignment (absolute 0-100, not cross-sectional)
    s20, s50, s200 = d["sma20"].iat[-1], d["sma50"].iat[-1], d["sma200"].iat[-1]
    slope200 = np.nan
    if n > 220 and pd.notna(d["sma200"].iat[-1]) and pd.notna(d["sma200"].iat[-21]):
        slope200 = float(d["sma200"].iat[-1] / d["sma200"].iat[-21] - 1)
    tcomp = 0.0
    if pd.notna(s20):
        tcomp += 0.15 * (px > s20)
    if pd.notna(s50):
        tcomp += 0.20 * (px > s50)
    if pd.notna(s200):
        tcomp += 0.35 * (px > s200)
        tcomp += 0.15 * (s50 > s200)             # golden alignment
    if pd.notna(slope200):
        tcomp += 0.15 * (slope200 > 0)           # long-term rising
    trend_score = round(tcomp * 100, 1)

    # relative strength vs benchmark (excess return)
    rs6 = rs12 = np.nan
    if bench_close is not None and len(bench_close) > 130:
        b6, b12 = _ret(bench_close, 126), _ret(bench_close, 252)
        if pd.notna(r6) and pd.notna(b6):
            rs6 = r6 - b6
        if pd.notna(r12) and pd.notna(b12):
            rs12 = r12 - b12

    # positioning / liquidity (reported, lightly used)
    hi = float(d["High"].iloc[-TRADING_DAYS:].max()) if n >= 60 else np.nan
    lo = float(d["Low"].iloc[-TRADING_DAYS:].min()) if n >= 60 else np.nan
    range_pos = (px - lo) / (hi - lo) if pd.notna(hi) and hi > lo else np.nan
    turnover = float((c * d["Volume"]).iloc[-20:].mean()) if n >= 20 else np.nan

    return {
        "price": round(px, 2), "bars": n,
        "ret_1m": r1, "ret_3m": r3, "ret_6m": r6, "ret_12m": r12,
        "vol_ann": vol_ann, "mom_blend": mom_blend,
        "trend_score": trend_score, "rs_6m": rs6, "rs_12m": rs12,
        "range_pos_52w": range_pos, "turnover": turnover,
        "rsi": float(d["rsi"].iat[-1]) if pd.notna(d["rsi"].iat[-1]) else np.nan,
    }


def _pct_rank(series: pd.Series) -> pd.Series:
    """Cross-sectional percentile 0-100 (higher = better). NaNs stay NaN."""
    return series.rank(pct=True) * 100


def cross_sectional_scores(raw_by_symbol: dict[str, dict],
                           weights: dict | None = None) -> dict[str, dict]:
    """Turn raw factors for the whole universe into 0-100 sub-scores + composite
    Genie Score + rank. Percentile ranking is exact given the universe."""
    if not raw_by_symbol:
        return {}
    df = pd.DataFrame(raw_by_symbol).T
    w = weights or {"Momentum": 0.30, "Trend": 0.25, "RelativeStrength": 0.20,
                    "LowVolatility": 0.15, "Value": 0.0, "Quality": 0.0}

    sub = pd.DataFrame(index=df.index)
    sub["Momentum"] = _pct_rank(df["mom_blend"].astype(float))
    sub["Trend"] = df["trend_score"].astype(float)          # already 0-100 absolute
    sub["RelativeStrength"] = _pct_rank(df["rs_6m"].astype(float))
    sub["LowVolatility"] = _pct_rank(-df["vol_ann"].astype(float))  # low vol -> high score

    # optional fundamental sub-scores if provided in raw (Tier 2)
    if "value_raw" in df.columns:
        sub["Value"] = _pct_rank(df["value_raw"].astype(float))
    if "quality_raw" in df.columns:
        sub["Quality"] = _pct_rank(df["quality_raw"].astype(float))

    out = {}
    for sym in df.index:
        parts, wsum, comp = {}, 0.0, 0.0
        for fac, wt in w.items():
            if fac in sub.columns and pd.notna(sub.at[sym, fac]) and wt > 0:
                parts[fac] = round(float(sub.at[sym, fac]), 1)
                comp += sub.at[sym, fac] * wt
                wsum += wt
            elif fac in sub.columns:
                parts[fac] = None if pd.isna(sub.at[sym, fac]) else round(float(sub.at[sym, fac]), 1)
        composite = round(comp / wsum, 1) if wsum > 0 else None
        out[sym] = {"genie_score": composite, "subscores": parts,
                    "raw": {k: (None if (isinstance(v, float) and pd.isna(v)) else v)
                            for k, v in raw_by_symbol[sym].items()}}

    # rank by composite (1 = best)
    ranked = sorted([s for s in out if out[s]["genie_score"] is not None],
                    key=lambda s: out[s]["genie_score"], reverse=True)
    for r, sym in enumerate(ranked, 1):
        out[sym]["rank"] = r
        out[sym]["rank_total"] = len(ranked)
        out[sym]["percentile"] = round((1 - (r - 1) / len(ranked)) * 100, 0) if ranked else None
    return out
