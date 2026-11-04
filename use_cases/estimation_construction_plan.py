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
            material["normalizations"].append("stock_build_up_does_not_match_finished_thickness")
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
