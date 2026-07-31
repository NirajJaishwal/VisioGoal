"""Standings endpoint — a league's table, nested under the league resource."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.db.dependencies import DbSession
from app.schemas.common import ErrorResponse
from app.schemas.standing import StandingRead
from app.services import standings_service

router = APIRouter(prefix="/leagues", tags=["standings"])


@router.get(
    "/{league_id}/standings",
    response_model=list[StandingRead],
    summary="Get a league's standings",
    responses={404: {"model": ErrorResponse, "description": "League not found"}},
)
async def get_standings(
    session: DbSession,
    league_id: Annotated[int, Path(ge=1, description="Internal league id.")],
    season: Annotated[
        int | None,
        Query(
            ge=1900,
            le=2100,
            description="Season starting year, e.g. 2025. Omit for all seasons.",
            examples=[2025],
        ),
    ] = None,
) -> list[StandingRead]:
    """Return the league table, optionally filtered to a single season."""
    return await standings_service.list_standings(session, league_id, season)
