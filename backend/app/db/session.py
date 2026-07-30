"""Async SQLAlchemy engine, session factory, and FastAPI dependency.

The engine is created once at import time and shared across the app. Use
`get_db()` as a FastAPI dependency (added in a later phase) to obtain a
request-scoped `AsyncSession` that is always closed and rolled back on error.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# `pool_pre_ping` transparently recycles stale connections; `echo` mirrors the
# debug flag so SQL is logged only in development.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    future=True,
)

# `expire_on_commit=False` keeps ORM objects usable after commit (important for
# returning them from request handlers without triggering lazy re-loads).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async session (FastAPI dependency)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
