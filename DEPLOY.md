# Deploying Genie (the live TA web app)

Genie needs a **running Python backend** (it fetches live data + runs the rules engine
per request). GitHub Pages is static-only, so it can't host the engine. The pattern is:

> **Code lives on GitHub → a Python host runs it → users get a public https URL.**

The host **auto-deploys from your GitHub repo on every push.**

---

## Option A — Render.com (recommended, free, GitHub-native)

1. **Put the repo on GitHub** (see "Push to GitHub" below).
2. Go to **render.com** → sign in with GitHub.
3. **New + → Blueprint** → select this repo. Render reads [`render.yaml`](render.yaml)
   and configures everything (build = `pip install -r requirements.txt`,
   start = `python web/server.py`).
4. Click **Apply**. First build takes a few minutes. You get
   `https://genie-ta.onrender.com` (or similar).
5. Every `git push` auto-redeploys.

*Free tier note:* the service **sleeps after ~15 min idle**; the first request after
that takes ~30–60s to wake (cold start). Fine for personal use. A paid tier ($7/mo)
stays always-on.

## Option B — Railway.app (also free-ish, one command)

1. Repo on GitHub.
2. railway.app → **New Project → Deploy from GitHub repo** → pick it.
3. Railway detects Python + [`Procfile`](Procfile) (`web: python web/server.py`) and
   deploys. Add a public domain in Settings → Networking.

## Option C — Any VPS (full control, always-on)

On an Ubuntu box (DigitalOcean/Oracle-free-tier/EC2):
```bash
git clone <your-repo> && cd "Technical Analysis Engine"
pip install -r requirements.txt
PORT=80 python web/server.py        # or run behind nginx + systemd
```

---

## Push to GitHub (first time)

```bash
cd "Technical Analysis Engine"
git add -A
git commit -m "Genie: live TA web app"
gh repo create genie-ta --public --source=. --push     # needs GitHub CLI, or:
# git remote add origin https://github.com/<you>/genie-ta.git
# git branch -M main && git push -u origin main
```

---

## Run locally

```bash
python web/server.py            # http://localhost:8000
```

---

## What the user gets

- Autocomplete over **~2,000 NSE stocks** (ticker *or* company name).
- Live, per-request analysis from the same engine that powers the CLI/dashboard.
- Plain-English verdict (Buy / Hold / Wait / Avoid), 5 jargon-free cards, a price map.

## Data & limits

- Data is Yahoo Finance end-of-day (intraday is ~15 min delayed). Not tick real-time.
- Results are cached 15 min per symbol (see `web/server.py` `_CACHE_TTL`) to stay under
  rate limits when several users hit the same stock.
- Educational technical analysis — **not** investment advice.

## Optional upgrade: LLM commentary per stock

Genie's verdict is deterministic (rules engine). If you want a written, human-style
paragraph per stock, add a server-side call to the Claude API in `engine/advisor.py`
(needs an `ANTHROPIC_API_KEY` env var and costs per call). Ask and I'll wire it in.
