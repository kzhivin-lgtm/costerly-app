from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
import json
from time import perf_counter
from typing import Callable

import streamlit as st

from config import get_optional_secret
from observability.runtime import report_runtime_failure
from styles.objects import apply_objects_css
from ui.js_guards import (
    install_objects_price_input_guard,
    install_workflow_header_alignment_guard,
)
from ui import objects_pricing
from ui import objects_workflow
from ui.screen_transition import (
    OBJECTS_MARKER_ID,
)
from use_cases.estimation import load_objects_estimation_data, refresh_objects_estimation_prices
from use_cases.estimation_runtime import submit_prepared_estimation_job
from use_cases.estimation_parts_check_runtime import load_estimation_cycle_cost, load_parts_check
from use_cases.object_detail_runtime import submit_object_detail_prefetch
from use_cases.final_approval import final_approval
from ui.objects_workflow import pricing_signature
from use_cases.estimation_progress import EstimationCycle, clear_estimate_progress, get_estimate_progress
from use_cases.proposal_pdf import load_estimate_proposal_url
from db.supabase_client import get_supabase_client
from db.workflow_routes import ensure_object_workflow_route_tokens, workflow_route_key
from state.company_auth import company_auth_enabled
from state.session import invalidate_object_detail_cache


@dataclass(frozen=True)
class ObjectsScreenState:
    """Loaded Project data plus non-fatal render messages."""
    data: dict[str, object]
    data_error: str | None = None
    cache_warning: str | None = None


def _empty_objects_data() -> dict[str, object]:
    """Return an empty real-data shape when no estimate exists yet."""
    return {
        "rows": [],
        "project_costs": [],
        "summary": {"project_price": None, "vat": None, "total": None},
    }


