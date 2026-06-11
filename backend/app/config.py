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


settings = Settings()
