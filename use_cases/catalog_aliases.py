"""Read the shared aliases used to interpret incoming material text.

Aliases are catalog data, not agent prompts and not a second material catalog.
They establish only a Family or the role/value of a Pricing Key fact.  Material
selection remains the responsibility of Material Resolver.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from use_cases.material_identity_resolution import normalize_material_phrase


@dataclass(frozen=True)
class PriceSourceAliasContext:
    """One bounded read of catalog aliases for one Price Source cycle.

    This is deliberately data only.  It contains no price, purchase format or
    Company Catalog offer, and it makes no Family selection on its own.
    """

    family_aliases: Mapping[str, tuple[str, ...]]
    family_categories: Mapping[str, str]
    ambiguous_family_aliases: frozenset[str]
    attribute_value_aliases: Mapping[str, Mapping[str, Mapping[str, tuple[str, ...]]]]
    brand_aliases: Mapping[str, str]
    product_system_aliases: Mapping[str, tuple[str, str, str]]
    operation_aliases: Mapping[str, Mapping[str, object]]
    measurement_unit_aliases: Mapping[str, Mapping[str, object]]
    family_names: Mapping[str, str] = field(default_factory=dict)


def normalize_measurement_unit(
    value: object,
    *,
    alias_context: PriceSourceAliasContext | None,
) -> str:
    """Resolve one source unit through the shared catalog aliases.

    Unit wording is input vocabulary, just like Family wording.  The caller
    receives only the catalog's canonical calculation unit, never a locally
    maintained synonym.  An empty context intentionally cannot guess.
    """
    if alias_context is None:
        return ""
    payload = alias_context.measurement_unit_aliases.get(normalize_material_phrase(value))
    return str((payload or {}).get("unit_code") or "")


def _rows(query: Any) -> list[dict[str, Any]]:
    response = query.execute()
    return [dict(row) for row in (response.data or []) if isinstance(row, Mapping)]


def build_estimation_alias_context(
    *,
    family_codes: Sequence[str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]],
    family_rows: Sequence[Mapping[str, Any]],
    family_alias_rows: Sequence[Mapping[str, Any]],
    pricing_key_alias_rows: Sequence[Mapping[str, Any]],
    pricing_key_value_alias_rows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, dict[str, object]]:
    """Build the bounded alias context for one Estimation V3 request.

    The caller supplies only the Families and Pricing Key fields permitted for
    the current Resolver batch.  An alias from another Family can therefore
    never expand the agent's material vocabulary.
    """
    family_id_by_code = {
        str(row.get("family_code") or ""): str(row.get("family_id") or "")
        for row in family_rows
        if row.get("family_code") and row.get("family_id")
    }
    aliases_by_family_id: dict[str, list[str]] = defaultdict(list)
    for row in family_alias_rows:
        family_id = str(row.get("family_id") or "")
        alias = str(row.get("alias_text") or "").strip()
        if family_id and alias and alias not in aliases_by_family_id[family_id]:
            aliases_by_family_id[family_id].append(alias)
    aliases_by_family_field: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in pricing_key_alias_rows:
        family_id = str(row.get("family_id") or "")
        field = str(row.get("fact_field") or "")
        alias = str(row.get("alias_text") or "").strip()
        key = (family_id, field)
        if family_id and field and alias and alias not in aliases_by_family_field[key]:
            aliases_by_family_field[key].append(alias)
    value_aliases_by_family_field: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in pricing_key_value_alias_rows:
        family_id = str(row.get("family_id") or "")
        field = str(row.get("fact_field") or "")
        canonical_value = str(row.get("canonical_value") or "").strip()
        alias = str(row.get("alias_text") or "").strip()
        if not (family_id and field and canonical_value and alias):
            continue
        aliases = value_aliases_by_family_field[(family_id, field)][canonical_value]
        if alias not in aliases:
            aliases.append(alias)

    result: dict[str, dict[str, object]] = {}
    for family_code in sorted({str(code).strip() for code in family_codes if str(code).strip()}):
        family_id = family_id_by_code.get(family_code)
        if not family_id:
            continue
        context: dict[str, object] = {
            "catalog_family": family_code,
            "family_aliases": aliases_by_family_id.get(family_id, []),
            "pricing_key_aliases": {
                field: aliases_by_family_field.get((family_id, str(field)), [])
                for field in pricing_key_fields_by_family.get(family_code, ())
            },
        }
        value_aliases = {
            field: dict(value_aliases_by_family_field.get((family_id, str(field)), {}))
            for field in pricing_key_fields_by_family.get(family_code, ())
            if value_aliases_by_family_field.get((family_id, str(field)), {})
        }
        if value_aliases:
            context["pricing_key_value_aliases"] = value_aliases
        result[family_code] = context
    return result


def load_estimation_alias_context(
    client: Any,
    *,
    family_codes: Sequence[str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, object]]:
    """Load the shared, active aliases required by one Estimation batch."""
    family_codes = sorted({
        str(code).strip()
        for code in family_codes
        if str(code).strip()
    })
    if not family_codes:
        return {}
    family_rows = _rows(
        client.table("reference_material_families")
        .select("family_id,family_code,family_name")
        .eq("active", True)
        .in_("family_code", family_codes)
    )
    family_ids = sorted({str(row["family_id"]) for row in family_rows if row.get("family_id")})
    if not family_ids:
        return {}
    family_alias_rows = _rows(
        client.table("reference_material_family_aliases")
        .select("family_id,alias_text")
        .eq("active", True)
        .in_("family_id", family_ids)
    )
    pricing_key_alias_rows = _rows(
        client.table("reference_material_pricing_key_aliases")
        .select("family_id,fact_field,alias_text")
        .eq("active", True)
        .in_("family_id", family_ids)
    )
    pricing_key_value_alias_rows = _rows(
        client.table("reference_material_pricing_key_value_aliases")
        .select("family_id,fact_field,canonical_value,alias_text")
        .eq("active", True)
        .in_("family_id", family_ids)
    )
    return build_estimation_alias_context(
        family_codes=family_codes,
        pricing_key_fields_by_family=pricing_key_fields_by_family,
        family_rows=family_rows,
        family_alias_rows=family_alias_rows,
        pricing_key_alias_rows=pricing_key_alias_rows,
        pricing_key_value_alias_rows=pricing_key_value_alias_rows,
    )


def canonicalize_estimation_pricing_key_values(
    facts: Mapping[str, Any],
    *,
    family_alias_context: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Map only exact catalog value aliases after V3 has selected a Family.

    The extraction agent may preserve a source spelling, for example ``carbon
    steel``.  This deterministic step never adds a missing fact and never
    changes Family.  It gives Material Resolver the same canonical Pricing Key
    vocabulary that Price Source uses.
    """
    normalized = dict(facts)
    materials: list[Any] = []
    for raw in facts.get("materials") or ():
        if not isinstance(raw, Mapping):
            materials.append(raw)
            continue
        material = dict(raw)
        family = str(material.get("family") or "")
        aliases_by_field = dict(
            (family_alias_context.get(family) or {}).get("pricing_key_value_aliases") or {}
        )
        specification = dict(material.get("specification") or {})
        for field, canonical_values in aliases_by_field.items():
            if field not in specification:
                continue
            canonical_by_alias = {
                normalize_material_phrase(alias): canonical_value
                for canonical_value, aliases in dict(canonical_values or {}).items()
                for alias in tuple(aliases or ()) + (canonical_value,)
            }
            canonical = canonical_by_alias.get(normalize_material_phrase(specification[field]))
            if canonical:
                specification[field] = canonical
        material["specification"] = specification
        materials.append(material)
    normalized["materials"] = materials
    return normalized