def prepared_objects_data_from_seed_rows(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    """Build the complete first-paint Objects payload from reviewed rows.

    File Review calls this before it enables Continue.  Keeping this tiny
    builder here means the destination owns its rendering shape, while the
    source screen can hand off a complete, read-free payload rather than a
    partial collection of seed rows.
    """
    prepared_rows = [dict(row) for row in rows]
    return {
        "rows": prepared_rows,
        "project_costs": _project_cost_rows_for_seed(prepared_rows, allow_totals=False),
        "summary": {
            "project_price": None,
            "vat": None,
            "total": None,
            "project_pricing_ready": False,
        },
    }


def prepare_objects_navigation_state(
    *,
    company_id: str,
    run_id: str,
    estimate_id: str,
    seed_rows: list[dict[str, object]] | None = None,
) -> dict[str, object] | None:
    """Return the full Objects state required before File Review enables Continue.

    A new estimate has no durable rows yet, so its already-reviewed seed is
    the complete first-paint state.  Reopening a completed estimate resolves
    its cached or durable rows here, before the navigation click, including
    Object Detail route tokens.  The callback therefore only swaps prepared
    state and never starts an additional read.
    """
    if seed_rows is not None:
        return {
            "data": prepared_objects_data_from_seed_rows(seed_rows),
            "data_error": None,
            "cache_warning": None,
        }

    state = _current_objects_state(estimate_id)
    if state.data_error:
        return None
    return {
        "data": _data_with_object_routes(
            state.data,
            company_id=company_id,
            run_id=run_id,
            estimate_id=estimate_id,
        ),
        "data_error": None,
        "cache_warning": state.cache_warning,
    }


def _consume_prepared_objects_navigation_state(
    *,
    company_id: str,
    run_id: str | None,
    estimate_id: str | None,
) -> ObjectsScreenState | None:
    """Consume one File Review handoff only when it belongs to this screen.

    The payload exists for the first destination render only.  Subsequent
    fragment or ordinary reruns return to normal cache freshness rules, so a
    completed background calculation cannot remain visually frozen.
    """
    prepared = st.session_state.get("objects_navigation_ready")
    if not isinstance(prepared, dict):
        return None
    if (
        str(prepared.get("company_id") or "") != str(company_id)
        or str(prepared.get("run_id") or "") != str(run_id or "")
        or str(prepared.get("estimate_id") or "") != str(estimate_id or "")
    ):
        return None
    st.session_state.pop("objects_navigation_ready", None)
    data = prepared.get("data")
    if not isinstance(data, dict):
        return None
    return ObjectsScreenState(
        data=data,
        data_error=(
            str(prepared["data_error"])
            if prepared.get("data_error")
            else None
        ),
        cache_warning=(
            str(prepared["cache_warning"])
            if prepared.get("cache_warning")
            else None
        ),
    )


def _consume_estimation_future() -> None:
    """Store the background estimation result once the worker is done."""
    future = st.session_state.get("estimation_batch_future")
    if not isinstance(future, Future) or not future.done():
        return

    estimate_id = st.session_state.get("current_estimate_id")
    cycle_estimate_id = st.session_state.pop("objects_estimation_future_id", None)
    cycle = _estimation_cycle(cycle_estimate_id)
    try:
        result = future.result()
        st.session_state.last_estimation_result = result
        st.session_state.last_estimation_error = None
        if cycle and isinstance(result, dict) and result.get("estimate_id") == cycle_estimate_id:
            cycle.cost_usd = result.get("cost_usd")
            cycle.worker_failed = (result.get("estimation") or {}).get("status") == "completed_with_failures"
        if estimate_id:
            st.session_state.setdefault("estimation_terminal_failures", {}).pop(
                str(estimate_id), None,
            )
            st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
            invalidate_object_detail_cache(str(estimate_id))
    except Exception as exc:
        st.session_state.last_estimation_error = str(exc)
        if cycle:
            cycle.worker_failed = True
        if estimate_id:
            st.session_state.setdefault("estimation_terminal_failures", {})[
                str(estimate_id)
            ] = str(exc)
    finally:
        if cycle:
            cycle.worker_finished = True
        st.session_state.prepared_estimate_access = None
        clear_estimate_progress(st.session_state.get("current_estimate_id"))
        st.session_state.estimation_batch_future = None


def _start_prepared_estimation_launch() -> None:
    """Queue the accepted File Review plan without delaying Objects' first paint."""
    request = st.session_state.get("objects_estimation_launch_request")
    if not isinstance(request, dict):
        return

    estimate_id = str(request.get("estimate_id") or "")
    run_id = str(request.get("run_id") or "")
    company_id = str(request.get("company_id") or "")
    file_name = str(request.get("file_name") or "")
    file_bytes = request.get("file_bytes")
    if not estimate_id or not run_id or not company_id or not file_name or not isinstance(file_bytes, bytes):
        st.session_state.objects_estimation_launch_request = None
        st.session_state.prepared_estimate_access = None
        st.session_state.last_estimation_error = "The prepared Objects launch is incomplete. Please return to File Review."
        return

    cycle = EstimationCycle(started_at=request.get("cycle_started_at", perf_counter()))
    st.session_state.setdefault("objects_estimation_cycles", {})[estimate_id] = cycle
    try:
        st.session_state.estimation_batch_future = submit_prepared_estimation_job(
            estimate_id=estimate_id,
            run_id=run_id,
            company_id=company_id,
            file_name=file_name,
            file_bytes=file_bytes,
            object_edits=request.get("object_edits") or {},
            metadata_values=request.get("metadata_values") or {},
            edits_changed=bool(request.get("edits_changed")),
            ignored_object_ids=set(request.get("ignored_object_ids") or set()),
            create_shell=bool(request.get("create_shell")),
        )
        st.session_state.objects_estimation_future_id = estimate_id
        st.session_state.setdefault("estimation_terminal_failures", {}).pop(
            estimate_id, None,
        )
    except Exception as exc:
        cycle.worker_failed = cycle.worker_finished = True
        st.session_state.last_estimation_error = str(exc)
        st.session_state.prepared_estimate_access = None
    finally:
        # The Future owns an immutable copy of the input.  Retaining PDF bytes
        # in Session State after dispatch is unnecessary and risks a stale
        # request starting after a later navigation.
        st.session_state.objects_estimation_launch_request = None


def _objects_price_input_config() -> tuple[str | None, str | None, str | None]:
    return (
        get_optional_secret("SUPABASE_URL"),
        get_optional_secret("SUPABASE_ANON_KEY"),
        st.session_state.get("auth_access_token") if company_auth_enabled() else None,
    )


def _load_objects_screen_data(estimate_id: str) -> tuple[dict[str, object], str | None]:
    """Load Objects data from session cache first, then Supabase when needed."""
    cache = st.session_state.setdefault("objects_estimation_data_cache", {})
    dirty_estimates = st.session_state.setdefault("objects_estimation_cache_dirty", set())

    if estimate_id in cache and estimate_id not in dirty_estimates:
        pricing_dirty = st.session_state.setdefault("objects_estimation_pricing_dirty", set())
        if estimate_id in pricing_dirty:
            try:
                cache[estimate_id] = refresh_objects_estimation_prices(estimate_id, cache[estimate_id])
                pricing_dirty.discard(estimate_id)
                st.session_state.pop("approved_object_keys", None)
            except Exception as exc:
                return cache[estimate_id], f"Could not refresh saved prices. Your edits are retained. ({exc})"
        return cache[estimate_id], None

    try:
        data = load_objects_estimation_data(estimate_id)
    except Exception as exc:
        cached = cache.get(estimate_id)
        if cached is not None:
            return (
                cached,
                f"Could not refresh Project from Supabase. Showing last available data. ({exc})",
            )
        raise

    cache[estimate_id] = data
    dirty_estimates.discard(estimate_id)
    st.session_state.setdefault("objects_estimation_pricing_dirty", set()).discard(estimate_id)
    return data, None


def _data_with_progress(data: dict[str, object], estimate_id: str | None) -> dict[str, object]:
    """Show File Review objects immediately until the estimate shell reaches Supabase."""
    seed_rows = st.session_state.get("objects_estimation_seed_rows") or []
    rows_source = data.get("rows") or seed_rows
    if not rows_source:
        return data

    progress = get_estimate_progress(estimate_id)
    rows = [dict(row) for row in rows_source]
    if progress:
        active_object_id = str(progress.get("object_id") or "")
        for row in rows:
            if str(row.get("object_key") or "") == active_object_id:
                row["status"] = str(progress.get("status") or "running")
                row["progress_percent"] = progress.get("percent")
                row["progress_updated_at"] = progress.get("updated_at")
                break

    # A worker can fail after its first optimistic progress update. Preserve
    # that terminal state in this session even if the same infrastructure
    # incident also prevents the durable failure write.
    local_failures = st.session_state.get("estimation_terminal_failures", {})
    local_failure = (
        local_failures.get(str(estimate_id))
        if isinstance(local_failures, dict) and estimate_id
        else None
    )
    if local_failure:
        for row in rows:
            if objects_pricing.row_status(row) in {"running", "pending"}:
                row["status"] = "failed"
                row["progress_percent"] = 100
                row["progress_label"] = "estimation_handoff_failed"
                row["self_cost_unit"] = None

    for row in rows:
        status = objects_pricing.row_status(row)
        if status == "running":
            row["self_cost_unit"] = f"{objects_pricing.smooth_progress_percent(row)}%"

    estimation_running = isinstance(st.session_state.get("estimation_batch_future"), Future)
    all_objects_terminal = bool(rows) and all(
        objects_pricing.row_status(row) in {"completed", "review_required"}
        and row.get("sale_price_total") is not None
        for row in rows
    )
    summary = dict(data.get("summary") or {})
    if estimation_running or not all_objects_terminal:
        summary.update(
            {
                "project_price": None,
                "vat": None,
                "total": None,
                "project_pricing_ready": False,
            }
        )
        return {
            **data,
            "rows": rows,
            "project_costs": _project_cost_rows_for_seed(rows, allow_totals=False),
            "summary": summary,
        }

    summary["project_pricing_ready"] = True
    project_costs = data.get("project_costs") or _project_cost_rows_for_seed(rows)
    return {**data, "rows": rows, "project_costs": project_costs, "summary": summary}


def _project_cost_rows_for_seed(
    rows: list[dict[str, object]], *, allow_totals: bool = True
) -> list[dict[str, object]]:
    """Build project-level cost rows while estimate results are still loading."""
    if not rows:
        return []
    all_completed = allow_totals and all(
        objects_pricing.row_status(row) in {"completed", "review_required"}
        and row.get("sale_price_total") is not None
        for row in rows
    )
    subtotal = sum(objects_pricing.number(row.get("sale_price_total"), 0) for row in rows)
    delivery = round(subtotal * 0.03, 2) if all_completed else None
    installation = round(subtotal * 0.10, 2) if all_completed else None

    return [
        {
            "object_key": "delivery",
            "name": "Delivery",
            "materials": "project-level cost",
            "quantity": 1,
            "self_cost_unit": None,
            "sale_price_unit": delivery,
            "sale_price_total": None,
            "status": "completed" if all_completed else "pending",
            "percent": 3,
            "suggestion": "suggested: 3% of objects subtotal",
        },
        {
            "object_key": "installation",
            "name": "Installation",
            "materials": "project-level cost",
            "quantity": 1,
            "self_cost_unit": None,
            "sale_price_unit": installation,
            "sale_price_total": None,
            "status": "completed" if all_completed else "pending",
            "percent": 10,
            "suggestion": "suggested: 10% of objects subtotal",
        },
    ]


def _mark_objects_cache_dirty_when_estimation_runs(estimate_id: str | None) -> None:
    """Force a refresh while the background estimation worker can still change rows."""
    estimation_running = isinstance(st.session_state.get("estimation_batch_future"), Future)
    if estimation_running and estimate_id:
        st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)


