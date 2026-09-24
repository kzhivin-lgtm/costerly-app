from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import TYPE_CHECKING, Mapping, Sequence

from db.company_access import assert_company_owner
from db.supabase_client import get_supabase_client

if TYPE_CHECKING:
    from state.company_auth import CompanyAccess


PRICING_METHODS = {
    "unknown",
    "hourly",
    "per_sheet",
    "per_part",
    "per_job",
    "quote_only",
}
STRUCTURED_PRICING_METHODS = {"hourly", "per_sheet", "per_part", "per_job"}


class MachineryError(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityField:
    key: str
    label: str
    kind: str = "number"
    unit: str | None = None
    input_unit: str | None = None
    required: bool = False
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class MachineSpec:
    code: str
    industry: str
    display_name: str
    description: str
    fields: tuple[CapabilityField, ...]


def _number(
    key: str,
    label: str,
    unit: str,
    *,
    input_unit: str | None = None,
    required: bool = False,
) -> CapabilityField:
    return CapabilityField(key, label, "number", unit, input_unit, required)


def _multi(key: str, label: str, options: Sequence[str], *, required: bool = False) -> CapabilityField:
    return CapabilityField(key, label, "multiselect", None, None, required, tuple(options))


def _text(key: str, label: str, *, required: bool = False) -> CapabilityField:
    return CapabilityField(key, label, "text", None, None, required)


def _boolean(key: str, label: str) -> CapabilityField:
    return CapabilityField(key, label, "boolean")


WOOD_MATERIALS = ("MDF", "Particleboard / LDSP", "Plywood", "Solid wood", "Compact laminate", "Plastic")
METAL_MATERIALS = ("Mild steel", "Stainless steel", "Aluminum", "Brass", "Copper")


MACHINE_SPECS: tuple[MachineSpec, ...] = (
    MachineSpec("wood_cnc_router", "woodworking", "CNC router", "Routing, drilling and profiling sheet goods or solid wood", (
        _number("work_area_x_mm", "Working area, length", "mm", input_unit="m", required=True),
        _number("work_area_y_mm", "Working area, width", "mm", input_unit="m", required=True),
        _number("max_thickness_mm", "Maximum workpiece thickness", "mm"),
        _multi("materials", "Materials normally processed", WOOD_MATERIALS, required=True),
        _boolean("two_sided_processing", "Two-sided processing is supported"),
    )),
    MachineSpec("wood_panel_saw", "woodworking", "Panel cutting saw", "Straight panel sizing and cutting", (
        _number("max_cut_length_mm", "Maximum cut length", "mm", input_unit="m", required=True),
        _number("max_thickness_mm", "Maximum stack or panel thickness", "mm"),
        _multi("materials", "Panel materials", WOOD_MATERIALS[:3], required=True),
    )),
    MachineSpec("wood_edge_bander", "woodworking", "Edge bander", "Application and finishing of panel edge material", (
        _number("max_panel_thickness_mm", "Maximum panel thickness", "mm"),
        _number("max_edge_thickness_mm", "Maximum edge thickness", "mm"),
        _multi("edge_materials", "Edge materials", ("Melamine", "PVC", "ABS", "Veneer", "Solid wood")),
    )),
    MachineSpec("wood_boring_machine", "woodworking", "Boring machine", "Repeatable construction and hardware drilling", (
        _number("max_panel_length_mm", "Maximum panel length", "mm", input_unit="m"),
        _number("max_panel_width_mm", "Maximum panel width", "mm", input_unit="m"),
        _boolean("cnc_controlled", "CNC-controlled drilling"),
    )),
    MachineSpec("wood_veneer_press", "woodworking", "Veneer or laminating press", "Flat pressing of veneer or laminate", (
        _number("platen_length_mm", "Press length", "mm", input_unit="m", required=True),
        _number("platen_width_mm", "Press width", "mm", input_unit="m", required=True),
        _boolean("heated", "Heated press"),
    )),
    MachineSpec("wood_solid_preparation", "woodworking", "Solid wood preparation line", "Planing, thicknessing and dimensioning solid wood", (
        _number("max_width_mm", "Maximum working width", "mm", input_unit="m"),
        _number("max_thickness_mm", "Maximum workpiece thickness", "mm"),
        _multi("processes", "Available operations", ("Jointing", "Thickness planing", "Rip sawing", "Crosscutting", "Moulding"), required=True),
    )),
    MachineSpec("wood_wide_belt_sander", "woodworking", "Wide-belt sander or calibrator", "Calibrating and sanding panels or solid wood", (
        _number("max_width_mm", "Maximum working width", "mm", input_unit="m", required=True),
        _number("min_thickness_mm", "Minimum workpiece thickness", "mm"),
        _multi("materials", "Materials", WOOD_MATERIALS[:4]),
    )),
    MachineSpec("wood_case_clamp", "woodworking", "Case clamp or assembly press", "Squaring and pressing assembled cases", (
        _number("max_length_mm", "Maximum case width", "mm", input_unit="m"),
        _number("max_height_mm", "Maximum case height", "mm", input_unit="m"),
        _number("max_depth_mm", "Maximum case depth", "mm", input_unit="m"),
    )),
    MachineSpec("metal_sheet_laser", "metalworking", "Sheet laser cutter", "Profile cutting of sheet metal", (
        _number("work_area_x_mm", "Working area, length", "mm", input_unit="m", required=True),
        _number("work_area_y_mm", "Working area, width", "mm", input_unit="m", required=True),
        _text("material_thickness_limits", "Materials and maximum thicknesses", required=True),
        _number("laser_power_kw", "Laser power", "kW"),
    )),
    MachineSpec("metal_tube_laser", "metalworking", "Tube laser cutter", "Profile cutting of tube and section", (
        _number("max_stock_length_mm", "Maximum stock length", "mm", input_unit="m", required=True),
        _number("max_profile_size_mm", "Maximum profile diameter or side", "mm", required=True),
        _text("material_thickness_limits", "Materials and maximum wall thicknesses", required=True),
    )),
    MachineSpec("metal_press_brake", "metalworking", "Press brake", "Controlled bending of sheet metal", (
        _number("max_bend_length_mm", "Maximum bend length", "mm", input_unit="m", required=True),
        _number("tonnage_t", "Press force", "t", required=True),
        _text("material_thickness_limits", "Typical material and thickness limits"),
    )),
    MachineSpec("metal_sheet_shear", "metalworking", "Sheet shear or guillotine", "Straight cutting of sheet metal", (
        _number("max_cut_length_mm", "Maximum cut length", "mm", input_unit="m", required=True),
        _text("material_thickness_limits", "Material and thickness limits"),
    )),
    MachineSpec("metal_punch_press", "metalworking", "Punching or hydraulic press", "Punching, stamping and press operations", (
        _number("tonnage_t", "Press force", "t", required=True),
        _number("bed_length_mm", "Working bed length", "mm", input_unit="m"),
        _number("bed_width_mm", "Working bed width", "mm", input_unit="m"),
        _text("processes", "Typical press operations"),
    )),
    MachineSpec("metal_profile_saw", "metalworking", "Tube or profile saw", "Length and mitre cutting of profiles", (
        _number("max_profile_size_mm", "Maximum profile diameter or side", "mm"),
        _boolean("mitre_cutting", "Mitre cutting is supported"),
        _multi("materials", "Materials", METAL_MATERIALS),
    )),
    MachineSpec("metal_profile_bender", "metalworking", "Tube or profile bender", "Controlled bending of tube and profiles", (
        _number("max_profile_size_mm", "Maximum profile diameter or side", "mm"),
        _text("profile_limits", "Typical profiles and wall-thickness limits"),
    )),
    MachineSpec("metal_rolling_machine", "metalworking", "Plate or section rolling machine", "Rolling plate and sections to a radius", (
        _number("max_working_width_mm", "Maximum working width", "mm", input_unit="m"),
        _text("material_thickness_limits", "Material and thickness limits"),
    )),
    MachineSpec("metal_welding", "metalworking", "Welding capability", "MIG, MAG, TIG or other welding processes", (
        _multi("processes", "Welding processes", ("MIG / MAG", "TIG", "MMA / stick", "Spot welding", "Robotic welding"), required=True),
        _multi("materials", "Materials", METAL_MATERIALS, required=True),
    )),
    MachineSpec("metal_deburring", "metalworking", "Deburring or grinding machine", "Edge cleanup, deburring and grinding", (
        _number("max_width_mm", "Maximum working width", "mm", input_unit="m"),
        _multi("processes", "Processes", ("Deburring", "Edge rounding", "Grinding", "Brushing")),
    )),
    MachineSpec("metal_drill_tap", "metalworking", "Drill or tapping station", "Hole drilling, countersinking and tapping", (
        _number("max_drill_diameter_mm", "Maximum drilling diameter", "mm"),
        _text("thread_range", "Typical tapping range"),
    )),
    MachineSpec("finish_wet_spray_booth", "finishing", "Wet-paint spray booth", "Controlled wet coating application", (
        _number("max_part_length_mm", "Maximum part length", "mm", input_unit="m"),
        _number("max_part_width_mm", "Maximum part width", "mm", input_unit="m"),
        _number("max_part_height_mm", "Maximum part height", "mm", input_unit="m"),
        _multi("coating_families", "Coating families", ("Paint", "Lacquer", "Varnish", "Stain", "Oil")),
    )),
    MachineSpec("finish_drying_chamber", "finishing", "Drying or curing chamber", "Controlled drying or curing of wet finishes", (
        _number("max_part_length_mm", "Maximum part length", "mm", input_unit="m"),
        _number("max_temperature_c", "Maximum temperature", "°C"),
    )),
    MachineSpec("finish_powder_booth", "finishing", "Powder-coating booth", "Controlled powder application and recovery", (
        _number("max_part_length_mm", "Maximum part length", "mm", input_unit="m"),
        _number("max_part_width_mm", "Maximum part width", "mm", input_unit="m"),
        _number("max_part_height_mm", "Maximum part height", "mm", input_unit="m"),
    )),
    MachineSpec("finish_powder_oven", "finishing", "Powder-curing oven", "Thermal curing of powder coating", (
        _number("inside_length_mm", "Internal length", "mm", input_unit="m", required=True),
        _number("inside_width_mm", "Internal width", "mm", input_unit="m", required=True),
        _number("inside_height_mm", "Internal height", "mm", input_unit="m", required=True),
        _number("max_temperature_c", "Maximum temperature", "°C"),
    )),
    MachineSpec("finish_sandblast_booth", "finishing", "Sandblasting booth", "Abrasive surface preparation", (
        _number("max_part_length_mm", "Maximum part length", "mm", input_unit="m"),
        _number("max_part_width_mm", "Maximum part width", "mm", input_unit="m"),
        _number("max_part_height_mm", "Maximum part height", "mm", input_unit="m"),
    )),
    MachineSpec("finish_wash_line", "finishing", "Washing or degreasing line", "Cleaning and pretreatment before coating", (
        _number("max_part_length_mm", "Maximum part length", "mm", input_unit="m"),
        _multi("processes", "Processes", ("Degreasing", "Rinsing", "Phosphating", "Conversion coating")),
    )),
    MachineSpec("finish_polishing", "finishing", "Polishing or buffing station", "Mechanical polishing and buffing", (
        _multi("materials", "Materials", METAL_MATERIALS + ("Solid wood", "Plastic")),
        _text("finish_range", "Typical finish range"),
    )),
)

MACHINE_SPEC_BY_CODE = {spec.code: spec for spec in MACHINE_SPECS}
INDUSTRY_LABELS = {
    "woodworking": "Woodworking",
    "metalworking": "Metalworking",
    "finishing": "Painting & Finishing",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _normalized_name(value: str) -> str:
    return re.sub(r"[^\w]+", " ", value.casefold(), flags=re.UNICODE).strip()


def _require_company(access: CompanyAccess) -> str:
    company_id = _clean_text(access.company_id)
    if not company_id:
        raise PermissionError("Company access is required.")
    return company_id


def _validate_capabilities(machine_code: str, values: Mapping[str, object]) -> dict:
    spec = MACHINE_SPEC_BY_CODE.get(machine_code)
    if spec is None:
        raise MachineryError("Unknown machinery catalog item.")
    allowed = {field.key: field for field in spec.fields}
    result: dict[str, object] = {}
    for key, raw_value in values.items():
        field = allowed.get(key)
        if field is None:
            continue
        if field.kind == "number":
            if raw_value in (None, ""):
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise MachineryError(f"{field.label} must be a number.") from exc
            if value == 0:
                continue
            if value < 0:
                raise MachineryError(f"{field.label} must be greater than zero.")
            result[key] = value
        elif field.kind == "boolean":
            result[key] = bool(raw_value)
        elif field.kind == "multiselect":
            selected = [str(item) for item in (raw_value or []) if str(item) in field.options]
            if selected:
                result[key] = selected
        else:
            cleaned = _clean_text(raw_value)
            if cleaned:
                result[key] = cleaned
    missing = [field.label for field in spec.fields if field.required and not result.get(field.key)]
    if missing:
        raise MachineryError("Complete the required fields: " + ", ".join(missing))
    return result


def _validate_pricing(method: str, values: Mapping[str, object]) -> tuple[str, dict]:
    if method not in PRICING_METHODS:
        raise MachineryError("Choose a valid pricing method.")
    if method in {"unknown", "quote_only"}:
        return method, {}
    try:
        rate = float(values.get("rate") or 0)
    except (TypeError, ValueError) as exc:
        raise MachineryError("Enter a valid customer rate.") from exc
    if rate <= 0:
        raise MachineryError("Enter a customer rate greater than zero.")
    currency = _clean_text(values.get("currency")).upper()
    if len(currency) != 3:
        raise MachineryError("Enter a three-letter currency code.")
    pricing: dict[str, object] = {"rate": rate, "currency": currency}
    rate_kind = _clean_text(values.get("rate_kind"))
    if rate_kind:
        if rate_kind not in {"internal_cost", "customer_price", "supplier_quote"}:
            raise MachineryError("Choose a valid rate type.")
        pricing["rate_kind"] = rate_kind
    for key in ("setup_fee", "minimum_charge"):
        if values.get(key) not in (None, ""):
            try:
                amount = float(values[key])
            except (TypeError, ValueError) as exc:
                raise MachineryError("Setup fee and minimum charge must be numbers.") from exc
            if amount < 0:
                raise MachineryError("Setup fee and minimum charge cannot be negative.")
            pricing[key] = amount
    return method, pricing


def list_company_machinery(access: CompanyAccess) -> list[dict]:
    company_id = _require_company(access)
    return (
        get_supabase_client().table("company_machinery")
        .select("company_machine_id,company_id,machine_code,availability_status,display_name,capabilities,pricing_method,pricing,accepts_external_work,source,verified_at,active,updated_at")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []


def list_company_suppliers(access: CompanyAccess) -> list[dict]:
    company_id = _require_company(access)
    return (
        get_supabase_client().table("company_suppliers")
        .select("supplier_id,supplier_name,categories,active")
        .eq("company_id", company_id)
        .eq("active", True)
        .order("supplier_name")
        .execute()
    ).data or []


def list_supplier_services(access: CompanyAccess) -> list[dict]:
    company_id = _require_company(access)
    return (
        get_supabase_client().table("company_supplier_services")
        .select("supplier_service_id,company_id,supplier_id,machine_code,capabilities,pricing_method,pricing,typical_lead_time_days,preferred,verified_at,active,updated_at")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []


def save_company_machinery(
    access: CompanyAccess,
    *,
    machine_code: str,
    availability_status: str,
    capabilities: Mapping[str, object] | None = None,
    pricing_method: str = "unknown",
    pricing: Mapping[str, object] | None = None,
    accepts_external_work: bool | None = None,
) -> dict:
    company_id = _require_company(access)
    if machine_code not in MACHINE_SPEC_BY_CODE:
        raise MachineryError("Unknown machinery catalog item.")
    if availability_status not in {"in_house", "not_in_house"}:
        raise MachineryError("Choose whether this capability is available in-house.")
    client = get_supabase_client()
    assert_company_owner(client, access.user_id, company_id)
    if availability_status == "in_house":
        clean_capabilities = _validate_capabilities(machine_code, capabilities or {})
        clean_method, clean_pricing = _validate_pricing(pricing_method, pricing or {})
        external_work = bool(accepts_external_work)
    else:
        clean_capabilities = {}
        clean_method = "unknown"
        clean_pricing = {}
        external_work = None
    payload = {
        "company_id": company_id,
        "machine_code": machine_code,
        "availability_status": availability_status,
        "capabilities": clean_capabilities,
        "pricing_method": clean_method,
        "pricing": clean_pricing,
        "accepts_external_work": external_work,
        "source": "owner_confirmed",
        "verified_at": _now(),
        "active": True,
        "updated_at": _now(),
    }
    rows = (
        client.table("company_machinery")
        .upsert(payload, on_conflict="company_id,machine_code")
        .execute()
    ).data or []
    if not rows:
        raise MachineryError("Machinery settings could not be saved.")
    return rows[0]


def create_or_get_supplier(access: CompanyAccess, supplier_name: str) -> dict:
    company_id = _require_company(access)
    clean_name = _clean_text(supplier_name)
    normalized = _normalized_name(clean_name)
    if not normalized:
        raise MachineryError("Enter the supplier name.")
    client = get_supabase_client()
    assert_company_owner(client, access.user_id, company_id)
    existing = (
        client.table("company_suppliers")
        .select("supplier_id,supplier_name,categories,active")
        .eq("company_id", company_id)
        .eq("normalized_name", normalized)
        .limit(1)
        .execute()
    ).data or []
    categories = sorted(set((existing[0].get("categories") or []) + ["production_services"])) if existing else ["production_services"]
    rows = (
        client.table("company_suppliers")
        .upsert(
            {
                "company_id": company_id,
                "supplier_name": clean_name,
                "normalized_name": normalized,
                "categories": categories,
                "active": True,
                "updated_at": _now(),
            },
            on_conflict="company_id,normalized_name",
        )
        .execute()
    ).data or []
    if not rows:
        raise MachineryError("The supplier could not be saved.")
    return rows[0]


def save_supplier_service(
    access: CompanyAccess,
    *,
    supplier_id: str,
    machine_code: str,
    pricing_method: str = "quote_only",
    pricing: Mapping[str, object] | None = None,
    typical_lead_time_days: object = None,
    preferred: bool = True,
) -> dict:
    company_id = _require_company(access)
    if machine_code not in MACHINE_SPEC_BY_CODE:
        raise MachineryError("Unknown machinery catalog item.")
    client = get_supabase_client()
    assert_company_owner(client, access.user_id, company_id)
    supplier_rows = (
        client.table("company_suppliers")
        .select("supplier_id")
        .eq("company_id", company_id)
        .eq("supplier_id", supplier_id)
        .eq("active", True)
        .limit(1)
        .execute()
    ).data or []
    if not supplier_rows:
        raise PermissionError("Supplier is not available to this company.")
    clean_method, clean_pricing = _validate_pricing(pricing_method, pricing or {})
    lead_time = None
    if typical_lead_time_days not in (None, ""):
        try:
            lead_time = float(typical_lead_time_days)
        except (TypeError, ValueError) as exc:
            raise MachineryError("Lead time must be a number of days.") from exc
        if lead_time < 0:
            raise MachineryError("Lead time cannot be negative.")
    rows = (
        client.table("company_supplier_services")
        .upsert(
            {
                "company_id": company_id,
                "supplier_id": supplier_id,
                "machine_code": machine_code,
                "pricing_method": clean_method,
                "pricing": clean_pricing,
                "typical_lead_time_days": lead_time,
                "preferred": bool(preferred),
                "verified_at": _now(),
                "active": True,
                "updated_at": _now(),
            },
            on_conflict="company_id,supplier_id,machine_code",
        )
        .execute()
    ).data or []
    if not rows:
        raise MachineryError("The supplier service could not be saved.")
    return rows[0]


def deactivate_supplier_services(access: CompanyAccess, *, machine_code: str) -> None:
    """Deactivate current routing choices while retaining their audit history."""
    company_id = _require_company(access)
    if machine_code not in MACHINE_SPEC_BY_CODE:
        raise MachineryError("Unknown machinery catalog item.")
    client = get_supabase_client()
    assert_company_owner(client, access.user_id, company_id)
    (
        client.table("company_supplier_services")
        .update({"active": False, "preferred": False, "updated_at": _now()})
        .eq("company_id", company_id)
        .eq("machine_code", machine_code)
        .eq("active", True)
        .execute()
    )


def build_company_production_context(company_id: str, *, client=None) -> dict:
    """Build a bounded, deterministic snapshot for Estimation Agent input."""
    company_id = _clean_text(company_id)
    if not company_id:
        raise MachineryError("Company is required for production routing.")
    client = client or get_supabase_client()
    machinery = (
        client.table("company_machinery")
        .select("machine_code,availability_status,capabilities,pricing_method,pricing,accepts_external_work,verified_at")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []
    suppliers = (
        client.table("company_suppliers")
        .select("supplier_id,supplier_name")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []
    supplier_names = {str(row["supplier_id"]): row.get("supplier_name") for row in suppliers}
    services = (
        client.table("company_supplier_services")
        .select("supplier_service_id,supplier_id,machine_code,capabilities,pricing_method,pricing,typical_lead_time_days,preferred,verified_at")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []
    for row in services:
        row["supplier_name"] = supplier_names.get(str(row.get("supplier_id")))
    service_ids = [row["supplier_service_id"] for row in services if row.get("supplier_service_id")]
    offers: list[dict] = []
    if service_ids:
        offers = (
            client.table("company_service_offers")
            .select("service_offer_id,supplier_service_id,source_price,source_unit,currency,vat_included,setup_fee,minimum_charge,material_included,delivery_included,valid_from,confidence,created_at")
            .eq("company_id", company_id)
            .eq("status", "active")
            .in_("supplier_service_id", service_ids)
            .order("created_at", desc=True)
            .execute()
        ).data or []
    return {
        "schema_version": "machinery_context_v1",
        "generated_at": _now(),
        "company_id": company_id,
        "machines": machinery,
        "supplier_services": services,
        "active_supplier_offers": offers,
        "price_precedence": [
            "active_supplier_offer",
            "supplier_quote_history",
            "confirmed_in_house_rate",
            "regional_market_benchmark",
            "needs_review",
        ],
        "routing_rules": {
            "manual_fallback_requires_explicit_confirmation": True,
            "panel_material_manual_fallback_allowed": False,
            "powder_coating_requires": ["finish_powder_booth", "finish_powder_oven"],
        },
    }
