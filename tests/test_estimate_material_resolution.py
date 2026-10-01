from datetime import date
from decimal import Decimal

from use_cases.estimate_material_resolution import resolve_estimate_material_requirement


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


def _identity(identity_id: str, **attributes):
    return {
        "pricing_identity_id": identity_id,
        "market_code": "IL",
        "status": "active",
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
