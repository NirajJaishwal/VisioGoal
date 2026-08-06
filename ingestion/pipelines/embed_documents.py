"""Embed pipeline — generate readable summaries and populate the vector store.

Runs *after* the data refresh: reads the loaded football data from PostgreSQL,
writes one natural-language summary per team, league, and finished match, embeds
them with the local Sentence-Transformers model, and upserts both the vectors
(ChromaDB) and their source text (the `documents` table).

Idempotent — deterministic doc ids mean re-runs overwrite in place. Run with:

    python -m pipelines.embed_documents
"""

from __future__ import annotations

import asyncio
import time

from sqlalchemy import func, select

from common.config import settings
from common.logging import configure_logging, get_logger, log_event
from embed.embedder import Embedder
from embed.store import upsert_documents
from embed.summaries import Doc, league_doc, match_doc, team_doc, trend_doc
from load.db import AsyncSessionLocal
from load.tables import leagues, matches, standings, teams

log = get_logger("pipelines.embed_documents")


def _print(message: str) -> None:
    print(message, flush=True)


async def _rows(session, stmt) -> list[dict]:
    """Execute a Core `select` and return plain dicts."""
    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result]


async def _target_season(session) -> int | None:
    """The season to embed: the configured pin, else the newest we have."""
    if settings.football_data_season is not None:
        return settings.football_data_season
    return await session.scalar(select(func.max(standings.c.season)))


async def _target_seasons(session) -> list[int]:
    if settings.football_data_start_season is not None:
        return [s for s in settings.football_data_seasons if s is not None]
    rows = await session.execute(select(standings.c.season).distinct().order_by(standings.c.season))
    return [row[0] for row in rows]


async def _build_docs(session, season: int) -> list[Doc]:
    """Assemble team, league, and match summaries for one season."""
    league_rows = await _rows(session, select(leagues))
    leagues_by_id = {row["id"]: row for row in league_rows}

    team_rows = await _rows(session, select(teams))
    teams_by_id = {row["id"]: row for row in team_rows}

    standing_rows = await _rows(
        session, select(standings).where(standings.c.season == season)
    )
    match_rows = await _rows(
        session,
        select(matches).where(
            matches.c.season == season,
            matches.c.status == "FINISHED",
            matches.c.home_score.is_not(None),
            matches.c.away_score.is_not(None),
        ),
    )

    docs: list[Doc] = []

    # Group standings by league for both team docs and the league overview.
    by_league: dict[int, list[dict]] = {}
    for standing in standing_rows:
        by_league.setdefault(standing["league_id"], []).append(standing)

    for league_id, rows in by_league.items():
        league = leagues_by_id.get(league_id)
        if league is None:
            continue
        league_view = {**league, "season": season}
        for standing in rows:
            team = teams_by_id.get(standing["team_id"])
            if team is not None:
                docs.append(team_doc(team, standing, league_view))
        names = {r["team_id"]: teams_by_id.get(r["team_id"], {}).get("name", "?") for r in rows}
        docs.append(league_doc(league_view, rows, names))

    for match in match_rows:
        league = leagues_by_id.get(match["league_id"])
        home = teams_by_id.get(match["home_team_id"])
        away = teams_by_id.get(match["away_team_id"])
        if league is None or home is None or away is None:
            continue
        league_view = {**league, "season": season}
        docs.append(match_doc(match, home["name"], away["name"], league_view))

    return docs


async def run() -> int:
    """Embed every summary for the target season; return the document count."""
    configure_logging()
    start = time.monotonic()
    _print("Football embed pipeline — generating summaries and vectors")

    async with AsyncSessionLocal() as session:
        seasons = await _target_seasons(session)
        if not seasons:
            _print("No standings found — run the data refresh first. Nothing to embed.")
            return 0

        _print(f"Target seasons: {', '.join(map(str, seasons))}")
        docs = []
        for season in seasons:
            docs.extend(await _build_docs(session, season))
        # Group duplicated clubs by provider id so trend docs span league-season rows.
        team_rows = await _rows(session, select(teams))
        standing_rows = await _rows(session, select(standings).where(standings.c.season.in_(seasons)))
        league_rows = await _rows(session, select(leagues))
        teams_by_id = {row["id"]: row for row in team_rows}
        by_provider: dict[int, list[dict]] = {}
        for row in standing_rows:
            team = teams_by_id.get(row["team_id"])
            if team:
                by_provider.setdefault(team["external_id"], []).append({**row, "team": team})
        league_by_id = {row["id"]: row for row in league_rows}
        for rows in by_provider.values():
            docs.append(trend_doc(rows[0]["team"], rows, league_by_id))
        _print(f"Built {len(docs)} summaries (teams + leagues + matches)")
        if not docs:
            return 0

        # Embed all summaries in one batch, then write vectors + source rows.
        embedder = Embedder()
        embeddings = embedder.embed([d.content for d in docs])
        embedder.upsert(
            ids=[d.doc_id for d in docs],
            embeddings=embeddings,
            documents=[d.content for d in docs],
            metadatas=[d.metadata for d in docs],
        )
        _print(f"Upserted {len(docs)} vectors into Chroma (total: {embedder.count()})")

        # Note: the reads above have already autobegun a transaction on this
        # session, so we commit directly rather than opening a nested
        # `session.begin()` block (which would raise "transaction already begun").
        written = await upsert_documents(
            session,
            [
                {
                    "entity_type": d.entity_type,
                    "entity_id": d.entity_id,
                    "content": d.content,
                    "chroma_id": d.doc_id,
                }
                for d in docs
            ],
        )
        await session.commit()
        _print(f"Mirrored {written} rows into the documents table")

    elapsed = time.monotonic() - start
    log_event(log, "embed_finished", seasons=seasons, documents=len(docs))
    _print(f"Completed in {elapsed:.1f}s")
    return len(docs)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
