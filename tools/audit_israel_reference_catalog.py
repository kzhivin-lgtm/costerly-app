#!/usr/bin/env python3
"""Generate a read-only coverage audit of the canonical Israel catalog.

The audit reads the actual catalog chain:
Global Family -> Global Model -> Israel Listing -> Israel price and format.
It deliberately ignores the older pricing-identity bridge. That bridge is an
implementation detail of an earlier resolver, not a catalog entity.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client
from use_cases.material_identity_status import pricing_policy_by_family_code


DEFAULT_OUTPUT = ROOT / "notes" / "ISRAEL_REFERENCE_DEFAULT_POLICY_MATRIX_3_17_4_1.md"
COVERAGE_OUTPUT = ROOT / "notes" / "ISRAEL_REFERENCE_COVERAGE_AUDIT_3_17_4_1.md"


# Only owner-confirmed baselines are stated here. A blank cell means that a
# default must not be invented until an approved canonical Israel listing and
# price exist for it. Secondary fields never split catalog rows.
_OWNER_CONFIRMED_DEFAULTS: dict[str, dict[str, Any]] = {
    "mdf_hdf": {"thickness": 17},
    "faced_mdf": {"thickness": 17},
    "particleboard": {"thickness": 17},
    "melamine_faced_particleboard": {"thickness": 17},
    "plywood": {"thickness": 17},
    "osb": {"thickness": 18},
    "fibreboard_hardboard": {"thickness": 3},
    "compact_laminate": {"thickness": 12},
    "wood_veneer": {"species": "oak", "secondary_thickness_mm": 0.6},
    "edge_banding": {"width": 22, "thickness": 0.8},
    "natural_stone_slab": {"stone_type": "marble", "thickness": 20},
    "engineered_quartz_mineral_hybrid": {"thickness": 20},
    "sintered_ultra_compact_surface": {"thickness": 12},
    "porcelain_ceramic_slab": {"thickness": 12},
    "solid_surface": {"thickness": 12},
    "terrazzo_engineered_agglomerate": {"thickness": 20},
    "paint_lacquer_stain": {"coating_system": "standard paint"},
    "powder_coating": {"coating_system": "standard semi-matte powder coating"},
    "metal_tube": {"metal_type": "carbon steel", "section_profile": "round_tube"},
    "metal_profile_angle_channel": {"metal_type": "carbon steel", "section_profile": "angle"},
    "metal_flat_bar": {"metal_type": "carbon steel", "width": 30, "thickness": 1.5},
}

_KEY_ATTRIBUTE_CODES: dict[str, tuple[str, ...]] = {
    "thickness": ("thickness",), "species": ("species",), "width": ("width",),
    "width_thickness": ("width", "thickness"),
    "dimensions": ("dimensions", "length", "width", "depth", "diameter"),
    "metal_type": ("metal_type",), "section_profile": ("section_profile",),
    "wall_thickness": ("wall_thickness",), "diameter": ("diameter",),
    "coating_system": ("coating_system",), "stone_type": ("stone_type",),
    "chemistry_product_type": ("chemistry_product_type",),
    "nominal_length": ("nominal_length", "length", "depth"),
    "component_type": ("component_type",), "packaging_type": ("packaging_type",),
}


def _rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(offset, offset + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        offset += 1000


def _has_value(values: Mapping[str, Any], code: str) -> bool:
    return values.get(code) not in (None, "", [], {})


def _key_complete(values: Mapping[str, Any], key_fields: Iterable[str]) -> bool:
    for field in key_fields:
        if field == "width_thickness":
            compound = values.get("width_thickness")
            if isinstance(compound, Mapping) and all(
                _has_value(compound, key)
                for key in ("width_mm", "thickness_mm")
            ):
                continue
        alternatives = _KEY_ATTRIBUTE_CODES.get(field, (field,))
        if not any(_has_value(values, candidate) for candidate in alternatives):
            return False
    return True


def _default_matches(values: Mapping[str, Any], defaults: Mapping[str, Any]) -> bool:
    comparable = {key: value for key, value in defaults.items() if not key.startswith("secondary_")}
    return bool(comparable) and all(
        str(values.get(key)).casefold() == str(value).casefold()
        for key, value in comparable.items()
    )


def _display_specs(specs: Mapping[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in specs.items()) if specs else "pending"


def _default_mode(family_code: str, key_fields: Iterable[str]) -> str:
    if family_code.startswith("hardware_"):
        return "lowest compatible package, Company first, then Israel"
    if family_code == "purchased_fabricated_component":
        return "no generic default, component type remains required"
    if family_code == "packaging_material":
        return "standard Israel position after package type is known"
    if not tuple(key_fields):
        return "standard Israel position"
    return "Pricing-Key default after family is proven"


def _gap(row: Mapping[str, Any]) -> str:
    if row["models"] == 0:
        return "no canonical model"
    if row["listings"] == 0:
        return "no active Israel listing"
    if row["key_complete_models"] == 0:
        return "models lack complete Pricing Key"
    if row["active_price_models"] == 0:
        return "no active Israel price"
    if str(row["family_code"]).startswith("hardware_"):
        return "covered" if row["retail_package_models"] else "no active package price"
    if row["material_only_models"] == 0:
        return "no active material-only price"
    if row["format_policy"] != "not_required" and row["formats"] == 0:
        return "no approved purchase format"
    if row["default_specs"] and row["default_match_models"] == 0:
        return "default baseline pending"
    return "covered"


def _write_default_matrix(path: Path, rows: list[dict[str, Any]], *, summary: str) -> None:
    body = [
        "# Israel Reference Default Policy Matrix, 3.17.4.1", "",
        "Status: policy baseline generated from the Family registry and owner-confirmed defaults.", "",
        "## Contract", "",
        "- Every Israel Reference row is an authoritative canonical market position.",
        "- A Company row links many-to-one to one Israel position when Family and Pricing Key match.",
        "- Family plus Pricing Key is the complete matching depth. Secondary attributes describe the position but do not create another price class.",
        "- A default completes missing Pricing Key facts only after Family is proven. It never infers Family.",
        "- Hardware uses a deterministic package-selection branch, Company first and Israel second.", "",
        f"Live snapshot: {summary}", "",
        "| Family | Pricing Key | Default policy | Confirmed baseline | Purchase format | Catalog state |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        body.append(
            f"| {row['family_code']} | {', '.join(row['key_fields']) or 'none'} | "
            f"{row['default_mode']} | {_display_specs(row['default_specs'])} | "
            f"{row['format_policy']} | {row['gap']} |"
        )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _write_coverage_audit(path: Path, rows: list[dict[str, Any]], *, summary: str) -> None:
    totals = Counter(row["gap"] for row in rows)
    body = [
        "# Israel Reference Coverage Audit, 3.17.4.1", "",
        "Status: read-only snapshot of Global Family -> Global Model -> Israel Listing -> Israel Price and Purchase Format.", "",
        f"Summary: {summary}", "", "## Gap totals", "",
        *(f"- {gap}: {count}" for gap, count in sorted(totals.items())), "", "## Family coverage", "",
        "| Family | Models | IL listings | Key-complete models | Priced positions | Material-only | Package prices | Formats | Default match | Gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        body.append(
            "| {family_code} | {models} | {listings} | {key_complete_models} | {active_price_models} | {material_only_models} | {retail_package_models} | {formats} | {default_match_models} | {gap} |".format(**row)
        )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--default-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--coverage-output", type=Path, default=COVERAGE_OUTPUT)
    args = parser.parse_args()
    client = get_supabase_client()
    families = _rows(client, "reference_material_families", filters={"active": True})
    policies = _rows(client, "reference_material_family_pricing_policies", filters={"active": True})
    models = _rows(client, "reference_material_models", filters={"active": True})
    listings = _rows(client, "reference_market_material_listings", filters={"market_code": "IL", "active": True})
    values = _rows(client, "reference_material_model_attribute_values", filters={})
    mappings = _rows(client, "reference_market_material_legacy_mappings", filters={"market_code": "IL", "classification_status": "mapped"})
    prices = _rows(client, "market_material_model_prices", filters={"market_code": "IL", "status": "active"})
    formats = _rows(client, "reference_market_material_supply_formats", filters={"active": True})

    policies_by_code = pricing_policy_by_family_code(policies, families=families)
    active_models = {str(row["material_model_id"]): row for row in models}
    active_listings = {
        str(row["market_material_listing_id"]): row for row in listings
        if str(row.get("material_model_id") or "") in active_models
    }
    listing_by_model = {str(row["material_model_id"]): listing_id for listing_id, row in active_listings.items()}
    values_by_model: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in values:
        model_id = str(row.get("material_model_id") or "")
        if model_id in active_models:
            values_by_model[model_id][str(row.get("attribute_code") or "")] = row.get("attribute_value")
    model_by_legacy_material = {
        str(row.get("legacy_material_id") or ""): str(row.get("material_model_id") or "")
        for row in mappings if str(row.get("material_model_id") or "") in active_models
    }
    prices_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for price in prices:
        model_id = model_by_legacy_material.get(str(price.get("material_id") or ""))
        if model_id in listing_by_model:
            prices_by_model[model_id].append(price)
    formats_by_listing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for supply_format in formats:
        listing_id = str(supply_format.get("market_material_listing_id") or "")
        if listing_id in active_listings:
            formats_by_listing[listing_id].append(supply_format)

    audit_rows: list[dict[str, Any]] = []
    for family in sorted(families, key=lambda row: str(row["family_code"])):
        family_id, code = str(family["family_id"]), str(family["family_code"])
        policy = policies_by_code.get(code)
        key_fields = tuple(str(value) for value in (policy or {}).get("pricing_key_attribute_codes") or ())
        family_models = [model for model in active_models.values() if str(model.get("family_id") or "") == family_id]
        listed_models = [model for model in family_models if str(model.get("material_model_id") or "") in listing_by_model]
        key_complete = [model for model in listed_models if _key_complete(values_by_model[str(model["material_model_id"])], key_fields)]
        priced = [model for model in key_complete if prices_by_model.get(str(model["material_model_id"]))]
        material_only = [model for model in priced if any(str(price.get("price_scope") or "") == "material_only" for price in prices_by_model[str(model["material_model_id"])])]
        package = [model for model in priced if any(str(price.get("price_scope") or "") == "retail_package" for price in prices_by_model[str(model["material_model_id"])])]
        default_specs = _OWNER_CONFIRMED_DEFAULTS.get(code, {})
        default_matches = [model for model in priced if _default_matches(values_by_model[str(model["material_model_id"])], default_specs)]
        listing_ids = {listing_by_model[str(model["material_model_id"])] for model in listed_models}
        row = {
            "family_code": code, "key_fields": key_fields, "default_mode": _default_mode(code, key_fields),
            "default_specs": default_specs, "format_policy": str((policy or {}).get("purchase_format_policy") or "missing"),
            "models": len(family_models), "listings": len(listed_models), "key_complete_models": len(key_complete),
            "active_price_models": len(priced), "material_only_models": len(material_only),
            "retail_package_models": len(package), "formats": sum(len(formats_by_listing[x]) for x in listing_ids),
            "default_match_models": len(default_matches),
        }
        row["gap"] = _gap(row)
        audit_rows.append(row)
    covered = sum(row["gap"] == "covered" for row in audit_rows)
    summary = f"{len(audit_rows)} active families, {covered} covered by canonical Israel positions"
    args.default_output.parent.mkdir(parents=True, exist_ok=True)
    args.coverage_output.parent.mkdir(parents=True, exist_ok=True)
    default_tmp = args.default_output.with_suffix(args.default_output.suffix + ".tmp")
    coverage_tmp = args.coverage_output.with_suffix(args.coverage_output.suffix + ".tmp")
    try:
        _write_default_matrix(default_tmp, audit_rows, summary=summary)
        _write_coverage_audit(coverage_tmp, audit_rows, summary=summary)
        default_tmp.replace(args.default_output)
        coverage_tmp.replace(args.coverage_output)
    finally:
        default_tmp.unlink(missing_ok=True)
        coverage_tmp.unlink(missing_ok=True)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
