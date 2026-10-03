from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from db.supabase_client import get_supabase_client
from use_cases.proposal_pdf import proposal_signed_url


def load_projects_workspace(company_id: str) -> dict[str, list[dict[str, Any]]]:
    """Load the company-scoped Partner, Project, and Version hierarchy."""
    client = get_supabase_client()
    def load_organizations():
        return (
            client.table("organizations")
            .select("organization_id,name,is_partner,is_client,updated_at")
            .eq("company_id", company_id)
            .order("name")
            .execute().data or []
        )

    def load_projects():
        return (
            client.table("projects")
            .select("project_id,partner_organization_id,client_organization_id,name,status,updated_at")
            .eq("company_id", company_id)
            .order("updated_at", desc=True)
            .execute().data or []
        )

    def load_versions():
        return (
            client.table("project_versions")
            .select("version_id,project_id,version_number,run_id,estimate_id,status,approved_at,summary,proposal_pdf_path")
            .eq("company_id", company_id)
            .order("version_number", desc=True)
            .execute().data or []
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        organizations_future = executor.submit(load_organizations)
        projects_future = executor.submit(load_projects)
        versions_future = executor.submit(load_versions)
        organizations = organizations_future.result()
        projects = projects_future.result()
        versions = versions_future.result()
    latest_version_ids: set[str] = set()
    latest_by_project: dict[str, dict[str, Any]] = {}
    for version in versions:
        project_id = str(version.get("project_id") or "")
        current = latest_by_project.get(project_id)
        if current is None or int(version.get("version_number") or 0) > int(
            current.get("version_number") or 0
        ):
            latest_by_project[project_id] = version
    latest_version_ids = {
        str(version.get("version_id") or "") for version in latest_by_project.values()
    }
    for version in versions:
        if str(version.get("version_id") or "") not in latest_version_ids:
            continue
        object_path = str(version.get("proposal_pdf_path") or "").strip()
        if not object_path:
            continue
        try:
            version["proposal_pdf_url"] = proposal_signed_url(client, object_path)
        except Exception:
            version["proposal_pdf_url"] = None
    return {
        "organizations": [row for row in organizations if row.get("is_partner")],
        "clients": [row for row in organizations if row.get("is_client")],
        "projects": list(projects),
        "versions": list(versions),
    }
