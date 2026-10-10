from __future__ import annotations

from dataclasses import dataclass
import json
import streamlit as st

from config import get_optional_secret
from db.repositories import delete_rfq_object_detail_draft, fetch_rfq_object_detail_draft
from db.supabase_client import get_supabase_client
from styles.object_detail import apply_object_detail_css
from ui import object_detail_view
from ui.js_guards import (
    install_object_detail_input_guard,
)
from use_cases.estimation import (
    apply_object_detail_line_edit,
    apply_object_detail_snapshot,
    approve_object_estimate,
    load_object_detail_data,
)
from state.company_auth import company_auth_enabled


@dataclass(frozen=True)
class ObjectDetailContext:
    """Current Object Detail route/session identifiers."""
    estimate_id: str
    object_id: str
    run_id: str


def render_object_detail_screen(company_id: str) -> None:
    """Render one object estimate detail screen from persisted estimate data."""
    context = _current_object_detail_context()
    if context is None:
        apply_object_detail_css()
        _render_missing_object_detail_context()
        return

    apply_object_detail_css()
    _consume_pending_object_detail_changes()
    if _approve_after_pending_changes(context):
        st.rerun()

    data = _load_object_detail_or_render_error(context)
    if data is None:
        return

    _render_object_detail(data, context)
    _install_object_detail_runtime(context)

def _current_object_detail_context() -> ObjectDetailContext | None:
    estimate_id = st.session_state.get("current_estimate_id")
    object_id = st.session_state.get("current_object_id")
    if not estimate_id or not object_id:
        return None
    return ObjectDetailContext(
        estimate_id=str(estimate_id),
        object_id=str(object_id),
        run_id=str(st.session_state.get("current_run_id") or ""),
    )


def _render_missing_object_detail_context() -> None:
    st.error("No object estimate selected.")
    _back_to_objects_button()


def _back_to_objects_button() -> None:
    from state.session import set_screen

    st.button(
        "BACK TO OBJECTS",
        type="secondary",
        on_click=set_screen,
        args=("objects",),
    )


def _consume_pending_object_detail_changes() -> None:
    _consume_pending_object_detail_snapshot()
    _consume_pending_object_detail_edit()


def _approve_after_pending_changes(context: ObjectDetailContext) -> bool:
    if not st.session_state.pop("object_detail_approve_after_edit", False):
        return False
    _approve_current_object_and_return(
        estimate_id=context.estimate_id,
        object_id=context.object_id,
        recalculate=False,
    )
    return True


def _load_object_detail_or_render_error(context: ObjectDetailContext) -> dict[str, object] | None:
    try:
        return load_object_detail_data(
            estimate_id=context.estimate_id,
            object_id=context.object_id,
        )
    except Exception as exc:
        st.error(f"Could not load Object Detail: {exc}")
        _back_to_objects_button()
        return None


def _render_object_detail(data: dict[str, object], context: ObjectDetailContext) -> None:
    st.markdown(
        object_detail_view.hero_html(data),
        unsafe_allow_html=True,
    )
    st.markdown(
        object_detail_view.detail_html(
            data,
            run_id=context.run_id,
            estimate_id=context.estimate_id,
            object_id=context.object_id,
        ),
        unsafe_allow_html=True,
    )
    with st.container(key="object_detail_navigation_bridges"):
        st.button(
            "Back to Objects",
            key="object_detail_back_bridge",
            on_click=_return_to_objects,
        )
        st.button(
            "Approve Estimate",
            key="object_detail_approve_bridge",
            on_click=_approve_current_object_and_return,
            kwargs={
                "estimate_id": context.estimate_id,
                "object_id": context.object_id,
                "run_id": context.run_id,
            },
        )


def _return_to_objects() -> None:
    st.session_state.current_object_id = None
    st.session_state.screen = "objects"


def _install_object_detail_runtime(context: ObjectDetailContext) -> None:
    install_object_detail_input_guard(
        run_id=context.run_id,
        estimate_id=context.estimate_id,
        object_id=context.object_id,
        supabase_url=get_optional_secret("SUPABASE_URL"),
        supabase_anon_key=get_optional_secret("SUPABASE_ANON_KEY"),
        supabase_access_token=(
            st.session_state.get("auth_access_token") if company_auth_enabled() else None
        ),
    )


def _consume_pending_object_detail_edit() -> bool:
    pending = st.session_state.pop("object_detail_pending_edit", None)
    if not pending:
        return False
    estimate_id = str(pending.get("estimate_id") or "")
    object_id = str(pending.get("object_id") or "")
    apply_object_detail_line_edit(
        estimate_id=estimate_id,
        object_id=object_id,
        line_id=str(pending.get("line_id") or ""),
        field=str(pending.get("field") or ""),
        value=str(pending.get("value") or ""),
    )
    _mark_objects_estimation_dirty(estimate_id)
    return True


def _consume_pending_object_detail_snapshot() -> bool:
    pending = st.session_state.pop("object_detail_pending_snapshot", None)
    if not pending:
        return False
    estimate_id = str(pending.get("estimate_id") or "")
    object_id = str(pending.get("object_id") or "")
    try:
        edits = json.loads(str(pending.get("snapshot") or "[]"))
    except json.JSONDecodeError:
        edits = []
    apply_object_detail_snapshot(
        estimate_id=estimate_id,
        object_id=object_id,
        run_id=str(st.session_state.get("current_run_id") or ""),
        edits=edits if isinstance(edits, list) else [],
    )
    _mark_objects_estimation_dirty(estimate_id)
    return bool(edits)


def _approve_current_object_and_return(
    *,
    estimate_id: str,
    object_id: str,
    run_id: str | None = None,
    object_key: str | None = None,
    recalculate: bool = True,
) -> None:
    user_id = str(st.session_state.get("auth_user_id") or "")
    if user_id:
        client = get_supabase_client()
        edits = fetch_rfq_object_detail_draft(
            client,
            user_id=user_id,
            estimate_id=estimate_id,
            object_id=object_id,
        )
        if edits:
            apply_object_detail_snapshot(
                estimate_id=estimate_id,
                object_id=object_id,
                run_id=str(run_id or st.session_state.get("current_run_id") or ""),
                edits=edits,
                approve=True,
            )
            delete_rfq_object_detail_draft(
                client,
                user_id=user_id,
                estimate_id=estimate_id,
                object_id=object_id,
            )
            recalculate = False
            _mark_objects_estimation_dirty(estimate_id)
            approved_object_keys = st.session_state.setdefault("approved_object_keys", set())
            approved_object_keys.add(object_key or object_id)
            st.session_state.screen = "objects"
            return
    approve_object_estimate(
        estimate_id=estimate_id,
        object_id=object_id,
        recalculate=recalculate,
    )
    _mark_objects_estimation_dirty(estimate_id)
    approved_object_keys = st.session_state.setdefault("approved_object_keys", set())
    approved_object_keys.add(object_key or object_id)
    st.session_state.screen = "objects"


def _mark_objects_estimation_dirty(estimate_id: str) -> None:
    if not estimate_id:
        return
    st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
