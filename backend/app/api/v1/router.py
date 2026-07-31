"""Aggregate all v1 endpoint routers into a single router.

Mounted by `app.main` under the `/api/v1` prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import leagues, matches, standings, teams

api_router = APIRouter()
api_router.include_router(leagues.router)
api_router.include_router(standings.router)
api_router.include_router(teams.router)
api_router.include_router(matches.router)
