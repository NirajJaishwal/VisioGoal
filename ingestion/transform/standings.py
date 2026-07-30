"""Transform a Football-Data.org standings payload into `standings` rows.

Pure function: raw provider JSON in, plain dicts out. Each row carries the
team's *provider* id (`team_external_id`); the loader resolves it to our
internal team id, keeping transformation free of database state.
"""

from __future__ import annotations

from typing import Any


def transform_standings(
    standings_payload: dict[str, Any], season: int
) -> list[dict[str, Any]]:
    """Map a `/competitions/{code}/standings` payload to `standings` row dicts.

    Only the overall table (`type == "TOTAL"`) is used for the MVP; home/away
    splits are ignored.
    """
    rows: list[dict[str, Any]] = []
    for group in standings_payload.get("standings", []):
        if group.get("type") != "TOTAL":
            continue
        for entry in group.get("table", []):
            team = entry.get("team") or {}
            rows.append(
                {
                    "team_external_id": team.get("id"),
                    "season": season,
                    "position": entry.get("position"),
                    "played": entry.get("playedGames", 0),
                    "won": entry.get("won", 0),
                    "drawn": entry.get("draw", 0),
                    "lost": entry.get("lost", 0),
                    "goals_for": entry.get("goalsFor", 0),
                    "goals_against": entry.get("goalsAgainst", 0),
                    "points": entry.get("points", 0),
                }
            )
    return rows
