from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping


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