def build_price_source_alias_context(
    *,
    family_rows: Sequence[Mapping[str, Any]],
    family_alias_rows: Sequence[Mapping[str, Any]],
    ambiguous_family_alias_rows: Sequence[Mapping[str, Any]],
    attribute_value_alias_rows: Sequence[Mapping[str, Any]],
    brand_rows: Sequence[Mapping[str, Any]],
    brand_alias_rows: Sequence[Mapping[str, Any]],
    product_system_rows: Sequence[Mapping[str, Any]],
    product_system_alias_rows: Sequence[Mapping[str, Any]],
    operation_rows: Sequence[Mapping[str, Any]],
    operation_alias_rows: Sequence[Mapping[str, Any]],
    measurement_unit_alias_rows: Sequence[Mapping[str, Any]],
) -> PriceSourceAliasContext:
    """Build Price Source recognition data from persistent catalog rows only."""
    family_code_by_id = {
        str(row.get("family_id")): str(row.get("family_code"))
        for row in family_rows
        if row.get("family_id") and row.get("family_code")
    }
    family_categories = {
        str(row.get("family_code")): str(row.get("category_name"))
        for row in family_rows
        if row.get("family_code") and row.get("category_name")
    }
    family_names = {
        str(row.get("family_code")): str(row.get("family_name"))
        for row in family_rows
        if row.get("family_code") and row.get("family_name")
    }
    family_aliases: dict[str, list[str]] = defaultdict(list)
    for row in family_alias_rows:
        family_code = family_code_by_id.get(str(row.get("family_id") or ""))
        alias = str(row.get("alias_text") or "").strip()
        if family_code and alias and alias not in family_aliases[family_code]:
            family_aliases[family_code].append(alias)

    attribute_values: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for row in attribute_value_alias_rows:
        family_code = family_code_by_id.get(str(row.get("family_id") or ""))
        field = str(row.get("fact_field") or "").strip()
        value = str(row.get("canonical_value") or "").strip()
        alias = str(row.get("alias_text") or "").strip()
        if family_code and field and value and alias and alias not in attribute_values[family_code][field][value]:
            attribute_values[family_code][field][value].append(alias)

    brand_name_by_id = {
        str(row.get("brand_id")): str(row.get("canonical_name"))
        for row in brand_rows
        if row.get("brand_id") and row.get("canonical_name")
    }
    brand_aliases = {
        str(row.get("alias_key")): brand_name_by_id[str(row.get("brand_id"))]
        for row in brand_alias_rows
        if str(row.get("alias_key") or "") and str(row.get("brand_id") or "") in brand_name_by_id
    }

    system_by_id = {
        str(row.get("product_system_id")): (
            str(row.get("canonical_name")), str(row.get("brand_name")),
            family_code_by_id.get(str(row.get("family_id") or ""), ""),
        )
        for row in product_system_rows
        if row.get("product_system_id") and row.get("canonical_name") and row.get("brand_name")
        and family_code_by_id.get(str(row.get("family_id") or ""))
    }
    product_system_aliases = {
        str(row.get("alias_key")): system_by_id[str(row.get("product_system_id"))]
        for row in product_system_alias_rows
        if str(row.get("alias_key") or "") and str(row.get("product_system_id") or "") in system_by_id
    }

    operation_code_by_id = {
        str(row.get("operation_id")): str(row.get("operation_code"))
        for row in operation_rows
        if row.get("operation_id") and row.get("operation_code")
    }
    operation_aliases = {
        str(row.get("alias_key")): {
            "operation_code": operation_code_by_id[str(row.get("operation_id"))],
            "service_only": bool(row.get("service_only")),
        }
        for row in operation_alias_rows
        if str(row.get("alias_key") or "") and str(row.get("operation_id") or "") in operation_code_by_id
    }
    measurement_units = {
        normalize_material_phrase(row.get("alias_key")): {
            "unit_code": str(row.get("unit_code")),
            "dimension_code": str(row.get("dimension_code")),
            "conversion_factor": row.get("conversion_factor"),
        }
        for row in measurement_unit_alias_rows
        if str(row.get("alias_key") or "") and row.get("unit_code")
    }
    return PriceSourceAliasContext(
        family_aliases={code: tuple(aliases) for code, aliases in family_aliases.items()},
        family_categories=family_categories,
        family_names=family_names,
        ambiguous_family_aliases=frozenset(
            str(row.get("alias_key")) for row in ambiguous_family_alias_rows if row.get("alias_key")
        ),
        attribute_value_aliases={
            family_code: {
                field: {value: tuple(aliases) for value, aliases in values.items()}
                for field, values in fields.items()
            }
            for family_code, fields in attribute_values.items()
        },
        brand_aliases=brand_aliases,
        product_system_aliases=product_system_aliases,
        operation_aliases=operation_aliases,
        measurement_unit_aliases=measurement_units,
    )


