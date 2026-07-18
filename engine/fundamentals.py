"""Fundamentals (Tier 2) — with a hard accuracy contract.

Only fields that pass a reconciliation/sanity check are returned. Every value
carries its source and as-of date. Missing or failing fields are omitted (the UI
shows 'n/a'), NEVER guessed. Beta is NOT taken from yfinance (its India betas are
wrong); it's computed from price vs the benchmark in factors/analytics instead.

Validation:
  * trailingPE reconciles with price/EPS  (PE * EPS ~= price, <=12% off)
  * marketCap reconciles with price*shares (<=15% off) when shares available
  * ratios are bounded to sane ranges, else dropped
Cached to data/fundamentals/<sym>.json for the day so figures are stable/auditable.
"""
from __future__ import annotations
import json
from datetime import date, datetime

import yfinance as yf

from . import paths

FUND_DIR = paths.DATA_DIR / "fundamentals"


def _sane(v, lo, hi):
    try:
        v = float(v)
        return v if lo <= v <= hi else None
    except (TypeError, ValueError):
        return None


def _cache_path(symbol: str):
    safe = symbol.replace("&", "_AND_").replace("^", "_IDX_").replace("/", "_")
    return FUND_DIR / f"{safe}.json"


def fetch(symbol: str, yf_ticker: str, price: float | None = None,
          force: bool = False) -> dict:
    """Return validated fundamentals for one stock. Served from today's cache
    unless force. `price` (from our own OHLCV) is used to reconcile PE/marketCap."""
    FUND_DIR.mkdir(parents=True, exist_ok=True)
    cp = _cache_path(symbol)
    if not force and cp.exists():
        try:
            cached = json.loads(cp.read_text(encoding="utf-8"))
            if cached.get("as_of") == date.today().isoformat():
                return cached
        except Exception:
            pass

    out = {"symbol": symbol, "as_of": date.today().isoformat(),
           "source": "Yahoo Finance (yfinance)", "fields": {}, "flags": []}
    try:
        info = yf.Ticker(yf_ticker).info
    except Exception as e:
        out["flags"].append(f"fetch_failed:{str(e)[:40]}")
        cp.write_text(json.dumps(out), encoding="utf-8")
        return out

    f = out["fields"]
    pe = _sane(info.get("trailingPE"), 0, 500)
    eps = info.get("trailingEps")
    fwd_pe = _sane(info.get("forwardPE"), 0, 500)
    pb = _sane(info.get("priceToBook"), 0, 200)
    roe = _sane(info.get("returnOnEquity"), -2, 5)
    margin = _sane(info.get("profitMargins"), -2, 2)
    d2e = _sane(info.get("debtToEquity"), 0, 2000)
    eg = _sane(info.get("earningsGrowth"), -5, 20)
    rg = _sane(info.get("revenueGrowth"), -5, 20)
    dy = _sane(info.get("dividendYield"), 0, 100)
    mcap = info.get("marketCap")
    shares = info.get("sharesOutstanding")
    sector = info.get("sector")
    industry = info.get("industry")

    # --- reconciliation gates ---
    # PE must reconcile with our price and EPS (both from trustworthy sources)
    if pe is not None and eps not in (None, 0) and price:
        implied = pe * eps
        if abs(implied / price - 1) <= 0.12:
            f["pe"] = round(pe, 2)
            f["eps_ttm"] = round(float(eps), 2)
        else:
            out["flags"].append("pe_eps_price_mismatch_dropped")
    elif pe is not None and not price:
        f["pe"] = round(pe, 2)   # can't reconcile without price; keep but flag
        out["flags"].append("pe_unreconciled_no_price")

    if fwd_pe is not None:
        f["forward_pe"] = round(fwd_pe, 2)
    if pb is not None:
        f["price_to_book"] = round(pb, 2)
    if roe is not None:
        f["roe_pct"] = round(roe * 100, 1)
    if margin is not None:
        f["net_margin_pct"] = round(margin * 100, 1)
    if d2e is not None:
        f["debt_to_equity"] = round(d2e / 100 if d2e > 5 else d2e, 2)  # yfinance uses %
    if eg is not None:
        f["earnings_growth_pct"] = round(eg * 100, 1)
    if rg is not None:
        f["revenue_growth_pct"] = round(rg * 100, 1)
    if dy is not None:
        f["dividend_yield_pct"] = round(dy, 2)
    if sector:
        f["sector"] = sector
    if industry:
        f["industry"] = industry

    if mcap and price and shares:
        if abs((price * shares) / mcap - 1) <= 0.15:
            f["market_cap_cr"] = round(mcap / 1e7, 0)
        else:
            out["flags"].append("marketcap_unreconciled_dropped")
    elif mcap:
        f["market_cap_cr"] = round(mcap / 1e7, 0)

    # --- factor inputs (only from validated fields) ---
    # Value: higher = cheaper. earnings yield + book yield.
    value_raw = None
    ey = (1 / f["pe"]) if f.get("pe") else None
    by = (1 / f["price_to_book"]) if f.get("price_to_book") else None
    if ey is not None or by is not None:
        value_raw = (ey or 0) * 0.6 + (by or 0) * 0.4
    # Quality: higher = better. ROE + margin, penalise leverage.
    quality_raw = None
    if f.get("roe_pct") is not None or f.get("net_margin_pct") is not None:
        quality_raw = (f.get("roe_pct", 0) or 0) * 0.6 + (f.get("net_margin_pct", 0) or 0) * 0.4
    out["value_raw"] = value_raw
    out["quality_raw"] = quality_raw

    cp.write_text(json.dumps(out), encoding="utf-8")
    return out
