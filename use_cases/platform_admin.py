from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any


PLATFORM_ROLES = {"platform_admin", "platform_viewer"}
ACCOUNT_STAGES = {"test", "pilot", "paid"}
PERIOD_OPTIONS = {7, 30, 90, 0}


@dataclass(frozen=True)
class PlatformAccess:
    user_id: str
    role: str


def load_platform_access(client: Any, user_id: str) -> PlatformAccess | None:
    """Return explicit cross-company access, independent of company role."""
    rows = (
        client.table("platform_staff")
        .select("user_id,role,active")
        .eq("user_id", user_id)
        .eq("active", True)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        return None
    role = str(rows[0].get("role") or "")
    if role not in PLATFORM_ROLES:
        return None
    return PlatformAccess(user_id=str(rows[0]["user_id"]), role=role)


def require_platform_access(client: Any, user_id: str) -> PlatformAccess:
    access = load_platform_access(client, user_id)
    if access is None:
        raise PermissionError("Platform Admin access is required.")
    return access


def load_company_dashboard(
    client: Any,
    *,
    requesting_user_id: str,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Load one server-guarded aggregate row per company."""
    if days not in PERIOD_OPTIONS:
        raise ValueError("Unsupported Admin dashboard period.")
    require_platform_access(client, requesting_user_id)
    response = client.rpc(
        "platform_admin_company_dashboard",
        {
            "p_requesting_user_id": requesting_user_id,
            "p_days": days,
        },
    ).execute()
    return [dict(row) for row in (response.data or [])]


def record_dashboard_view(client: Any, *, platform_user_id: str) -> None:
    """Audit cross-company dashboard access without recording customer content."""
    require_platform_access(client, platform_user_id)
    client.table("platform_admin_audit_events").insert(
        {
            "platform_user_id": platform_user_id,
            "company_id": None,
            "action": "company_dashboard_viewed",
            "metadata": {},
        }
    ).execute()


def record_daily_activity(
    client: Any,
    *,
    company_id: str,
    user_id: str,
) -> None:
    """Record one authenticated activity row per company user and UTC day."""
    client.rpc(
        "record_product_usage_event",
        {
            "p_company_id": company_id,
            "p_user_id": user_id,
            "p_event_name": "authenticated_daily_activity",
            "p_entity_fingerprint": None,
            "p_metadata": {},
        },
    ).execute()


def company_file_fingerprint(company_id: str, file_bytes: bytes) -> str:
    """Create a company-scoped opaque fingerprint without retaining the file."""
    digest = sha256()
    digest.update(company_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(file_bytes)
    return digest.hexdigest()


def record_rfq_upload(
    client: Any,
    *,
    company_id: str,
    user_id: str | None,
    file_bytes: bytes,
) -> bool:
    """Record an RFQ upload and return whether the same company uploaded it before."""
    response = client.rpc(
        "record_product_usage_event",
        {
            "p_company_id": company_id,
            "p_user_id": user_id,
            "p_event_name": "rfq_uploaded",
            "p_entity_fingerprint": company_file_fingerprint(company_id, file_bytes),
            "p_metadata": {},
        },
    ).execute()
    rows = response.data or []
    return bool(rows and rows[0].get("is_repeat"))


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def format_ai_cost(value_usd: Any, *, unpriced_events: int = 0) -> str:
    """Show cents below one dollar and preserve incomplete-cost evidence."""
    value = _decimal(value_usd)
    if value == 0 and unpriced_events:
        return "Cost unavailable"
    if value < 1:
        amount = f"{value * 100:.1f}¢"
    else:
        amount = f"${value:.2f}"
    return f"{amount} partial" if unpriced_events else amount


def company_operational_status(row: dict[str, Any]) -> tuple[str, str]:
    """Return a factual status without inferring customer sentiment."""
    failed = int(row.get("failed_agent_events") or 0)
    files = int(row.get("files_uploaded") or 0)
    if failed:
        return (f"{failed} failed", "attention")
    if not files:
        return ("No usage", "neutral")
    return ("OK", "ok")


def normalize_dashboard_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize RPC values into a stable presentation contract."""
    stage = str(row.get("account_stage") or "pilot").lower()
    if stage not in ACCOUNT_STAGES:
        stage = "pilot"
    normalized = dict(row)
    normalized["account_stage"] = stage
    for key in (
        "users_count",
        "active_days_7",
        "active_days_30",
        "files_uploaded",
        "files_reuploaded",
        "detection_runs",
        "detection_unpriced_events",
        "estimation_calls",
        "estimation_unpriced_events",
        "price_source_runs",
        "price_source_unpriced_events",
        "pdfs_generated",
        "total_unpriced_events",
        "failed_agent_events",
    ):
        normalized[key] = int(row.get(key) or 0)
    return normalized
