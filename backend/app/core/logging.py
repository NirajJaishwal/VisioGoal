"""Application logging: a single configuration entrypoint plus request logging.

`configure_logging()` installs a consistent formatter on the root logger.
`RequestLoggingMiddleware` logs one line per HTTP request with its method, path,
status code, and duration — enough to trace behaviour without extra tooling.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"

logger = logging.getLogger("app.request")


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once (idempotent across reloads)."""
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit a structured log line for every request/response cycle."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
