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
    "finish", "drawer_slide", "hinge", "gas_lift", "leg",
}
_FAMILY_PREFERENCE = {
    "visible_sheet": ("mdf_hdf", "melamine_faced_particleboard", "particleboard"),
    "internal_sheet": ("melamine_faced_particleboard", "particleboard", "mdf_hdf"),
    "backing_sheet": ("fibreboard_hardboard", "mdf_hdf", "particleboard"),
    "worktop_sheet": ("mdf_hdf", "melamine_faced_particleboard", "particleboard"),
    "finish": ("paint_lacquer_stain",),
    "drawer_slide": ("hardware_drawer_slide",),
    "hinge": ("hardware_hinge",),
    "gas_lift": ("hardware_lift_system",),
    "leg": ("purchased_fabricated_component",),
}
_CONSTRUCTION_MATERIAL_NAMES = {
    "mdf_hdf": "MDF",
    "melamine_faced_particleboard": "LDSP",
    "particleboard": "Particleboard",
    "fibreboard_hardboard": "Hardboard",
    "timber_solid_wood_panel": "Solid wood panel",
    "paint_lacquer_stain": "Paint finish",
    "hardware_drawer_slide": "Drawer slide",
    "hardware_hinge": "Cabinet hinge",
    "hardware_lift_system": "Gas lift",
    "purchased_fabricated_component": "Furniture leg",
    "metal_round_bar_rod_wire": "Furniture leg",
}
_ROLE_WORDS = frozenset({
    "cabinet", "carcass", "facade", "table", "seat", "worktop", "countertop",
    "drawer", "panel", "backing", "sheet", "leg",
})
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


