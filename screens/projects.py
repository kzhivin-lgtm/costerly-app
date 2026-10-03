from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from state.session import set_screen
from styles.projects import apply_projects_css
from use_cases.projects import load_projects_workspace


def _select_partner(organization_id: str) -> None:
    st.session_state.projects_partner_id = organization_id
    st.session_state.projects_project_id = None


def _select_project(project_id: str) -> None:
    st.session_state.projects_project_id = project_id


def _show_partners() -> None:
    st.session_state.projects_partner_id = None
    st.session_state.projects_project_id = None


def _show_partner_projects() -> None:
    st.session_state.projects_project_id = None


def _open_version(run_id: str, estimate_id: str) -> None:
    st.session_state.current_run_id = run_id
    st.session_state.current_estimate_id = estimate_id
    st.session_state.current_estimate_run_id = run_id
    st.session_state.current_object_id = None
    set_screen("objects")


def _card(title: object, meta: str, value: str) -> str:
    return (
        '<div class="projects-card">'
        '<div>'
        f'<div class="projects-card-title">{escape(str(title or "Untitled"))}</div>'
        f'<div class="projects-card-meta">{escape(meta)}</div>'
        '</div>'
        f'<div class="projects-card-value">{escape(value)}</div>'
        '</div>'
    )


def _summary_total(summary: object) -> str:
    if not isinstance(summary, dict):
        return ""
    raw = summary.get("project_total") or summary.get("total")
    try:
        return f"₪{float(raw):,.0f}" if raw is not None else ""
    except (TypeError, ValueError):
        return ""


def _render_partners(data: dict[str, list[dict[str, Any]]]) -> None:
    partners = data["organizations"]
    projects = data["projects"]
    if not partners:
        st.markdown(
            '<div class="projects-empty">Projects will appear here after the first Final Approval</div>',
            unsafe_allow_html=True,
        )
        return

    for partner in partners:
        partner_id = str(partner["organization_id"])
        partner_projects = [
            project for project in projects
            if str(project.get("partner_organization_id")) == partner_id
        ]
        content, action = st.columns([8, 1.6], vertical_alignment="center")
        content.markdown(
            _card(
                partner.get("name"),
                "Partner and Client" if partner.get("is_client") else "Partner",
                f'{len(partner_projects)} project{"s" if len(partner_projects) != 1 else ""}',
            ),
            unsafe_allow_html=True,
        )
        action.button(
            "OPEN",
            key=f"projects_partner_{partner_id}",
            use_container_width=True,
            on_click=_select_partner,
            args=(partner_id,),
        )


def _render_projects(data: dict[str, list[dict[str, Any]]], partner_id: str) -> None:
    partners = {str(row["organization_id"]): row for row in data["organizations"]}
    clients = {str(row["organization_id"]): str(row.get("name") or "") for row in data["clients"]}
    partner = partners.get(partner_id)
    if partner is None:
        _show_partners()
        st.rerun()

    st.button("BACK TO PARTNERS", key="projects_back_partners", on_click=_show_partners)
    st.markdown(f'<h1 class="projects-title">{escape(str(partner.get("name") or "Projects"))}</h1>', unsafe_allow_html=True)
    projects = [
        row for row in data["projects"]
        if str(row.get("partner_organization_id")) == partner_id
    ]
    if not projects:
        st.markdown('<div class="projects-empty">No finalized projects yet</div>', unsafe_allow_html=True)
        return

    for project in projects:
        project_id = str(project["project_id"])
        versions = [row for row in data["versions"] if str(row.get("project_id")) == project_id]
        client_name = clients.get(str(project.get("client_organization_id")), "No client specified")
        content, action = st.columns([8, 1.6], vertical_alignment="center")
        content.markdown(
            _card(project.get("name"), f"Client: {client_name}", f'{len(versions)} version{"s" if len(versions) != 1 else ""}'),
            unsafe_allow_html=True,
        )
        action.button(
            "OPEN",
            key=f"projects_project_{project_id}",
            use_container_width=True,
            on_click=_select_project,
            args=(project_id,),
        )


def _render_versions(data: dict[str, list[dict[str, Any]]], partner_id: str, project_id: str) -> None:
    project = next((row for row in data["projects"] if str(row.get("project_id")) == project_id), None)
    if project is None or str(project.get("partner_organization_id")) != partner_id:
        _show_partner_projects()
        st.rerun()

    st.button("BACK TO PROJECTS", key="projects_back_projects", on_click=_show_partner_projects)
    st.markdown(f'<h1 class="projects-title">{escape(str(project.get("name") or "Versions"))}</h1>', unsafe_allow_html=True)
    versions = [row for row in data["versions"] if str(row.get("project_id")) == project_id]
    if not versions:
        st.markdown('<div class="projects-empty">No finalized versions yet</div>', unsafe_allow_html=True)
        return

    for version in versions:
        version_id = str(version["version_id"])
        approved_at = str(version.get("approved_at") or "")[:10] or "Date unavailable"
        content, action = st.columns([8, 1.6], vertical_alignment="center")
        content.markdown(
            _card(f'Version {version.get("version_number")}', approved_at, _summary_total(version.get("summary"))),
            unsafe_allow_html=True,
        )
        action.button(
            "OPEN",
            key=f"projects_version_{version_id}",
            use_container_width=True,
            on_click=_open_version,
            args=(str(version["run_id"]), str(version["estimate_id"])),
        )


def render_projects_screen(company_id: str) -> None:
    apply_projects_css()
    st.markdown('<div class="projects-screen-active"></div>', unsafe_allow_html=True)
    try:
        data = load_projects_workspace(company_id)
    except Exception:
        st.error("Projects are temporarily unavailable")
        return

    partner_id = str(st.session_state.get("projects_partner_id") or "")
    project_id = str(st.session_state.get("projects_project_id") or "")
    if partner_id and project_id:
        _render_versions(data, partner_id, project_id)
    elif partner_id:
        _render_projects(data, partner_id)
    else:
        st.markdown('<h1 class="projects-title">Projects</h1>', unsafe_allow_html=True)
        _render_partners(data)
