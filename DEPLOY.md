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
   - API: <http://localhost:8000> (interactive docs at `/docs` are enabled only
     when `ENVIRONMENT` is not `production`).

> **Fail-fast in production.** When `ENVIRONMENT=production`, the backend refuses
> to start unless `SECRET_KEY` is a real value (not the default and ≥32 chars)
> and a TMDB credential is set. This prevents accidentally shipping forgeable
> JWTs. Generate a key with the command above.

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
| `FRONTEND_URL` | Public URL of the frontend, used to build links inside emails. |
| `RATE_LIMIT_ENABLED` | In-process per-IP throttling on auth endpoints (default `true`). |
| `ENVIRONMENT` | `development` or `production`. In production: docs are hidden, HSTS is sent, and the config guard runs. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_USE_TLS` / `EMAIL_FROM` | Transactional email. Leave `SMTP_HOST` blank to log emails to the console instead of sending. |

### Frontend (build-time)

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Base URL the browser uses to reach the API. Baked into the client bundle at build time, so rebuild the image when it changes. |

## Free-tier deploy on Render (no credit card)

The repo ships a [`render.yaml`](./render.yaml) Blueprint that provisions the
whole stack on Render's free plans — a free Postgres instance and two free
Docker web services. No payment method is required.

1. Push this repository to GitHub (already the case if you cloned it from your
   own remote).
2. In the [Render dashboard](https://dashboard.render.com), click
   **New + → Blueprint** and select this repository. Render reads `render.yaml`
   and shows the three resources it will create.
3. When prompted, paste your **TMDB v4 access token** (the only `sync: false`
   value). `SECRET_KEY` is generated automatically; `DATABASE_URL` is wired to
   the managed database; CORS and API URLs are pre-filled.
4. Click **Apply**. The backend applies migrations on first boot and the
   frontend builds with the API URL baked in.

Notes:

- **Service names must be globally unique.** The Blueprint hardcodes
  `https://filmclub-api.onrender.com` and `https://filmclub-web.onrender.com`.
  If either name is taken, Render appends a suffix; update `CORS_ORIGINS`,
  `FRONTEND_URL` (backend) and `NEXT_PUBLIC_API_URL` (frontend) to the real
  URLs shown in the dashboard, then redeploy.
- **Free database expiry.** Render's free Postgres is deleted after ~30 days.
  Back up or upgrade before then if you want to keep the data.
- **Cold starts.** Free web services spin down after inactivity and take a few
  seconds to wake on the next request.
- **DB URL scheme.** Render hands out `postgres://…` URLs; the app rewrites
  these to `postgresql+asyncpg://…` automatically (see `app/config.py`), so the
  same value works for both the server and Alembic.

## Production notes

- **HTTPS / reverse proxy.** Put a TLS-terminating proxy (Caddy, nginx,
  Traefik, or your platform's load balancer) in front of both services. Point
  `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` at the public HTTPS URLs.
- **Managed Postgres.** To use a hosted database (Neon, Supabase, RDS), drop the
  `db` service and set `DATABASE_URL` on the backend to the managed connection
  string. A `postgres://` or `postgresql://` URL is rewritten to the
  `postgresql+asyncpg://` driver automatically, so you can paste the provider's
  URL as-is.
- **Secrets.** Never commit `.env`. Use your platform's secret store for
  `SECRET_KEY`, `TMDB_*`, and the database password.
- **Migrations.** They run automatically at container start. To run them by
  hand: `docker compose run --rm backend alembic upgrade head`.
- **Scaling.** The backend is stateless (JWT auth, no server-side sessions), so
  it scales horizontally behind a load balancer. Postgres is the only stateful
  component. Note the auth rate limiter keeps its counters in process memory, so
  with N replicas the effective per-IP limit is ~N×; for a strict global limit,
  enforce it at the reverse proxy / WAF or swap in a Redis-backed limiter.
- **Workers.** The image runs a single Uvicorn process. To use more cores, run
  multiple replicas behind the load balancer, or override the command to
  `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers N`.
- **Security headers.** The API sends `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, and (in production) `Strict-Transport-Security`. Terminate
  TLS at the proxy so HSTS is meaningful. The Next.js frontend sends its own
  Content-Security-Policy and related headers (see `frontend/next.config.ts`),
  with `connect-src` scoped to `NEXT_PUBLIC_API_URL`.

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
