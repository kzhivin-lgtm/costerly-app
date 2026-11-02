"""V4.15 structural composition for an approximate material BOM.

The visual model identifies large physical assemblies and source dimensions.
This module, not the model, expands those assemblies into conventional
material-bearing parts.  It deliberately models a small set of construction
topologies rather than a catalogue of products.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1


_UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0}
_ROLES = {
    "box_carcass", "drawer_bank", "vertical_panel", "shelf_stack",
    "table", "countertop", "facade_set",
}
_MATERIAL_ROLES = {
    "visible_sheet", "internal_sheet", "backing_sheet", "worktop_sheet",
    "finish", "drawer_slide", "leg",
}
_FAMILY_PREFERENCE = {
    "visible_sheet": ("mdf_hdf", "melamine_faced_particleboard", "particleboard"),
    "internal_sheet": ("melamine_faced_particleboard", "particleboard", "mdf_hdf"),
    "backing_sheet": ("fibreboard_hardboard", "mdf_hdf", "particleboard"),
    "worktop_sheet": ("mdf_hdf", "melamine_faced_particleboard", "particleboard"),
    "finish": ("paint_lacquer_stain",),
    "drawer_slide": ("hardware_drawer_slide",),
    "leg": ("purchased_fabricated_component",),
}
_FURNITURE_PRIMARY_SPAN_MIN_MM = 450.0
_FURNITURE_PRIMARY_SPAN_MAX_MM = 6000.0


def _positive(value: Any, *, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive number") from exc
    if result <= 0:
        raise ValueError(f"{field} must be a positive number")
    return result


def _integer(value: Any, *, field: str, default: int = 0) -> int:
    if value is None:
        return default
    result = _positive(value, field=field)
    if int(result) != result:
        raise ValueError(f"{field} must be a whole positive number")
    return int(result)


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
        raise ValueError(f"{field} must contain immutable evidence references")
    return list(value)


def _unit_context(raw: Any, *, allowed: set[str]) -> tuple[str, list[str], str | None]:
    if not isinstance(raw, Mapping):
        raise ValueError("document_unit is required")
    unit = str(raw.get("unit") or "").casefold()
    if unit not in _UNIT_TO_MM:
        raise ValueError("document_unit.unit must be mm, cm or m")
    basis = str(raw.get("basis") or "")
    refs = _refs(raw.get("evidence_refs"), allowed=allowed, required=basis == "explicit_source", field="document_unit.evidence_refs")
    reason = str(raw.get("assumption_reason") or "").strip() or None
    if basis not in {"explicit_source", "document_convention_assumption"}:
        raise ValueError("document_unit.basis is invalid")
    if basis == "document_convention_assumption" and not reason:
        raise ValueError("document_unit assumption requires a reason")
    if basis == "document_convention_assumption" and refs:
        raise ValueError("document_unit assumption may not claim source evidence")
    return unit, refs, reason


def _resolve_document_unit(*, extraction: Mapping[str, Any], allowed: set[str]) -> tuple[str, list[str], str | None, str]:
    """Resolve a unitless furniture drawing before any part is composed.

    A unitless document is resolved by comparing complete scale scenarios for
    primary assemblies, not by trusting one value or document metadata. Each
    assembly contributes one vote from its source/derived width, height and
    depth axes. Counts, thicknesses and unassigned OCR numbers are excluded.
    A valid scenario makes a majority of assemblies furniture-scale without
    making a material number of them micro-furniture or architecture-scale.
    """
    unit, refs, reason = _unit_context(extraction.get("document_unit"), allowed=allowed)
    raw_context = extraction.get("document_unit") or {}
    if str(raw_context.get("basis") or "") == "explicit_source":
        return unit, refs, reason, "explicit_source"
    assemblies: list[list[float]] = []
    for assembly in extraction.get("assemblies") or []:
        if not isinstance(assembly, Mapping):
            continue
        dimensions = assembly.get("dimensions") or {}
        if not isinstance(dimensions, Mapping):
            continue
        axes: list[float] = []
        for raw_dimension in dimensions.values():
            if not isinstance(raw_dimension, Mapping):
                continue
            # A model-selected per-axis `mm` is still only a convention. Only
            # an explicitly sourced unit can defeat this deterministic guard.
            if str(raw_dimension.get("unit_basis") or "") == "explicit_source":
                continue
            if str(raw_dimension.get("basis") or "") not in {"source", "derived"}:
                continue
            try:
                value = _positive(raw_dimension.get("value"), field="unit_scenario.dimension")
            except ValueError:
                continue
            axes.append(value)
        # One isolated number has no physical scale. Two or three assigned
        # outer axes describe a primary assembly and count exactly once.
        if len(axes) >= 2:
            assemblies.append(axes)
    if not assemblies:
        return unit, refs, reason, "model_document_convention"

    def scenario_score(candidate_unit: str) -> tuple[int, int, int]:
        multiplier = _UNIT_TO_MM[candidate_unit]
        plausible = micro = oversized = 0
        for axes in assemblies:
            span = max(axes) * multiplier
            if span < _FURNITURE_PRIMARY_SPAN_MIN_MM:
                micro += 1
            elif span > _FURNITURE_PRIMARY_SPAN_MAX_MM:
                oversized += 1
            else:
                plausible += 1
        return plausible, micro, oversized

    scores = {candidate: scenario_score(candidate) for candidate in _UNIT_TO_MM}
    # Candidate ranking is deterministic. A candidate needs a majority of
    # physical assemblies in the furniture envelope. Ties retain the model's
    # declared convention because geometry alone has no further evidence.
    majority = len(assemblies) // 2 + 1
    viable = [
        candidate for candidate, (plausible, micro, oversized) in scores.items()
        if plausible >= majority and plausible > micro and plausible > oversized
    ]
    if viable:
        selected = max(
            viable,
            key=lambda candidate: (
                scores[candidate][0], -scores[candidate][1] - scores[candidate][2],
                candidate == unit,
            ),
        )
        selected_score = scores[selected]
        return (
            selected, [],
            (
                "Unitless primary-assembly scenario selected "
                f"{selected}: {selected_score[0]}/{len(assemblies)} furniture-scale, "
                f"{selected_score[1]} micro, {selected_score[2]} oversized."
            ),
            "primary_assembly_scale_scenario",
        )
    return unit, refs, reason, "model_document_convention"


def _dimension(
    raw: Any, *, default_unit: str, allowed: set[str], field: str,
    force_document_unit: bool = False,
) -> tuple[float, list[str], str, str | None]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field} is required")
    explicit_axis_unit = str(raw.get("unit_basis") or "") == "explicit_source"
    selected_unit = raw.get("unit") if (explicit_axis_unit or not force_document_unit) else default_unit
    unit = str(selected_unit or default_unit).casefold()
    if unit not in _UNIT_TO_MM:
        raise ValueError(f"{field}.unit must be mm, cm or m")
    basis = str(raw.get("basis") or "")
    refs = _refs(raw.get("evidence_refs"), allowed=allowed, required=basis in {"source", "derived"}, field=f"{field}.evidence_refs")
    reason = str(raw.get("assumption_reason") or "").strip() or None
    if basis not in {"source", "derived", "assumption"}:
        raise ValueError(f"{field}.basis is invalid")
    if basis == "assumption" and not reason:
        raise ValueError(f"{field} assumption requires a reason")
    if basis == "assumption" and refs:
        raise ValueError(f"{field} assumption may not claim source evidence")
    return round(_positive(raw.get("value"), field=field) * _UNIT_TO_MM[unit], 3), refs, basis, reason


def _default_family(*, role: str, allowed: set[str]) -> str:
    for family in _FAMILY_PREFERENCE[role]:
        if family in allowed:
            return family
    if not allowed:
        raise ValueError("no material families are available")
    return sorted(allowed)[0]


def _default_thickness(role: str) -> float | None:
    if role == "backing_sheet":
        return 3.0
    if role == "worktop_sheet":
        return 36.0
    if role in {"visible_sheet", "internal_sheet"}:
        return 18.0
    return None


def build_structural_assembly_bom(*, input_row: Mapping[str, Any], dimension_graph: Mapping[str, Any], extraction: Mapping[str, Any], allowed_material_families: Sequence[str]) -> dict[str, Any]:
    """Expand bounded assembly topology to auditable material parts.

    All dimensions remain attributed to immutable evidence.  Conventional
    panel thicknesses and hidden carcass members are explicit construction
    assumptions in the returned facts, never source claims.
    """
    payload = input_row.get("input_payload") or {}
    if payload.get("contract_version") != "estimation_input_v4":
        raise ValueError("structural BOM requires estimation_input_v4")
    if dimension_graph.get("contract_version") != "estimation_dimension_graph_v1":
        raise ValueError("structural BOM requires Dimension Graph")
    allowed_refs = _allowed_refs(payload)
    allowed_families = {str(item) for item in allowed_material_families if str(item)}
    document_unit, document_unit_refs, document_unit_reason, document_unit_basis = _resolve_document_unit(
        extraction=extraction, allowed=allowed_refs,
    )
    object_payload = payload.get("object") or {}
    object_quantity = _integer(object_payload.get("quantity") or 1, field="object.quantity", default=1)
    materials: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    assemblies: list[dict[str, Any]] = []
    assumptions: list[str] = []
    requirement_ids: dict[tuple[str, str, str], str] = {}

    if document_unit_reason:
        assumptions.append(f"Document unit: {document_unit_reason}")

    def material_requirement(raw_materials: Mapping[str, Mapping[str, Any]], role: str) -> str:
        raw = raw_materials.get(role) or {}
        if not isinstance(raw, Mapping):
            raw = {}
        family = str(raw.get("family") or "").strip()
        if family not in allowed_families:
            family = _default_family(role=role, allowed=allowed_families)
            assumptions.append(f"Default {role} material family: {family}")
        source_name = str(raw.get("source_name") or f"Assumed {role.replace('_', ' ')}").strip()
        basis = str(raw.get("basis") or "construction_assumption")
        if basis not in {"source_evidence", "construction_assumption"}:
            raise ValueError(f"material role {role} has invalid basis")
        refs = _refs(raw.get("evidence_refs"), allowed=allowed_refs, required=basis == "source_evidence", field=f"material_roles.{role}.evidence_refs")
        if basis == "construction_assumption" and refs:
            raise ValueError(f"material role {role} assumption may not claim source evidence")
        specification = dict(raw.get("specification") or {}) if isinstance(raw.get("specification"), Mapping) else {}
        thickness = specification.get("thickness_mm")
        if role in {"visible_sheet", "internal_sheet", "backing_sheet", "worktop_sheet"}:
            if thickness is None:
                thickness = _default_thickness(role)
                assumptions.append(f"Default {role} thickness: {thickness:g} mm")
            specification["thickness_mm"] = _positive(thickness, field=f"material_roles.{role}.thickness_mm")
        key = (family, source_name, json.dumps(specification, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        existing = requirement_ids.get(key)
        if existing:
            return existing
        requirement_id = f"material-{len(requirement_ids) + 1:03d}"
        requirement_ids[key] = requirement_id
        materials.append({
            "requirement_id": requirement_id, "source_name": source_name, "family": family,
            "specification": specification, "basis": basis, "evidence_refs": refs,
            "quantity": None, "unit": None,
        })
        return requirement_id

    def add_part(*, assembly_id: str, role: str, requirement_id: str, quantity: int, length: float, width: float, refs: list[str], basis: str, reason: str | None) -> None:
        if quantity <= 0 or length <= 0 or width <= 0:
            return
        parts.append({
            "part_id": f"{assembly_id}:{role}:{len(parts) + 1:03d}", "assembly_id": assembly_id,
            "component_role": role, "material_requirement_id": requirement_id,
            "quantity": quantity * object_quantity, "length_mm": round(length, 3), "width_mm": round(width, 3),
            "rotation_allowed": True, "basis": basis, "evidence_refs": refs,
            "assumption_reason": reason,
        })

    seen_assemblies: set[str] = set()
    for raw in extraction.get("assemblies") or []:
        if not isinstance(raw, Mapping):
            continue
        assembly_id = str(raw.get("assembly_id") or "").strip()
        assembly_role = str(raw.get("assembly_role") or "").strip()
        if not assembly_id or assembly_id in seen_assemblies or assembly_role not in _ROLES:
            raise ValueError("assembly requires unique id and supported structural role")
        seen_assemblies.add(assembly_id)
        assembly_refs = _refs(raw.get("evidence_refs"), allowed=allowed_refs, required=True, field=f"{assembly_id}.evidence_refs")
        assembly_quantity = _integer(raw.get("quantity"), field=f"{assembly_id}.quantity", default=1)
        dimensions = raw.get("dimensions") or {}
        if not isinstance(dimensions, Mapping):
            raise ValueError(f"{assembly_id}.dimensions must be an object")
        parsed_dimensions = {
            name: _dimension(
                dimensions.get(name), default_unit=document_unit, allowed=allowed_refs,
                field=f"{assembly_id}.dimensions.{name}",
                # A scale scenario supersedes every model-convention axis unit.
                # Only `unit_basis=explicit_source` remains authoritative inside
                # `_dimension`, so a model cannot silently mix cm and mm.
                force_document_unit=document_unit_basis == "primary_assembly_scale_scenario",
            )
            for name in ("width", "height", "depth")
            if dimensions.get(name) is not None
        }
        required_dimensions = {
            "box_carcass": {"width", "height", "depth"}, "drawer_bank": {"width", "height", "depth"},
            "shelf_stack": {"width", "height", "depth"}, "table": {"width", "depth"},
            "countertop": {"width", "depth"}, "vertical_panel": {"width", "height"},
            "facade_set": {"width", "height"},
        }[assembly_role]
        if not required_dimensions.issubset(parsed_dimensions):
            raise ValueError(f"{assembly_id} lacks dimensions required by {assembly_role}")
        material_roles = {
            str(item.get("role") or ""): item
            for item in raw.get("material_roles") or []
            if isinstance(item, Mapping) and str(item.get("role") or "") in _MATERIAL_ROLES
        }
        counts = raw.get("counts") or {}
        if not isinstance(counts, Mapping):
            raise ValueError(f"{assembly_id}.counts must be an object")
        dimensions_refs = list(dict.fromkeys(ref for value in parsed_dimensions.values() for ref in value[1])) or assembly_refs
        width = parsed_dimensions.get("width", (0, [], "", None))[0]
        height = parsed_dimensions.get("height", (0, [], "", None))[0]
        depth = parsed_dimensions.get("depth", (0, [], "", None))[0]
        dimension_basis = "source" if all(value[2] == "source" for value in parsed_dimensions.values()) else "derived"
        dimension_reason = next((value[3] for value in parsed_dimensions.values() if value[3]), None)
        assemblies.append({
            "assembly_id": assembly_id, "assembly_role": assembly_role, "quantity": assembly_quantity,
            "evidence_refs": assembly_refs, "dimension_refs": dimensions_refs,
        })
        visible = None
        internal = None
        backing = None
        internal_thickness = 0.0
        facade_count = _integer(counts.get("facades"), field=f"{assembly_id}.counts.facades", default=0)
        if assembly_role in {"drawer_bank", "vertical_panel", "facade_set"} or facade_count:
            visible = material_requirement(material_roles, "visible_sheet")
        if assembly_role in {"box_carcass", "drawer_bank", "shelf_stack"}:
            internal = material_requirement(material_roles, "internal_sheet")
            backing = material_requirement(material_roles, "backing_sheet")
            internal_thickness = float(next(
                item["specification"]["thickness_mm"] for item in materials
                if item["requirement_id"] == internal
            ))

        def panel(role: str, requirement_id: str, count: int, length: float, panel_width: float) -> None:
            add_part(assembly_id=assembly_id, role=role, requirement_id=requirement_id,
                     quantity=count * assembly_quantity, length=length, width=panel_width,
                     refs=dimensions_refs, basis="derived" if dimension_basis == "source" else dimension_basis,
                     reason=dimension_reason or "Conventional structural panel derived from assembly dimensions.")

        if assembly_role in {"box_carcass", "drawer_bank", "shelf_stack"}:
            assert internal is not None and backing is not None
            panel("carcass_side", internal, 2, height, depth)
            panel("carcass_top_bottom", internal, 2, width, depth)
            panel("carcass_back", backing, 1, width, height)
            shelf_count = _integer(counts.get("shelves"), field=f"{assembly_id}.counts.shelves", default=0)
            panel("shelf", internal, shelf_count, max(width - 2 * internal_thickness, 1), depth)
        if assembly_role == "drawer_bank":
            assert visible is not None
            drawer_count = _integer(counts.get("drawers"), field=f"{assembly_id}.counts.drawers", default=1)
            drawer_width = max(width / drawer_count, 1)
            drawer_height = max(height / drawer_count, 1)
            panel("drawer_front", visible, drawer_count, drawer_width, drawer_height)
            panel("drawer_bottom", internal, drawer_count, max(drawer_width - 2 * internal_thickness, 1), max(depth - internal_thickness, 1))
            panel("drawer_side", internal, drawer_count * 2, max(depth - internal_thickness, 1), max(drawer_height - 2 * internal_thickness, 1))
            panel("drawer_back", internal, drawer_count, max(drawer_width - 2 * internal_thickness, 1), max(drawer_height - 2 * internal_thickness, 1))
            if "drawer_slide" in material_roles:
                requirement_id = material_requirement(material_roles, "drawer_slide")
                material = next(item for item in materials if item["requirement_id"] == requirement_id)
                material["quantity"] = (material.get("quantity") or 0) + drawer_count * assembly_quantity * object_quantity
                material["unit"] = "piece"
        elif assembly_role == "box_carcass" and facade_count:
            assert visible is not None
            panel("facade", visible, facade_count, width / facade_count, height)
        elif assembly_role == "vertical_panel":
            assert visible is not None
            panel("vertical_panel", visible, 1, width, height)
        elif assembly_role == "facade_set":
            assert visible is not None
            count = facade_count or 1
            panel("facade", visible, count, width / count, height)
        elif assembly_role in {"table", "countertop"}:
            worktop = material_requirement(material_roles, "worktop_sheet") if "worktop_sheet" in material_roles else material_requirement(material_roles, "visible_sheet")
            top_count = _integer(counts.get("top_layers"), field=f"{assembly_id}.counts.top_layers", default=1)
            panel("top", worktop, top_count, width, depth)
        if assembly_role == "table" and "leg" in material_roles:
            leg_count = _integer(counts.get("legs"), field=f"{assembly_id}.counts.legs", default=2)
            requirement_id = material_requirement(material_roles, "leg")
            material = next(item for item in materials if item["requirement_id"] == requirement_id)
            material["quantity"] = (material.get("quantity") or 0) + leg_count * assembly_quantity * object_quantity
            material["unit"] = "piece"
        if "finish" in material_roles:
            requirement_id = material_requirement(material_roles, "finish")
            material = next(item for item in materials if item["requirement_id"] == requirement_id)
            material["quantity"] = (material.get("quantity") or 0) + assembly_quantity * object_quantity
            material["unit"] = "piece"

    for raw in extraction.get("secondary_items") or []:
        if not isinstance(raw, Mapping):
            continue
        role = str(raw.get("role") or "")
        if role not in {"drawer_slide", "leg"}:
            raise ValueError("secondary item role is unsupported")
        count = _integer(raw.get("quantity"), field=f"secondary_items.{role}.quantity")
        refs = _refs(raw.get("evidence_refs"), allowed=allowed_refs, required=True, field=f"secondary_items.{role}.evidence_refs")
        material = raw.get("material")
        if not isinstance(material, Mapping):
            raise ValueError("secondary item requires material")
        requirement_id = material_requirement({role: material}, role)
        target = next(item for item in materials if item["requirement_id"] == requirement_id)
        target["quantity"] = (target.get("quantity") or 0) + count * object_quantity
        target["unit"] = "piece"

    if not parts and not any(item.get("quantity") for item in materials):
        raise ValueError("structural BOM has no material demand")
    preview_refs = sorted(ref for ref in allowed_refs if ref.startswith("storage://"))
    return {
        "contract_version": ASSEMBLY_BOM_V1,
        "composition_version": "structural_bom_v4_15",
        "input_id": str(input_row.get("input_id") or ""), "object_input_revision": int(input_row.get("object_input_revision") or 1),
        "run_id": str(payload.get("run_id") or ""), "company_id": str(payload.get("company_id") or ""),
        "object_id": str(object_payload.get("object_id") or ""), "object_name": str(object_payload.get("object_name") or ""),
        "quantity": object_quantity, "status": "ready", "dimension_graph_contract": str(dimension_graph["contract_version"]),
        "document_unit": {
            "unit": document_unit, "evidence_refs": document_unit_refs,
            "resolution": document_unit_basis,
        },
        "assemblies": assemblies, "materials": materials, "parts": parts,
        "assumptions": list(dict.fromkeys(assumptions)),
        "omissions": [str(item) for item in extraction.get("omissions") or [] if str(item).strip()],
        "primary_preview_ref": preview_refs[0],
    }
