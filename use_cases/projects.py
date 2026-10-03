from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from db.supabase_client import get_supabase_client


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
    return {
        "organizations": [row for row in organizations if row.get("is_partner")],
        "clients": [row for row in organizations if row.get("is_client")],
        "projects": list(projects),
        "versions": list(versions),
    }
