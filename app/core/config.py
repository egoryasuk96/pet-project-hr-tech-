"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets must come from the environment (NFR-DEP-03)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Employee Service"
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/employee_service"
    jwt_secret: str = "local-dev-only-change-me-jwt-secret"
    jwt_ttl_hours: int = 8
    demo_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
