"""Team model — a club competing in a league."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.league import League
    from app.models.match import Match
    from app.models.standing import Standing


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable id from the external data provider (Football-Data.org team id). Used
    # to resolve match/standing team references to internal ids across endpoints.
    external_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(60))
    crest_url: Mapped[str | None] = mapped_column(String(500))
    venue: Mapped[str | None] = mapped_column(String(160))

    league: Mapped["League"] = relationship(back_populates="teams")
    home_matches: Mapped[list["Match"]] = relationship(
        back_populates="home_team", foreign_keys="Match.home_team_id"
    )
    away_matches: Mapped[list["Match"]] = relationship(
        back_populates="away_team", foreign_keys="Match.away_team_id"
    )
    standings: Mapped[list["Standing"]] = relationship(back_populates="team")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Team id={self.id} name={self.name!r}>"
