"""Document model — RAG source text mirrored from ChromaDB.

Postgres stays the source of truth for each embedded chunk's text; ChromaDB
holds the vectors keyed by `chroma_id`. This lets the vector store be rebuilt
from Postgres at any time. (Populated in a later, RAG-focused phase.)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # What the document describes, e.g. "league" | "team" | "match".
    entity_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    # PK of the described row in its own table (not a DB-level FK — polymorphic).
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Corresponding id in the ChromaDB collection (null until embedded).
    chroma_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Document id={self.id} {self.entity_type}:{self.entity_id}>"
