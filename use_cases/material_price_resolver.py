from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from statistics import median
from typing import Any, Literal, Mapping, Sequence


ResolutionStatus = Literal["resolved", "needs_review"]
PriceAuthority = Literal["company", "market_baseline"]

_SIX_PLACES = Decimal("0.000001")
_UNIT_ALIASES = {
    "piece": "ea",
    "pieces": "ea",
    "unit": "ea",
    "units": "ea",
    "m": "lm",
    "meter": "lm",
    "metre": "lm",
    "m2": "sqm",
    "m²": "sqm",
    "liter": "l",
    "litre": "l",
}
_UNIT_FACTORS = {
    "mass": {"g": Decimal("0.001"), "kg": Decimal("1")},
    "volume": {"ml": Decimal("0.001"), "l": Decimal("1")},
    "length": {
        "mm": Decimal("0.001"),
        "cm": Decimal("0.01"),
        "lm": Decimal("1"),
    },
    "area": {"cm2": Decimal("0.0001"), "sqm": Decimal("1")},
}


class MaterialPriceResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedMaterialPrice:
    status: ResolutionStatus
    reference_material_id: str
    unit: str
    currency: str
    price_low: Decimal | None = None
    price_typical: Decimal | None = None
    price_high: Decimal | None = None
    authority: PriceAuthority | None = None
    price_scope: str | None = None
    confidence: Decimal | None = None
    company_offer_ids: tuple[str, ...] = ()
    baseline_id: str | None = None
    reason_codes: tuple[str, ...] = ()
    schema_version: str = "material_price_resolution_v1"

    @property
    def needs_review(self) -> bool:
        return self.status == "needs_review"

    def require_resolved(self) -> ResolvedMaterialPrice:
        if self.needs_review:
            reasons = ", ".join(self.reason_codes) or "unresolved"
            raise MaterialPriceResolutionError(
                f"Material price requires review: {reasons}."
            )
        return self


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise MaterialPriceResolutionError(f"{name} must be numeric.")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MaterialPriceResolutionError(f"{name} must be numeric.") from exc
    if not parsed.is_finite():
        raise MaterialPriceResolutionError(f"{name} must be finite.")
    return parsed