def _optional_count(value: Any, *, field: str, default: int, zero_is_meaningful: bool) -> int:
    """Read an optional model count without turning an explicit zero into a failure."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result < 0 or int(result) != result:
        return default
    count = int(result)
    if count == 0 and not zero_is_meaningful:
        return default
    return count


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


def _unit_context(raw: Any, *, allowed: set[str]) -> tuple[str, list[str], str | None, list[str]]:
    if not isinstance(raw, Mapping):
        raise ValueError("document_unit is required")
    unit = str(raw.get("unit") or "").casefold()
    if unit not in _UNIT_TO_MM:
        raise ValueError("document_unit.unit must be mm, cm or m")
    basis = str(raw.get("basis") or "")
    reason = str(raw.get("assumption_reason") or "").strip() or None
    if basis not in {"explicit_source", "document_convention_assumption"}:
        raise ValueError("document_unit.basis is invalid")
    raw_refs = raw.get("evidence_refs")
    normalizations: list[str] = []
    if basis == "document_convention_assumption":
        # The assumption itself is the provenance. A model may redundantly
        # attach refs, but retaining them would falsely upgrade it to source
        # evidence. Discard the metadata contradiction and continue.
        refs = []
        if raw_refs not in (None, []):
            normalizations.append("document_unit_assumption_refs_discarded")
    else:
        refs = _refs(raw_refs, allowed=allowed, required=True, field="document_unit.evidence_refs")
    if basis == "document_convention_assumption" and not reason:
        raise ValueError("document_unit assumption requires a reason")
    return unit, refs, reason, normalizations


def _resolve_document_unit(
    *, extraction: Mapping[str, Any], allowed: set[str], dimension_scale_gate: Mapping[str, Any] | None = None,
) -> tuple[str, list[str], str | None, str, list[str]]:
    """Use the visual interpretation's one document-wide unit decision.

    Unit inference belongs to the visual stage, which can read dimension lines
    in the context of the whole drawing. The deterministic composer only
    enforces that a cited source unit remains explicit and converts the chosen
    document convention consistently.
    """
    unit, refs, reason, normalizations = _unit_context(extraction.get("document_unit"), allowed=allowed)
    raw_context = extraction.get("document_unit") or {}
    if str(raw_context.get("basis") or "") == "explicit_source":
        return unit, refs, reason, "explicit_source", normalizations
    decision = (dimension_scale_gate or {}).get("decision")
    if isinstance(decision, Mapping) and str(decision.get("required_unit") or "") in _UNIT_TO_MM:
        return (
            str(decision["required_unit"]), [], str(decision.get("reason") or "").strip() or None,
            "ocr_scale_guard", normalizations,
        )
    return unit, refs, reason, "model_document_convention", normalizations


def _expected_region_ids(payload: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for page in ((payload.get("object") or {}).get("evidence_pages") or []):
        if not isinstance(page, Mapping):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        for index, region in enumerate(page.get("regions") or [], start=1):
            if isinstance(region, Mapping):
                result.add(f"p{page_number}-region-{index:03d}")
    return result


def _audit_coverage(
    *, extraction: Mapping[str, Any], expected_region_ids: set[str], assembly_ids: set[str], secondary_ids: set[str],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Return valid ledger entries plus a non-blocking completeness audit.

    Coverage protects against unnoticed omissions, but it is not source
    evidence and cannot be allowed to suppress an otherwise usable estimate.
    A missing, duplicated, or unsupported entry remains diagnosable in facts.
    """
    if not expected_region_ids:
        return [], {
            "status": "not_applicable", "expected_region_count": 0,
            "covered_region_ids": [], "missing_region_ids": [], "invalid_entry_count": 0,
        }
    coverage = extraction.get("coverage")
    coverage_items = coverage if isinstance(coverage, list) else []
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    invalid_entry_count = 0
    allowed_exclusions = {"unshown_fasteners", "minor_unmeasured_trim", "reference_only", "non_material_annotation"}
    for raw in coverage_items:
        if not isinstance(raw, Mapping):
            invalid_entry_count += 1
            continue
        region_id = str(raw.get("region_id") or "")
        disposition = str(raw.get("disposition") or "")
        target_id = str(raw.get("target_id") or "")
        reason = str(raw.get("reason") or "")
        if not region_id or region_id in seen or region_id not in expected_region_ids:
            invalid_entry_count += 1
            continue
        seen.add(region_id)
        if disposition == "assembly" and target_id in assembly_ids:
            pass
        elif disposition == "secondary_item" and target_id in secondary_ids:
            pass
        elif disposition == "excluded" and reason in allowed_exclusions:
            target_id = ""
        else:
            invalid_entry_count += 1
            continue
        result.append({"region_id": region_id, "disposition": disposition, "target_id": target_id, "reason": reason})
    covered_region_ids = {item["region_id"] for item in result}
    missing_region_ids = sorted(expected_region_ids - covered_region_ids)
    if not coverage_items:
        status = "not_provided"
    elif not missing_region_ids and invalid_entry_count == 0:
        status = "complete"
    else:
        status = "partial"
    return result, {
        "status": status,
        "expected_region_count": len(expected_region_ids),
        "covered_region_ids": sorted(covered_region_ids),
        "missing_region_ids": missing_region_ids,
        "invalid_entry_count": invalid_entry_count,
    }


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


def _construction_material_name(*, raw_name: object, family: str, role: str) -> str:
    """Keep assembly labels out of the material resolver and customer UI."""
    name = " ".join(str(raw_name or "").split()).strip()
    words = {word.strip(" ,./-_").casefold() for word in name.split()}
    if name and not (words & _ROLE_WORDS):
        return name
    if role == "leg":
        return "Furniture leg"
    return _CONSTRUCTION_MATERIAL_NAMES.get(family, "Material")


def _required_dimensions(assembly_role: str) -> set[str]:
    return {
        "box_carcass": {"width", "height", "depth"},
        "drawer_bank": {"width", "height", "depth"},
        "shelf_stack": {"width", "height", "depth"},
        "table": {"width", "depth"},
        "countertop": {"width", "depth"},
        "vertical_panel": {"width", "height"},
        "facade_set": {"width", "height"},
    }[assembly_role]


