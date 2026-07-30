"""League model — a competition/season (e.g. Premier League 2024)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.standing import Standing
    from app.models.team import Team


class League(Base, TimestampMixin):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    # Season stored as the starting year, e.g. 2024 for the 2024/25 season.
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    teams: Mapped[list["Team"]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )
    matches: Mapped[list["Match"]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )
    standings: Mapped[list["Standing"]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<League id={self.id} name={self.name!r} season={self.season}>"
