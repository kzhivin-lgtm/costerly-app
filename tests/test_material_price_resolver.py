from datetime import date
from decimal import Decimal

import pytest

from use_cases.material_price_resolver import (
    MaterialPriceResolutionError,
    resolve_material_price,
)


MATERIAL_ID = "material-1"


def _company_offer(**changes):
    row = {
        "offer_id": "company-offer-1",
        "reference_material_id": MATERIAL_ID,
        "normalized_price": "100",
        "normalized_unit": "sqm",
        "currency": "ILS",
        "vat_included": False,
        "valid_from": "2026-01-01",
        "confidence": "90",
        "status": "active",
    }
    row.update(changes)
    return row


def _baseline(**changes):
    row = {
        "baseline_id": "baseline-1",
        "material_id": MATERIAL_ID,
        "market_code": "IL",
        "price_low": "80",
        "price_typical": "100",
        "price_high": "130",
        "unit": "sqm",
        "currency": "ILS",
        "price_scope": "material_only",
        "confidence": "55",
        "status": "active",
        "effective_from": "2026-01-01",
        "effective_to": None,
    }
    row.update(changes)
    return row


def _resolve(*, company=(), baselines=None, **changes):
    return resolve_material_price(
        reference_material_id=MATERIAL_ID,
        requested_unit="sqm",
        currency="ILS",
        market_code="IL",
        company_offer_rows=company,
        market_baseline_rows=baselines if baselines is not None else (_baseline(),),
        as_of=date(2026, 9, 28),
        **changes,
    )


def test_company_exact_price_precedes_market_baseline():
    result = _resolve(company=(_company_offer(),))

    assert result.status == "resolved"
    assert result.authority == "company"
    assert result.price_low == Decimal("100.000000")
    assert result.price_typical == Decimal("100.000000")
    assert result.price_high == Decimal("100.000000")
    assert result.company_offer_ids == ("company-offer-1",)
    assert result.baseline_id is None


def test_company_vat_included_price_is_returned_ex_vat():
    result = _resolve(
        company=(_company_offer(normalized_price="118", vat_included=True),),
        vat_percent=18,
    )

    assert result.authority == "company"
    assert result.price_typical == Decimal("100.000000")


def test_multiple_company_offers_form_a_company_range():
    result = _resolve(
        company=(
            _company_offer(offer_id="offer-a", normalized_price="80", confidence="80"),
            _company_offer(offer_id="offer-b", normalized_price="100", confidence="90"),
            _company_offer(offer_id="offer-c", normalized_price="150", confidence="70"),
        )
    )

    assert result.authority == "company"
    assert result.price_low == Decimal("80.000000")
    assert result.price_typical == Decimal("100.000000")
    assert result.price_high == Decimal("150.000000")
    assert result.confidence == Decimal("80.000000")


def test_deterministic_unit_conversion_is_supported():
    result = resolve_material_price(
        reference_material_id=MATERIAL_ID,
        requested_unit="kg",
        currency="ILS",
        market_code="IL",
        company_offer_rows=(_company_offer(normalized_price="0.2", normalized_unit="g"),),
        market_baseline_rows=(),
    )

    assert result.authority == "company"
    assert result.price_typical == Decimal("200.000000")
    assert result.unit == "kg"


def test_unusable_company_offer_falls_back_with_reason():
    result = _resolve(company=(_company_offer(vat_included=None),))

    assert result.authority == "market_baseline"
    assert result.price_typical == Decimal("100.000000")
    assert result.reason_codes == ("company_offer_not_usable",)


def test_market_model_is_a_distinct_fallback_authority():
    model = _baseline(baseline_id=None, model_price_id="model-price-1")

    result = _resolve(baselines=(model,))

    assert result.authority == "market_model"
    assert result.baseline_id == "model-price-1"


def test_exact_price_scope_can_be_required():
    missing = _resolve(price_scope="cut_to_size")
    found = _resolve(
        baselines=(_baseline(price_scope="cut_to_size"),),
        price_scope="cut_to_size",
    )

    assert missing.needs_review
    assert missing.reason_codes == ("market_baseline_not_found",)
    assert found.authority == "market_baseline"
    assert found.price_scope == "cut_to_size"


def test_company_material_only_offer_does_not_override_requested_cut_scope():
    result = _resolve(
        company=(_company_offer(),),
        baselines=(_baseline(price_scope="cut_to_size"),),
        price_scope="cut_to_size",
    )

    assert result.authority == "market_baseline"
    assert result.price_scope == "cut_to_size"
    assert result.reason_codes == ("company_offer_not_usable",)


def test_different_company_scopes_are_not_silently_aggregated():
    result = _resolve(
        company=(
            _company_offer(offer_id="material", price_scope="material_only"),
            _company_offer(offer_id="cut", price_scope="cut_to_size"),
        )
    )

    assert result.authority == "market_baseline"
    assert result.reason_codes == ("ambiguous_company_price_scope",)


def test_multiple_compatible_baselines_require_review():
    result = _resolve(
        baselines=(
            _baseline(baseline_id="baseline-a", price_scope="material_only"),
            _baseline(baseline_id="baseline-b", price_scope="cut_to_size"),
        )
    )

    assert result.needs_review
    assert result.reason_codes == ("ambiguous_market_baseline",)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "candidate"},
        {"effective_from": "2026-10-01"},
        {"effective_to": "2026-09-27"},
        {"market_code": "US"},
        {"currency": "USD"},
        {"unit": "sheet"},
    ],
)
def test_ineligible_baseline_returns_needs_review(changes):
    result = _resolve(baselines=(_baseline(**changes),))

    assert result.needs_review
    assert result.reason_codes == ("market_baseline_not_found",)


def test_require_resolved_rejects_unresolved_result():
    result = _resolve(baselines=())

    with pytest.raises(MaterialPriceResolutionError, match="market_baseline_not_found"):
        result.require_resolved()


def test_invalid_vat_percent_is_rejected():
    with pytest.raises(MaterialPriceResolutionError, match="between 0 and 100"):
        _resolve(vat_percent=-1)
