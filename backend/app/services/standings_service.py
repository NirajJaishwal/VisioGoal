"""Standings service — read the league table for a league/season."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standing import Standing
from app.models.team import Team
from app.schemas.standing import StandingRead
from app.schemas.team import TeamRef
from app.services.league_service import _get_league_or_404


def _to_read(standing: Standing, team: Team) -> StandingRead:
    """Build a StandingRead from a (Standing, Team) row, deriving goal diff."""
    return StandingRead(
        league_id=standing.league_id,
        season=standing.season,
        position=standing.position,
        team=TeamRef.model_validate(team),
        played=standing.played,
        won=standing.won,
        drawn=standing.drawn,
        lost=standing.lost,
        goals_for=standing.goals_for,
        goals_against=standing.goals_against,
        goal_difference=standing.goals_for - standing.goals_against,
        points=standing.points,
    )


async def list_standings(
    session: AsyncSession, league_id: int, season: int | None
) -> list[StandingRead]:
    """Return a league's table, optionally filtered to one season.

    Raises NotFoundError if the league does not exist. Results are ordered by
    season (newest first) then table position. A single join avoids N+1 lookups
    for team details.
    """
    await _get_league_or_404(session, league_id)

    stmt = (
        select(Standing, Team)
        .join(Team, Team.id == Standing.team_id)
        .where(Standing.league_id == league_id)
    )
    if season is not None:
        stmt = stmt.where(Standing.season == season)
    stmt = stmt.order_by(Standing.season.desc(), Standing.position.asc())

    result = await session.execute(stmt)
    return [_to_read(standing, team) for standing, team in result.all()]
