"""Deterministic project-level material purchasing plans.

The Material Engine is intentionally independent of OCR, visual interpretation
and catalog identity matching.  It receives already-resolved material demands
and compatible purchasable candidates, aggregates every compatible demand in
one estimate, and chooses the least-cost complete purchase plan.  This keeps
sheet nesting and stock rounding at estimate scope rather than on individual
objects or parts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Literal, Mapping, Sequence


PurchaseKind = Literal["sheet", "linear_stock", "linear_cut", "volume_direct", "piece", "direct"]
PlanStatus = Literal["planned", "needs_review"]


class MaterialEngineError(ValueError):
    """Raised when a caller gives the deterministic engine an invalid fact."""


def _decimal(value: Decimal | int | float | str, field: str) -> Decimal:
    if isinstance(value, bool):
        raise MaterialEngineError(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MaterialEngineError(f"{field} must be numeric") from exc
    if not result.is_finite():
        raise MaterialEngineError(f"{field} must be finite")
    return result


def _positive(value: Decimal | int | float | str, field: str) -> Decimal:
    result = _decimal(value, field)
    if result <= 0:
        raise MaterialEngineError(f"{field} must be positive")
    return result


def _whole(value: Decimal, field: str) -> int:
    if value != value.to_integral_value():
        raise MaterialEngineError(f"{field} must be a whole number")
    return int(value)


@dataclass(frozen=True)
class MaterialDemand:
    """One physical requirement produced by one estimate part.

    ``selection_key`` is built by the Material Resolver from the material
    family and its completed Pricing Key.  It deliberately keeps product
    selection out of the Estimation Agent and makes only truly compatible
    demands eligible for consolidation.
    """

    demand_id: str
    object_id: str
    material_family: str
    selection_key: str
    quantity: Decimal | int | float | str
    unit: str
    compatible_candidate_ids: tuple[str, ...]
    part_id: str | None = None
    material_requirement_id: str | None = None
    length_mm: Decimal | int | float | str | None = None
    width_mm: Decimal | int | float | str | None = None
    area_mm2: Decimal | int | float | str | None = None
    linear_length_mm: Decimal | int | float | str | None = None
    volume_mm3: Decimal | int | float | str | None = None
    rotation_allowed: bool = True


@dataclass(frozen=True)
class MaterialSupplyCandidate:
    """A concrete purchase option pre-filtered by Material Resolver.

    ``price_per_purchase_unit`` is always ex VAT and in the purchase unit
    represented by ``purchase_kind``.  Converting source offer units into this
    value belongs at the Resolver boundary, before the Engine compares basket
    totals.
    """

    candidate_id: str
    material_family: str
    selection_key: str
    purchase_kind: PurchaseKind
    price_per_purchase_unit: Decimal | int | float | str
    currency: str = "ILS"
    purchasable_dimensions: Mapping[str, Decimal | int | float | str] | None = None
    package_quantity: Decimal | int | float | str = Decimal("1")
    kerf_mm: Decimal | int | float | str = Decimal("0")
    authority: Literal["company", "israel_reference"] = "company"
    offer_id: str | None = None
    reference_price_id: str | None = None


@dataclass(frozen=True)
class MaterialAllocation:
    demand_id: str
    purchase_index: int
    object_id: str
    material_requirement_id: str | None = None
    length_mm: Decimal | None = None
    width_mm: Decimal | None = None
    area_mm2: Decimal | None = None
    volume_mm3: Decimal | None = None
    quantity: Decimal | None = None
    rotated: bool = False


@dataclass(frozen=True)
class MaterialPurchaseLine:
    selection_key: str
    candidate_id: str
    purchase_kind: PurchaseKind
    purchase_quantity: Decimal
    price_per_purchase_unit: Decimal
    total_cost: Decimal
    currency: str
    allocations: tuple[MaterialAllocation, ...]


@dataclass(frozen=True)
class MaterialPlan:
    status: PlanStatus
    lines: tuple[MaterialPurchaseLine, ...]
    unresolved_demand_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    algorithm_version: str = "material_engine_v1"


@dataclass(frozen=True)
class _CandidatePlan:
    line: MaterialPurchaseLine | None
    reason_code: str | None = None


def _candidate_dimensions(candidate: MaterialSupplyCandidate) -> tuple[Decimal, Decimal | None]:
    dimensions = dict(candidate.purchasable_dimensions or {})
    length = _positive(dimensions.get("length_mm"), "purchasable_dimensions.length_mm")
    width_value = dimensions.get("width_mm")
    width = _positive(width_value, "purchasable_dimensions.width_mm") if width_value is not None else None
    return length, width


def _demand_dimensions(demand: MaterialDemand) -> tuple[Decimal, Decimal]:
    if demand.length_mm is None or demand.width_mm is None:
        raise MaterialEngineError("sheet demand requires length_mm and width_mm")
    return (
        _positive(demand.length_mm, "demand.length_mm"),
        _positive(demand.width_mm, "demand.width_mm"),
    )


def _demand_quantity(demand: MaterialDemand, *, whole: bool = False) -> Decimal:
    quantity = _positive(demand.quantity, "demand.quantity")
    if whole:
        _whole(quantity, "demand.quantity")
    return quantity


def _demand_area(demand: MaterialDemand) -> Decimal | None:
    if demand.area_mm2 is None:
        return None
    return _positive(demand.area_mm2, "demand.area_mm2")


def _demand_linear_length(demand: MaterialDemand) -> Decimal | None:
    if demand.linear_length_mm is None:
        return None
    return _positive(demand.linear_length_mm, "demand.linear_length_mm")


def _demand_volume(demand: MaterialDemand) -> Decimal | None:
    if demand.volume_mm3 is None:
        return None
    return _positive(demand.volume_mm3, "demand.volume_mm3")


def _ceil(value: Decimal) -> Decimal:
    return value.to_integral_value(rounding=ROUND_CEILING)


def _validate_candidate(candidate: MaterialSupplyCandidate) -> None:
    if not candidate.candidate_id or not candidate.selection_key or not candidate.material_family:
        raise MaterialEngineError("candidate id, family and selection key are required")
    _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    _positive(candidate.package_quantity, "candidate.package_quantity")
    kerf = _decimal(candidate.kerf_mm, "candidate.kerf_mm")
    if kerf < 0:
        raise MaterialEngineError("candidate.kerf_mm cannot be negative")
    if candidate.purchase_kind in {"sheet", "linear_stock"}:
        _candidate_dimensions(candidate)


def _place_sheet_parts(
    *, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate
) -> _CandidatePlan:
    sheet_length, sheet_width = _candidate_dimensions(candidate)
    if sheet_width is None:
        raise MaterialEngineError("sheet candidate requires width_mm")
    kerf = _decimal(candidate.kerf_mm, "candidate.kerf_mm")
    parts: list[tuple[Decimal, Decimal, MaterialDemand, int, bool]] = []
    aggregate_demands: list[tuple[MaterialDemand, Decimal]] = []
    direct_sheet_demands: list[tuple[MaterialDemand, int]] = []
    for demand in demands:
        if str(demand.unit or "").strip().casefold() in {"sheet", "sheets"}:
            direct_sheet_demands.append((
                demand,
                _whole(_demand_quantity(demand, whole=True), "demand.quantity"),
            ))
            continue
        area = _demand_area(demand)
        if area is not None:
            aggregate_demands.append((demand, area))
            continue
        quantity = _whole(_demand_quantity(demand, whole=True), "demand.quantity")
        length, width = _demand_dimensions(demand)
        for index in range(quantity):
            parts.append((length, width, demand, index, demand.rotation_allowed))
    # Largest rectangles first gives a deterministic, conservative nesting
    # heuristic.  The plan records the exact placements, so a later optimiser
    # can replace this strategy without changing the external contract.
    parts.sort(key=lambda part: (-part[0] * part[1], -max(part[0], part[1]), part[2].demand_id, part[3]))
    sheets: list[list[tuple[Decimal, Decimal, Decimal, Decimal]]] = []
    allocations: list[MaterialAllocation] = []

    for length, width, demand, _index, rotation_allowed in parts:
        # Kerf is clearance between rectangular cuts.  Inflating each part is
        # deliberately conservative and avoids hiding a kerf requirement in a
        # percentage-waste rule.
        orientations = [(length + kerf, width + kerf, False)]
        if rotation_allowed and length != width:
            orientations.append((width + kerf, length + kerf, True))
        placed = False
        for sheet_index, free_rectangles in enumerate(sheets, start=1):
            for free_index, (x, y, free_length, free_width) in enumerate(tuple(free_rectangles)):
                fitting = [
                    orientation for orientation in orientations
                    if orientation[0] <= free_length and orientation[1] <= free_width
                ]
                if not fitting:
                    continue
                used_length, used_width, rotated = min(
                    fitting,
                    key=lambda orientation: (
                        min(free_length - orientation[0], free_width - orientation[1]),
                        max(free_length - orientation[0], free_width - orientation[1]),
                        orientation[2],
                    ),
                )
                del free_rectangles[free_index]
                right = (x + used_length, y, free_length - used_length, used_width)
                below = (x, y + used_width, free_length, free_width - used_width)
                if right[2] > 0 and right[3] > 0:
                    free_rectangles.append(right)
                if below[2] > 0 and below[3] > 0:
                    free_rectangles.append(below)
                allocations.append(MaterialAllocation(
                    demand_id=demand.demand_id, purchase_index=sheet_index,
                    object_id=demand.object_id,
                    material_requirement_id=demand.material_requirement_id,
                    length_mm=length, width_mm=width, quantity=Decimal("1"), rotated=rotated,
                ))
                placed = True
                break
            if placed:
                break
        if placed:
            continue
        fitting = [
            orientation for orientation in orientations
            if orientation[0] <= sheet_length and orientation[1] <= sheet_width
        ]
        if not fitting:
            return _CandidatePlan(line=None, reason_code="demand_exceeds_purchasable_sheet")
        used_length, used_width, rotated = min(
            fitting,
            key=lambda orientation: (sheet_length - orientation[0], sheet_width - orientation[1], orientation[2]),
        )
        free_rectangles = []
        right = (used_length, Decimal("0"), sheet_length - used_length, used_width)
        below = (Decimal("0"), used_width, sheet_length, sheet_width - used_width)
        if right[2] > 0 and right[3] > 0:
            free_rectangles.append(right)
        if below[2] > 0 and below[3] > 0:
            free_rectangles.append(below)
        sheets.append(free_rectangles)
        allocations.append(MaterialAllocation(
            demand_id=demand.demand_id, purchase_index=len(sheets),
            object_id=demand.object_id,
            material_requirement_id=demand.material_requirement_id,
            length_mm=length, width_mm=width, quantity=Decimal("1"), rotated=rotated,
        ))

    # A row already expressed in sheets is a physical purchase instruction,
    # not a geometric area that should be re-nested.
    for demand, quantity in direct_sheet_demands:
        for _ in range(quantity):
            sheets.append([])
            allocations.append(MaterialAllocation(
                demand_id=demand.demand_id,
                purchase_index=len(sheets),
                object_id=demand.object_id,
                material_requirement_id=demand.material_requirement_id,
                quantity=Decimal("1"),
            ))

    # A manual norm is intentionally allowed without invented part geometry.
    # It cannot safely consume fragmented offcuts left by known rectangles:
    # area alone does not prove that a physical piece fits.  It therefore adds
    # whole sheets by area. This deliberately conservative commercial estimate
    # never claims that an exact cut layout exists for the manual adjustment.
    sheet_capacity = sheet_length * sheet_width
    for demand, area in aggregate_demands:
        outstanding = area
        while outstanding > 0:
            used = min(outstanding, sheet_capacity)
            sheets.append([])
            outstanding -= used
            allocations.append(MaterialAllocation(
                demand_id=demand.demand_id, purchase_index=len(sheets),
                object_id=demand.object_id,
                material_requirement_id=demand.material_requirement_id,
                area_mm2=used,
            ))

    price = _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    quantity = Decimal(len(sheets))
    return _CandidatePlan(line=MaterialPurchaseLine(
        selection_key=candidate.selection_key,
        candidate_id=candidate.candidate_id,
        purchase_kind="sheet",
        purchase_quantity=quantity,
        price_per_purchase_unit=price,
        total_cost=price * quantity,
        currency=candidate.currency,
        allocations=tuple(allocations),
    ))


def _place_linear_stock(
    *, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate
) -> _CandidatePlan:
    stock_length, _unused_width = _candidate_dimensions(candidate)
    kerf = _decimal(candidate.kerf_mm, "candidate.kerf_mm")
    cuts: list[tuple[Decimal, MaterialDemand, int]] = []
    aggregate_demands: list[tuple[MaterialDemand, Decimal]] = []
    for demand in demands:
        aggregate_length = _demand_linear_length(demand)
        if aggregate_length is not None:
            aggregate_demands.append((demand, aggregate_length))
            continue
        quantity = _whole(_demand_quantity(demand, whole=True), "demand.quantity")
        if demand.length_mm is None:
            raise MaterialEngineError("linear-stock demand requires length_mm")
        length = _positive(demand.length_mm, "demand.length_mm") + kerf
        for index in range(quantity):
            cuts.append((length, demand, index))
    cuts.sort(key=lambda cut: (-cut[0], cut[1].demand_id, cut[2]))
    remaining: list[Decimal] = []
    allocations: list[MaterialAllocation] = []
    for length, demand, _index in cuts:
        if length > stock_length:
            return _CandidatePlan(line=None, reason_code="demand_exceeds_purchasable_stock")
        selected = next((index for index, free in enumerate(remaining) if free >= length), None)
        if selected is None:
            remaining.append(stock_length - length)
            selected = len(remaining) - 1
        else:
            remaining[selected] -= length
        allocations.append(MaterialAllocation(
            demand_id=demand.demand_id, purchase_index=selected + 1,
            object_id=demand.object_id,
            material_requirement_id=demand.material_requirement_id,
            length_mm=length - kerf, quantity=Decimal("1"),
        ))

    for demand, aggregate_length in aggregate_demands:
        outstanding = aggregate_length
        for stock_index, free_length in enumerate(remaining, start=1):
            if outstanding <= 0:
                break
            used = min(outstanding, free_length)
            if used <= 0:
                continue
            remaining[stock_index - 1] -= used
            outstanding -= used
            allocations.append(MaterialAllocation(
                demand_id=demand.demand_id, purchase_index=stock_index,
                object_id=demand.object_id,
                material_requirement_id=demand.material_requirement_id,
                length_mm=used,
            ))
        while outstanding > 0:
            used = min(outstanding, stock_length)
            remaining.append(stock_length - used)
            outstanding -= used
            allocations.append(MaterialAllocation(
                demand_id=demand.demand_id, purchase_index=len(remaining),
                object_id=demand.object_id,
                material_requirement_id=demand.material_requirement_id,
                length_mm=used,
            ))
    price = _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    quantity = Decimal(len(remaining))
    return _CandidatePlan(line=MaterialPurchaseLine(
        selection_key=candidate.selection_key,
        candidate_id=candidate.candidate_id,
        purchase_kind="linear_stock",
        purchase_quantity=quantity,
        price_per_purchase_unit=price,
        total_cost=price * quantity,
        currency=candidate.currency,
        allocations=tuple(allocations),
    ))


def _place_linear_cut(*, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate) -> _CandidatePlan:
    total_length = Decimal("0")
    allocations: list[MaterialAllocation] = []
    for demand in demands:
        length = _demand_linear_length(demand)
        if length is None:
            length = _positive(demand.length_mm, "demand.length_mm") * _demand_quantity(demand, whole=True)
        total_length += length
        allocations.append(MaterialAllocation(demand_id=demand.demand_id, purchase_index=1,
            object_id=demand.object_id, material_requirement_id=demand.material_requirement_id, length_mm=length))
    quantity = total_length / Decimal("1000")
    price = _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    return _CandidatePlan(line=MaterialPurchaseLine(selection_key=candidate.selection_key,
        candidate_id=candidate.candidate_id, purchase_kind="linear_cut", purchase_quantity=quantity,
        price_per_purchase_unit=price, total_cost=price * quantity, currency=candidate.currency,
        allocations=tuple(allocations)))


def _place_volume_direct(*, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate) -> _CandidatePlan:
    allocations, total = [], Decimal("0")
    for demand in demands:
        volume = _demand_volume(demand)
        if volume is None:
            return _CandidatePlan(line=None, reason_code="demand_volume_required")
        total += volume
        allocations.append(MaterialAllocation(demand_id=demand.demand_id, purchase_index=1,
            object_id=demand.object_id, material_requirement_id=demand.material_requirement_id, volume_mm3=volume))
    quantity = total / Decimal("1000000000")
    price = _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    return _CandidatePlan(line=MaterialPurchaseLine(selection_key=candidate.selection_key,
        candidate_id=candidate.candidate_id, purchase_kind="volume_direct", purchase_quantity=quantity,
        price_per_purchase_unit=price, total_cost=price * quantity, currency=candidate.currency,
        allocations=tuple(allocations)))


def _plan_piece_or_direct(
    *, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate
) -> _CandidatePlan:
    total = sum((_demand_quantity(demand) for demand in demands), Decimal("0"))
    package_quantity = _positive(candidate.package_quantity, "candidate.package_quantity")
    if candidate.purchase_kind == "piece":
        purchase_quantity = _ceil(total / package_quantity)
    else:
        purchase_quantity = total / package_quantity
    price = _positive(candidate.price_per_purchase_unit, "candidate.price_per_purchase_unit")
    allocations = tuple(
        MaterialAllocation(
            demand_id=demand.demand_id,
            purchase_index=1,
            object_id=demand.object_id,
            material_requirement_id=demand.material_requirement_id,
            quantity=_demand_quantity(demand),
        )
        for demand in demands
    )
    return _CandidatePlan(line=MaterialPurchaseLine(
        selection_key=candidate.selection_key,
        candidate_id=candidate.candidate_id,
        purchase_kind=candidate.purchase_kind,
        purchase_quantity=purchase_quantity,
        price_per_purchase_unit=price,
        total_cost=price * purchase_quantity,
        currency=candidate.currency,
        allocations=allocations,
    ))


def _plan_candidate(
    *, demands: Sequence[MaterialDemand], candidate: MaterialSupplyCandidate
) -> _CandidatePlan:
    _validate_candidate(candidate)
    if candidate.purchase_kind == "sheet":
        return _place_sheet_parts(demands=demands, candidate=candidate)
    if candidate.purchase_kind == "linear_stock":
        return _place_linear_stock(demands=demands, candidate=candidate)
    if candidate.purchase_kind == "linear_cut":
        return _place_linear_cut(demands=demands, candidate=candidate)
    if candidate.purchase_kind == "volume_direct":
        return _place_volume_direct(demands=demands, candidate=candidate)
    return _plan_piece_or_direct(demands=demands, candidate=candidate)


def plan_material_purchases(
    *, demands: Sequence[MaterialDemand], candidates: Sequence[MaterialSupplyCandidate]
) -> MaterialPlan:
    """Build a deterministic, estimate-wide purchase plan.

    The caller supplies only candidates already cleared by Material Resolver.
    A candidate must cover every demand in its ``selection_key`` group.  The
    winner is the lowest complete purchasable basket cost, then candidate id,
    so an inexpensive unit price cannot win if it requires more sheets or
    stock bars.
    """
    demands_by_key: dict[str, list[MaterialDemand]] = {}
    for demand in demands:
        if not demand.demand_id or not demand.object_id or not demand.material_family or not demand.selection_key:
            raise MaterialEngineError("demand id, object id, family and selection key are required")
        if not demand.compatible_candidate_ids:
            raise MaterialEngineError("demand must have compatible candidate ids")
        demands_by_key.setdefault(demand.selection_key, []).append(demand)
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    if len(candidate_by_id) != len(candidates):
        raise MaterialEngineError("candidate ids must be unique")

    lines: list[MaterialPurchaseLine] = []
    unresolved: list[str] = []
    reasons: set[str] = set()
    for selection_key in sorted(demands_by_key):
        group = tuple(demands_by_key[selection_key])
        common_ids = set(group[0].compatible_candidate_ids)
        for demand in group[1:]:
            common_ids.intersection_update(demand.compatible_candidate_ids)
        possible: list[MaterialPurchaseLine] = []
        group_reasons: set[str] = set()
        for candidate_id in sorted(common_ids):
            candidate = candidate_by_id.get(candidate_id)
            if candidate is None or candidate.selection_key != selection_key:
                continue
            plan = _plan_candidate(demands=group, candidate=candidate)
            if plan.line is not None:
                possible.append(plan.line)
            elif plan.reason_code:
                group_reasons.add(plan.reason_code)
        if not possible:
            unresolved.extend(demand.demand_id for demand in group)
            reasons.update(group_reasons or {"no_complete_purchase_candidate"})
            continue
        # The accepted commercial rule is company-first, then Israel fallback.
        # Price is compared only inside the authority lane that can supply the
        # complete group, never across Company and Israel candidates.
        company_possible = [
            line for line in possible
            if candidate_by_id[line.candidate_id].authority == "company"
        ]
        eligible = company_possible or possible
        currencies = {line.currency for line in eligible}
        if len(currencies) > 1:
            unresolved.extend(demand.demand_id for demand in group)
            reasons.add("candidate_currency_conflict")
            continue
        lines.append(min(eligible, key=lambda line: (line.total_cost, line.candidate_id)))

    return MaterialPlan(
        status="planned" if not unresolved else "needs_review",
        lines=tuple(lines),
        unresolved_demand_ids=tuple(sorted(unresolved)),
        reason_codes=tuple(sorted(reasons)),
    )
