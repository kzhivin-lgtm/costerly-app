from decimal import Decimal

import pytest

from use_cases.material_identity_resolution import (
    build_material_identity_index,
    normalize_material_phrase,
    normalize_supplier_sku,
    resolve_material_identity,
)


MDF_ID = "material-mdf-18"
PLYWOOD_ID = "material-plywood-18"


def _material(material_id, category, name, **specifications):
    return {
        "material_id": material_id,
        "category_code": category,
        "canonical_name": name,
        "base_unit": "sqm",
        "specifications": specifications,
        "active": True,
    }


MATERIALS = (
    _material(MDF_ID, "mdf", "Standard raw MDF 18 mm", thickness_mm=18, surface="raw"),
    _material(
        PLYWOOD_ID,
        "plywood",
        "Birch plywood 18 mm",
        thickness_mm=18,
        species="birch",
    ),
)


def _alias(material_id, text, *, exact=True):
    return {
        "material_id": material_id,
        "market_code": "IL",
        "alias_text": text,
        "exact_identity": exact,
        "active": True,
    }


def _resolve(**changes):
    values = {
        "phrase": "MDF 18 mm",
        "market_code": "IL",
        "materials": MATERIALS,
        "reference_aliases": (_alias(MDF_ID, "MDF 18 mm"),),
    }
    values.update(changes)
    return resolve_material_identity(**values)


def test_phrase_and_sku_normalization_are_deterministic():
    assert normalize_material_phrase("  MDF 18мм × 1220  ") == "mdf 18 mm x 1220"
    assert normalize_material_phrase("MDF 18 millimeters x 1220") == "mdf 18 mm x 1220"
    assert normalize_supplier_sku(" AB-12 / 34 ") == "ab1234"


def test_exact_supplier_sku_is_first_route():
    result = _resolve(
        phrase="anything",
        supplier_name="Supplier A",
        supplier_sku="AB-123",
        market_offers=(
            {
                "material_id": PLYWOOD_ID,
                "market_code": "IL",
                "supplier_name": "Supplier A",
                "supplier_sku": "AB123",
            },
        ),
    )

    assert result.status == "resolved"
    assert result.route == "exact_supplier_sku"
    assert result.selected_material_id == PLYWOOD_ID


def test_confirmed_company_alias_precedes_market_alias():
    result = _resolve(
        company_aliases=(
            {
                "material_id": PLYWOOD_ID,
                "alias_text": "MDF 18 mm",
                "supplier_id": None,
                "active": True,
            },
        )
    )

    assert result.route == "exact_company_alias"
    assert result.selected_material_id == PLYWOOD_ID


def test_exact_market_alias_resolves_without_model():
    result = _resolve()

    assert result.status == "resolved"
    assert result.route == "exact_market_alias"
    assert result.selected_material_id == MDF_ID


def test_raw_supplier_phrase_can_resolve_when_normalized_name_was_translated():
    result = _resolve(
        phrase="Birch plywood 18 mm",
        alternate_phrases=("לביד ליבנה 18 מ״מ",),
        reference_aliases=(_alias(PLYWOOD_ID, "לביד ליבנה 18 מ״מ"),),
    )

    assert result.status == "resolved"
    assert result.route == "exact_market_alias"
    assert result.selected_material_id == PLYWOOD_ID


def test_conflicting_hard_attribute_rejects_exact_alias():
    result = _resolve(
        category_code="mdf",
        specifications={"thickness_mm": 19},
    )

    assert result.status == "new_identity_or_needs_review"
    assert result.selected_material_id is None


def test_exact_alias_tolerates_unrecorded_hard_attribute():
    result = _resolve(
        category_code="mdf",
        specifications={"thickness_mm": 18, "colour": "white"},
    )

    assert result.status == "resolved"
    assert result.route == "exact_market_alias"
    assert result.selected_material_id == MDF_ID


def test_shortlist_tolerates_unrecorded_hard_attribute():
    result = _resolve(
        phrase="MDF board",
        reference_aliases=(),
        category_code="mdf",
        specifications={"thickness_mm": 18, "colour": "white"},
    )

    assert result.status == "resolved"
    assert result.route == "compatible_hard_attributes"
    assert result.selected_material_id == MDF_ID


