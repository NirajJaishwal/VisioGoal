"""Health endpoint — liveness plus a live database connectivity probe."""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.dependencies import DbSession
from app.schemas.common import HealthResponse

logger = logging.getLogger("app.health")

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    responses={
        200: {"description": "Service is up and the database is reachable."},
        503: {"description": "Database is unreachable."},
    },
)
async def health(session: DbSession) -> HealthResponse | JSONResponse:
    """Return service status and confirm database connectivity via `SELECT 1`."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("Health check DB probe failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "disconnected"},
        )
    return HealthResponse(status="ok", database="connected")
