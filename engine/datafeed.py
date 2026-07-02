"""DataFeed: batched, cached, rate-limit-resilient OHLCV fetcher.

Design goals (the loop must NEVER crash on a data problem):
  * Batch many tickers into one yfinance HTTP call (the #1 lever vs rate limits).
  * Cache every symbol to its own CSV; reuse within the same bar (no refetch).
  * Exponential backoff + retry on transient failures; split a failing batch once.
  * Per-symbol extraction so a partial batch (some tickers NaN) still yields data.
  * Skip + log dead tickers; return them so the caller can report, never raise.

Columns are normalized to: Open, High, Low, Close, Adj Close, Volume
Index: tz-naive DatetimeIndex named 'Datetime', ascending.
"""
from __future__ import annotations
import json
import time as _time
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import yfinance as yf

from . import paths
from .logutil import get_logger

_OHLCV = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

# poll_minutes -> nearest valid yfinance intraday interval
_VALID_INTRADAY = [1, 2, 5, 15, 30, 60, 90]


def _nearest_interval(poll_minutes: int) -> str:
    best = min(_VALID_INTRADAY, key=lambda v: abs(v - poll_minutes))
    return f"{best}m"


def to_yf(symbol: str) -> str:
    """Bare NSE symbol -> yfinance ticker. Anything already carrying an exchange
    suffix (RELIANCE.NS, MRTX.BO) or an index (^NSEI) passes through unchanged."""
    s = symbol.strip().upper()
    if s.startswith("^") or "." in s:
        return s
    return f"{s}.NS"


