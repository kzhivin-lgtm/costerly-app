from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
import json
from typing import Callable

import streamlit as st

from config import get_optional_secret
from styles.objects import apply_objects_css
from ui.js_guards import (
    install_objects_price_input_guard,
    install_workflow_header_alignment_guard,
)
from ui import objects_pricing
from ui.layout import render_post_upload_header
from ui.screen_transition import (
    OBJECTS_MARKER_ID,
)
from use_cases.estimation import load_objects_estimation_data
from use_cases.final_approval import final_approval
from use_cases.estimation_progress import clear_estimate_progress, get_estimate_progress
from use_cases.proposal_pdf import load_estimate_proposal_url
from db.supabase_client import get_supabase_client
from db.workflow_routes import ensure_object_workflow_route_tokens, workflow_route_key
from state.company_auth import company_auth_enabled


@dataclass(frozen=True)
class ObjectsScreenState:
    """Loaded Objects Estimation data plus non-fatal render messages."""
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


def _consume_estimation_future() -> None:
    """Store the background estimation result once the worker is done."""
    future = st.session_state.get("estimation_batch_future")
    if not isinstance(future, Future) or not future.done():
        return

    try:
        st.session_state.last_estimation_result = future.result()
        st.session_state.last_estimation_error = None
        estimate_id = st.session_state.get("current_estimate_id")
        if estimate_id:
            st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
    except Exception as exc:
        st.session_state.last_estimation_error = str(exc)
    finally:
        clear_estimate_progress(st.session_state.get("current_estimate_id"))
        st.session_state.estimation_batch_future = None


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
        return cache[estimate_id], None

    try:
        data = load_objects_estimation_data(estimate_id)
    except Exception as exc:
        cached = cache.get(estimate_id)
        if cached is not None:
            return (
                cached,
                f"Could not refresh Objects Estimation from Supabase. Showing last available data. ({exc})",
            )
        raise

    cache[estimate_id] = data
    dirty_estimates.discard(estimate_id)
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
    """Return Objects Estimation data plus user-visible error/warning strings."""
    if not estimate_id:
        return ObjectsScreenState(data=_empty_objects_data())

    # The File Review callback already creates these rows before the background
    # worker begins. Render them immediately instead of blocking navigation on
    # several Supabase reads while the estimate is still actively changing.
    seed_rows = st.session_state.get("objects_estimation_seed_rows") or []
    future = st.session_state.get("estimation_batch_future")
    if seed_rows and isinstance(future, Future) and not future.done():
        rows = [dict(row) for row in seed_rows]
        return ObjectsScreenState(
            data={
                "rows": rows,
                "project_costs": _project_cost_rows_for_seed(rows),
                "summary": {"project_price": None, "vat": None, "total": None},
            }
        )

    try:
        data, cache_warning = _load_objects_screen_data(estimate_id)
        return ObjectsScreenState(data=data, cache_warning=cache_warning)
    except Exception as exc:
        return ObjectsScreenState(
            data=_empty_objects_data(),
            data_error=f"Could not load Objects Estimation: {exc}",
        )


def _persisted_objects_state(estimate_id: str | None) -> ObjectsScreenState:
    """Load the latest persisted rows while the background worker is active."""
    if not estimate_id:
        return ObjectsScreenState(data=_empty_objects_data())
    st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
    try:
        data, cache_warning = _load_objects_screen_data(estimate_id)
        return ObjectsScreenState(data=data, cache_warning=cache_warning)
    except Exception as exc:
        return ObjectsScreenState(
            data=_empty_objects_data(),
            data_error=f"Could not load Objects Estimation: {exc}",
        )


def _render_objects_messages(
    *,
    estimate_id: str | None,
    data_error: str | None,
    cache_warning: str | None,
) -> None:
    """Render non-table Objects Estimation messages."""
    if not estimate_id:
        st.warning("No active estimate. Return to File Review and start Objects Estimation.")
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


