from decimal import Decimal
from pathlib import Path

from tools.israel_reference_readiness import load_seed_report
from use_cases.reference_material_readiness import (
    ReferenceOffer,
    build_reference_readiness_report,
    derive_baseline_candidates,
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
        "confidence": Decimal("80"),
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


def test_single_source_candidate_uses_confidence_driven_provisional_range():
    candidate = derive_baseline_candidates((_offer(),))[0]

    assert candidate.price_low == Decimal("80.000000")
    assert candidate.price_typical == Decimal("100.000000")
    assert candidate.price_high == Decimal("120.000000")
    assert candidate.confidence == Decimal("55.000000")
    assert candidate.distinct_source_count == 1
    assert candidate.methodology.startswith("single_source_provisional")


def test_single_source_candidate_uncertainty_is_bounded():
    high_confidence = derive_baseline_candidates(
        (_offer(confidence=Decimal("99")),)
    )[0]
    low_confidence = derive_baseline_candidates(
        (_offer(confidence=Decimal("10")),)
    )[0]

    assert (high_confidence.price_low, high_confidence.price_high) == (
        Decimal("85.000000"),
        Decimal("115.000000"),
    )
    assert (low_confidence.price_low, low_confidence.price_high) == (
        Decimal("60.000000"),
        Decimal("140.000000"),
    )


def test_multi_source_candidate_deduplicates_sources_and_caps_outlier():
    candidates = derive_baseline_candidates(
        (
            _offer(normalized_price_ex_vat=Decimal("90")),
            _offer(offer_id="offer-2", normalized_price_ex_vat=Decimal("110")),
            _offer(
                offer_id="offer-3",
                source_id="source-2",
                normalized_price_ex_vat=Decimal("1000"),
                confidence=Decimal("70"),
            ),
        )
    )

    candidate = candidates[0]
    assert candidate.price_typical == Decimal("550.000000")
    assert candidate.price_low == Decimal("330.000000")
    assert candidate.price_high == Decimal("880.000000")
    assert candidate.confidence == Decimal("65.000000")
    assert candidate.distinct_source_count == 2
    assert candidate.methodology.startswith("multi_source_robust")


def test_candidate_derivation_rejects_blocked_offer():
    candidates = derive_baseline_candidates(
        (_offer(vat_mode="unknown", normalized_price_ex_vat=None),)
    )

    assert candidates == ()


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


def test_home_center_normalization_is_evidence_bounded_and_non_activating():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_home_center_vat_normalization.sql"
    ).read_text()
    lowered = sql.lower()

    assert "website terms section 65" in sql
    assert "o.supplier_name = 'Home Center'" in sql
    assert "s.source_url like 'https://www.homecenter.co.il/%'" in sql
    assert "o.market_code = 'IL'" in sql
    assert "o.status = 'candidate'" in sql
    assert "o.vat_mode = 'unknown'" in sql
    assert "source_price / 1.18 / normalized_quantity" in sql
    assert "when m.base_unit = 'l'" in sql
    assert "when m.base_unit = 'kg'" in sql
    assert "insert into public.market_material_baselines" not in lowered
    assert "status = 'active'" not in lowered


def test_camisa_normalization_is_inference_labeled_and_non_activating():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_camisa_vat_normalization.sql"
    ).read_text()
    lowered = sql.lower()

    assert "expected 21 total candidates" in sql
    assert "pending_count + normalized_count <> 21" in sql
    assert "o.supplier_name = 'Camisa'" in sql
    assert "s.source_url like 'https://www.camisa.co.il/%'" in sql
    assert "o.market_code = 'IL'" in sql
    assert "o.status = 'candidate'" in sql
    assert "o.vat_mode = 'unknown'" in sql
    assert "'vat_evidence_type', 'legal_inference'" in sql
    assert "source_price / 1.18 / sheet_area_sqm" in sql
    assert "m.base_unit = 'sqm'" in sql
    assert "confidence = least(coalesce(o.confidence, 68), 68)" in sql
    assert "insert into public.market_material_baselines" not in lowered
    assert "status = 'active'" not in lowered


def test_ikea_normalization_uses_direct_terms_and_preserves_identity_blocker():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_ikea_vat_normalization.sql"
    ).read_text()
    lowered = sql.lower()

    assert "expected 11 total candidates" in sql
    assert "pending_count + normalized_count <> 8" in sql
    assert "excluded_mirror_count <> 3" in sql
    assert "o.supplier_name = 'IKEA Israel'" in sql
    assert "not like '%mirror thickness%'" in sql
    assert "when m.base_unit = 'set' then 1::numeric" in sql
    assert "when m.base_unit = 'l'" in sql
    assert "'vat_evidence_type', 'direct_supplier_terms'" in sql
    assert "'vat_mode_source', 'IKEA Israel website terms'" in sql
    assert "source_price / 1.18 / normalized_quantity" in sql
    assert "insert into public.market_material_baselines" not in lowered
    assert "status = 'active'" not in lowered


def test_algolan_normalization_preserves_price_per_sheet_without_area_guess():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_algolan_sheet_normalization.sql"
    ).read_text()
    lowered = sql.lower()

    assert "expected 12 sheet candidates" in sql
    assert "pending_count + normalized_count <> 12" in sql
    assert "o.supplier_name = 'Algolan'" in sql
    assert "m.base_unit = 'sheet'" in sql
    assert "o.vat_mode = 'excluded'" in sql
    assert "o.package_quantity = 1" in sql
    assert "normalized_price_ex_vat = o.source_price" in sql
    assert "normalized_unit = 'sheet'" in sql
    assert "sheet_dimensions_required_for_area_conversion" in sql
    assert "normalized_unit = 'sqm'" not in sql
    assert "insert into public.market_material_baselines" not in lowered
    assert "status = 'active'" not in lowered


def test_ar_sharpening_normalization_handles_piece_and_weight_packages():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_ar_sharpening_normalization.sql"
    ).read_text()
    lowered = sql.lower()

    assert "expected 14 candidates" in sql
    assert "o.supplier_name in ('A.R. Sharpening', 'AR Sharpening')" in sql
    assert "s.source_url like 'https://www.ar-aia.co.il/%'" in sql
    assert "when m.base_unit = 'kg'" in sql
    assert "when m.base_unit = 'ea' then o.package_quantity" in sql
    assert "'vat_evidence_type', 'legal_inference'" in sql
    assert "confidence = least(coalesce(o.confidence, 60), 60)" in sql
    assert "source_price / 1.18 / normalized_quantity" in sql
    assert "insert into public.market_material_baselines" not in lowered
    assert "status = 'active'" not in lowered
