"""Transform a Football-Data.org teams payload into `teams` rows.

Pure function: raw provider JSON in, plain dicts matching our schema out. The
internal `league_id` foreign key is not set here — the loader assigns it, so
transformation stays independent of database state.
"""

from __future__ import annotations

from typing import Any


def transform_teams(teams_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a `/competitions/{code}/teams` payload to `teams` row dicts."""
    rows: list[dict[str, Any]] = []
    for team in teams_payload.get("teams", []):
        rows.append(
            {
                "external_id": team["id"],
                "name": team["name"],
                # Prefer the three-letter abbreviation, fall back to shortName.
                "short_name": team.get("tla") or team.get("shortName"),
                "crest_url": team.get("crest"),
                "venue": team.get("venue"),
            }
        )
    return rows
