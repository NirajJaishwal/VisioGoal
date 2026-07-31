"""Application exceptions and centralized handlers.

Services raise the small `AppError` hierarchy below; routers stay free of
try/except and status-code logic. Every handler returns the same envelope:

    {"error": {"code": "<machine_code>", "message": "<human message>"}}

so clients can rely on one error shape across 400/404/422/500 responses.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.error")


class AppError(Exception):
    """Base class for expected, HTTP-mappable application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """A requested resource does not exist -> 404."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class BadRequestError(AppError):
    """The request was syntactically valid but semantically wrong -> 400."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"


def _envelope(code: str, message: str, status_code: int) -> JSONResponse:
    """Build the standard error envelope response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all error handlers to the application."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Summarize the first problem; full detail stays in the log.
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        message = first.get("msg", "Validation error")
        if loc:
            message = f"{loc}: {message}"
        return _envelope(
            "validation_error", message, status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Wrap framework HTTP errors (e.g. unmatched routes -> 404) in the envelope.
        code = "http_error" if exc.status_code >= 500 else "not_found"
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "bad_request"
        return _envelope(code, str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return _envelope(
            "internal_error",
            "An unexpected error occurred.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
