#!/usr/bin/env python3
"""Build a deterministic Israel Reference canonical-name migration.

This generator reads the live canonical catalog and writes one reviewable SQL
migration.  It never changes Supabase itself.  The generated SQL updates only
the Global Model and the matching Israel Listing display names.  Legacy source
evidence, source prices and Pricing Key values are deliberately untouched.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client


DEFAULT_OUTPUT = ROOT / "db" / "sql" / "2026_10_14_canonicalize_israel_reference_names.sql"


_ENTITY_BY_FAMILY = {
    "aluminium_composite_panel": "Aluminium composite panel",
    "compact_laminate": "Compact laminate",
    "composite_sandwich_panel": "Composite sandwich panel",
    "decorative_film_foil": "Decorative film",
    "edge_banding": "Edge banding",
    "engineered_quartz_mineral_hybrid": "Engineered quartz slab",
    "faced_mdf": "MDF",
    "fibreboard_hardboard": "Hardboard",
    "glass": "Glass",
    "lightweight_sandwich_panel": "Lightweight sandwich panel",
    "melamine_faced_particleboard": "LDSP",
    "metal_flat_bar": "Metal flat bar",
    "metal_profile_angle_channel": "Metal profile",
    "metal_round_bar_rod_wire": "Metal round bar",
    "metal_tube": "Metal tube",
    "mirror": "Mirror",
    "natural_stone_slab": "Natural stone slab",
    "osb": "OSB",
    "particleboard": "Particleboard",
    "plywood": "Plywood",
    "plywood_special": "Plywood",
    "porcelain_ceramic_slab": "Porcelain slab",
    "sheet_metal": "Sheet metal",
    "sintered_ultra_compact_surface": "Sintered surface",
    "solid_surface": "Solid surface",
    "terrazzo_engineered_agglomerate": "Terrazzo",
    "timber_solid_wood_panel": "Solid timber panel",
    "vinyl_film": "Vinyl film",
    "wood_veneer": "Wood veneer",
}

# These records were seeded during the early catalogue experiment under MDF.
# Their own saved names prove a different Family.  The companion SQL migration
# corrects the Family without touching source evidence, prices or listings.
# Keeping the overlay here lets the generated name migration be reviewed and
# applied immediately after that correction, rather than producing a stale MDF
# name from the pre-correction live read.
_EXPERIMENTAL_FAMILY_CORRECTIONS: dict[str, tuple[str, Mapping[str, Any]]] = {
    "gcm_v1_exp_hardboard_raw_3_2": ("fibreboard_hardboard", {}),
    "gcm_v1_exp_laminated_solid_oak_20": ("timber_solid_wood_panel", {"species": "oak"}),
    "gcm_v1_exp_laminated_solid_oak_40": ("timber_solid_wood_panel", {"species": "oak"}),
    "gcm_v1_exp_laminated_solid_pine_18": ("timber_solid_wood_panel", {"species": "pine"}),
    "gcm_v1_exp_laminated_solid_pine_28": ("timber_solid_wood_panel", {"species": "pine"}),
    "gcm_v1_exp_mdf_laminate_17": ("faced_mdf", {}),
    "gcm_v1_exp_melamine_17": ("melamine_faced_particleboard", {}),
    "gcm_v1_exp_melamine_27": ("melamine_faced_particleboard", {}),
}

_SURFACE_BY_MODEL_PREFIX = (
    ("gcm_v1_mdf_faced_acrylic", "acrylic"),
    ("gcm_v1_mdf_faced_hpl_one_side", "hpl_one_sided"),
    ("gcm_v1_mdf_faced_hpl_two_sides", "hpl_two_sided"),
    ("gcm_v1_mdf_faced_lacquered_one_side", "lacquered_one_sided"),
    ("gcm_v1_mdf_faced_lacquered_two_sides", "lacquered_two_sided"),
    ("gcm_v1_mdf_faced_melamine_one_side", "melamine_one_sided"),
    ("gcm_v1_mdf_faced_melamine_two_sides", "melamine_two_sided"),
    ("gcm_v1_mdf_faced_pet", "pet"),
    ("gcm_v1_mdf_faced_veneer_one_side", "veneer_one_sided"),
    ("gcm_v1_mdf_faced_veneer_two_sides", "veneer_two_sided"),
)

_SECTION_PROFILE_DEFAULTS = {
    "square_tube": "square_tube_20x20",
    "rectangular_tube": "rectangular_tube_40x20",
    "round_tube": "round_tube_d20",
    "angle": "angle_30x30",
}

_DISPLAY_VALUES = {
    "surface": {
        "acrylic": "Acrylic",
        "hpl_one_sided": "HPL, one-sided",
        "hpl_two_sided": "HPL, two-sided",
        "lacquered_one_sided": "Lacquered, one-sided",
        "lacquered_two_sided": "Lacquered, two-sided",
        "laminated": "Laminated",
        "melamine_one_sided": "Melamine, one-sided",
        "melamine_two_sided": "Melamine, two-sided",
        "pet": "PET",
        "veneer_one_sided": "Veneer, one-sided",
        "veneer_two_sided": "Veneer, two-sided",
    },
    "section_profile": {
        "square_tube_20x20": "Square tube 20 × 20 mm",
        "rectangular_tube_40x20": "Rectangular tube 40 × 20 mm",
        "round_tube_d20": "Round tube Ø20 mm",
        "angle_30x30": "Angle 30 × 30 mm",
        "channel": "Channel",
        "beam": "Beam",
    },
}

def _rows(client: Any, table: str, fields: str, **filters: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = client.table(table).select(fields)
        for column, value in filters.items():
            query = query.eq(column, value)
        page = query.range(offset, offset + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        offset += 1000


def _number(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\.0+$", "", text)


def _title(value: Any) -> str:
    return " ".join(part.capitalize() for part in str(value or "").replace("_", " ").split())


def _entity(family: str, raw_name: str) -> str:
    folded = raw_name.casefold()
    if family == "mdf_hdf":
        return "HDF" if "hdf" in folded or "high-density fibreboard" in folded else "MDF"
    if family == "acrylic_pmma":
        return "Acrylic sheet"
    if family == "hpl_cpl":
        return "CPL" if folded.startswith("cpl") else "HPL"
    if family == "polycarbonate_petg_pvc_abs":
        for token, label in (("abs", "ABS sheet"), ("petg", "PETG sheet"), ("polycarbonate", "Polycarbonate sheet"), ("pvc foam", "PVC foam board"), ("pvc", "PVC sheet")):
            if folded.startswith(token):
                return label
    if family == "sheet_plastic":
        match = re.match(r"([^,]+?\s+sheet)\b", raw_name, flags=re.IGNORECASE)
        if match:
            return _title(match.group(1))
        return "Plastic sheet"
    return _ENTITY_BY_FAMILY.get(family, "")


def _key_value(code: str, facts: Mapping[str, Any]) -> str:
    value = facts.get(code)
    if code in _DISPLAY_VALUES and value in _DISPLAY_VALUES[code]:
        return _DISPLAY_VALUES[code][value]
    if code == "thickness":
        return f"{_number(value)} mm" if value not in (None, "") else ""
    if code == "width":
        return f"{_number(value)} mm" if value not in (None, "") else ""
    if code == "diameter":
        return f"Ø{_number(value)} mm" if value not in (None, "") else ""
    if code == "nominal_length":
        return f"{_number(value)} mm" if value not in (None, "") else ""
    if code == "alloy":
        return str(value or "").strip()
    if code == "width_thickness" and isinstance(value, Mapping):
        width, thickness = _number(value.get("width_mm")), _number(value.get("thickness_mm"))
        return f"{width} × {thickness} mm" if width and thickness else ""
    if code in {"metal_type", "section_profile", "species", "stone_type", "coating_system", "chemistry_product_type", "component_type", "packaging_type", "model_series"}:
        return _title(value)
    return _title(value)


def _clean_secondary(raw_name: str, entity: str, key_parts: Iterable[str], brand: str, family: str) -> str:
    """Remove only facts already rendered before the secondary segment.

    The catalog's previous name is structured source-proved content.  Do not
    discard a word merely because it looks generic: it can be a useful grade,
    form, construction or finish.  This operation therefore removes only an
    exact repeated Pricing Key or confirmed brand, then moves every remaining
    token after the standardized prefix.
    """
    text = raw_name
    # The entity has moved to its contractual first position, so an exact
    # repeated entity word need not survive in the tail.  This changes order,
    # not meaning.
    if entity:
        text = re.sub(re.escape(entity), "", text, flags=re.IGNORECASE)
    for part in key_parts:
        if part:
            text = re.sub(re.escape(part), "", text, flags=re.IGNORECASE)
            if part.casefold() == "aluminium":
                text = re.sub(r"aluminum", "", text, flags=re.IGNORECASE)
    if brand:
        text = re.sub(re.escape(brand), "", text, flags=re.IGNORECASE)
    # The early records called edge-glued solid timber "laminated solid wood".
    # This is the user-confirmed construction term, while the raw evidence is
    # retained separately and never overwritten by this display-name migration.
    if family == "timber_solid_wood_panel":
        text = re.sub(r"laminated\s+solid\s+wood\s+panel", "edge-glued", text, flags=re.IGNORECASE)
    if family == "melamine_faced_particleboard":
        text = re.sub(r"melamine-faced\s+particleboard", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmelamine\s+faced\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\s*melamine\s*,?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b1\s+side\b", "one-sided", text, flags=re.IGNORECASE)
        text = re.sub(r"\b2\s+sides\b", "two-sided", text, flags=re.IGNORECASE)
    if family == "plywood":
        text = re.sub(r"plastic\s+laminate\s+faced", "laminated", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text)
    return text.strip(" ,-")


def _name(*, family: str, raw_name: str, key_codes: Iterable[str], facts: Mapping[str, Any], brand: str) -> str:
    entity = _entity(family, raw_name)
    # Families without a structured Pricing Key still have their already
    # proven entity name. Rewording them would invent a structure absent from
    # their catalog data.
    if not entity:
        return raw_name
    key_parts = [part for code in key_codes if (part := _key_value(code, facts))]
    parts = [entity, *key_parts]
    if brand:
        parts.append(brand)
    # These Families have controlled name segments. Do not append a source-text
    # tail such as "faced", "substrate" or a repeated dimension.
    if family in {"metal_tube", "metal_profile_angle_channel"}:
        for code in ("alloy", "finish"):
            if part := _key_value(code, facts):
                parts.append(part)
        return ", ".join(parts)
    if family == "faced_mdf":
        if "surface" not in set(key_codes) and (surface := _key_value("surface", facts)):
            parts.append(surface)
        return ", ".join(parts)
    # A fact that is not a Pricing Key is a proven secondary attribute.  The
    # solid-timber Family prices by species, while thickness remains material
    # information that must continue to be displayed.
    rendered_secondary_facts: list[str] = []
    if "thickness" not in set(key_codes) and (thickness := _key_value("thickness", facts)):
        rendered_secondary_facts.append(thickness)
        parts.append(thickness)
    secondary = _clean_secondary(raw_name, entity, [*key_parts, *rendered_secondary_facts], brand, family)
    if secondary:
        parts.append(secondary)
    return ", ".join(parts)


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    client = get_supabase_client()
    families = _rows(client, "reference_material_families", "family_id,family_code", active=True)
    policies = _rows(client, "reference_material_family_pricing_policies", "family_id,pricing_key_attribute_codes", active=True)
    models = _rows(client, "reference_material_models", "material_model_id,family_id,material_model_code,canonical_name,brand_id", active=True)
    values = _rows(client, "reference_material_model_attribute_values", "material_model_id,attribute_code,attribute_value")
    brands = _rows(client, "reference_brands", "brand_id,canonical_name", active=True)

    family_by_id = {str(row["family_id"]): str(row["family_code"]) for row in families}
    policy_by_family_id = {str(row["family_id"]): tuple(row.get("pricing_key_attribute_codes") or ()) for row in policies}
    policy_by_family_code = {
        family_by_id[str(row["family_id"])]: tuple(row.get("pricing_key_attribute_codes") or ())
        for row in policies
    }
    brand_by_id = {str(row["brand_id"]): str(row["canonical_name"]) for row in brands}
    facts_by_model: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in values:
        facts_by_model[str(row["material_model_id"])][str(row["attribute_code"])] = row.get("attribute_value")

    generated: list[tuple[str, str]] = []
    for model in models:
        family_id = str(model["family_id"])
        family = family_by_id[family_id]
        facts = dict(facts_by_model[str(model["material_model_id"])])
        correction = _EXPERIMENTAL_FAMILY_CORRECTIONS.get(str(model["material_model_code"]))
        if correction:
            family, extra_facts = correction
            facts.update(extra_facts)
        model_code = str(model["material_model_code"])
        if family == "faced_mdf":
            for prefix, surface in _SURFACE_BY_MODEL_PREFIX:
                if model_code.startswith(prefix):
                    facts["surface"] = surface
                    break
            if model_code == "gcm_v1_exp_mdf_laminate_17":
                facts["surface"] = "laminated"
        if family in {"metal_tube", "metal_profile_angle_channel"}:
            section_profile = facts.get("section_profile")
            if section_profile in _SECTION_PROFILE_DEFAULTS:
                facts["section_profile"] = _SECTION_PROFILE_DEFAULTS[section_profile]
            if not facts.get("metal_type") and "brass_cuzn37" in model_code:
                facts["metal_type"] = "brass"
            alloy_match = re.match(
                r"^(?:Aluminium|Brass|Carbon steel|Copper|Galvanized steel|Stainless steel)\s+([^,]+),",
                str(model["canonical_name"]),
                flags=re.IGNORECASE,
            )
            if alloy_match:
                facts["alloy"] = alloy_match.group(1)
            for suffix, finish in (
                ("anodized", "anodized"),
                ("mill finish", "mill_finish"),
                ("powder-coat ready", "powder_coat_ready"),
                ("brushed", "brushed"),
                ("mirror polished", "mirror_polished"),
            ):
                if str(model["canonical_name"]).casefold().endswith(suffix):
                    facts["finish"] = finish
                    break
        name = _name(
            family=family,
            raw_name=str(model["canonical_name"]),
            key_codes=policy_by_family_code.get(family, policy_by_family_id.get(family_id, ())),
            facts=facts,
            brand=brand_by_id.get(str(model.get("brand_id") or ""), ""),
        )
        generated.append((str(model["material_model_code"]), name))

    duplicate_names = defaultdict(list)
    for code, name in generated:
        duplicate_names[name.casefold()].append(code)
    duplicated = {name: codes for name, codes in duplicate_names.items() if len(codes) > 1}
    if duplicated:
        sample = "; ".join(f"{name}: {', '.join(codes[:3])}" for name, codes in list(duplicated.items())[:5])
        raise SystemExit(f"refusing to generate ambiguous names ({len(duplicated)} duplicates): {sample}")

    lines = [
        "-- Israel Reference canonical-name migration.",
        "-- Generated by tools/build_israel_reference_name_migration.py from the live catalog.",
        "-- Updates only display names on Global Models and their IL Listings.",
        "-- Raw source evidence, prices, Family, Pricing Key and purchase formats are untouched.",
        "", "begin;", "",
        "create temporary table _canonical_name_seed (",
        "    material_model_code text primary key,",
        "    canonical_name text not null",
        ") on commit drop;", "",
        "insert into _canonical_name_seed (material_model_code, canonical_name) values",
    ]
    lines.extend(
        f"    ({_sql_literal(code)}, {_sql_literal(name)})" + ("," if index < len(generated) - 1 else ";")
        for index, (code, name) in enumerate(sorted(generated))
    )
    lines.extend([
        "", "update public.reference_material_models model", "set canonical_name = seed.canonical_name, updated_at = now()",
        "from _canonical_name_seed seed", "where model.material_model_code = seed.material_model_code", "  and model.active;", "",
        "update public.reference_market_material_listings listing", "set canonical_market_name = model.canonical_name, updated_at = now()",
        "from public.reference_material_models model", "where listing.market_code = 'IL'", "  and listing.active", "  and listing.material_model_id = model.material_model_id;", "",
        "do $$", "declare", "    mismatches integer;", "    missing integer;", "begin",
        "    select count(*) into missing", "    from _canonical_name_seed seed", "    left join public.reference_material_models model on model.material_model_code = seed.material_model_code and model.active", "    where model.material_model_id is null;",
        "    if missing <> 0 then", "        raise exception 'Canonical-name migration did not update % active models', missing;", "    end if;",
        "    select count(*) into mismatches", "    from public.reference_market_material_listings listing", "    join public.reference_material_models model on model.material_model_id = listing.material_model_id", "    where listing.market_code = 'IL' and listing.active and listing.canonical_market_name <> model.canonical_name;",
        "    if mismatches <> 0 then", "        raise exception 'Global Model and Israel Listing names diverged for % rows', mismatches;", "    end if;",
        "end $$;", "", "commit;",
    ])
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output} for {len(generated)} Global Models and Israel Listings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
