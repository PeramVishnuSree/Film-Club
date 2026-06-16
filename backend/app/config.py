from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Film Club API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://filmclub:filmclub@localhost:5432/filmclub"

    tmdb_api_key: str = ""
    tmdb_access_token: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p"

    cors_origins: list[str] = ["http://localhost:3000"]

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

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host)


settings = Settings()