def _date(value: Any, name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise MaterialPriceResolutionError(f"{name} must be an ISO date.") from exc


def _canonical_unit(value: Any) -> str:
    unit = str(value or "").strip().casefold()
    return _UNIT_ALIASES.get(unit, unit)


def _unit_price_multiplier(source_unit: str, target_unit: str) -> Decimal | None:
    source = _canonical_unit(source_unit)
    target = _canonical_unit(target_unit)
    if not source or not target:
        return None
    if source == target:
        return Decimal("1")
    for factors in _UNIT_FACTORS.values():
        if source in factors and target in factors:
            return factors[target] / factors[source]
    return None


def _round_price(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACES, rounding=ROUND_HALF_UP)


def _effective(row: Mapping[str, Any], as_of: date) -> bool:
    valid_from = row.get("valid_from") or row.get("effective_from")
    valid_to = row.get("valid_to") or row.get("effective_to")
    if valid_from and _date(valid_from, "valid_from") > as_of:
        return False
    if valid_to and _date(valid_to, "valid_to") < as_of:
        return False
    return True


def _company_candidate(
    row: Mapping[str, Any],
    *,
    reference_material_id: str,
    requested_unit: str,
    currency: str,
    as_of: date,
    vat_percent: Decimal | None,
    price_scope: str | None,
) -> tuple[Decimal, Decimal, str, str] | None:
    if str(row.get("status") or "") != "active":
        return None
    if str(row.get("reference_material_id") or "") != reference_material_id:
        return None
    if str(row.get("currency") or "").upper() != currency:
        return None
    row_scope = str(row.get("price_scope") or "material_only")
    if price_scope is not None and row_scope != price_scope:
        return None
    if not _effective(row, as_of):
        return None
    multiplier = _unit_price_multiplier(
        str(row.get("normalized_unit") or ""),
        requested_unit,
    )
    if multiplier is None:
        return None
    price = _decimal(row.get("normalized_price"), "normalized_price")
    if price <= 0:
        return None
    vat_included = row.get("vat_included")
    if vat_included is None:
        return None
    if vat_included:
        if vat_percent is None or vat_percent < 0:
            return None
        price = price / (Decimal("1") + vat_percent / Decimal("100"))
    confidence = _decimal(row.get("confidence"), "confidence")
    if confidence < 0 or confidence > 100:
        return None
    offer_id = str(row.get("offer_id") or "").strip()
    if not offer_id:
        return None
    return _round_price(price * multiplier), confidence, offer_id, row_scope


def _baseline_candidate(
    row: Mapping[str, Any],
    *,
    reference_material_id: str,
    requested_unit: str,
    currency: str,
    market_code: str,
    price_scope: str | None,
    as_of: date,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str] | None:
    if str(row.get("status") or "") != "active":
        return None
    if str(row.get("material_id") or "") != reference_material_id:
        return None
    if str(row.get("market_code") or "") != market_code:
        return None
    if str(row.get("currency") or "").upper() != currency:
        return None
    row_scope = str(row.get("price_scope") or "")
    if price_scope is not None and row_scope != price_scope:
        return None
    if not _effective(row, as_of):
        return None
    multiplier = _unit_price_multiplier(str(row.get("unit") or ""), requested_unit)
    if multiplier is None:
        return None
    low = _decimal(row.get("price_low"), "price_low") * multiplier
    typical = _decimal(row.get("price_typical"), "price_typical") * multiplier
    high = _decimal(row.get("price_high"), "price_high") * multiplier
    if low < 0 or not low <= typical <= high:
        return None
    confidence = _decimal(row.get("confidence"), "confidence")
    if confidence < 0 or confidence > 100:
        return None
    baseline_id = str(row.get("baseline_id") or "").strip()
    if not baseline_id:
        return None
    return (
        _round_price(low),
        _round_price(typical),
        _round_price(high),
        confidence,
        baseline_id,
        row_scope,
    )


def resolve_material_price(
    *,
    reference_material_id: str,
    requested_unit: str,
    currency: str,
    market_code: str,
    company_offer_rows: Sequence[Mapping[str, Any]],
    market_baseline_rows: Sequence[Mapping[str, Any]],
    price_scope: str | None = None,
    vat_percent: Decimal | int | str | None = None,
    as_of: date | None = None,
) -> ResolvedMaterialPrice:
    """Resolve an ex-VAT price with company data before the market baseline."""

    material_id = str(reference_material_id or "").strip()
    unit = _canonical_unit(requested_unit)
    resolved_currency = str(currency or "").strip().upper()
    market = str(market_code or "").strip().upper()
    if not material_id:
        raise MaterialPriceResolutionError("reference_material_id is required.")
    if not unit:
        raise MaterialPriceResolutionError("requested_unit is required.")
    if len(resolved_currency) != 3:
        raise MaterialPriceResolutionError("currency must be a three-letter code.")
    if len(market) != 2:
        raise MaterialPriceResolutionError("market_code must be a two-letter code.")
    effective_date = as_of or date.today()
    vat = _decimal(vat_percent, "vat_percent") if vat_percent is not None else None
    if vat is not None and (vat < 0 or vat > 100):
        raise MaterialPriceResolutionError("vat_percent must be between 0 and 100.")

    company_candidates = tuple(
        candidate
        for row in company_offer_rows
        if (
            candidate := _company_candidate(
                row,
                reference_material_id=material_id,
                requested_unit=unit,
                currency=resolved_currency,
                as_of=effective_date,
                vat_percent=vat,
                price_scope=price_scope,
            )
        )
        is not None
    )
    reason_codes: list[str] = []
    company_scopes = {candidate[3] for candidate in company_candidates}
    if len(company_scopes) == 1:
        prices = sorted(candidate[0] for candidate in company_candidates)
        confidences = sorted(candidate[1] for candidate in company_candidates)
        return ResolvedMaterialPrice(
            status="resolved",
            reference_material_id=material_id,
            unit=unit,
            currency=resolved_currency,
            price_low=_round_price(prices[0]),
            price_typical=_round_price(Decimal(str(median(prices)))),
            price_high=_round_price(prices[-1]),
            authority="company",
            price_scope=next(iter(company_scopes)),
            confidence=_round_price(Decimal(str(median(confidences)))),
            company_offer_ids=tuple(
                sorted(row[2] for row in company_candidates)
            ),
        )
    if len(company_scopes) > 1:
        reason_codes.append("ambiguous_company_price_scope")
    elif company_offer_rows:
        reason_codes.append("company_offer_not_usable")
    baseline_candidates = tuple(
        candidate
        for row in market_baseline_rows
        if (
            candidate := _baseline_candidate(
                row,
                reference_material_id=material_id,
                requested_unit=unit,
                currency=resolved_currency,
                market_code=market,
                price_scope=price_scope,
                as_of=effective_date,
            )
        )
        is not None
    )
    if len(baseline_candidates) == 1:
        low, typical, high, confidence, baseline_id, scope = baseline_candidates[0]
        return ResolvedMaterialPrice(
            status="resolved",
            reference_material_id=material_id,
            unit=unit,
            currency=resolved_currency,
            price_low=low,
            price_typical=typical,
            price_high=high,
            authority="market_baseline",
            price_scope=scope,
            confidence=confidence,
            baseline_id=baseline_id,
            reason_codes=tuple(reason_codes),
        )
    if len(baseline_candidates) > 1:
        reason_codes.append("ambiguous_market_baseline")
    else:
        reason_codes.append("market_baseline_not_found")
    return ResolvedMaterialPrice(
        status="needs_review",
        reference_material_id=material_id,
        unit=unit,
        currency=resolved_currency,
        reason_codes=tuple(reason_codes),
    )


def load_material_price_rows(
    client: Any,
    *,
    company_id: str,
    reference_material_id: str,
    market_code: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load only rows eligible to participate in one material resolution."""

    material_rows = (
        client.table("company_material_items")
        .select("company_material_id,reference_material_id,status")
        .eq("company_id", company_id)
        .eq("reference_material_id", reference_material_id)
        .neq("status", "archived")
        .execute()
    ).data or []
    material_ids = [str(row["company_material_id"]) for row in material_rows]
    company_rows: list[dict[str, Any]] = []
    if material_ids:
        company_rows = (
            client.table("company_material_offers")
            .select(
                "offer_id,company_material_id,normalized_price,normalized_unit,"
                "currency,vat_included,valid_from,confidence,status,created_at"
            )
            .eq("company_id", company_id)
            .eq("status", "active")
            .in_("company_material_id", material_ids)
            .execute()
        ).data or []
        reference_by_company_material = {
            str(row["company_material_id"]): str(row["reference_material_id"])
            for row in material_rows
        }
        company_rows = [
            {
                **dict(row),
                "reference_material_id": reference_by_company_material.get(
                    str(row.get("company_material_id"))
                ),
            }
            for row in company_rows
        ]

    baseline_rows = (
        client.table("market_material_baselines")
        .select(
            "baseline_id,material_id,market_code,region,price_low,price_typical,"
            "price_high,unit,currency,price_scope,confidence,status,effective_from,"
            "effective_to,version"
        )
        .eq("material_id", reference_material_id)
        .eq("market_code", market_code)
        .eq("status", "active")
        .execute()
    ).data or []
    return company_rows, [dict(row) for row in baseline_rows]


def resolve_company_first_material_price(
    client: Any,
    *,
    company_id: str,
    reference_material_id: str,
    requested_unit: str,
    currency: str = "ILS",
    market_code: str = "IL",
    price_scope: str | None = None,
    vat_percent: Decimal | int | str | None = None,
    as_of: date | None = None,
) -> ResolvedMaterialPrice:
    company_rows, baseline_rows = load_material_price_rows(
        client,
        company_id=company_id,
        reference_material_id=reference_material_id,
        market_code=market_code,
    )
    return resolve_material_price(
        reference_material_id=reference_material_id,
        requested_unit=requested_unit,
        currency=currency,
        market_code=market_code,
        company_offer_rows=company_rows,
        market_baseline_rows=baseline_rows,
        price_scope=price_scope,
        vat_percent=vat_percent,
        as_of=as_of,
    )
