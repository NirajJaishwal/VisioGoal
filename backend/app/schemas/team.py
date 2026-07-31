"""Team API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TeamRef(BaseModel):
    """Compact team reference embedded in standings and matches."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Internal team id.")
    name: str = Field(description="Full team name.")
    short_name: str | None = Field(default=None, description="Abbreviation / short name.")
    crest_url: str | None = Field(default=None, description="URL of the team crest image.")


class TeamRead(BaseModel):
    """A club as exposed by the API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 5,
                "external_id": 57,
                "league_id": 1,
                "name": "Arsenal FC",
                "short_name": "ARS",
                "crest_url": "https://crests.football-data.org/57.png",
                "venue": "Emirates Stadium",
            }
        },
    )

    id: int = Field(description="Internal team id.")
    external_id: int = Field(description="Data-provider team id.")
    league_id: int = Field(description="Id of the league the team belongs to.")
    name: str = Field(description="Full team name.")
    short_name: str | None = Field(default=None, description="Abbreviation / short name.")
    crest_url: str | None = Field(default=None, description="URL of the team crest image.")
    venue: str | None = Field(default=None, description="Home stadium name.")
