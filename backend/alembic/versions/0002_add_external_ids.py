"""add_external_ids

Adds `external_id` columns to leagues, teams, and matches so the ingestion
pipeline can perform idempotent upserts keyed on the data provider's stable ids
(Football-Data.org). A unique index on each column both enforces "no duplicate
rows" and gives Postgres a conflict target for `INSERT ... ON CONFLICT`.

The `standings` table already has a natural unique key
(`uq_standings_team_season`), so it needs no external id.

Revision ID: 0002_external_ids
Revises: 0001_initial
Create Date: 2026-07-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_external_ids"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The tables are empty at first ingestion, so NOT NULL is safe to add
    # directly (no backfill required).
    op.add_column("leagues", sa.Column("external_id", sa.Integer(), nullable=False))
    op.add_column("teams", sa.Column("external_id", sa.Integer(), nullable=False))
    op.add_column("matches", sa.Column("external_id", sa.Integer(), nullable=False))

    op.create_index(
        "ix_leagues_external_id", "leagues", ["external_id"], unique=True
    )
    op.create_index("ix_teams_external_id", "teams", ["external_id"], unique=True)
    op.create_index(
        "ix_matches_external_id", "matches", ["external_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_matches_external_id", table_name="matches")
    op.drop_index("ix_teams_external_id", table_name="teams")
    op.drop_index("ix_leagues_external_id", table_name="leagues")

    op.drop_column("matches", "external_id")
    op.drop_column("teams", "external_id")
    op.drop_column("leagues", "external_id")
