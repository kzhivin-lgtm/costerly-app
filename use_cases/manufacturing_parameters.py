from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from use_cases.manufacturing_costing import CalculatorIdentity, ValueRange


SUPPORTED_CALCULATORS: set[CalculatorIdentity] = {
    "cnc_router_in_house",
    "cnc_router_subcontractor",
    "sheet_laser_in_house",
    "sheet_laser_subcontractor",
}
SOURCE_PRIORITY = {
    "official": 50,
    "provider": 40,
    "manufacturer": 30,
    "research": 20,
    "platform_prior": 10,
}


class ManufacturingParameterError(ValueError):
    pass


@dataclass(frozen=True)
class ParameterScope:
    country_code: str = "IL"
    region: str | None = None
    material_family: str | None = None
    thickness_mm: Decimal | None = None
    machine_class: str | None = None
    object_family: str | None = None
    qualifiers: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if len(self.country_code) != 2 or self.country_code != self.country_code.upper():
            raise ManufacturingParameterError("country_code must be two uppercase letters.")
        if self.thickness_mm is not None:
            thickness = _decimal(self.thickness_mm, "thickness_mm")
            if thickness < 0:
                raise ManufacturingParameterError("thickness_mm cannot be negative.")
            object.__setattr__(self, "thickness_mm", thickness)
        object.__setattr__(self, "qualifiers", dict(self.qualifiers or {}))


@dataclass(frozen=True)
class ParameterRequirement:
    key: str
    unit: str
    currency: str | None = None


@dataclass(frozen=True)
class ManufacturingParameter:
    parameter_id: str
    calculator: CalculatorIdentity
    parameter_key: str
    country_code: str
    region: str | None
    material_family: str | None
    thickness_min_mm: Decimal | None
    thickness_max_mm: Decimal | None
    machine_class: str | None
    object_family: str | None
    qualifiers: Mapping[str, Any]
    value: ValueRange
    unit: str
    currency: str | None
    source_type: str
    source_name: str
    source_url: str
    source_date: date
    confidence: Decimal
    version: int
    effective_from: date
    effective_to: date | None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> ManufacturingParameter:
        calculator = str(row.get("calculator") or "")
        if calculator not in SUPPORTED_CALCULATORS:
            raise ManufacturingParameterError("Unsupported manufacturing calculator.")
        if str(row.get("status") or "") != "active":
            raise ManufacturingParameterError("Only Active manufacturing parameters may resolve.")
        source_type = str(row.get("source_type") or "")
        if source_type not in SOURCE_PRIORITY:
            raise ManufacturingParameterError("Unsupported manufacturing parameter source type.")
        source_url = str(row.get("source_url") or "").strip()
        if not source_url:
            raise ManufacturingParameterError("Active manufacturing parameter requires a source URL.")
        if not row.get("approved_by") or not row.get("approved_at"):
            raise ManufacturingParameterError("Active manufacturing parameter requires approval.")
        version = _integer(row.get("version"), "version")
        if version <= 0:
            raise ManufacturingParameterError("version must be positive.")
        confidence = _decimal(row.get("confidence"), "confidence")
        if confidence < 0 or confidence > 100:
            raise ManufacturingParameterError("confidence must be between 0 and 100.")
        qualifiers = row.get("qualifiers") or {}
        if not isinstance(qualifiers, Mapping):
            raise ManufacturingParameterError("qualifiers must be an object.")
        lower = _optional_decimal(row.get("thickness_min_mm"), "thickness_min_mm")
        upper = _optional_decimal(row.get("thickness_max_mm"), "thickness_max_mm")
        if lower is not None and lower < 0:
            raise ManufacturingParameterError("thickness_min_mm cannot be negative.")
        if upper is not None and upper < 0:
            raise ManufacturingParameterError("thickness_max_mm cannot be negative.")
        if lower is not None and upper is not None and lower > upper:
            raise ManufacturingParameterError("Invalid thickness range.")
        effective_from = _iso_date(row.get("effective_from"), "effective_from")
        effective_to = _optional_iso_date(row.get("effective_to"), "effective_to")
        if effective_to is not None and effective_from > effective_to:
            raise ManufacturingParameterError("Invalid effective date range.")
        currency = str(row.get("currency") or "").strip() or None
        if currency is not None and (len(currency) != 3 or currency != currency.upper()):
            raise ManufacturingParameterError("currency must be a three-letter uppercase code.")
        return cls(
            parameter_id=_required_text(row.get("parameter_id"), "parameter_id"),
            calculator=calculator,  # type: ignore[arg-type]
            parameter_key=_required_text(row.get("parameter_key"), "parameter_key"),
            country_code=_required_text(row.get("country_code"), "country_code"),
            region=_optional_text(row.get("region")),
            material_family=_optional_text(row.get("material_family")),
            thickness_min_mm=lower,
            thickness_max_mm=upper,
            machine_class=_optional_text(row.get("machine_class")),
            object_family=_optional_text(row.get("object_family")),
            qualifiers=dict(qualifiers),
            value=ValueRange(
                _decimal(row.get("value_low"), "value_low"),
                _decimal(row.get("value_typical"), "value_typical"),
                _decimal(row.get("value_high"), "value_high"),
            ),
            unit=_required_text(row.get("unit"), "unit"),
            currency=currency,
            source_type=source_type,
            source_name=_required_text(row.get("source_name"), "source_name"),
            source_url=source_url,
            source_date=_iso_date(row.get("source_date"), "source_date"),
            confidence=confidence,
            version=version,
            effective_from=effective_from,
            effective_to=effective_to,
        )


