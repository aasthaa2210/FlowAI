# FlowAI — Route Intelligence

A light, corporate-style frontend wired to your existing Python backend
(`route_analysis.py`, `ai_recommendations.py`, `notifications.py`,
`llm_assistant.py`) through a Flask API layer (`backend/app.py`), now with
accounts, saved routes, and a live map.

## What's inside

- **Login / signup** — real accounts, passwords are hashed (never stored as
  plain text), stays logged in via a session cookie.
- **Route analysis** — pick two Ahmedabad locations, hit Analyze, get live
  distance/duration, a congestion index on a tick-gauge, and the route
  drawn on a live map (Leaflet + OpenStreetMap, no API key needed).
- **Save routes** — bookmark any analyzed route to your account; view or
  delete them under "Saved routes."
- **Profile** — click your name top-right to see your account details.
- **Analyzed routes history** — every route you analyze in the session feeds
  the notifications and recommendations panels.
- **Notifications** — rule-based alerts generated from your analyzed routes.
- **AI recommendations** — LLM-generated suggestions (Groq) based on the same data.
- **Chat assistant** — floating dock, bottom right, asks your `llm_assistant.py`.

## 0. First-time setup (do this once)

```bash
cd backend
pip install -r requirements.txt
```

Create a file called `.env` inside the `backend` folder (copy
`.env.example` and rename it, or just create a new file called exactly
`.env`) with your real keys:
```
ORS_API_KEY=your-real-key
GEMINI_API_KEY=your-real-key
GROQ_API_KEY=your-real-key
SECRET_KEY=any-random-string-you-make-up
```
`SECRET_KEY` signs your login sessions — any random text works locally,
e.g. `SECRET_KEY=hopefully-random-abc123`.

A local database file (`flowai.db`) is created automatically the first
time you run the server — this is where accounts and saved routes live.
Delete that file any time to wipe all accounts and start fresh.

## 1. Run the backend

```bash
cd backend
python app.py
```

Starts the API at **http://localhost:5000**. Endpoints:

| Endpoint                | Method | Purpose                                   |
|--------------------------|--------|--------------------------------------------|
| `/api/health`            | GET    | Check the server is up                     |
| `/api/auth/signup`       | POST   | Create an account                          |
| `/api/auth/login`        | POST   | Log in                                     |
| `/api/auth/logout`       | POST   | Log out                                    |
| `/api/auth/me`           | GET    | Check who's currently logged in            |
| `/api/route`             | POST   | Calls `get_route()` — distance/duration/congestion/map geometry |
| `/api/routes/save`       | POST   | Save a route to the logged-in account      |
| `/api/routes/mine`       | GET    | List the logged-in account's saved routes  |
| `/api/routes/<id>`       | DELETE | Delete one saved route                     |
| `/api/recommendations`   | POST   | Calls `get_recommendations()` — AI advice via Groq |
| `/api/notifications`     | POST   | Calls `generate_notifications()` — rule-based alerts |
| `/api/chat`              | POST   | Calls `ask_traffic_assistant()` — chat assistant   |

Your original `route_analysis.py` / `ai_recommendations.py` /
`notifications.py` / `llm_assistant.py` logic is untouched aside from
`route_analysis.py` now also returning the route's map geometry, and
timeouts added so a network hiccup fails fast instead of hanging forever.

## 2. Run the frontend

Plain HTML/CSS/JS, no build step:

```bash
cd frontend
python3 -m http.server 8080
```

Visit **http://localhost:8080**. It calls the API at
`http://localhost:5000/api` (edit `API_BASE` near the top of `app.js` once
you deploy the backend elsewhere).

## Notes

- Your original `config.py` had real keys typed directly into it — that's
  now replaced with reading from environment variables (the `.env` file
  locally, or your hosting platform's dashboard once deployed). Keys
  should never sit in code that could end up shared or uploaded anywhere.
- If any of your ORS / Gemini / Groq keys were ever pasted somewhere public
  (a chat, a public repo, etc.), rotate them from each provider's dashboard.
- The location list in `app.js` (`LOCATIONS`) is a starter set of ~20
  Ahmedabad areas with coordinates — add or edit freely.
- Design: light background, monochrome graphite/white palette. Color is
  used only for traffic-status signal (green/amber/red) — never as brand
  decoration.

## Putting it online (so anyone can access it, not just your computer)

This uses [Render](https://render.com) — free tier, no credit card needed
for this size of project. You'll deploy the backend and frontend as two
separate services.

### 1. Push this project to GitHub
Create a new repo on github.com and upload this whole `FlowAI-App` folder
(GitHub's website lets you drag-and-drop files if you don't want to use
git commands).

**Important:** don't upload your `.env` file — only `.env.example` should
go up. Real keys go into Render's dashboard instead (step 2). Also don't
upload `flowai.db` — it'll be recreated fresh on the server.

### 2. Deploy the backend
On Render: **New +** → **Web Service** → connect your GitHub repo → set:
- **Root directory:** `backend`
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`

Under **Environment**, add these variables:
- `ORS_API_KEY` = your real key
- `GEMINI_API_KEY` = your real key
- `GROQ_API_KEY` = your real key
- `SECRET_KEY` = a random string
- `FRONTEND_ORIGIN` = the URL your frontend will live at (step 4) — e.g.
  `https://flowai-xxxx.onrender.com` (no trailing slash). This is required
  for login to work cross-site; without it the browser will block the
  session cookie.

Deploy. You'll get a URL like `https://flowai-backend-xxxx.onrender.com`.
Test it by visiting `https://flowai-backend-xxxx.onrender.com/api/health` —
it should show `{"status": "ok", ...}`.

**Database note:** Render's free tier uses a temporary disk, so the
SQLite database (accounts, saved routes) can get wiped when the service
restarts or redeploys. Fine for testing/demos; for something you want to
keep long-term, swap in a free hosted Postgres (e.g. from
[Supabase](https://supabase.com) or [Neon](https://neon.tech)) by setting
a `DATABASE_URL` environment variable — the code already reads that if
it's present.

### 3. Point the frontend at that backend
In `frontend/app.js`, change `API_BASE` near the top:
```js
const API_BASE = "https://flowai-backend-xxxx.onrender.com/api";
```

### 4. Deploy the frontend
On Render: **New +** → **Static Site** → same repo → set:
- **Root directory:** `frontend`
- **Build command:** (leave blank)
- **Publish directory:** `.`

Deploy. You'll get a public URL like `https://flowai-xxxx.onrender.com` —
share this one. Go back and make sure `FRONTEND_ORIGIN` (step 2) matches
this exact URL, then redeploy the backend so it takes effect.

### Notes on the free tier
Render's free web services sleep after 15 minutes of no traffic — the
first request after a while can take 30-60 seconds to wake up. Normal on
the free tier, not a bug. Worth a heads-up if you demo it live.
