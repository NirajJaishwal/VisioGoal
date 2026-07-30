"""Async database engine and session factory for the ingestion pipeline.

Kept separate from the backend's `app.db.session` because ingestion is its own
deployable with its own lifecycle. The URL comes from configuration (env).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
