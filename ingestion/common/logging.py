"""Structured (JSON-line) logging for the ingestion pipeline.

Every log record is emitted as a single JSON object so runs are machine-parseable
(and still readable in a terminal). Call `configure_logging()` once at process
start, then use `get_logger(__name__)` and pass structured fields via `extra`:

    log = get_logger(__name__)
    log.info("api_request", extra={"endpoint": "/competitions/PL", "status": 200})

Helper wrappers (`log_event`) make the common "event + fields" shape concise.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
from typing import Any

# Attributes present on every stdlib LogRecord — anything *not* in this set is
# treated as a caller-supplied structured field and included in the JSON output.
_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Render a LogRecord (plus any `extra` fields) as one JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _dt.datetime.fromtimestamp(
                record.created, tz=_dt.timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    root = logging.getLogger()
    root.setLevel(level)
    # Replace any existing handlers so repeated calls don't double-log.
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Log a structured event at INFO level: `event` name + arbitrary fields."""
    logger.info(event, extra=fields)
