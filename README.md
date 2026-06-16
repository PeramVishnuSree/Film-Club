# Film Club

An open-source, ad-free movie logging and discovery app — a Letterboxd-style
alternative you can self-host. Log films, keep a diary and watchlists, write and
like reviews, rate what you watch, build (and rank) lists, follow other people,
see where each film is streaming, browse trending and top-rated titles, and get
recommendations tailored to your taste.

All film data comes from [TMDB](https://www.themoviedb.org/) (free, with
attribution). This product uses the TMDB API but is not endorsed or certified
by TMDB.

## Features

- **Logging** — diary entries with dates, ratings (½–5 stars), likes, rewatches,
  and notes.
- **Watchlist & lists** — a personal watchlist plus custom lists, optionally
  ranked, public or private, with likes.
- **Reviews** — write reviews, mark spoilers, and like others' reviews.
- **Discovery** — trending, an editorial Top 500, full-text film search, and
  per-film watch-provider availability by region.
- **Recommendations** — personalized picks drawn from the people you follow and
  your own taste, with a short "why" for each.
- **Social** — follow users, an activity feed, profiles, and notifications for
  follows and likes.
- **Stats** — a lifetime overview and a year-in-review dashboard (hours watched,
  rating distribution, top genres and films, monthly activity).
- **Import** — bring your history over from a Letterboxd CSV export
  (diary, ratings, watchlist).
- **Accounts** — JWT auth, email verification, and password reset.

## Tech stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Alembic, Postgres,
  PyJWT + bcrypt.
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS.
- **Data:** TMDB API (metadata, trending, watch providers, recommendation base).
- **Tests:** pytest against a real Postgres database.
- **CI:** GitHub Actions (backend tests, frontend typecheck/lint/build).

## Quick start with Docker

The fastest way to run the whole stack (Postgres + API + web):

```bash
cp backend/.env.example backend/.env   # add TMDB creds + a SECRET_KEY
docker compose up --build
```

Frontend on http://localhost:3000, API docs on http://localhost:8000/docs.
See [DEPLOY.md](./DEPLOY.md) for configuration and production guidance.

## Local development

### Backend

Requires Python 3.12 and a Postgres instance (local via `brew install
postgresql@16`, or a free cloud DB like Neon/Supabase).

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your TMDB credentials and DATABASE_URL
alembic upgrade head        # create the database schema
uvicorn app.main:app --reload
```

Visit http://localhost:8000/ and http://localhost:8000/docs.

You'll need a TMDB credential — a free
[v3 API key](https://www.themoviedb.org/settings/api) or a v4 read access
token. Set `TMDB_API_KEY` or `TMDB_ACCESS_TOKEN` in `.env`.

### Frontend

Requires Node 20+.

```bash
cd frontend
npm install
# point the browser at your local API:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Visit http://localhost:3000.

## Running the tests

The backend test suite runs against a real Postgres database (it relies on
Postgres-only features). Create a test database and run pytest:

```bash
cd backend
createdb filmclub_test                 # once
pip install -r requirements-dev.txt
pytest
```

Override the target database with `TEST_DATABASE_URL` if needed. Tests use an
in-memory TMDB stand-in, so they never hit the network.

Frontend checks:

```bash
cd frontend
npx tsc --noEmit && npm run lint && npm run build
```

## Project layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, tests
frontend/   Next.js App Router app
docker-compose.yml, DEPLOY.md   container stack + deployment docs
```

## Contributing

Issues and pull requests are welcome. Please run the backend and frontend checks
above before opening a PR; CI runs the same checks.

## Legal

- **License:** [GNU AGPL-3.0](./LICENSE). If you run a modified version as a
  network service, you must make your source available to its users.
- **Privacy & terms:** see [PRIVACY.md](./PRIVACY.md) and [TERMS.md](./TERMS.md)
  (templates for self-hosters to adapt).
- **TMDB:** This product uses the TMDB API but is not endorsed or certified by
  TMDB.
