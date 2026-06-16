# Deploying Film Club

Film Club ships as two containers — a FastAPI backend and a Next.js frontend —
backed by PostgreSQL. The repository includes Dockerfiles for each and a
`docker-compose.yml` that wires the whole stack together.

## Prerequisites

- Docker with Compose v2 (`docker compose`, not the legacy `docker-compose`)
- A TMDB API credential — a free [v3 API key](https://www.themoviedb.org/settings/api)
  or a v4 read access token. Watch data, posters, and search all come from TMDB.

## Quick start (Docker Compose)

1. Create the backend env file and fill in your secrets:

   ```bash
   cp backend/.env.example backend/.env
   # set TMDB_ACCESS_TOKEN (or TMDB_API_KEY) and a strong SECRET_KEY
   ```

   Generate a secret key with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Provide the values Compose reads from the environment. You can export them or
   put them in a root `.env` file (Compose loads it automatically):

   ```bash
   # .env (repo root) — consumed by docker-compose.yml
   POSTGRES_PASSWORD=use-a-real-password
   SECRET_KEY=paste-the-generated-hex
   TMDB_ACCESS_TOKEN=your-tmdb-v4-token
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Build and start everything:

   ```bash
   docker compose up --build
   ```

   - Frontend: <http://localhost:3000>
   - API + docs: <http://localhost:8000/docs>

The backend container applies Alembic migrations on startup (see
`backend/docker-entrypoint.sh`), retrying until Postgres is ready, so the first
boot needs no manual migration step. Postgres data persists in the `pgdata`
named volume.

## Configuration reference

### Backend (`backend/.env` or environment)

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://...`). Compose sets this to the `db` service automatically. |
| `SECRET_KEY` | Signing key for JWTs. **Must** be changed from the default in production. |
| `TMDB_ACCESS_TOKEN` | TMDB v4 read token (preferred), sent as a Bearer header. |
| `TMDB_API_KEY` | TMDB v3 key (alternative to the token). |
| `CORS_ORIGINS` | JSON array of allowed frontend origins, e.g. `["https://filmclub.example"]`. |
| `ENVIRONMENT` | `development` or `production`. |

### Frontend (build-time)

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Base URL the browser uses to reach the API. Baked into the client bundle at build time, so rebuild the image when it changes. |

## Production notes

- **HTTPS / reverse proxy.** Put a TLS-terminating proxy (Caddy, nginx,
  Traefik, or your platform's load balancer) in front of both services. Point
  `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` at the public HTTPS URLs.
- **Managed Postgres.** To use a hosted database (Neon, Supabase, RDS), drop the
  `db` service and set `DATABASE_URL` on the backend to the managed connection
  string. Keep the `postgresql+asyncpg://` driver prefix.
- **Secrets.** Never commit `.env`. Use your platform's secret store for
  `SECRET_KEY`, `TMDB_*`, and the database password.
- **Migrations.** They run automatically at container start. To run them by
  hand: `docker compose run --rm backend alembic upgrade head`.
- **Scaling.** The backend is stateless (JWT auth, no server-side sessions), so
  it scales horizontally behind a load balancer. Postgres is the only stateful
  component.

## Building images individually

```bash
# Backend
docker build -t filmclub-backend ./backend

# Frontend (bake the API URL for the browser bundle)
docker build -t filmclub-frontend \
  --build-arg NEXT_PUBLIC_API_URL=https://api.filmclub.example ./frontend
```

## Running without Docker

See the per-service development instructions in [`README.md`](./README.md):
create a Python virtualenv for the backend and run `npm run dev` for the
frontend against a local Postgres instance.
