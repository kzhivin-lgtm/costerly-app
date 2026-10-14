#!/usr/bin/env python3
"""Generate the read-only Israel Reference Default and Coverage audit.

This is deliberately an audit, not a seed.  It turns the live catalog into
two reviewable documents before any identities, prices, or default rows are
written.  The Default Policy Matrix stops identity at the Family Pricing Key;
secondary attributes remain descriptive data and do not create catalog keys.
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
from use_cases.material_identity_status import (
    material_pricing_selection_key,
    pricing_policy_by_family_code,
)
from use_cases.price_source_taxonomy import catalog_v2_taxonomy_for_family


DEFAULT_OUTPUT = ROOT / "notes" / "ISRAEL_REFERENCE_DEFAULT_POLICY_MATRIX_3_17_4_1.md"
COVERAGE_OUTPUT = ROOT / "notes" / "ISRAEL_REFERENCE_COVERAGE_AUDIT_3_17_4_1.md"


# These are only decisions already made by the owner in the current catalog
# rebuild.  A blank specification is intentional: it means no default should
# be invented before the family has an approved, priced Israel identity.
_OWNER_CONFIRMED_DEFAULTS: dict[str, dict[str, Any]] = {
    "mdf_hdf": {"thickness_mm": 17},
    "faced_mdf": {"thickness_mm": 17},
    "particleboard": {"thickness_mm": 17},
    "melamine_faced_particleboard": {"thickness_mm": 17},
    "plywood": {"thickness_mm": 17},
    "osb": {"thickness_mm": 18},
    "fibreboard_hardboard": {"thickness_mm": 3},
    "compact_laminate": {"thickness_mm": 12},
    "wood_veneer": {"species": "oak", "secondary_thickness_mm": 0.6},
    "edge_banding": {"width_mm": 22, "thickness_mm": 0.8},
    "natural_stone_slab": {"stone_type": "marble", "thickness_mm": 20},
    "engineered_quartz_mineral_hybrid": {"thickness_mm": 20},
    "sintered_ultra_compact_surface": {"thickness_mm": 12},
    "porcelain_ceramic_slab": {"thickness_mm": 12},
    "solid_surface": {"thickness_mm": 12},
    "terrazzo_engineered_agglomerate": {"thickness_mm": 20},
    "paint_lacquer_stain": {"coating_system": "standard paint"},
    "powder_coating": {"coating_system": "standard semi-matte powder coating"},
    "metal_tube": {
        "metal_type": "carbon steel",
        "section_profile": "round tube Ø20 mm",
        "secondary_wall_thickness_mm": 1.5,
    },
    "metal_profile_angle_channel": {
        "metal_type": "carbon steel",
        "section_profile": "angle 30×30 mm",
        "secondary_wall_thickness_mm": 1.5,
    },
    "metal_flat_bar": {"metal_type": "carbon steel", "width_mm": 30, "thickness_mm": 1.5},
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


def _catalog_family(identity: Mapping[str, Any], policy_by_code: Mapping[str, Mapping[str, Any]]) -> str | None:
    attributes = dict(identity.get("price_attributes") or {})
    for field in ("global_family_code", "catalog_v2_family_code"):
        code = str(attributes.get(field) or "").strip()
        if code in policy_by_code:
            return code
    raw = str(attributes.get("material_family") or "").strip()
    if raw in policy_by_code:
        return raw
    taxonomy = catalog_v2_taxonomy_for_family(raw.replace("_", " "))
    projected = str((taxonomy or {}).get("family_code") or "").strip()
    return projected if projected in policy_by_code else None


def _display_specs(specs: Mapping[str, Any]) -> str:
    if not specs:
        return "pending"
    return ", ".join(f"{key}={value}" for key, value in specs.items())


def _default_mode(family_code: str, key_fields: Iterable[str]) -> str:
    if family_code.startswith("hardware_"):
        return "lowest compatible package candidate, Company first, then Israel"
    if family_code == "packaging_material":
        return "standard Israel candidate after package type is known"
    if family_code == "purchased_fabricated_component":
        return "no generic default, component type remains required"
    if not tuple(key_fields):
        return "standard Israel candidate, exact baseline pending"
    return "Israel-backed Pricing Key default"


def _gap(
    *,
    policy: Mapping[str, Any] | None,
    identities: int,
    active_prices: int,
    material_only_prices: int,
    key_complete_identities: int,
    default_variants: int,
    supply_formats: int,
    format_policy: str,
) -> str:
    if policy is None:
        return "missing Pricing Key policy"
    if identities == 0:
        return "no active Israel identity"
    if key_complete_identities == 0:
        return "identity has incomplete Pricing Key"
    if active_prices == 0:
        return "identity has no active Israel price"
    if material_only_prices == 0:
        return "only non-material price scopes"
    if format_policy != "not_required" and supply_formats == 0:
        return "no approved purchase format"
    if default_variants == 0:
        return "no active default anchor"
    return "covered"


def _write_default_matrix(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    generated_summary: str,
) -> None:
    body = [
        "# Israel Reference Default Policy Matrix, 3.17.4.1",
        "",
        "Status: proposed catalog-rebuild baseline. This document is generated from the live Israel Reference catalog plus owner-confirmed default decisions.",
        "",
        "## Contract",
        "",
        "- A catalog identity ends at the Family Pricing Key. Secondary attributes are descriptive and do not multiply identities.",
        "- A Family Default is allowed only after the family is proven. It fills absent Pricing Key facts, then the normal Company-first, Israel-second resolver runs.",
        "- A generic hardware default means the lowest compatible active package candidate, not an invented component specification.",
        "- Missing family stays review-visible. A fully specified uncommon item absent from both catalogs is an Assumption Fallback and a Catalog Gap, never a Family Default.",
        "",
        f"Live audit summary: {generated_summary}",
        "",
        "## Family matrix",
        "",
        "| Family | Pricing Key | Default mode | Owner-confirmed baseline | Purchase format | Live status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        body.append(
            "| {family} | {key} | {mode} | {baseline} | {format} | {gap} |".format(
                family=row["family_code"],
                key=", ".join(row["key_fields"]) or "none",
                mode=row["default_mode"],
                baseline=_display_specs(row["default_specs"]),
                format=row["format_policy"],
                gap=row["gap"],
            )
        )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _write_coverage_audit(path: Path, rows: list[dict[str, Any]], *, generated_summary: str) -> None:
    counts = Counter(row["gap"] for row in rows)
    body = [
        "# Israel Reference Coverage Audit, 3.17.4.1",
        "",
        "Status: read-only snapshot from the live Israel Reference catalog. Regenerate with `tools/audit_israel_reference_catalog.py` before each seed batch.",
        "",
        f"Summary: {generated_summary}",
        "",
        "## Gap totals",
        "",
    ]
    body.extend(f"- {gap}: {count}" for gap, count in sorted(counts.items()))
    body.extend([
        "",
        "## Family coverage",
        "",
        "| Family | Active identities | Pricing-Key complete | Any active price | Material-only price | Formats | Active default | Gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in rows:
        body.append(
            "| {family_code} | {identities} | {key_complete_identities} | {active_prices} | {material_only_prices} | {supply_formats} | {default_variants} | {gap} |".format(**row)
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
    identities = _rows(client, "reference_material_pricing_identities", filters={"market_code": "IL", "status": "active"})
    prices = _rows(client, "market_material_pricing_identity_prices", filters={"status": "active"})
    formats = _rows(client, "reference_material_family_supply_formats", filters={"active": True})
    defaults = _rows(client, "reference_material_family_default_variants", filters={"active": True})

    policy_by_code = pricing_policy_by_family_code(policies, families=families)
    family_by_id = {str(row["family_id"]): str(row["family_code"]) for row in families}
    identities_by_family: dict[str, set[str]] = defaultdict(set)
    for identity in identities:
        family = _catalog_family(identity, policy_by_code)
        if family:
            identities_by_family[family].add(str(identity["pricing_identity_id"]))
    active_prices_by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for price in prices:
        active_prices_by_identity[str(price["pricing_identity_id"])].append(price)
    formats_by_family = Counter(family_by_id.get(str(row.get("family_id") or "")) for row in formats)
    defaults_by_family = Counter(family_by_id.get(str(row.get("family_id") or "")) for row in defaults)

    audit_rows: list[dict[str, Any]] = []
    for family in sorted(families, key=lambda row: str(row["family_code"])):
        code = str(family["family_code"])
        policy = policy_by_code.get(code)
        key_fields = tuple(str(value) for value in (policy or {}).get("pricing_key_attribute_codes") or ())
        identity_ids = identities_by_family.get(code, set())
        key_complete_identity_ids: set[str] = set()
        for identity in identities:
            identity_id = str(identity.get("pricing_identity_id") or "")
            if identity_id not in identity_ids:
                continue
            specifications = dict(identity.get("price_attributes") or {})
            specifications["material_family"] = code
            if material_pricing_selection_key(
                material_family=code,
                specifications=specifications,
                pricing_policies=policy_by_code,
            ) is not None:
                key_complete_identity_ids.add(identity_id)
        scoped_prices = [price for identity_id in identity_ids for price in active_prices_by_identity.get(identity_id, ())]
        material_only = [price for price in scoped_prices if str(price.get("price_scope") or "") == "material_only"]
        format_policy = str((policy or {}).get("purchase_format_policy") or "missing")
        audit_rows.append({
            "family_code": code,
            "key_fields": key_fields,
            "default_mode": _default_mode(code, key_fields),
            "default_specs": _OWNER_CONFIRMED_DEFAULTS.get(code, {}),
            "format_policy": format_policy,
            "identities": len(identity_ids),
            "active_prices": len(scoped_prices),
            "material_only_prices": len(material_only),
            "key_complete_identities": len(key_complete_identity_ids),
            "supply_formats": formats_by_family.get(code, 0),
            "default_variants": defaults_by_family.get(code, 0),
            "gap": _gap(
                policy=policy,
                identities=len(identity_ids),
                active_prices=len(scoped_prices),
                material_only_prices=len(material_only),
                key_complete_identities=len(key_complete_identity_ids),
                default_variants=defaults_by_family.get(code, 0),
                supply_formats=formats_by_family.get(code, 0),
                format_policy=format_policy,
            ),
        })

    covered = sum(row["gap"] == "covered" for row in audit_rows)
    summary = f"{len(audit_rows)} active families, {covered} fully covered under the current default-anchor model"
    args.default_output.parent.mkdir(parents=True, exist_ok=True)
    args.coverage_output.parent.mkdir(parents=True, exist_ok=True)
    default_tmp = args.default_output.with_suffix(args.default_output.suffix + ".tmp")
    coverage_tmp = args.coverage_output.with_suffix(args.coverage_output.suffix + ".tmp")
    try:
        _write_default_matrix(default_tmp, audit_rows, generated_summary=summary)
        _write_coverage_audit(coverage_tmp, audit_rows, generated_summary=summary)
        default_tmp.replace(args.default_output)
        coverage_tmp.replace(args.coverage_output)
    finally:
        default_tmp.unlink(missing_ok=True)
        coverage_tmp.unlink(missing_ok=True)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
