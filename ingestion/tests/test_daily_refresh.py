"""Regression tests for the multi-season refresh orchestration."""

from pipelines.daily_refresh import LoadResult, _report


def test_report_accepts_the_explicit_competition_season() -> None:
    """Reporting must not rely on a local variable from the caller's scope."""
    totals: dict[str, LoadResult] = {}

    _report("matches", "PL", 2024, LoadResult(inserted=2, updated=1), totals)

    assert totals["matches"].inserted == 2
    assert totals["matches"].updated == 1
