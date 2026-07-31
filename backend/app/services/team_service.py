"""Team service — list/filter teams and fetch one by id."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.dependencies import Pagination
from app.models.standing import Standing
from app.models.team import Team
from app.schemas.common import Page
from app.schemas.team import TeamRead


def _apply_filters(
    stmt: Select, league_id: int | None, season: int | None
) -> Select:
    """Apply the shared team filters to any statement selecting from Team.

    Defined once so the list query and the count query stay in sync (no
    duplicated filter logic). A `season` filter restricts to teams that have a
    standings row for that season (the season-partitioned source of truth).
    """
    if season is not None:
        stmt = stmt.join(Standing, Standing.team_id == Team.id).where(
            Standing.season == season
        )
    if league_id is not None:
        stmt = stmt.where(Team.league_id == league_id)
    return stmt


async def list_teams(
    session: AsyncSession,
    league_id: int | None,
    season: int | None,
    pagination: Pagination,
) -> Page[TeamRead]:
    """Return a paginated, filtered list of teams plus the total count."""
    total = await session.scalar(
        _apply_filters(select(func.count(func.distinct(Team.id))), league_id, season)
    )

    stmt = (
        _apply_filters(select(Team), league_id, season)
        .distinct()
        .order_by(Team.name)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    result = await session.execute(stmt)
    items = [TeamRead.model_validate(team) for team in result.scalars()]

    return Page(
        items=items,
        total=total or 0,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_team(session: AsyncSession, team_id: int) -> TeamRead:
    """Return a single team or raise NotFoundError."""
    team = await session.get(Team, team_id)
    if team is None:
        raise NotFoundError(f"Team {team_id} not found")
    return TeamRead.model_validate(team)
