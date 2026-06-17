from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secret-key values that must never be used in production. The defaults shipped
# in code / .env.example / docker-compose fall into this set so a deploy that
# forgot to set a real key fails fast instead of running forgeable JWTs.
_INSECURE_SECRETS = {"dev-insecure-change-me", "change-me", "", "secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Film Club API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://filmclub:filmclub@localhost:5432/filmclub"

    tmdb_api_key: str = ""
    tmdb_access_token: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p"

    # Stored as a raw string (not list[str]) so pydantic-settings doesn't force
    # JSON decoding of the env var; the `cors_origins` property parses it,
    # accepting JSON, a single URL, or a comma-separated list.
    cors_origins_raw: str = Field(
        default="http://localhost:3000", validation_alias="CORS_ORIGINS"
    )

    secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Public URL of the frontend, used to build links inside emails.
    frontend_url: str = "http://localhost:3000"

    # --- email / SMTP ---
    # When smtp_host is blank, emails are logged to the console instead of sent
    # (handy in development). Configure these in production to deliver real mail.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True  # STARTTLS
    email_from: str = "Film Club <no-reply@filmclub.local>"

    # Token lifetimes for the email-driven flows.
    password_reset_expire_minutes: int = 60
    email_verify_expire_minutes: int = 60 * 24  # 1 day

    # In-process per-IP rate limiting on auth endpoints. Disabled in the test
    # suite (state would otherwise leak across cases).
    rate_limit_enabled: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Coerce cloud-provider DSNs to the async driver this app uses.

        Managed Postgres (Render, Neon, Supabase, Heroku, …) hands out URLs
        like ``postgres://…`` or ``postgresql://…`` and often append libpq
        query params (``sslmode``, ``channel_binding``) that the psycopg/libpq
        stack understands but ``asyncpg`` does not. SQLAlchemy's async engine
        and Alembic both need the ``postgresql+asyncpg://`` scheme, so rewrite
        the scheme and translate the SSL params here once — covering both the
        app engine and migrations, which read ``settings.database_url``.
        """
        if not isinstance(value, str) or not value:
            return value

        # 1) Driver scheme.
        if value.startswith("postgres://"):
            value = "postgresql+asyncpg://" + value[len("postgres://") :]
        elif value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]

        # 2) Translate / drop query params asyncpg can't parse.
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

        parts = urlsplit(value)
        if not parts.query:
            return value

        new_query: list[tuple[str, str]] = []
        for key, val in parse_qsl(parts.query, keep_blank_values=True):
            if key == "sslmode":
                # asyncpg uses `ssl`, not libpq's `sslmode`, but accepts the same
                # string values (require, verify-ca, verify-full, …). Pass the
                # value through; drop an explicit "disable" (no encryption).
                if val and val != "disable":
                    new_query.append(("ssl", val))
            elif key == "channel_binding":
                # libpq-only; asyncpg rejects it outright.
                continue
            else:
                new_query.append((key, val))

        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(new_query), parts.fragment)
        )

    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins, parsed from ``CORS_ORIGINS``.

        Accepts a JSON array (``["https://app.vercel.app"]``), a single URL
        (``https://app.vercel.app``), or a comma-separated list — whichever is
        easiest to type into a hosting dashboard.
        """
        raw = self.cors_origins_raw.strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            return json.loads(raw)
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    def validate_for_production(self) -> None:
        """Fail fast on insecure configuration when running in production.

        Called at app startup. Catches the most dangerous misconfiguration —
        deploying with the default JWT signing key, which would let anyone forge
        access tokens for any account.
        """
        if not self.is_production:
            return
        problems: list[str] = []
        if self.secret_key.strip() in _INSECURE_SECRETS or len(self.secret_key) < 32:
            problems.append(
                "SECRET_KEY is unset, default, or too short. Generate one with: "
                'python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if not (self.tmdb_access_token or self.tmdb_api_key):
            problems.append("No TMDB credential set (TMDB_ACCESS_TOKEN or TMDB_API_KEY).")
        if problems:
            raise RuntimeError(
                "Refusing to start in production with insecure configuration:\n  - "
                + "\n  - ".join(problems)
            )


settings = Settings()