def load_price_source_alias_context(client: Any) -> PriceSourceAliasContext:
    """Read the complete Price Source alias context from the catalog once.

    The Price Source cycle supplies this immutable context to every row, so it
    performs no per-row catalog round trips and has no fallback to a Python
    synonym list.
    """
    family_rows = _rows(
        client.table("reference_material_families")
        .select("family_id,family_code,family_name,category_id")
        .eq("active", True)
    )
    category_rows = _rows(
        client.table("reference_material_family_categories")
        .select("category_id,category_name")
        .eq("active", True)
    )
    category_name_by_id = {
        str(row.get("category_id")): str(row.get("category_name"))
        for row in category_rows if row.get("category_id") and row.get("category_name")
    }
    family_rows = [
        {**row, "category_name": category_name_by_id.get(str(row.get("category_id") or ""), "")}
        for row in family_rows
    ]
    family_ids = sorted({str(row["family_id"]) for row in family_rows if row.get("family_id")})
    family_alias_rows = _rows(
        client.table("reference_material_family_aliases")
        .select("family_id,alias_text")
        .eq("active", True)
        .in_("family_id", family_ids)
    ) if family_ids else []
    ambiguous_family_alias_rows = _rows(
        client.table("reference_material_family_ambiguous_aliases")
        .select("alias_key")
        .eq("active", True)
    )
    attribute_value_alias_rows = _rows(
        client.table("reference_material_pricing_key_value_aliases")
        .select("family_id,fact_field,canonical_value,alias_text")
        .eq("active", True)
        .in_("family_id", family_ids)
    ) if family_ids else []
    brand_rows = _rows(
        client.table("reference_brands")
        .select("brand_id,canonical_name")
        .eq("active", True)
    )
    brand_ids = sorted({str(row["brand_id"]) for row in brand_rows if row.get("brand_id")})
    brand_alias_rows = _rows(
        client.table("reference_brand_aliases")
        .select("brand_id,alias_key")
        .eq("active", True)
        .in_("brand_id", brand_ids)
    ) if brand_ids else []
    product_system_rows = _rows(
        client.table("reference_brand_product_systems")
        .select("product_system_id,canonical_name,brand_id,family_id")
        .eq("active", True)
    )
    brand_name_by_id = {
        str(row.get("brand_id")): str(row.get("canonical_name"))
        for row in brand_rows if row.get("brand_id") and row.get("canonical_name")
    }
    product_system_rows = [
        {**row, "brand_name": brand_name_by_id.get(str(row.get("brand_id") or ""), "")}
        for row in product_system_rows
    ]
    system_ids = sorted({str(row["product_system_id"]) for row in product_system_rows if row.get("product_system_id")})
    product_system_alias_rows = _rows(
        client.table("reference_brand_product_system_aliases")
        .select("product_system_id,alias_key")
        .eq("active", True)
        .in_("product_system_id", system_ids)
    ) if system_ids else []
    operation_rows = _rows(
        client.table("reference_operations")
        .select("operation_id,operation_code")
        .eq("active", True)
    )
    operation_ids = sorted({str(row["operation_id"]) for row in operation_rows if row.get("operation_id")})
    operation_alias_rows = _rows(
        client.table("reference_operation_aliases")
        .select("operation_id,alias_key,service_only")
        .eq("active", True)
        .in_("operation_id", operation_ids)
    ) if operation_ids else []
    measurement_unit_alias_rows = _rows(
        client.table("reference_measurement_unit_aliases")
        .select("alias_key,unit_code,dimension_code,conversion_factor")
        .eq("active", True)
    )
    return build_price_source_alias_context(
        family_rows=family_rows,
        family_alias_rows=family_alias_rows,
        ambiguous_family_alias_rows=ambiguous_family_alias_rows,
        attribute_value_alias_rows=attribute_value_alias_rows,
        brand_rows=brand_rows,
        brand_alias_rows=brand_alias_rows,
        product_system_rows=product_system_rows,
        product_system_alias_rows=product_system_alias_rows,
        operation_rows=operation_rows,
        operation_alias_rows=operation_alias_rows,
        measurement_unit_alias_rows=measurement_unit_alias_rows,
    )
