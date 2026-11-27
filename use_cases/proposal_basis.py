"""Shared identity of the saved inputs approved for a commercial proposal."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
import math
import hashlib
import json
from typing import Any


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return _json_safe(float(value))
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        return None if not math.isfinite(value) else int(value) if value.is_integer() else value
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def pricing_signature(data: dict[str, Any]) -> str:
    """Identify the saved commercial basis, excluding progress/timing/UI state."""
    fields = ("object_key", "name", "materials", "quantity", "proposal_input_basis", "self_cost_unit", "sale_price_unit", "sale_price_total", "reviewed", "status")
    project = (data.get('document') or {}).get('project') or {}
    def metadata(key):
        value = str(data.get(key, project.get(key)) or '').strip()
        return None if value.lower() in {'', 'unknown', 'none', 'null', '-', '—'} else value
    basis = {
        "production_time_working_days": data.get('production_time_working_days'),
        "advance_payment_percent": data.get('advance_payment_percent'),
        "project_name": metadata('project_name'),
        "design_partner": metadata('design_partner'),
        "client": metadata('client'),
        "proposal_source": data.get("proposal_source"),
        "rows": [{field: row.get(field) for field in fields} for row in data.get("rows") or []],
        "project_costs": [{field: row.get(field) for field in ("object_key", "sale_price_unit", "sale_price_total")}
                          for row in data.get("project_costs") or []],
        "summary": {field: (data.get("summary") or {}).get(field) for field in ("project_price", "vat", "total", "vat_percent")},
    }
    return hashlib.sha256(json.dumps(_json_safe(basis), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
