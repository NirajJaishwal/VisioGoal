"""Source adapter protocol.

The rest of the pipeline depends on this interface, never on a vendor's JSON
shape directly. A richer paid source can be dropped in later by implementing the
same protocol — the transform/load/pipeline layers stay untouched.

Each method returns the provider's raw JSON (a plain dict). Normalization into
our schema is the job of `transform/`, keeping fetch and transform isolated.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class SourceError(Exception):
    """Raised when a data source cannot satisfy a request (after retries)."""


@runtime_checkable
class FootballSource(Protocol):
    async def get_competition(self, code: str) -> dict[str, Any]:
        """Fetch competition/league metadata for a competition code."""
        ...

    async def get_teams(self, code: str) -> dict[str, Any]:
        """Fetch the teams competing in a competition."""
        ...

    async def get_standings(self, code: str) -> dict[str, Any]:
        """Fetch the current league table for a competition."""
        ...

    async def get_matches(self, code: str) -> dict[str, Any]:
        """Fetch the fixtures/results for a competition."""
        ...
