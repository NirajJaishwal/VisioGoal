"""create_initial_schema

Creates the six MVP tables: leagues, teams, matches, standings, documents,
chat_messages — with foreign keys and indexes on FK / season fields.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- leagues ---
    op.create_table(
        "leagues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_leagues_season", "leagues", ["season"])

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("short_name", sa.String(length=60), nullable=True),
        sa.Column("crest_url", sa.String(length=500), nullable=True),
        sa.Column("venue", sa.String(length=160), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_teams_league_id", "teams", ["league_id"])

    # --- matches ---
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "home_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "away_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("matchday", sa.Integer(), nullable=True),
        sa.Column("kickoff_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="SCHEDULED",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_matches_league_id", "matches", ["league_id"])
    op.create_index("ix_matches_home_team_id", "matches", ["home_team_id"])
    op.create_index("ix_matches_away_team_id", "matches", ["away_team_id"])
    op.create_index("ix_matches_matchday", "matches", ["matchday"])
    op.create_index("ix_matches_kickoff_datetime", "matches", ["kickoff_datetime"])

    # --- standings ---
    op.create_table(
        "standings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("played", sa.Integer(), server_default="0", nullable=False),
        sa.Column("won", sa.Integer(), server_default="0", nullable=False),
        sa.Column("drawn", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("goals_for", sa.Integer(), server_default="0", nullable=False),
        sa.Column("goals_against", sa.Integer(), server_default="0", nullable=False),
        sa.Column("points", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "league_id", "team_id", "season", name="uq_standings_team_season"
        ),
    )
    op.create_index("ix_standings_league_id", "standings", ["league_id"])
    op.create_index("ix_standings_team_id", "standings", ["team_id"])
    op.create_index("ix_standings_season", "standings", ["season"])

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chroma_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_entity_type", "documents", ["entity_type"])
    op.create_index("ix_documents_entity_id", "documents", ["entity_id"])
    op.create_index("ix_documents_chroma_id", "documents", ["chroma_id"], unique=True)

    # --- chat_messages ---
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_documents_chroma_id", table_name="documents")
    op.drop_index("ix_documents_entity_id", table_name="documents")
    op.drop_index("ix_documents_entity_type", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_standings_season", table_name="standings")
    op.drop_index("ix_standings_team_id", table_name="standings")
    op.drop_index("ix_standings_league_id", table_name="standings")
    op.drop_table("standings")

    op.drop_index("ix_matches_kickoff_datetime", table_name="matches")
    op.drop_index("ix_matches_matchday", table_name="matches")
    op.drop_index("ix_matches_away_team_id", table_name="matches")
    op.drop_index("ix_matches_home_team_id", table_name="matches")
    op.drop_index("ix_matches_league_id", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_teams_league_id", table_name="teams")
    op.drop_table("teams")

    op.drop_index("ix_leagues_season", table_name="leagues")
    op.drop_table("leagues")
