"""Match endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.db.dependencies import DbSession, PaginationDep
from app.schemas.common import Page
from app.schemas.match import MatchRead, MatchStatus
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=Page[MatchRead], summary="List matches")
async def list_matches(
    session: DbSession,
    pagination: PaginationDep,
    league_id: Annotated[
        int | None, Query(ge=1, description="Filter by league id.")
    ] = None,
    season: Annotated[
        int | None,
        Query(
            ge=1900, le=2100, description="Filter by season starting year.", examples=[2025]
        ),
    ] = None,
    matchday: Annotated[
        int | None, Query(ge=1, description="Filter by matchday / round.")
    ] = None,
    status: Annotated[
        MatchStatus | None, Query(description="Filter by match status.")
    ] = None,
) -> Page[MatchRead]:
    """Return a paginated list of matches, filtered by any combination of fields."""
    return await match_service.list_matches(
        session, league_id, season, matchday, status, pagination
    )
