from datetime import date
from decimal import Decimal

from use_cases.estimate_material_resolution import resolve_estimate_material_requirement
from use_cases.material_identity_resolution import (
    build_material_identity_index,
    resolve_material_identity,
)


AS_OF = date(2026, 9, 30)


def _company_item(material_id: str, name: str, **specifications):
    return {
        "company_material_id": material_id,
        "canonical_name": name,
        "normalized_name": name,
        "category": specifications.pop("category", "plywood"),
        "status": "private",
        "specifications": specifications,
    }


def _offer(offer_id: str, material_id: str, **overrides):
    return {
        "offer_id": offer_id,
        "company_material_id": material_id,
        "status": "active",
        "currency": "ILS",
        "normalized_unit": "sqm",
        "normalized_price": "100",
        "price_scope": "material_only",
        **overrides,
    }


def _identity(identity_id: str, *, base_unit="sqm", canonical_name=None, **attributes):
    return {
        "pricing_identity_id": identity_id,
        "market_code": "IL",
        "status": "active",
        "base_unit": base_unit,
        "canonical_name": canonical_name or identity_id,
        "price_attributes": attributes,
    }


def _price(price_id: str, identity_id: str, **overrides):
    return {
        "pricing_identity_price_id": price_id,
        "pricing_identity_id": identity_id,
        "status": "active",
        "currency": "ILS",
        "unit": "sqm",
        "price_scope": "material_only",
        "price_low": "80",
        "price_typical": "100",
        "price_high": "120",
        "effective_from": "2026-01-01",
        **overrides,
    }


def _resolve(**overrides):
    values = {
        "requirement_name": "Birch plywood B/B",
        "material_family": "plywood",
        "specifications": {"thickness_mm": 18, "species": "birch", "grade": "B/B"},
        "requested_unit": "sqm",
        "company_material_items": (),
        "company_offers": (),
        "pricing_identities": (),
        "pricing_identity_prices": (),
        "as_of": AS_OF,
    }
    values.update(overrides)
    return resolve_estimate_material_requirement(**values)


def test_e13_unique_compatible_company_material_wins_before_israel_fallback():
    result = _resolve(
        company_material_items=(_company_item("company-birch-18", "Birch plywood B/B", thickness_mm=18, species="birch", grade="B/B"),),
        company_offers=(_offer("offer-1", "company-birch-18", supplier_sku="supplier-irrelevant"),),
        pricing_identities=(_identity("israel-birch-18", material_family="plywood", thickness_mm=18, species="birch", grade="B/B"),),
        pricing_identity_prices=(_price("model-1", "israel-birch-18"),),
    )

    assert result.status == "resolved"
    assert result.authority == "company"
    assert result.company_material_id == "company-birch-18"
    assert result.offer_ids == ("offer-1",)


def test_e14_missing_company_material_uses_one_active_israel_price_model():
    result = _resolve(
        pricing_identities=(_identity("israel-birch-18", material_family="plywood", thickness_mm=18, species="birch", grade="B/B"),),
        pricing_identity_prices=(_price("model-1", "israel-birch-18"),),
    )

    assert result.status == "resolved"
    assert result.authority == "israel_pricing"
    assert result.pricing_identity_id == "israel-birch-18"
    assert result.pricing_identity_price_id == "model-1"
    assert result.price_typical == Decimal("100")


def test_e15_ambiguous_company_material_requires_review_without_fallback():
    result = _resolve(
        company_material_items=(
            _company_item("company-1", "Birch plywood B/B", thickness_mm=18, species="birch", grade="B/B"),
            _company_item("company-2", "Birch plywood B/B", thickness_mm=18, species="birch", grade="B/B"),
        ),
        company_offers=(_offer("offer-1", "company-1"), _offer("offer-2", "company-2")),
        pricing_identities=(_identity("israel-birch-18", material_family="plywood", thickness_mm=18, species="birch", grade="B/B"),),
        pricing_identity_prices=(_price("model-1", "israel-birch-18"),),
    )

    assert result.status == "needs_review"
    assert result.reason_codes == ("ambiguous_company_material",)


