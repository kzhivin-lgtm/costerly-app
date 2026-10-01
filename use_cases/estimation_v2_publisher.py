"""Deterministic Estimation v2 publisher for the existing product UI.

Object Facts are evidence-backed input only. This module owns material price
resolution, Labor Engine execution, overhead allocation, persistence and the
final object status consumed by Objects and Object Detail.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import re
from statistics import median
from typing import Any, Mapping, Sequence

from db.repositories import (
    fetch_active_israel_material_families,
    fetch_estimation_v2_fact_result,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
)
from agents.estimation_v2_page_facts_agent import ESTIMATION_V2_FACTS_AGENT_VERSION
from use_cases.estimate_material_resolution import resolve_estimate_material_requirement
from use_cases.estimation_v2_composition import compose_object_estimate, validate_object_facts
from use_cases.estimation_v2_labor_adapter import build_labor_input
from use_cases.labor_engine import estimate_labor
from use_cases.machinery import build_company_production_context
from use_cases.manufacturing_estimation import (
    ManufacturingEstimationError,
    build_manufacturing_cost_lines,
)
from use_cases.manufacturing_parameters import ManufacturingParameterError
from use_cases.material_identity_resolution import build_material_identity_index
from use_cases.material_price_resolver import _unit_price_multiplier
from use_cases.overhead_engine import build_overhead_lines


_ROLE_CANDIDATES = {
    "carpenter": ("carpenter",),
    "cnc_operator": ("cnc_operator",),
    "wood_machine_operator": ("cnc_operator", "carpenter"),
    "general_worker": ("general_worker", "carpenter"),
    "packer": ("general_worker", "carpenter"),
    "production_manager": ("production_manager", "general_manager"),
    "welder": ("welder",),
    "metal_machine_operator": ("welder", "general_worker"),
    "press_brake_operator": ("welder",),
    "grinder_polisher": ("painter_finisher", "welder"),
    "metal_finisher": ("painter_finisher", "welder"),
    "powder_coating_operator": ("painter_finisher",),
}

_ROUTINE_CONSUMABLE_FAMILIES = frozenset({
    "abrasives",
    "adhesives_sealants_and_fillers",
    "bulk_fasteners",
    "counted_furniture_connectors",
    "installation_consumables",
    "packaging_materials",
    "shop_consumables_and_tool_wear",
})
_MATERIAL_POLICY_PERCENTAGES = (
    ("consumables", "Consumables", 5.0),
    ("packaging", "Packaging", 1.0),
)


def _rows(client: Any, table: str, *, company_id: str | None = None) -> list[dict[str, Any]]:
    query = client.table(table).select("*")
    if company_id:
        query = query.eq("company_id", company_id)
    return [dict(row) for row in (query.execute().data or [])]


def _paged_rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read a full resolver catalog instead of PostgREST's first 1,000 rows."""
    page_size = 1000
    start = 0
    result: list[dict[str, Any]] = []
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(start, start + page_size - 1).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < page_size:
            return result
        start += page_size


def _number(value: Any, default: float = 0) -> float:
    try:
        return default if value is None or value == "" else float(value)
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(child) for child in value]
    return value


def _public_facts(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: child for key, child in value.items() if not str(key).startswith("_bom_")}


