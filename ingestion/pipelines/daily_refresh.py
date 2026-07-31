"""Daily refresh pipeline.

Orchestrates the full ingestion flow for each configured competition:

    Fetch leagues → Fetch teams → Fetch standings → Fetch matches
                              → Transform → Store in PostgreSQL

Each competition is loaded inside a single transaction: on any failure that
competition rolls back cleanly and the run moves on to the next one (so one bad
league never aborts the whole refresh). Because every write is an idempotent
upsert, the pipeline is safe to re-run at any time.

Run it with:
    python -m pipelines.daily_refresh
"""

from __future__ import annotations

import asyncio
import time

from common.config import settings
from common.logging import configure_logging, get_logger, log_event
from load.db import AsyncSessionLocal
from load.loaders import (
    LoadResult,
    upsert_league,
    upsert_matches,
    upsert_standings,
    upsert_teams,
)
from sources.base import SourceError
from sources.football_data import FootballDataClient
from transform.leagues import transform_league
from transform.matches import transform_matches
from transform.standings import transform_standings
from transform.teams import transform_teams

log = get_logger("pipelines.daily_refresh")


def _print(message: str) -> None:
    """Human-readable progress to stdout (alongside the JSON logs)."""
    print(message, flush=True)


async def _process_competition(
    client: FootballDataClient, code: str, totals: dict[str, LoadResult]
) -> None:
    """Run fetch → transform → store for a single competition code."""
    _print(f"\n=== {code} ===")

    # Optional season pin: when set, every season-scoped endpoint and the league
    # row use it, so the whole dataset stays consistent. Unset → current season.
    season = settings.football_data_season

    # --- Fetch (each request is throttled + retried inside the client) ---
    competition = await client.get_competition(code)
    teams_payload = await client.get_teams(code, season=season)
    standings_payload = await client.get_standings(code, season=season)
    matches_payload = await client.get_matches(code, season=season)

    # --- Transform (pure, no I/O) ---
    league_row = transform_league(competition)
    if season is not None:
        # Keep the league row on the fetched season, not the API's current one.
        league_row["season"] = season
    standing_rows = transform_standings(standings_payload, league_row["season"])
    team_rows = transform_teams(teams_payload)
    match_rows = transform_matches(matches_payload)

    log_event(
        log,
        "records_fetched",
        competition=code,
        teams=len(team_rows),
        standings=len(standing_rows),
        matches=len(match_rows),
    )
    _print(
        f"[{code}] fetched: {len(team_rows)} teams, "
        f"{len(standing_rows)} standings, {len(match_rows)} matches"
    )

    # --- Store: one transaction per competition (rolls back on failure) ---
    load_season = league_row["season"]
    async with AsyncSessionLocal() as session:
        async with session.begin():
            league_id, league_res = await upsert_league(session, league_row)
            _report("leagues", code, league_res, totals)

            teams_res, team_map = await upsert_teams(session, league_id, team_rows)
            _report("teams", code, teams_res, totals)

            standings_res = await upsert_standings(
                session, league_id, load_season, standing_rows, team_map
            )
            _report("standings", code, standings_res, totals)

            matches_res = await upsert_matches(
                session, league_id, load_season, match_rows, team_map
            )
            _report("matches", code, matches_res, totals)
        # `session.begin()` commits here on success, or has rolled back on error.


def _report(
    entity: str, code: str, result: LoadResult, totals: dict[str, LoadResult]
) -> None:
    """Log + print a single entity's load result and fold it into the totals."""
    log_event(
        log,
        "records_loaded",
        competition=code,
        entity=entity,
        inserted=result.inserted,
        updated=result.updated,
        skipped=result.skipped,
        deleted=result.deleted,
    )
    _print(
        f"[{code}] {entity:<9} inserted={result.inserted} "
        f"updated={result.updated} deleted={result.deleted} "
        f"skipped={result.skipped}"
    )
    agg = totals.setdefault(entity, LoadResult())
    agg.inserted += result.inserted
    agg.updated += result.updated
    agg.skipped += result.skipped
    agg.deleted += result.deleted


async def run() -> dict[str, LoadResult]:
    """Execute the refresh for every configured competition; return totals."""
    configure_logging()
    start = time.monotonic()
    totals: dict[str, LoadResult] = {}

    _print("Football data ingestion — daily refresh")
    _print(f"Competitions: {', '.join(settings.football_data_competitions)}")
    log_event(
        log, "pipeline_started", competitions=settings.football_data_competitions
    )

    async with FootballDataClient() as client:
        for code in settings.football_data_competitions:
            try:
                await _process_competition(client, code, totals)
            except SourceError as exc:
                # Skip this competition, keep going with the rest.
                log_event(log, "competition_failed", competition=code, error=str(exc))
                _print(f"[{code}] FAILED: {exc}")

    elapsed = time.monotonic() - start
    _print("\n--- Summary ---")
    for entity, res in totals.items():
        _print(
            f"{entity:<9} inserted={res.inserted} updated={res.updated} "
            f"deleted={res.deleted} skipped={res.skipped}"
        )
    _print(f"Completed in {elapsed:.1f}s")
    log_event(
        log,
        "pipeline_finished",
        execution_seconds=round(elapsed, 2),
        totals={k: vars(v) for k, v in totals.items()},
    )
    return totals


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
