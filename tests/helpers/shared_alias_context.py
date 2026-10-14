"""Build test recognition data from the SQL seeds used by the catalog.

This module deliberately does not reproduce a Python synonym dictionary.  It
reads the same seed files that populate the unified alias tables, then builds
the bounded context consumed by Price Source tests.
"""

from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import re

from use_cases.catalog_aliases import PriceSourceAliasContext
from use_cases.material_identity_resolution import normalize_material_phrase


_ROOT = Path(__file__).resolve().parents[2]
_SQL = _ROOT / "db" / "sql"


def _seed_rows(filename: str, cte: str, *, occurrence: int = -1) -> list[tuple[str, ...]]:
    text = (_SQL / filename).read_text(encoding="utf-8")
    starts = list(re.finditer(
        rf"with\s+{re.escape(cte)}\s*\([^)]*\)\s+as\s*\(\s*values\s*",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ))
    if not starts:
        raise AssertionError(f"Seed CTE {cte!r} is missing from {filename}")
    start = starts[occurrence].end()
    end = re.search(
        r"\)\s*(?:,\s*[a-z_][a-z0-9_]*\s*\(|\ninsert\s+into)",
        text[start:],
        flags=re.IGNORECASE,
    )
    if not end:
        raise AssertionError(f"Seed CTE {cte!r} does not terminate before an insert in {filename}")
    values = text[start:start + end.start()]
    rows: list[tuple[str, ...]] = []
    for match in re.finditer(r"\(([^\n()]*)\)", values):
        fields: list[str] = []
        value = ""
        quoted = False
        index = 0
        row = match.group(1)
        while index < len(row):
            character = row[index]
            if character == "'":
                if quoted and index + 1 < len(row) and row[index + 1] == "'":
                    value += "'"
                    index += 2
                    continue
                quoted = not quoted
            elif character == "," and not quoted:
                fields.append(value.strip())
                value = ""
            else:
                value += character
            index += 1
        fields.append(value.strip())
        rows.append(tuple(fields))
    return rows


def _families_for_fact(fact_field: str, family_codes: set[str]) -> set[str]:
    if fact_field in {"metal_type", "section_profile", "wall_thickness"}:
        return {code for code in family_codes if code.startswith("metal_") or code == "sheet_metal"}
    if fact_field == "species":
        return {"timber_solid_wood_panel", "wood_veneer", "plywood"} & family_codes
    if fact_field == "coating_system":
        return {
            "powder_coating", "paint_lacquer_stain", "primer", "filler_hardener_thinner",
        } & family_codes
    if fact_field == "construction":
        return {
            "mdf_hdf", "faced_mdf", "particleboard", "melamine_faced_particleboard",
            "plywood", "plywood_special", "osb", "fibreboard_hardboard",
            "lightweight_sandwich_panel", "hpl_cpl", "compact_laminate",
        } & family_codes
    return family_codes


@lru_cache(maxsize=1)
def shared_alias_context() -> PriceSourceAliasContext:
    family_rows = [
        *_seed_rows("2026_10_14_shared_material_aliases_seed.sql", "family_alias_seed"),
        *_seed_rows("2026_10_14_shared_legacy_aliases_seed.sql", "family_alias_seed"),
        *_seed_rows("2026_10_14_shared_legacy_aliases_seed.sql", "multilingual_family_alias_seed"),
    ]
    family_aliases: dict[str, list[str]] = defaultdict(list)
    for family_code, _language, alias in family_rows:
        if alias not in family_aliases[family_code]:
            family_aliases[family_code].append(alias)
    family_codes = set(family_aliases)
    family_names = {
        code: name
        for code, name, *_rest in _seed_rows(
            "2026_10_11_catalog_global_family_seed.sql", "family_seed"
        )
    }

    ambiguous = frozenset(
        normalize_material_phrase(row[0])
        for row in _seed_rows("2026_10_14_shared_legacy_aliases_seed.sql", "ambiguous_seed")
    )

    attribute_values: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for filename, cte in (
        ("2026_10_14_shared_material_aliases_seed.sql", "value_alias_seed"),
        ("2026_10_14_shared_legacy_aliases_seed.sql", "attribute_value_alias_seed"),
    ):
        for fact_field, canonical_value, _language, alias in _seed_rows(filename, cte):
            for family_code in _families_for_fact(fact_field, family_codes):
                if alias not in attribute_values[family_code][fact_field][canonical_value]:
                    attribute_values[family_code][fact_field][canonical_value].append(alias)

    brand_names = {
        code: name
        for code, name in _seed_rows("2026_10_14_shared_brand_aliases_seed.sql", "brand_seed")
    }
    brand_aliases: dict[str, str] = {}
    for cte in ("brand_alias_seed", "russian_brand_alias_seed"):
        for row in _seed_rows("2026_10_14_shared_brand_aliases_seed.sql", cte):
            code, alias = row[0], row[-1]
            if code in brand_names:
                brand_aliases[normalize_material_phrase(alias)] = brand_names[code]

    system_rows = _seed_rows(
        "2026_10_11_catalog_hardware_brand_product_system_seed.sql",
        "product_system_seed",
    )
    systems = {
        row[0]: (row[4], brand_names.get(row[1], row[1]), row[2])
        for row in system_rows
        if len(row) >= 5 and row[1] in brand_names
    }
    product_system_aliases: dict[str, tuple[str, str]] = {}
    for system_code, alias in _seed_rows(
        "2026_10_11_catalog_hardware_brand_product_system_seed.sql",
        "product_system_alias_seed",
    ):
        if system_code in systems:
            product_system_aliases[normalize_material_phrase(alias)] = systems[system_code]

    operation_aliases: dict[str, dict[str, object]] = {}
    for code, _language, alias, service_only in _seed_rows(
        "2026_10_14_shared_legacy_aliases_seed.sql", "operation_alias_seed",
    ):
        operation_aliases[normalize_material_phrase(alias)] = {
            "operation_code": code,
            "service_only": service_only.casefold() == "true",
        }

    measurement_unit_aliases: dict[str, dict[str, object]] = {}
    for code, dimension, factor, _language, alias in _seed_rows(
        "2026_10_14_shared_measurement_unit_aliases_seed.sql", "unit_alias_seed",
    ):
        measurement_unit_aliases[normalize_material_phrase(alias)] = {
            "unit_code": code,
            "dimension_code": dimension,
            "conversion_factor": float(factor),
        }
    return PriceSourceAliasContext(
        family_aliases={code: tuple(aliases) for code, aliases in family_aliases.items()},
        family_categories={code: "catalog" for code in family_aliases},
        ambiguous_family_aliases=ambiguous,
        attribute_value_aliases={
            code: {field: {value: tuple(aliases) for value, aliases in values.items()} for field, values in fields.items()}
            for code, fields in attribute_values.items()
        },
        brand_aliases=brand_aliases,
        product_system_aliases=product_system_aliases,
        operation_aliases=operation_aliases,
        measurement_unit_aliases=measurement_unit_aliases,
        family_names=family_names,
    )