def test_unique_hard_attribute_match_resolves():
    result = _resolve(
        phrase="green board",
        reference_aliases=(),
        category_code="plywood",
        specifications={"thickness_mm": 18, "species": "birch"},
    )

    assert result.route == "compatible_hard_attributes"
    assert result.selected_material_id == PLYWOOD_ID


def test_non_exact_alias_returns_bounded_shortlist():
    materials = tuple(
        _material(f"m-{index}", "mdf", f"MDF board {index} mm", thickness_mm=index)
        for index in range(4, 14)
    )
    aliases = tuple(_alias(row["material_id"], row["canonical_name"], exact=False) for row in materials)
    result = resolve_material_identity(
        phrase="MDF board",
        market_code="IL",
        materials=materials,
        reference_aliases=aliases,
        category_code="mdf",
    )

    assert result.status == "shortlist"
    assert len(result.candidates) == 5
    assert all(candidate.score <= Decimal("94") for candidate in result.candidates)


def test_material_family_removes_cross_family_shortlist_candidates():
    materials = (
        _material("plywood-18", "wood", "Birch plywood, 18 mm", thickness_mm=18),
        _material("oak-18", "wood", "Oak veneer, 18 mm", thickness_mm=18),
    )
    result = resolve_material_identity(
        phrase="Plywood 18 mm",
        market_code="IL",
        materials=materials,
        reference_aliases=(),
        specifications={"thickness_mm": 18},
        material_family="plywood",
    )

    assert result.status == "shortlist"
    assert [candidate.material_id for candidate in result.candidates] == ["plywood-18"]


def test_known_family_with_no_compatible_variant_never_falls_back_cross_family():
    materials = (
        _material("melamine-18", "wood", "Melamine board, 18 mm", thickness_mm=18),
        _material("oak-17", "wood", "Oak veneer, 17 mm", thickness_mm=17),
    )
    result = resolve_material_identity(
        phrase="Melamine 17 mm",
        market_code="IL",
        materials=materials,
        reference_aliases=(),
        specifications={"thickness_mm": 17},
        material_family="melamine",
    )

    assert result.status == "new_identity_or_needs_review"
    assert result.candidates == ()


def test_laminated_solid_timber_uses_butcher_block_retrieval_synonym():
    materials = (
        _material("pine-block", "wood", "Pine butcher-block panel"),
        _material("pine-plywood", "wood", "Pine plywood, 18 mm", thickness_mm=18),
    )
    result = resolve_material_identity(
        phrase="Pine laminated 18 mm",
        market_code="IL",
        materials=materials,
        reference_aliases=(),
        specifications={"thickness_mm": 18},
        material_family="solid timber laminated",
    )

    assert result.status == "shortlist"
    assert [candidate.material_id for candidate in result.candidates] == ["pine-block"]


def test_no_compatible_material_creates_review_route():
    result = _resolve(
        phrase="unknown titanium honeycomb",
        reference_aliases=(),
        category_code="metal_honeycomb",
    )

    assert result.status == "new_identity_or_needs_review"
    assert result.route == "no_compatible_identity"


def test_shortlist_limit_is_bounded():
    with pytest.raises(ValueError, match="between 1 and 5"):
        _resolve(shortlist_limit=6)


def test_material_identity_index_preserves_family_and_alias_resolution():
    materials = (
        _material("mdf-18", "mdf", "Standard raw MDF 18 mm", thickness_mm=18),
        _material("plywood-18", "plywood", "Birch plywood 18 mm", thickness_mm=18),
        _material("steel-2", "steel", "Steel sheet 2 mm", thickness_mm=2),
    )
    aliases = (
        _alias("mdf-18", "MDF 18 mm"),
        _alias("plywood-18", "Birch plywood 18 mm", exact=False),
    )
    request = {
        "phrase": "Birch plywood 18 mm",
        "market_code": "IL",
        "materials": materials,
        "reference_aliases": aliases,
        "specifications": {"thickness_mm": 18},
        "material_family": "plywood",
    }
    assert resolve_material_identity(**request) == resolve_material_identity(
        **request,
        material_identity_index=build_material_identity_index(materials, aliases, "IL"),
    )
