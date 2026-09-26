# Trip Planner Agent — Gemini-Powered Web App

This is a new layer on top of the original capstone project: the same
mock flight/hotel/activity inventory, the same budget-tier and pacing
rules, but now a **real Gemini agent** holds the conversation, decides
when to call the search tools, and assembles the itinerary — instead of
the deterministic Python agent (`agent.py`) doing it with regex parsing.

Both versions live in the same repo on purpose. `agent.py` +
`eval_suite.py` + `personas.py` are the eval-tested, fully deterministic
version — keep those as-is, they're the part a hiring manager can
actually verify with `python3 eval_suite.py`. This new folder is the
"and here's what it looks like wired up to a real LLM" follow-up.

## What's in this folder

```
app.py              FastAPI server: Gemini chat sessions, tool calling, validation
mock_inventory.py   The same mock destinations/flights/hotels/activities data
tools.py            Thin wrappers around mock_inventory, exposed to Gemini as tools
validators.py       Runtime version of the eval suite's pacing/budget checks
static/index.html   Chat frontend (day-tabs itinerary view, same design system)
requirements.txt
render.yaml         One-click Render blueprint
.env.example        Copy to .env locally — never commit your real key
```

## How it actually works

1. You send a message. Gemini decides whether it has enough information
   (destination, days, budget, travelers, vibe) or needs to ask more.
2. Once it does, Gemini calls `search_flights`, `search_hotels`, and
   `search_activities` — real function calls, not simulated — which run
   the same mock data your eval suite already tests.
3. Gemini assembles a day-by-day plan and replies with a short message
   plus a fenced ` ```json ` block containing the full itinerary.
4. **The server validates that JSON** against the same pacing and
   budget-tier rules `eval_suite.py` checks (`validators.py`). If Gemini's
   plan breaks a rule — wrong number of activities for the vibe, a hotel
   tier that doesn't match the budget tier — the server automatically
   sends it back with the specific violation and asks for a fix, up to
   two tries, before showing you anything.

That last part is the piece worth pointing out in an interview: the eval
suite didn't just validate a static agent once, its logic is now a live
guardrail on a nondeterministic LLM's output.

## 1. Run it locally first

Don't skip this — deploying before you've confirmed it works locally
just moves the debugging to a slower feedback loop.

```bash
cd trip_planner_web   # or wherever you placed these files in your repo
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your real key after GEMINI_API_KEY=

export $(cat .env | xargs)       # or just: set GEMINI_API_KEY=... on Windows
uvicorn app:app --reload
```

Open **http://localhost:8000** — you should see the chat interface. Try:

```
Kyoto for 8 days, cultural vibe, $6000 for two of us
```

and watch it come back with a full itinerary. If something's wrong,
you'll see the error in your terminal (uvicorn logs every request) — much
faster to debug here than on Render.

**Quick check without the browser:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "solo trip to Bali, relaxing, 10 days, $1500"}'
```

## 2. Push this to your GitHub repo

```bash
# from your existing trip_planner repo root
cp -r /path/to/trip_planner_web/* .
git add app.py mock_inventory.py tools.py validators.py static/ requirements.txt render.yaml .env.example .gitignore README_DEPLOY.md
git commit -m "Add Gemini-powered web app alongside the deterministic agent"
git push
```

**Double-check `.env` is in `.gitignore` before you push** — if you ever
commit a real key by accident, treat it as compromised: regenerate it at
https://aistudio.google.com/apikey immediately, don't just delete the
commit (it stays in git history).

## 3. Deploy on Render

### Option A — one-click blueprint (uses `render.yaml`)

1. Go to https://dashboard.render.com → **New** → **Blueprint**.
2. Connect your GitHub account if you haven't, then select your
   `trip_planner` repo.
3. Render reads `render.yaml` automatically and shows you the service
   it's about to create. Click **Apply**.
4. It'll ask you to fill in `GEMINI_API_KEY` since the blueprint marks it
   `sync: false` on purpose (so it's never stored in the repo). Paste
   your key there.
5. Click **Deploy**. First build takes 2-4 minutes.

### Option B — manual setup (if you'd rather not use the blueprint)

1. https://dashboard.render.com → **New** → **Web Service**.
2. Connect your repo.
3. Settings:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. Under **Environment**, add:
   - `GEMINI_API_KEY` = your real key
5. **Create Web Service**.

Either way, once it's live you'll get a public URL like
`https://trip-planner-agent.onrender.com` — that's the link you share
with anyone.

## 4. Things worth knowing about the free tier

- **Cold starts**: Render's free plan spins your service down after
  ~15 minutes of no traffic. The first request after that takes
  20-50 seconds while it wakes back up — normal, not a bug. If you're
  demoing this live, open the link a minute before you need it.
- **Sessions reset on restart**: conversations are held in memory
  (`_SESSIONS` in `app.py`). A redeploy or a free-tier restart clears
  them, so anyone mid-conversation has to start over. Fine for a
  portfolio demo; if you want this to survive restarts, the fix is
  swapping that in-memory dict for Redis or a database table — a good
  "next step" to mention if asked about production-readiness.
- **API costs**: Gemini's free tier has generous per-minute/per-day
  limits, but a public link means anyone can use your key's quota. Keep
  an eye on usage at https://aistudio.google.com if you share this
  widely, and consider adding basic rate-limiting if it gets real
  traffic.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "GEMINI_API_KEY is not set on the server" | Env var missing on Render — check the Environment tab |
| 502 "Gemini API error: 403" | Bad or expired API key — regenerate at AI Studio |
| Itinerary never appears, just keeps asking questions | Check your uvicorn/Render logs for the actual model reply — it may be waiting on a field you haven't given it yet (all five: destination, days, budget, travelers, vibe) |
| Same broken itinerary shown twice | The correction loop caps at 2 retries (`MAX_CORRECTION_ATTEMPTS` in `app.py`) — raise it if needed, but 2 is usually enough and keeps latency reasonable |
