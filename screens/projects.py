from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any
from urllib.parse import urlsplit

import streamlit as st

from styles.projects import apply_projects_css
from use_cases.projects import load_projects_workspace


def _money(value: object) -> str:
    try:
        return f"₪{float(value):,.0f}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return "—"


def _calculation_time(value: object) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return escape(str(value))
    return parsed.strftime("%d %b %Y, %H:%M")


def _pdf_link(value: object) -> str:
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return '<span class="projects-pdf-empty">—</span>'
    return (
        f'<a class="projects-pdf-link" href="{escape(url, quote=True)}" '
        'target="_blank" rel="noopener noreferrer" download>PDF</a>'
    )


def _latest_versions(versions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for version in versions:
        project_id = str(version.get("project_id") or "")
        current = latest.get(project_id)
        if current is None or int(version.get("version_number") or 0) > int(
            current.get("version_number") or 0
        ):
            latest[project_id] = version
    return latest


def _project_row(
    project: dict[str, Any],
    *,
    client_names: dict[str, str],
    version: dict[str, Any] | None,
) -> str:
    summary = version.get("summary") if version else {}
    if not isinstance(summary, dict):
        summary = {}
    return (
        '<div class="projects-project-row">'
        f'<div class="projects-project-name">{escape(str(project.get("name") or "Untitled project"))}</div>'
        f'<div>{escape(client_names.get(str(project.get("client_organization_id") or ""), "—"))}</div>'
        f'<div>{_calculation_time(version.get("approved_at") if version else None)}</div>'
        f'<div class="projects-total">{_money(summary.get("total"))}</div>'
        f'<div>{_pdf_link(version.get("proposal_pdf_path") if version else None)}</div>'
        '</div>'
    )


def _projects_table(data: dict[str, list[dict[str, Any]]]) -> str:
    partners = data["organizations"]
    projects = data["projects"]
    client_names = {
        str(row.get("organization_id")): str(row.get("name") or "")
        for row in data["clients"]
    }
    latest_versions = _latest_versions(data["versions"])
    if not partners:
        return '<div class="projects-empty">Projects will appear here after the first Final Approval</div>'

    partner_sections: list[str] = []
    for partner in partners:
        partner_id = str(partner.get("organization_id") or "")
        partner_projects = [
            project
            for project in projects
            if str(project.get("partner_organization_id") or "") == partner_id
        ]
        rows = "".join(
            _project_row(
                project,
                client_names=client_names,
                version=latest_versions.get(str(project.get("project_id") or "")),
            )
            for project in partner_projects
        )
        if not rows:
            rows = '<div class="projects-partner-empty">No finalized projects yet</div>'
        partner_sections.append(
            '<details class="projects-partner">'
            '<summary>'
            f'<span class="projects-partner-name">{escape(str(partner.get("name") or "Untitled partner"))}</span>'
            f'<span class="projects-partner-count">{len(partner_projects)} project{"s" if len(partner_projects) != 1 else ""}</span>'
            '</summary>'
            '<div class="projects-projects-body">'
            '<div class="projects-project-head">'
            '<div>Project</div><div>Client</div><div>Calculation</div><div>Total</div><div>PDF</div>'
            '</div>'
            f'{rows}'
            '</div>'
            '</details>'
        )
    return f'<div class="projects-table-card">{"".join(partner_sections)}</div>'


def render_projects_screen(company_id: str) -> None:
    apply_projects_css()
    st.markdown('<div class="projects-screen-active"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="projects-title">Projects</h1>', unsafe_allow_html=True)
    try:
        data = load_projects_workspace(company_id)
    except Exception:
        st.error("Projects are temporarily unavailable")
        return
    st.markdown(_projects_table(data), unsafe_allow_html=True)