def _recoverable_assemblies(extraction: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Discard only invalid assembly identities, never incomplete geometry.

    A visual model can recognise several large assemblies but lack one required
    dimension for a secondary one. That is an auditable omission, not a reason
    to throw away every other sourced material demand in the estimate.
    """
    usable: list[dict[str, Any]] = []
    omissions: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(extraction.get("assemblies") or [], start=1):
        if not isinstance(raw, Mapping):
            omissions.append({"kind": "assembly", "identifier": f"assembly-{index}", "reason_code": "not_an_object"})
            continue
        assembly_id = str(raw.get("assembly_id") or "").strip()
        role = str(raw.get("assembly_role") or "").strip()
        if not assembly_id or assembly_id in seen or role not in _ROLES:
            omissions.append({"kind": "assembly", "identifier": assembly_id or f"assembly-{index}", "reason_code": "invalid_identity_or_role"})
            continue
        seen.add(assembly_id)
        normalized = dict(raw)
        if not isinstance(raw.get("dimensions"), Mapping):
            normalized["dimensions"] = {}
            omissions.append({"kind": "assembly", "identifier": assembly_id, "reason_code": "dimensions_defaulted"})
        if not isinstance(raw.get("counts"), Mapping):
            normalized["counts"] = {}
            omissions.append({"kind": "assembly", "identifier": assembly_id, "reason_code": "invalid_counts_defaulted"})
        usable.append(normalized)
    return usable, omissions


_DIMENSION_DEFAULTS_MM = {"width": 600.0, "height": 720.0, "depth": 600.0}
_FRONT_KINDS = {"drawer_front", "hinged_facade", "lift_up_facade"}
_FRONT_ARRANGEMENTS = {"stacked", "side_by_side"}


def _front_groups(raw: Mapping[str, Any], *, assembly_role: str, counts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalise visual front topology, with a backward-compatible fallback.

    The visual stage identifies fronts.  This function deliberately does not
    select hardware or a shop-fitting system, it only gives the deterministic
    composer the topology needed for approximate quantities.
    """
    groups: list[dict[str, Any]] = []
    for index, candidate in enumerate(raw.get("front_groups") or [], start=1):
        if not isinstance(candidate, Mapping):
            continue
        kind = str(candidate.get("front_kind") or "")
        if kind not in _FRONT_KINDS:
            continue
        quantity = _optional_count(
            candidate.get("quantity"), field=f"front_groups.{index}.quantity", default=1, zero_is_meaningful=True,
        )
        if quantity <= 0:
            continue
        arrangement = str(candidate.get("arrangement") or "stacked")
        if arrangement not in _FRONT_ARRANGEMENTS:
            arrangement = "stacked"
        groups.append({"front_kind": kind, "quantity": quantity, "arrangement": arrangement})
    if groups:
        return groups
    drawer_count = _optional_count(counts.get("drawers"), field="counts.drawers", default=0, zero_is_meaningful=True)
    facade_count = _optional_count(counts.get("facades"), field="counts.facades", default=0, zero_is_meaningful=True)
    if assembly_role == "drawer_bank" and drawer_count:
        return [{"front_kind": "drawer_front", "quantity": drawer_count, "arrangement": "stacked"}]
    if facade_count:
        return [{"front_kind": "hinged_facade", "quantity": facade_count, "arrangement": "side_by_side"}]
    return []


def _front_size(*, width: float, height: float, group: Mapping[str, Any]) -> tuple[float, float]:
    quantity = int(group["quantity"])
    if group["arrangement"] == "side_by_side":
        return max(width / quantity, 1), height
    return width, max(height / quantity, 1)


def _slide_depth_mm(cabinet_depth_mm: float) -> int:
    """Use the owner-approved depth minus 100 mm, rounded down by 100 mm."""
    return max(100, int((max(cabinet_depth_mm - 100, 100)) // 100) * 100)


def _hinges_per_facade(height_mm: float) -> int:
    if height_mm > 2000:
        return 4
    if height_mm > 600:
        return 3
    return 2


def _valid_model_refs(value: object, *, allowed: set[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item in allowed]


def _normalize_model_references(
    extraction: Mapping[str, Any], *, allowed: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Downgrade unsupported model citations to explicit assumptions.

    Evidence references are an integrity boundary, not a calculation gate. A
    model may echo a page label or Dimension Graph id rather than an immutable
    ref. Keep the estimate approximate, but never retain that as a false source
    claim or reject otherwise usable assemblies.
    """
    normalized = dict(extraction)
    markers: list[str] = []
    page_refs = sorted(ref for ref in allowed if ref.startswith("storage://"))

    document_unit = extraction.get("document_unit")
    if isinstance(document_unit, Mapping):
        unit = dict(document_unit)
        basis = str(unit.get("basis") or "")
        refs = _valid_model_refs(unit.get("evidence_refs"), allowed=allowed)
        if basis == "explicit_source" and not refs:
            unit["basis"] = "document_convention_assumption"
            unit["evidence_refs"] = []
            unit["assumption_reason"] = "The supplied unit citation was not an immutable evidence reference."
            markers.append("document_unit_invalid_refs_downgraded")
        elif basis == "document_convention_assumption" and unit.get("evidence_refs") not in (None, []):
            unit["evidence_refs"] = []
            markers.append("document_unit_assumption_refs_discarded")
        normalized["document_unit"] = unit

    assemblies: list[Any] = []
    for raw in extraction.get("assemblies") or []:
        if not isinstance(raw, Mapping):
            assemblies.append(raw)
            continue
        assembly = dict(raw)
        refs = _valid_model_refs(assembly.get("evidence_refs"), allowed=allowed)
        if not refs and page_refs:
            assembly["evidence_refs"] = [page_refs[0]]
            markers.append("assembly_invalid_refs_replaced_with_page_artifact")
        else:
            assembly["evidence_refs"] = refs
        dimensions = assembly.get("dimensions")
        if isinstance(dimensions, Mapping):
            normalized_dimensions: dict[str, Any] = {}
            for axis, raw_dimension in dimensions.items():
                if not isinstance(raw_dimension, Mapping):
                    normalized_dimensions[str(axis)] = raw_dimension
                    continue
                dimension = dict(raw_dimension)
                basis = str(dimension.get("basis") or "")
                refs = _valid_model_refs(dimension.get("evidence_refs"), allowed=allowed)
                if basis in {"source", "derived"} and not refs:
                    dimension["basis"] = "assumption"
                    dimension["evidence_refs"] = []
                    dimension["assumption_reason"] = "The supplied dimension citation was not an immutable evidence reference."
                    markers.append("dimension_invalid_refs_downgraded_to_assumption")
                elif basis == "assumption" and dimension.get("evidence_refs") not in (None, []):
                    dimension["evidence_refs"] = []
                    markers.append("dimension_assumption_refs_discarded")
                else:
                    dimension["evidence_refs"] = refs
                normalized_dimensions[str(axis)] = dimension
            assembly["dimensions"] = normalized_dimensions
        material_roles: list[Any] = []
        for raw_material in assembly.get("material_roles") or []:
            if not isinstance(raw_material, Mapping):
                material_roles.append(raw_material)
                continue
            material = dict(raw_material)
            basis = str(material.get("basis") or "construction_assumption")
            refs = _valid_model_refs(material.get("evidence_refs"), allowed=allowed)
            if basis == "source_evidence" and not refs:
                material["basis"] = "construction_assumption"
                material["evidence_refs"] = []
                markers.append("material_invalid_refs_downgraded_to_assumption")
            elif basis == "construction_assumption":
                if material.get("evidence_refs") not in (None, []):
                    markers.append("material_assumption_refs_discarded")
                material["evidence_refs"] = []
            else:
                material["evidence_refs"] = refs
            material_roles.append(material)
        assembly["material_roles"] = material_roles
        assemblies.append(assembly)
    normalized["assemblies"] = assemblies
    return normalized, list(dict.fromkeys(markers))


def build_structural_assembly_bom(
    *, input_row: Mapping[str, Any], dimension_graph: Mapping[str, Any], extraction: Mapping[str, Any],
    allowed_material_families: Sequence[str], dimension_scale_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
    extraction, reference_normalizations = _normalize_model_references(extraction, allowed=allowed_refs)
    allowed_families = {str(item) for item in allowed_material_families if str(item)}
    document_unit, document_unit_refs, document_unit_reason, document_unit_basis, normalizations = _resolve_document_unit(
        extraction=extraction, allowed=allowed_refs, dimension_scale_gate=dimension_scale_gate,
    )
    normalizations = [*reference_normalizations, *normalizations]
    object_payload = payload.get("object") or {}
    object_quantity = _integer(object_payload.get("quantity") or 1, field="object.quantity", default=1)
    materials: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    assemblies: list[dict[str, Any]] = []
    assumptions: list[str] = []
    requirement_ids: dict[tuple[str, str, str], str] = {}
    usable_assemblies, structural_omissions = _recoverable_assemblies(extraction)

    # A drawing often states one cabinet depth once and leaves its connected
    # peers unlabelled.  We only copy a peer value when it is the sole value
    # for that axis in this object.  Otherwise the construction default below
    # is safer than pretending unrelated cabinets share a depth.
    peer_dimensions: dict[str, list[tuple[float, list[str]]]] = {"width": [], "height": [], "depth": []}
    for candidate in usable_assemblies:
        raw_dimensions = candidate.get("dimensions") or {}
        if not isinstance(raw_dimensions, Mapping):
            continue
        for axis in peer_dimensions:
            if raw_dimensions.get(axis) is None:
                continue
            try:
                value, refs, _basis, _reason = _dimension(
                    raw_dimensions[axis], default_unit=document_unit, allowed=allowed_refs,
                    field=f"peer.dimensions.{axis}", force_document_unit=False,
                )
            except ValueError:
                continue
            if refs:
                peer_dimensions[axis].append((value, refs))

    if document_unit_reason:
        assumptions.append(f"Document unit: {document_unit_reason}")

    def material_requirement(
        raw_materials: Mapping[str, Mapping[str, Any]], role: str,
        *, extra_specification: Mapping[str, Any] | None = None,
    ) -> str:
        raw = raw_materials.get(role) or {}
        if not isinstance(raw, Mapping):
            raw = {}
        family = str(raw.get("family") or "").strip()
        if family not in allowed_families:
            family = _default_family(role=role, allowed=allowed_families)
            assumptions.append(f"Default {role} material family: {family}")
        basis = str(raw.get("basis") or "construction_assumption")
        if basis not in {"source_evidence", "construction_assumption"}:
            raise ValueError(f"material role {role} has invalid basis")
        source_name = str(raw.get("source_name") or "").strip()
        if basis == "construction_assumption":
            source_name = _construction_material_name(raw_name=source_name, family=family, role=role)
        elif not source_name:
            source_name = _CONSTRUCTION_MATERIAL_NAMES.get(family, "Material")
        refs = _refs(raw.get("evidence_refs"), allowed=allowed_refs, required=basis == "source_evidence", field=f"material_roles.{role}.evidence_refs")
        if basis == "construction_assumption" and refs:
            raise ValueError(f"material role {role} assumption may not claim source evidence")
        specification = dict(raw.get("specification") or {}) if isinstance(raw.get("specification"), Mapping) else {}
        if extra_specification:
            specification.update(dict(extra_specification))
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

    def add_hardware(*, raw_materials: Mapping[str, Mapping[str, Any]], role: str, quantity: int, unit: str, extra_specification: Mapping[str, Any] | None = None) -> None:
        if quantity <= 0:
            return
        # Narrow test fixtures may intentionally omit the hardware family.
        # Production catalog context contains these global families.  Do not
        # substitute sheet material for a fitting merely to manufacture demand.
        if not any(family in allowed_families for family in _FAMILY_PREFERENCE[role]):
            assumptions.append(f"No enabled family for {role}; hardware demand retained in topology only.")
            return
        requirement_id = material_requirement(raw_materials, role, extra_specification=extra_specification)
        material = next(item for item in materials if item["requirement_id"] == requirement_id)
        material["quantity"] = (material.get("quantity") or 0) + quantity * object_quantity
        material["unit"] = unit

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
    for raw in usable_assemblies:
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
        required_dimensions = _required_dimensions(assembly_role)
        parsed_dimensions: dict[str, tuple[float, list[str], str, str | None]] = {}
        for name in ("width", "height", "depth"):
            raw_dimension = dimensions.get(name)
            if raw_dimension is not None:
                try:
                    parsed_dimensions[name] = _dimension(
                        raw_dimension, default_unit=document_unit, allowed=allowed_refs,
                        field=f"{assembly_id}.dimensions.{name}", force_document_unit=False,
                    )
                    continue
                except ValueError:
                    pass
            if name not in required_dimensions:
                continue
            known_values = peer_dimensions[name]
            unique_values = {round(value, 3) for value, _refs_value in known_values}
            if len(unique_values) == 1 and known_values:
                peer_value, peer_refs = known_values[0]
                parsed_dimensions[name] = (
                    peer_value, peer_refs, "derived",
                    f"Derived from the only source-supported {name} shared by this object's cabinet blocks.",
                )
            else:
                parsed_dimensions[name] = (
                    _DIMENSION_DEFAULTS_MM[name], [], "assumption",
                    f"Default cabinet {name}: {_DIMENSION_DEFAULTS_MM[name]:g} mm because the drawing does not resolve it.",
                )
            assumptions.append(f"{assembly_id} {name}: {parsed_dimensions[name][3]}")
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
        front_groups = _front_groups(raw, assembly_role=assembly_role, counts=counts)
        hardware_topology: list[dict[str, Any]] = []
        for group in front_groups:
            quantity = int(group["quantity"])
            _front_width, front_height = _front_size(width=width, height=height, group=group)
            if group["front_kind"] == "drawer_front":
                hardware_topology.append({
                    "role": "drawer_slide", "quantity": quantity, "purchase_unit": "set",
                    "depth_mm": _slide_depth_mm(depth),
                })
            elif group["front_kind"] == "hinged_facade":
                hardware_topology.append({
                    "role": "hinge", "quantity": quantity * _hinges_per_facade(front_height), "purchase_unit": "piece",
                })
            elif group["front_kind"] == "lift_up_facade":
                hardware_topology.append({"role": "gas_lift", "quantity": quantity, "purchase_unit": "set"})
        assemblies.append({
            "assembly_id": assembly_id, "assembly_role": assembly_role, "quantity": assembly_quantity,
            "evidence_refs": assembly_refs, "dimension_refs": dimensions_refs,
            "front_groups": front_groups, "hardware": hardware_topology,
        })
        visible = None
        internal = None
        backing = None
        internal_thickness = 0.0
        facade_count = sum(group["quantity"] for group in front_groups if group["front_kind"] != "drawer_front")
        exposure = raw.get("exposure") if isinstance(raw.get("exposure"), Mapping) else {}
        exposed_sides = {side for side in ("left", "right") if bool(exposure.get(side))}
        if assembly_role in {"drawer_bank", "vertical_panel", "facade_set"} or facade_count or exposed_sides:
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
            for side in ("left", "right"):
                if side in exposed_sides:
                    assert visible is not None
                    panel("carcass_side_exposed", visible, 1, height, depth)
                else:
                    panel("carcass_side", internal, 1, height, depth)
            panel("carcass_top_bottom", internal, 2, width, depth)
            panel("carcass_back", backing, 1, width, height)
            shelf_count = _optional_count(
                counts.get("shelves"), field=f"{assembly_id}.counts.shelves", default=0, zero_is_meaningful=True,
            )
            panel("shelf", internal, shelf_count, max(width - 2 * internal_thickness, 1), depth)
        if assembly_role == "drawer_bank":
            assert visible is not None
            drawer_groups = [group for group in front_groups if group["front_kind"] == "drawer_front"]
            if not drawer_groups:
                drawer_groups = [{"front_kind": "drawer_front", "quantity": 1, "arrangement": "stacked"}]
            for group in drawer_groups:
                drawer_width, drawer_height = _front_size(width=width, height=height, group=group)
                drawer_count = int(group["quantity"])
                panel("drawer_front", visible, drawer_count, drawer_width, drawer_height)
                panel("drawer_bottom", internal, drawer_count, max(drawer_width - 2 * internal_thickness, 1), max(depth - internal_thickness, 1))
                panel("drawer_side", internal, drawer_count * 2, max(depth - internal_thickness, 1), max(drawer_height - 2 * internal_thickness, 1))
                panel("drawer_back", internal, drawer_count, max(drawer_width - 2 * internal_thickness, 1), max(drawer_height - 2 * internal_thickness, 1))
                add_hardware(
                    raw_materials=material_roles, role="drawer_slide", quantity=drawer_count * assembly_quantity,
                    unit="set", extra_specification={"depth_mm": _slide_depth_mm(depth)},
                )
        elif assembly_role == "box_carcass" and facade_count:
            assert visible is not None
            for group in front_groups:
                if group["front_kind"] == "drawer_front":
                    continue
                front_width, front_height = _front_size(width=width, height=height, group=group)
                panel("facade", visible, int(group["quantity"]), front_width, front_height)
                if group["front_kind"] == "hinged_facade":
                    add_hardware(
                        raw_materials=material_roles, role="hinge",
                        quantity=int(group["quantity"]) * _hinges_per_facade(front_height) * assembly_quantity,
                        unit="piece",
                    )
                elif group["front_kind"] == "lift_up_facade":
                    add_hardware(
                        raw_materials=material_roles, role="gas_lift",
                        quantity=int(group["quantity"]) * assembly_quantity, unit="set",
                    )
        elif assembly_role == "vertical_panel":
            assert visible is not None
            panel("vertical_panel", visible, 1, width, height)
        elif assembly_role == "facade_set":
            assert visible is not None
            groups = front_groups or [{"front_kind": "hinged_facade", "quantity": 1, "arrangement": "side_by_side"}]
            for group in groups:
                front_width, front_height = _front_size(width=width, height=height, group=group)
                panel("facade", visible, int(group["quantity"]), front_width, front_height)
                if group["front_kind"] == "hinged_facade":
                    add_hardware(
                        raw_materials=material_roles, role="hinge",
                        quantity=int(group["quantity"]) * _hinges_per_facade(front_height) * assembly_quantity,
                        unit="piece",
                    )
                elif group["front_kind"] == "lift_up_facade":
                    add_hardware(
                        raw_materials=material_roles, role="gas_lift",
                        quantity=int(group["quantity"]) * assembly_quantity, unit="set",
                    )
        elif assembly_role in {"table", "countertop"}:
            worktop = material_requirement(material_roles, "worktop_sheet") if "worktop_sheet" in material_roles else material_requirement(material_roles, "visible_sheet")
            top_count = _optional_count(
                counts.get("top_layers"), field=f"{assembly_id}.counts.top_layers", default=1, zero_is_meaningful=False,
            )
            panel("top", worktop, top_count, width, depth)
        if assembly_role == "table" and "leg" in material_roles:
            leg_count = _optional_count(
                counts.get("legs"), field=f"{assembly_id}.counts.legs", default=2, zero_is_meaningful=False,
            )
            add_hardware(raw_materials=material_roles, role="leg", quantity=leg_count * assembly_quantity, unit="piece")
        if "finish" in material_roles:
            requirement_id = material_requirement(material_roles, "finish")
            material = next(item for item in materials if item["requirement_id"] == requirement_id)
            material["quantity"] = (material.get("quantity") or 0) + assembly_quantity * object_quantity
            material["unit"] = "piece"

    secondary_ids: set[str] = set()
    for index, raw in enumerate(extraction.get("secondary_items") or [], start=1):
        if not isinstance(raw, Mapping):
            structural_omissions.append({"kind": "secondary_item", "identifier": f"secondary-{index}", "reason_code": "not_an_object"})
            continue
        secondary_id = str(raw.get("secondary_id") or f"secondary-{index}")
        if secondary_id in secondary_ids:
            structural_omissions.append({"kind": "secondary_item", "identifier": secondary_id, "reason_code": "duplicate_identity"})
            continue
        secondary_ids.add(secondary_id)
        role = str(raw.get("role") or "")
        if role not in {"drawer_slide", "hinge", "gas_lift", "leg"}:
            structural_omissions.append({"kind": "secondary_item", "identifier": secondary_id, "reason_code": "unsupported_role"})
            continue
        try:
            count = _integer(raw.get("quantity"), field=f"secondary_items.{role}.quantity")
            _refs(raw.get("evidence_refs"), allowed=allowed_refs, required=True, field=f"secondary_items.{role}.evidence_refs")
        except ValueError:
            structural_omissions.append({"kind": "secondary_item", "identifier": secondary_id, "reason_code": "invalid_quantity_or_evidence"})
            continue
        material = raw.get("material")
        if not isinstance(material, Mapping):
            structural_omissions.append({"kind": "secondary_item", "identifier": secondary_id, "reason_code": "missing_material"})
            continue
        unit = "piece" if role in {"hinge", "leg"} else "set"
        add_hardware(raw_materials={role: material}, role=role, quantity=count, unit=unit)

    if not parts and not any(item.get("quantity") for item in materials):
        raise ValueError("structural BOM has no material demand")
    coverage, coverage_audit = _audit_coverage(
        extraction=extraction, expected_region_ids=_expected_region_ids(payload),
        assembly_ids=seen_assemblies, secondary_ids=secondary_ids,
    )
    preview_refs = sorted(ref for ref in allowed_refs if ref.startswith("storage://"))
    return {
        "contract_version": ASSEMBLY_BOM_V1,
        "composition_version": "structural_bom_v5_2",
        "input_id": str(input_row.get("input_id") or ""), "object_input_revision": int(input_row.get("object_input_revision") or 1),
        "run_id": str(payload.get("run_id") or ""), "company_id": str(payload.get("company_id") or ""),
        "object_id": str(object_payload.get("object_id") or ""), "object_name": str(object_payload.get("object_name") or ""),
        "quantity": object_quantity, "status": "ready", "dimension_graph_contract": str(dimension_graph["contract_version"]),
        "document_unit": {
            "unit": document_unit, "evidence_refs": document_unit_refs,
            "resolution": document_unit_basis,
            **({"scale_gate": dict((dimension_scale_gate or {}).get("decision") or {})}
               if document_unit_basis == "ocr_scale_guard" else {}),
        },
        "assemblies": assemblies, "materials": materials, "parts": parts,
        "assumptions": list(dict.fromkeys(assumptions)),
        "normalizations": normalizations,
        "structural_omissions": structural_omissions,
        "omissions": [str(item) for item in extraction.get("omissions") or [] if str(item).strip()],
        "coverage": coverage, "coverage_audit": coverage_audit,
        "primary_preview_ref": preview_refs[0],
    }
