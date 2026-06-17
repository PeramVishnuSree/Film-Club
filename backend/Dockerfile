# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

# - PYTHONUNBUFFERED: stream logs straight to the container output
# - PYTHONDONTWRITEBYTECODE: no .pyc clutter in the image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so they cache across code changes.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application code.
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# The entrypoint applies migrations, then execs the given command.
# Bind to $PORT when the platform provides one (Render, Heroku, …) and fall
# back to 8000 for local runs / docker-compose. `exec` keeps uvicorn as PID 1
# inside the shell so it receives SIGTERM for graceful shutdown.
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
