"""Match service — list/filter fixtures and results."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.dependencies import Pagination
from app.models.match import Match
from app.models.team import Team
from app.schemas.common import Page
from app.schemas.match import MatchRead, MatchStatus
from app.schemas.team import TeamRef

# Distinct aliases so home and away teams can be joined in the same query.
_Home = aliased(Team, name="home_team")
_Away = aliased(Team, name="away_team")


def _apply_filters(
    stmt: Select,
    league_id: int | None,
    season: int | None,
    matchday: int | None,
    status: MatchStatus | None,
) -> Select:
    """Apply the shared match filters (kept in one place for list + count)."""
    if league_id is not None:
        stmt = stmt.where(Match.league_id == league_id)
    if season is not None:
        stmt = stmt.where(Match.season == season)
    if matchday is not None:
        stmt = stmt.where(Match.matchday == matchday)
    if status is not None:
        stmt = stmt.where(Match.status == status.value)
    return stmt


def _to_read(match: Match, home: Team, away: Team) -> MatchRead:
    """Build a MatchRead from a (Match, home Team, away Team) row."""
    return MatchRead(
        id=match.id,
        external_id=match.external_id,
        league_id=match.league_id,
        season=match.season,
        matchday=match.matchday,
        status=match.status,
        kickoff_datetime=match.kickoff_datetime,
        home_team=TeamRef.model_validate(home),
        away_team=TeamRef.model_validate(away),
        home_score=match.home_score,
        away_score=match.away_score,
    )


async def list_matches(
    session: AsyncSession,
    league_id: int | None,
    season: int | None,
    matchday: int | None,
    status: MatchStatus | None,
    pagination: Pagination,
) -> Page[MatchRead]:
    """Return a paginated, filtered list of matches with both teams joined."""
    total = await session.scalar(
        _apply_filters(
            select(func.count()).select_from(Match),
            league_id,
            season,
            matchday,
            status,
        )
    )

    stmt = _apply_filters(
        select(Match, _Home, _Away)
        .join(_Home, _Home.id == Match.home_team_id)
        .join(_Away, _Away.id == Match.away_team_id),
        league_id,
        season,
        matchday,
        status,
    )
    stmt = (
        stmt.order_by(Match.kickoff_datetime, Match.id)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    result = await session.execute(stmt)
    items = [_to_read(match, home, away) for match, home, away in result.all()]

    return Page(
        items=items,
        total=total or 0,
        limit=pagination.limit,
        offset=pagination.offset,
    )
