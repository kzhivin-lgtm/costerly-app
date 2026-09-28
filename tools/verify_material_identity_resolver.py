from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client  # noqa: E402
from use_cases.material_identity_resolution import (  # noqa: E402
    normalize_material_phrase,
    normalize_supplier_sku,
    resolve_material_identity,
)


def main() -> None:
    client = get_supabase_client()
    materials = (
        client.table("reference_materials")
        .select(
            "material_id,category_code,canonical_name,base_unit,specifications,active"
        )
        .eq("active", True)
        .execute()
        .data
        or []
    )
    aliases = (
        client.table("reference_material_aliases")
        .select(
            "material_id,market_code,alias_text,alias_kind,exact_identity,active"
        )
        .eq("market_code", "IL")
        .eq("active", True)
        .execute()
        .data
        or []
    )
    offers = (
        client.table("market_material_offers")
        .select("material_id,market_code,supplier_name,supplier_sku")
        .eq("market_code", "IL")
        .execute()
        .data
        or []
    )

    exact_groups: dict[str, set[str]] = defaultdict(set)
    exact_phrases: dict[str, str] = {}
    for alias in aliases:
        if alias.get("exact_identity") is not True:
            continue
        key = normalize_material_phrase(alias.get("alias_text"))
        exact_groups[key].add(str(alias["material_id"]))
        exact_phrases[key] = str(alias["alias_text"])

    exact_unique = 0
    exact_correct = 0
    exact_collision_false_resolutions = 0
    for key, material_ids in exact_groups.items():
        if len(material_ids) != 1:
            collision_result = resolve_material_identity(
                phrase=exact_phrases[key],
                market_code="IL",
                materials=materials,
                reference_aliases=aliases,
                market_offers=offers,
            )
            exact_collision_false_resolutions += collision_result.status == "resolved"
            continue
        exact_unique += 1
        expected = next(iter(material_ids))
        result = resolve_material_identity(
            phrase=exact_phrases[key],
            market_code="IL",
            materials=materials,
            reference_aliases=aliases,
            market_offers=offers,
        )
        exact_correct += result.selected_material_id == expected

    sku_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    sku_inputs: dict[tuple[str, str], tuple[str, str]] = {}
    for offer in offers:
        if not offer.get("supplier_name") or not offer.get("supplier_sku"):
            continue
        key = (
            normalize_material_phrase(offer["supplier_name"]),
            normalize_supplier_sku(offer["supplier_sku"]),
        )
        sku_groups[key].add(str(offer["material_id"]))
        sku_inputs[key] = (str(offer["supplier_name"]), str(offer["supplier_sku"]))

    sku_unique = 0
    sku_correct = 0
    sku_collision_false_resolutions = 0
    for key, material_ids in sku_groups.items():
        if len(material_ids) != 1:
            supplier_name, supplier_sku = sku_inputs[key]
            collision_result = resolve_material_identity(
                phrase="supplier sku",
                market_code="IL",
                materials=materials,
                reference_aliases=aliases,
                market_offers=offers,
                supplier_name=supplier_name,
                supplier_sku=supplier_sku,
            )
            sku_collision_false_resolutions += (
                collision_result.route == "exact_supplier_sku"
            )
            continue
        sku_unique += 1
        supplier_name, supplier_sku = sku_inputs[key]
        expected = next(iter(material_ids))
        result = resolve_material_identity(
            phrase="supplier sku",
            market_code="IL",
            materials=materials,
            reference_aliases=aliases,
            market_offers=offers,
            supplier_name=supplier_name,
            supplier_sku=supplier_sku,
        )
        sku_correct += result.selected_material_id == expected

    result = {
        "materials": len(materials),
        "aliases": len(aliases),
        "unique_exact_alias_routes": exact_unique,
        "correct_exact_alias_routes": exact_correct,
        "unique_supplier_sku_routes": sku_unique,
        "correct_supplier_sku_routes": sku_correct,
        "colliding_exact_alias_keys": sum(
            len(material_ids) > 1 for material_ids in exact_groups.values()
        ),
        "colliding_supplier_sku_keys": sum(
            len(material_ids) > 1 for material_ids in sku_groups.values()
        ),
        "collision_false_resolutions": (
            exact_collision_false_resolutions + sku_collision_false_resolutions
        ),
    }
    print(result)
    if (
        exact_correct != exact_unique
        or sku_correct != sku_unique
        or exact_collision_false_resolutions
        or sku_collision_false_resolutions
    ):
        raise SystemExit("Material identity resolver returned a false exact match")


if __name__ == "__main__":
    main()
