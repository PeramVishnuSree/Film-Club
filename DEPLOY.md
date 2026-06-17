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

## Free-tier production deploy (no credit card)

For a real deploy that avoids the worst free-tier pain (cold starts, a database
that expires), put each tier on the platform that serves it best:

| Tier | Platform | Why |
| --- | --- | --- |
| Frontend (Next.js) | **Vercel** | Never sleeps, global CDN, built for Next.js |
| Database (Postgres) | **Neon** | Free **and persistent** — no 30-day expiry |
| Backend (FastAPI) | **Render** | Docker web service, kept warm by a cron ping |

None of these require a payment method.

### 1. Database — Neon

1. Create a project at [neon.tech](https://neon.tech) and copy the connection
   string (looks like `postgres://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`).
2. You'll paste this as `DATABASE_URL` on the backend (next step). The app
   rewrites the scheme to `postgresql+asyncpg://` and translates `sslmode` to
   asyncpg's `ssl` automatically (see `app/config.py`), so paste it as-is.

### 2. Backend — Render

The repo ships a [`render.yaml`](./render.yaml) Blueprint for the API only.

1. In the [Render dashboard](https://dashboard.render.com): **New + → Blueprint**,
   select this repo. Render reads `render.yaml` and shows the `filmclub-api`
   service.
2. When prompted for the `sync: false` values:
   - `DATABASE_URL` → your Neon connection string
   - `TMDB_ACCESS_TOKEN` → your TMDB v4 read token
   - `CORS_ORIGINS` → your Vercel app URL (e.g. `https://film-club.vercel.app`)
   - `FRONTEND_URL` → the same Vercel app URL
   `SECRET_KEY` is generated automatically.
3. **Apply.** The backend applies migrations to Neon on first boot and starts.
   Confirm `https://filmclub-api.onrender.com/health` returns `{"status":"healthy"}`.

> If the Vercel URL isn't known yet, set `CORS_ORIGINS`/`FRONTEND_URL` after
> step 3 in the service's **Environment** tab and let it redeploy.

### 3. Frontend — Vercel

1. At [vercel.com](https://vercel.com), **Add New → Project**, import this repo.
2. Set **Root Directory** to `frontend`. Framework preset auto-detects Next.js.
3. Add an environment variable **`NEXT_PUBLIC_API_URL`** =
   `https://filmclub-api.onrender.com` (baked into the client bundle at build
   time and used to scope the frontend's CSP `connect-src`).
4. **Deploy.** Vercel gives you the app URL — make sure it matches what you put
   in the backend's `CORS_ORIGINS`/`FRONTEND_URL`.

### 4. Keep the backend warm

Render free services spin down after ~15 min idle (~50s cold start). The
included [`.github/workflows/keep-warm.yml`](./.github/workflows/keep-warm.yml)
pings `/health` every ~10 minutes to prevent that. It runs automatically on
GitHub Actions (free; unlimited minutes on public repos). A free external
pinger like cron-job.org or UptimeRobot is an equivalent alternative.

Notes:

- **One always-on backend fits the free budget.** Render gives 750 instance-
  hours/month; a single warm service uses ~744. Don't keep a second free web
  service always-on or you'll exceed it.
- **Service name uniqueness.** `render.yaml` and the keep-warm workflow assume
  `filmclub-api.onrender.com`. If that name is taken, Render appends a suffix —
  update the workflow URL and `NEXT_PUBLIC_API_URL` to match.

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
