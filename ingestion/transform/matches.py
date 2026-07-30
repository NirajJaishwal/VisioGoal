"""Transform a Football-Data.org matches payload into `matches` rows.

Pure function: raw provider JSON in, plain dicts out. Team references are kept
as *provider* ids (`home_team_external_id` / `away_team_external_id`); the loader
resolves them to internal ids.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_utc(value: str | None) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp (…Z) into a timezone-aware datetime."""
    if not value:
        return None
    # Python's fromisoformat accepts the offset form, not the trailing "Z".
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def transform_matches(matches_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a `/competitions/{code}/matches` payload to `matches` row dicts."""
    rows: list[dict[str, Any]] = []
    for match in matches_payload.get("matches", []):
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        full_time = (match.get("score") or {}).get("fullTime") or {}
        rows.append(
            {
                "external_id": match["id"],
                "home_team_external_id": home.get("id"),
                "away_team_external_id": away.get("id"),
                "matchday": match.get("matchday"),
                "kickoff_datetime": _parse_utc(match.get("utcDate")),
                "home_score": full_time.get("home"),
                "away_score": full_time.get("away"),
                "status": match.get("status", "SCHEDULED"),
            }
        )
    return rows
