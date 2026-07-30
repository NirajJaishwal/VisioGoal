"""Application configuration.

Settings are loaded from environment variables (and a local `.env` file in
development) via pydantic-settings. Import the shared `settings` instance, or
call `get_settings()` where a cached accessor is preferable (e.g. FastAPI deps).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unrelated keys (Anthropic, Chroma, ...) in .env
    )

    # --- Core ---
    environment: str = "development"
    debug: bool = False

    # --- Database ---
    # Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/db
    database_url: str = (
        "postgresql+asyncpg://football:changeme@localhost:5432/football_intel"
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()


settings = get_settings()
