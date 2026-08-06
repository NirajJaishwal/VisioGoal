"""Ingestion configuration — loaded from environment (never hardcoded).

The ingestion package has a lifecycle separate from the backend, so it carries
its own settings object rather than importing `app.core.config`. Values come
from environment variables (and a local `.env` in development) via
pydantic-settings. Secrets (the API key) live only in the environment.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database (async SQLAlchemy URL) ---
    # Host is `localhost` for a local run and `postgres` inside docker-compose.
    database_url: str = (
        "postgresql+asyncpg://football:changeme@localhost:5432/football_intel"
    )

    # --- Football-Data.org API ---
    # The API key is required and read from the environment only.
    football_data_api_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"

    # Competition codes to ingest (Football-Data.org free tier: top-5 leagues).
    #   PL=Premier League · PD=La Liga · BL1=Bundesliga · SA=Serie A · FL1=Ligue 1
    football_data_competitions: list[str] = ["PL", "PD", "BL1", "SA", "FL1"]
    # Optional JSON object keyed by provider competition code, e.g.
    # {"PD": "La Liga"}. This changes presentation only, never provider ids.
    football_data_display_names: dict[str, str] = {}

    # Inclusive historical range, as season start years (e.g. 2018..2025).
    football_data_start_season: int | None = None
    football_data_end_season: int | None = None
    # Legacy one-season setting. Kept so existing .env files continue to work.
    # Left unset, the pipeline fetches each competition's *current* season — which,
    # before a new season kicks off, has no played matches (all scores null). Pin a
    # completed/in-progress season here to ingest real results.
    football_data_season: int | None = None

    # --- Embeddings / vector store (RAG) ---
    # Local Sentence-Transformers model; MUST match the backend so a query
    # embedded at answer time lands in the same space as the embedded documents.
    embedding_model: str = "all-MiniLM-L6-v2"
    # ChromaDB connection — compose service name + internal port.
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "football_docs"
    # Keep below Chroma's server-side maximum and make large historical loads
    # scale without changing vector ids or embeddings.
    chroma_upsert_batch_size: int = Field(default=5000, ge=1)

    # --- HTTP resilience ---
    request_timeout_seconds: float = 30.0
    max_retries: int = 5
    # Free tier allows ~10 requests/minute; keep a polite floor between calls.
    min_request_interval_seconds: float = 6.5
    backoff_base_seconds: float = 2.0

    @property
    def has_api_key(self) -> bool:
        return bool(self.football_data_api_key.strip())

    @model_validator(mode="after")
    def validate_season_range(self) -> Settings:
        if (self.football_data_start_season is None) != (self.football_data_end_season is None):
            raise ValueError("FOOTBALL_DATA_START_SEASON and FOOTBALL_DATA_END_SEASON must be set together")
        if (
            self.football_data_start_season
            and self.football_data_end_season
            and self.football_data_start_season > self.football_data_end_season
        ):
            raise ValueError("FOOTBALL_DATA_START_SEASON cannot exceed FOOTBALL_DATA_END_SEASON")
        return self

    @property
    def football_data_seasons(self) -> list[int | None]:
        """Configured historical seasons, falling back to the legacy setting."""
        if self.football_data_start_season is not None:
            return list(range(self.football_data_start_season, self.football_data_end_season + 1))
        return [self.football_data_season]

    def competition_display_name(self, code: str, provider_name: str) -> str:
        return self.football_data_display_names.get(code, provider_name)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()


settings = get_settings()
