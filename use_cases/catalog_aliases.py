"""Read the shared aliases used to interpret incoming material text.

Aliases are catalog data, not agent prompts and not a second material catalog.
They establish only a Family or the role/value of a Pricing Key fact.  Material
selection remains the responsibility of Material Resolver.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence


def _rows(query: Any) -> list[dict[str, Any]]:
    response = query.execute()
    return [dict(row) for row in (response.data or []) if isinstance(row, Mapping)]


def build_estimation_alias_context(
    *,
    source_family_to_catalog_family: Mapping[str, str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]],
    family_rows: Sequence[Mapping[str, Any]],
    family_alias_rows: Sequence[Mapping[str, Any]],
    pricing_key_alias_rows: Sequence[Mapping[str, Any]],
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

    result: dict[str, dict[str, object]] = {}
    for source_family, catalog_family in sorted(source_family_to_catalog_family.items()):
        family_id = family_id_by_code.get(str(catalog_family))
        if not family_id:
            continue
        result[source_family] = {
            "catalog_family": str(catalog_family),
            "family_aliases": aliases_by_family_id.get(family_id, []),
            "pricing_key_aliases": {
                field: aliases_by_family_field.get((family_id, str(field)), [])
                for field in pricing_key_fields_by_family.get(source_family, ())
            },
        }
    return result


def load_estimation_alias_context(
    client: Any,
    *,
    source_family_to_catalog_family: Mapping[str, str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, object]]:
    """Load the shared, active aliases required by one Estimation batch."""
    family_codes = sorted({
        str(code).strip()
        for code in source_family_to_catalog_family.values()
        if str(code).strip()
    })
    if not family_codes:
        return {}
    family_rows = _rows(
        client.table("reference_material_families")
        .select("family_id,family_code")
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
    return build_estimation_alias_context(
        source_family_to_catalog_family=source_family_to_catalog_family,
        pricing_key_fields_by_family=pricing_key_fields_by_family,
        family_rows=family_rows,
        family_alias_rows=family_alias_rows,
        pricing_key_alias_rows=pricing_key_alias_rows,
    )
