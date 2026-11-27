from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Callable
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import streamlit as st

from styles.projects import apply_projects_css
from ui.layout import render_screen_header
from use_cases.projects import load_projects_workspace
from use_cases.proposal_document import optional_metadata


def _money(value: object) -> str:
    try:
        return f"₪{float(value):,.0f}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return "—"


def _calculation_time(value: object, timezone: str | None = None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return escape(str(value))
    if timezone and parsed.tzinfo is not None:
        parsed=parsed.astimezone(ZoneInfo(timezone))
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
        f'<div class="projects-project-name">{escape(str(project.get("name") or "Project"))}</div>'
        f'<div>{escape(client_names.get(str(project.get("client_organization_id") or ""), "—"))}</div>'
        f'<div>{_calculation_time(version.get("approved_at") if version else None, version.get("timezone") if version else None)}</div>'
        f'<div class="projects-total">{_money(summary.get("total"))}</div>'
        f'<div>{_pdf_link(version.get("proposal_pdf_url") if version else None)}</div>'
        '</div>'
    )


def _objects_table(version):
    rows=[]
    for obj in version.get('objects') or []:
        name=escape(str(obj.get('name') or 'Object'))
        material=escape(str(obj.get('materials') or ''))
        quantity=escape(str(obj.get('quantity') if obj.get('quantity') is not None else '—'))
        rows.append('<tr><td dir="auto">'+name+('<small>'+material+'</small>' if material else '')+'</td>'
                    +'<td>'+quantity+'</td><td>'+_money(obj.get('sale_price_unit'))+'</td>'
                    +'<td>'+_money(obj.get('sale_price_total'))+'</td></tr>')
    if not rows:return ''
    return ('<table class="projects-objects"><thead><tr><th>Object</th><th>Qty</th><th>Unit price</th><th>Total</th></tr></thead>'
            +'<tbody>'+''.join(rows)+'</tbody></table>')


def _calculation_groups(versions):
    groups={}
    for version in versions:
        groups.setdefault(str(version.get('estimate_id') or version.get('version_id')),[]).append(version)
    result=[]
    for estimate_id,items in groups.items():
        items=sorted(items,key=lambda v:int(v.get('version_number') or 0),reverse=True)
        name=optional_metadata((items[0].get('project_metadata') or {}).get('project_name'))
        label='Calculation'+(' · '+str(name) if name else '')
        history=[]
        for version in items:
            summary=version.get('summary') or {}
            history.append('<details class="projects-version" data-version-number="'+str(int(version.get('version_number') or 0))+'">'
                +'<summary><strong>V'+str(int(version.get('version_number') or 0))+'</strong>'
                +'<span>'+_calculation_time(version.get('approved_at'),version.get('timezone'))+'</span>'
                +'<span class="projects-total">'+_money(summary.get('total'))+'</span>'
                +_pdf_link(version.get('proposal_pdf_url'))+'</summary>'+_objects_table(version)+'</details>')
        result.append('<details class="projects-calculation" data-estimate-id="'+escape(estimate_id,quote=True)+'">'
                      +'<summary>'+escape(label)+'</summary><div class="projects-version-list">'+''.join(history)+'</div></details>')
    return ''.join(result)


def _project_history(project,versions,files):
    project_id=str(project.get('project_id') or '')
    versions=[v for v in versions if str(v.get('project_id') or '')==project_id]
    files=[f for f in files if str(f.get('project_id') or '')==project_id]
    sections=[];file_ids={str(f.get('file_id')) for f in files}
    for source in files:
        file_id=str(source.get('file_id'))
        items=[v for v in versions if str(v.get('source_file_id') or '')==file_id]
        if not items:continue
        sections.append('<details class="projects-file" data-source-file-id="'+escape(file_id,quote=True)+'">'
            +'<summary>'+escape(str(source.get('file_name') or 'File'))+'</summary>'
            +'<div class="projects-calculations">'+_calculation_groups(items)+'</div></details>')
    legacy=[v for v in versions if str(v.get('source_file_id') or '') not in file_ids]
    # Historical records without a known original remain visible directly;
    # inventing an Unknown File/Partner group would create false metadata.
    sections.append(_calculation_groups(legacy))
    return '<div class="projects-history">'+''.join(sections)+'</div>'


def _projects_table(data: dict[str, list[dict[str, Any]]]) -> str:
    partners=data['organizations'];projects=data['projects'];versions=data['versions']
    client_names={str(row.get('organization_id')):str(row.get('name') or '') for row in data['clients']}
    latest=_latest_versions(versions)
    if not projects:
        return '<div class="projects-empty">Projects will appear here after the first proposal is generated</div>'
    def project_markup(project):
        row=_project_row(project,client_names=client_names,version=latest.get(str(project.get('project_id') or '')))
        return ('<details class="projects-project" data-project-id="'+escape(str(project.get('project_id') or ''),quote=True)+'">'
                +'<summary>'+row+'</summary>'+_project_history(project,versions,data.get('files') or [])+'</details>')
    head=('<div class="projects-project-head"><div>Project</div><div>Client</div><div>Calculation</div><div>Total</div><div>PDF</div></div>')
    sections=[];assigned=set()
    for partner in partners:
        partner_id=str(partner.get('organization_id') or '')
        owned=[p for p in projects if str(p.get('partner_organization_id') or '')==partner_id]
        assigned.update(str(p.get('project_id')) for p in owned)
        if not owned:continue
        sections.append('<details class="projects-partner"><summary><span class="projects-partner-name">'
            +escape(str(partner.get('name') or 'Partner'))+'</span><span class="projects-partner-count">'
            +str(len(owned))+' project'+('s' if len(owned)!=1 else '')+'</span></summary>'
            +'<div class="projects-projects-body">'+head+''.join(project_markup(p) for p in owned)+'</div></details>')
    unassigned=[p for p in projects if str(p.get('project_id')) not in assigned]
    if unassigned:sections.append('<div class="projects-projects-body">'+head+''.join(project_markup(p) for p in unassigned)+'</div>')
    return '<div class="projects-table-card">'+''.join(sections)+'</div>'


def render_projects_screen(
    company_id: str,
    *,
    render_header_controls: Callable[[], None] | None = None,
) -> None:
    apply_projects_css()
    st.markdown('<div class="projects-screen-active"></div>', unsafe_allow_html=True)
    render_screen_header(
        lambda: st.markdown('<h1 class="projects-title">Partners</h1>', unsafe_allow_html=True),
        render_header_controls,
    )
    try:
        data = load_projects_workspace(company_id)
    except Exception:
        st.error("Projects are temporarily unavailable")
        return
    st.markdown(_projects_table(data), unsafe_allow_html=True)
