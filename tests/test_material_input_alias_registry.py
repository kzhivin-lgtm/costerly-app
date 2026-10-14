from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from use_cases.material_input_alias_registry import (
    FAMILY_ALIASES,
    PRICING_KEY_ALIASES,
    alias_context_for_v3,
)


def _seeded_catalog_family_codes() -> set[str]:
    sql = Path("db/sql/2026_10_11_catalog_v2_global_family_seed.sql").read_text(encoding="utf-8")
    family_seed = sql.split("with family_seed", 1)[1].split("insert into public.reference_material_families", 1)[0]
    return set(re.findall(r"^\s*\('([a-z0-9_]+)',", family_seed, flags=re.MULTILINE))


def test_alias_registry_covers_every_seeded_catalog_family_once():
    assert set(FAMILY_ALIASES) == _seeded_catalog_family_codes()

    aliases_to_families: dict[str, list[str]] = defaultdict(list)
    for family_code, aliases in FAMILY_ALIASES.items():
        assert aliases, family_code
        assert any(re.search(r"[A-Za-z]", alias) for alias in aliases), family_code
        assert any(re.search(r"[А-Яа-яЁё]", alias) for alias in aliases), family_code
        assert any(re.search(r"[\u0590-\u05ff]", alias) for alias in aliases), family_code
        for alias in aliases:
            aliases_to_families[alias.casefold().strip()].append(family_code)

    collisions = {
        alias: sorted(set(families))
        for alias, families in aliases_to_families.items()
        if len(set(families)) > 1
    }
    assert collisions == {}


def test_v3_context_is_limited_to_requested_families_and_pricing_keys():
    context = alias_context_for_v3(
        source_family_to_catalog_family={
            "mdf": "mdf_hdf",
            "metal profile": "metal_profile_angle_channel",
        },
        pricing_key_fields_by_family={
            "mdf": ("thickness_mm",),
            "metal profile": ("profile_section", "metal_type"),
        },
    )

    assert set(context) == {"mdf", "metal profile"}
    assert "мдф" in context["mdf"]["family_aliases"]
    assert context["mdf"]["pricing_key_aliases"] == {
        "thickness_mm": list(PRICING_KEY_ALIASES["thickness_mm"]),
    }
    assert "профиль металлический" in context["metal profile"]["family_aliases"]
    assert context["metal profile"]["pricing_key_aliases"] == {
        "profile_section": list(PRICING_KEY_ALIASES["profile_section"]),
        "metal_type": list(PRICING_KEY_ALIASES["metal_type"]),
    }
