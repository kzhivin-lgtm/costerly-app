import pytest

from use_cases.estimation_assumption_price_contract import (
    ASSUMPTION_PRICE_V1,
    validate_assumption_price_v1,
)


def _price(**overrides):
    result = {
        "contract_version": ASSUMPTION_PRICE_V1,
        "material_requirement_id": "internal_carcass",
        "amount": 200,
        "currency": "ILS",
        "unit": "sheet",
        "confidence": 15,
        "basis_kind": "estimator_allowance",
        "rationale": [
            "No compatible Company Catalog or Israel Reference candidate was available.",
            "Estimator allowance selected for one standard internal carcass sheet.",
        ],
        "source_candidates": [],
    }
    result.update(overrides)
    return result


def test_unreferenced_allowance_is_a_valid_priced_assumption():
    result = validate_assumption_price_v1(_price())

    assert result["amount"] == 200.0
    assert result["confidence"] == 15.0
    assert result["basis_kind"] == "estimator_allowance"


def test_zero_confidence_is_allowed_for_a_price_with_no_external_evidence():
    assert validate_assumption_price_v1(_price(confidence=0))["confidence"] == 0.0


def test_global_source_requires_final_ils_price_and_source_trace():
    result = validate_assumption_price_v1(_price(
        amount=235,
        confidence=48,
        basis_kind="global_listing_projected_to_israel",
        rationale=["German listing was projected to Israel with a saved conversion input."],
        source_candidates=[{"url": "https://example.test/item", "currency": "EUR", "observed_price": 40}],
    ))

    assert result["currency"] == "ILS"
    assert result["source_candidates"][0]["currency"] == "EUR"


def test_assumption_price_can_never_be_blank_or_zero():
    with pytest.raises(ValueError, match="amount must be positive"):
        validate_assumption_price_v1(_price(amount=0))
