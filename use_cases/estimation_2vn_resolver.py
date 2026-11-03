"""2VN geometry resolution for approximate furniture estimation.

The first view is visual: the bounded vision response declares which drawing
view it read and the local orientation of a printed dimension.  The second
view is numeric: this module verifies that declaration against immutable OCR
numbers and the Dimension Graph's source-side spatial candidates.  Neither
view alone is permitted to silently turn a nearby number into a cabinet axis.

The resolver intentionally returns a usable result for incomplete drawings.
Unverified dimensions remain assumptions or cross-view derivations, with their
basis retained for the later structural composer.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping


TWO_VN_V1 = "estimation_2vn_v1"
_PROJECTIONS = {"front_elevation", "side_elevation", "top_plan", "section", "isometric", "unknown"}
_AXES = {"width", "height", "depth"}
_ORIENTATIONS = {"horizontal", "vertical"}
_RESOLUTIONS = {"direct", "cross_view", "linked_zone", "assumption"}


def _unit_scale(unit: object) -> float:
    return {"mm": 1.0, "cm": 10.0, "m": 1000.0}.get(str(unit or "").casefold(), 1.0)


def _expected_axis(*, projection: str, orientation: str, top_plan_axis: str | None = None) -> str | None:
    if projection == "front_elevation":
        return "width" if orientation == "horizontal" else "height"
    if projection == "side_elevation":
        return "depth" if orientation == "horizontal" else "height"
    if projection == "top_plan":
        if orientation == "horizontal":
            return top_plan_axis if top_plan_axis in {"width", "depth"} else None
        return "depth" if top_plan_axis == "width" else "width" if top_plan_axis == "depth" else None
    if projection == "section":
        if orientation == "vertical":
            return "height"
        return top_plan_axis if top_plan_axis in {"width", "depth"} else None
    return None


def _number_mm(*, number: Mapping[str, Any], document_unit: str) -> float:
    return float(number["numeric_value"]) * _unit_scale(number.get("printed_unit") or document_unit)


def _dimension_mm(*, dimension: Mapping[str, Any], document_unit: str) -> float | None:
    try:
        return float(dimension["value"]) * _unit_scale(dimension.get("unit") or document_unit)
    except (KeyError, TypeError, ValueError):
        return None


def resolve_2vn_geometry(*, dimension_graph: Mapping[str, Any], extraction: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return normalized extraction plus a bounded 2VN audit.

    A direct witness must agree on: declared projection/orientation, an
    immutable Dimension Graph number, and its numerical value in the selected
    document unit.  A missing witness never terminates estimation, it simply
    cannot upgrade a visual guess into source geometry.
    """
    if dimension_graph.get("contract_version") != "estimation_dimension_graph_v1":
        raise ValueError("2VN resolver requires Dimension Graph")

    normalized = dict(extraction)
    assemblies = [dict(item) for item in extraction.get("assemblies") or [] if isinstance(item, Mapping)]
    normalized["assemblies"] = assemblies
    document = extraction.get("document_unit") or {}
    document_unit = str(document.get("unit") or "mm").casefold()
    numbers = {str(item.get("dimension_id")): item for item in dimension_graph.get("dimension_numbers") or [] if isinstance(item, Mapping)}
    relations_by_dimension: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for relation in dimension_graph.get("relations") or []:
        if isinstance(relation, Mapping):
            relations_by_dimension[str(relation.get("from_dimension_id") or "")].append(relation)
    graph_view_ids = {str(item.get("view_id")) for item in dimension_graph.get("views") or [] if isinstance(item, Mapping)}

    views: dict[str, dict[str, str]] = {}
    for raw in extraction.get("view_interpretations") or []:
        if not isinstance(raw, Mapping):
            continue
        view_id = str(raw.get("view_id") or "")
        projection = str(raw.get("projection") or "unknown")
        if view_id not in graph_view_ids or projection not in _PROJECTIONS:
            continue
        top_plan_axis = str(raw.get("horizontal_axis") or "")
        views[view_id] = {"projection": projection, "horizontal_axis": top_plan_axis}

    bindings_by_assembly_axis: dict[tuple[str, str], Mapping[str, Any]] = {}
    rejected_keys: set[tuple[str, str]] = set()
    rejected: list[dict[str, str]] = []
    for raw in extraction.get("dimension_bindings") or []:
        if not isinstance(raw, Mapping):
            continue
        assembly_id = str(raw.get("assembly_id") or "")
        axis = str(raw.get("axis") or "")
        view_id = str(raw.get("view_id") or "")
        orientation = str(raw.get("local_orientation") or "")
        dimension_id = str(raw.get("dimension_id") or "")
        resolution = str(raw.get("resolution") or "")
        if axis not in _AXES or view_id not in views or orientation not in _ORIENTATIONS or dimension_id not in numbers or resolution not in _RESOLUTIONS:
            rejected.append({"assembly_id": assembly_id, "axis": axis, "reason": "invalid_binding"})
            rejected_keys.add((assembly_id, axis))
            continue
        expected = _expected_axis(
            projection=views[view_id]["projection"], orientation=orientation,
            top_plan_axis=views[view_id]["horizontal_axis"],
        )
        if expected != axis:
            rejected.append({"assembly_id": assembly_id, "axis": axis, "reason": "axis_projection_mismatch"})
            rejected_keys.add((assembly_id, axis))
            continue
        bindings_by_assembly_axis.setdefault((assembly_id, axis), raw)

    witnesses: list[dict[str, Any]] = []
    outcomes: Counter[str] = Counter()
    for assembly in assemblies:
        assembly_id = str(assembly.get("assembly_id") or "")
        dimensions = assembly.get("dimensions")
        if not isinstance(dimensions, Mapping):
            continue
        updated_dimensions = dict(dimensions)
        for axis, raw_dimension in dimensions.items():
            if axis not in _AXES or not isinstance(raw_dimension, Mapping):
                continue
            binding = bindings_by_assembly_axis.get((assembly_id, axis))
            if binding is None:
                if (assembly_id, axis) in rejected_keys:
                    # A rejected source binding cannot be allowed to retain its
                    # raw number. Remove it so the deterministic composer uses
                    # a peer or bounded construction assumption instead.
                    updated_dimensions.pop(axis, None)
                    outcomes["rejected_to_fallback"] += 1
                    continue
                outcomes["unbound"] += 1
                continue
            number = numbers[str(binding["dimension_id"])]
            value_mm = _dimension_mm(dimension=raw_dimension, document_unit=document_unit)
            number_value_mm = _number_mm(number=number, document_unit=document_unit)
            relations = relations_by_dimension[str(binding["dimension_id"])]
            has_view_candidate = any(
                item.get("relation") == "nearest_view_candidate" and item.get("to_view_id") == binding["view_id"]
                for item in relations
            )
            has_vector_candidate = any(item.get("relation") == "number_to_vector_line_candidate" for item in relations)
            score = 0.60 + (0.25 if has_view_candidate else 0.0) + (0.15 if has_vector_candidate else 0.0)
            numeric_match = value_mm is not None and abs(value_mm - number_value_mm) <= max(3.0, number_value_mm * 0.003)
            resolution = str(binding["resolution"])
            verified_direct = resolution == "direct" and numeric_match and score >= 0.85
            witness = {
                "assembly_id": assembly_id, "axis": axis, "view_id": str(binding["view_id"]),
                "dimension_id": str(binding["dimension_id"]), "resolution": resolution,
                "score": round(score, 2), "numeric_match": numeric_match,
                "verification": "direct" if verified_direct else "cross_view_or_assumption",
                "evidence_refs": list(number.get("evidence_refs") or []),
            }
            witnesses.append(witness)
            if verified_direct:
                updated = dict(raw_dimension)
                updated.update({"value": number["numeric_value"], "unit": number.get("printed_unit") or document_unit,
                                "basis": "source", "evidence_refs": list(number.get("evidence_refs") or []),
                                "assumption_reason": None})
                updated_dimensions[axis] = updated
                outcomes["direct"] += 1
            elif resolution in {"cross_view", "linked_zone"}:
                updated = dict(raw_dimension)
                updated.update({"basis": "derived", "evidence_refs": list(number.get("evidence_refs") or [])})
                updated_dimensions[axis] = updated
                outcomes["derived"] += 1
            else:
                outcomes["unverified"] += 1
        assembly["dimensions"] = updated_dimensions

    # A shallow drawer face is often printed beside the side-view depth.  If a
    # drawer bank's alleged direct depth is no greater than its own front
    # height, it is not a credible usable drawer depth for an approximate BOM.
    # Prefer the largest numeric candidate attached to a declared side-depth
    # view, retain its immutable citation, and mark it derived rather than
    # pretending the heuristic is a direct measurement.
    depth_views = {
        view_id for view_id, value in views.items()
        if value["projection"] in {"side_elevation", "section"} and value["horizontal_axis"] == "depth"
    }
    side_depth_numbers = [
        number for number in numbers.values()
        if any(relation.get("relation") == "nearest_view_candidate" and relation.get("to_view_id") in depth_views
               for relation in relations_by_dimension.get(str(number.get("dimension_id") or ""), []))
    ]
    for assembly in assemblies:
        if str(assembly.get("assembly_role") or "") != "drawer_bank":
            continue
        dimensions = assembly.get("dimensions") or {}
        if not isinstance(dimensions, Mapping):
            continue
        height_mm = _dimension_mm(dimension=dimensions.get("height") or {}, document_unit=document_unit)
        depth_mm = _dimension_mm(dimension=dimensions.get("depth") or {}, document_unit=document_unit)
        if height_mm is None or depth_mm is None or depth_mm > height_mm or not side_depth_numbers:
            continue
        candidate = max(side_depth_numbers, key=lambda item: _number_mm(number=item, document_unit=document_unit))
        candidate_mm = _number_mm(number=candidate, document_unit=document_unit)
        if candidate_mm <= depth_mm:
            continue
        updated = dict(dimensions)
        updated["depth"] = {
            "value": candidate["numeric_value"], "unit": candidate.get("printed_unit") or document_unit,
            "basis": "derived", "evidence_refs": list(candidate.get("evidence_refs") or []),
            "assumption_reason": "Drawer depth was reconciled to the larger side-view depth candidate because the original depth was no greater than the drawer front height.",
        }
        assembly["dimensions"] = updated
        outcomes["drawer_depth_cross_view"] += 1
        witnesses.append({
            "assembly_id": str(assembly.get("assembly_id") or ""), "axis": "depth", "view_id": "cross_side_view",
            "dimension_id": str(candidate.get("dimension_id") or ""), "resolution": "linked_zone",
            "score": 0.0, "numeric_match": True, "verification": "drawer_depth_cross_view",
            "evidence_refs": list(candidate.get("evidence_refs") or []),
        })

    normalized["view_interpretations"] = [
        {"view_id": view_id, **value} for view_id, value in sorted(views.items())
    ]
    normalized["dimension_bindings"] = [dict(item) for item in bindings_by_assembly_axis.values()]
    audit = {
        "contract_version": TWO_VN_V1,
        "status": "ready",
        "view_interpretations": normalized["view_interpretations"],
        "dimension_witnesses": witnesses,
        "binding_outcomes": dict(sorted(outcomes.items())),
        "rejected_bindings": rejected,
        "fallback_policy": "unresolved_dimensions_continue_to_peer_or_construction_default",
    }
    return normalized, audit