def _settings(client: Any, company_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = _rows(client, "overhead_settings", company_id=company_id)
    monthly = _rows(client, "overhead_monthly", company_id=company_id)
    return (settings[0] if settings else {}, monthly[0] if monthly else {})


def _catalogs(client: Any, company_id: str) -> dict[str, Any]:
    identities = _paged_rows(
        client,
        "reference_material_pricing_identities",
        filters={"market_code": "IL", "status": "active"},
    )
    prices = _paged_rows(
        client,
        "market_material_pricing_identity_prices",
        filters={"status": "active"},
    )
    baselines = _paged_rows(
        client,
        "market_material_baselines",
        filters={"market_code": "IL", "status": "active"},
    )
    all_reference_materials = _paged_rows(
        client, "reference_materials", filters={"active": True}
    )
    catalog_reference_materials = [
        row for row in all_reference_materials
        if (row.get("specifications") or {}).get("catalog_version")
        == "israel_global_catalog_v1"
    ] or all_reference_materials
    pricing_identity_members = _paged_rows(
        client, "reference_material_pricing_identity_members", filters={}
    )
    identity_attributes = {
        str(row.get("pricing_identity_id") or ""): dict(row.get("price_attributes") or {})
        for row in identities
    }
    identity_ids_by_material: dict[str, set[str]] = {}
    for row in pricing_identity_members:
        material_id = str(row.get("material_id") or "")
        identity_id = str(row.get("pricing_identity_id") or "")
        if material_id and identity_id:
            identity_ids_by_material.setdefault(material_id, set()).add(identity_id)
    reference_materials = []
    for row in catalog_reference_materials:
        material_id = str(row.get("material_id") or "")
        linked_ids = identity_ids_by_material.get(material_id) or set()
        specifications = dict(row.get("specifications") or {})
        if len(linked_ids) == 1:
            for key, value in identity_attributes.get(next(iter(linked_ids)), {}).items():
                if value not in (None, "", []) and key not in specifications:
                    specifications[key] = value
        reference_materials.append({**row, "specifications": specifications})
    reference_aliases = _paged_rows(
        client,
        "reference_material_aliases",
        filters={"market_code": "IL", "active": True},
    )
    return {
        "items": _rows(client, "company_material_items", company_id=company_id),
        "offers": _rows(client, "company_material_offers", company_id=company_id),
        "identities": identities,
        "prices": prices,
        "baselines": baselines,
        "reference_materials": reference_materials,
        "reference_aliases": reference_aliases,
        "material_identity_index": build_material_identity_index(
            reference_materials, reference_aliases, "IL"
        ),
        "pricing_identity_members": pricing_identity_members,
    }


def _price_samples(
    catalogs: Mapping[str, Any], *, family: str | None, target_unit: str,
    material_form: str | None = None,
) -> list[float]:
    family_key = str(family or "").strip().casefold()
    identities = {
        str(row.get("pricing_identity_id") or ""): row
        for row in catalogs.get("identities") or []
    }
    reference_materials = {
        str(row.get("material_id") or ""): row
        for row in catalogs.get("reference_materials") or []
    }
    samples: list[float] = []
    for row in catalogs.get("prices") or []:
        identity = identities.get(str(row.get("pricing_identity_id") or ""), {})
        attributes = identity.get("price_attributes") or {}
        row_family = str(attributes.get("material_family") or "").strip().casefold()
        if family_key and row_family != family_key:
            continue
        if material_form:
            detail = reference_materials.get(str(attributes.get("detail_material_id") or ""), {})
            if material_form.casefold() not in str(detail.get("canonical_name") or "").casefold():
                continue
        multiplier = _unit_price_multiplier(str(row.get("unit") or ""), target_unit)
        value = _number(row.get("price_high") or row.get("price_typical"))
        if multiplier is not None and value > 0:
            samples.append(value * float(multiplier))

    materials = {
        str(row.get("material_id") or ""): row
        for row in catalogs.get("reference_materials") or []
    }
    family_phrase = family_key.replace("_", " ")
    for row in catalogs.get("baselines") or []:
        material = materials.get(str(row.get("material_id") or ""), {})
        specifications = material.get("specifications") or {}
        corpus = " ".join((
            str(material.get("canonical_name") or ""),
            str(specifications.get("material_family") or ""),
            str(specifications.get("global_canonical_id") or "").replace("-", " "),
        )).casefold()
        if family_phrase and family_phrase not in corpus:
            continue
        if material_form and material_form.casefold() not in corpus:
            continue
        multiplier = _unit_price_multiplier(str(row.get("unit") or ""), target_unit)
        value = _number(row.get("price_high") or row.get("price_typical"))
        if multiplier is not None and value > 0:
            samples.append(value * float(multiplier))
    return samples


_PROFILE_DIMENSIONS = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:x|×|х)\s*(\d+(?:[.,]\d+)?)"
    r"(?:\s*(?:x|×|х)\s*(\d+(?:[.,]\d+)?))?",
    re.IGNORECASE,
)


def _material_for_pricing(material: Mapping[str, Any]) -> dict[str, Any]:
    """Correct narrow, auditable extraction-family mistakes before resolution."""
    normalized = dict(material)
    name = str(material.get("source_name") or "").casefold()
    family = str(material.get("family") or "").casefold()
    is_perforated_sheet = any(token in name for token in ("perforat", "перфор", "מחורר"))
    if family == "metal_coatings" and is_perforated_sheet:
        normalized["family"] = "carbon_steel"
        normalized["pricing_normalization"] = "perforated_metal_sheet_is_carbon_steel"
        family = "carbon_steel"
    raw_unit = str(material.get("unit") or "").strip().casefold()
    unit_aliases = {"м": "m", "м2": "m2", "м²": "m²", "л": "l", "шт": "piece"}
    normalized_unit = unit_aliases.get(raw_unit, str(material.get("unit") or ""))
    sheet_families = {
        "mdf", "plywood", "particleboard", "melamine", "hdf", "osb",
    }
    specification = dict(material.get("specification") or {})
    if normalized_unit == "piece" and family in sheet_families:
        width = _number(specification.get("width_mm"))
        height = _number(specification.get("height_mm"))
        if width > 0 and height > 0:
            normalized["quantity"] = round(
                _number(material.get("quantity"), 1) * width * height / 1_000_000,
                4,
            )
            normalized_unit = "m²"
            normalized["pricing_normalization"] = "sheet_piece_dimensions_to_area"
        else:
            normalized_unit = "sheet"
    if normalized_unit != material.get("unit"):
        normalized["source_unit"] = material.get("unit")
        normalized["unit"] = normalized_unit
    return normalized


