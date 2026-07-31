"""Match API schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.team import TeamRef


class MatchStatus(str, Enum):
    """Match lifecycle states (mirrors the data provider's states)."""

    SCHEDULED = "SCHEDULED"
    TIMED = "TIMED"
    IN_PLAY = "IN_PLAY"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    SUSPENDED = "SUSPENDED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    AWARDED = "AWARDED"


class MatchRead(BaseModel):
    """A single fixture/result as exposed by the API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 101,
                "external_id": 537785,
                "league_id": 1,
                "season": 2025,
                "matchday": 1,
                "status": "FINISHED",
                "kickoff_datetime": "2025-08-15T19:00:00Z",
                "home_team": {"id": 5, "name": "Liverpool FC", "short_name": "LIV"},
                "away_team": {"id": 9, "name": "AFC Bournemouth", "short_name": "BOU"},
                "home_score": 4,
                "away_score": 2,
            }
        }
    )

    id: int = Field(description="Internal match id.")
    external_id: int = Field(description="Data-provider match id.")
    league_id: int = Field(description="Id of the league the match belongs to.")
    season: int | None = Field(default=None, description="Season starting year.")
    matchday: int | None = Field(default=None, description="Matchday / round number.")
    status: str = Field(description="Match status, e.g. SCHEDULED or FINISHED.")
    kickoff_datetime: datetime | None = Field(
        default=None, description="Kick-off time (UTC)."
    )
    home_team: TeamRef = Field(description="Home team.")
    away_team: TeamRef = Field(description="Away team.")
    home_score: int | None = Field(default=None, description="Full-time home goals.")
    away_score: int | None = Field(default=None, description="Full-time away goals.")
