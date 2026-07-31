"""League service — read operations over the `leagues` table.

Routers call these functions; they never touch ORM models themselves. Each
function returns Pydantic schemas, never ORM objects.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.league import League
from app.schemas.league import LeagueRead


async def _get_league_or_404(session: AsyncSession, league_id: int) -> League:
    """Return the League ORM row or raise NotFoundError (shared by services)."""
    league = await session.get(League, league_id)
    if league is None:
        raise NotFoundError(f"League {league_id} not found")
    return league


async def list_leagues(session: AsyncSession) -> list[LeagueRead]:
    """Return all leagues, ordered by name."""
    result = await session.execute(select(League).order_by(League.name))
    return [LeagueRead.model_validate(row) for row in result.scalars()]


async def get_league(session: AsyncSession, league_id: int) -> LeagueRead:
    """Return a single league or raise NotFoundError."""
    league = await _get_league_or_404(session, league_id)
    return LeagueRead.model_validate(league)