def _english_material_name(material: Mapping[str, Any]) -> str:
    source_name = str(material.get("source_name") or "").strip()
    if source_name and source_name.isascii():
        return source_name
    family = str(material.get("family") or "material").replace("_", " ").title()
    specification = dict(material.get("specification") or {})
    detail = specification.get("profile_section")
    if not detail and _number(specification.get("thickness_mm")) > 0:
        detail = f"{_number(specification.get('thickness_mm')):g} mm"
    return f"{family}, {detail}" if detail else family


def _steel_profile_geometry(material: Mapping[str, Any]) -> dict[str, Any] | None:
    if str(material.get("family") or "").casefold() not in {
        "carbon_steel", "galvanized_steel", "aluminium",
    }:
        return None
    specification = dict(material.get("specification") or {})
    corpus = " ".join((str(material.get("source_name") or ""), str(specification.get("profile_section") or ""))).casefold()
    shape = None
    for candidate, tokens in (
        ("square tube", ("square tube", "square hollow", "квадратн", "מרובע")),
        ("rectangular tube", ("rectangular tube", "rectangular hollow", "прямоугольн", "מלבני")),
        ("round tube", ("round tube", "circular tube", "кругл", "עגול")),
        ("angle", ("angle", "угол", "זווית")),
    ):
        if any(token in corpus for token in tokens):
            shape = candidate
            break
    match = _PROFILE_DIMENSIONS.search(corpus.replace(",", "."))
    width = _number(specification.get("width_mm"))
    height = _number(specification.get("height_mm"), width)
    explicit_wall = _number(specification.get("wall_thickness_mm"))
    if match:
        width = width or float(match.group(1))
        height = height or float(match.group(2))
        explicit_wall = explicit_wall or (float(match.group(3)) if match.group(3) else 0)
    if shape == "round tube":
        width = _number(specification.get("diameter_mm")) or width
        height = width
    if shape is None and width > 0 and height > 0:
        shape = "square tube" if width == height else "rectangular tube"
    if width <= 0 or height <= 0:
        return None
    return {
        "material_form": shape, "width_mm": width, "height_mm": height,
        "wall_thickness_mm": explicit_wall or 1.5,
        "wall_thickness_policy": "explicit" if explicit_wall else "furniture_profile_default_1_5_mm",
    }


def _fallback_material_unit_cost(
    material: Mapping[str, Any], catalogs: Mapping[str, Any],
) -> tuple[float | None, str, dict[str, Any]]:
    family = str(material.get("family") or "")
    unit = str(material.get("unit") or "")
    unit_key = unit.casefold().replace("²", "2").replace("м", "m")
    specification = dict(material.get("specification") or {})
    direct = _price_samples(catalogs, family=family, target_unit=unit)
    if direct:
        value = round(float(median(direct)) * 1.05, 4)
        return value, "family_high_median", {"sample_count": len(direct), "reserve_percent": 5}

    family_key = family.casefold()
    if family_key in {"carbon_steel", "galvanized_steel", "aluminium"}:
        profile = _steel_profile_geometry(material)
        kg_prices = _price_samples(
            catalogs, family=family, target_unit="kg",
            material_form=profile["material_form"] if profile else None,
        )
        if kg_prices:
            kg_price = float(median(kg_prices))
            density_factor = 2.70 if family_key == "aluminium" else 7.85
            thickness = _number(specification.get("thickness_mm"))
            if unit_key in {"m2", "sqm"} and thickness > 0:
                kg_per_unit = thickness * density_factor
                return (
                    round(kg_price * kg_per_unit * 1.10, 4),
                    "steel_sheet_area_to_weight",
                    {"kg_per_m2": kg_per_unit, "kg_price": kg_price, "reserve_percent": 10},
                )
            if unit_key in {"m", "lm"} and profile:
                width = profile["width_mm"]
                height = profile["height_mm"]
                wall = profile["wall_thickness_mm"]
                if profile["material_form"] == "angle":
                    section_area = wall * (width + height - wall)
                elif profile["material_form"] == "round tube":
                    inner_diameter = max(width - 2 * wall, 0)
                    section_area = 3.141592653589793 * (width ** 2 - inner_diameter ** 2) / 4
                else:
                    inner_width = max(width - 2 * wall, 0)
                    inner_height = max(height - 2 * wall, 0)
                    section_area = width * height - inner_width * inner_height
                kg_per_unit = section_area * density_factor / 1000
                return (
                    round(kg_price * kg_per_unit * 1.10, 4),
                    "steel_profile_length_to_weight",
                    {**profile, "kg_per_m": kg_per_unit, "kg_price": kg_price, "reserve_percent": 10},
                )

    if unit_key in {"m2", "sqm"} and family_key in {"metal_coatings", "wood_coatings"}:
        purchase_unit = "kg" if family_key == "metal_coatings" else "l"
        purchase_prices = _price_samples(catalogs, family=family, target_unit=purchase_unit)
        if purchase_prices:
            consumption = 0.15 if purchase_unit == "kg" else 0.35
            price = float(median(purchase_prices))
            return (
                round(price * consumption * 1.10, 4),
                "coating_area_to_purchase_unit",
                {"purchase_unit": purchase_unit, "consumption_per_m2": consumption,
                 "purchase_unit_price": price, "reserve_percent": 10},
            )

    return None, "no_evidence_based_price", {"family": family_key, "unit": unit}


