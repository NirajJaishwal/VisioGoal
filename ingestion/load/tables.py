"""SQLAlchemy Core table definitions used by the loaders.

The ingestion package is decoupled from the backend, so it does not import the
backend ORM models. Instead it declares Core `Table` objects mirroring the
columns it reads/writes. The physical schema (and its constraints) is owned by
the backend's Alembic migrations — these definitions must stay in sync with them.

Only columns the pipeline touches are declared; DB-managed columns like
`created_at` (server default) are intentionally omitted from inserts.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

leagues = Table(
    "leagues",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("external_id", Integer, nullable=False),
    Column("name", String(120), nullable=False),
    Column("country", String(80), nullable=False),
    Column("season", Integer, nullable=False),
)

teams = Table(
    "teams",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("external_id", Integer, nullable=False),
    Column("league_id", Integer, ForeignKey("leagues.id"), nullable=False),
    Column("name", String(120), nullable=False),
    Column("short_name", String(60)),
    Column("crest_url", String(500)),
    Column("venue", String(160)),
    UniqueConstraint("external_id", "league_id", name="uq_teams_external_league"),
)

matches = Table(
    "matches",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("external_id", Integer, unique=True, nullable=False),
    Column("league_id", Integer, ForeignKey("leagues.id"), nullable=False),
    Column("home_team_id", Integer, ForeignKey("teams.id"), nullable=False),
    Column("away_team_id", Integer, ForeignKey("teams.id"), nullable=False),
    Column("season", Integer),
    Column("matchday", Integer),
    Column("kickoff_datetime", DateTime(timezone=True)),
    Column("home_score", Integer),
    Column("away_score", Integer),
    Column("status", String(30), nullable=False),
)

standings = Table(
    "standings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("league_id", Integer, ForeignKey("leagues.id"), nullable=False),
    Column("team_id", Integer, ForeignKey("teams.id"), nullable=False),
    Column("season", Integer, nullable=False),
    Column("position", Integer, nullable=False),
    Column("played", Integer, nullable=False),
    Column("won", Integer, nullable=False),
    Column("drawn", Integer, nullable=False),
    Column("lost", Integer, nullable=False),
    Column("goals_for", Integer, nullable=False),
    Column("goals_against", Integer, nullable=False),
    Column("points", Integer, nullable=False),
    UniqueConstraint("league_id", "team_id", "season", name="uq_standings_team_season"),
)

# Mirrors each embedded chunk's source text; `chroma_id` links to the vector in
# ChromaDB and is the idempotency key for the embed step (ON CONFLICT target).
documents = Table(
    "documents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("entity_type", String(40), nullable=False),
    Column("entity_id", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("chroma_id", String(100), unique=True),
)
