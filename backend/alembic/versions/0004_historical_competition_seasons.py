"""allow provider competitions and teams to exist in multiple seasons

Revision ID: 0004_historical_seasons
Revises: 0003_match_season
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0004_historical_seasons"
down_revision: Union[str, None] = "0003_match_season"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_leagues_external_id", table_name="leagues")
    op.create_index("ix_leagues_external_id", "leagues", ["external_id"])
    op.create_unique_constraint("uq_leagues_external_season", "leagues", ["external_id", "season"])
    op.drop_index("ix_teams_external_id", table_name="teams")
    op.create_index("ix_teams_external_id", "teams", ["external_id"])
    op.create_unique_constraint("uq_teams_external_league", "teams", ["external_id", "league_id"])


def downgrade() -> None:
    op.drop_constraint("uq_teams_external_league", "teams", type_="unique")
    op.drop_index("ix_teams_external_id", table_name="teams")
    op.create_index("ix_teams_external_id", "teams", ["external_id"], unique=True)
    op.drop_constraint("uq_leagues_external_season", "leagues", type_="unique")
    op.drop_index("ix_leagues_external_id", table_name="leagues")
    op.create_index("ix_leagues_external_id", "leagues", ["external_id"], unique=True)
