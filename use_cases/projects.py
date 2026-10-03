from __future__ import annotations

from typing import Any

from db.supabase_client import get_supabase_client


def load_projects_workspace(company_id: str) -> dict[str, list[dict[str, Any]]]:
    """Load the company-scoped Partner, Project, and Version hierarchy."""
    client = get_supabase_client()
    organizations = (
        client.table("organizations")
        .select("organization_id,name,is_partner,is_client,updated_at")
        .eq("company_id", company_id)
        .eq("is_partner", True)
        .order("name")
        .execute()
        .data
        or []
    )
    projects = (
        client.table("projects")
        .select("project_id,partner_organization_id,client_organization_id,name,status,updated_at")
        .eq("company_id", company_id)
        .order("updated_at", desc=True)
        .execute()
        .data
        or []
    )
    versions = (
        client.table("project_versions")
        .select("version_id,project_id,version_number,run_id,estimate_id,status,approved_at,summary")
        .eq("company_id", company_id)
        .order("version_number", desc=True)
        .execute()
        .data
        or []
    )
    clients = (
        client.table("organizations")
        .select("organization_id,name")
        .eq("company_id", company_id)
        .eq("is_client", True)
        .execute()
        .data
        or []
    )
    return {
        "organizations": list(organizations),
        "clients": list(clients),
        "projects": list(projects),
        "versions": list(versions),
    }
