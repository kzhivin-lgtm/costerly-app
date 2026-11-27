from __future__ import annotations

from datetime import date, datetime
from contextlib import nullcontext
from decimal import Decimal
import math
from typing import Any

from db.company_access import assert_estimate_owned, assert_run_owned
from db.supabase_client import get_supabase_client
from use_cases.estimation import load_objects_estimation_data
from use_cases.proposal_pdf import load_estimate_proposal_url, publish_proposal_pdf, capture_proposal_document


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
    confirmed_data: dict[str, Any] | None = None,
    trace=None,
) -> dict[str, Any]:
    """Freeze one fully reviewed estimate into its durable Project version."""
    data = confirmed_data if confirmed_data is not None else load_objects_estimation_data(estimate_id)
    rows = [dict(row) for row in data.get("rows") or []]
    summary = dict(data.get("summary") or {})
    if confirmed_data is None and (not rows or not all(
        row.get("reviewed")
        and row.get("sale_price_total") is not None
        and str(row.get("status") or "") in {"completed", "review_required"}
        for row in rows
    )):
        raise ValueError("Review and approve every object before Final Approval")
    if confirmed_data is None and summary.get("total") is None:
        raise ValueError("Project pricing must be complete before Final Approval")

    client = get_supabase_client()
    assert_run_owned(client, run_id, company_id)
    assert_estimate_owned(client, estimate_id, company_id)
    existing_rows = (client.table('project_versions').select('project_id,version_id,version_number,proposal_pdf_path,snapshot')
                     .eq('company_id',company_id).eq('estimate_id',estimate_id).limit(1).execute().data or [])
    existing = existing_rows[0] if existing_rows else None
    if existing and existing.get('proposal_pdf_path'):
        return {**existing,'created':False,'proposal_pdf_url':load_estimate_proposal_url(
            client=client,company_id=company_id,estimate_id=estimate_id)}
    snapshot = _json_safe({
        "production_time_working_days": data.get('production_time_working_days'),
        "advance_payment_percent": data.get('advance_payment_percent'),
        "rows": rows,
        "project_costs": [dict(row) for row in data.get("project_costs") or []],
        "summary": summary,
    })
    if existing:
        snapshot = existing.get('snapshot') or snapshot
    else:
        with trace.span('server.proposal_sources') if trace else nullcontext():
            snapshot['document'] = capture_proposal_document(client=client,company_id=company_id,run_id=run_id,snapshot=snapshot)
    with trace.span('server.proposal_freeze') if trace else nullcontext():
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
    # A concurrent/retried approval must render the stored version, never fresh Profile values.
    stored_rows = (client.table('project_versions').select('snapshot,proposal_pdf_path')
                   .eq('company_id',company_id).eq('version_id',str(result['version_id'])).limit(1).execute().data or [])
    if not stored_rows or not isinstance(stored_rows[0].get('snapshot'),dict):
        raise RuntimeError('The approved proposal snapshot is unavailable')
    snapshot = stored_rows[0]['snapshot']
    if stored_rows[0].get('proposal_pdf_path'):
        result['proposal_pdf_path'] = stored_rows[0]['proposal_pdf_path']
        result['proposal_pdf_url'] = load_estimate_proposal_url(client=client,company_id=company_id,estimate_id=estimate_id)
        return result
    result["proposal_pdf_path"] = publish_proposal_pdf(
        client=client,
        company_id=company_id,
        project_id=str(result["project_id"]),
        version_id=str(result["version_id"]),
        run_id=run_id,
        snapshot=snapshot,
        trace=trace,
    )
    result["proposal_pdf_url"] = load_estimate_proposal_url(
        client=client,
        company_id=company_id,
        estimate_id=estimate_id,
    )
    return result
