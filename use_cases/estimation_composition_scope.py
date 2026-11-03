"""Validation and enforcement of Estimation Analyze composition scopes."""

from __future__ import annotations

from typing import Any, Mapping

from agents.estimation_composition_analyze_agent import COMPOSITION_SCOPE_V1


_ROLES = {"box_carcass", "drawer_bank", "vertical_panel", "shelf_stack", "table", "countertop", "facade_set"}
_OPERABILITY = {"fixed", "drawer", "hinged", "lift_up", "none"}
_FRONT_BY_OPERABILITY = {
    "fixed": [], "none": [],
    "drawer": ["drawer_front"], "hinged": ["hinged_facade"], "lift_up": ["lift_up_facade"],
}


def _positive_int(value: object) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def validate_composition_scope(*, scope: Mapping[str, Any], input_id: str) -> dict[str, Any]:
    """Return a bounded immutable composition scope or fail before Calculation."""
    if scope.get("contract_version") != COMPOSITION_SCOPE_V1:
        raise ValueError("composition scope has an invalid contract version")
    if str(scope.get("input_id") or "") != input_id:
        raise ValueError("composition scope input does not match calculation input")
    zones: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in scope.get("zones") or []:
        if not isinstance(raw, Mapping):
            continue
        scope_id = str(raw.get("scope_id") or "").strip()
        role = str(raw.get("assembly_role") or "").strip()
        operability = str(raw.get("operability") or "").strip()
        if not scope_id or scope_id in seen or role not in _ROLES or operability not in _OPERABILITY:
            continue
        seen.add(scope_id)
        counts = dict(raw.get("counts") or {}) if isinstance(raw.get("counts"), Mapping) else {}
        allowed_fronts = _FRONT_BY_OPERABILITY[operability]
        raw_groups = raw.get("front_groups") if isinstance(raw.get("front_groups"), list) else []
        groups = []
        for group in raw_groups:
            if not isinstance(group, Mapping) or str(group.get("front_kind") or "") not in allowed_fronts:
                continue
            quantity = _positive_int(group.get("quantity"))
            if quantity:
                groups.append({
                    "front_kind": str(group["front_kind"]), "quantity": quantity,
                    "arrangement": str(group.get("arrangement") or "stacked"),
                })
        # The semantic count is authoritative.  A malformed front_groups list
        # must not turn a known three-drawer unit into six facades downstream.
        if operability == "drawer":
            quantity = _positive_int(counts.get("drawers")) or sum(item["quantity"] for item in groups)
            groups = [{"front_kind": "drawer_front", "quantity": quantity, "arrangement": "stacked"}] if quantity else []
            counts = {"drawers": quantity} if quantity else {}
        elif operability in {"hinged", "lift_up"}:
            quantity = _positive_int(counts.get("facades")) or sum(item["quantity"] for item in groups)
            kind = allowed_fronts[0]
            groups = [{"front_kind": kind, "quantity": quantity, "arrangement": "side_by_side"}] if quantity else []
            counts = {"facades": quantity} if quantity else {}
        else:
            groups, counts = [], {}
        refs = [str(item) for item in raw.get("evidence_refs") or [] if isinstance(item, str) and item]
        zones.append({
            "scope_id": scope_id, "assembly_role": role, "semantic_role": str(raw.get("semantic_role") or role),
            "operability": operability, "counts": counts, "front_groups": groups, "evidence_refs": refs,
        })
    if not zones:
        raise ValueError("composition scope has no valid zones")
    return {
        "contract_version": COMPOSITION_SCOPE_V1, "status": "ready", "input_id": input_id,
        "object_id": str(scope.get("object_id") or ""), "object_summary": str(scope.get("object_summary") or ""),
        "zones": zones, "assumptions": [str(item) for item in scope.get("assumptions") or [] if str(item).strip()],
    }


def apply_composition_scope(*, extraction: Mapping[str, Any], scope: Mapping[str, Any]) -> dict[str, Any]:
    """Make Calculation a constrained decomposition rather than re-analysis.

    Zones are created from the Analyze contract, so a Calculation response
    cannot add a new facade set or turn a fixed screen into cabinet doors.
    It may only fill dimensions, exposure and material roles for those zones.
    """
    allowed = {str(zone["scope_id"]): zone for zone in scope["zones"]}
    calculated = {
        str(item.get("assembly_id") or ""): dict(item)
        for item in extraction.get("assemblies") or [] if isinstance(item, Mapping)
    }
    remaining = list(calculated.values())
    remapped_ids: dict[str, str] = {}
    assemblies: list[dict[str, Any]] = []
    for scope_id, zone in allowed.items():
        candidate = calculated.get(scope_id)
        if candidate is None:
            # A model may preserve the previous generic assembly ids despite
            # the Calculation instruction. Match the only compatible physical
            # role in scope order, then remap its 2VN bindings before they are
            # resolved. It never grants permission for a new zone.
            candidate = next((item for item in remaining if str(item.get("assembly_role") or "") == zone["assembly_role"]), {})
        candidate_id = str(candidate.get("assembly_id") or "")
        if candidate_id:
            remapped_ids[candidate_id] = scope_id
            remaining = [item for item in remaining if str(item.get("assembly_id") or "") != candidate_id]
        assembly = dict(candidate)
        assembly.update({
            "assembly_id": scope_id,
            "assembly_role": zone["assembly_role"],
            "counts": dict(zone["counts"]),
            "front_groups": list(zone["front_groups"]),
            "evidence_refs": list(candidate.get("evidence_refs") or zone["evidence_refs"]),
        })
        assemblies.append(assembly)
    # Structural hardware comes only from the locked front topology. Preserve
    # legs as explicit physical components, but do not let Calculation inject
    # rails, hinges or gas lifts around a fixed zone.
    secondary_items = [
        dict(item) for item in extraction.get("secondary_items") or []
        if isinstance(item, Mapping) and str(item.get("role") or "") == "leg"
    ]
    bindings = []
    for raw in extraction.get("dimension_bindings") or []:
        if not isinstance(raw, Mapping):
            continue
        source_id = str(raw.get("assembly_id") or "")
        if source_id not in remapped_ids:
            continue
        bindings.append({**dict(raw), "assembly_id": remapped_ids[source_id]})
    return {
        **dict(extraction), "assemblies": assemblies, "dimension_bindings": bindings, "secondary_items": secondary_items,
        "composition_scope": dict(scope),
    }


def calculation_handoff(*, scope: Mapping[str, Any], dimension_graph: Mapping[str, Any]) -> dict[str, Any]:
    """Stable, inspectable contract passed into the second model call."""
    return {
        "contract_version": "estimation_calculation_handoff_v1",
        "composition_scope": dict(scope),
        "dimension_graph_summary": {
            "contract_version": dimension_graph.get("contract_version"),
            "dimension_count": len(dimension_graph.get("dimension_numbers") or []),
            "view_count": len(dimension_graph.get("views") or []),
        },
        "calculation_boundary": "May fill geometry and construction roles only. It may not add, remove or reclassify scope zones or operability.",
    }
