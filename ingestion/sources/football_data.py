"""Football-Data.org API client (async httpx).

Responsibilities kept deliberately narrow: authenticate, make requests, respect
rate limits, retry transient failures, and return raw JSON. It knows nothing
about our database schema — transformation happens in `transform/`.

Free-tier notes:
  - Auth via the `X-Auth-Token` header.
  - ~10 requests/minute; a 429 carries how long to wait. We also self-throttle
    with a minimum interval between requests to avoid tripping the limit.

Usage:
    async with FootballDataClient() as client:
        teams = await client.get_teams("PL")
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from common.config import Settings, settings as default_settings
from common.logging import get_logger
from sources.base import SourceError

log = get_logger(__name__)

# Status codes worth retrying: rate limiting + transient server errors.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _season(season: int | None) -> dict[str, Any] | None:
    """Build the optional `?season=YYYY` query param (omitted when None)."""
    return {"season": season} if season is not None else None


class FootballDataError(SourceError):
    """Raised for non-recoverable Football-Data.org responses."""


class FootballDataClient:
    """Async adapter for the Football-Data.org v4 REST API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or default_settings
        if not self._settings.has_api_key:
            raise FootballDataError(
                "FOOTBALL_DATA_API_KEY is not set. Provide it via the environment "
                "(never hardcode secrets)."
            )
        self._client: httpx.AsyncClient | None = None
        # Monotonic timestamp of the last request, for self-throttling.
        self._last_request_at: float = 0.0

    # --- lifecycle ---------------------------------------------------------
    async def __aenter__(self) -> "FootballDataClient":
        self._client = httpx.AsyncClient(
            base_url=self._settings.football_data_base_url,
            headers={"X-Auth-Token": self._settings.football_data_api_key},
            timeout=self._settings.request_timeout_seconds,
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # --- public endpoints --------------------------------------------------
    async def get_competition(self, code: str) -> dict[str, Any]:
        return await self._get(f"/competitions/{code}")

    async def get_teams(self, code: str, season: int | None = None) -> dict[str, Any]:
        return await self._get(f"/competitions/{code}/teams", params=_season(season))

    async def get_standings(
        self, code: str, season: int | None = None
    ) -> dict[str, Any]:
        return await self._get(
            f"/competitions/{code}/standings", params=_season(season)
        )

    async def get_matches(
        self, code: str, season: int | None = None
    ) -> dict[str, Any]:
        return await self._get(f"/competitions/{code}/matches", params=_season(season))

    async def probe(
        self, path: str, params: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any] | None, dict[str, str]]:
        """Make one un-retried request for the capability probe.

        The normal ingestion methods deliberately retry transient failures. A
        probe instead needs the provider's *actual* response status so it can
        distinguish an unavailable endpoint (404), a subscription restriction
        (401/403), and rate limiting (429).  Callers receive a parsed JSON body
        when possible plus the response headers relevant to rate-limit reports.
        """
        if self._client is None:
            raise FootballDataError(
                "Client not initialized — use 'async with FootballDataClient()'."
            )
        await self._throttle()
        self._last_request_at = time.monotonic()
        response = await self._client.get(path, params=params)
        try:
            payload: dict[str, Any] | None = response.json()
        except ValueError:
            payload = None
        headers = {
            key: value
            for key, value in response.headers.items()
            if "limit" in key.lower()
            or "rate" in key.lower()
            or key.lower() == "retry-after"
        }
        return response.status_code, payload, headers

    # --- internals ---------------------------------------------------------
    async def _throttle(self) -> None:
        """Sleep so consecutive requests respect the minimum interval."""
        min_interval = self._settings.min_request_interval_seconds
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET `path` with throttling, retries, and clean error handling."""
        if self._client is None:
            raise FootballDataError(
                "Client not initialized — use 'async with FootballDataClient()'."
            )

        last_exc: Exception | None = None
        for attempt in range(1, self._settings.max_retries + 1):
            await self._throttle()
            log.info(
                "api_request",
                extra={"endpoint": path, "params": params or {}, "attempt": attempt},
            )
            self._last_request_at = time.monotonic()
            try:
                response = await self._client.get(path, params=params)
            except httpx.TransportError as exc:
                # Network-level failure (DNS, connection reset, timeout) — retry.
                last_exc = exc
                await self._sleep_backoff(attempt, reason=f"transport:{exc!r}")
                continue

            if response.status_code == 200:
                return response.json()

            if response.status_code in _RETRYABLE_STATUS:
                wait = self._retry_after(response, attempt)
                log.warning(
                    "api_retryable_status",
                    extra={
                        "endpoint": path,
                        "status": response.status_code,
                        "attempt": attempt,
                        "wait_seconds": round(wait, 2),
                    },
                )
                await asyncio.sleep(wait)
                continue

            # Non-retryable (401/403/404/…): fail fast with a clean message.
            raise FootballDataError(
                f"GET {path} failed with {response.status_code}: "
                f"{response.text[:200]}"
            )

        raise FootballDataError(
            f"GET {path} exhausted {self._settings.max_retries} retries "
            f"(last error: {last_exc!r})"
        )

    def _retry_after(self, response: httpx.Response, attempt: int) -> float:
        """Prefer the server's Retry-After header; else exponential backoff."""
        header = response.headers.get("Retry-After")
        if header:
            try:
                return float(header)
            except ValueError:
                pass
        return self._backoff(attempt)

    def _backoff(self, attempt: int) -> float:
        return self._settings.backoff_base_seconds * (2 ** (attempt - 1))

    async def _sleep_backoff(self, attempt: int, reason: str) -> None:
        wait = self._backoff(attempt)
        log.warning(
            "api_transient_error",
            extra={"attempt": attempt, "wait_seconds": round(wait, 2), "reason": reason},
        )
        await asyncio.sleep(wait)
