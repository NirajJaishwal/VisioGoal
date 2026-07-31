"""FastAPI application factory.

Wires together configuration, logging, exception handling, and routers. The
layering is strict:

    Router (api/v1/endpoints)  ->  Service (services)  ->  ORM (models)  ->  DB

Routers never import ORM models; all query logic lives in the service layer.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.endpoints import health
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.db.session import engine

API_V1_PREFIX = "/api/v1"

DESCRIPTION = """
REST API for the Football Intelligence Platform.

Read-only access to leagues, teams, standings, and matches ingested from
Football-Data.org. All data is pre-computed by the ingestion pipeline; these
endpoints only ever read from PostgreSQL.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Service and database health checks."},
    {"name": "leagues", "description": "Competitions and their seasons."},
    {"name": "standings", "description": "League tables (basic team statistics)."},
    {"name": "teams", "description": "Clubs, filterable by league and season."},
    {"name": "matches", "description": "Fixtures and results, with rich filtering."},
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Dispose the database engine cleanly on shutdown (avoids warnings)."""
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="Football Intelligence Platform API",
        description=DESCRIPTION,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=OPENAPI_TAGS,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    # Health lives at the root; resource routers under /api/v1.
    app.include_router(health.router)
    app.include_router(api_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
