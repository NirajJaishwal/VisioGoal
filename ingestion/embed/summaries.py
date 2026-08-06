"""Turn database rows into readable natural-language summaries for embedding.

Per the RAG design we embed *sentences a human would write*, not raw SQL rows —
e.g. "Liverpool finished 1st with 84 points, scored 86 goals and conceded 41."
Similarity search over prose matches how people ask questions far better than
search over column values would.

Each builder returns a `Doc`: a deterministic id (so re-runs upsert in place),
the entity link (for the `documents` mirror table), the text to embed, the
metadata stored alongside the vector (used by the API to scope SQL + cite
sources), and a human-readable `source` label for citations.

These are pure functions — the pipeline supplies plain dicts read from the DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Doc:
    doc_id: str
    entity_type: str
    entity_id: int
    content: str
    metadata: dict[str, Any]
    source: str


def _ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 11 -> '11th' ..."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def team_doc(team: dict, standing: dict, league: dict) -> Doc:
    """One team's season in prose: placement, record, goals, form."""
    season = standing["season"]
    pos = standing["position"]
    gd = standing["goals_for"] - standing["goals_against"]
    content = (
        f"{team['name']} play in the {league['name']} ({league['country']}) in the "
        f"{season} season. They are {_ordinal(pos)} with {standing['points']} points "
        f"from {standing['played']} matches ({standing['won']} wins, "
        f"{standing['drawn']} draws, {standing['lost']} losses). They scored "
        f"{standing['goals_for']} goals and conceded {standing['goals_against']} "
        f"(goal difference {gd:+d})."
    )
    return Doc(
        doc_id=f"team:{team['id']}:{season}",
        entity_type="team",
        entity_id=team["id"],
        content=content,
        metadata={
            "entity_type": "team",
            "entity_id": team["id"],
            "league_id": league["id"],
            "league_name": league["name"],
            "season": season,
            "source": f"{team['name']} — {league['name']} {season}",
        },
        source=f"{team['name']} — {league['name']} {season}",
    )


def league_doc(league: dict, standings: list[dict], teams: dict[int, str]) -> Doc:
    """A league-season overview: leader, chasing pack, and the relegation end."""
    season = league["season"]
    ordered = sorted(standings, key=lambda s: s["position"])
    parts: list[str] = [
        (
            f"The {league['name']} ({league['country']}) {season} season features "
            f"{len(ordered)} teams."
        )
    ]
    if ordered:
        leader = ordered[0]
        parts.append(
            f"{teams.get(leader['team_id'], 'The leader')} lead with "
            f"{leader['points']} points ({leader['goals_for']} scored, "
            f"{leader['goals_against']} conceded)."
        )
        top = ", ".join(
            f"{_ordinal(s['position'])} {teams.get(s['team_id'], '?')} "
            f"({s['points']} pts)"
            for s in ordered[:5]
        )
        parts.append(f"Top of the table: {top}.")
        bottom = ", ".join(
            f"{_ordinal(s['position'])} {teams.get(s['team_id'], '?')} "
            f"({s['points']} pts)"
            for s in ordered[-3:]
        )
        parts.append(f"Bottom of the table: {bottom}.")

    return Doc(
        doc_id=f"league:{league['id']}:{season}",
        entity_type="league",
        entity_id=league["id"],
        content=" ".join(parts),
        metadata={
            "entity_type": "league",
            "entity_id": league["id"],
            "league_id": league["id"],
            "league_name": league["name"],
            "season": season,
            "source": f"{league['name']} {season} Season Overview",
        },
        source=f"{league['name']} {season} Season Overview",
    )


def match_doc(match: dict, home: str, away: str, league: dict) -> Doc:
    """A finished result in prose (won/lost/drew), with the scoreline and date."""
    hs, as_ = match["home_score"], match["away_score"]
    when = match["kickoff_datetime"].date().isoformat() if match["kickoff_datetime"] else "an unknown date"
    if hs > as_:
        outcome = f"{home} beat {away} {hs}-{as_} at home"
    elif as_ > hs:
        outcome = f"{home} lost {hs}-{as_} at home to {away}"
    else:
        outcome = f"{home} drew {hs}-{as_} at home with {away}"
    md = f" (matchday {match['matchday']})" if match.get("matchday") else ""
    content = (
        f"On {when}, {outcome} in the {league['name']} {league['season']}{md}."
    )
    return Doc(
        doc_id=f"match:{match['id']}",
        entity_type="match",
        entity_id=match["id"],
        content=content,
        metadata={
            "entity_type": "match",
            "entity_id": match["id"],
            "league_id": league["id"],
            "league_name": league["name"],
            "season": league["season"],
            "source": f"{home} {hs}-{as_} {away} ({when})",
        },
        source=f"{home} {hs}-{as_} {away} ({when})",
    )


def trend_doc(team: dict, rows: list[dict], leagues_by_id: dict[int, dict]) -> Doc:
    """Cross-season team trajectory grounded in every available standing row."""
    ordered = sorted(rows, key=lambda row: row["season"])
    first, last = ordered[0], ordered[-1]
    history = "; ".join(
        f"{row['season']}: {row['points']} points, {_ordinal(row['position'])} in "
        f"{leagues_by_id[row['league_id']]['name']}"
        for row in ordered
        if row["league_id"] in leagues_by_id
    )
    return Doc(
        doc_id=f"trend:team:{team['external_id']}",
        entity_type="team_trend",
        entity_id=team["id"],
        content=(
            f"Historical performance for {team['name']} from {first['season']} to "
            f"{last['season']}: {history}. Their points changed from "
            f"{first['points']} to {last['points']} over this period."
        ),
        metadata={"entity_type": "team_trend", "entity_id": team["id"], "season": last["season"],
                  "league_id": last["league_id"], "source": f"{team['name']} Historical Trend"},
        source=f"{team['name']} Historical Trend",
    )
