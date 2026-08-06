"""Hybrid retrieval for the football analyst copilot.

Two complementary sources are combined into a single grounded context block:

1. **Structured retrieval** (SQL over PostgreSQL) — the authoritative numbers:
   league standings (position, played, W/D/L, goals, points) and recent match
   results. This is deterministic truth the model must not contradict.

2. **Semantic retrieval** (ChromaDB) — natural-language summaries of teams,
   leagues, and matches, ranked by similarity to the question. These surface the
   *relevant* entities and double as the retrieval that scopes the SQL: the
   leagues a semantic hit points at are the leagues whose full tables we pull.

The two are assembled by `retrieve()` into a `Retrieval` (context text + a list
of human-readable citations). Embedding and the Chroma call are synchronous
(sentence-transformers / chromadb), so they run in a threadpool to avoid
blocking the event loop; the SQL uses the async session directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.ai import embeddings, vectorstore
from app.models.league import League
from app.models.match import Match
from app.models.standing import Standing
from app.models.team import Team

# How many semantic neighbours to pull, how many leagues' tables to include when
# scoped by those neighbours, and how many recent results per league to show.
_SEMANTIC_RESULTS = 6
_MAX_SCOPED_LEAGUES = 3
_RECENT_MATCHES_PER_LEAGUE = 8


@dataclass
class Retrieval:
    """The assembled grounding for one question."""

    context: str
    citations: list[str] = field(default_factory=list)


async def retrieve(session: AsyncSession, query: str) -> Retrieval:
    """Build grounded context (structured + semantic) for a user question."""
    semantic_docs, semantic_meta = await _semantic(query)

    scopes = await _resolve_scopes(session, semantic_meta)

    blocks: list[str] = []
    citations: list[str] = []

    for league, season in scopes:
        table = await _standings_block(session, league, season)
        if table:
            blocks.append(table)
            citations.append(f"{league.name} {season} Standings")
        results = await _recent_results_block(session, league, season)
        if results:
            blocks.append(results)

    if semantic_docs:
        blocks.append(
            "=== Related summaries (semantic search) ===\n"
            + "\n".join(f"- {doc}" for doc in semantic_docs)
        )
        for meta in semantic_meta:
            source = (meta or {}).get("source")
            if source and source not in citations:
                citations.append(source)

    return Retrieval(context="\n\n".join(blocks), citations=citations)


# --- semantic side ---------------------------------------------------------
async def _semantic(query: str) -> tuple[list[str], list[dict]]:
    """Return the top-N semantic documents and their metadata (threadpooled).

    Any failure to reach the vector store degrades to empty results — the
    structured SQL side still grounds the answer, so the copilot keeps working.
    """
    try:
        embedding = await run_in_threadpool(embeddings.embed_text, query)
        result = await run_in_threadpool(
            vectorstore.query, embedding, _SEMANTIC_RESULTS
        )
    except Exception:  # noqa: BLE001 - degrade gracefully if Chroma is unreachable
        return [], []

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    # Pad metadata so the two lists stay index-aligned.
    metadatas = list(metadatas) + [{}] * (len(documents) - len(metadatas))
    return list(documents), metadatas


# --- scope resolution ------------------------------------------------------
async def _resolve_scopes(
    session: AsyncSession, metadatas: list[dict]
) -> list[tuple[League, int]]:
    """Decide which (league, season) tables to include.

    Preference order:
      1. The distinct leagues referenced by the semantic hits (capped), each at
         the newest season we have standings for — a focused, on-topic answer.
      2. Fallback: every league at its latest season — for broad questions
         ("summarize the season") where no single entity was matched.
    """
    requested: list[tuple[int, int]] = []
    for meta in metadatas:
        lid, season = (meta or {}).get("league_id"), (meta or {}).get("season")
        if isinstance(lid, int) and isinstance(season, int) and (lid, season) not in requested:
            requested.append((lid, season))

    if requested:
        requested = requested[:_MAX_SCOPED_LEAGUES * 3]
        leagues = await _leagues_by_id(session, [lid for lid, _ in requested])
        by_id = {league.id: league for league in leagues}
        return [(by_id[lid], season) for lid, season in requested if lid in by_id]
    leagues = await _all_leagues(session)

    scopes: list[tuple[League, int]] = []
    for league in leagues:
        season = await _latest_season(session, league.id)
        if season is not None:
            scopes.append((league, season))
    return scopes


async def _leagues_by_id(
    session: AsyncSession, league_ids: list[int]
) -> list[League]:
    result = await session.execute(select(League).where(League.id.in_(league_ids)))
    by_id = {league.id: league for league in result.scalars()}
    # Preserve the semantic ranking order.
    return [by_id[lid] for lid in league_ids if lid in by_id]


async def _all_leagues(session: AsyncSession) -> list[League]:
    result = await session.execute(select(League).order_by(League.name))
    return list(result.scalars())


async def _latest_season(session: AsyncSession, league_id: int) -> int | None:
    return await session.scalar(
        select(Standing.season)
        .where(Standing.league_id == league_id)
        .order_by(Standing.season.desc())
        .limit(1)
    )


# --- structured side -------------------------------------------------------
async def _standings_block(
    session: AsyncSession, league: League, season: int
) -> str:
    """Render one league's full table for a season as a compact text block."""
    stmt = (
        select(Standing, Team)
        .join(Team, Team.id == Standing.team_id)
        .where(Standing.league_id == league.id, Standing.season == season)
        .order_by(Standing.position.asc())
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return ""

    lines = [f"=== {league.name} ({league.country}) {season} Standings ==="]
    for standing, team in rows:
        gd = standing.goals_for - standing.goals_against
        lines.append(
            f"{standing.position:>2}. {team.name:<26} "
            f"P{standing.played:<2} W{standing.won:<2} D{standing.drawn:<2} "
            f"L{standing.lost:<2} GF{standing.goals_for:<3} GA{standing.goals_against:<3} "
            f"GD{gd:+d} Pts{standing.points}"
        )
    return "\n".join(lines)


async def _recent_results_block(
    session: AsyncSession, league: League, season: int
) -> str:
    """Render the most recent finished results for a league/season."""
    stmt = (
        select(Match)
        .where(
            Match.league_id == league.id,
            Match.season == season,
            Match.status == "FINISHED",
        )
        .order_by(Match.kickoff_datetime.desc())
        .limit(_RECENT_MATCHES_PER_LEAGUE)
    )
    matches = list((await session.execute(stmt)).scalars())
    if not matches:
        return ""

    # Resolve team names in one round-trip.
    team_ids = {m.home_team_id for m in matches} | {m.away_team_id for m in matches}
    names = await _team_names(session, team_ids)

    lines = [f"=== {league.name} {season} — Recent Results ==="]
    for m in matches:
        when = m.kickoff_datetime.date().isoformat() if m.kickoff_datetime else "—"
        home = names.get(m.home_team_id, f"Team {m.home_team_id}")
        away = names.get(m.away_team_id, f"Team {m.away_team_id}")
        lines.append(f"{when}  {home} {m.home_score}-{m.away_score} {away}")
    return "\n".join(lines)


async def _team_names(session: AsyncSession, team_ids: set[int]) -> dict[int, str]:
    if not team_ids:
        return {}
    result = await session.execute(
        select(Team.id, Team.name).where(Team.id.in_(team_ids))
    )
    return {tid: name for tid, name in result.all()}
