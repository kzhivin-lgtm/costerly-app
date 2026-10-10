from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any
from threading import Lock


PLATFORM_ROLES = {"platform_admin", "platform_viewer"}
ACCOUNT_STAGES = {"test", "pilot", "paid"}
PERIOD_OPTIONS = {7, 30, 90, 0}
MANUFACTURING_CALCULATORS = {
    "cnc_router_in_house",
    "cnc_router_subcontractor",
    "sheet_laser_in_house",
    "sheet_laser_subcontractor",
}
_PRODUCT_SESSION_EXECUTOR = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="product-session"
)
_HEADER_PREFETCH_EXECUTOR = ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="header-prefetch"
)
_HEADER_PREFETCH_LOCK = Lock()
_HEADER_PREFETCHES: dict[tuple[str, str], Any] = {}


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
    params = {
        "p_requesting_user_id": requesting_user_id,
        "p_days": days,
    }
    try:
        response = client.rpc(
            "platform_admin_company_dashboard_v3",
            params,
        ).execute()
    except Exception as exc:
        message = str(exc)
        if "PGRST202" not in message and "Could not find the function" not in message:
            raise
        try:
            response = client.rpc("platform_admin_company_dashboard_v2", params).execute()
        except Exception as fallback_exc:
            fallback_message = str(fallback_exc)
            if "PGRST202" not in fallback_message and "Could not find the function" not in fallback_message:
                raise
            response = client.rpc("platform_admin_company_dashboard", params).execute()
    return [dict(row) for row in (response.data or [])]


def load_manufacturing_parameter_library(
    client: Any,
    *,
    requesting_user_id: str,
    calculator: str | None = None,
    include_history: bool = False,
) -> list[dict[str, Any]]:
    """Load the Staff-only CNC / Laser parameter library through its guarded RPC."""
    require_platform_access(client, requesting_user_id)
    if calculator is not None and calculator not in MANUFACTURING_CALCULATORS:
        raise ValueError("Unsupported manufacturing calculator.")
    response = client.rpc(
        "platform_admin_manufacturing_cost_parameters",
        {
            "p_requesting_user_id": requesting_user_id,
            "p_calculator": calculator,
            "p_include_history": bool(include_history),
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


def record_authenticated_session(
    client: Any,
    *,
    company_id: str,
    user_id: str,
    session_id: str,
) -> None:
    """Record one company activity row per authenticated runtime session."""
    fingerprint = sha256(
        f"{company_id}\0{session_id}".encode("utf-8")
    ).hexdigest()
    client.rpc(
        "record_product_usage_event",
        {
            "p_company_id": company_id,
            "p_user_id": user_id,
            "p_event_name": "authenticated_session_started",
            "p_entity_fingerprint": fingerprint,
            "p_metadata": {},
        },
    ).execute()


def record_authenticated_session_in_background(
    client: Any,
    *,
    company_id: str,
    user_id: str,
    session_id: str,
) -> None:
    """Record product activity without holding the first authenticated render."""
    _PRODUCT_SESSION_EXECUTOR.submit(
        record_authenticated_session,
        client,
        company_id=company_id,
        user_id=user_id,
        session_id=session_id,
    )


def prefetch_header_access_in_background(*, user_id: str, company_id: str) -> None:
    """Warm non-critical header data without holding first authenticated paint."""
    key = (str(user_id), str(company_id))
    with _HEADER_PREFETCH_LOCK:
        existing = _HEADER_PREFETCHES.get(key)
        if existing is not None and not existing.done():
            return
        from db.supabase_client import get_supabase_client
        from use_cases.latest_estimate import load_latest_estimate_route

        def load_header_data():
            client = get_supabase_client()
            with ThreadPoolExecutor(max_workers=2) as executor:
                platform_future = executor.submit(load_platform_access, client, key[0])
                latest_future = executor.submit(
                    load_latest_estimate_route, client, key[1]
                )
                return platform_future.result(), latest_future.result()

        _HEADER_PREFETCHES[key] = _HEADER_PREFETCH_EXECUTOR.submit(load_header_data)


def take_prefetched_header_access(
    *, user_id: str, company_id: str
) -> tuple[PlatformAccess | None, dict[str, str] | None] | None:
    """Return a completed header prefetch, never wait for it in a UI run."""
    key = (str(user_id), str(company_id))
    with _HEADER_PREFETCH_LOCK:
        future = _HEADER_PREFETCHES.get(key)
    if future is None or not future.done():
        return None
    try:
        result = future.result()
    except Exception:
        return None
    if not isinstance(result, tuple) or len(result) != 2:
        return None
    return result


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
    """Show tracked provider cost in dollars without mixing display units."""
    value = _decimal(value_usd)
    if value == 0 and unpriced_events:
        return "—"
    return f"{value:.2f}"


def company_operational_status(row: dict[str, Any]) -> tuple[str, str]:
    """Return a factual status without inferring customer sentiment."""
    failed = int(row.get("failed_agent_events") or 0)
    if failed:
        label = "failure" if failed == 1 else "failures"
        return (f"{failed} agent {label}", "attention")
    activity = sum(
        int(row.get(key) or 0)
        for key in (
            "files_uploaded",
            "detection_runs",
            "estimation_calls",
            "price_source_runs",
            "pdfs_generated",
        )
    )
    if not activity:
        return ("No activity", "neutral")
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
