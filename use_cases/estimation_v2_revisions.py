"""Pure revision and idempotency rules for Estimation v2 objects."""

from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


REVISION_ACTION_VALUES = frozenset({
    "unchanged", "update_display_name", "reaggregate_quantity", "deactivate",
    "reactivate_reuse", "reextract",
})
REQUIRED_COMPOSITION_VERSION_KEYS = frozenset({
    "material_catalog", "pricing_catalog", "labor_catalog", "machinery_snapshot",
    "overhead_policy", "pricing_policy",
})
_OBJECT_STATE_FIELDS = frozenset({
    "object_id", "object_name", "quantity", "ignored", "evidence_signature",
})
_PREVIOUS_STATE_FIELDS = _OBJECT_STATE_FIELDS | {"object_input_revision"}


class EstimationV2RevisionError(ValueError):
    pass


def _validate_state(value: Mapping[str, Any], *, previous: bool) -> dict[str, Any]:
    state = dict(value)
    expected = _PREVIOUS_STATE_FIELDS if previous else _OBJECT_STATE_FIELDS
    missing = set(expected) - set(state)
    extra = set(state) - set(expected)
    if missing or extra:
        raise EstimationV2RevisionError(
            f"object state keys are invalid, missing={sorted(missing)}, extra={sorted(extra)}"
        )
    for field in ("object_id", "object_name", "evidence_signature"):
        if not str(state[field] or "").strip():
            raise EstimationV2RevisionError(f"{field} must be non-empty")
    quantity = state["quantity"]
    if isinstance(quantity, bool):
        raise EstimationV2RevisionError("quantity must be numeric")
    try:
        number = float(quantity)
    except (TypeError, ValueError) as exc:
        raise EstimationV2RevisionError("quantity must be numeric") from exc
    if not isfinite(number) or number <= 0:
        raise EstimationV2RevisionError("quantity must be greater than zero")
    if not isinstance(state["ignored"], bool):
        raise EstimationV2RevisionError("ignored must be boolean")
    if previous:
        revision = state["object_input_revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise EstimationV2RevisionError("object_input_revision must be a positive integer")
    return state


def plan_object_revision(
    *,
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, Any]:
    """Plan only the work implied by approved File Review changes."""
    before = _validate_state(previous, previous=True)
    after = _validate_state(current, previous=False)
    if str(before["object_id"]) != str(after["object_id"]):
        raise EstimationV2RevisionError("object_id cannot change across revisions")

    name_changed = str(before["object_name"]) != str(after["object_name"])
    quantity_changed = float(before["quantity"]) != float(after["quantity"])
    evidence_changed = str(before["evidence_signature"]) != str(after["evidence_signature"])
    revision = int(before["object_input_revision"])

    if after["ignored"]:
        action = "unchanged" if before["ignored"] else "deactivate"
        result = (action, revision, False, True, False, False)
    elif evidence_changed:
        result = ("reextract", revision + 1, True, False, True, True)
    elif quantity_changed:
        result = ("reaggregate_quantity", revision + 1, True, True, False, True)
    elif before["ignored"]:
        result = ("reactivate_reuse", revision, True, True, False, True)
    elif name_changed:
        result = ("update_display_name", revision, True, True, False, False)
    else:
        result = ("unchanged", revision, True, True, False, False)

    action, next_revision, active, reuse_facts, queue_extraction, recalculate = result
    return {
        "action": action,
        "next_object_input_revision": next_revision,
        "active": active,
        "reuse_facts": reuse_facts,
        "queue_extraction": queue_extraction,
        "recalculate": recalculate,
        "display_name_changed": name_changed,
        "quantity_changed": quantity_changed,
        "evidence_changed": evidence_changed,
    }


def build_composition_idempotency_key(
    *,
    input_id: str,
    object_input_revision: int,
    versions: Mapping[str, Any],
) -> str:
    """Return one stable key for the same frozen input and version set."""
    resolved_input_id = str(input_id or "").strip()
    if not resolved_input_id:
        raise EstimationV2RevisionError("input_id must be non-empty")
    if isinstance(object_input_revision, bool) or not isinstance(object_input_revision, int) or object_input_revision < 1:
        raise EstimationV2RevisionError("object_input_revision must be a positive integer")
    missing = set(REQUIRED_COMPOSITION_VERSION_KEYS) - set(versions)
    if missing:
        raise EstimationV2RevisionError(f"composition versions missing keys: {sorted(missing)}")
    normalized_versions = {
        key: str(versions[key] or "").strip()
        for key in sorted(REQUIRED_COMPOSITION_VERSION_KEYS)
    }
    if not all(normalized_versions.values()):
        raise EstimationV2RevisionError("composition versions must be non-empty")
    payload = {
        "input_id": resolved_input_id,
        "object_input_revision": object_input_revision,
        "versions": normalized_versions,
    }
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
    return f"estimation-v2:{sha256(encoded).hexdigest()}"