def test_e16_supplier_sku_is_not_a_company_matching_input():
    result = _resolve(
        requirement_name="Supplier SKU 8172",
        company_material_items=(_company_item("company-birch-18", "Birch plywood B/B", thickness_mm=18, species="birch", grade="B/B"),),
        company_offers=(_offer("offer-1", "company-birch-18", supplier_sku="8172"),),
    )

    assert result.status == "needs_review"
    assert result.authority is None
    assert result.company_material_id is None
    assert result.reason_codes == ("pricing_identity_not_found",)


def test_exact_reference_material_membership_resolves_detailed_price_class_without_sku():
    result = _resolve(
        requirement_name="Epoxy metal primer",
        material_family="metal_coatings",
        specifications={"supplier_sku": "must-not-matter"},
        requested_unit="l",
        reference_materials=({
            "material_id": "reference-primer", "canonical_name": "Epoxy metal primer", "active": True,
        },),
        pricing_identity_members=({
            "material_id": "reference-primer", "pricing_identity_id": "primer-class",
        },),
        pricing_identities=(_identity("primer-class", material_family="metal_coatings"),),
        pricing_identity_prices=(_price("primer-price", "primer-class", unit="l"),),
    )

    assert result.status == "resolved"
    assert result.authority == "israel_pricing"
    assert result.pricing_identity_id == "primer-class"
    assert result.price_typical == Decimal("100")


def test_estimation_uses_reference_alias_then_membership_before_broad_price_matching():
    result = _resolve(
        requirement_name="Painted MDF 18 mm",
        material_family="mdf",
        specifications={"thickness_mm": 18, "finish": "painted"},
        reference_materials=({
            "material_id": "reference-mdf-18",
            "canonical_name": "Standard MDF, raw, 18 mm",
            "active": True,
            "specifications": {"material_family": "mdf", "thickness_mm": 18},
        },),
        reference_aliases=({
            "material_id": "reference-mdf-18", "market_code": "IL",
            "alias_text": "Painted MDF 18 mm", "exact_identity": True,
            "active": True,
        },),
        pricing_identity_members=({
            "material_id": "reference-mdf-18", "pricing_identity_id": "mdf-18-class",
        },),
        pricing_identities=(
            _identity("mdf-18-class", material_family="mdf", thickness_mm=18),
            _identity("broad-mdf-a", material_family="mdf"),
            _identity("broad-mdf-b", material_family="mdf"),
        ),
        pricing_identity_prices=(_price("mdf-18-price", "mdf-18-class"),),
    )

    assert result.status == "resolved"
    assert result.pricing_identity_id == "mdf-18-class"
    assert result.pricing_identity_price_id == "mdf-18-price"


def test_estimation_does_not_substitute_an_unlisted_mdf_thickness():
    result = _resolve(
        requirement_name="MDF 20 mm",
        material_family="mdf",
        specifications={"thickness_mm": 20},
        reference_materials=(
            {"material_id": "mdf-19", "canonical_name": "MDF 19 mm", "active": True,
             "specifications": {"material_family": "mdf", "thickness_mm": 19}},
            {"material_id": "mdf-22", "canonical_name": "MDF 22 mm", "active": True,
             "specifications": {"material_family": "mdf", "thickness_mm": 22}},
        ),
        reference_aliases=(),
        pricing_identity_members=(),
        pricing_identities=(),
        pricing_identity_prices=(),
    )

    assert result.status == "needs_review"
    assert result.reason_codes == ("pricing_identity_not_found",)


