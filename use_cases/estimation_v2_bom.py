"""Deterministic material takeoff for supported Estimation v2 templates."""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
import re
from typing import Any, Mapping


class EstimationV2BomError(ValueError):
    pass


def _positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise EstimationV2BomError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EstimationV2BomError(f"{name} must be numeric") from exc
    if not isfinite(number) or number <= 0:
        raise EstimationV2BomError(f"{name} must be greater than zero")
    return number


def _source_preview(facts: Mapping[str, Any]) -> str:
    value = str(facts.get("primary_preview_ref") or "").strip()
    if not value:
        raise EstimationV2BomError("primary_preview_ref is required")
    return value


def _material(
    *, requirement_id: str, source_name: str, family: str, specification: Mapping[str, Any],
    quantity: float, unit: str, preview_ref: str, calculation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "source_name": source_name,
        "family": family,
        "specification": dict(specification),
        "quantity": round(quantity, 4),
        "unit": unit,
        "evidence_refs": [preview_ref],
        "calculation": dict(calculation),
    }


def _strip_calculation(material: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in material.items() if key != "calculation"}


def _open_shelving_unit(facts: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = facts.get("dimensions_mm") or {}
    features = facts.get("features") or {}
    width_mm = _positive(dimensions.get("width"), "dimensions_mm.width")
    depth_mm = _positive(dimensions.get("depth"), "dimensions_mm.depth")
    height_mm = _positive(dimensions.get("height"), "dimensions_mm.height")
    shelf_count = int(_positive(features.get("shelf_count"), "features.shelf_count"))
    if shelf_count != float(features.get("shelf_count")):
        raise EstimationV2BomError("features.shelf_count must be an integer")
    if width_mm > 2000 or depth_mm > 1200 or height_mm > 4000:
        raise EstimationV2BomError("open shelving dimensions are outside the supported envelope")

    preview_ref = _source_preview(facts)
    source_materials = [row for row in (facts.get("materials") or []) if isinstance(row, Mapping)]
    mdf = next((row for row in source_materials if row.get("family") == "mdf"), None)
    profile = next((row for row in source_materials if row.get("family") in {"carbon_steel", "galvanized_steel"}
                    and any(token in str(row.get("source_name") or "").casefold()
                            for token in ("profile", "профил"))), None)
    perforated = next((row for row in source_materials if row.get("family") in {"carbon_steel", "galvanized_steel"}
                       and any(token in str(row.get("source_name") or "").casefold()
                               for token in ("perfor", "перфор"))), None)
    if mdf is None or profile is None or perforated is None:
        raise EstimationV2BomError("open shelving requires MDF, metal profile and perforated sheet facts")

    profile_spec = dict(profile.get("specification") or {})
    section_text = str(profile_spec.get("profile_section") or "20x20").lower().replace("×", "x")
    if re.search(r"(?<!\d)20\s*x\s*20(?!\d)", section_text) is None:
        raise EstimationV2BomError("only 20x20 square tube is supported for open shelving v1")
    wall_thickness_mm = float(profile_spec.get("wall_thickness_mm") or 1.5)
    if wall_thickness_mm <= 0 or wall_thickness_mm * 2 >= 20:
        raise EstimationV2BomError("square tube wall thickness is invalid")

    # Two vertical members plus one rectangular support frame per shelf.
    net_profile_m = (2 * height_mm + shelf_count * 2 * (width_mm + depth_mm)) / 1000
    profile_waste_factor = 1.05
    profile_length_m = net_profile_m * profile_waste_factor
    section_area_mm2 = 20 * 20 - (20 - 2 * wall_thickness_mm) ** 2
    kg_per_m = section_area_mm2 * 0.00785
    profile_kg = profile_length_m * kg_per_m

    mdf_quantity = mdf.get("quantity")
    if mdf_quantity is None:
        net_mdf_sqm = width_mm * depth_mm * shelf_count / 1_000_000
        mdf_basis = "template rectangle fallback"
    else:
        if str(mdf.get("unit") or "").lower() not in {"m2", "sqm"}:
            raise EstimationV2BomError("MDF takeoff must use square metres")
        net_mdf_sqm = _positive(mdf_quantity, "materials.mdf.quantity")
        mdf_basis = "preview panel takeoff"
    mdf_waste_factor = 1.15
    mdf_sqm = net_mdf_sqm * mdf_waste_factor

    perforated_quantity = perforated.get("quantity")
    if perforated_quantity is None:
        net_perforated_sqm = width_mm * height_mm / 1_000_000
        perforated_basis = "width x height"
    else:
        if str(perforated.get("unit") or "").lower() not in {"m2", "sqm"}:
            raise EstimationV2BomError("perforated sheet takeoff must use square metres")
        net_perforated_sqm = _positive(perforated_quantity, "materials.perforated.quantity")
        perforated_basis = "preview panel takeoff"
    perforated_waste_factor = 1.10
    perforated_sqm = net_perforated_sqm * perforated_waste_factor

    tube_surface_sqm = 4 * 0.020 * profile_length_m
    sheet_surface_sqm = 2 * net_perforated_sqm
    coating_surface_sqm = tube_surface_sqm + sheet_surface_sqm
    wet_coating_l_per_sqm = 0.16
    coating_l = max(0.1, coating_surface_sqm * wet_coating_l_per_sqm)

    materials_with_calculation = [
        _material(
            requirement_id="bom-profile", source_name="Carbon steel S235, square tube, mill finish",
            family="carbon_steel",
            specification={"grade": "S235", "profile_section": "20x20", "wall_thickness_mm": wall_thickness_mm,
                           "finish": "mill finish"},
            quantity=profile_kg, unit="kg", preview_ref=preview_ref,
            calculation={"net_length_m": round(net_profile_m, 4), "waste_factor": profile_waste_factor,
                         "purchase_length_m": round(profile_length_m, 4), "kg_per_m": round(kg_per_m, 4)},
        ),
        _material(
            requirement_id="bom-mdf", source_name="Standard MDF, raw, 19 mm",
            family="mdf", specification={"thickness_mm": 19, "finish": "raw", "surface": "20 mm design proxy"},
            quantity=mdf_sqm, unit="m2", preview_ref=preview_ref,
            calculation={"basis": mdf_basis, "net_sqm": round(net_mdf_sqm, 4), "waste_factor": mdf_waste_factor},
        ),
        _material(
            requirement_id="bom-perforated", source_name="Carbon steel S235 perforated sheet, mill finish",
            family="carbon_steel", specification={"grade": "S235", "surface": "perforated", "finish": "mill finish"},
            quantity=perforated_sqm, unit="m2", preview_ref=preview_ref,
            calculation={"basis": perforated_basis, "net_sqm": round(net_perforated_sqm, 4),
                         "waste_factor": perforated_waste_factor},
        ),
        _material(
            requirement_id="bom-primer", source_name="Epoxy metal primer", family="metal_coatings",
            specification={"coating": "epoxy primer"}, quantity=coating_l, unit="l", preview_ref=preview_ref,
            calculation={"coating_surface_sqm": round(coating_surface_sqm, 4),
                         "litres_per_sqm": wet_coating_l_per_sqm, "coats": 1},
        ),
        _material(
            requirement_id="bom-topcoat", source_name="Polyurethane metal topcoat, satin", family="metal_coatings",
            specification={"coating": "polyurethane topcoat", "finish": "satin"},
            quantity=coating_l, unit="l", preview_ref=preview_ref,
            calculation={"coating_surface_sqm": round(coating_surface_sqm, 4),
                         "litres_per_sqm": wet_coating_l_per_sqm, "coats": 1},
        ),
    ]
    result = deepcopy(dict(facts))
    result["status"] = "ready"
    result["dimensions_mm"] = {"width": width_mm, "depth": depth_mm, "height": height_mm}
    result["features"] = {
        **dict(features), "shelf_count": shelf_count, "back_panel": True,
        "profile_section_mm": 20,
    }
    result["materials"] = [_strip_calculation(row) for row in materials_with_calculation]
    result["purchased_components"] = []
    result["review_items"] = [
        {
            "code": "material_identity_ambiguous", "severity": "warning",
            "path": "materials[bom-profile].specification.wall_thickness_mm",
            "message": "Square-tube wall thickness is not stated. Draft uses the explicit 1.5 mm estimating assumption.",
            "evidence_refs": [preview_ref],
        },
        {
            "code": "material_identity_ambiguous", "severity": "warning",
            "path": "materials[bom-mdf].specification.thickness_mm",
            "message": "The design states 20 mm MDF. Draft uses the available 19 mm Israel price class as a visible proxy.",
            "evidence_refs": [preview_ref],
        },
    ]
    return {
        "facts": result,
        "calculations": {row["requirement_id"]: row["calculation"] for row in materials_with_calculation},
        "assumptions": ["square_tube_wall_1_5_mm", "mdf_19_mm_price_proxy", "template_waste_factors_v1",
                        "wet_coating_0_16_l_per_sqm_per_coat"],
    }


def derive_supported_bom(facts: Mapping[str, Any]) -> dict[str, Any] | None:
    template = facts.get("template") or {}
    code = template.get("code") if isinstance(template, Mapping) else None
    if code == "open_shelving_unit":
        return _open_shelving_unit(facts)
    return None
