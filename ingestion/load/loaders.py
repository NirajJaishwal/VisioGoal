"""Idempotent loaders — upsert transformed rows into PostgreSQL.

Every loader uses `INSERT ... ON CONFLICT DO UPDATE` keyed on a table's unique
constraint, so re-running the pipeline never creates duplicate rows and always
converges the table to the latest fetched state. Loaders only *execute*
statements on the session they are given; transaction boundaries (commit /
rollback) are owned by the caller (the pipeline).

Each loader reports how many rows were inserted vs. updated. Counts are computed
by checking which conflict keys already exist before the upsert — transparent
and portable, at the cost of one extra SELECT per batch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from sqlalchemy import delete, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.logging import get_logger
from load.tables import leagues, matches, standings, teams

log = get_logger(__name__)


@dataclass
class LoadResult:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0

    @property
    def total(self) -> int:
        return self.inserted + self.updated


async def _existing_single(
    session: AsyncSession, table: Any, key_col: str, keys: Sequence[Any]
) -> set[Any]:
    """Return the subset of `keys` already present in `table.key_col`."""
    if not keys:
        return set()
    col = table.c[key_col]
    result = await session.execute(select(col).where(col.in_(list(keys))))
    return {row[0] for row in result.all()}


async def _existing_composite(
    session: AsyncSession, table: Any, cols: Sequence[str], keys: Sequence[tuple]
) -> set[tuple]:
    """Return the subset of composite `keys` already present in `table`."""
    if not keys:
        return set()
    columns = [table.c[c] for c in cols]
    result = await session.execute(
        select(*columns).where(tuple_(*columns).in_([tuple(k) for k in keys]))
    )
    return {tuple(row) for row in result.all()}


async def _prune(
    session: AsyncSession,
    table: Any,
    *,
    league_id: int,
    season: int,
    keep_col: str,
    keep_values: Sequence[Any],
) -> int:
    """Delete rows for exactly one (league_id, season) that are no longer present.

    Removes rows in `table` scoped to `league_id` AND `season` whose `keep_col`
    is not in `keep_values` — i.e. only stale rows of the season being loaded.
    Other seasons are never matched (the `season` predicate excludes them), and
    leagues/teams are never touched (this only ever runs against fact tables).

    Safety: if `keep_values` is empty (nothing was fetched — e.g. a transient
    empty response), pruning is skipped entirely rather than deleting the whole
    season, so a bad fetch can't wipe good data.
    """
    if not keep_values:
        return 0
    result = await session.execute(
        delete(table).where(
            table.c.league_id == league_id,
            table.c.season == season,
            table.c[keep_col].notin_(list(keep_values)),
        )
    )
    return result.rowcount or 0


async def _upsert(
    session: AsyncSession,
    table: Any,
    rows: list[dict[str, Any]],
    conflict_cols: Sequence[str],
    update_cols: Iterable[str],
    existing: set,
    key_of,
) -> LoadResult:
    """Perform the ON CONFLICT upsert and return insert/update counts."""
    if not rows:
        return LoadResult()

    inserted = sum(1 for r in rows if key_of(r) not in existing)
    updated = len(rows) - inserted

    stmt = pg_insert(table).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c[c] for c in conflict_cols],
        set_={col: stmt.excluded[col] for col in update_cols},
    )
    await session.execute(stmt)
    return LoadResult(inserted=inserted, updated=updated)


# --- entity loaders --------------------------------------------------------
async def upsert_league(
    session: AsyncSession, row: dict[str, Any]
) -> tuple[int, LoadResult]:
    """Upsert one league and return its internal id plus the load result."""
    existing = await _existing_single(
        session, leagues, "external_id", [row["external_id"]]
    )
    result = await _upsert(
        session,
        leagues,
        [row],
        conflict_cols=["external_id"],
        update_cols=["name", "country", "season"],
        existing=existing,
        key_of=lambda r: r["external_id"],
    )
    internal_id = await session.scalar(
        select(leagues.c.id).where(leagues.c.external_id == row["external_id"])
    )
    return int(internal_id), result


async def upsert_teams(
    session: AsyncSession, league_id: int, rows: list[dict[str, Any]]
) -> tuple[LoadResult, dict[int, int]]:
    """Upsert teams for a league; return the result and a provider→internal map."""
    prepared = [{**row, "league_id": league_id} for row in rows]
    existing = await _existing_single(
        session, teams, "external_id", [r["external_id"] for r in prepared]
    )
    result = await _upsert(
        session,
        teams,
        prepared,
        conflict_cols=["external_id"],
        update_cols=["league_id", "name", "short_name", "crest_url", "venue"],
        existing=existing,
        key_of=lambda r: r["external_id"],
    )
    # Build the provider-id → internal-id map for FK resolution downstream.
    result_rows = await session.execute(
        select(teams.c.external_id, teams.c.id).where(teams.c.league_id == league_id)
    )
    team_map = {ext: internal for ext, internal in result_rows.all()}
    return result, team_map


async def upsert_standings(
    session: AsyncSession,
    league_id: int,
    season: int,
    rows: list[dict[str, Any]],
    team_map: dict[int, int],
) -> LoadResult:
    """Upsert standings, resolving provider team ids to internal ids.

    After upserting, prune any standings rows for *this league and season only*
    whose team is no longer in the fetched table (e.g. a relegated/absent team
    from an earlier run), so the season's data mirrors the source exactly.
    """
    prepared: list[dict[str, Any]] = []
    skipped = 0
    for row in rows:
        team_id = team_map.get(row["team_external_id"])
        if team_id is None:
            skipped += 1
            log.warning(
                "standing_team_unresolved",
                extra={"team_external_id": row["team_external_id"], "league_id": league_id},
            )
            continue
        prepared.append(
            {
                "league_id": league_id,
                "team_id": team_id,
                "season": row["season"],
                "position": row["position"],
                "played": row["played"],
                "won": row["won"],
                "drawn": row["drawn"],
                "lost": row["lost"],
                "goals_for": row["goals_for"],
                "goals_against": row["goals_against"],
                "points": row["points"],
            }
        )

    conflict = ["league_id", "team_id", "season"]
    existing = await _existing_composite(
        session,
        standings,
        conflict,
        [(r["league_id"], r["team_id"], r["season"]) for r in prepared],
    )
    result = await _upsert(
        session,
        standings,
        prepared,
        conflict_cols=conflict,
        update_cols=[
            "position", "played", "won", "drawn", "lost",
            "goals_for", "goals_against", "points",
        ],
        existing=existing,
        key_of=lambda r: (r["league_id"], r["team_id"], r["season"]),
    )
    result.skipped = skipped
    result.deleted = await _prune(
        session,
        standings,
        league_id=league_id,
        season=season,
        keep_col="team_id",
        keep_values=[r["team_id"] for r in prepared],
    )
    return result


async def upsert_matches(
    session: AsyncSession,
    league_id: int,
    season: int,
    rows: list[dict[str, Any]],
    team_map: dict[int, int],
) -> LoadResult:
    """Upsert matches, resolving provider team ids to internal ids.

    Each row is stamped with `season`. After upserting, prune any matches for
    *this league and season only* whose external id is no longer in the fetched
    set (e.g. a fixture removed upstream since an earlier run).
    """
    prepared: list[dict[str, Any]] = []
    skipped = 0
    for row in rows:
        home_id = team_map.get(row["home_team_external_id"])
        away_id = team_map.get(row["away_team_external_id"])
        if home_id is None or away_id is None:
            skipped += 1
            log.warning(
                "match_team_unresolved",
                extra={
                    "match_external_id": row["external_id"],
                    "home_team_external_id": row["home_team_external_id"],
                    "away_team_external_id": row["away_team_external_id"],
                },
            )
            continue
        prepared.append(
            {
                "external_id": row["external_id"],
                "league_id": league_id,
                "home_team_id": home_id,
                "away_team_id": away_id,
                "season": season,
                "matchday": row["matchday"],
                "kickoff_datetime": row["kickoff_datetime"],
                "home_score": row["home_score"],
                "away_score": row["away_score"],
                "status": row["status"],
            }
        )

    existing = await _existing_single(
        session, matches, "external_id", [r["external_id"] for r in prepared]
    )
    result = await _upsert(
        session,
        matches,
        prepared,
        conflict_cols=["external_id"],
        update_cols=[
            "league_id", "home_team_id", "away_team_id", "season", "matchday",
            "kickoff_datetime", "home_score", "away_score", "status",
        ],
        existing=existing,
        key_of=lambda r: r["external_id"],
    )
    result.skipped = skipped
    result.deleted = await _prune(
        session,
        matches,
        league_id=league_id,
        season=season,
        keep_col="external_id",
        keep_values=[r["external_id"] for r in prepared],
    )
    return result
