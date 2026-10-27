"""Forecast File Review arrival without changing RFQ processing work."""

from __future__ import annotations

import json
from statistics import median
from typing import Any


def processing_page_bucket(page_count: int | None) -> str:
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        return "unknown"
    if page_count <= 2:
        return "1-2"
    if page_count <= 6:
        return "3-6"
    if page_count <= 12:
        return "7-12"
    if page_count <= 20:
        return "13-20"
    return "21+"


def fallback_file_review_seconds(page_count: int | None) -> float:
    """Conservative cold-start forecast, superseded by same-company history."""
    return {
        "1-2": 40.0,
        "3-6": 60.0,
        "7-12": 90.0,
        "13-20": 150.0,
        "21+": 240.0,
        "unknown": 90.0,
    }[processing_page_bucket(page_count)]


def minimum_history_observations(page_count: int | None) -> int:
    """Return the evidence threshold for a timing forecast.

    A 21+ page run is unusually expensive to repeat merely to collect a third
    timing sample.  Two close, same-company runs are enough to replace the
    deliberately pessimistic cold-start figure; smaller files retain three.
    """
    return 2 if processing_page_bucket(page_count) == "21+" else 3


def _raw_usage(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("raw_usage") if isinstance(row, dict) else None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            value = None
    return value if isinstance(value, dict) else {}


def _duration(row: dict[str, Any]) -> float | None:
    try:
        value = float(row.get("duration_seconds"))
    except (AttributeError, TypeError, ValueError):
        value = None
    if value is None or value <= 0:
        try:
            value = float(_raw_usage(row).get("duration_seconds"))
        except (TypeError, ValueError):
            return None
    return value if value > 0 else None


def estimate_file_review_seconds(
    history: list[dict[str, Any]], *, page_count: int | None,
) -> dict[str, Any]:
    """Estimate to first File Review from successful same-company cycles.

    A page bucket normally needs three observations before it supersedes the
    conservative cold-start forecast.  The 21+ bucket needs two because each
    observed run is materially costly. Median is intentionally used instead of
    a mean so a provider outage or retry-heavy run cannot dominate the bar.
    """
    bucket = processing_page_bucket(page_count)
    values: list[float] = []
    for row in history:
        if str(row.get("status") or "") != "succeeded":
            continue
        raw = _raw_usage(row)
        if processing_page_bucket(raw.get("page_count")) != bucket:
            continue
        duration = _duration(row)
        if duration is not None:
            values.append(duration)
    if len(values) >= minimum_history_observations(page_count):
        return {
            "seconds": round(float(median(values)), 1),
            "source": "same_company_page_bucket_median",
            "sample_size": len(values),
            "page_bucket": bucket,
        }
    return {
        "seconds": fallback_file_review_seconds(page_count),
        "source": "conservative_cold_start",
        "sample_size": len(values),
        "page_bucket": bucket,
    }


def progress_fraction(*, elapsed_seconds: float, expected_total_seconds: float) -> float:
    """Map elapsed time to a truthful, never-complete-before-result bar."""
    elapsed = max(0.0, float(elapsed_seconds))
    expected = max(1.0, float(expected_total_seconds))
    if elapsed < expected:
        return max(0.04, min(0.96, elapsed / expected))
    # When a provider outlives its historical median, retain visible movement
    # but reserve completion for the actual File Review handoff.
    overtime = (elapsed - expected) / expected
    return min(0.985, 0.96 + 0.025 * (1 - pow(2.718281828, -overtime)))
