"""Match model — a single fixture between two teams."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.league import League
    from app.models.team import Team


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable id from the external data provider (Football-Data.org match id).
    external_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    matchday: Mapped[int | None] = mapped_column(Integer, index=True)
    kickoff_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    # e.g. SCHEDULED / IN_PLAY / FINISHED (mirrors the data provider's states).
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="SCHEDULED"
    )

    league: Mapped["League"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(
        back_populates="home_matches", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        back_populates="away_matches", foreign_keys=[away_team_id]
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Match id={self.id} {self.home_team_id} v {self.away_team_id} "
            f"status={self.status!r}>"
        )
