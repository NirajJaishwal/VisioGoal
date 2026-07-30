"""Transform a Football-Data.org competition payload into a `leagues` row.

Pure function: raw provider JSON in, a plain dict matching our schema out. No
API calls, no database access.
"""

from __future__ import annotations

from typing import Any


def season_start_year(competition: dict[str, Any]) -> int:
    """Derive the season's starting year from the competition's current season.

    Football-Data returns `currentSeason.startDate` as an ISO date string
    (e.g. "2024-08-16"); the leading year is our `season` value.
    """
    current = competition.get("currentSeason") or {}
    start_date = current.get("startDate")
    if not start_date:
        raise ValueError("competition payload is missing currentSeason.startDate")
    return int(str(start_date)[:4])


def transform_league(competition: dict[str, Any]) -> dict[str, Any]:
    """Map a competition payload to a `leagues` row dict."""
    area = competition.get("area") or {}
    return {
        "external_id": competition["id"],
        "name": competition["name"],
        "country": area.get("name") or "Unknown",
        "season": season_start_year(competition),
    }
