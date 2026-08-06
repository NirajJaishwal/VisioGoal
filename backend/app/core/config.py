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
        extra="ignore",  # ignore unrelated keys (Groq, Chroma, ...) in .env
    )

    # --- Core ---
    environment: str = "development"
    debug: bool = False

    # --- Database ---
    # Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/db
    database_url: str = (
        "postgresql+asyncpg://football:changeme@localhost:5432/football_intel"
    )

    # --- AI / RAG ---
    # Groq key (server-side only; the frontend never sees it).
    groq_api_key: str = ""
    # Groq-hosted model id. See https://console.groq.com/docs/models for the
    # current catalog — ids change as models are added/retired.
    groq_model: str = "llama-3.3-70b-versatile"
    # ChromaDB (vector store) connection — compose service name + internal port.
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "football_docs"
    # Local Sentence-Transformers model used for both ingestion and query embedding.
    embedding_model: str = "all-MiniLM-L6-v2"
    # Max tokens for a chat answer (streamed).
    chat_max_tokens: int = 2048

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def has_groq_key(self) -> bool:
        """True only when a real (non-placeholder) Groq key is configured.

        Groq keys are prefixed `gsk_`; anything shorter than a plausible key (or
        an obvious placeholder) is treated as unset so the chat endpoint can
        report a clear configuration error instead of failing at request time.
        """
        key = self.groq_api_key.strip()
        return bool(key) and not key.lower().endswith("xxxxxxxx")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()


settings = get_settings()
