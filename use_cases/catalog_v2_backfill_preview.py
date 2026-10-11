"""Read-only projection of one legacy material into the Catalog V2 layers.

The module intentionally returns data only. A later persistence step must use
these projections after the V2 contract and Global family seed are applied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from use_cases.catalog_migration_map import MAPPED, classify_legacy_material


ISRAEL_MARKET_CODE = "IL"


@dataclass(frozen=True)
class CatalogV2BackfillPreview:
    legacy_material_id: str
    family_code: str
    global_model_code: str
    global_canonical_name: str
    primary_attribute_code: str
    primary_attribute_value: Any
    market_code: str
    israel_listing_code: str
    israel_canonical_name: str


def preview_legacy_material_backfill(
    row: Mapping[str, Any],
    *,
    category_name: str | None,
) -> CatalogV2BackfillPreview | None:
    """Return the safe V2 projection, or ``None`` for excluded/review rows."""
    decision = classify_legacy_material(row, category_name=category_name)
    if decision.status != MAPPED:
        return None

    legacy_material_id = str(row.get("material_id") or "").strip()
    canonical_name = str(row.get("canonical_name") or "").strip()
    if not legacy_material_id or not canonical_name:
        raise ValueError("Mapped legacy material requires material_id and canonical_name.")

    return CatalogV2BackfillPreview(
        legacy_material_id=legacy_material_id,
        family_code=decision.family_code or _raise("Mapped decision lacks family_code."),
        global_model_code=decision.global_model_code or _raise("Mapped decision lacks global_model_code."),
        global_canonical_name=canonical_name,
        primary_attribute_code=decision.primary_attribute_code or _raise("Mapped decision lacks primary attribute."),
        primary_attribute_value=decision.primary_attribute_value,
        market_code=ISRAEL_MARKET_CODE,
        israel_listing_code=decision.israel_listing_code or _raise("Mapped decision lacks Israel listing code."),
        israel_canonical_name=canonical_name,
    )


def _raise(message: str) -> Any:
    raise ValueError(message)
