"""Tiny local web app for the TA engine — standard library only (no Flask, no
install, no database). Type a company/ticker, get a plain-English verdict.

Run:  python web/server.py          then open  http://localhost:8000
      python web/server.py --port 9000

Endpoints:
  GET /                      -> the page
  GET /api/suggest?q=rel     -> autocomplete matches (ticker or company name)
  GET /api/analyze?symbol=M&M-> full plain-English analysis (runs the engine)
"""
from __future__ import annotations
import argparse, json, os, sys, time, threading, warnings
import urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WEB = ROOT / "web"
# Full NSE list (~2000 names) if present, else the curated fallback.
_symfile = WEB / "symbols_full.json"
if not _symfile.exists():
    _symfile = WEB / "symbols.json"
SYMBOLS = json.loads(_symfile.read_text(encoding="utf-8"))
NAME_BY_SYM = {x["s"]: x["n"] for x in SYMBOLS}

# Heavy imports (pandas/ta/yfinance + engine) are LAZY so the server binds the
# port instantly and Render's health check passes — no slow-startup restarts.
# Analysis is also serialised (one at a time) to stay within the 512MB free tier.
_ENGINE = {}          # holds analyze fn, feed, cfg after first use
_ENGINE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 1800
_LOCK = threading.Lock()


def _engine():
    with _ENGINE_LOCK:
        if not _ENGINE:
            from engine.config import load_config
            from engine.datafeed import DataFeed
            from engine.advisor import analyze
            cfg = load_config(); cfg["mode"] = "eod"; cfg["data"]["eod_period"] = "1y"
            _ENGINE.update(analyze=analyze, feed=DataFeed(cfg), cfg=cfg)
        return _ENGINE


def cached_analyze(sym: str, name: str | None = None) -> dict:
    now = time.time()
    with _LOCK:
        hit = _CACHE.get(sym)
        if hit and now - hit[0] < _CACHE_TTL:
            return hit[1]
    e = _engine()
    nm = name or NAME_BY_SYM.get(sym) or NAME_BY_SYM.get(sym.rsplit(".", 1)[0])
    with _ENGINE_LOCK:  # serialise heavy work -> avoids concurrent-request OOM
        res = e["analyze"](sym, e["feed"], e["cfg"], name=nm)
    with _LOCK:
        _CACHE[sym] = (now, res)
    return res


def _clean(o):
    """Recursively replace NaN/Inf with None so browsers can JSON.parse the reply
    (Python emits bare NaN which is invalid JSON and breaks the frontend)."""
    import math
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    return o


def dumps(o) -> str:
    return json.dumps(_clean(o))


_SEARCH_CACHE: dict[str, tuple[float, list]] = {}
_SEARCH_TTL = 900


def yahoo_search(q: str) -> list:
    """Resolve any query to real NSE/BSE tickers via Yahoo's search API. This is
    how BSE-only names (e.g. Merritronix -> MRTX.BO) get found — their Yahoo
    ticker isn't guessable from the name. Cached + fails soft."""
    key = q.lower()
    now = time.time()
    hit = _SEARCH_CACHE.get(key)
    if hit and now - hit[0] < _SEARCH_TTL:
        return hit[1]
    out = []
    try:
        url = ("https://query2.finance.yahoo.com/v1/finance/search?q="
               + urllib.parse.quote(q) + "&quotesCount=10&newsCount=0")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        for it in data.get("quotes", []):
            sym = it.get("symbol", "")
            if sym.endswith(".NS") or sym.endswith(".BO"):
                out.append({"s": sym.rsplit(".", 1)[0],
                            "n": it.get("shortname") or it.get("longname") or sym,
                            "t": sym, "exch": "NSE" if sym.endswith(".NS") else "BSE"})
    except Exception:
        pass
    _SEARCH_CACHE[key] = (now, out)
    return out


def suggest(q: str, limit=10):
    q = (q or "").strip()
    if not q:
        return []
    qu = q.upper()
    exact, symstart, namestart, contains = [], [], [], []
    for x in SYMBOLS:                       # fast local NSE list first, best-ranked
        s, n = x["s"].upper(), x["n"].upper()
        item = {"s": x["s"], "n": x["n"], "t": x["s"], "exch": "NSE"}
        if s == qu:
            exact.append(item)
        elif s.startswith(qu):
            symstart.append(item)
        elif n.startswith(qu):
            namestart.append(item)
        elif qu in s or qu in n:
            contains.append(item)
    results = (exact + symstart + namestart + contains)[:limit]
    # If the local NSE list is thin on matches, ask Yahoo — this is where BSE-only
    # stocks (and anything not on NSE) come from.
    if len(results) < limit:
        have = {r["t"].upper() for r in results} | {r["s"].upper() for r in results}
        for y in yahoo_search(q):
            if y["s"].upper() not in have and y["t"].upper() not in have:
                results.append(y)
                have.add(y["s"].upper())
            if len(results) >= limit:
                break
    return results[:limit]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):  # quiet console
        pass

    def do_HEAD(self):
        # uptime monitors (UptimeRobot etc.) probe with HEAD — answer 200, no body
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        try:
            if u.path == "/healthz":
                self._send(200, "ok", "text/plain")
            elif u.path in ("/", "/index.html"):
                self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/suggest":
                self._send(200, dumps(suggest(qs.get("q", [""])[0])))
            elif u.path == "/api/analyze":
                sym = qs.get("symbol", [""])[0].strip().upper()
                nm = qs.get("name", [""])[0].strip() or None
                if not sym:
                    self._send(400, dumps({"ok": False, "error": "No symbol given."})); return
                self._send(200, dumps(cached_analyze(sym, nm)))
            else:
                self._send(404, dumps({"error": "not found"}))
        except Exception as e:  # never 500 the whole app
            self._send(200, dumps({"ok": False, "error": f"Server error: {e}"}))


_POPULAR = [  # warmed at startup so the common searches are near-instant
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "TATAMOTORS",
    "TATASTEEL", "ITC", "AXISBANK", "M&M", "BHARTIARTL", "MARUTI", "WIPRO",
    "HCLTECH", "SUNPHARMA", "TITAN", "LT", "KOTAKBANK", "BAJFINANCE", "ADANIENT",
    "HINDUNILVR", "ONGC", "NTPC", "POWERGRID", "COALINDIA", "JSWSTEEL", "VEDL",
    "ZOMATO", "IRCTC", "IRFC", "TATAPOWER", "DLF", "PNB", "BEL", "HAL",
]


def _prewarm():
    """Warm the data cache for the most-searched names in the background so the
    first user request for them doesn't pay the Yahoo fetch."""
    try:
        e = _engine()
        e["feed"].fetch_universe(_POPULAR)          # one batched fetch
        e["feed"].fetch_universe([e["cfg"]["benchmark"]])
        print(f"Pre-warmed {len(_POPULAR)} popular symbols.")
    except Exception as ex:
        print(f"Pre-warm skipped: {ex}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    ap.add_argument("--no-prewarm", action="store_true")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Genie TA server running on {args.host}:{args.port} "
          f"({len(SYMBOLS)} symbols)   (Ctrl-C to stop)")
    if not args.no_prewarm:
        threading.Thread(target=_prewarm, daemon=True).start()  # non-blocking
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
