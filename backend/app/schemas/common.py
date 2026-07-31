"""Shared API schemas: pagination envelope, error envelope, health payload.

These are the cross-cutting response shapes reused by multiple endpoints. Kept
separate so no single resource module owns them.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Page[T](BaseModel):
    """A paginated slice of results plus the metadata needed to fetch more."""

    items: list[T] = Field(description="The results for this page.")
    total: int = Field(description="Total rows matching the filters (ignores paging).")
    limit: int = Field(description="Maximum rows requested for this page.")
    offset: int = Field(description="Number of rows skipped before this page.")


class ErrorDetail(BaseModel):
    """Machine-readable error code plus a human-readable message."""

    code: str = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Human-readable explanation of the error.")


class ErrorResponse(BaseModel):
    """The consistent error envelope returned for every non-2xx response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"error": {"code": "not_found", "message": "League 999 not found"}}
        }
    )

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Liveness/readiness payload for `GET /health`."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok", "database": "connected"}}
    )

    status: str = Field(description="Overall service status.")
    database: str = Field(description="Database connectivity status.")
