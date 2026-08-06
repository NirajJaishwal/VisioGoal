"""Discover Football-Data.org access granted to the configured API key.

The provider's catalogue varies by subscription, so this script intentionally
does not assume that player, squad, lineup, coach, or head-to-head endpoints
exist.  It makes a small, throttled set of read-only requests, classifies each
response, and writes a JSON report suitable for deciding which optional data
to ingest.

Run with::

    python -m scripts.probe_capabilities
    python -m scripts.probe_capabilities --output /tmp/football-data-capabilities.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.config import settings
from common.logging import configure_logging
from sources.football_data import FootballDataClient


def _classification(status: int) -> str:
    if 200 <= status < 300:
        return "supported"
    if status in {401, 403}:
        return "subscription_restriction"
    if status == 404:
        return "unsupported"
    if status == 429:
        return "rate_limited"
    return "error"


async def _probe(
    client: FootballDataClient,
    name: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    status, payload, headers = await client.probe(path, params)
    return (
        {
            "endpoint": name,
            "path": path,
            "params": params or {},
            "status": _classification(status),
            "http_status": status,
            "rate_limit_headers": headers,
        },
        payload,
    )


async def run() -> dict[str, Any]:
    """Probe common provider resources and return the capability report."""
    configure_logging()
    if not settings.has_api_key:
        raise RuntimeError("FOOTBALL_DATA_API_KEY is not configured")

    code = settings.football_data_competitions[0]
    season = settings.football_data_season
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "competition_code": code,
        "historical_season_tested": season,
        "endpoints": [],
        "historical_availability": "not_tested",
    }

    async with FootballDataClient() as client:
        for name, path, params in [
            ("competitions", "/competitions", None),
            ("areas", "/areas", None),
            ("competition", f"/competitions/{code}", None),
            ("teams", f"/competitions/{code}/teams", {"season": season} if season else None),
            ("standings", f"/competitions/{code}/standings", {"season": season} if season else None),
            ("matches", f"/competitions/{code}/matches", {"season": season} if season else None),
            ("scorers", f"/competitions/{code}/scorers", {"season": season} if season else None),
        ]:
            entry, payload = await _probe(client, name, path, params)
            report["endpoints"].append(entry)
            if name == "matches":
                report["historical_availability"] = (
                    "available" if entry["status"] == "supported" and season else "not_available"
                )
            if name == "teams" and payload:
                team_rows = payload.get("teams") or []
                if team_rows:
                    report["sample_team_id"] = team_rows[0].get("id")
            if name == "matches" and payload:
                match_rows = payload.get("matches") or []
                if match_rows:
                    report["sample_match_id"] = match_rows[0].get("id")

        team_id = report.get("sample_team_id")
        if team_id:
            for name, path in [
                ("player_information", f"/teams/{team_id}"),
                ("squad", f"/teams/{team_id}/squad"),
                ("coaches", f"/teams/{team_id}/coaches"),
            ]:
                entry, _ = await _probe(client, name, path)
                report["endpoints"].append(entry)

        match_id = report.get("sample_match_id")
        if match_id:
            for name, path in [
                ("match_information", f"/matches/{match_id}"),
                ("head_to_head", f"/matches/{match_id}/head2head"),
                ("lineups", f"/matches/{match_id}/lineups"),
                ("statistics", f"/matches/{match_id}/statistics"),
            ]:
                entry, _ = await _probe(client, name, path)
                report["endpoints"].append(entry)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("capability-report.json"),
        help="JSON report path (default: capability-report.json).",
    )
    args = parser.parse_args()
    report = asyncio.run(run())
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