def _current_objects_state(estimate_id: str | None) -> ObjectsScreenState:
    """Return Project data plus user-visible error/warning strings."""
    if not estimate_id:
        return ObjectsScreenState(data=_empty_objects_data())

    # The File Review callback already creates these rows before the background
    # worker begins. Render them immediately instead of blocking navigation on
    # several Supabase reads while the estimate is still actively changing.
    seed_rows = st.session_state.get("objects_estimation_seed_rows") or []
    future = st.session_state.get("estimation_batch_future")
    if seed_rows and isinstance(future, Future) and not future.done():
        return ObjectsScreenState(data=prepared_objects_data_from_seed_rows(seed_rows))

    try:
        data, cache_warning = _load_objects_screen_data(estimate_id)
        return ObjectsScreenState(data=data, cache_warning=cache_warning)
    except Exception as exc:
        report_runtime_failure("objects.load", exc, rfq_run_id=st.session_state.get("current_run_id"), estimate_id=estimate_id)
        return ObjectsScreenState(
            data=_empty_objects_data(),
            data_error=f"Could not load Project: {exc}",
        )


def _persisted_objects_state(estimate_id: str | None) -> ObjectsScreenState:
    """Load the latest persisted rows while the background worker is active."""
    if not estimate_id:
        return ObjectsScreenState(data=_empty_objects_data())
    future = st.session_state.get("estimation_batch_future")
    shell_ready = getattr(future, "estimate_shell_ready", None)
    if isinstance(future, Future) and not future.done() and shell_ready is not None and not shell_ready.is_set():
        # A new accepted launch paints seeds before its worker persists the
        # shell. Ownership reads are valid only after that write is accepted.
        return ObjectsScreenState(data=prepared_objects_data_from_seed_rows(
            st.session_state.get("objects_estimation_seed_rows") or []
        ))
    cache = st.session_state.setdefault("objects_estimation_data_cache", {})
    dirty = st.session_state.setdefault("objects_estimation_cache_dirty", set())
    if estimate_id in cache and estimate_id not in dirty and not isinstance(future, Future):
        st.session_state.setdefault("objects_estimation_pricing_dirty", set()).add(estimate_id)
        data, warning = _load_objects_screen_data(estimate_id)
        return ObjectsScreenState(data=data, cache_warning=warning)
    dirty.add(estimate_id)
    try:
        data, cache_warning = _load_objects_screen_data(estimate_id)
        return ObjectsScreenState(data=data, cache_warning=cache_warning)
    except Exception as exc:
        report_runtime_failure("objects.refresh", exc, rfq_run_id=st.session_state.get("current_run_id"), estimate_id=estimate_id)
        return ObjectsScreenState(
            data=_empty_objects_data(),
            data_error=f"Could not load Project: {exc}",
        )


