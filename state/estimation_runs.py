from __future__ import annotations


_ESTIMATE_BY_RUN_ID: dict[str, str] = {}


def remember_estimate_for_run(*, run_id: str, estimate_id: str) -> None:
    _ESTIMATE_BY_RUN_ID[run_id] = estimate_id


def get_estimate_for_run(run_id: str) -> str | None:
    return _ESTIMATE_BY_RUN_ID.get(run_id)


def clear_estimation_runs() -> None:
    _ESTIMATE_BY_RUN_ID.clear()
