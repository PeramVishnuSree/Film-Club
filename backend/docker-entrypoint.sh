#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres, apply migrations, then hand off to the container command.
# DATABASE_URL must be set (see .env.example).

echo "Applying database migrations..."
# Retry a few times so a freshly-started Postgres has time to accept connections.
attempts=0
until alembic upgrade head; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 10 ]; then
    echo "Migrations failed after $attempts attempts; giving up." >&2
    exit 1
  fi
  echo "Database not ready yet (attempt $attempts); retrying in 2s..."
  sleep 2
done

echo "Migrations applied. Starting: $*"
exec "$@"
