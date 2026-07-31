"""End-to-end smoke test for the ingestion setup.

Verifies, in order:
  1. Database connectivity  (SELECT 1 through the async engine)
  2. API connectivity       (one authenticated Football-Data.org request)
  3. Leagues inserted       (ingest one competition's league row, then count)
  4. Teams inserted         (ingest that competition's teams, then count)

It ingests a single probe competition (default: PL) end-to-end, so a pass means
fetch → transform → upsert → read-back all work. Writes are idempotent, so the
script is safe to run repeatedly. Exits non-zero if any check fails.

Run it with:
    python -m scripts.verify_setup
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import func, select, text

from common.config import settings
from common.logging import configure_logging
from load.db import AsyncSessionLocal, engine
from load.loaders import upsert_league, upsert_teams
from load.tables import leagues, teams
from sources.football_data import FootballDataClient
from transform.leagues import transform_league
from transform.teams import transform_teams

PROBE_CODE = "PL"


def _ok(label: str, detail: str = "") -> None:
    print(f"  [PASS] {label}{f' — {detail}' if detail else ''}", flush=True)


def _fail(label: str, detail: str = "") -> None:
    print(f"  [FAIL] {label}{f' — {detail}' if detail else ''}", flush=True)


async def _check_database() -> bool:
    try:
        async with engine.connect() as conn:
            value = await conn.scalar(text("SELECT 1"))
        assert value == 1
        _ok("Database connectivity")
        return True
    except Exception as exc:  # noqa: BLE001 - report any failure to the operator
        _fail("Database connectivity", repr(exc))
        return False


async def _check_api_and_ingest() -> bool:
    if not settings.has_api_key:
        _fail("API connectivity", "FOOTBALL_DATA_API_KEY is not set in the environment")
        return False

    try:
        async with FootballDataClient() as client:
            competition = await client.get_competition(PROBE_CODE)
            _ok("API connectivity", f"fetched competition {competition.get('name')!r}")
            teams_payload = await client.get_teams(
                PROBE_CODE, season=settings.football_data_season
            )
    except Exception as exc:  # noqa: BLE001
        _fail("API connectivity", repr(exc))
        return False

    # --- Ingest the probe league + teams, then read the counts back ---
    try:
        league_row = transform_league(competition)
        if settings.football_data_season is not None:
            league_row["season"] = settings.football_data_season
        team_rows = transform_teams(teams_payload)
        async with AsyncSessionLocal() as session:
            async with session.begin():
                league_id, _ = await upsert_league(session, league_row)
                await upsert_teams(session, league_id, team_rows)

            league_count = await session.scalar(
                select(func.count()).select_from(leagues)
            )
            team_count = await session.scalar(
                select(func.count()).select_from(teams).where(
                    teams.c.league_id == league_id
                )
            )
    except Exception as exc:  # noqa: BLE001
        _fail("Insert leagues/teams", repr(exc))
        return False

    passed = True
    if league_count and league_count >= 1:
        _ok("Leagues inserted", f"{league_count} league row(s) in DB")
    else:
        _fail("Leagues inserted", "no league rows found")
        passed = False

    if team_count and team_count >= 1:
        _ok("Teams inserted", f"{team_count} team(s) for {PROBE_CODE}")
    else:
        _fail("Teams inserted", "no team rows found")
        passed = False

    return passed


async def run() -> int:
    configure_logging()
    print("Ingestion setup verification\n")

    db_ok = await _check_database()
    if not db_ok:
        print("\nResult: FAIL (database unreachable — cannot verify inserts)")
        return 1

    ingest_ok = await _check_api_and_ingest()

    print()
    if db_ok and ingest_ok:
        print("Result: PASS — all checks succeeded")
        return 0
    print("Result: FAIL — see failed checks above")
    return 1


def main() -> None:
    sys.exit(asyncio.run(run()))


if __name__ == "__main__":
    main()