@dataclass(frozen=True)
class ResolvedParameterSet:
    calculator: CalculatorIdentity
    values: Mapping[str, ManufacturingParameter]
    missing_keys: tuple[str, ...]
    ambiguous_keys: tuple[str, ...]
    schema_version: str = "manufacturing_parameter_resolution_v1"

    @property
    def needs_review(self) -> bool:
        return bool(self.missing_keys or self.ambiguous_keys)

    @property
    def parameter_ids(self) -> tuple[str, ...]:
        return tuple(parameter.parameter_id for parameter in self.values.values())

    def value_range(self, key: str) -> ValueRange:
        parameter = self.values.get(key)
        if parameter is None:
            raise ManufacturingParameterError(f"Parameter {key} was not resolved.")
        return parameter.value

    def require_complete(self) -> ResolvedParameterSet:
        if self.needs_review:
            unresolved = ", ".join((*self.missing_keys, *self.ambiguous_keys))
            raise ManufacturingParameterError(
                f"Manufacturing parameter set requires review: {unresolved}."
            )
        return self


def _required_text(value: Any, name: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ManufacturingParameterError(f"{name} is required.")
    return result


def _optional_text(value: Any) -> str | None:
    result = str(value or "").strip()
    return result or None


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ManufacturingParameterError(f"{name} must be numeric.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ManufacturingParameterError(f"{name} must be numeric.") from exc
    if not result.is_finite():
        raise ManufacturingParameterError(f"{name} must be finite.")
    return result


def _optional_decimal(value: Any, name: str) -> Decimal | None:
    if value is None or value == "":
        return None
    return _decimal(value, name)


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ManufacturingParameterError(f"{name} must be an integer.")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ManufacturingParameterError(f"{name} must be an integer.") from exc
    if str(result) != str(value).strip():
        raise ManufacturingParameterError(f"{name} must be an integer.")
    return result


def _iso_date(value: Any, name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ManufacturingParameterError(f"{name} must be an ISO date.") from exc


def _optional_iso_date(value: Any, name: str) -> date | None:
    if value is None or value == "":
        return None
    return _iso_date(value, name)


def _field_specificity(record_value: str | None, requested_value: str | None) -> int | None:
    if requested_value is None:
        return 0 if record_value is None else None
    if record_value is None:
        return 0
    if record_value.casefold() == requested_value.casefold():
        return 1
    return None


def _thickness_specificity(parameter: ManufacturingParameter, requested: Decimal | None) -> int | None:
    lower = parameter.thickness_min_mm
    upper = parameter.thickness_max_mm
    if requested is None:
        return 0 if lower is None and upper is None else None
    if lower is not None and requested < lower:
        return None
    if upper is not None and requested > upper:
        return None
    return 1 if lower is not None or upper is not None else 0


def _qualifier_specificity(
    record_qualifiers: Mapping[str, Any],
    requested_qualifiers: Mapping[str, Any],
) -> int | None:
    for key, value in record_qualifiers.items():
        if key not in requested_qualifiers or requested_qualifiers[key] != value:
            return None
    return len(record_qualifiers)


def _match_rank(
    parameter: ManufacturingParameter,
    scope: ParameterScope,
) -> tuple[int, int, int] | None:
    if parameter.country_code != scope.country_code:
        return None
    specificities: list[int] = []
    for record_value, requested_value in (
        (parameter.region, scope.region),
        (parameter.material_family, scope.material_family),
        (parameter.machine_class, scope.machine_class),
        (parameter.object_family, scope.object_family),
    ):
        specificity = _field_specificity(record_value, requested_value)
        if specificity is None:
            return None
        specificities.append(specificity)
    thickness_specificity = _thickness_specificity(parameter, scope.thickness_mm)
    if thickness_specificity is None:
        return None
    qualifier_specificity = _qualifier_specificity(
        parameter.qualifiers,
        scope.qualifiers or {},
    )
    if qualifier_specificity is None:
        return None
    specificity = sum(specificities) + thickness_specificity + qualifier_specificity
    bounded_thickness_width = Decimal("Infinity")
    if parameter.thickness_min_mm is not None and parameter.thickness_max_mm is not None:
        bounded_thickness_width = parameter.thickness_max_mm - parameter.thickness_min_mm
    # Higher specificity wins. For two containing thickness bands, the narrower
    # band wins only after every named scope dimension has matched equally.
    width_rank = 0 if bounded_thickness_width.is_infinite() else -int(
        bounded_thickness_width * 1000
    )
    return specificity, width_rank, SOURCE_PRIORITY[parameter.source_type]


def resolve_manufacturing_parameters(
    rows: Sequence[Mapping[str, Any]],
    *,
    calculator: CalculatorIdentity,
    requirements: Sequence[ParameterRequirement],
    scope: ParameterScope,
    as_of: date | None = None,
) -> ResolvedParameterSet:
    if calculator not in SUPPORTED_CALCULATORS:
        raise ManufacturingParameterError("Unsupported manufacturing calculator.")
    effective_date = as_of or date.today()
    parsed: list[ManufacturingParameter] = []
    for row in rows:
        if str(row.get("status") or "") != "active":
            continue
        parameter = ManufacturingParameter.from_row(row)
        if parameter.calculator != calculator:
            continue
        if parameter.effective_from > effective_date:
            continue
        if parameter.effective_to is not None and parameter.effective_to < effective_date:
            continue
        parsed.append(parameter)

    values: dict[str, ManufacturingParameter] = {}
    missing: list[str] = []
    ambiguous: list[str] = []
    seen_requirement_keys: set[str] = set()
    for requirement in requirements:
        if requirement.key in seen_requirement_keys:
            raise ManufacturingParameterError(
                f"Duplicate parameter requirement: {requirement.key}."
            )
        seen_requirement_keys.add(requirement.key)
        candidates: list[tuple[tuple[int, int, int], ManufacturingParameter]] = []
        for parameter in parsed:
            if parameter.parameter_key != requirement.key:
                continue
            rank = _match_rank(parameter, scope)
            if rank is None:
                continue
            if parameter.unit != requirement.unit or parameter.currency != requirement.currency:
                raise ManufacturingParameterError(
                    f"Active parameter {requirement.key} has an incompatible unit or currency."
                )
            candidates.append((rank, parameter))
        if not candidates:
            missing.append(requirement.key)
            continue
        best_rank = max(rank for rank, _parameter in candidates)
        best = [parameter for rank, parameter in candidates if rank == best_rank]
        if len(best) != 1:
            ambiguous.append(requirement.key)
            continue
        values[requirement.key] = best[0]

    return ResolvedParameterSet(
        calculator=calculator,
        values=values,
        missing_keys=tuple(missing),
        ambiguous_keys=tuple(ambiguous),
    )


def load_active_manufacturing_parameter_rows(
    client: Any,
    *,
    calculator: CalculatorIdentity,
    country_code: str = "IL",
) -> list[dict[str, Any]]:
    if calculator not in SUPPORTED_CALCULATORS:
        raise ManufacturingParameterError("Unsupported manufacturing calculator.")
    if len(country_code) != 2 or country_code != country_code.upper():
        raise ManufacturingParameterError("country_code must be two uppercase letters.")
    response = (
        client.table("manufacturing_cost_parameters")
        .select("*")
        .eq("calculator", calculator)
        .eq("country_code", country_code)
        .eq("status", "active")
        .execute()
    )
    return [dict(row) for row in (response.data or [])]
