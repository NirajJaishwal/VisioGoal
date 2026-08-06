"""Mirror embedded chunks into the Postgres `documents` table.

ChromaDB holds the vectors; Postgres stays the source of truth for each chunk's
text, so the vector store can be rebuilt from the database at any time. Upserts
key on `chroma_id` (the deterministic doc id), matching the embed step's
idempotency so re-runs converge rather than duplicate.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from load.tables import documents


async def upsert_documents(
    session: AsyncSession, rows: list[dict[str, Any]]
) -> int:
    """Upsert `{entity_type, entity_id, content, chroma_id}` rows on chroma_id."""
    if not rows:
        return 0
    stmt = pg_insert(documents).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[documents.c.chroma_id],
        set_={
            "entity_type": stmt.excluded.entity_type,
            "entity_id": stmt.excluded.entity_id,
            "content": stmt.excluded.content,
        },
    )
    await session.execute(stmt)
    return len(rows)