def test_estimation_index_uses_catalog_material_family_instead_of_cross_family_noise():
    materials = (
        {"material_id": "steel", "canonical_name": "Square hollow section 20 mm",
         "active": True, "specifications": {"material_family": "carbon_steel"}},
        {"material_id": "plastic", "canonical_name": "Polycarbonate sheet 20 mm",
         "active": True, "specifications": {"material_family": "polycarbonate"}},
    )
    index = build_material_identity_index(materials, (), "IL")

    identity = resolve_material_identity(
        phrase="металл профиль 20мм",
        market_code="IL",
        material_family="carbon_steel",
        specifications={},
        materials=materials,
        reference_aliases=(),
        material_identity_index=index,
    )

    assert identity.status == "shortlist"
    assert [candidate.material_id for candidate in identity.candidates] == ["steel"]


def test_missing_sheet_thickness_uses_next_higher_price_class():
    result = _resolve(
        requirement_name="MDF 20 mm",
        material_family="mdf",
        specifications={"thickness_mm": 20},
        pricing_identities=(
            _identity("mdf-19", material_family="mdf", construction="raw", thickness_mm=19),
            _identity("mdf-22", material_family="mdf", construction="raw", thickness_mm=22),
        ),
        pricing_identity_prices=(
            _price("price-19", "mdf-19"),
            _price("price-22", "mdf-22", price_typical="140", price_high="160"),
        ),
    )

    assert result.status == "resolved"
    assert result.pricing_identity_id == "mdf-22"
    assert result.price_typical == Decimal("140")
    assert result.resolved_material_name == "mdf-22"
    assert result.requested_thickness_mm == Decimal("20")
    assert result.priced_thickness_mm == Decimal("22")
    assert result.thickness_policy == "next_higher_sheet_thickness"


def test_missing_sheet_thickness_uses_lower_only_when_no_higher_exists():
    result = _resolve(
        requirement_name="MDF 25 mm",
        material_family="mdf",
        specifications={"thickness_mm": 25},
        pricing_identities=(
            _identity("mdf-19", material_family="mdf", construction="raw", thickness_mm=19),
            _identity("mdf-22", material_family="mdf", construction="raw", thickness_mm=22),
        ),
        pricing_identity_prices=(_price("price-22", "mdf-22"),),
    )

    assert result.status == "resolved"
    assert result.pricing_identity_id == "mdf-22"
    assert result.thickness_policy == "nearest_lower_when_no_higher_sheet_thickness"


def test_thickness_fallback_does_not_apply_to_non_sheet_price_units():
    result = _resolve(
        requirement_name="Square tube, 2.5 mm wall",
        material_family="carbon_steel",
        specifications={"thickness_mm": 2.5},
        requested_unit="kg",
        pricing_identities=(
            _identity("steel-2", base_unit="kg", material_family="carbon_steel", thickness_mm=2),
            _identity("steel-3", base_unit="kg", material_family="carbon_steel", thickness_mm=3),
        ),
        pricing_identity_prices=(
            _price("steel-price-2", "steel-2", unit="kg"),
            _price("steel-price-3", "steel-3", unit="kg"),
        ),
    )

    assert result.status == "needs_review"
    assert result.requested_thickness_mm is None
    assert result.priced_thickness_mm is None


def test_incompatible_reference_membership_is_ignored_before_sheet_fallback():
    result = _resolve(
        requirement_name="Standard MDF raw 20 mm",
        material_family="mdf",
        specifications={"thickness_mm": 20},
        reference_materials=({
            "material_id": "bad-reference", "canonical_name": "Standard MDF raw 20 mm",
            "active": True, "specifications": {"material_family": "mdf", "thickness_mm": 20},
        },),
        pricing_identity_members=({
            "material_id": "bad-reference", "pricing_identity_id": "hdf-20",
        },),
        pricing_identities=(
            _identity("hdf-20", material_family="hdf", construction="raw", thickness_mm=20),
            _identity("mdf-22", material_family="mdf", construction="raw", thickness_mm=22),
        ),
        pricing_identity_prices=(
            _price("hdf-price", "hdf-20"),
            _price("mdf-price", "mdf-22"),
        ),
    )

    assert result.status == "resolved"
    assert result.pricing_identity_id == "mdf-22"
    assert result.thickness_policy == "next_higher_sheet_thickness"
