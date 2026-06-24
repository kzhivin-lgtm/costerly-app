from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


EstimateStatus = Literal["pending", "running", "completed", "failed"]
EstimateLineSection = Literal["material", "labor", "overhead"]


@dataclass(frozen=True)
class ObjectEstimateSeed:
    """Detected object data needed to create an estimation work item."""

    run_id: str
    company_id: str
    object_id: str
    object_name: str
    quantity: float


@dataclass(frozen=True)
class EstimateLineDraft:
    """One editable estimation line returned by an Estimation Agent later."""

    section: EstimateLineSection
    group_name: str
    item_name: str
    unit: str | None = None
    unit_cost: float | None = None
    quantity: float | None = None
    role: str | None = None
    hours: float | None = None
    rate: float | None = None
    monthly_cost: float | None = None
    allocation_basis: str | None = None
    raw_agent_json: dict[str, Any] = field(default_factory=dict)
