"""Reusable FastAPI dependencies.

Centralizes the injectable pieces every endpoint needs — a database session,
settings, and validated pagination — as `Annotated` aliases so routers stay
declarative (`session: DbSession`) and validation lives in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db

# Async request-scoped database session.
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Cached application settings.
SettingsDep = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True)
class Pagination:
    """Validated limit/offset for list endpoints."""

    limit: int
    offset: int


def get_pagination(
    limit: Annotated[
        int, Query(ge=1, le=200, description="Max rows to return (1–200).")
    ] = 50,
    offset: Annotated[
        int, Query(ge=0, description="Rows to skip before returning results.")
    ] = 0,
) -> Pagination:
    """Provide validated pagination parameters (422 on out-of-range values)."""
    return Pagination(limit=limit, offset=offset)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