def _company_offer_price(
    resolution: Any,
    offers: Sequence[Mapping[str, Any]],
    *,
    requested_unit: str,
    vat_percent: float,
) -> tuple[float | None, str]:
    candidates: list[tuple[Decimal, str]] = []
    allowed = set(resolution.offer_ids)
    for offer in offers:
        offer_id = str(offer.get("offer_id") or "")
        if offer_id not in allowed:
            continue
        multiplier = _unit_price_multiplier(str(offer.get("normalized_unit") or ""), requested_unit)
        if multiplier is None:
            continue
        try:
            price = Decimal(str(offer.get("normalized_price"))) * multiplier
        except Exception:
            continue
        if offer.get("vat_included") is True:
            price /= Decimal("1") + Decimal(str(vat_percent)) / Decimal("100")
        if price > 0:
            candidates.append((price, offer_id))
    if not candidates:
        return None, "company-offer:unavailable"
    candidates.sort(key=lambda item: (item[0], item[1]))
    middle = candidates[(len(candidates) - 1) // 2]
    return round(float(middle[0]), 4), f"company-offer:{middle[1]}"


def _material_rows_and_costs(
    *,
    facts: Mapping[str, Any],
    catalogs: Mapping[str, Sequence[Mapping[str, Any]]],
    vat_percent: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for index, material in enumerate(facts.get("materials") or [], start=1):
        material = _material_for_pricing(material)
        if str(material.get("family") or "").casefold() in _ROUTINE_CONSUMABLE_FAMILIES:
            continue
        line_id = f"{facts['object_id']}_material_{index:04d}"
        quantity = _number(material.get("quantity"))
        unit = str(material.get("unit") or "")
        resolution = resolve_estimate_material_requirement(
            requirement_name=str(material.get("source_name") or material.get("family") or ""),
            material_family=str(material.get("family") or "") or None,
            specifications=material.get("specification") or {},
            requested_unit=unit,
            company_material_items=catalogs["items"],
            company_offers=catalogs["offers"],
            pricing_identities=catalogs["identities"],
            pricing_identity_prices=catalogs["prices"],
            reference_materials=catalogs.get("reference_materials") or [],
            reference_aliases=catalogs.get("reference_aliases") or [],
            pricing_identity_members=catalogs.get("pricing_identity_members") or [],
            material_identity_index=catalogs.get("material_identity_index"),
            as_of=date.today(),
        )
        unit_cost: float | None = None
        source_ref = "material-resolution:unresolved"
        if resolution.status == "resolved" and resolution.authority == "company":
            unit_cost, source_ref = _company_offer_price(
                resolution, catalogs["offers"], requested_unit=unit, vat_percent=vat_percent
            )
        elif resolution.status == "resolved" and resolution.price_typical is not None:
            unit_cost = float(resolution.price_typical)
            source_ref = f"israel-pricing:{resolution.pricing_identity_price_id}"
        fallback: dict[str, Any] | None = None
        if unit_cost is None:
            unit_cost, fallback_rule, fallback_details = _fallback_material_unit_cost(material, catalogs)
            source_ref = f"derived-price-policy:{fallback_rule}"
            fallback = {
                "rule": fallback_rule, "details": fallback_details,
                "original_resolution_status": resolution.status,
                "requested_unit": unit, "estimated_unit_cost": unit_cost,
            }
        cost = None if unit_cost is None else round(max(quantity, 1) * unit_cost, 2)
        source_name = material.get("source_name") or material.get("family")
        displayed_name = (
            resolution.resolved_material_name
            if resolution.thickness_policy and resolution.resolved_material_name
            else _english_material_name(material)
        )
        normalization_note = None
        if resolution.thickness_policy:
            normalization_note = (
                f"Requested {resolution.requested_thickness_mm} mm; priced as "
                f"{resolution.priced_thickness_mm} mm by sheet-thickness policy"
            )
        cost_lines.append({
            "line_id": line_id, "section": "material",
            "status": "review_required" if unit_cost is None else "estimated" if fallback else "resolved",
            "amount": cost, "currency": "ILS", "source_ref": source_ref,
            "reason_codes": ["material_price_unresolved"] if fallback else [],
        })
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "material",
            "group_name": "Materials", "item_name": displayed_name,
            "catalog_match_query": material.get("source_name"), "unit": unit,
            "unit_cost": unit_cost, "quantity": quantity or 1, "cost": cost,
            "source": "estimation_v2", "sort_order": index * 10,
            "needs_price": unit_cost is None, "needs_review": bool(fallback),
            "confidence": 45 if fallback and unit_cost is not None else None,
            "notes": normalization_note or (
                f"Derived by policy: {fallback['rule']}" if fallback and unit_cost is not None
                else "No evidence-based price available" if fallback else None
            ),
            "raw_agent_json": _json_safe({
                "facts": dict(material), "resolution": resolution.__dict__, "fallback": fallback,
            }),
        })
    return db_rows, cost_lines


