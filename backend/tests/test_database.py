"""Database verification tests.

Two checks:
1. All six models are registered on the shared metadata (no DB required).
2. A live async connection to PostgreSQL succeeds (requires the DB running;
   the test is skipped if the DB is unreachable, so it is safe to run anywhere).

Run with:  pytest tests/test_database.py -v
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine

EXPECTED_TABLES = {
    "leagues",
    "teams",
    "matches",
    "standings",
    "documents",
    "chat_messages",
}


def test_models_are_registered() -> None:
    """Importing app.db.base must register every MVP table on the metadata."""
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Models not registered on Base.metadata: {missing}"


@pytest.mark.asyncio
async def test_database_connection() -> None:
    """A trivial query must round-trip through the async engine."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    except (SQLAlchemyError, OSError) as exc:
        pytest.skip(f"PostgreSQL not reachable (skipping live check): {exc}")
