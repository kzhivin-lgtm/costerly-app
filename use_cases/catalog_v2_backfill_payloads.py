"""Database-ready, but not database-writing, Catalog V2 backfill payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from use_cases.catalog_v2_backfill_preview import CatalogV2BackfillPreview


@dataclass(frozen=True)
class CatalogV2BackfillPayload:
    material_model: dict[str, Any]
    model_attribute_value: dict[str, Any]
    market_listing: dict[str, Any]
    legacy_mapping: dict[str, Any]


def build_catalog_v2_backfill_payload(
    preview: CatalogV2BackfillPreview,
) -> CatalogV2BackfillPayload:
    """Build deterministic rows without resolving UUID foreign keys or writing."""
    return CatalogV2BackfillPayload(
        material_model={
            "family_code": preview.family_code,
            "material_model_code": preview.global_model_code,
            "canonical_name": preview.global_canonical_name,
            "active": True,
        },
        model_attribute_value={
            "material_model_code": preview.global_model_code,
            "family_code": preview.family_code,
            "attribute_code": preview.primary_attribute_code,
            "attribute_value": preview.primary_attribute_value,
        },
        market_listing={
            "market_code": preview.market_code,
            "material_model_code": preview.global_model_code,
            "listing_code": preview.israel_listing_code,
            "canonical_market_name": preview.israel_canonical_name,
            "availability_status": "unknown",
            "active": True,
        },
        legacy_mapping={
            "legacy_material_id": preview.legacy_material_id,
            "market_code": preview.market_code,
            "family_code": preview.family_code,
            "material_model_code": preview.global_model_code,
            "listing_code": preview.israel_listing_code,
            "classification_status": "mapped",
            "classification_basis": "deterministic_rule",
            "classification_evidence": {
                "primary_attribute_code": preview.primary_attribute_code,
                "primary_attribute_value": preview.primary_attribute_value,
            },
        },
    )