def _render_pricing_table(
    data: dict[str, object],
    *,
    estimate_id: str | None,
    run_id: str | None,
) -> None:
    """Render the Objects Estimation pricing table."""
    st.markdown(
        objects_pricing.pricing_table_html(
            rows=_rows_with_approved_overlay(data["rows"]),
            project_costs=data["project_costs"],
            summary=data["summary"],
            estimate_id=estimate_id,
            run_id=run_id,
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


def _open_object_detail(object_id: str) -> None:
    st.session_state.current_object_id = str(object_id)
    st.session_state.screen = "object_detail"


def _render_object_detail_navigation_bridges(data: dict[str, object]) -> None:
    """Keep HTML table actions on the current Streamlit session."""
    with st.container(key="object_detail_navigation_bridges"):
        for row in data.get("rows") or []:
            object_id = str(row.get("object_key") or "")
            if not object_id or str(row.get("status") or "") not in {
                "completed",
                "review_required",
            }:
                continue
            st.button(
                f"Open Object Detail {object_id}",
                key=objects_pricing.object_detail_navigation_key(object_id),
                on_click=_open_object_detail,
                args=(object_id,),
            )


def _complete_final_approval(*, company_id: str, run_id: str, estimate_id: str) -> None:
    """Freeze the estimate and keep its proposal available on Objects."""
    try:
        result = final_approval(
            company_id=company_id,
            run_id=run_id,
            estimate_id=estimate_id,
        )
    except Exception as exc:
        st.session_state.final_approval_error = str(exc)
        return
    st.session_state.final_approval_error = None
    st.session_state.setdefault("proposal_pdf_urls_by_estimate", {})[estimate_id] = result.get(
        "proposal_pdf_url"
    )


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
    """Render bottom navigation actions for Objects Estimation."""
    from state.session import set_screen

    col_back, col_generate = st.columns(2, gap="small")
    proposal_ready = bool(
        st.session_state.get("proposal_pdf_urls_by_estimate", {}).get(str(estimate_id))
    )

    col_back.button(
        "BACK TO FILE REVIEW",
        type="secondary",
        use_container_width=True,
        on_click=set_screen,
        args=("file_review",),
    )

    col_generate.button(
        "APPROVED" if proposal_ready else "FINAL APPROVAL",
        key="final_approval_approved" if proposal_ready else "final_approval",
        type="primary",
        use_container_width=True,
        disabled=proposal_ready or not (run_id and estimate_id and _final_approval_ready(data)),
        help=(
            None
            if proposal_ready or (run_id and estimate_id and _final_approval_ready(data))
            else "Review and approve every object before Final Approval"
        ),
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
) -> None:
    """Render the messages and pricing table that may change during Estimation."""
    _render_objects_messages(
        estimate_id=estimate_id,
        data_error=screen_state.data_error,
        cache_warning=screen_state.cache_warning,
    )
    data = _data_with_progress(screen_state.data, estimate_id)
    _render_pricing_table(data, estimate_id=estimate_id, run_id=run_id)


@st.fragment(run_every=1.5)
def _render_live_objects_content(*, estimate_id: str, run_id: str | None) -> None:
    """Safely refresh persisted Estimation rows without mutating React-owned DOM."""
    future_before = st.session_state.get("estimation_batch_future")
    _consume_estimation_future()
    if isinstance(future_before, Future) and not isinstance(
        st.session_state.get("estimation_batch_future"), Future
    ):
        st.session_state.pop("objects_live_poll_estimate_id", None)
        st.rerun()

    # The first fragment render stays on the already prepared seed rows so the
    # Objects transition is not delayed by an extra Supabase read. Timed
    # fragment reruns then replace the seed with persisted per-object results.
    if st.session_state.get("objects_live_poll_estimate_id") != estimate_id:
        st.session_state.objects_live_poll_estimate_id = estimate_id
        screen_state = _current_objects_state(estimate_id)
    else:
        screen_state = _persisted_objects_state(estimate_id)
    with st.container(key="objects_live_pricing"):
        _render_objects_table_content(
            estimate_id=estimate_id,
            run_id=run_id,
            screen_state=screen_state,
        )


def render_objects_screen(
    company_id: str,
    *,
    render_header_controls: Callable[[], None] | None = None,
) -> None:
    """Render the object pricing review screen from persisted estimate data."""
    apply_objects_css()
    _consume_estimation_future()

    estimate_id = st.session_state.get("current_estimate_id")
    run_id = st.session_state.get("current_run_id")
    _mark_objects_cache_dirty_when_estimation_runs(estimate_id)

    render_post_upload_header(
        "Objects Estimation",
        "Review objects → Set sale price → Final Approval",
        class_name="objects-estimation-header",
        marker_id=OBJECTS_MARKER_ID,
        render_header_controls=render_header_controls,
    )
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
    if _final_approval_ready(screen_state.data):
        _load_existing_proposal_url(company_id=company_id, estimate_id=estimate_id)
    if estimate_id and isinstance(st.session_state.get("estimation_batch_future"), Future):
        _render_live_objects_content(estimate_id=str(estimate_id), run_id=run_id)
    else:
        st.session_state.pop("objects_live_poll_estimate_id", None)
        _render_objects_table_content(
            estimate_id=estimate_id,
            run_id=run_id,
            screen_state=screen_state,
        )

    # Actions and JavaScript runtimes remain outside the timed fragment. They
    # are installed once per full render and cannot flicker or be replaced by a
    # progress-only refresh.
    action_data = _data_with_progress(screen_state.data, estimate_id)
    _render_object_detail_navigation_bridges(action_data)
    _render_objects_actions(
        company_id=company_id,
        run_id=run_id,
        estimate_id=estimate_id,
        data=action_data,
    )
    if st.session_state.get("final_approval_error"):
        st.error(f"Final Approval failed: {st.session_state.final_approval_error}")
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
