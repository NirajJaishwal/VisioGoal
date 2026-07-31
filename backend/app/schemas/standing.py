"""Standings API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.team import TeamRef


class StandingRead(BaseModel):
    """A single league-table row for a team in a season.

    Also carries the MVP's basic team stats (played, W/D/L, goals, points).
    `goal_difference` is derived (`goals_for - goals_against`).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "league_id": 1,
                "season": 2025,
                "position": 1,
                "team": {
                    "id": 5,
                    "name": "Arsenal FC",
                    "short_name": "ARS",
                    "crest_url": "https://crests.football-data.org/57.png",
                },
                "played": 38,
                "won": 28,
                "drawn": 6,
                "lost": 4,
                "goals_for": 91,
                "goals_against": 29,
                "goal_difference": 62,
                "points": 90,
            }
        }
    )

    league_id: int = Field(description="Id of the league this table belongs to.")
    season: int = Field(description="Season starting year.")
    position: int = Field(description="Table position (1 = top).")
    team: TeamRef = Field(description="The team occupying this row.")
    played: int = Field(description="Matches played.")
    won: int = Field(description="Matches won.")
    drawn: int = Field(description="Matches drawn.")
    lost: int = Field(description="Matches lost.")
    goals_for: int = Field(description="Goals scored.")
    goals_against: int = Field(description="Goals conceded.")
    goal_difference: int = Field(description="goals_for - goals_against.")
    points: int = Field(description="Total points.")
