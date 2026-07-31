"""add_match_season

Adds a `season` column to `matches` so ingestion can scope its per-season
cleanup to exactly one season (delete/replace) without ever touching other
seasons. `standings` and `leagues` already carry `season`; this makes `matches`
symmetric.

Existing rows are backfilled from the kickoff year using the European-season
convention (a season starting in year Y runs Aug Y → May Y+1): months July or
later belong to season Y, earlier months to season Y-1. The column is left
nullable so the migration is safe on any existing data; the loader always
populates it for newly ingested matches.

Revision ID: 0003_match_season
Revises: 0002_external_ids
Create Date: 2026-07-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_match_season"
down_revision: Union[str, None] = "0002_external_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("season", sa.Integer(), nullable=True))
    op.create_index("ix_matches_season", "matches", ["season"])

    # Backfill existing rows from their kickoff year (best effort; only where a
    # kickoff time is known). Newly ingested rows get `season` from the loader.
    op.execute(
        """
        UPDATE matches
        SET season = CASE
            WHEN EXTRACT(MONTH FROM kickoff_datetime) >= 7
                THEN EXTRACT(YEAR FROM kickoff_datetime)
            ELSE EXTRACT(YEAR FROM kickoff_datetime) - 1
        END
        WHERE kickoff_datetime IS NOT NULL AND season IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_matches_season", table_name="matches")
    op.drop_column("matches", "season")
