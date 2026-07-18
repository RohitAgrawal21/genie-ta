"""Daily universe scan → the reference distribution every stock is scored against.

Run once/day (offline or via a job): computes raw factors + validated
fundamentals for a liquid universe, cross-sectionally scores them, and saves
web/rankings.json (leaderboard + the raw factor distributions). The live app
loads that file; a single stock — even one NOT in the universe — is scored by
positioning its factors against the cached distribution (score_against).

All price factors are exact; fundamentals are pre-validated in fundamentals.py.
"""
from __future__ import annotations
import json
from datetime import date

import numpy as np
import pandas as pd

from . import paths
from .indicators import compute_indicators
from .factors import raw_factors, cross_sectional_scores
from .fundamentals import fetch as fetch_fund
from .datafeed import to_yf

BALANCED_WEIGHTS = {"Momentum": 0.25, "Trend": 0.20, "RelativeStrength": 0.15,
                    "LowVolatility": 0.10, "Value": 0.15, "Quality": 0.15}

RANKINGS_FILE = paths.ROOT / "web" / "rankings.json"

# factor -> (raw key, mode). mode 'pct' = percentile vs universe; 'abs' = use raw.
_FAC = {
    "Momentum": ("mom_blend", "pct"),
    "Trend": ("trend_score", "abs"),
    "RelativeStrength": ("rs_6m", "pct"),
    "LowVolatility": ("vol_ann", "pct_inv"),   # low vol -> high score
    "Value": ("value_raw", "pct"),
    "Quality": ("quality_raw", "pct"),
}


def _dist(raws: dict) -> dict:
    """Sorted raw value arrays per factor key, for percentile positioning."""
    keys = {v[0] for v in _FAC.values()}
    out = {}
    for k in keys:
        vals = [r[k] for r in raws.values() if r.get(k) is not None
                and not (isinstance(r[k], float) and np.isnan(r[k]))]
        out[k] = sorted(float(v) for v in vals)
    return out


def _pctile(sorted_vals: list, x: float) -> float:
    if not sorted_vals or x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    n = len(sorted_vals)
    # fraction of universe at or below x
    import bisect
    return round(bisect.bisect_right(sorted_vals, x) / n * 100, 1)


def score_against(raw: dict, dist: dict, weights: dict = None) -> dict:
    """Score ONE stock's raw factors against a cached universe distribution."""
    weights = weights or BALANCED_WEIGHTS
    sub, comp, wsum = {}, 0.0, 0.0
    for fac, wt in weights.items():
        key, mode = _FAC[fac]
        x = raw.get(key)
        if mode == "abs":
            val = x if x is not None else None
        elif mode == "pct_inv":
            arr = dist.get(key, [])
            p = _pctile(arr, x)
            val = round(100 - p, 1) if p is not None else None
        else:
            val = _pctile(dist.get(key, []), x)
        sub[fac] = val
        if val is not None and wt > 0:
            comp += val * wt
            wsum += wt
    composite = round(comp / wsum, 1) if wsum > 0 else None
    return {"genie_score": composite, "subscores": sub}


def scan(feed, cfg, symbols: list[str], with_fundamentals=True, log=None) -> dict:
    data, failed = feed.fetch_universe(symbols)
    bench_data, _ = feed.fetch_universe([cfg["benchmark"]])
    bench_close = bench_data.get(cfg["benchmark"], pd.DataFrame()).get("Close")

    raws, funds = {}, {}
    for s, df in data.items():
        if len(df) < 130:
            continue
        raws[s] = raw_factors(compute_indicators(df), bench_close)
        if with_fundamentals:
            fu = fetch_fund(s, to_yf(s), price=raws[s]["price"])
            raws[s]["value_raw"] = fu.get("value_raw")
            raws[s]["quality_raw"] = fu.get("quality_raw")
            funds[s] = {"fields": fu["fields"], "source": fu["source"],
                        "as_of": fu["as_of"], "flags": fu["flags"]}
            if log:
                log.info("scanned %s", s)

    scored = cross_sectional_scores(raws, BALANCED_WEIGHTS)
    for s in scored:
        scored[s]["fundamentals"] = funds.get(s, {}).get("fields", {})
        scored[s]["fund_source"] = funds.get(s, {}).get("source")
        scored[s]["fund_as_of"] = funds.get(s, {}).get("as_of")

    return {
        "as_of": date.today().isoformat(),
        "weights": BALANCED_WEIGHTS,
        "universe_size": len(scored),
        "failed": failed,
        "dist": _dist(raws),
        "scores": scored,
    }


def save(result: dict):
    RANKINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RANKINGS_FILE.write_text(json.dumps(result), encoding="utf-8")


def load() -> dict | None:
    if RANKINGS_FILE.exists():
        try:
            return json.loads(RANKINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None