def _render_objects_messages(
    *,
    estimate_id: str | None,
    data_error: str | None,
    cache_warning: str | None,
) -> None:
    """Render non-table Project messages."""
    if not estimate_id:
        st.warning("No active estimate. Return to File Review and start Project.")
    if data_error:
        st.error(data_error)
    if cache_warning:
        st.warning(cache_warning)
    if st.session_state.get("last_estimation_error"):
        st.error(f"Estimation failed: {st.session_state.last_estimation_error}")


def _rows_with_approved_overlay(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Apply local approved-state feedback before rendering pricing rows."""
    approved_object_keys = st.session_state.get("approved_object_keys", set())
    return [
        {
            **row,
            "reviewed": bool(row.get("reviewed")) or row.get("object_key") in approved_object_keys,
        }
        for row in rows
    ]


def _estimation_cycle(estimate_id: str | None) -> EstimationCycle | None:
    return st.session_state.get("objects_estimation_cycles", {}).get(estimate_id)


def _render_pricing_table(
    data: dict[str, object],
    *,
    estimate_id: str | None,
    run_id: str | None,
    company_id: str | None = None,
    header_slots: objects_workflow.ObjectsHeaderSlots | None = None,
) -> None:
    """Render the Project pricing table."""
    rows = _rows_with_approved_overlay(data["rows"])
    cycle = _estimation_cycle(estimate_id)
    elapsed = None
    if cycle:
        ready_ids = [
            str(row["object_key"]) for row in rows
            if row.get("object_key") and objects_pricing.review_action_ready(row)
        ]
        failed_count = sum(objects_pricing.row_status(row) == "failed" for row in rows)
        elapsed = cycle.observe(perf_counter(), ready_ids=ready_ids,
                                all_terminal=bool(rows) and len(ready_ids) + failed_count == len(rows))
    running = bool(cycle and cycle.total_seconds is None)
    cost_usd = cycle.cost_usd if cycle else None
    if cost_usd is None and not running and estimate_id and run_id and company_id and rows and all(
        objects_pricing.review_action_ready(row) for row in rows
    ):
        key = company_id, run_id, estimate_id
        costs = st.session_state.setdefault("objects_saved_cycle_costs", {})
        if key not in costs:
            try:
                costs[key] = load_estimation_cycle_cost(
                    client=get_supabase_client(), company_id=company_id, run_id=run_id, estimate_id=estimate_id,
                )
            except Exception:
                costs[key] = None
        cost_usd = costs[key]
    metrics_html = objects_pricing.cycle_metrics_html(
        rows, elapsed=elapsed, ready_seconds=cycle.ready_seconds if cycle else {},
        cost_usd=cost_usd, running=running,
    ) if estimate_id else ""
    if header_slots is not None:
        metadata = st.session_state.get('file_review_data_cache', {}).get(str(run_id), {}).get('run') or {}
        if st.session_state.get('file_review_run_metadata_run_id') == run_id:
            metadata = {**metadata, **(st.session_state.get('file_review_run_metadata') or {})}
        name = metadata.get('project_name', data.get('project_name'))
        objects_workflow.update_header(header_slots, metrics_html=metrics_html, data={**data, "rows": rows, 'project_name': name}, estimate_id=estimate_id)
    st.markdown(
        objects_pricing.pricing_table_html(
            rows=rows,
            project_costs=data["project_costs"],
            summary=data["summary"],
            estimate_id=estimate_id,
            run_id=run_id,
            cycle_html="" if header_slots is not None else metrics_html,
            production_time_working_days=data.get('production_time_working_days'),
            proposal_pdf_url=(
                st.session_state.get("proposal_pdf_urls_by_estimate", {}).get(str(estimate_id))
                if estimate_id
                else None
            ),
        ),
        unsafe_allow_html=True,
    )


def _data_with_object_routes(
    data: dict[str, object],
    *,
    company_id: str,
    run_id: str | None,
    estimate_id: str | None,
) -> dict[str, object]:
    """Attach durable Object Detail fallbacks without changing visible row data."""
    if not run_id or not estimate_id:
        return data
    cache = st.session_state.setdefault("workflow_route_tokens", {})
    client = get_supabase_client()
    object_ids = [
        str(row.get("object_key") or "")
        for row in data.get("rows") or []
        if str(row.get("object_key") or "")
        and str(row.get("status") or "") in {"completed", "review_required"}
    ]
    missing_ids = [
        object_id
        for object_id in object_ids
        if workflow_route_key(
            scope="object",
            run_id=str(run_id),
            estimate_id=str(estimate_id),
            object_id=object_id,
        ) not in cache
    ]
    if missing_ids:
        created = ensure_object_workflow_route_tokens(
            client,
            company_id=company_id,
            run_id=str(run_id),
            estimate_id=str(estimate_id),
            object_ids=missing_ids,
        )
        for object_id, token in created.items():
            cache[workflow_route_key(
                scope="object",
                run_id=str(run_id),
                estimate_id=str(estimate_id),
                object_id=object_id,
            )] = token
    rows = []
    for source in data.get("rows") or []:
        row = dict(source)
        object_id = str(row.get("object_key") or "")
        if object_id and str(row.get("status") or "") in {"completed", "review_required"}:
            route_key = workflow_route_key(
                scope="object",
                run_id=str(run_id),
                estimate_id=str(estimate_id),
                object_id=object_id,
            )
            row["route_token"] = cache.get(route_key)
        rows.append(row)
    return {**data, "rows": rows}


def _cache_routed_objects_data(
    *, estimate_id: str | None, data: dict[str, object], data_error: str | None,
) -> None:
    """Retain route-enriched terminal rows for a later File Review return."""
    if not estimate_id or data_error:
        return
    st.session_state.setdefault("objects_estimation_data_cache", {})[str(estimate_id)] = data
    st.session_state.setdefault("objects_estimation_cache_dirty", set()).discard(
        str(estimate_id)
    )


def _open_object_detail(object_id: str) -> None:
    st.session_state.object_detail_quantity_check = (str(st.session_state.get("current_estimate_id") or ""), str(object_id))
    st.session_state.current_object_id = str(object_id)
    st.session_state.screen = "object_detail"


def _back_to_file_review_with_ready_cache(company_id: str) -> None:
    """Return to the exact File Review snapshot already rendered this session."""
    run_id = str(st.session_state.get("current_run_id") or "")
    review_cache = st.session_state.get("file_review_data_cache", {})
    review_data = review_cache.get(run_id) if isinstance(review_cache, dict) else None
    if run_id and isinstance(review_data, dict):
        st.session_state.file_review_navigation_ready = {
            "company_id": company_id,
            "run_id": run_id,
            "data": review_data,
        }
    st.session_state.screen = "file_review"


def _render_object_detail_navigation_bridges(data: dict[str, object]) -> None:
    """Mount native navigation before the live table makes Review clickable."""
    with st.container(key="object_detail_navigation_bridges"):
        for row in data.get("rows") or []:
            object_id = str(row.get("object_key") or "")
            if not object_id:
                continue
            st.button(
                f"Open Object Detail {object_id}",
                key=objects_pricing.object_detail_navigation_key(object_id),
                on_click=_open_object_detail,
                args=(object_id,),
            )


def _prefetch_completed_object_details(
    *, estimate_id: str | None, company_id: str, data: dict[str, object],
) -> None:
    """Warm completed Object Detail snapshots without gating navigation."""
    if not estimate_id:
        return
    estimate_key = str(estimate_id)
    cache = st.session_state.setdefault("object_detail_data_cache", {})
    dirty_estimates = st.session_state.setdefault("object_detail_data_cache_dirty", set())
    futures = st.session_state.setdefault("object_detail_prefetch_futures", {})
    failed_prefetches = st.session_state.setdefault("object_detail_prefetch_failed", set())
    for row in data.get("rows") or []:
        object_id = str(row.get("object_key") or "")
        if not object_id or objects_pricing.row_status(row) not in {"completed", "review_required"}:
            continue
        cache_key = (estimate_key, object_id)
        if cache_key in cache and estimate_key not in dirty_estimates:
            continue

        prefetch = futures.get(cache_key)
        if prefetch is None:
            if cache_key not in failed_prefetches:
                futures[cache_key] = submit_object_detail_prefetch(
                    estimate_id=estimate_key,
                    object_id=object_id,
                    company_id=str(company_id),
                )
        elif prefetch.done():
            futures.pop(cache_key, None)
            try:
                cache[cache_key] = prefetch.result()
                dirty_estimates.discard(estimate_key)
            except Exception:
                failed_prefetches.add(cache_key)


def _complete_final_approval(*, company_id: str, run_id: str, estimate_id: str) -> None:
    """Freeze the estimate and keep its proposal available on Objects."""
    try:
        basis = st.session_state.get("objects_set_price_basis", {}).get(estimate_id)
        if not basis:
            raise ValueError("Select Set prices before generating the proposal")
        saved = _persisted_objects_state(estimate_id)
        if saved.data_error or saved.cache_warning or not objects_workflow.prices_are_set(estimate_id, saved.data):
            raise ValueError("Prices changed. Select Set prices again")
        result = final_approval(
            company_id=company_id,
            run_id=run_id,
            estimate_id=estimate_id,
        )
    except Exception as exc:
        st.session_state.final_approval_error = str(exc)
    else:
        st.session_state.final_approval_error = None
        st.session_state.setdefault("proposal_pdf_urls_by_estimate", {})[estimate_id] = result.get(
            "proposal_pdf_url"
        )


def _set_objects_prices(*, estimate_id: str) -> None:
    """Accept the saved pricing basis without altering any price or cost."""
    try:
        state = _persisted_objects_state(estimate_id)
        if state.data_error or state.cache_warning:
            raise ValueError("Could not reload the saved prices. Try again")
        if not _final_approval_ready(state.data):
            raise ValueError("Approve every object before setting prices")
        st.session_state.setdefault("objects_set_price_basis", {})[estimate_id] = pricing_signature(state.data)
        st.session_state["objects_price_confirmation_id"] = st.session_state.get("objects_price_confirmation_id", 0) + 1
        _cache_routed_objects_data(estimate_id=estimate_id, data=state.data, data_error=None)
        st.session_state["final_approval_error"] = None
    except Exception as exc:
        st.session_state.setdefault("objects_set_price_basis", {}).pop(estimate_id, None)
        st.session_state["final_approval_error"] = str(exc)


def _load_existing_proposal_url(*, company_id: str, estimate_id: str | None) -> None:
    if not estimate_id:
        return
    cache = st.session_state.setdefault("proposal_pdf_urls_by_estimate", {})
    estimate_key = str(estimate_id)
    if estimate_key in cache:
        return
    try:
        cache[estimate_key] = load_estimate_proposal_url(
            client=get_supabase_client(),
            company_id=company_id,
            estimate_id=estimate_key,
        )
    except Exception:
        cache[estimate_key] = None


def _final_approval_ready(data: dict[str, object]) -> bool:
    rows = _rows_with_approved_overlay(list(data.get("rows") or []))
    summary = dict(data.get("summary") or {})
    return bool(rows) and summary.get("total") is not None and all(
        row.get("reviewed")
        and row.get("sale_price_total") is not None
        and str(row.get("status") or "") in {"completed", "review_required"}
        for row in rows
    )


def _render_objects_actions(
    *,
    company_id: str,
    run_id: str | None,
    estimate_id: str | None,
    data: dict[str, object],
) -> None:
    """Render bottom navigation actions for Project."""
    proposal_ready = bool(
        st.session_state.get("proposal_pdf_urls_by_estimate", {}).get(str(estimate_id))
    )

    prices_set = objects_workflow.prices_are_set(estimate_id, data)
    ready = bool(run_id and estimate_id and _final_approval_ready(data))
    with st.container(key="objects_actions"):
        col_back, col_set, col_generate = st.columns(3, gap="small")
    col_back.button(
        "Back to File Review",
        type="secondary",
        use_container_width=True,
        on_click=_back_to_file_review_with_ready_cache,
        args=(company_id,),
    )

    col_set.button(
        "Set Prices", key="objects_set_prices", type="secondary",
        use_container_width=True, disabled=proposal_ready or not ready,
        on_click=_set_objects_prices, kwargs={"estimate_id": str(estimate_id or "")},
    )
    col_generate.button(
        "GENERATE PROPOSAL",
        key="final_approval_approved" if proposal_ready else f"objects_generate_proposal_{st.session_state.get('objects_price_confirmation_id', 0)}",
        type="primary",
        use_container_width=True,
        disabled=proposal_ready or not ready or not prices_set,
        on_click=_complete_final_approval,
        kwargs={
            "company_id": company_id,
            "run_id": str(run_id or ""),
            "estimate_id": str(estimate_id or ""),
        },
    )


def _install_objects_price_input_runtime(
    *,
    estimate_id: str | None,
    supabase_url: str | None,
    supabase_anon_key: str | None,
    supabase_access_token: str | None = None,
) -> None:
    """Install the React-safe client-side price editor for the current estimate."""
    if estimate_id:
        install_objects_price_input_guard(
            estimate_id=str(estimate_id),
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_access_token=supabase_access_token,
        )
    # Do not install the former live progress poller here. It replaced children
    # inside Streamlit's React-owned table with innerHTML, which can race React
    # reconciliation during workflow navigation (removeChild NotFoundError).
    # Each Objects entry renders the latest persisted progress snapshot instead.


def _render_objects_table_content(
    *,
    estimate_id: str | None,
    run_id: str | None,
    screen_state: ObjectsScreenState,
    company_id: str | None = None,
    header_slots: objects_workflow.ObjectsHeaderSlots | None = None,
) -> None:
    """Render the messages and pricing table that may change during Estimation."""
    _render_objects_messages(
        estimate_id=estimate_id,
        data_error=screen_state.data_error,
        cache_warning=screen_state.cache_warning,
    )
    data = _data_with_progress(screen_state.data, estimate_id)
    _render_pricing_table(data, estimate_id=estimate_id, run_id=run_id, company_id=company_id, header_slots=header_slots)


def _render_live_objects_content(
    *, estimate_id: str | None, run_id: str | None, company_id: str,
    initial_state: ObjectsScreenState, live: bool,
    header_slots: objects_workflow.ObjectsHeaderSlots | None = None,
) -> None:
    """Safely refresh persisted Estimation rows without mutating React-owned DOM."""
    future_before = st.session_state.get("estimation_batch_future")
    _consume_estimation_future()
    if isinstance(future_before, Future) and not isinstance(
        st.session_state.get("estimation_batch_future"), Future
    ):
        st.session_state.pop("objects_live_poll_estimate_id", None)
        # Stay inside the Objects fragment when the worker becomes terminal.
        # A full app rerun can replay a durable File Review route while the
        # browser is still reconciling the Objects transition. This fragment
        # can load and render the just-persisted terminal rows directly.

    # The first fragment render stays on the already prepared seed rows so the
    # Objects transition is not delayed by an extra Supabase read. Timed
    # fragment reruns then replace the seed with persisted per-object results.
    if not live:
        st.session_state.pop("objects_live_poll_estimate_id", None)
        screen_state = initial_state
    elif st.session_state.get("objects_live_poll_estimate_id") != estimate_id:
        st.session_state.objects_live_poll_estimate_id = estimate_id
        screen_state = _current_objects_state(estimate_id)
    else:
        screen_state = _persisted_objects_state(estimate_id)
    routed_data = _data_with_object_routes(
        screen_state.data,
        company_id=company_id,
        run_id=run_id,
        estimate_id=estimate_id,
    )
    if not isinstance(st.session_state.get("estimation_batch_future"), Future):
        _cache_routed_objects_data(
            estimate_id=estimate_id,
            data=routed_data,
            data_error=screen_state.data_error,
        )
    with st.container(key="objects_live_pricing"):
        _render_objects_table_content(
            estimate_id=estimate_id,
            run_id=run_id,
            company_id=company_id,
            header_slots=header_slots,
            screen_state=ObjectsScreenState(
                data=routed_data,
                data_error=screen_state.data_error,
                cache_warning=screen_state.cache_warning,
            ),
        )
    _prefetch_completed_object_details(
        estimate_id=estimate_id,
        company_id=company_id,
        data=_data_with_progress(routed_data, estimate_id),
    )


def _worktop_area_rows(report):
    labels = {"main_worktop": "Main surface", "contrasting_end": "Contrasting end"}
    rows = []
    for object_id, obj in report.get("objects", {}).items():
        for part in obj.get("parts", ()):
            outline = part.get("worktop_outline") or {}
            if not outline:
                continue
            for surface in outline.get("surfaces", ()):
                rows.append({"Object": object_id, "Surface": labels.get(surface["material_role"], "Surface"),
                             "Area (m²)": f"{surface['area_m2']:.1f}"})
            rows.append({"Object": object_id, "Surface": "Total",
                         "Area (m²)": f"{outline['outer']['area_m2']:.1f}"})
    return rows


def _render_parts_check(*, estimate_id: str, run_id: str, company_id: str) -> None:
    if not estimate_id or not run_id:
        return
    key = company_id, run_id, estimate_id
    if st.button("Parts Check", key=f"parts-check-{estimate_id}"):
        try:
            result = load_parts_check(client=get_supabase_client(), company_id=company_id,
                                      run_id=run_id, estimate_id=estimate_id)
            if result["status"] == "ready":
                report = json.loads(result["payload"])
                result["worktop_areas"] = _worktop_area_rows(report)
                result["sheet_groups"] = (report.get("sheet_layout") or {}).get("groups", [])
        except Exception:
            result = {"status": "read_failed"}
        st.session_state.parts_check_result = (key, result)
    active_key, result = st.session_state.get("parts_check_result", (None, {}))
    if active_key != key:
        return
    status = result["status"]
    if status == "ready":
        if areas := result.get("worktop_areas"):
            st.caption("Worktop material area")
            st.table(areas)
        if groups := result.get("sheet_groups"):
            st.caption("CNC sheet layout")
            st.table([{"Stock": group["material"],
                       "Format (mm)": " × ".join(f"{d:g}" for d in group["size_mm"]),
                       "Sheets": group["layout"]["stock_count"],
                       "Placed blanks": group["layout"]["blank_count"],
                       "Unplaced": sum(group["layout"]["unplaced"].values())} for group in groups])
        st.download_button(f"Download Parts Check ({result['part_rows']} rows)",
                           data=result["payload"], file_name="parts-check.json",
                           mime="application/json", on_click="ignore")
    elif status == "running":
        st.info("Parts Check is running. Select Parts Check again to refresh.")
    elif status == "failed":
        st.warning("Parts Check could not finish for this upload.")
    elif status == "read_failed":
        st.warning("Parts Check could not be loaded. Try again.")
    else:
        st.caption("Parts Check is not available for this upload yet.")


def render_objects_screen(
    company_id: str,
    *,
    render_header_controls: Callable[[], None] | None = None,
) -> None:
    """Render the object pricing review screen from persisted estimate data."""
    apply_objects_css()
    estimate_id = st.session_state.get("current_estimate_id")
    run_id = st.session_state.get("current_run_id")
    # Emit the target screen before even queueing the worker. Streamlit marks
    # prior elements stale while a rerun is in flight, so submitting work first
    # could leave File Review visibly beneath a new Objects heading.
    metadata = (st.session_state.get('file_review_data_cache', {}).get(str(run_id), {}).get('run') or {})
    if st.session_state.get('file_review_run_metadata_run_id') == run_id:
        metadata = {**metadata, **(st.session_state.get('file_review_run_metadata') or {})}
    header_slots = objects_workflow.render_objects_header(
        objects_workflow.project_title(metadata.get('project_name')), render_header_controls,
        show_metrics=st.session_state.get("_platform_access") is not None,
    )
    # The File Review callback already populated visible seed rows. Queue
    # persistence only after the native destination header exists, so a click
    # never waits for worker setup before Objects starts replacing File Review.
    _start_prepared_estimation_launch()
    _consume_estimation_future()
    _mark_objects_cache_dirty_when_estimation_runs(estimate_id)
    screen_state = _consume_prepared_objects_navigation_state(
        company_id=company_id,
        run_id=run_id,
        estimate_id=estimate_id,
    )
    if screen_state is None:
        screen_state = _current_objects_state(estimate_id)
        screen_state = ObjectsScreenState(
            data=_data_with_object_routes(
                screen_state.data,
                company_id=company_id,
                run_id=run_id,
                estimate_id=estimate_id,
            ),
            data_error=screen_state.data_error,
            cache_warning=screen_state.cache_warning,
        )
    if not isinstance(st.session_state.get("estimation_batch_future"), Future):
        _cache_routed_objects_data(
            estimate_id=estimate_id,
            data=screen_state.data,
            data_error=screen_state.data_error,
        )
    if _final_approval_ready(screen_state.data):
        _load_existing_proposal_url(company_id=company_id, estimate_id=estimate_id)
    live = bool(estimate_id and isinstance(st.session_state.get("estimation_batch_future"), Future))
    # The timed fragment can enable Review without a full app rerun. Its
    # native buttons must already exist for all objects in the prepared batch.
    action_data = _data_with_progress(screen_state.data, estimate_id)
    _render_object_detail_navigation_bridges(action_data)
    # One fragment and delta path for both running and saved estimates. A
    # full rerun must replace the same subtree, rather than moving a stale
    # pricing table between a fragment and the app root.
    st.fragment(_render_live_objects_content, run_every=1.5 if live else None)(
        estimate_id=estimate_id, run_id=run_id, company_id=company_id,
        initial_state=screen_state, live=live,
        header_slots=header_slots,
    )

    # Actions and JavaScript runtimes remain outside the timed fragment. They
    # are installed once per full render and cannot flicker or be replaced by a
    # progress-only refresh.
    _render_objects_actions(
        company_id=company_id,
        run_id=run_id,
        estimate_id=estimate_id,
        data=action_data,
    )
    if not live:
        _prefetch_completed_object_details(estimate_id=estimate_id, company_id=company_id, data=action_data)
    if st.session_state.get("final_approval_error"):
        st.error(st.session_state.final_approval_error)
    install_workflow_header_alignment_guard(
        ".objects-estimation-header h1.workflow-title"
    )
    supabase_url, supabase_anon_key, supabase_access_token = _objects_price_input_config()
    _install_objects_price_input_runtime(
        estimate_id=estimate_id,
        supabase_url=supabase_url,
        supabase_anon_key=supabase_anon_key,
        supabase_access_token=supabase_access_token,
    )
    if estimate_id:
        objects_workflow.install_actions_runtime(str(estimate_id))
