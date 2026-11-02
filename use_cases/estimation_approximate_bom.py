"""Versioned, deterministic approximate BOM recipes.

These recipes make a material estimate from a validated construction brief.
They intentionally do not model gaps, machining, labour or price.  Every
rectangle is a recipe result, never a fact claimed from the source document.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from use_cases.estimation_object_to_estimate_contract import validate_object_to_estimate_v1


APPROXIMATE_BOM_V1 = "estimation_approximate_bom_v1"
WARDROBE_CARCASS_RECIPE_V1 = "wardrobe_carcass_v1"


def _recipe_role(
    *, role: str, defaults: Mapping[str, Mapping[str, Any]], source_roles: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """Return role material and whether it is a declared construction default."""
    if role in source_roles:
        return dict(source_roles[role]), False
    return dict(defaults[role]), True


def _auxiliary_requirement_id(
    *, role: str, role_material: Mapping[str, Any], used_ids: set[str], ordinal: int,
) -> str:
    """Keep every visible fitting separate in the Material Engine plan."""
    family = re.sub(r"[^a-z0-9]+", "_", str(role_material.get("family") or "").casefold()).strip("_")
    base = family or role
    if base not in used_ids:
        used_ids.add(base)
        return base
    value = f"{base}_{ordinal}"
    while value in used_ids:
        ordinal += 1
        value = f"{base}_{ordinal}"
    used_ids.add(value)
    return value


def _is_paint_finish(role_material: Mapping[str, Any]) -> bool:
    return str(role_material.get("family") or "").casefold() == "paint_lacquer_stain"


def compose_approximate_bom_v1(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Compose the initial wardrobe/cabinet carcass recipe from a valid brief.

    The output has the stable ``materials`` and ``parts`` fields expected by
    the downstream Material Engine, while preserving recipe and assumption
    provenance for review.  It is not yet persisted or connected to runtime.
    """
    normalized = validate_object_to_estimate_v1(brief)
    if normalized["object_kind"] not in {"wardrobe", "cabinet"}:
        raise ValueError("no approximate BOM recipe exists for this object")
    if normalized["status"] == "failed":
        raise ValueError("cannot compose approximate BOM from a failed brief")

    dimensions = normalized["dimensions_mm"]
    width = dimensions["width"]["value_mm"]
    depth = dimensions["depth"]["value_mm"]
    height = dimensions["height"]["value_mm"]
    counts = normalized["counts"]
    bay_count = counts.get("bay_count", {"value": 1})["value"]
    door_count = counts.get("door_count", {"value": bay_count})["value"]
    shelf_count = counts.get("shelf_count_per_bay", {"value": 1})["value"]

    source_roles = {
        str(item["role"]): item
        for item in normalized["material_roles"]
        if str(item["role"]) in {"visible_facade", "internal_carcass", "backing"}
    }
    defaults = {
        "visible_facade": {
            "role": "visible_facade", "source_name": "Assumed visible facade MDF",
            "family": "mdf_hdf", "specification": {"board_type": "mdf", "thickness_mm": 18},
            "evidence_refs": [],
            "quantity": None, "unit": None,
        },
        "internal_carcass": {
            "role": "internal_carcass", "source_name": "Assumed internal melamine faced particleboard",
            "family": "melamine_faced_particleboard", "specification": {"thickness_mm": 18},
            "evidence_refs": [],
            "quantity": None, "unit": None,
        },
        "backing": {
            "role": "backing", "source_name": "Assumed hardboard backing",
            "family": "fibreboard_hardboard", "specification": {"thickness_mm": 3},
            "evidence_refs": [],
            "quantity": None, "unit": None,
        },
    }
    facade, facade_default = _recipe_role(role="visible_facade", defaults=defaults, source_roles=source_roles)
    carcass, carcass_default = _recipe_role(role="internal_carcass", defaults=defaults, source_roles=source_roles)
    backing, backing_default = _recipe_role(role="backing", defaults=defaults, source_roles=source_roles)
    carcass_thickness = float(carcass["specification"].get("thickness_mm") or 18)
    if carcass_thickness <= 0:
        raise ValueError("internal_carcass thickness must be positive")

    bay_width = width / bay_count
    inner_width = bay_width - 2 * carcass_thickness
    inner_height = height - 2 * carcass_thickness
    if inner_width <= 0 or inner_height <= 0:
        raise ValueError("object dimensions are incompatible with carcass thickness")

    materials = []
    parts = []
    assumptions = list(normalized["assumptions"])

    def requirement(role_material: Mapping[str, Any], *, requirement_id: str, default: bool, default_rule: str) -> None:
        if default and default_rule not in assumptions:
            assumptions.append(default_rule)
        materials.append({
            "requirement_id": requirement_id,
            "source_name": str(role_material["source_name"]), "family": str(role_material["family"]),
            "specification": dict(role_material["specification"]), "quantity": None, "unit": None,
            "evidence_refs": list(role_material.get("evidence_refs") or []),
            "basis": "construction_assumption" if default else "source_evidence",
        })

    requirement(facade, requirement_id="visible_facade", default=facade_default, default_rule="default_visible_facade_mdf")
    requirement(carcass, requirement_id="internal_carcass", default=carcass_default, default_rule="default_internal_melamine_faced_particleboard")
    requirement(backing, requirement_id="backing", default=backing_default, default_rule="default_backing_hardboard")
    # A named finish or fitting is a separate material demand even when the
    # sketch supplies no usable quantity.  That prevents a visible handle,
    # rail or coating from silently disappearing.  An explicit quantity is
    # multiplied by the finished-object quantity here, before project-wide
    # aggregation; otherwise the mandatory A fallback remains an auditable
    # provisional allowance.
    used_requirement_ids = {"visible_facade", "internal_carcass", "backing"}
    for role in ("finish", "hardware"):
        for ordinal, role_material in enumerate(
            (item for item in normalized["material_roles"] if item["role"] == role), start=1,
        ):
            requirement(
                role_material,
                requirement_id=_auxiliary_requirement_id(
                    role=role, role_material=role_material,
                    used_ids=used_requirement_ids, ordinal=ordinal,
                ),
                default=False,
                default_rule="",
            )
            if role_material.get("quantity") is not None:
                materials[-1]["quantity"] = float(role_material["quantity"]) * normalized["quantity"]
                materials[-1]["unit"] = role_material.get("unit")
            elif role == "finish" and _is_paint_finish(role_material):
                # V4 is an estimate, not a coating-shop recipe. One standard
                # paint set per finished object is the deliberately bounded
                # material norm until a source declares consumption.
                materials[-1]["quantity"] = float(normalized["quantity"])
                materials[-1]["unit"] = "piece"
                if "default_paint_finish_kit_per_finished_object" not in assumptions:
                    assumptions.append("default_paint_finish_kit_per_finished_object")
    if "derived_equal_bay_width" not in assumptions:
        assumptions.append("derived_equal_bay_width")
    if "derived_equal_door_width" not in assumptions:
        assumptions.append("derived_equal_door_width")
    if "default_single_shelf_per_bay" not in assumptions and "shelf_count_per_bay" not in counts:
        assumptions.append("default_single_shelf_per_bay")
    if "default_carcass_thickness_18mm" not in assumptions and carcass_default:
        assumptions.append("default_carcass_thickness_18mm")
    if "default_backing_thickness_3mm" not in assumptions and backing_default:
        assumptions.append("default_backing_thickness_3mm")

    def part(part_id: str, *, requirement_id: str, quantity: int, length_mm: float, width_mm: float) -> None:
        # Material Engine's part quantity is the total demand for this object
        # row, not a per-finished-item norm.  Multiplication belongs here so
        # sheet nesting can combine every finished item in the project.
        total_quantity = quantity * normalized["quantity"]
        parts.append({
            "part_id": part_id, "material_requirement_id": requirement_id, "quantity": total_quantity,
            "length_mm": round(length_mm, 3), "width_mm": round(width_mm, 3), "rotation_allowed": True,
            "basis": "approximate_recipe",
        })

    part("facade_doors", requirement_id="visible_facade", quantity=door_count, length_mm=height, width_mm=width / door_count)
    part("carcass_sides", requirement_id="internal_carcass", quantity=bay_count * 2, length_mm=height, width_mm=depth)
    part("carcass_top_bottom", requirement_id="internal_carcass", quantity=bay_count * 2, length_mm=bay_width, width_mm=depth)
    part("carcass_shelves", requirement_id="internal_carcass", quantity=bay_count * shelf_count, length_mm=inner_width, width_mm=depth)
    part("backing_panels", requirement_id="backing", quantity=bay_count, length_mm=height, width_mm=bay_width)

    return {
        "contract_version": APPROXIMATE_BOM_V1,
        "recipe_version": WARDROBE_CARCASS_RECIPE_V1,
        "input_id": normalized["input_id"], "object_input_revision": normalized["object_input_revision"],
        "run_id": normalized["run_id"], "company_id": normalized["company_id"],
        "object_id": normalized["object_id"], "object_name": normalized["object_name"],
        "quantity": normalized["quantity"], "dimensions_mm": dimensions,
        "materials": materials, "parts": parts, "assumptions": assumptions,
        "status": "ready",
        "primary_preview_ref": normalized["primary_preview_ref"],
    }
