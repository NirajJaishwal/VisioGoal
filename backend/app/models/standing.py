"""Standing model — a team's league-table row for a season.

This table also carries the MVP's "basic team statistics" (played, W/D/L,
goals for/against, points), so no separate team_stats table is needed yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.league import League
    from app.models.team import Team


class Standing(Base, TimestampMixin):
    __tablename__ = "standings"
    __table_args__ = (
        # One row per team per league-season → safe idempotent upserts later.
        UniqueConstraint("league_id", "team_id", "season", name="uq_standings_team_season"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    played: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    won: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    drawn: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    lost: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    league: Mapped["League"] = relationship(back_populates="standings")
    team: Mapped["Team"] = relationship(back_populates="standings")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Standing team={self.team_id} pos={self.position} pts={self.points}>"
