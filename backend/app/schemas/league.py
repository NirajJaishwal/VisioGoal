"""League API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LeagueRead(BaseModel):
    """A competition/season as exposed by the API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "external_id": 2021,
                "name": "Premier League",
                "country": "England",
                "season": 2025,
            }
        },
    )

    id: int = Field(description="Internal league id.")
    external_id: int = Field(description="Data-provider competition id.")
    name: str = Field(description="League name, e.g. 'Premier League'.")
    country: str = Field(description="Country the league belongs to.")
    season: int = Field(description="Season starting year, e.g. 2025 for 2025/26.")
