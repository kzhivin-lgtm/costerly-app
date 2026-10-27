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
        "21+": 360.0,
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


def _cycle_page_count(row: dict[str, Any]) -> int | None:
    """Read the real page count from current or pre-V6.51 cycle telemetry."""
    raw = _raw_usage(row)
    direct = raw.get("page_count")
    if isinstance(direct, int) and not isinstance(direct, bool) and direct > 0:
        return direct
    # V6.47-V6.50 wrote page_count=0 for normal OCR PDFs, but their exact
    # post-Fusion plan already contains the real OCR page count. Reuse those
    # completed cycles instead of discarding valuable observed timing.
    plan = raw.get("stage_aware_progress_plan_input")
    planned = plan.get("page_count") if isinstance(plan, dict) else None
    return (
        planned
        if isinstance(planned, int) and not isinstance(planned, bool) and planned > 0
        else None
    )


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
        if processing_page_bucket(_cycle_page_count(row)) != bucket:
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


def build_stage_progress_plan(
    *,
    page_count: int | None,
    elapsed_seconds: float,
    plan_input: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one file-specific, immutable progress plan after Fusion.

    The numbers are a forecast for movement *inside* a stage.  The server's
    stage callbacks remain the authority that closes one stage and opens the
    next.  This deliberately keeps a slow provider request inside its own
    range instead of allowing elapsed wall time to push the whole bar to 90%.
    """
    raw_batches = plan_input.get("discovery_batches_estimated_tokens")
    if not isinstance(raw_batches, list):
        raw_batches = []
    batch_tokens = [
        max(1, int(value))
        for value in raw_batches
        if isinstance(value, (int, float))
    ]
    if not batch_tokens:
        batch_tokens = [max(10_000, int(plan_input.get("full_estimated_input_tokens") or 10_000))]

    model = str(plan_input.get("registry_model") or "").lower()
    model_multiplier = 1.35 if "sonnet" in model else 1.0
    candidate_regions = max(0, int(plan_input.get("candidate_region_count") or 0))
    review_images = max(
        int(plan_input.get("review_image_estimate") or 0),
        int(plan_input.get("page_count") or page_count or 0),
    )

    # These are deliberately transparent work-unit estimates.  Historical
    # cycles can raise the total forecast, while exact batch/token shape still
    # determines how that remaining time is distributed across this file.
    discovery_seconds = [
        round(model_multiplier * max(12.0, 7.0 + tokens / 2_000.0), 1)
        for tokens in batch_tokens
    ]
    review_seconds = round(
        model_multiplier * max(10.0, 6.0 + review_images * 0.55), 1,
    )
    registry_seconds = round(max(4.0, 3.0 + candidate_regions * 0.08), 1)
    saving_seconds = 3.0
    observed_seconds = max(1.0, float(elapsed_seconds))
    unscaled_remaining = sum(discovery_seconds) + review_seconds + registry_seconds + saving_seconds
    historical_forecast = estimate_file_review_seconds(
        history or [], page_count=page_count,
    )
    historical_seconds = float(historical_forecast["seconds"])
    raw_shape_seconds = observed_seconds + unscaled_remaining
    # Exact batch shape distributes the remaining work. Once we have enough
    # same-page-bucket observations, their median is the estimate of the total
    # lap. The earlier `max()` made an intentionally rough token estimate
    # override real production history and could only make F worse.
    forecast_seconds = (
        max(observed_seconds + 10.0, historical_seconds)
        if historical_forecast["source"] == "same_company_page_bucket_median"
        else raw_shape_seconds
    )
    remaining_target = max(1.0, forecast_seconds - observed_seconds)
    scale = remaining_target / unscaled_remaining

    stages: list[dict[str, Any]] = [{
        "id": "pre_fusion",
        "label": "OCR and Fusion",
        "expected_seconds": round(observed_seconds, 1),
    }]
    for number, seconds in enumerate(discovery_seconds, start=1):
        stages.append({
            "id": f"discovery_{number}",
            "label": f"Discovery batch {number} of {len(discovery_seconds)}",
            "expected_seconds": round(seconds * scale, 1),
            "estimated_input_tokens": batch_tokens[number - 1],
        })
    stages.extend([
        {
            "id": "membership_review",
            "label": "Membership review",
            "expected_seconds": round(review_seconds * scale, 1),
        },
        {
            "id": "registry_assembly",
            "label": "Registry assembly",
            "expected_seconds": round(registry_seconds * scale, 1),
        },
        {
            "id": "saving",
            "label": "Saving results",
            "expected_seconds": round(saving_seconds * scale, 1),
        },
    ])
    return {
        "version": "stage_aware_progress_v1",
        "forecast_seconds": int(round(forecast_seconds)),
        "page_count": page_count,
        "plan_input": dict(plan_input),
        "stages": stages,
    }


def stage_progress_floor(plan: dict[str, Any] | None, stage_id: str | None) -> float:
    """Return the completed-stage floor without inventing current-stage work."""
    if not isinstance(plan, dict) or not stage_id:
        return 0.0
    stages = plan.get("stages")
    if not isinstance(stages, list):
        return 0.0
    total = sum(max(0.0, float(row.get("expected_seconds") or 0)) for row in stages)
    if total <= 0:
        return 0.0
    completed = 0.0
    for row in stages:
        if str(row.get("id") or "") == stage_id:
            break
        completed += max(0.0, float(row.get("expected_seconds") or 0))
    return max(0.0, min(0.985, completed / total))
