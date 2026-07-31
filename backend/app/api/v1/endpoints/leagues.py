"""League endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path

from app.db.dependencies import DbSession
from app.schemas.common import ErrorResponse
from app.schemas.league import LeagueRead
from app.services import league_service

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueRead], summary="List all leagues")
async def list_leagues(session: DbSession) -> list[LeagueRead]:
    """Return every league in the database."""
    return await league_service.list_leagues(session)


@router.get(
    "/{league_id}",
    response_model=LeagueRead,
    summary="Get a league by id",
    responses={404: {"model": ErrorResponse, "description": "League not found"}},
)
async def get_league(
    session: DbSession,
    league_id: Annotated[int, Path(ge=1, description="Internal league id.")],
) -> LeagueRead:
    """Return a single league, or 404 if it does not exist."""
    return await league_service.get_league(session, league_id)
