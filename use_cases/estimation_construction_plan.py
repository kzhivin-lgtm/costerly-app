"""V6.1 material intent validation and locked construction handoff.

Source references validate provenance, not the truth of a visual inference.
The latter remains an explicitly recorded estimating assumption.
"""
from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping, Sequence

CONSTRUCTION_VERSION = "estimation_construction_v6_1"
MATERIAL_ROLES = {
    "visible_sheet", "carcass_sheet", "internal_sheet", "backing_sheet", "worktop_sheet",
    "finish", "leg", "edge_banding",
}
HIDDEN_ROLES = {"internal_sheet", "backing_sheet"}


def with_shared_document_context(inputs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Read-time compatibility for legacy inputs from the SAME immutable run.

    Full-file Analyze can cite a legend owned by another input's source page.
    Each subsequent composer must retain those same validated references. This
    adds shared context only; it never changes object-owned geometry/membership
    or writes back to the immutable input records.
    """
    identities = {(str((row.get("input_payload") or {}).get("company_id") or ""),
                   str((row.get("input_payload") or {}).get("run_id") or "")) for row in inputs}
    if len(identities) > 1:
        raise ValueError("shared construction context requires one company/file run")
    collected: dict[str, dict[str, Any]] = {kind: {} for kind in ("artifacts", "ocr_blocks", "ocr_literal_items")}
    for row in inputs:
        for container in ("document_context", "evidence"):
            for kind, items in collected.items():
                for item in ((row.get("input_payload") or {}).get(container) or {}).get(kind) or []:
                    if not isinstance(item, Mapping):
                        continue
                    if kind == "artifacts" and item.get("artifact_kind") != "page":
                        continue
                    ref = item.get("storage_ref") if kind == "artifacts" else item.get("block_ref")
                    if ref:
                        items.setdefault(str(ref), deepcopy(dict(item)))
    result = []
    for row in inputs:
        copied = deepcopy(dict(row))
        payload = copied.setdefault("input_payload", {})
        context = payload.setdefault("document_context", {})
        context.update({kind: list(items.values()) for kind, items in collected.items()})
        context.setdefault("contract_version", "estimation_document_context_v6_1")
        context["source_input_ids"] = sorted(str(item.get("input_id") or "") for item in inputs)
        context["boundary"] = "Shared immutable file context, not object geometry membership."
        result.append(copied)
    return result


def evidence_refs(inputs: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        str(item.get("storage_ref") or item.get("block_ref"))
        for row in inputs
        for container in ("evidence", "document_context")
        for kind in ("artifacts", "ocr_blocks", "ocr_literal_items")
        for item in ((row.get("input_payload") or {}).get(container) or {}).get(kind) or []
        if isinstance(item, Mapping) and (item.get("storage_ref") or item.get("block_ref"))
    }


def positive(value: Any, default: float) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) and result > 0 else default
    except (ValueError, TypeError):
        return default


def validate_thickness_witnesses(scope: Mapping[str, Any], *, dimension_graph: Mapping[str, Any],
                                 dimension_scale_gate: Mapping[str, Any]) -> dict[str, Any]:
    """Numeric consistency only, never infer ownership of a dimension line.

    A known 19-cm reference cannot prove 19-mm stock. Preserve the selected
    construction as an assumption, but remove its contradicted source claim.
    Without an explicit unit or the existing scale guard, do not guess a unit.
    """
    result = deepcopy(dict(scope))
    convention = (dimension_scale_gate.get("decision") or {}).get("required_unit")
    scales = {"mm": 1, "cm": 10, "m": 1000}
    numeric_by_ref = {}
    for number in dimension_graph.get("dimension_numbers") or []:
        scale = scales.get(number.get("printed_unit") or convention)
        if scale is None:
            continue
        for ref in number.get("evidence_refs") or []:
            numeric_by_ref[ref] = float(number["numeric_value"]) * scale
    for zone in result.get("zones") or []:
        for material in zone.get("material_roles") or []:
            if material.get("thickness_basis") != "source":
                continue
            values = [numeric_by_ref[ref] for ref in material.get("thickness_evidence_refs") or [] if ref in numeric_by_ref]
            thickness = float(material.get("finished_thickness_mm") or 0)
            if values and not any(abs(thickness - value) <= 1 for value in values):
                reason = "Cited dimension does not match finished thickness in the source unit; selected construction retained as an assumption."
                material.update(thickness_basis="assumption", thickness_evidence_refs=[],
                                construction_reason=f"{material.get('construction_reason') or ''} {reason}".strip())
                material.setdefault("normalizations", []).append("contradicted_thickness_source_downgraded")
                result.setdefault("assumptions", []).append(f"{zone['scope_id']}/{material['role']}: {reason}")
    return result


def normalize_palette(raw: Any, *, allowed_refs: set[str], families: Sequence[str]) -> dict[str, dict[str, Any]]:
    palette = {}
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, Mapping):
            continue
        material_id = str(item.get("material_id") or "")
        if not material_id or material_id in palette:
            raise ValueError("construction palette requires unique material ids")
        family = str(item.get("family") or "")
        if family not in families:
            raise ValueError("construction palette has unsupported material family")
        basis = str(item.get("basis") or "construction_default")
        if basis not in {"source", "linked_source", "visual_assumption", "construction_default"}:
            raise ValueError("construction palette has invalid provenance")
        chain = []
        for link in item.get("evidence_chain") or []:
            if isinstance(link, Mapping) and link.get("ref") in allowed_refs:
                chain.append({"ref": link["ref"], "observation": str(link.get("observation") or ""),
                              "kind": str(link.get("kind") or "observation")})
        reason = str(item.get("reason") or "").strip()
        audit = []
        kinds = {link["kind"] for link in chain}
        if basis == "source" and not chain or basis == "linked_source" and not {"callout", "definition"} <= kinds:
            basis = "construction_default"
            audit.append("unsupported_source_assignment_downgraded")
            reason = "Source assignment could not be traced; retained as an estimating assumption."
        specification = dict(item.get("specification") or {})
        palette[material_id] = {
            "material_id": material_id, "source_name": str(item.get("source_name") or family),
            "family": family, "specification": specification, "intent_basis": basis,
            "basis": "source_evidence" if basis in {"source", "linked_source"} else "construction_assumption",
            "evidence_refs": list(dict.fromkeys(link["ref"] for link in chain)) if basis in {"source", "linked_source"} else [],
            "evidence_chain": chain, "reason": reason or "Conventional material assumption for the observed construction.",
            "attribute_assumptions": {str(key): str(value) for key, value in (item.get("attribute_assumptions") or {}).items()}
                if isinstance(item.get("attribute_assumptions"), Mapping) else {},
            "normalizations": audit,
        }
    if not palette:
        raise ValueError("construction palette is empty")
    return palette


def lock_zone_materials(zone: Mapping[str, Any], palette: Mapping[str, Mapping[str, Any]], *, allowed_refs: set[str]) -> list[dict[str, Any]]:
    """Compile explicit role assignments, without allowing Calculation to choose families."""
    result = []
    for assignment in zone.get("material_assignments") or []:
        role = str(assignment.get("role") or "")
        if role not in MATERIAL_ROLES:
            raise ValueError("construction assignment has unsupported role")
        material_id = str(assignment.get("material_id") or "")
        if material_id not in palette:
            raise ValueError("construction assignment references unknown material")
        material = deepcopy(palette[material_id])
        material["role"] = role
        material["layer_count"] = min(8, max(1, int(positive(assignment.get("layer_count"), 1))))
        stock = positive((material.get("specification") or {}).get("thickness_mm"), 0)
        material["finished_thickness_mm"] = positive(assignment.get("finished_thickness_mm"), stock * material["layer_count"])
        material["construction_reason"] = str(assignment.get("reason") or material["reason"])
        material["thickness_basis"] = str(assignment.get("thickness_basis") or "assumption")
        material["thickness_evidence_refs"] = [ref for ref in assignment.get("thickness_evidence_refs") or [] if ref in allowed_refs]
        if material["thickness_basis"] not in {"source", "derived", "assumption"} or (material["thickness_basis"] == "source" and not material["thickness_evidence_refs"]):
            material["thickness_basis"] = "assumption"
        if stock and abs(material["finished_thickness_mm"] - stock * material["layer_count"]) > 1:
            if material["thickness_basis"] != "assumption":
                raise ValueError("source or derived finished thickness contradicts purchased stock layers")
            material["finished_thickness_mm"] = stock * material["layer_count"]
            material["normalizations"].append("assumed_finished_thickness_aligned_to_selected_stock_layers")
            material["construction_reason"] += " Inconsistent assumed finished thickness aligned to the selected purchased stock layers."
        material["alternatives"] = []
        if role == "finish":
            material["applies_to_roles"] = [str(value) for value in assignment.get("applies_to_roles") or ["visible_sheet", "carcass_sheet", "worktop_sheet"]
                                            if value in {"visible_sheet", "carcass_sheet", "worktop_sheet", "internal_sheet", "backing_sheet"}]
        # Alternatives change a hidden substrate, never a specified finish or geometry.
        if role in HIDDEN_ROLES and material["basis"] != "source_evidence" and material["layer_count"] == 1:
            for alt_id in dict.fromkeys(assignment.get("alternative_material_ids") or []):
                alt = palette.get(alt_id)
                if not alt or alt_id == material_id:
                    continue
                alt_stock = positive((alt.get("specification") or {}).get("thickness_mm"), 0)
                if stock > 0 and alt_stock == stock:
                    material["alternatives"].append(deepcopy(alt))
        edge_id = assignment.get("edge_material_id")
        if edge_id:
            if edge_id not in palette:
                raise ValueError("construction edge references unknown material")
            edge = deepcopy(palette[edge_id])
            edge["role"] = "edge_banding"
            edge_width = positive(edge["specification"].get("width_mm"), 0)
            finished = material["finished_thickness_mm"]
            if finished and edge_width < finished:
                if edge["basis"] == "source_evidence" and edge_width:
                    raise ValueError("specified edge width is smaller than finished panel thickness")
                edge["specification"]["width_mm"] = finished
                edge["normalizations"].append("assumed_edge_width_covers_finished_panel")
                edge["reason"] += " Assumed edge width raised to cover the finished panel thickness, not one purchased layer."
            material["edge_material"] = edge
            material["alternatives"] = []  # A substitution would also need an edge-system comparison.
        result.append(material)
    if not result:
        raise ValueError("construction zone has no material assignment")
    if len({item["role"] for item in result}) != len(result):
        raise ValueError("construction zone has duplicate material roles")
    # An omitted hidden material is not permission to invent another family.
    # Reuse the zone's stock, with an explicit single-layer estimating default.
    roles = {item["role"] for item in result}
    seed = next((item for item in result if item["role"] in {"visible_sheet", "carcass_sheet", "internal_sheet", "worktop_sheet"}), None)
    required = {
        "drawer_bank": {"visible_sheet", "carcass_sheet", "internal_sheet", "backing_sheet"},
        "box_carcass": {"visible_sheet", "carcass_sheet", "internal_sheet", "backing_sheet"},
        "shelf_stack": {"carcass_sheet", "internal_sheet", "backing_sheet"},
        "vertical_panel": {"visible_sheet"}, "facade_set": {"visible_sheet"},
        "countertop": {"worktop_sheet"}, "table": {"worktop_sheet"}, "support": {"leg"},
    }.get(str(zone.get("assembly_role")), set())
    for role in sorted(required - roles):
        if seed is None or role == "leg":
            raise ValueError(f"construction zone is missing required material role: {role}")
        material = deepcopy(seed)
        material.update(role=role, alternatives=[], basis="construction_assumption", evidence_refs=[],
                        intent_basis="construction_default", layer_count=1,
                        finished_thickness_mm=positive(seed["specification"].get("thickness_mm"), 0),
                        reason="Unspecified component uses the zone's existing stock as a single-layer estimating assumption.")
        material.pop("edge_material", None)
        if role in {"carcass_sheet", "visible_sheet", "worktop_sheet"}:
            material.update(layer_count=seed["layer_count"], finished_thickness_mm=seed["finished_thickness_mm"],
                            reason="Unspecified structural role follows the zone's assigned finished panel construction.")
        material["construction_reason"] = material["reason"]
        material["thickness_basis"] = "assumption"
        material["thickness_evidence_refs"] = []
        result.append(material)
    return result


def normalize_construction_scope(scope: Mapping[str, Any], *, palette: Mapping[str, Mapping[str, Any]], allowed_refs: set[str]) -> dict[str, Any]:
    result = deepcopy(dict(scope))
    result["construction_version"] = CONSTRUCTION_VERSION
    result["material_palette"] = deepcopy(dict(palette))
    ids = {str(zone.get("scope_id") or "") for zone in result["zones"]}
    for zone in result["zones"]:
        # A decorative "facade" is not an operating front. Canonicalize only
        # the fully fixed, zero-front contract; never rescue a hinged screen.
        if (zone.get("assembly_role") == "facade_set" and zone.get("panel_groups")
                and zone.get("operability") in {"fixed", "none"}
                and not zone.get("front_groups")
                and not any((zone.get("counts") or {}).get(key) for key in ("drawers", "facades"))):
            zone["assembly_role"] = "vertical_panel"
            result.setdefault("assumptions", []).append(
                f"{zone['scope_id']}: fixed decorative facade groups use the fixed panel composer; no operating hardware.")
        zone["material_roles"] = lock_zone_materials(zone, palette, allowed_refs=allowed_refs)
        zone["quantity"] = max(1, int(positive(zone.get("quantity"), 1)))
        zone["evidence_refs"] = [ref for ref in zone.get("evidence_refs") or [] if ref in allowed_refs]
        zone["geometry_links"] = [
            {"axis": link["axis"], "peer_scope_id": link["peer_scope_id"], "reason": str(link.get("reason") or "")}
            for link in zone.get("geometry_links") or []
            if isinstance(link, Mapping) and link.get("axis") in {"width", "height", "depth"}
            and link.get("peer_scope_id") in ids and link.get("peer_scope_id") != zone["scope_id"]
        ]
        groups = []
        if zone.get("panel_groups") and zone.get("assembly_role") != "vertical_panel":
            raise ValueError("construction panel groups require a fixed panel assembly")
        for group in zone.get("panel_groups") or []:
            if not isinstance(group, Mapping) or not group.get("group_id"):
                raise ValueError("construction panel group requires identity")
            role = group.get("material_role") or "visible_sheet"
            if role not in {item["role"] for item in zone["material_roles"]}:
                raise ValueError("construction panel group has no assigned material")
            groups.append({"group_id": str(group["group_id"]), "component_role": str(group.get("component_role") or "panel"),
                           "quantity": max(1, int(positive(group.get("quantity"), 1))), "material_role": role,
                           "reason": str(group.get("reason") or "Observed fixed panel group.")})
        if len({group["group_id"] for group in groups}) != len(groups):
            raise ValueError("construction panel groups require unique ids")
        zone["panel_groups"] = groups
        zone["construction"] = str(zone.get("construction") or "conventional")
        zone["exposure"] = {side: bool((zone.get("exposure") or {}).get(side)) for side in ("left", "right")}
    used_ids = {material["material_id"] for zone in result["zones"] for material in zone["material_roles"]}
    used_ids.update(alt["material_id"] for zone in result["zones"] for material in zone["material_roles"] for alt in material.get("alternatives") or [])
    used_ids.update(material["edge_material"]["material_id"] for zone in result["zones"] for material in zone["material_roles"] if material.get("edge_material"))
    result["material_palette"] = {key: value for key, value in result["material_palette"].items() if key in used_ids}
    return result


def apply_locked_construction(assembly: dict[str, Any], zone: Mapping[str, Any]) -> None:
    measured = {str(group.get("group_id")): group for group in assembly.get("panel_groups") or [] if isinstance(group, Mapping)}
    assembly["panel_groups"] = [
        {**deepcopy(group), "dimensions": deepcopy((measured.get(group["group_id"]) or {}).get("dimensions") or {})}
        for group in zone.get("panel_groups") or []
    ]
    for key in ("material_roles", "quantity", "geometry_links", "construction", "exposure"):
        assembly[key] = deepcopy(zone[key])
    assembly["construction_version"] = CONSTRUCTION_VERSION
