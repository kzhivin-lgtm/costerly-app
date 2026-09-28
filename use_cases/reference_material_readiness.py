from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


KNOWN_VAT_MODES = frozenset({"included", "excluded", "exempt"})
ELIGIBLE_STATUSES = frozenset({"candidate", "reviewed", "active"})


@dataclass(frozen=True)
class ReferenceOffer:
    offer_id: str
    material_id: str
    market_code: str
    source_id: str
    currency: str
    price_scope: str
    vat_mode: str
    normalized_price_ex_vat: Decimal | None
    normalized_unit: str | None
    status: str
    region: str | None = None
    confidence: Decimal | None = None
    source_price: Decimal | None = None
    source_unit: str | None = None
    package_quantity: Decimal | None = None
    conversion_basis: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ReferenceMaterial:
    material_id: str
    department: str
    category_code: str
    base_unit: str
    specifications: Mapping[str, Any] | None = None


@dataclass(frozen=True, order=True)
class BaselineGroupKey:
    material_id: str
    unit: str
    currency: str
    price_scope: str
    region: str | None = None


@dataclass(frozen=True)
class BaselineCandidateReadiness:
    key: BaselineGroupKey
    offer_count: int
    distinct_source_count: int
    price_low_observed: Decimal
    price_high_observed: Decimal
    readiness: str


@dataclass(frozen=True)
class DerivedBaselineCandidate:
    key: BaselineGroupKey
    price_low: Decimal
    price_typical: Decimal
    price_high: Decimal
    confidence: Decimal
    methodology: str
    offer_ids: tuple[str, ...]
    distinct_source_count: int


@dataclass(frozen=True)
class CatalogPriceCandidate:
    material_id: str
    price_low: Decimal
    price_typical: Decimal
    price_high: Decimal
    unit: str
    currency: str
    price_scope: str
    confidence: Decimal
    tier: str
    methodology: str
    offer_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceReadinessReport:
    market_code: str
    currency: str
    material_count: int
    offer_count: int
    eligible_offer_count: int
    eligible_material_count: int
    blocked_material_count: int
    baseline_group_count: int
    single_source_group_count: int
    multi_source_group_count: int
    blocked_offer_reasons: Mapping[str, int]
    material_status_counts: Mapping[str, int]
    department_counts: Mapping[str, Mapping[str, int]]
    groups: tuple[BaselineCandidateReadiness, ...]


def offer_blocking_reasons(
    offer: ReferenceOffer,
    *,
    market_code: str,
    currency: str,
) -> tuple[str, ...]:
    reasons = []
    if offer.status not in ELIGIBLE_STATUSES:
        reasons.append("ineligible_status")
    if offer.market_code != market_code:
        reasons.append("wrong_market")
    if offer.currency != currency:
        reasons.append("wrong_currency")
    if offer.vat_mode not in KNOWN_VAT_MODES:
        reasons.append("unknown_vat")
    if offer.normalized_price_ex_vat is None:
        reasons.append("missing_normalized_price")
    elif offer.normalized_price_ex_vat <= 0:
        reasons.append("non_positive_normalized_price")
    if not offer.normalized_unit or not offer.normalized_unit.strip():
        reasons.append("missing_normalized_unit")
    return tuple(reasons)


