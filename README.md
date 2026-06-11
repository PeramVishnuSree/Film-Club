# Film Club

An open-source, ad-free movie logging and discovery app — a Letterboxd-style
alternative. Log films, keep a diary/journal and watchlists, write reviews,
give ratings, follow other users, see where each film is streaming, browse
trending titles, and get recommendations tailored to your taste.

All film data comes from [TMDB](https://www.themoviedb.org/) (free, commercial
use with attribution). This product uses the TMDB API but is not endorsed or
certified by TMDB.

## Status

Early MVP scaffolding. See `docs/` for the build plan.

## Tech stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Alembic, Postgres
- **Frontend:** Next.js + TypeScript + Tailwind (added in a later step)
- **Data:** TMDB API (metadata, trending, watch providers, base recommendations)

## Backend — local development

Requires Python 3.12 and a Postgres instance (local via `brew install
postgresql@16`, or a free cloud DB like Neon/Supabase).

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your TMDB_API_KEY and DATABASE_URL
uvicorn app.main:app --reload
```

Visit http://localhost:8000/ and http://localhost:8000/docs.

## License

TBD — choosing between MIT and AGPL before first public release.
