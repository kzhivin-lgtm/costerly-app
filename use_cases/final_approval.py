from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import math
from typing import Any

from db.company_access import assert_estimate_owned, assert_run_owned
from db.supabase_client import get_supabase_client
from use_cases.estimation import load_objects_estimation_data
from use_cases.proposal_pdf import load_estimate_proposal_url, publish_proposal_pdf


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def final_approval(
    *,
    company_id: str,
    run_id: str,
    estimate_id: str,
) -> dict[str, Any]:
    """Freeze one fully reviewed estimate into its durable Project version."""
    data = load_objects_estimation_data(estimate_id)
    rows = [dict(row) for row in data.get("rows") or []]
    summary = dict(data.get("summary") or {})
    if not rows or not all(
        row.get("reviewed")
        and row.get("sale_price_total") is not None
        and str(row.get("status") or "") in {"completed", "review_required"}
        for row in rows
    ):
        raise ValueError("Review and approve every object before Final Approval")
    if summary.get("total") is None:
        raise ValueError("Project pricing must be complete before Final Approval")

    client = get_supabase_client()
    assert_run_owned(client, run_id, company_id)
    assert_estimate_owned(client, estimate_id, company_id)
    snapshot = _json_safe({
        "rows": rows,
        "project_costs": [dict(row) for row in data.get("project_costs") or []],
        "summary": summary,
    })
    response = client.rpc(
        "finalize_project_estimate",
        {
            "p_company_id": company_id,
            "p_run_id": run_id,
            "p_estimate_id": estimate_id,
            "p_snapshot": snapshot,
        },
    ).execute()
    result = response.data
    if isinstance(result, list):
        result = result[0] if result else None
    if not isinstance(result, dict) or not result.get("project_id"):
        raise RuntimeError("Final Approval did not return a Project version")
    result["proposal_pdf_path"] = publish_proposal_pdf(
        client=client,
        company_id=company_id,
        project_id=str(result["project_id"]),
        version_id=str(result["version_id"]),
        run_id=run_id,
        snapshot=snapshot,
    )
    result["proposal_pdf_url"] = load_estimate_proposal_url(
        client=client,
        company_id=company_id,
        estimate_id=estimate_id,
    )
    return result