def build_reference_readiness_report(
    *,
    material_departments: Mapping[str, str],
    offers: Iterable[ReferenceOffer],
    market_code: str = "IL",
    currency: str = "ILS",
) -> ReferenceReadinessReport:
    offer_rows = tuple(offers)
    eligible_by_group: dict[BaselineGroupKey, list[ReferenceOffer]] = defaultdict(list)
    offers_by_material: dict[str, list[ReferenceOffer]] = defaultdict(list)
    eligible_material_ids: set[str] = set()
    blocked_reason_counts: Counter[str] = Counter()

    for offer in offer_rows:
        offers_by_material[offer.material_id].append(offer)
        reasons = offer_blocking_reasons(
            offer,
            market_code=market_code,
            currency=currency,
        )
        if reasons:
            blocked_reason_counts.update(reasons)
            continue
        eligible_material_ids.add(offer.material_id)
        key = BaselineGroupKey(
            material_id=offer.material_id,
            unit=offer.normalized_unit.strip(),
            currency=offer.currency,
            price_scope=offer.price_scope,
            region=offer.region,
        )
        eligible_by_group[key].append(offer)

    group_rows = []
    for key, group_offers in eligible_by_group.items():
        prices = tuple(offer.normalized_price_ex_vat for offer in group_offers)
        source_count = len({offer.source_id for offer in group_offers})
        group_rows.append(
            BaselineCandidateReadiness(
                key=key,
                offer_count=len(group_offers),
                distinct_source_count=source_count,
                price_low_observed=min(prices),
                price_high_observed=max(prices),
                readiness=(
                    "multi_source_candidate"
                    if source_count >= 2
                    else "single_source_provisional"
                ),
            )
        )

    material_status_counts: Counter[str] = Counter()
    department_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for material_id, department in material_departments.items():
        material_offers = offers_by_material.get(material_id, ())
        if material_id in eligible_material_ids:
            status = "eligible"
        elif material_offers:
            status = "normalization_blocked"
        else:
            status = "evidence_gap"
        material_status_counts[status] += 1
        department_counts[department][status] += 1
        department_counts[department]["total"] += 1

    group_rows.sort(
        key=lambda row: (
            row.key.material_id,
            row.key.unit,
            row.key.currency,
            row.key.price_scope,
            row.key.region or "",
        )
    )
    multi_source_count = sum(
        row.readiness == "multi_source_candidate" for row in group_rows
    )
    return ReferenceReadinessReport(
        market_code=market_code,
        currency=currency,
        material_count=len(material_departments),
        offer_count=len(offer_rows),
        eligible_offer_count=sum(len(rows) for rows in eligible_by_group.values()),
        eligible_material_count=len(eligible_material_ids),
        blocked_material_count=len(material_departments) - len(eligible_material_ids),
        baseline_group_count=len(group_rows),
        single_source_group_count=len(group_rows) - multi_source_count,
        multi_source_group_count=multi_source_count,
        blocked_offer_reasons=dict(sorted(blocked_reason_counts.items())),
        material_status_counts=dict(sorted(material_status_counts.items())),
        department_counts={
            department: dict(sorted(counts.items()))
            for department, counts in sorted(department_counts.items())
        },
        groups=tuple(group_rows),
    )


def _median(values: Iterable[Decimal]) -> Decimal:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Median requires at least one value")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal("2")