def _material_policy_rows_and_costs(
    *, facts: Mapping[str, Any], primary_material_total: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply locked material-cost formulas from the temporary Pricing Policy."""
    base = round(max(primary_material_total, 0), 2)
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for offset, (policy, label, percent) in enumerate(_MATERIAL_POLICY_PERCENTAGES):
        amount = round(base * percent / 100, 2)
        line_id = f"{facts['object_id']}_material_policy_{policy}"
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "material",
            "group_name": "Materials", "item_name": label,
            "catalog_match_query": None, "unit": "% of materials", "unit_cost": percent,
            "quantity": 1, "cost": amount, "source": "pricing_policy",
            "sort_order": 900 + offset * 10, "needs_price": False, "needs_review": False,
            "confidence": 100, "notes": f"{percent:g}% of primary material cost",
            "raw_agent_json": {
                "policy": f"{policy}_percent_of_primary_materials",
                "percent": percent, "primary_material_total": base, "locked": True,
            },
        })
        cost_lines.append({
            "line_id": f"{line_id}_cost", "section": "material", "status": "resolved",
            "amount": amount, "currency": "ILS",
            "source_ref": f"pricing-policy:{policy}:{percent:g}-percent",
            "reason_codes": [],
        })
    return db_rows, cost_lines


def _manufacturing_input(facts: Mapping[str, Any]) -> dict[str, Any]:
    materials = {
        str(row.get("requirement_id") or ""): row
        for row in facts.get("materials") or []
        if isinstance(row, Mapping)
    }
    features: list[dict[str, Any]] = []
    for feature in facts.get("manufacturing_features") or []:
        if not isinstance(feature, Mapping):
            continue
        material = materials.get(str(feature.get("material_requirement_id") or ""), {})
        specification = material.get("specification") or {}
        features.append({
            "process": feature.get("process"),
            "material_family": material.get("family"),
            "thickness_mm": specification.get("thickness_mm"),
            **dict(feature.get("measurements") or {}),
            **dict(feature.get("flags") or {}),
            "evidence_pages": ", ".join(str(value) for value in feature.get("evidence_refs") or []),
            "notes": "",
        })
    return {
        "estimate_id": facts["estimate_id"],
        "object_id": facts["object_id"],
        "company_id": facts["company_id"],
        "manufacturing": features,
    }


def _manufacturing_rows_and_costs(
    *,
    facts: Mapping[str, Any],
    production_context: Mapping[str, Any],
    parameter_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not facts.get("manufacturing_features"):
        return [], []
    try:
        rows = build_manufacturing_cost_lines(
            estimation_result=_manufacturing_input(facts),
            production_context=production_context,
            parameter_rows=parameter_rows,
        )
    except (ManufacturingEstimationError, ManufacturingParameterError, ValueError) as exc:
        return _fallback_manufacturing_rows(facts, production_context, str(exc))
    if not rows:
        return _fallback_manufacturing_rows(facts, production_context, "no deterministic route")
    costs = [{
        "line_id": f"{facts['object_id']}_machinery_{index:04d}",
        "section": "machinery", "status": "resolved",
        "amount": _number(row.get("cost")), "currency": "ILS",
        "source_ref": f"manufacturing-engine:{(row.get('raw_agent_json') or {}).get('calculator')}",
        "reason_codes": [],
    } for index, row in enumerate(rows, start=1)]
    return rows, costs


def _fallback_manufacturing_rows(
    facts: Mapping[str, Any], production_context: Mapping[str, Any], diagnostic: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose unresolved machinery without inventing hours or rates."""
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for index, feature in enumerate(facts.get("manufacturing_features") or [], start=1):
        process = str(feature.get("process") or "manufacturing")
        machine_code = "wood_cnc_router" if process == "cnc_router" else "metal_sheet_laser"
        line_id = f"{facts['object_id']}_manufacturing_fallback_{index:04d}"
        audit = {
            "resolution": "no_deterministic_machinery_cost", "machine_code": machine_code,
            "diagnostic": diagnostic, "feature": dict(feature),
        }
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "labor",
            "group_name": "In-house CNC / Laser manufacturing",
            "item_name": process.replace('_', ' ').title(),
            "role": "machine service", "hours": None, "rate": None, "cost": None,
            "source": "estimation_v2", "sort_order": 800 + index * 10,
            "needs_price": True, "needs_review": True, "confidence": None,
            "hours_basis": "No deterministic machinery route available",
            "raw_agent_json": _json_safe(audit),
        })
        cost_lines.append({
            "line_id": f"{line_id}_cost", "section": "machinery", "status": "review_required",
            "amount": None, "currency": "ILS",
            "source_ref": f"machinery-resolution:unresolved:{machine_code}",
            "reason_codes": ["machinery_cost_unresolved"],
        })
    return db_rows, cost_lines


