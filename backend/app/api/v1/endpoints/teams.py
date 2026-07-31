"""Team endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.db.dependencies import DbSession, PaginationDep
from app.schemas.common import ErrorResponse, Page
from app.schemas.team import TeamRead
from app.services import team_service

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=Page[TeamRead], summary="List teams")
async def list_teams(
    session: DbSession,
    pagination: PaginationDep,
    league_id: Annotated[
        int | None, Query(ge=1, description="Filter by league id.")
    ] = None,
    season: Annotated[
        int | None,
        Query(
            ge=1900,
            le=2100,
            description="Filter to teams that appear in this season's standings.",
            examples=[2025],
        ),
    ] = None,
) -> Page[TeamRead]:
    """Return a paginated list of teams, optionally filtered by league/season."""
    return await team_service.list_teams(session, league_id, season, pagination)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Get a team by id",
    responses={404: {"model": ErrorResponse, "description": "Team not found"}},
)
async def get_team(
    session: DbSession,
    team_id: Annotated[int, Path(ge=1, description="Internal team id.")],
) -> TeamRead:
    """Return a single team, or 404 if it does not exist."""
    return await team_service.get_team(session, team_id)