def _round_price(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def derive_baseline_candidates(
    offers: Iterable[ReferenceOffer],
    *,
    market_code: str = "IL",
    currency: str = "ILS",
) -> tuple[DerivedBaselineCandidate, ...]:
    """Derive review-only price candidates from eligible normalized evidence.

    Duplicate observations from one source are collapsed to one source median.
    A single source receives a confidence-driven provisional range. Multiple
    sources use the median source price and a dispersion range capped at 40%
    below and 60% above the median so one extreme source cannot define the
    entire market interval.
    """

    eligible_by_group: dict[BaselineGroupKey, list[ReferenceOffer]] = defaultdict(list)
    for offer in offers:
        if offer_blocking_reasons(
            offer,
            market_code=market_code,
            currency=currency,
        ):
            continue
        key = BaselineGroupKey(
            material_id=offer.material_id,
            unit=offer.normalized_unit.strip(),
            currency=offer.currency,
            price_scope=offer.price_scope,
            region=offer.region,
        )
        eligible_by_group[key].append(offer)

    candidates = []
    for key, group_offers in eligible_by_group.items():
        offers_by_source: dict[str, list[ReferenceOffer]] = defaultdict(list)
        for offer in group_offers:
            offers_by_source[offer.source_id].append(offer)

        source_prices = {
            source_id: _median(
                offer.normalized_price_ex_vat for offer in source_offers
            )
            for source_id, source_offers in offers_by_source.items()
        }
        source_confidences = {
            source_id: _median(
                offer.confidence if offer.confidence is not None else Decimal("50")
                for offer in source_offers
            )
            for source_id, source_offers in offers_by_source.items()
        }
        typical = _median(source_prices.values())
        source_count = len(source_prices)

        if source_count == 1:
            source_confidence = next(iter(source_confidences.values()))
            uncertainty = min(
                Decimal("0.40"),
                max(Decimal("0.15"), (Decimal("100") - source_confidence) / 100),
            )
            low = typical * (Decimal("1") - uncertainty)
            high = typical * (Decimal("1") + uncertainty)
            confidence = min(source_confidence, Decimal("55"))
            methodology = (
                "single_source_provisional: source-median typical; symmetric "
                f"confidence-derived range +/-{_round_price(uncertainty * 100)}%"
            )
        else:
            low = max(min(source_prices.values()), typical * Decimal("0.60"))
            high = min(max(source_prices.values()), typical * Decimal("1.60"))
            confidence = min(
                _median(source_confidences.values()),
                Decimal("55") + Decimal("10") * (source_count - 1),
                Decimal("85"),
            )
            methodology = (
                "multi_source_robust: one median per source; median typical; "
                "observed dispersion capped to -40%/+60% of typical"
            )

        candidates.append(
            DerivedBaselineCandidate(
                key=key,
                price_low=_round_price(low),
                price_typical=_round_price(typical),
                price_high=_round_price(high),
                confidence=_round_price(confidence),
                methodology=methodology,
                offer_ids=tuple(sorted(offer.offer_id for offer in group_offers)),
                distinct_source_count=source_count,
            )
        )

    candidates.sort(
        key=lambda row: (
            row.key.material_id,
            row.key.unit,
            row.key.currency,
            row.key.price_scope,
            row.key.region or "",
        )
    )
    return tuple(candidates)


def _decimal_from_mapping(
    values: Mapping[str, Any],
    *keys: str,
) -> Decimal | None:
    for key in keys:
        value = values.get(key)
        if value is None:
            continue
        try:
            parsed = Decimal(str(value))
        except Exception:
            continue
        if parsed > 0:
            return parsed
    return None


def _modeled_offer_unit_price(
    material: ReferenceMaterial,
    offer: ReferenceOffer,
) -> Decimal | None:
    if offer.source_price is None or offer.source_price <= 0:
        return None
    basis = offer.conversion_basis or {}
    blocker = str(basis.get("normalization_blocked_by", "")).lower()
    if basis.get("price_is_configurable_minimum"):
        return None
    if "selected dimensions" in blocker or "selected substrate" in blocker:
        return None
    if material.base_unit == "sqm" and "sheet dimensions not stated" in blocker:
        return None

    direct_price_keys = {
        "ea": ("gross_price_per_piece_ils",),
        "kg": ("price_per_kg_ils",),
        "sqm": ("gross_price_per_sqm_ils",),
    }
    direct_price = _decimal_from_mapping(
        basis,
        *direct_price_keys.get(material.base_unit, ()),
    )
    if direct_price is not None:
        return direct_price

    if material.base_unit == "ea":
        quantity = _decimal_from_mapping(basis, "pricing_quantity")
        if quantity is None:
            quantity = offer.package_quantity
    elif material.base_unit == "set":
        quantity = Decimal("1")
    elif material.base_unit == "l":
        quantity = _decimal_from_mapping(basis, "net_volume_l")
        if quantity is None:
            quantity = offer.package_quantity
    elif material.base_unit == "kg":
        quantity = _decimal_from_mapping(basis, "net_weight_kg")
        if quantity is None:
            quantity = offer.package_quantity
    elif material.base_unit == "sqm":
        quantity = _decimal_from_mapping(
            basis,
            "sheet_area_sqm",
            "package_area_sqm",
            "area_sqm",
        )
    elif material.base_unit == "lm" and offer.source_unit == "lm":
        quantity = Decimal("1")
    elif material.base_unit == "sheet":
        quantity = offer.package_quantity or Decimal("1")
    else:
        quantity = offer.package_quantity

    if quantity is None or quantity <= 0:
        return None
    return offer.source_price / quantity


def _scope_mode(candidates: Iterable[CatalogPriceCandidate]) -> str:
    counts = Counter(candidate.price_scope for candidate in candidates)
    return sorted(counts, key=lambda scope: (-counts[scope], scope))[0]


def derive_complete_catalog_candidates(
    *,
    materials: Iterable[ReferenceMaterial],
    offers: Iterable[ReferenceOffer],
    market_code: str = "IL",
    currency: str = "ILS",
) -> tuple[CatalogPriceCandidate, ...]:
    """Return one review-only price candidate for every priceable material.

    The hierarchy is exact normalized evidence, a usable observed offer,
    explicit dimension-range modeling, a category median, a department median,
    then a global same-unit median. Modeled tiers never alter the underlying
    offer or claim verified VAT.
    """

    material_rows = {material.material_id: material for material in materials}
    offer_rows = tuple(offers)
    exact_rows = derive_baseline_candidates(
        offer_rows,
        market_code=market_code,
        currency=currency,
    )
    exact_by_material: dict[str, list[DerivedBaselineCandidate]] = defaultdict(list)
    for row in exact_rows:
        exact_by_material[row.key.material_id].append(row)

    result: dict[str, CatalogPriceCandidate] = {}
    for material_id, rows in exact_by_material.items():
        material = material_rows.get(material_id)
        if material is None:
            continue
        compatible = [row for row in rows if row.key.unit == material.base_unit]
        if not compatible:
            continue
        chosen = sorted(
            compatible,
            key=lambda row: (
                -row.distinct_source_count,
                -row.confidence,
                row.key.price_scope,
                row.key.region or "",
            ),
        )[0]
        result[material_id] = CatalogPriceCandidate(
            material_id=material_id,
            price_low=chosen.price_low,
            price_typical=chosen.price_typical,
            price_high=chosen.price_high,
            unit=chosen.key.unit,
            currency=chosen.key.currency,
            price_scope=chosen.key.price_scope,
            confidence=chosen.confidence,
            tier=(
                "exact_multi_source"
                if chosen.distinct_source_count > 1
                else "exact_single_source"
            ),
            methodology=chosen.methodology,
            offer_ids=chosen.offer_ids,
        )

    offers_by_material: dict[str, list[ReferenceOffer]] = defaultdict(list)
    for offer in offer_rows:
        offers_by_material[offer.material_id].append(offer)

    for material_id, material in material_rows.items():
        if material_id in result:
            continue
        modeled = []
        for offer in offers_by_material.get(material_id, ()):
            if (
                offer.market_code != market_code
                or offer.currency != currency
                or offer.status not in ELIGIBLE_STATUSES
            ):
                continue
            unit_price = _modeled_offer_unit_price(material, offer)
            if unit_price is None:
                continue
            if offer.vat_mode == "included":
                typical = unit_price / Decimal("1.18")
                vat_low = typical
                vat_high = typical
                vat_basis = "known VAT-included source price"
                confidence_cap = Decimal("40")
            elif offer.vat_mode in {"excluded", "exempt"}:
                typical = unit_price
                vat_low = typical
                vat_high = typical
                vat_basis = "known VAT-exclusive source price"
                confidence_cap = Decimal("40")
            else:
                vat_low = unit_price / Decimal("1.18")
                vat_high = unit_price
                typical = (vat_low + vat_high) / Decimal("2")
                vat_basis = "VAT-ambiguous source price midpoint"
                confidence_cap = Decimal("35")
            source_confidence = offer.confidence or Decimal("50")
            is_starting_price = bool(
                (offer.conversion_basis or {}).get("price_is_starting_from")
            )
            if is_starting_price:
                typical = typical * Decimal("1.25")
                confidence_cap = Decimal("20")
            uncertainty = min(
                Decimal("0.40"),
                max(Decimal("0.20"), (Decimal("100") - source_confidence) / 100),
            )
            if is_starting_price:
                low = vat_low
                high = typical * Decimal("2")
                qualifier = "starting-price uplift with one-sided wide range"
            else:
                low = min(vat_low, typical * (Decimal("1") - uncertainty))
                high = max(vat_high, typical * (Decimal("1") + uncertainty))
                qualifier = "confidence-derived uncertainty"
            modeled.append(
                CatalogPriceCandidate(
                    material_id=material_id,
                    price_low=_round_price(low),
                    price_typical=_round_price(typical),
                    price_high=_round_price(high),
                    unit=material.base_unit,
                    currency=currency,
                    price_scope=offer.price_scope,
                    confidence=_round_price(min(source_confidence, confidence_cap)),
                    tier="modeled_offer",
                    methodology=(
                        f"{vat_basis}; {qualifier}; "
                        "underlying offer remains unmodified"
                    ),
                    offer_ids=(offer.offer_id,),
                )
            )
        if modeled:
            chosen = sorted(
                modeled,
                key=lambda row: (-row.confidence, row.offer_ids),
            )[0]
            result[material_id] = chosen

    for material_id, material in material_rows.items():
        if material_id in result or material.base_unit != "sqm":
            continue
        dimensions = (material.specifications or {}).get("max_dimensions_mm")
        if not isinstance(dimensions, (list, tuple)) or len(dimensions) != 2:
            continue
        try:
            area = (
                Decimal(str(dimensions[0]))
                * Decimal(str(dimensions[1]))
                / Decimal("1000000")
            )
        except Exception:
            continue
        if area <= 0:
            continue
        range_candidates = []
        for offer in offers_by_material.get(material_id, ()):
            basis = offer.conversion_basis or {}
            price_range = basis.get("displayed_price_range_ils")
            if not isinstance(price_range, (list, tuple)) or len(price_range) != 2:
                continue
            try:
                gross_low = Decimal(str(price_range[0])) / area
                gross_high = Decimal(str(price_range[1])) / area
            except Exception:
                continue
            if gross_low <= 0 or gross_high < gross_low:
                continue
            if offer.vat_mode == "included":
                low = gross_low / Decimal("1.18")
                high = gross_high / Decimal("1.18")
            elif offer.vat_mode in {"excluded", "exempt"}:
                low = gross_low
                high = gross_high
            else:
                low = gross_low / Decimal("1.18")
                high = gross_high
            range_candidates.append(
                CatalogPriceCandidate(
                    material_id=material_id,
                    price_low=_round_price(low),
                    price_typical=_round_price((low + high) / Decimal("2")),
                    price_high=_round_price(high),
                    unit="sqm",
                    currency=currency,
                    price_scope=offer.price_scope,
                    confidence=Decimal("15.000000"),
                    tier="modeled_configurable_range",
                    methodology=(
                        "displayed configurable full-range divided by canonical "
                        "maximum panel area; VAT ambiguity retained in bounds"
                    ),
                    offer_ids=(offer.offer_id,),
                )
            )
        if range_candidates:
            result[material_id] = sorted(
                range_candidates,
                key=lambda row: (row.price_high - row.price_low, row.offer_ids),
            )[0]

    for material_id, material in material_rows.items():
        if material_id in result or material.base_unit != "sqm":
            continue
        sheet_candidates = []
        for offer in offers_by_material.get(material_id, ()):
            if (
                offer.market_code != market_code
                or offer.currency != currency
                or offer.status not in ELIGIBLE_STATUSES
                or offer.source_unit != "sheet_dimensions_unstated"
                or offer.source_price is None
                or offer.source_price <= 0
            ):
                continue
            if offer.vat_mode == "included":
                net_sheet_price = offer.source_price / Decimal("1.18")
                vat_basis = "known VAT-included sheet price"
            elif offer.vat_mode in {"excluded", "exempt"}:
                net_sheet_price = offer.source_price
                vat_basis = "known VAT-exclusive sheet price"
            else:
                continue

            standard_sheet_area = Decimal("2.9768")  # 2440 x 1220 mm
            large_sheet_area = Decimal("5.796")  # 2800 x 2070 mm
            typical = net_sheet_price / standard_sheet_area
            low = net_sheet_price / large_sheet_area
            high = typical * Decimal("1.25")
            sheet_candidates.append(
                CatalogPriceCandidate(
                    material_id=material_id,
                    price_low=_round_price(low),
                    price_typical=_round_price(typical),
                    price_high=_round_price(high),
                    unit="sqm",
                    currency=currency,
                    price_scope=offer.price_scope,
                    confidence=Decimal("15.000000"),
                    tier="modeled_sheet_area_assumption",
                    methodology=(
                        f"{vat_basis}; observed per-sheet price divided by "
                        "an explicit 2440 x 1220 mm standard-sheet assumption; "
                        "range includes a 2800 x 2070 mm alternative and 25% "
                        "upside; source dimensions remain unknown"
                    ),
                    offer_ids=(offer.offer_id,),
                )
            )
        if sheet_candidates:
            result[material_id] = sorted(
                sheet_candidates,
                key=lambda row: (-row.confidence, row.offer_ids),
            )[0]

    exact_catalog = tuple(
        candidate
        for candidate in result.values()
        if candidate.tier.startswith("exact_")
    )
    fallback_indexes: tuple[
        tuple[
            str,
            dict[tuple[str, str], list[CatalogPriceCandidate]],
            Decimal,
            Decimal,
        ],
        ...,
    ]
    category_index: dict[tuple[str, str], list[CatalogPriceCandidate]] = defaultdict(list)
    department_index: dict[tuple[str, str], list[CatalogPriceCandidate]] = defaultdict(list)
    unit_index: dict[tuple[str, str], list[CatalogPriceCandidate]] = defaultdict(list)
    for candidate in exact_catalog:
        material = material_rows[candidate.material_id]
        category_index[(material.category_code, material.base_unit)].append(candidate)
        department_index[(material.department, material.base_unit)].append(candidate)
        unit_index[(candidate.unit, candidate.unit)].append(candidate)
    fallback_indexes = (
        ("modeled_category", category_index, Decimal("20"), Decimal("0.50")),
        ("modeled_department", department_index, Decimal("10"), Decimal("0.65")),
        ("modeled_global_unit", unit_index, Decimal("5"), Decimal("0.75")),
    )

    for material_id, material in material_rows.items():
        if material_id in result:
            continue
        keys = {
            "modeled_category": (material.category_code, material.base_unit),
            "modeled_department": (material.department, material.base_unit),
            "modeled_global_unit": (material.base_unit, material.base_unit),
        }
        for tier, index, confidence, downside in fallback_indexes:
            peers = index.get(keys[tier], ())
            if not peers:
                continue
            typical = _median(peer.price_typical for peer in peers)
            price_scope = _scope_mode(peers)
            result[material_id] = CatalogPriceCandidate(
                material_id=material_id,
                price_low=_round_price(typical * (Decimal("1") - downside)),
                price_typical=_round_price(typical),
                price_high=_round_price(typical * (Decimal("1") + downside * 2)),
                unit=material.base_unit,
                currency=currency,
                price_scope=price_scope,
                confidence=_round_price(confidence),
                tier=tier,
                methodology=(
                    f"{tier} median from {len(peers)} exact-price peers; "
                    "broad asymmetric uncertainty"
                ),
                offer_ids=tuple(
                    sorted(
                        {
                            offer_id
                            for peer in peers
                            if peer.price_scope == price_scope
                            for offer_id in peer.offer_ids
                        }
                    )
                ),
            )
            break

    return tuple(result[material_id] for material_id in sorted(result))