class DataFeed:
    def __init__(self, config: dict, logger=None):
        self.cfg = config
        self.dcfg = config["data"]
        self.log = logger or get_logger("datafeed")
        self.mode = config["mode"]
        if self.mode == "eod":
            self.interval = self.dcfg["eod_interval"]
            self.period = self.dcfg["eod_period"]
            self.bar_seconds = 24 * 3600
        else:
            self.interval = _nearest_interval(int(config["poll_minutes"]))
            self.period = self.dcfg["intraday_period"]
            self.bar_seconds = int(config["poll_minutes"]) * 60
        self.tz = config["timezone"]
        paths.ensure_dirs()
        self._meta = self._load_meta()

    # ---------- cache metadata ----------
    def _load_meta(self) -> dict:
        if paths.CACHE_META_FILE.exists():
            try:
                return json.loads(paths.CACHE_META_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_meta(self) -> None:
        paths.CACHE_META_FILE.write_text(json.dumps(self._meta, indent=2), encoding="utf-8")

    def _cache_path(self, symbol: str) -> Path:
        safe = symbol.replace("^", "_IDX_").replace("&", "_AND_")
        return paths.CACHE_DIR / f"{safe}__{self.mode}__{self.interval}.csv"

    def _is_fresh(self, symbol: str) -> bool:
        meta = self._meta.get(self._cache_key(symbol))
        if not meta or not self._cache_path(symbol).exists():
            return False
        last = meta.get("last_fetch")
        if not last:
            return False
        try:
            last_dt = datetime.fromisoformat(last)
        except Exception:
            return False
        if self.mode == "eod":
            return last_dt.date() == date.today()
        return (datetime.now() - last_dt).total_seconds() < self.bar_seconds

    def _cache_key(self, symbol: str) -> str:
        return f"{symbol}|{self.mode}|{self.interval}"

    # ---------- normalization ----------
    def _normalize(self, df: pd.DataFrame, yf_ticker: str) -> pd.DataFrame | None:
        if df is None or len(df) == 0:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            lvl0 = set(df.columns.get_level_values(0))
            if yf_ticker in lvl0:
                df = df[yf_ticker]
            else:  # group_by='column' layout: (field, ticker)
                try:
                    df = df.xs(yf_ticker, axis=1, level=1)
                except Exception:
                    df = df.droplevel(1, axis=1)
        out = pd.DataFrame(index=df.index)
        for col in _OHLCV:
            out[col] = df[col] if col in df.columns else pd.NA
        out = out.dropna(how="all")
        if len(out) == 0 or out["Close"].dropna().empty:
            return None
        out.index = pd.to_datetime(out.index)
        # Intraday bars come back tz-aware (UTC). Convert to the exchange tz so
        # bar timestamps read as IST (09:15..15:30), THEN drop tz for clean CSVs.
        # Daily bars are tz-naive dates already -> left untouched.
        if out.index.tz is not None:
            out.index = out.index.tz_convert(self.tz).tz_localize(None)
        out.index.name = "Datetime"
        return out.sort_index()

    def load_cached(self, symbol: str) -> pd.DataFrame | None:
        p = self._cache_path(symbol)
        if not p.exists():
            return None
        try:
            df = pd.read_csv(p, index_col="Datetime", parse_dates=["Datetime"])
            return df if len(df) else None
        except Exception:
            return None

    def _write_cache(self, symbol: str, df: pd.DataFrame) -> None:
        df.to_csv(self._cache_path(symbol))
        self._meta[self._cache_key(symbol)] = {
            "last_fetch": datetime.now().isoformat(timespec="seconds"),
            "rows": int(len(df)),
            "last_bar": df.index[-1].isoformat() if len(df) else None,
        }

    # ---------- network ----------
    def _download(self, yf_tickers: list[str]) -> pd.DataFrame | None:
        """One yfinance call with retry + exponential backoff. Returns raw df or None."""
        retries = int(self.dcfg["max_retries"])
        base = float(self.dcfg["backoff_base_sec"])
        for attempt in range(retries):
            try:
                df = yf.download(
                    tickers=yf_tickers,
                    period=self.period,
                    interval=self.interval,
                    group_by="ticker",
                    auto_adjust=False,
                    threads=True,
                    progress=False,
                )
                if df is not None and len(df) > 0:
                    return df
                self.log.warning("Empty response (attempt %d/%d) for %d tickers",
                                 attempt + 1, retries, len(yf_tickers))
            except Exception as e:  # noqa: BLE001 — must never crash the loop
                self.log.warning("Download error (attempt %d/%d): %s",
                                 attempt + 1, retries, e)
            if attempt < retries - 1:
                _time.sleep(base * (2 ** attempt))
        return None

    def _fetch_batch(self, symbols: list[str]) -> tuple[dict[str, pd.DataFrame], list[str]]:
        """Fetch a batch; on whole-batch failure, split once and retry halves."""
        out: dict[str, pd.DataFrame] = {}
        failed: list[str] = []
        yf_map = {to_yf(s): s for s in symbols}
        raw = self._download(list(yf_map.keys()))
        if raw is None:
            if len(symbols) > 1:  # split once, recurse
                mid = len(symbols) // 2
                for half in (symbols[:mid], symbols[mid:]):
                    o, f = self._fetch_batch(half)
                    out.update(o)
                    failed.extend(f)
                return out, failed
            return {}, list(symbols)
        for yft, sym in yf_map.items():
            norm = self._normalize(raw, yft)
            if norm is None:
                failed.append(sym)
            else:
                self._write_cache(sym, norm)
                out[sym] = norm
        return out, failed

    # ---------- public API ----------
    def fetch_universe(self, symbols: list[str], force: bool = False
                       ) -> tuple[dict[str, pd.DataFrame], list[str]]:
        """Return ({symbol: df}, failed_symbols). Serves fresh cache without a
        network call; only fetches stale/missing symbols, in batches."""
        data: dict[str, pd.DataFrame] = {}
        to_fetch: list[str] = []
        for s in symbols:
            if not force and self._is_fresh(s):
                cached = self.load_cached(s)
                if cached is not None:
                    data[s] = cached
                    continue
            to_fetch.append(s)

        if to_fetch:
            self.log.info("Fetching %d/%d symbols (%d served from fresh cache) "
                          "mode=%s interval=%s", len(to_fetch), len(symbols),
                          len(symbols) - len(to_fetch), self.mode, self.interval)
        bs = int(self.dcfg["batch_size"])
        pause = float(self.dcfg["request_pause_sec"])
        failed: list[str] = []
        for i in range(0, len(to_fetch), bs):
            batch = to_fetch[i:i + bs]
            o, f = self._fetch_batch(batch)
            data.update(o)
            failed.extend(f)
            if i + bs < len(to_fetch):
                _time.sleep(pause)
        self._save_meta()
        if failed:
            self.log.warning("Failed symbols (%d): %s", len(failed), ", ".join(failed))
        return data, failed

    def get(self, symbol: str, force: bool = False) -> pd.DataFrame | None:
        d, _ = self.fetch_universe([symbol], force=force)
        return d.get(symbol)
