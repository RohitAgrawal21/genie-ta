"""Phase F: build a self-contained static dashboard.html from the JSON/CSV state.

Data is INLINED at build time (no fetch/CORS issues under file://, no backend,
no CDN). Re-run this after each cycle/backtest to refresh the dashboard.

Sections: KPIs, equity curve vs Nifty (inline SVG), open positions, latest
signals with the firing rule (the "why"), per-rule attribution, and a universe
editor (edit + download universe.txt — the no-backend way to change the list).

Run:  python scripts/build_dashboard.py   ->   opens-ready dashboard.html
"""
from __future__ import annotations
import json, sys, warnings, html
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from engine import paths
from engine.config import load_config
from engine.portfolio import load_state
from engine.analytics import compute

ROOT = paths.ROOT


def _read_json(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def esc(x):
    return html.escape(str(x))


def equity_svg(perf: pd.DataFrame, w=920, h=300, pad=40) -> str:
    if perf is None or len(perf) < 2:
        return "<p class='muted'>No performance data yet — run scripts/backtest.py.</p>"
    eq = perf["equity"].astype(float).reset_index(drop=True)
    bn = perf["benchmark"].astype(float).reset_index(drop=True)
    eq0, bn0 = eq.iloc[0], bn.dropna().iloc[0] if bn.notna().any() else None
    eq_n = eq / eq0 * 100
    bn_n = (bn / bn0 * 100) if bn0 else None
    series = [eq_n] + ([bn_n] if bn_n is not None else [])
    lo = min(s.min() for s in series) * 0.99
    hi = max(s.max() for s in series) * 1.01
    n = len(eq_n)

    def pts(s):
        out = []
        for i, v in enumerate(s):
            if pd.isna(v):
                continue
            x = pad + (w - 2 * pad) * i / (n - 1)
            y = h - pad - (h - 2 * pad) * (v - lo) / (hi - lo)
            out.append(f"{x:.1f},{y:.1f}")
        return " ".join(out)

    grid = ""
    for k in range(5):
        val = lo + (hi - lo) * k / 4
        y = h - pad - (h - 2 * pad) * k / 4
        grid += (f"<line x1='{pad}' y1='{y:.1f}' x2='{w-pad}' y2='{y:.1f}' class='grid'/>"
                 f"<text x='{pad-6}' y='{y+3:.1f}' class='axis' text-anchor='end'>{val:.0f}</text>")
    base = h - pad - (h - 2 * pad) * (100 - lo) / (hi - lo)
    legend = ("<rect x='{x}' y='14' width='12' height='3' class='eq'/>"
              "<text x='{x2}' y='20' class='axis'>Strategy</text>").format(x=w-220, x2=w-204)
    if bn_n is not None:
        legend += ("<rect x='{x}' y='28' width='12' height='3' class='bn'/>"
                   "<text x='{x2}' y='34' class='axis'>Nifty</text>").format(x=w-220, x2=w-204)
    poly = f"<polyline points='{pts(eq_n)}' class='eq' fill='none'/>"
    if bn_n is not None:
        poly += f"<polyline points='{pts(bn_n)}' class='bn' fill='none'/>"
    return (f"<svg viewBox='0 0 {w} {h}' class='chart'>{grid}"
            f"<line x1='{pad}' y1='{base:.1f}' x2='{w-pad}' y2='{base:.1f}' class='baseline'/>"
            f"{poly}{legend}</svg>")


def kpi(label, value, cls=""):
    return f"<div class='kpi'><div class='kpi-v {cls}'>{esc(value)}</div><div class='kpi-l'>{esc(label)}</div></div>"


def sign_cls(x):
    try:
        return "pos" if float(x) >= 0 else "neg"
    except Exception:
        return ""


def main():
    cfg = load_config()
    state = load_state(cfg)
    signals = _read_json(paths.SIGNALS_FILE, {"signals": {}, "market": {}})
    perf = pd.read_csv(paths.PERFORMANCE_FILE, parse_dates=["timestamp"]) \
        if paths.PERFORMANCE_FILE.exists() else None
    rep = compute(state, cfg) if state.get("trade_log") else {"summary": {}, "per_rule": [], "exit_reasons": {}}
    s = rep["summary"]
    universe_txt = (ROOT / "universe.txt").read_text(encoding="utf-8") if (ROOT / "universe.txt").exists() else ""
    mkt = signals.get("market", {})

    # ----- KPI row -----
    kpis = "".join([
        kpi("Equity", f"{s.get('final_equity', cfg['starting_capital']):,.0f}"),
        kpi("Total Return", f"{s.get('total_return_pct', 0):+.2f}%", sign_cls(s.get('total_return_pct', 0))),
        kpi("Alpha vs Nifty", f"{s.get('alpha_vs_nifty_pct', 0):+.2f}%" if s.get('alpha_vs_nifty_pct') is not None else "n/a",
            sign_cls(s.get('alpha_vs_nifty_pct', 0) or 0)),
        kpi("Max Drawdown", f"{s.get('max_drawdown_pct', 0):.2f}%", "neg"),
        kpi("Win Rate", f"{s.get('win_rate_pct', 0):.1f}%"),
        kpi("Trades", f"{s.get('num_trades', 0)}"),
        kpi("Profit Factor", f"{s.get('profit_factor', 0)}"),
        kpi("Regime", mkt.get("regime", "n/a")),
    ])

    # ----- open positions -----
    sig_map = signals.get("signals", {})
    pos_rows = ""
    for sym, p in state.get("positions", {}).items():
        cur = sig_map.get(sym, {}).get("price")
        unreal = (cur - p["entry_price"]) * p["shares"] if cur else 0
        ret = (cur / p["entry_price"] - 1) * 100 if cur else 0
        pos_rows += (f"<tr><td>{esc(sym)}</td><td>{esc(str(p['entry_ts'])[:10])}</td>"
                     f"<td>{p['entry_price']:.1f}</td><td>{cur if cur else '—'}</td>"
                     f"<td>{p['shares']}</td><td class='{sign_cls(unreal)}'>{unreal:,.0f}</td>"
                     f"<td class='{sign_cls(ret)}'>{ret:+.1f}%</td>"
                     f"<td class='why'>{esc(', '.join(p.get('entry_rules', [])))}</td></tr>")
    if not pos_rows:
        pos_rows = "<tr><td colspan='8' class='muted'>No open positions.</td></tr>"

    # ----- latest signals (top buys / sells with the why) -----
    rows = list(sig_map.values())
    buys = sorted([r for r in rows if r.get("net_signal") == "buy"], key=lambda x: -x.get("net_score", 0))[:12]
    sells = sorted([r for r in rows if r.get("net_signal") == "sell"], key=lambda x: x.get("net_score", 0))[:12]

    def sig_rows(lst):
        out = ""
        for r in lst:
            why = ", ".join(f"{f['rule_id']} {f['name']}" for f in r.get("fired", [])
                            if f["signal"] == r["net_signal"])[:160]
            out += (f"<tr><td>{esc(r['symbol'])}</td><td>{r.get('price')}</td>"
                    f"<td class='{sign_cls(r.get('net_score',0))}'>{r.get('net_score',0)}</td>"
                    f"<td>{r.get('rs_rating') if r.get('rs_rating') is not None else '—'}</td>"
                    f"<td class='why'>{esc(why)}</td></tr>")
        return out or "<tr><td colspan='5' class='muted'>None.</td></tr>"

    # ----- per-rule -----
    rule_rows = ""
    for r in rep["per_rule"]:
        rule_rows += (f"<tr><td>{esc(r['rule_id'])}</td><td>{esc(r['name'])}</td>"
                      f"<td>{esc(r['impl'])}</td><td>{r['trades']}</td>"
                      f"<td>{r['win_rate_pct']:.0f}%</td>"
                      f"<td class='{sign_cls(r['net_pnl'])}'>{r['net_pnl']:,.0f}</td>"
                      f"<td class='{sign_cls(r['avg_ret_pct'])}'>{r['avg_ret_pct']:+.1f}%</td></tr>")
    if not rule_rows:
        rule_rows = "<tr><td colspan='7' class='muted'>No closed trades yet.</td></tr>"

    gen = signals.get("generated_at", "—")
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TA Paper-Trading Engine — Dashboard</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--tx:#e6edf3;--mut:#8b949e;--pos:#3fb950;--neg:#f85149;--acc:#58a6ff;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:24px}}
h1{{font-size:20px;margin:0 0 4px}}h2{{font-size:15px;margin:26px 0 10px;color:var(--acc)}}
.sub{{color:var(--mut);font-size:12px;margin-bottom:18px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.kpi{{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:12px}}
.kpi-v{{font-size:19px;font-weight:600}}.kpi-l{{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.pos{{color:var(--pos)}}.neg{{color:var(--neg)}}.muted{{color:var(--mut)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--bd);border-radius:8px;overflow:hidden}}
th,td{{padding:7px 10px;text-align:left;border-bottom:1px solid var(--bd);font-size:12.5px}}
th{{color:var(--mut);font-weight:600;text-transform:uppercase;font-size:10.5px;letter-spacing:.04em}}
tr:last-child td{{border-bottom:none}}.why{{color:var(--mut);font-size:11px}}
.chart{{width:100%;background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:6px}}
.grid{{stroke:#21262d;stroke-width:1}}.baseline{{stroke:#484f58;stroke-dasharray:4 3;stroke-width:1}}
.eq{{stroke:var(--acc);stroke-width:2;fill:#58a6ff}}.bn{{stroke:#d29922;stroke-width:1.6;fill:#d29922}}
.axis{{fill:var(--mut);font-size:10px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
textarea{{width:100%;height:160px;background:#0d1117;color:var(--tx);border:1px solid var(--bd);border-radius:8px;padding:10px;font:12px monospace}}
button{{background:var(--acc);color:#0d1117;border:0;border-radius:6px;padding:8px 14px;font-weight:600;cursor:pointer;margin-top:8px}}
.note{{background:#1c2128;border-left:3px solid var(--acc);padding:10px 12px;border-radius:6px;color:var(--mut);font-size:12px;margin:8px 0}}
@media(max-width:720px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.two{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<h1>Technical Analysis Paper-Trading Engine</h1>
<div class="sub">Generated {esc(gen)} &nbsp;·&nbsp; mode {esc(signals.get('mode','—'))} &nbsp;·&nbsp;
Nifty {esc(mkt.get('price','—'))} ({esc(mkt.get('regime','—'))}) &nbsp;·&nbsp; PAPER TRADING ONLY</div>

<div class="kpis">{kpis}</div>

<h2>Equity Curve vs Nifty (rebased to 100)</h2>
{equity_svg(perf)}

<h2>Open Positions</h2>
<table><tr><th>Symbol</th><th>Entry</th><th>Entry ₹</th><th>Last ₹</th><th>Shares</th>
<th>Unreal P&L</th><th>Return</th><th>Entry rules (why)</th></tr>{pos_rows}</table>

<div class="two">
<div><h2>Top Buy Signals</h2><table><tr><th>Sym</th><th>₹</th><th>Score</th><th>RS</th><th>Why (rules fired)</th></tr>{sig_rows(buys)}</table></div>
<div><h2>Top Sell Signals</h2><table><tr><th>Sym</th><th>₹</th><th>Score</th><th>RS</th><th>Why (rules fired)</th></tr>{sig_rows(sells)}</table></div>
</div>

<h2>Per-Rule Attribution (entry participation)</h2>
<table><tr><th>Rule</th><th>Name</th><th>impl</th><th>Trades</th><th>Win%</th><th>Net P&L</th><th>Avg%</th></tr>{rule_rows}</table>

<h2>Universe Editor</h2>
<div class="note">Edit symbols below (one per line, no .NS). Click Download to save
<b>universe.txt</b>, then replace the file in the project root. The engine picks it
up on the next cycle. (A static page can't write files directly — this is the
no-backend way to modify/grow your list.)</div>
<textarea id="uni">{esc(universe_txt)}</textarea><br>
<button onclick="dl()">Download universe.txt</button>
<span id="cnt" class="muted"></span>
<script>
const ta=document.getElementById('uni');
function count(){{const n=ta.value.split('\\n').filter(l=>l.trim()&&!l.trim().startsWith('#')).length;
document.getElementById('cnt').textContent=' '+n+' symbols';}}
ta.addEventListener('input',count);count();
function dl(){{const b=new Blob([ta.value],{{type:'text/plain'}});const a=document.createElement('a');
a.href=URL.createObjectURL(b);a.download='universe.txt';a.click();}}
</script>
</div></body></html>"""

    out = ROOT / "dashboard.html"
    out.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {out}  ({len(html_doc):,} bytes). Open it in a browser.")


if __name__ == "__main__":
    main()