def _facts_without_manufacturing_labor(facts: Mapping[str, Any]) -> dict[str, Any]:
    processes = {
        str(row.get("process") or "")
        for row in facts.get("manufacturing_features") or []
        if isinstance(row, Mapping)
    }
    handled_codes: set[str] = set()
    if "sheet_laser" in processes:
        handled_codes.update({"sheet_laser_cutting", "sheet_nesting"})
    if "cnc_router" in processes:
        handled_codes.update({
            "cnc_programming", "sheet_nesting", "cnc_router_profile_cutting",
            "cnc_vertical_drilling", "cnc_horizontal_drilling", "cnc_grooving",
            "cnc_pocketing",
        })
    return {
        **facts,
        "labor_operations": [
            row for row in facts.get("labor_operations") or []
            if str(row.get("operation_code") or "") not in handled_codes
        ],
    }


def _purchased_component_rows_and_costs(
    facts: Mapping[str, Any], catalogs: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose unresolved bought fabrication in Object Detail, never as free material."""
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for index, component in enumerate(facts.get("purchased_components") or [], start=1):
        line_id = f"{facts['object_id']}_purchased_{index:04d}"
        component_type = str(component.get("component_type") or "Purchased component")
        material = {
            "family": component_type, "unit": component.get("unit") or "ea",
            "specification": component.get("specification") or {},
        }
        unit_cost, rule, details = _fallback_material_unit_cost(material, catalogs)
        quantity = max(_number(component.get("quantity")), 1)
        cost = None if unit_cost is None else round(quantity * unit_cost, 2)
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "material",
            "group_name": "Purchased fabricated components",
            "item_name": component_type.replace("_", " ").title(),
            "unit": component.get("unit"), "quantity": quantity,
            "unit_cost": unit_cost, "cost": cost, "source": "estimation_v2",
            "sort_order": 500 + index * 10, "needs_price": unit_cost is None, "needs_review": True,
            "confidence": 35 if unit_cost is not None else None,
            "notes": f"Derived by policy: {rule}" if unit_cost is not None else "No evidence-based price available",
            "raw_agent_json": _json_safe({"facts": dict(component), "fallback": {"rule": rule, "details": details}}),
        })
        cost_lines.append({
            "line_id": f"{line_id}_cost", "section": "purchased_component",
            "status": "estimated" if cost is not None else "review_required",
            "amount": cost, "currency": "ILS",
            "source_ref": f"derived-price-policy:{rule}",
            "reason_codes": ["purchased_component_price_unresolved"],
        })
    return db_rows, cost_lines


def _employee_rate(employee: Mapping[str, Any], monthly_capacity: float) -> float | None:
    gross_hourly = _number(employee.get("gross_hourly_rate"))
    if gross_hourly > 0:
        return gross_hourly
    gross_monthly = _number(employee.get("gross_monthly_salary"))
    return round(gross_monthly / monthly_capacity, 4) if gross_monthly > 0 and monthly_capacity > 0 else None


def _role_rate(
    role: str,
    employees: Sequence[Mapping[str, Any]],
    monthly_capacity: float,
) -> tuple[float | None, str | None]:
    active = [row for row in employees if not row.get("deleted_at")]
    for position in _ROLE_CANDIDATES.get(role, (role,)):
        matches = [row for row in active if str(row.get("position_code") or "") == position]
        rates = [rate for row in matches if (rate := _employee_rate(row, monthly_capacity)) is not None]
        if rates:
            return round(sum(rates) / len(rates), 4), position
    production = [
        row for row in active
        if str(row.get("department") or row.get("department_code") or "").casefold() == "production"
    ]
    rates = [rate for row in production if (rate := _employee_rate(row, monthly_capacity)) is not None]
    if rates:
        return round(sum(rates) / len(rates), 4), "company_average_production"
    return None, None


def _labor_rows_and_costs(
    *, client: Any, facts: Mapping[str, Any], settings: Mapping[str, Any],
    employees: Sequence[Mapping[str, Any]] | None = None,
    production_context: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, float]:
    labor_input = build_labor_input(facts)
    context = dict(production_context or build_company_production_context(str(facts["company_id"]), client=client))
    result = estimate_labor(labor_input, context)
    if result.get("status") != "estimated":
        return [], [{
            "line_id": f"{facts['object_id']}_labor_unresolved", "section": "labor",
            "status": "review_required", "amount": None, "currency": "ILS",
            "source_ref": "labor-engine:review", "reason_codes": ["labor_review_required"],
        }], 0, 0
    employees = list(employees) if employees is not None else _rows(
        client, "company_employees", company_id=str(facts["company_id"])
    )
    monthly_capacity = (
        _number(settings.get("workdays_per_month"), 22)
        * _number(settings.get("hours_per_day"), 8)
    )
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    base_total = 0.0
    hours_total = 0.0
    unresolved = False
    sort_order = 1000
    for operation in result.get("labor_lines") or []:
        for allocation in operation.get("role_allocations") or []:
            sort_order += 10
            role = str(allocation.get("role") or "")
            hours = _number(allocation.get("hours"))
            rate, matched_role = _role_rate(role, employees, monthly_capacity)
            cost = round(hours * rate, 2) if rate is not None and hours > 0 else 0.0
            used_company_average = bool(matched_role and matched_role.startswith("company_average_"))
            missing_rate = rate is None
            unresolved = unresolved or missing_rate
            base_total += cost
            hours_total += hours
            operation_audit = dict(operation)
            operation_audit["rate_resolution"] = {
                "requested_role": role, "matched_role": matched_role,
                "fallback": used_company_average, "rate": rate,
            }
            db_rows.append({
                "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
                "line_id": f"{facts['object_id']}_labor_{sort_order:04d}",
                "company_id": facts["company_id"], "section": "labor",
                "group_name": "Labor", "item_name": str(operation.get("operation_code") or "Work").replace("_", " ").title(),
                "role": matched_role or role, "hours": hours, "rate": rate, "cost": cost,
                "source": "labor_engine_v0", "sort_order": sort_order,
                "needs_price": missing_rate, "needs_review": used_company_average or missing_rate,
                "confidence": operation.get("baseline_confidence"), "hours_basis": operation.get("formula"),
                "notes": "Estimated with company average labor rate" if used_company_average
                else "No company labor rate available" if missing_rate else None,
                "raw_agent_json": operation_audit,
            })
    employer_percent = _number(settings.get("employer_load_percent"), 25)
    labor_total = round(base_total * (1 + employer_percent / 100), 2)
    cost_lines.append({
        "line_id": f"{facts['object_id']}_labor_total", "section": "labor",
        "status": "review_required" if unresolved else "resolved",
        "amount": None if unresolved else labor_total, "currency": "ILS",
        "source_ref": "labor-engine:labor_time_v0",
        "reason_codes": ["labor_review_required"] if unresolved else [],
    })
    return db_rows, cost_lines, hours_total, labor_total


def _safe_db_lines(lines: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep the publisher compatible until optional classification migration lands."""
    return [
        {key: value for key, value in dict(line).items() if key not in {"economic_classification", "price_scope"}}
        for line in lines
    ]


def build_estimation_v2_context(client: Any, company_id: str) -> dict[str, Any]:
    settings, overhead_monthly = _settings(client, company_id)
    return {
        "families": fetch_active_israel_material_families(client),
        "catalogs": _catalogs(client, company_id),
        "settings": settings,
        "overhead_monthly": overhead_monthly,
        "employees": _rows(client, "company_employees", company_id=company_id),
        "production_context": build_company_production_context(company_id, client=client),
        "manufacturing_parameters": _paged_rows(
            client,
            "manufacturing_cost_parameters",
            filters={"country_code": "IL", "status": "active"},
        ),
    }


def publish_estimation_v2_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_v2_fact_result(
        client, input_id=input_id, agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION
    )
    if not fact_result:
        raise RuntimeError("Object Facts result is missing after extraction.")
    facts = dict(fact_result.get("facts_payload") or {})
    shared = dict(context or build_estimation_v2_context(client, str(facts["company_id"])))
    families = set(shared["families"])
    validate_object_facts(facts, allowed_material_families=families)

    settings = dict(shared["settings"])
    overhead_monthly = dict(shared["overhead_monthly"])
    vat_percent = _number(settings.get("vat_percent"), 18)
    pricing_facts = {**facts, "estimate_id": estimate_id}
    material_rows, material_costs = _material_rows_and_costs(
        facts=pricing_facts, catalogs=shared["catalogs"], vat_percent=vat_percent
    )
    consumable_rows, consumable_costs = _material_policy_rows_and_costs(
        facts=pricing_facts,
        primary_material_total=sum(_number(row.get("cost")) for row in material_rows),
    )
    material_rows.extend(consumable_rows)
    material_costs.extend(consumable_costs)
    purchased_rows, purchased_costs = _purchased_component_rows_and_costs(
        pricing_facts, shared["catalogs"]
    )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id, status="running",
        progress_percent=70, progress_label="materials_resolved",
    )
    labor_rows, labor_costs, labor_hours, labor_total = _labor_rows_and_costs(
        client=client, facts=_facts_without_manufacturing_labor(pricing_facts), settings=settings,
        employees=shared["employees"], production_context=shared["production_context"],
    )
    manufacturing_rows, machinery_costs = _manufacturing_rows_and_costs(
        facts=pricing_facts,
        production_context=shared["production_context"],
        parameter_rows=shared.get("manufacturing_parameters") or [],
    )
    material_total = sum(_number(line.get("cost")) for line in material_rows)
    manufacturing_total = sum(_number(line.get("cost")) for line in manufacturing_rows)
    overhead_rows = _safe_db_lines(build_overhead_lines(
        estimate_id=estimate_id, object_id=object_id, company_id=str(facts["company_id"]),
        settings=settings, overhead_monthly=overhead_monthly,
        labor_hours_total=labor_hours,
        subtotal_before_overhead=material_total + labor_total + manufacturing_total,
    ))
    overhead_total = sum(_number(line.get("cost")) for line in overhead_rows)
    overhead_costs = [{
        "line_id": f"{object_id}_overhead_total", "section": "overhead",
        "status": "resolved" if overhead_rows else "review_required",
        "amount": overhead_total if overhead_rows else None, "currency": "ILS",
        "source_ref": "overhead-engine:company-profile",
        "reason_codes": [] if overhead_rows else ["overhead_review_required"],
    }]
    composition = compose_object_estimate(
        facts=_public_facts(facts),
        cost_lines=[*material_costs, *purchased_costs, *labor_costs, *machinery_costs, *overhead_costs],
        allowed_material_families=families,
    )
    replace_rfq_estimate_lines_for_object(
        client, estimate_id=estimate_id, object_id=object_id,
        lines=_safe_db_lines([
            *material_rows, *purchased_rows, *manufacturing_rows,
            *labor_rows, *overhead_rows,
        ]),
    )
    status = "completed" if composition["status"] == "complete" else "review_required"
    if composition.get("self_cost_unit") is not None:
        self_cost = _number(composition["self_cost_unit"])
        vat = round(self_cost * vat_percent / 100, 2)
        update_rfq_object_estimate_totals(
            client, estimate_id=estimate_id, object_id=object_id,
            self_cost_ex_vat=self_cost, vat_amount=vat,
            self_cost_total=round(self_cost + vat, 2),
        )
    else:
        update_rfq_object_estimate_totals(
            client, estimate_id=estimate_id, object_id=object_id,
            self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
        )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id, status=status,
        progress_percent=100,
        progress_label="completed" if status == "completed" else "costing_review_required",
    )
    return composition
