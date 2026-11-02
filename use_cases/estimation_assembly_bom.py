"""Validate an assembly-first construction interpretation into material facts."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


ASSEMBLY_BOM_V1 = "estimation_assembly_bom_v1"


def _positive(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _allowed_refs(payload: Mapping[str, Any]) -> set[str]:
    evidence = payload.get("evidence") or {}
    return {
        str(item.get("storage_ref") or item.get("block_ref") or "")
        for kind in ("artifacts", "ocr_blocks", "ocr_literal_items")
        for item in evidence.get(kind) or []
        if isinstance(item, Mapping) and str(item.get("storage_ref") or item.get("block_ref") or "")
    }


def _refs(value: Any, *, allowed: set[str], required: bool, field: str) -> list[str]:
    if value in (None, []) and not required:
        return []
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item in allowed for item in value):
        raise ValueError(f"{field} must contain only immutable evidence references")
    return list(value)


def _integer(value: Any, *, field: str) -> int:
    number = _positive(value)
    if number is None or int(number) != number:
        raise ValueError(f"{field} must be a positive integer")
    return int(number)


def build_assembly_bom(*, input_row: Mapping[str, Any], dimension_graph: Mapping[str, Any], extraction: Mapping[str, Any], allowed_material_families: Sequence[str]) -> dict[str, Any]:
    """Convert interpreted assemblies to parts without a product-type recipe.

    The model may describe only visible or bounded inferred construction.  This
    validator never supplies a hidden wardrobe/cabinet default and never turns
    a naked number into an object axis.
    """
    payload = input_row.get("input_payload") or {}
    if payload.get("contract_version") != "estimation_input_v4":
        raise ValueError("assembly BOM requires estimation_input_v4")
    if dimension_graph.get("contract_version") != "estimation_dimension_graph_v1":
        raise ValueError("assembly BOM requires the immutable Dimension Graph")
    object_payload = payload.get("object") or {}
    allowed_refs = _allowed_refs(payload)
    allowed_families = {str(item) for item in allowed_material_families}
    materials: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    assemblies: list[dict[str, Any]] = []
    assumptions: list[str] = []
    requirement_ids: dict[tuple[str, str, str, str], str] = {}

    def requirement_id(*, material: Mapping[str, Any]) -> str:
        key = (
            str(material["family"]), str(material["source_name"]), str(material["basis"]),
            json.dumps(material["specification"], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        existing = requirement_ids.get(key)
        if existing:
            return existing
        result = f"material-{len(requirement_ids) + 1:03d}"
        requirement_ids[key] = result
        materials.append({"requirement_id": result, **dict(material), "quantity": None, "unit": None})
        return result

    seen_assemblies: set[str] = set()
    for raw_assembly in extraction.get("assemblies") or []:
        if not isinstance(raw_assembly, Mapping):
            continue
        assembly_id = str(raw_assembly.get("assembly_id") or "").strip()
        if not assembly_id or assembly_id in seen_assemblies:
            raise ValueError("assembly_id must be unique and non-empty")
        seen_assemblies.add(assembly_id)
        assembly_refs = _refs(raw_assembly.get("evidence_refs"), allowed=allowed_refs, required=True, field=f"{assembly_id}.evidence_refs")
        component_ids: set[str] = set()
        assembly_components = []
        for raw_component in raw_assembly.get("components") or []:
            if not isinstance(raw_component, Mapping):
                continue
            component_id = str(raw_component.get("component_id") or "").strip()
            role = str(raw_component.get("component_role") or "").strip()
            if not component_id or component_id in component_ids or not role:
                raise ValueError(f"{assembly_id} component requires a unique id and role")
            component_ids.add(component_id)
            quantity = _integer(raw_component.get("quantity"), field=f"{assembly_id}.{component_id}.quantity")
            length = _positive(raw_component.get("length_mm"))
            width = _positive(raw_component.get("width_mm"))
            if length is None or width is None:
                raise ValueError(f"{assembly_id}.{component_id} requires positive finished length and width")
            geometry_basis = str(raw_component.get("geometry_basis") or "")
            geometry_refs = _refs(raw_component.get("geometry_evidence_refs"), allowed=allowed_refs, required=geometry_basis in {"evidence", "derived"}, field=f"{assembly_id}.{component_id}.geometry_evidence_refs")
            assumption_reason = raw_component.get("assumption_reason")
            if geometry_basis == "assumption":
                if geometry_refs or not isinstance(assumption_reason, str) or not assumption_reason.strip():
                    raise ValueError(f"{assembly_id}.{component_id} assumption requires a reason and no source geometry")
                assumptions.append(assumption_reason.strip())
            elif geometry_basis not in {"evidence", "derived"}:
                raise ValueError(f"{assembly_id}.{component_id} has unsupported geometry basis")
            material = raw_component.get("material")
            if not isinstance(material, Mapping):
                raise ValueError(f"{assembly_id}.{component_id} requires material")
            family = str(material.get("family") or "").strip()
            source_name = str(material.get("source_name") or "").strip()
            material_basis = str(material.get("basis") or "")
            if family not in allowed_families or not source_name or material_basis not in {"source_evidence", "construction_assumption"}:
                raise ValueError(f"{assembly_id}.{component_id} has unsupported material")
            material_refs = _refs(material.get("evidence_refs"), allowed=allowed_refs, required=material_basis == "source_evidence", field=f"{assembly_id}.{component_id}.material.evidence_refs")
            if material_basis == "construction_assumption" and material_refs:
                raise ValueError(f"{assembly_id}.{component_id} assumption material may not claim source evidence")
            specification = material.get("specification")
            if not isinstance(specification, Mapping):
                raise ValueError(f"{assembly_id}.{component_id}.material.specification must be an object")
            thickness = _positive(specification.get("thickness_mm"))
            if thickness is None:
                raise ValueError(f"{assembly_id}.{component_id} requires an explicit or assumed thickness_mm")
            normalized_material = {
                "source_name": source_name, "family": family, "specification": dict(specification),
                "basis": material_basis, "evidence_refs": material_refs,
            }
            material_requirement_id = requirement_id(material=normalized_material)
            part_id = f"{assembly_id}:{component_id}"
            parts.append({
                "part_id": part_id, "assembly_id": assembly_id, "component_role": role,
                "material_requirement_id": material_requirement_id, "quantity": quantity,
                "length_mm": round(length, 3), "width_mm": round(width, 3), "rotation_allowed": True,
                "basis": geometry_basis, "evidence_refs": geometry_refs,
                "assumption_reason": assumption_reason.strip() if isinstance(assumption_reason, str) else None,
            })
            assembly_components.append(part_id)
        assemblies.append({"assembly_id": assembly_id, "evidence_refs": assembly_refs, "part_ids": assembly_components})
    if not parts or not materials:
        raise ValueError("assembly BOM has no material-bearing components")
    preview_refs = sorted(ref for ref in allowed_refs if ref.startswith("storage://"))
    return {
        "contract_version": ASSEMBLY_BOM_V1,
        "input_id": str(input_row.get("input_id") or ""),
        "object_input_revision": int(input_row.get("object_input_revision") or 1),
        "run_id": str(payload.get("run_id") or ""), "company_id": str(payload.get("company_id") or ""),
        "object_id": str(object_payload.get("object_id") or ""), "object_name": str(object_payload.get("object_name") or ""),
        "quantity": object_payload.get("quantity") or 1, "status": "ready",
        "dimension_graph_contract": str(dimension_graph["contract_version"]),
        "assemblies": assemblies, "materials": materials, "parts": parts,
        "assumptions": list(dict.fromkeys(assumptions)),
        "omissions": [str(item) for item in extraction.get("omissions") or [] if str(item).strip()],
        "primary_preview_ref": preview_refs[0],
    }
