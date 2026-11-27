"""Objects V2 header and action feedback, independent of pricing-row rendering."""
from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1 as components

from ui.layout import post_upload_title_html
from ui.screen_transition import OBJECTS_MARKER_ID
from use_cases.proposal_basis import pricing_signature


@dataclass(frozen=True)
class ObjectsHeaderSlots:
    metrics: object
    stages: object
    title: object = None


def project_title(name) -> str:
    name = str(name or '').strip()
    return 'Project' if not name or name.lower() in {'unknown', 'none', 'null', '—', '-'} else f'Project {name}'


def project_header_html(title, **kwargs):
    markup = post_upload_title_html(title, **kwargs)
    if title.startswith('Project '):
        markup = markup.replace(html.escape(title), '<span class="project-title-label">Project</span> '
                                '<span class="project-title-name">' + html.escape(title[8:]) + '</span>', 1)
    return markup


def prices_are_set(estimate_id: str | None, data: dict) -> bool:
    return bool(estimate_id) and st.session_state.get("objects_set_price_basis", {}).get(str(estimate_id)) == pricing_signature(data)


def invalidate_proposal(estimate_id: str, *, session=None) -> None:
    """Revoke this draft's confirmation/download, preserving every issued file."""
    session = st.session_state if session is None else session
    key = str(estimate_id)
    for name in ('objects_set_price_basis', 'objects_confirmed_proposal_data', 'proposal_basis_by_estimate'):
        session.setdefault(name, {}).pop(key, None)
    session.setdefault('proposal_pdf_urls_by_estimate', {})[key] = None
    if (session.get('proposal_first_download') or {}).get('estimate_id') == key:
        session.pop('proposal_first_download', None)


def current_proposal_url(estimate_id: str | None, data: dict) -> str | None:
    key = str(estimate_id)
    signature = pricing_signature(data)
    issued = st.session_state.get('proposal_basis_by_estimate', {}).get(key)
    confirmed = st.session_state.get('objects_set_price_basis', {}).get(key)
    if (issued and issued != signature) or (confirmed and confirmed != signature):
        invalidate_proposal(key)
    return st.session_state.get('proposal_pdf_urls_by_estimate', {}).get(key)


def stages_html(data: dict, *, prices_set: bool, proposal_ready: bool, confirmation_id: int = 0) -> str:
    rows = list(data.get("rows") or [])
    reviewed = sum(bool(row.get("reviewed")) for row in rows)
    all_reviewed = bool(rows) and reviewed == len(rows)
    current = 4 if proposal_ready else 1 if not all_reviewed else 3 if prices_set else 2
    labels = ("Review Objects", "Set Prices", "Generate Proposal")
    details = (f"{reviewed} of {len(rows)} reviewed" if rows else "", "", "")
    steps = []
    for number, (label, detail) in enumerate(zip(labels, details), 1):
        state = "complete" if number < current else "current" if number == current else "future"
        marker = "✓" if number < current else str(number)
        aria = ' aria-current="step"' if number == current else ""
        steps.append(f'<li data-stage="{number}" data-state="{state}"{aria}>'
                     f'<div class="objects-stage-group"><span class="objects-stage-marker">{marker}</span>'
                     f'<div><strong>{label}</strong>'
                     + (f'<small>{html.escape(detail)}</small>' if detail else "")
                     + '</div></div></li>')
    return f'<ol class="objects-workflow-stages" data-confirmation-id="{int(confirmation_id)}" aria-label="Proposal preparation">' + "".join(steps) + '</ol>'


def render_objects_header(title: str, render_header_controls: Callable[[], None] | None, *, show_metrics: bool = True) -> ObjectsHeaderSlots:
    # The exact existing title markup and primary container remain unchanged.
    with st.container(key="costerly_screen_header"):
        with st.container(key="costerly_screen_header_primary"):
            title_slot = st.empty()
            title_slot.markdown(project_header_html(title, class_name="objects-estimation-header", marker_id=OBJECTS_MARKER_ID, align_mark_left=True), unsafe_allow_html=True)
        with st.container(key="objects_header_toolbar", horizontal=True, vertical_alignment="center", gap=24):
            if render_header_controls is not None:
                with st.container(key="objects_header_controls", width="content"):
                    render_header_controls()
            metrics = None
            if show_metrics:
                with st.container(key="objects_header_metrics", width="content"):
                    metrics = st.empty()
        with st.container(key="objects_header_stages"):
            stages = st.empty()
            stages.html(stages_html({}, prices_set=False, proposal_ready=False))
    return ObjectsHeaderSlots(metrics, stages, title_slot)


def update_header(slots: ObjectsHeaderSlots, *, metrics_html: str, data: dict, estimate_id: str | None) -> None:
    if slots.title is not None:
        slots.title.markdown(project_header_html(project_title(data.get('project_name')), class_name='objects-estimation-header', marker_id=OBJECTS_MARKER_ID, align_mark_left=True), unsafe_allow_html=True)
    proposal_ready = bool(current_proposal_url(estimate_id, data))
    if slots.metrics is not None:
        slots.metrics.html(
            '<div class="objects-technical-metrics">'
            + metrics_html +
            '<button type="button" class="objects-metrics-toggle" aria-expanded="true" '
            'aria-label="Collapse technical metrics"><span class="objects-metrics-chevron" aria-hidden="true"></span></button>'
            '</div>' if metrics_html else "", width="content",
        )
    slots.stages.html(stages_html(data, prices_set=prices_are_set(estimate_id, data), proposal_ready=proposal_ready,
                                 confirmation_id=st.session_state.get("objects_price_confirmation_id", 0)))


def install_actions_runtime(estimate_id: str) -> None:
    source = Path(__file__).with_name("objects_actions.js").read_text()
    source = source.replace("__ESTIMATE_ID__", json.dumps(estimate_id))
    components.html('<script>' + source + '</script>', height=0)



def download_generated_proposal(request: dict) -> None:
    """One download after the accepted generation, with no poll, timer or popup."""
    source = Path(__file__).with_name('proposal_download.js').read_text()
    source = source.replace('__DOWNLOAD_REQUEST__', json.dumps(request).replace('<', '\u003c'))
    with st.container(key='proposal_first_download_host'):
        components.html('<script>' + source + '</script>', height=0)
