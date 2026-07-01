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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.config import load_config
from engine.datafeed import DataFeed
from engine.advisor import analyze

WEB = ROOT / "web"
# Full NSE list (~2000 names) if present, else the curated fallback.
_symfile = WEB / "symbols_full.json"
if not _symfile.exists():
    _symfile = WEB / "symbols.json"
SYMBOLS = json.loads(_symfile.read_text(encoding="utf-8"))
NAME_BY_SYM = {x["s"]: x["n"] for x in SYMBOLS}

_CFG = load_config(); _CFG["mode"] = "eod"; _CFG["data"]["eod_period"] = "2y"
_FEED = DataFeed(_CFG)

# in-memory result cache so repeated/concurrent requests don't re-hit the feed
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 900  # seconds
_LOCK = threading.Lock()


def cached_analyze(sym: str) -> dict:
    now = time.time()
    with _LOCK:
        hit = _CACHE.get(sym)
        if hit and now - hit[0] < _CACHE_TTL:
            return hit[1]
    res = analyze(sym, _FEED, _CFG, name=NAME_BY_SYM.get(sym))
    with _LOCK:
        _CACHE[sym] = (now, res)
    return res


def suggest(q: str, limit=10):
    q = (q or "").strip().upper()
    if not q:
        return []
    starts, contains = [], []
    for x in SYMBOLS:
        s, n = x["s"].upper(), x["n"].upper()
        if s.startswith(q) or n.startswith(q):
            starts.append(x)
        elif q in s or q in n:
            contains.append(x)
    return (starts + contains)[:limit]


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

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/suggest":
                self._send(200, json.dumps(suggest(qs.get("q", [""])[0])))
            elif u.path == "/api/analyze":
                sym = qs.get("symbol", [""])[0].strip().upper()
                if not sym:
                    self._send(400, json.dumps({"ok": False, "error": "No symbol given."})); return
                self._send(200, json.dumps(cached_analyze(sym)))
            else:
                self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:  # never 500 the whole app
            self._send(200, json.dumps({"ok": False, "error": f"Server error: {e}"}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Genie TA server running on {args.host}:{args.port} "
          f"({len(SYMBOLS)} symbols)   (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
