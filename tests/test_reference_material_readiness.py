from decimal import Decimal

from tools.israel_reference_readiness import load_seed_report
from use_cases.reference_material_readiness import (
    ReferenceOffer,
    build_reference_readiness_report,
    offer_blocking_reasons,
)


def _offer(**overrides):
    values = {
        "offer_id": "offer-1",
        "material_id": "material-1",
        "market_code": "IL",
        "source_id": "source-1",
        "currency": "ILS",
        "price_scope": "material_only",
        "vat_mode": "included",
        "normalized_price_ex_vat": Decimal("100"),
        "normalized_unit": "sqm",
        "status": "candidate",
    }
    values.update(overrides)
    return ReferenceOffer(**values)


def test_unknown_vat_and_missing_normalization_are_explicit_blockers():
    offer = _offer(
        vat_mode="unknown",
        normalized_price_ex_vat=None,
        normalized_unit=None,
    )

    assert offer_blocking_reasons(
        offer,
        market_code="IL",
        currency="ILS",
    ) == (
        "unknown_vat",
        "missing_normalized_price",
        "missing_normalized_unit",
    )


def test_readiness_never_mixes_scope_unit_or_region():
    report = build_reference_readiness_report(
        material_departments={"material-1": "wood"},
        offers=(
            _offer(),
            _offer(offer_id="offer-2", source_id="source-2"),
            _offer(
                offer_id="offer-3",
                source_id="source-3",
                price_scope="cut_to_size",
            ),
            _offer(
                offer_id="offer-4",
                source_id="source-4",
                normalized_unit="sheet",
            ),
            _offer(
                offer_id="offer-5",
                source_id="source-5",
                region="north",
            ),
        ),
    )

    assert report.baseline_group_count == 4
    assert report.multi_source_group_count == 1
    assert report.single_source_group_count == 3


def test_duplicate_offers_from_one_source_do_not_become_multi_source():
    report = build_reference_readiness_report(
        material_departments={"material-1": "wood"},
        offers=(
            _offer(),
            _offer(offer_id="offer-2", normalized_price_ex_vat=Decimal("120")),
        ),
    )

    assert report.groups[0].offer_count == 2
    assert report.groups[0].distinct_source_count == 1
    assert report.groups[0].readiness == "single_source_provisional"


def test_current_israel_seed_readiness_counts_are_reproducible():
    report = load_seed_report()

    assert report.material_count == 280
    assert report.offer_count == 320
    assert report.eligible_offer_count == 112
    assert report.eligible_material_count == 103
    assert report.blocked_material_count == 177
    assert report.baseline_group_count == 111
    assert report.single_source_group_count == 110
    assert report.multi_source_group_count == 1
    assert report.blocked_offer_reasons == {
        "missing_normalized_price": 208,
        "missing_normalized_unit": 78,
        "unknown_vat": 192,
    }
