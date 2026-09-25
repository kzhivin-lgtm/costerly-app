from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import logging
from pathlib import Path
import time
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import streamlit as st

from db.company_access import assert_company_owner
from db.supabase_client import get_supabase_client
from styles.company_profile import apply_company_profile_css
from styles.object_detail import apply_object_detail_css
from ui import company_metrics_view
from ui.company_labor_bridge import company_labor_bridge
from ui.company_metrics_bridge import company_metrics_bridge
from ui.js_guards import (
    install_company_logo_picker_guard,
    install_company_metrics_input_guard,
    install_price_source_processing_guard,
    install_upload_dragover_guard,
)
from use_cases.email_addresses import is_valid_email_address
from use_cases.company_logo import (
    CompanyLogoError,
    NormalizedCompanyLogo,
    load_company_logo_bytes,
    normalize_company_logo,
    persist_company_logo,
)
from use_cases.price_sources import (
    PRICE_CATALOG_DEPARTMENTS,
    PriceSourceError,
    canonical_price_source_category,
    combine_price_source_files,
    list_price_catalog,
    list_price_sources,
    load_price_source_bytes,
    load_price_source_rows,
    process_price_source,
)
from use_cases.machinery import (
    INDUSTRY_LABELS,
    PROFILE_COSTING_MACHINE_CODES,
    PROFILE_MACHINE_SPECS,
    SUBCONTRACTOR_MACHINE_CODES,
    MachineryError,
    create_or_get_supplier,
    deactivate_company_machinery,
    deactivate_supplier_services,
    list_company_machinery,
    list_company_suppliers,
    list_supplier_services,
    save_company_machinery,
    save_supplier_service,
)

if TYPE_CHECKING:
    from state.company_auth import CompanyAccess


logger = logging.getLogger(__name__)


PROFILE_COLUMNS = (
    "company_id,company_name,legal_name,legal_name_hebrew,"
    "company_registration_number,vat_file_number,public_email,public_phone,"
    "website_url,address_street,address_house_number,address_city,"
    "address_postal_code,address_country,linkedin_url,instagram_url,facebook_url,"
    "bank_name,bank_number,branch_number,account_number,iban,swift,logo_url"
)
PROFILE_FIELDS = tuple(
    field for field in PROFILE_COLUMNS.split(",") if field not in {"company_id", "logo_url"}
)
METRIC_SETTING_FIELDS = (
    "vat_percent",
    "warranty_reserve_percent",
    "management_buffer_percent",
)
METRIC_SETTING_INSERT_DEFAULTS = {
    "vat_percent": 18,
    "employer_load_percent": 25,
    "labor_contingency_percent": 10,
    "warranty_reserve_percent": 5,
    "management_buffer_percent": 5,
    "design_bureau_commission_percent": 0,
    "production_workers": 12,
    "workdays_per_month": 21,
    "hours_per_day": 8,
    "sale_price_markup_percent": 30,
    "delivery_percent": 3,
    "installation_percent": 10,
}
METRIC_GROUPS = (
    (
        "Facility / Rent / Arnona",
        (
            ("rent_facilities_cost", "Rent"),
            ("arnona_facilities_cost", "Arnona"),
            ("maintenance_fee_facilities_cost", "Maintenance fee"),
        ),
    ),
    (
        "Utilities / Safety",
        (
            ("electricity_utilities_cost", "Electricity"),
            ("water_utilities_cost", "Water"),
            ("compressed_air_gas_utilities_cost", "Compressed air / gas"),
            ("insurance_safety_fire_utilities_cost", "Insurance / safety / fire"),
        ),
    ),
    (
        "Machinery / Equipment",
        (
            ("equipment_depreciation_machinery_cost", "Equipment depreciation"),
            ("machine_consumables_wear_machinery_cost", "Machine consumables / wear"),
        ),
    ),
    (
        "Software / Shop Supplies / Waste",
        (
            ("software_subscriptions_admin_cost", "Software subscriptions"),
            ("shop_supplies_cleaning_admin_cost", "Shop supplies / cleaning"),
            ("waste_removal_admin_cost", "Waste removal"),
        ),
    ),
    (
        "Other Spendings",
        (("other_spendings_cost", "Other spendings"),),
    ),
)
METRIC_MONTHLY_FIELDS = tuple(
    field for _group, rows in METRIC_GROUPS for field, _label in rows
)
LABOR_DEPARTMENTS = {
    "management": "Management",
    "office": "Office",
    "production": "Production",
}
LABOR_POSITIONS = {
    "management": (
        ("owner_director", "Owner / Director"),
        ("general_manager", "General Manager"),
        ("project_manager", "Project Manager"),
        ("production_manager", "Production Manager"),
    ),
    "office": (
        ("accountant", "Accountant"),
        ("office_administrator", "Office Administrator"),
        ("estimator", "Estimator"),
        ("sales_manager", "Sales Manager"),
        ("designer_draftsperson", "Designer"),
    ),
    "production": (
        ("carpenter", "Carpenter"),
        ("welder", "Welder"),
        ("cnc_operator", "CNC Operator"),
        ("painter_finisher", "Painter"),
        ("installer", "Installer"),
        ("general_worker", "Worker"),
    ),
}
LABOR_LEGACY_POSITION_LABELS = {
    "cabinetmaker_joiner": "Carpenter",
}
LABOR_PAY_TYPES = {
    "monthly_salary": "Monthly Salary",
    "hourly_rate": "Hourly Rate",
}
LABOR_EMPLOYEE_COLUMNS = (
    "employee_id,company_id,worker_name,department,position_code,"
    "pay_type,gross_monthly_salary,gross_hourly_rate,monthly_hours,"
    "employment_factor,total_hourly_cost,total_monthly_cost,deleted_at,created_at"
)
LABOR_DEFAULT_EMPLOYMENT_FACTOR = 1.25
LABOR_EMPLOYMENT_FACTOR_HELP = (
    "**Includes:**\n"
    "- Employer pension\n"
    "- Severance pay\n"
    "- National Insurance (Bituach Leumi)\n"
    "- Vacation and public holidays\n"
    "- Sick leave\n"
    "- Recuperation pay\n\n"
    "**Excludes:**\n"
    "- Overtime\n"
    "- Shabbat and holiday premiums\n"
    "- Bonuses\n"
    "- Meals"
)


def _current_access(access: CompanyAccess) -> CompanyAccess:
    from state.company_auth import current_company_access

    fresh = current_company_access()
    if (
        fresh is None
        or fresh.user_id != access.user_id
        or fresh.company_id is None
        or fresh.company_id != access.company_id
    ):
        raise PermissionError("Company access changed. Please sign in again.")
    return fresh


def _clean(value: object) -> str:
    return str(value or "").strip()


def _optional(value: object) -> str | None:
    cleaned = _clean(value)
    return cleaned or None


def _brand_mark() -> str:
    try:
        return Path("assets/brand/costelry_mark_indigo.svg").read_text()
    except OSError:
        return ""


IN_HOUSE_PRICING_OPTIONS = {
    "unknown": ("Not provided", "unknown", None),
    "hourly": ("Per machine hour", "hourly", None),
    "sheet": ("Per sheet", "per_sheet", None),
    "part": ("Per part", "per_part", None),
    "job": ("Per job", "per_job", None),
    "quote_only": ("Quote each job", "quote_only", None),
}
SUPPLIER_PRICING_OPTIONS = {
    "quote_only": ("Quote each job", "quote_only", None),
    "hourly": ("Per machine hour", "hourly", "supplier_quote"),
    "sheet": ("Per sheet", "per_sheet", "supplier_quote"),
    "part": ("Per part", "per_part", "supplier_quote"),
    "job": ("Per job", "per_job", "supplier_quote"),
    "unknown": ("Not provided", "unknown", None),
}
MACHINERY_PRICING_LABELS = {
    "unknown": "Not provided",
    "hourly": "Per machine hour",
    "per_sheet": "Per sheet",
    "per_part": "Per part",
    "per_job": "Per job",
    "quote_only": "Quote each job",
}


def _machinery_field_default(saved: dict, key: str, fallback=None):
    return (saved.get("capabilities") or {}).get(key, fallback)


def _machinery_number_text(field, saved_value: object) -> str:
    if saved_value in (None, ""):
        return ""
    try:
        value = float(saved_value)
    except (TypeError, ValueError):
        return str(saved_value)
    if field.unit == "mm" and field.input_unit == "m":
        value /= 1000
    return f"{value:g}"


def _machinery_number_storage_value(field, entered_value: object) -> object:
    text = str(entered_value or "").strip().replace(" ", "").replace(",", ".")
    if not text:
        return ""
    try:
        value = float(text)
    except ValueError:
        return text
    if field.unit == "mm" and field.input_unit == "m":
        value *= 1000
    return value


def _render_machine_capability_widget(field, saved: dict, key_prefix: str) -> object:
    display_unit = field.input_unit or field.unit
    unit_label = f" ({display_unit})" if display_unit else ""
    label = f"{field.label}{unit_label}{' *' if field.required else ''}"
    widget_key = f"{key_prefix}_{field.key}"
    default = _machinery_field_default(saved, field.key)
    if field.kind == "number":
        entered = st.text_input(
            label,
            value=_machinery_number_text(field, default),
            placeholder="e.g. 2.8" if display_unit == "m" else "",
            key=widget_key,
        )
        return _machinery_number_storage_value(field, entered)
    if field.kind == "multiselect":
        selected = st.pills(
            label,
            list(field.options),
            default=[item for item in (default or []) if item in field.options],
            selection_mode="multi",
            key=widget_key,
            width="stretch",
        )
        return list(selected or [])
    if field.kind == "boolean":
        return st.checkbox(label, value=bool(default), key=widget_key)
    return st.text_input(
        label,
        value=str(default or ""),
        key=widget_key,
    )


def _render_machine_capability_fields(
    spec,
    saved: dict,
    key_prefix: str,
    *,
    fields=None,
) -> dict:
    values: dict[str, object] = {}
    fields = list(fields if fields is not None else spec.fields)
    for start in range(0, len(fields), 3):
        columns = st.columns(3)
        for column, field in zip(columns, fields[start : start + 3]):
            with column:
                values[field.key] = _render_machine_capability_widget(
                    field, saved, key_prefix
                )
    return values


def _render_machinery_pricing(
    saved: dict,
    key_prefix: str,
    *,
    supplier: bool = False,
    method_column=None,
    options=None,
) -> tuple[str, dict]:
    saved_method = str(saved.get("pricing_method") or "unknown")
    saved_kind = str((saved.get("pricing") or {}).get("rate_kind") or "")
    options = options or (
        SUPPLIER_PRICING_OPTIONS if supplier else IN_HOUSE_PRICING_OPTIONS
    )
    selected_key = next(
        (
            key for key, (_label, method, rate_kind) in options.items()
            if method == saved_method
            and (rate_kind is None or rate_kind == saved_kind)
        ),
        "quote_only" if supplier else "unknown",
    )
    if method_column is None:
        method_column = st.columns(3)[0]
    with method_column:
        option_key = st.selectbox(
            "Supplier pricing method" if supplier else "Costing method",
            list(options),
            index=list(options).index(selected_key),
            format_func=lambda value: options[value][0],
            key=f"{key_prefix}_pricing_method",
        )
    _label, method, rate_kind = options[option_key]
    values: dict[str, object] = {}
    if method in {"hourly", "per_sheet", "per_part", "per_job"}:
        saved_pricing = saved.get("pricing") or {}
        preserved_in_house_kind = (
            saved_kind
            if saved_method == method
            and saved_kind in {"internal_cost", "customer_price"}
            else "internal_cost"
        )
        values["rate_kind"] = (
            rate_kind if supplier else preserved_in_house_kind
        )
        rate_columns = st.columns(3)
        with rate_columns[0]:
            values["rate"] = st.number_input(
                "Rate *",
                min_value=0.0,
                value=float(saved_pricing.get("rate") or 0),
                step=1.0,
                key=f"{key_prefix}_rate",
            )
        with rate_columns[1]:
            values["currency"] = st.text_input(
                "Currency *",
                value=str(saved_pricing.get("currency") or "ILS"),
                max_chars=3,
                key=f"{key_prefix}_currency",
            )
        with rate_columns[2]:
            values["setup_fee"] = st.number_input(
                "Setup fee",
                min_value=0.0,
                value=float(saved_pricing.get("setup_fee") or 0),
                step=1.0,
                key=f"{key_prefix}_setup_fee",
            )
        minimum_columns = st.columns(3)
        with minimum_columns[0]:
            values["minimum_charge"] = st.number_input(
                "Minimum charge",
                min_value=0.0,
                value=float(saved_pricing.get("minimum_charge") or 0),
                step=1.0,
                key=f"{key_prefix}_minimum_charge",
            )
    return method, values


def _render_cnc_machine_rate(
    saved: dict,
    key_prefix: str,
    *,
    method_column,
) -> tuple[str, dict]:
    saved_method = str(saved.get("pricing_method") or "unknown")
    saved_pricing = saved.get("pricing") or {}
    currency = str(saved_pricing.get("currency") or "ILS").upper()
    saved_rate = saved_pricing.get("rate") if saved_method == "hourly" else ""
    widget_key = f"{key_prefix}_machine_rate"
    with method_column:
        entered_rate = st.text_input(
            f"Machine rate / hour ({currency})",
            value=(
                _labor_form_number(saved_rate, decimals=2, grouped=True)
                if saved_rate not in (None, "")
                else ""
            ),
            key=widget_key,
            on_change=_format_grouped_number_input,
            args=(widget_key,),
        )
    normalized_rate = (
        str(entered_rate or "")
        .strip()
        .replace("\u202f", "")
        .replace(" ", "")
        .replace(",", "")
    )
    if not normalized_rate:
        return "unknown", {}
    pricing: dict[str, object] = {
        "rate": normalized_rate,
        "currency": currency,
        "rate_kind": str(saved_pricing.get("rate_kind") or "internal_cost"),
    }
    for key in ("setup_fee", "minimum_charge"):
        if saved_pricing.get(key) not in (None, ""):
            pricing[key] = saved_pricing[key]
    return "hourly", pricing


def _render_member_machinery(machine_rows: dict[str, dict], service_rows: list[dict], supplier_names: dict[str, str]) -> None:
    configured = [spec for spec in PROFILE_MACHINE_SPECS if spec.code in machine_rows]
    if not configured:
        st.info("Machinery has not been configured yet")
        return
    for industry, title in INDUSTRY_LABELS.items():
        group = [spec for spec in configured if spec.industry == industry]
        if not group:
            continue
        st.subheader(title)
        for spec in group:
            row = machine_rows[spec.code]
            status = "In-house" if row.get("availability_status") == "in_house" else "Not in-house"
            with st.expander(f"{spec.display_name} · {status}"):
                capabilities = row.get("capabilities") or {}
                for field in spec.fields:
                    value = capabilities.get(field.key)
                    if value not in (None, "", []):
                        display_unit = field.input_unit or field.unit
                        display_value = (
                            _machinery_number_text(field, value)
                            if field.kind == "number" else value
                        )
                        suffix = f" {display_unit}" if display_unit else ""
                        st.markdown(f"**{field.label}:** {display_value}{suffix}")
                pricing_method = str(row.get("pricing_method") or "unknown")
                if pricing_method != "unknown":
                    st.markdown(f"**Pricing:** {MACHINERY_PRICING_LABELS.get(pricing_method, pricing_method)}")
                matching = [service for service in service_rows if service.get("machine_code") == spec.code]
                for service in matching:
                    supplier_name = supplier_names.get(str(service.get("supplier_id")), "Supplier")
                    st.markdown(f"**Regular subcontractor:** {supplier_name}")


def _machinery_saved_summary(
    spec,
    saved: dict,
    services: list[dict],
    supplier_names: dict[str, str],
) -> str:
    status = str(saved.get("availability_status") or "")
    if status == "not_in_house":
        matching = next(
            (
                service
                for service in services
                if service.get("machine_code") == spec.code
            ),
            None,
        )
        if matching:
            name = supplier_names.get(str(matching.get("supplier_id")), "Supplier")
            return f"Subcontractor: {name}"
        return ""
    if status != "in_house":
        return ""

    capabilities = saved.get("capabilities") or {}
    details: list[str] = []
    dimensions: list[tuple[str, str]] = []
    multi_added = False
    for field in spec.fields:
        value = capabilities.get(field.key)
        if value in (None, "", []):
            continue
        if field.kind == "number" and len(dimensions) < 2:
            unit = field.input_unit or field.unit or ""
            dimensions.append((_machinery_number_text(field, value), unit))
        elif field.kind == "multiselect" and not multi_added:
            details.append(", ".join(str(item) for item in value[:3]))
            multi_added = True
    if len(dimensions) >= 2 and dimensions[0][1] == dimensions[1][1]:
        details.insert(
            0,
            f"{dimensions[0][0]} × {dimensions[1][0]} {dimensions[0][1]}".strip(),
        )
    elif dimensions:
        details.insert(0, f"{dimensions[0][0]} {dimensions[0][1]}".strip())
    return " · ".join(["In-house", *details[:2]])


def _render_owner_machinery(
    access: CompanyAccess,
    machine_rows: dict[str, dict],
    services: list[dict],
    supplier_names: dict[str, str],
) -> None:
    for industry, title in INDUSTRY_LABELS.items():
        with st.container(key=f"company_machinery_group_{industry}", border=True):
            st.markdown(
                '<div class="company-machinery-table-head">'
                f'<span>{escape(title)}</span>'
                '<span>Available in-house?</span>'
                '<span aria-hidden="true"></span>'
                '</div>',
                unsafe_allow_html=True,
            )
            for spec in (
                item for item in PROFILE_MACHINE_SPECS if item.industry == industry
            ):
                saved = machine_rows.get(spec.code, {})
                saved_status = str(saved.get("availability_status") or "")
                initial = {
                    "in_house": "Yes",
                    "not_in_house": "No",
                }.get(saved_status, "Not answered")
                row_key = f"machinery_{spec.code}"
                detail_open_key = f"{row_key}_detail_open"
                previous_availability_key = f"{row_key}_previous_availability"
                availability_widget_key = f"{row_key}_availability"
                availability_reset_key = f"{row_key}_availability_reset"
                availability_error_key = f"{row_key}_availability_error"
                availability_only = (
                    not spec.fields
                    and spec.code not in PROFILE_COSTING_MACHINE_CODES
                    and spec.code not in SUBCONTRACTOR_MACHINE_CODES
                )
                if detail_open_key not in st.session_state:
                    st.session_state[detail_open_key] = False
                if previous_availability_key not in st.session_state:
                    st.session_state[previous_availability_key] = initial
                if availability_reset_key in st.session_state:
                    st.session_state[availability_widget_key] = st.session_state.pop(
                        availability_reset_key
                    )
                with st.container(key=f"{row_key}_row"):
                    name_column, answer_column, toggle_column = st.columns(
                        [1.45, 1, 0.13], gap="small"
                    )
                    with name_column:
                        st.markdown(
                            f'<div class="company-machinery-name">{escape(spec.display_name)}</div>',
                            unsafe_allow_html=True,
                        )
                        summary = _machinery_saved_summary(
                            spec, saved, services, supplier_names
                        )
                        if summary:
                            st.markdown(
                                '<div class="company-machinery-summary">'
                                f'{escape(summary)}</div>',
                                unsafe_allow_html=True,
                            )
                    with answer_column:
                        availability = st.segmented_control(
                            f"{spec.display_name}: available in-house?",
                            ["Not answered", "Yes", "No"],
                            default=initial,
                            key=availability_widget_key,
                            label_visibility="collapsed",
                            width="stretch",
                        )
                        availability_class = {
                            "Yes": "yes",
                            "No": "no",
                        }.get(availability, "not-answered")
                        st.markdown(
                            '<span class="machinery-availability-state '
                            f'machinery-selected-{availability_class}"></span>',
                            unsafe_allow_html=True,
                        )
                    availability_changed = (
                        availability != st.session_state[previous_availability_key]
                    )
                    with toggle_column:
                        if (
                            not availability_only
                            and (
                                availability == "Yes"
                                or (
                                    availability == "No"
                                    and spec.code in SUBCONTRACTOR_MACHINE_CODES
                                )
                            )
                            and st.button(
                                "⌃" if st.session_state[detail_open_key] else "⌄",
                                key=f"{row_key}_toggle",
                            )
                        ):
                            st.session_state[detail_open_key] = not st.session_state[
                                detail_open_key
                            ]
                if availability_error_key in st.session_state:
                    st.error(st.session_state.pop(availability_error_key))
                save_availability_directly = (
                    availability_only
                    or (
                        availability == "No"
                        and spec.code not in SUBCONTRACTOR_MACHINE_CODES
                    )
                )
                if save_availability_directly and availability_changed:
                    previous_availability = st.session_state[previous_availability_key]
                    try:
                        if availability == "Not answered":
                            deactivate_company_machinery(
                                access,
                                machine_code=spec.code,
                            )
                        else:
                            save_company_machinery(
                                access,
                                machine_code=spec.code,
                                availability_status=(
                                    "in_house" if availability == "Yes"
                                    else "not_in_house"
                                ),
                                accepts_external_work=False,
                            )
                        deactivate_supplier_services(access, machine_code=spec.code)
                        st.session_state[previous_availability_key] = availability
                        st.rerun()
                    except (MachineryError, PermissionError) as exc:
                        st.session_state[availability_reset_key] = previous_availability
                        st.session_state[availability_error_key] = str(exc)
                        st.rerun()
                    except Exception:
                        st.session_state[availability_reset_key] = previous_availability
                        st.session_state[availability_error_key] = (
                            "Machinery settings could not be saved. Try again"
                        )
                        st.rerun()
                if availability_changed:
                    st.session_state[detail_open_key] = (
                        availability != "Not answered"
                    )
                    st.session_state[previous_availability_key] = availability
                if (
                    availability_only
                    or (
                        availability == "No"
                        and spec.code not in SUBCONTRACTOR_MACHINE_CODES
                    )
                ):
                    continue
                if (
                    availability == "Not answered"
                    or not st.session_state[detail_open_key]
                ):
                    continue

                with st.container(key=f"{row_key}_detail"):
                    capabilities: dict[str, object] = {}
                    pricing_method = "unknown"
                    pricing: dict[str, object] = {}
                    subcontractor_name = ""
                    confirm_change = False
                    if availability == "Yes":
                        technical_fields = [
                            field for field in spec.fields
                            if field.kind not in {"multiselect", "boolean"}
                        ]
                        selector_fields = [
                            field for field in spec.fields
                            if field.kind == "multiselect"
                        ]
                        boolean_fields = [
                            field for field in spec.fields
                            if field.kind == "boolean"
                        ]
                        capabilities.update(
                            _render_machine_capability_fields(
                                spec,
                                saved,
                                row_key,
                                fields=technical_fields,
                            )
                        )
                        shows_costing = spec.code in PROFILE_COSTING_MACHINE_CODES
                        defer_costing = bool(
                            shows_costing and boolean_fields and not selector_fields
                        )
                        if len(selector_fields) == 1 and shows_costing:
                            selector_column, method_column = st.columns([2, 1])
                            with selector_column:
                                field = selector_fields[0]
                                capabilities[field.key] = _render_machine_capability_widget(
                                    field, saved, row_key
                                )
                            pricing_method, pricing = _render_machinery_pricing(
                                saved, row_key, method_column=method_column
                            )
                        elif selector_fields or (shows_costing and not defer_costing):
                            second_row = st.columns(3)
                            for index, field in enumerate(selector_fields[:2]):
                                with second_row[index]:
                                    capabilities[field.key] = (
                                        _render_machine_capability_widget(
                                            field, saved, row_key
                                        )
                                    )
                            if shows_costing:
                                pricing_method, pricing = _render_machinery_pricing(
                                    saved,
                                    row_key,
                                    method_column=second_row[
                                        min(len(selector_fields), 2)
                                    ],
                                )
                            if len(selector_fields) > 2:
                                capabilities.update(
                                    _render_machine_capability_fields(
                                        spec,
                                        saved,
                                        row_key,
                                        fields=selector_fields[2:],
                                    )
                                )
                        if boolean_fields and not defer_costing:
                            checkbox_row = st.columns(3)
                            for index, field in enumerate(boolean_fields[:3]):
                                with checkbox_row[index]:
                                    capabilities[field.key] = (
                                        _render_machine_capability_widget(
                                            field, saved, row_key
                                        )
                                    )
                        if defer_costing:
                            detail_row = st.columns(3)
                            first_column_count = 2 if len(boolean_fields) >= 3 else 1
                            with detail_row[0]:
                                for field in boolean_fields[:first_column_count]:
                                    capabilities[field.key] = (
                                        _render_machine_capability_widget(
                                            field, saved, row_key
                                        )
                                    )
                            with detail_row[1]:
                                for field in boolean_fields[first_column_count:]:
                                    capabilities[field.key] = (
                                        _render_machine_capability_widget(
                                            field, saved, row_key
                                        )
                                    )
                            if spec.code == "wood_cnc_router":
                                pricing_method, pricing = _render_cnc_machine_rate(
                                    saved,
                                    row_key,
                                    method_column=detail_row[2],
                                )
                            else:
                                pricing_method, pricing = _render_machinery_pricing(
                                    saved,
                                    row_key,
                                    method_column=detail_row[2],
                                )
                    else:
                        matching_services = [
                            service for service in services
                            if service.get("machine_code") == spec.code
                        ]
                        current_supplier_name = (
                            supplier_names.get(
                                str(matching_services[0].get("supplier_id")), ""
                            ) if matching_services else ""
                        )
                        detail_columns = st.columns(3)
                        if saved_status == "in_house":
                            with detail_columns[0]:
                                confirm_change = st.checkbox(
                                    "Confirm this is no longer in-house",
                                    key=f"{row_key}_confirm_change",
                                )
                            supplier_column = detail_columns[1]
                        else:
                            supplier_column = detail_columns[0]
                        if spec.code in SUBCONTRACTOR_MACHINE_CODES:
                            with supplier_column:
                                no_supplier = "__no_supplier__"
                                add_supplier = "__add_supplier__"
                                existing_names = sorted(
                                    {
                                        name.strip()
                                        for name in supplier_names.values()
                                        if name.strip()
                                    },
                                    key=str.casefold,
                                )
                                if (
                                    current_supplier_name
                                    and current_supplier_name not in existing_names
                                ):
                                    existing_names.append(current_supplier_name)
                                supplier_options = [
                                    no_supplier,
                                    *existing_names,
                                    add_supplier,
                                ]
                                selected_supplier = (
                                    current_supplier_name
                                    if current_supplier_name
                                    else no_supplier
                                )
                                supplier_choice = st.selectbox(
                                    "Regular subcontractor",
                                    supplier_options,
                                    index=supplier_options.index(selected_supplier),
                                    format_func=lambda value: {
                                        no_supplier: "No regular subcontractor",
                                        add_supplier: "Add new subcontractor...",
                                    }.get(value, value),
                                    key=f"{row_key}_supplier_choice",
                                )
                            if supplier_choice == add_supplier:
                                with detail_columns[2]:
                                    subcontractor_name = st.text_input(
                                        "New subcontractor name",
                                        key=f"{row_key}_new_supplier",
                                    )
                            elif supplier_choice != no_supplier:
                                subcontractor_name = supplier_choice
                    submitted = st.button(
                        "Save",
                        key=f"{row_key}_save",
                        use_container_width=True,
                    )
                if not submitted:
                    continue
                try:
                    if saved_status == "in_house" and availability == "No" and not confirm_change:
                        raise MachineryError(
                            "Confirm that this capability is no longer available in-house"
                        )
                    status = "in_house" if availability == "Yes" else "not_in_house"
                    supplier_id = ""
                    if status == "not_in_house" and subcontractor_name.strip():
                        supplier = create_or_get_supplier(access, subcontractor_name)
                        supplier_id = str(supplier["supplier_id"])
                    save_company_machinery(
                        access,
                        machine_code=spec.code,
                        availability_status=status,
                        capabilities=capabilities,
                        pricing_method=pricing_method,
                        pricing=pricing,
                        accepts_external_work=False,
                    )
                    deactivate_supplier_services(access, machine_code=spec.code)
                    if status == "not_in_house" and supplier_id:
                        save_supplier_service(
                            access,
                            supplier_id=supplier_id,
                            machine_code=spec.code,
                            pricing_method="quote_only",
                        )
                    st.session_state[detail_open_key] = False
                    st.session_state[previous_availability_key] = availability
                    st.success("Saved")
                    st.rerun(scope="fragment")
                except (MachineryError, PermissionError) as exc:
                    st.error(str(exc))
                except Exception:
                    st.error(
                        "Machinery settings could not be saved. Check the values and try again"
                    )


@st.fragment
def _render_machinery(access: CompanyAccess) -> None:
    st.markdown('<div class="company-machinery-active"></div>', unsafe_allow_html=True)
    try:
        rows = list_company_machinery(access)
        suppliers = list_company_suppliers(access)
        services = list_supplier_services(access)
    except Exception:
        st.error("Machinery settings are unavailable right now. Try again after the database update")
        return
    machine_rows = {str(row.get("machine_code")): row for row in rows}
    supplier_names = {str(row.get("supplier_id")): str(row.get("supplier_name") or "Supplier") for row in suppliers}
    if access.role != "owner":
        _render_member_machinery(machine_rows, services, supplier_names)
        return
    _render_owner_machinery(access, machine_rows, services, supplier_names)


def load_company_profile(access: CompanyAccess) -> dict:
    rows = (
        get_supabase_client().table("companies")
        .select(PROFILE_COLUMNS)
        .eq("company_id", access.company_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise PermissionError("Company profile is unavailable.")
    return rows[0]


@st.cache_data(ttl=300, show_spinner=False)
def _load_company_metrics_by_id(company_id: str) -> tuple[dict, dict]:
    client = get_supabase_client()
    settings_rows = (
        client.table("overhead_settings")
        .select("company_id," + ",".join(METRIC_SETTING_FIELDS))
        .eq("company_id", company_id)
        .limit(1)
        .execute()
    ).data or []
    try:
        monthly_rows = (
            client.table("overhead_monthly")
            .select("company_id," + ",".join(METRIC_MONTHLY_FIELDS))
            .eq("company_id", company_id)
            .limit(1)
            .execute()
        ).data or []
    except Exception as exc:
        if "other_spendings_cost" not in str(exc):
            raise
        legacy_fields = tuple(
            field for field in METRIC_MONTHLY_FIELDS if field != "other_spendings_cost"
        )
        monthly_rows = (
            client.table("overhead_monthly")
            .select("company_id," + ",".join(legacy_fields))
            .eq("company_id", company_id)
            .limit(1)
            .execute()
        ).data or []
    settings = settings_rows[0] if settings_rows else {"company_id": company_id}
    monthly = monthly_rows[0] if monthly_rows else {"company_id": company_id}
    settings.setdefault("vat_percent", 18)
    return settings, monthly


def load_company_metrics(access: CompanyAccess) -> tuple[dict, dict]:
    return _load_company_metrics_by_id(str(access.company_id))


def save_company_profile(access: CompanyAccess, values: dict[str, object]) -> dict:
    fresh = _current_access(access)
    payload = {
        field: _optional(values[field])
        for field in PROFILE_FIELDS
        if field in values
    }
    if not payload:
        raise ValueError("No company details were provided.")

    if "company_name" in values:
        company_name = _clean(values.get("company_name"))
        if not company_name:
            raise ValueError("Company name is required.")
        payload["company_name"] = company_name

    public_email = _clean(values.get("public_email")) if "public_email" in values else ""
    if public_email and not is_valid_email_address(public_email):
        raise ValueError("Enter a valid official email address.")

    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)
    result = (
        client.table("companies")
        .update(payload)
        .eq("company_id", fresh.company_id)
        .execute()
    )
    rows = result.data or []
    if len(rows) != 1 or str(rows[0].get("company_id")) != fresh.company_id:
        raise RuntimeError("The company profile was not saved.")
    return rows[0]


def save_company_metrics(
    access: CompanyAccess,
    settings_values: dict[str, object],
    monthly_values: dict[str, object],
) -> None:
    fresh = _current_access(access)
    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)

    settings_payload = {"company_id": fresh.company_id}
    for field in METRIC_SETTING_FIELDS:
        value = float(settings_values.get(field) or 0)
        if value < 0 or value > 100:
            raise ValueError("VAT and reserve percentages must be between 0 and 100.")
        settings_payload[field] = int(round(value))

    monthly_payload = {"company_id": fresh.company_id}
    for field in METRIC_MONTHLY_FIELDS:
        value = float(monthly_values.get(field) or 0)
        if value < 0:
            raise ValueError("Monthly overhead costs cannot be negative.")
        monthly_payload[field] = int(round(value))

    settings_update = {key: value for key, value in settings_payload.items() if key != "company_id"}
    settings_rows = (
        client.table("overhead_settings")
        .update(settings_update)
        .eq("company_id", fresh.company_id)
        .execute()
    ).data or []
    if not settings_rows:
        client.table("overhead_settings").insert(
            {
                "company_id": fresh.company_id,
                **METRIC_SETTING_INSERT_DEFAULTS,
                **settings_update,
            }
        ).execute()

    monthly_update = {key: value for key, value in monthly_payload.items() if key != "company_id"}
    monthly_rows = (
        client.table("overhead_monthly")
        .update(monthly_update)
        .eq("company_id", fresh.company_id)
        .execute()
    ).data or []
    if not monthly_rows:
        client.table("overhead_monthly").insert(monthly_payload).execute()
    _load_company_metrics_by_id.clear()


def save_company_contacts(
    access: CompanyAccess, name: str, public_email: str, public_phone: str
) -> dict:
    """Keep the original focused update contract for existing callers."""
    fresh = _current_access(access)
    name = name.strip()
    public_email = public_email.strip()
    public_phone = public_phone.strip()
    if not name:
        raise ValueError("Company name is required.")
    if public_email and not is_valid_email_address(public_email):
        raise ValueError("Enter a valid official email address.")
    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)
    result = (
        client.table("companies")
        .update({
            "company_name": name,
            "public_email": public_email or None,
            "public_phone": public_phone or None,
        })
        .eq("company_id", fresh.company_id)
        .execute()
    )
    rows = result.data or []
    if len(rows) != 1 or str(rows[0].get("company_id")) != fresh.company_id:
        raise RuntimeError("The company profile was not saved.")
    return rows[0]


def load_company_members(access: CompanyAccess) -> list[dict]:
    fresh = _current_access(access)
    client = get_supabase_client()
    rows = (
        client.table("company_members")
        .select("user_id,role")
        .eq("company_id", fresh.company_id)
        .execute()
    ).data or []
    members = []
    for row in rows:
        user_id = str(row["user_id"])
        try:
            response = client.auth.admin.get_user_by_id(user_id)
            email = str(response.user.email or "Email unavailable")
        except Exception:
            email = fresh.email if user_id == fresh.user_id else "Email unavailable"
        members.append({
            "User ID": user_id,
            "Email": email,
            "Role": "Owner" if row["role"] == "owner" else "Member",
        })
    return sorted(members, key=lambda item: (item["Role"] != "Owner", item["Email"].lower()))


def _owner_access(access: CompanyAccess) -> tuple[CompanyAccess, object]:
    fresh = _current_access(access)
    if fresh.role != "owner":
        raise PermissionError("Only the company owner can access employee costs.")
    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)
    return fresh, client


@st.cache_data(ttl=60, show_spinner=False)
def _load_company_employees_by_id(company_id: str) -> list[dict]:
    client = get_supabase_client()
    return (
        client.table("company_employees")
        .select(LABOR_EMPLOYEE_COLUMNS)
        .eq("company_id", company_id)
        .is_("deleted_at", "null")
        .order("worker_name")
        .execute()
    ).data or []


def load_company_employees(access: CompanyAccess) -> list[dict]:
    # ``access`` was resolved from the authenticated session in this same app
    # run. Repeating the privileged owner lookup here added a network roundtrip
    # to every form-widget rerun. Mutations still revalidate through
    # ``_owner_access`` immediately before writing.
    if access.role != "owner" or not access.company_id:
        raise PermissionError("Only the company owner can access employee costs.")
    return _load_company_employees_by_id(str(access.company_id))


def add_company_employee(
    access: CompanyAccess,
    *,
    worker_name: str,
    department: str,
    position_code: str,
    pay_type: str,
    gross_monthly_salary: float = 0,
    gross_hourly_rate: float = 0,
    monthly_hours: float = 0,
    employment_factor: float = LABOR_DEFAULT_EMPLOYMENT_FACTOR,
    total_hourly_cost: float = 0,
    total_monthly_cost: float = 0,
) -> dict:
    payload = _company_employee_payload(
        worker_name=worker_name,
        department=department,
        position_code=position_code,
        pay_type=pay_type,
        gross_monthly_salary=gross_monthly_salary,
        gross_hourly_rate=gross_hourly_rate,
        monthly_hours=monthly_hours,
        employment_factor=employment_factor,
        total_hourly_cost=total_hourly_cost,
        total_monthly_cost=total_monthly_cost,
    )
    fresh, client = _owner_access(access)
    result = client.table("company_employees").insert({
        "company_id": fresh.company_id,
        **payload,
    }).execute()
    rows = result.data or []
    if len(rows) != 1 or str(rows[0].get("company_id")) != fresh.company_id:
        raise RuntimeError("The worker was not added.")
    _load_company_employees_by_id.clear()
    return rows[0]


def _company_employee_payload(
    *,
    worker_name: str,
    department: str,
    position_code: str,
    pay_type: str,
    gross_monthly_salary: float = 0,
    gross_hourly_rate: float = 0,
    monthly_hours: float = 0,
    employment_factor: float = LABOR_DEFAULT_EMPLOYMENT_FACTOR,
    total_hourly_cost: float = 0,
    total_monthly_cost: float = 0,
) -> dict:
    worker_name = _clean(worker_name)
    if not worker_name:
        raise ValueError("Worker name is required.")
    if department not in LABOR_DEPARTMENTS:
        raise ValueError("Select a valid department.")
    allowed_positions = {code for code, _label in LABOR_POSITIONS[department]}
    if position_code not in allowed_positions:
        raise ValueError("Select a valid position for this department.")
    if pay_type not in LABOR_PAY_TYPES:
        raise ValueError("Select a valid pay type.")
    factor = round(float(employment_factor or 0), 2)
    if factor <= 0:
        raise ValueError("Employment factor must be greater than zero.")

    payload = {
        "worker_name": worker_name,
        "department": department,
        "position_code": position_code,
        "pay_type": pay_type,
        "gross_monthly_salary": None,
        "gross_hourly_rate": None,
        "monthly_hours": None,
        "employment_factor": factor,
        "total_hourly_cost": None,
        "total_monthly_cost": None,
    }
    if pay_type == "monthly_salary":
        salary_value = float(gross_monthly_salary or 0)
        salary = int(salary_value)
        if salary <= 0:
            raise ValueError("Monthly salary must be greater than zero.")
        if salary_value != salary:
            raise ValueError("Monthly salary must be a whole number.")
        monthly_cost = round(
            float(total_monthly_cost or (salary * factor)),
            2,
        )
        if monthly_cost <= 0:
            raise ValueError("Total monthly cost must be greater than zero.")
        payload["gross_monthly_salary"] = salary
        payload["total_monthly_cost"] = monthly_cost
    else:
        hourly_rate_value = float(gross_hourly_rate or 0)
        hourly_rate = int(hourly_rate_value)
        hours_value = float(monthly_hours or 0)
        hours = int(hours_value)
        if hourly_rate <= 0:
            raise ValueError("Hourly rate must be greater than zero.")
        if hourly_rate_value != hourly_rate:
            raise ValueError("Hourly rate must be a whole number.")
        if hours <= 0:
            raise ValueError("Average hours per month must be greater than zero.")
        if hours_value != hours:
            raise ValueError("Average hours per month must be a whole number.")
        hourly_cost = round(
            float(total_hourly_cost or (hourly_rate * factor)),
            2,
        )
        monthly_cost = round(
            float(total_monthly_cost or (hourly_rate * hours * factor)),
            2,
        )
        if hourly_cost <= 0:
            raise ValueError("Total hourly cost must be greater than zero.")
        if monthly_cost <= 0:
            raise ValueError("Total monthly cost must be greater than zero.")
        payload["gross_hourly_rate"] = hourly_rate
        payload["monthly_hours"] = hours
        payload["total_hourly_cost"] = hourly_cost
        payload["total_monthly_cost"] = monthly_cost
    return payload


def update_company_employee(
    access: CompanyAccess,
    employee_id: str,
    **values: object,
) -> dict:
    employee_id = _clean(employee_id)
    if not employee_id:
        raise ValueError("Select a worker to edit.")
    payload = _company_employee_payload(**values)
    fresh, client = _owner_access(access)
    result = (
        client.table("company_employees")
        .update(payload)
        .eq("company_id", fresh.company_id)
        .eq("employee_id", employee_id)
        .execute()
    )
    rows = result.data or []
    if (
        len(rows) != 1
        or str(rows[0].get("company_id")) != fresh.company_id
        or str(rows[0].get("employee_id")) != employee_id
    ):
        raise RuntimeError("The worker was not updated.")
    _load_company_employees_by_id.clear()
    return rows[0]


def archive_company_employee(access: CompanyAccess, employee_id: str) -> dict:
    employee_id = _clean(employee_id)
    if not employee_id:
        raise ValueError("Select a worker to remove.")
    fresh, client = _owner_access(access)
    result = (
        client.table("company_employees")
        .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
        .eq("company_id", fresh.company_id)
        .eq("employee_id", employee_id)
        .is_("deleted_at", "null")
        .execute()
    )
    rows = result.data or []
    if (
        len(rows) != 1
        or str(rows[0].get("company_id")) != fresh.company_id
        or str(rows[0].get("employee_id")) != employee_id
    ):
        raise RuntimeError("The worker was not removed.")
    _load_company_employees_by_id.clear()
    return rows[0]


def _text_input(
    profile: dict,
    label: str,
    field: str,
    *,
    widget_key: str | None = None,
    **kwargs,
) -> str:
    return st.text_input(
        label,
        value=_clean(profile.get(field)),
        key=widget_key or f"profile_{field}",
        **kwargs,
    )


def _profile_save_button(label: str) -> bool:
    """Render the single emphasized Save action used by every Profile form."""
    return st.form_submit_button(label, type="primary", use_container_width=True)


def _format_israeli_phone(value: object) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if digits == "0":
        return "0"
    if digits.startswith("972"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    digits = digits[:9]
    if not digits:
        return ""
    parts = [digits[:2], digits[2:5], digits[5:9]]
    return "+972 " + " ".join(part for part in parts if part)


def _read_only_group(title: str, items: list[tuple[str, object]]) -> None:
    rows = "".join(
        '<div class="company-profile-readonly-item">'
        f'<span>{escape(label)}</span><strong>{escape(_clean(value) or "Not set")}</strong></div>'
        for label, value in items
    )
    st.markdown(
        f'<section class="company-profile-readonly"><h3>{escape(title)}</h3>'
        f'<div class="company-profile-readonly-grid">{rows}</div></section>',
        unsafe_allow_html=True,
    )


def _save_profile_section(
    access: CompanyAccess,
    values: dict[str, object],
    *,
    success_message: str,
) -> None:
    try:
        save_company_profile(access, values)
        st.success(success_message)
    except ValueError as exc:
        st.error(str(exc))
    except PermissionError:
        st.error("Only the company owner can save these details.")
    except Exception:
        st.error("Company details were not saved. Try again in a moment.")


@st.cache_data(ttl=300, show_spinner=False)
def _load_company_logo_preview(company_id: str, reference: str) -> bytes | None:
    return load_company_logo_bytes(
        client=get_supabase_client(),
        company_id=company_id,
        reference=reference,
    )


def _logo_preview_html(png_bytes: bytes | None) -> str:
    if png_bytes:
        source = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
        body = f'<img src="{source}" alt="Company logo preview" />'
    else:
        body = "<span>Logo</span>"
    return f'<div class="company-logo-preview">{body}</div>'


def _pending_company_logo(uploaded_file, trace=None) -> tuple[NormalizedCompanyLogo | None, str | None]:
    source = uploaded_file.getvalue()
    digest = hashlib.sha256(source).hexdigest()
    pending = st.session_state.get("_company_logo_pending")
    if isinstance(pending, dict) and pending.get("digest") == digest:
        return pending.get("logo"), pending.get("error")

    started_at = time.perf_counter()
    try:
        logo = normalize_company_logo(source)
    except CompanyLogoError as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        if trace is not None:
            trace.event(
                "server.company_logo_normalize",
                status="error",
                duration_ms=duration_ms,
                metadata={
                    "source_bytes": len(source),
                    "error_type": type(exc).__name__,
                },
            )
        st.session_state._company_logo_pending = {
            "digest": digest,
            "logo": None,
            "error": str(exc),
        }
        return None, str(exc)

    if trace is not None:
        trace.event(
            "server.company_logo_normalize",
            duration_ms=(time.perf_counter() - started_at) * 1000,
            metadata={
                "source_format": logo.source_format,
                "source_bytes": len(source),
                "source_width": logo.source_width,
                "source_height": logo.source_height,
                "content_width": logo.content_width,
                "content_height": logo.content_height,
                "output_bytes": len(logo.png_bytes),
            },
        )
    st.session_state._company_logo_pending = {
        "digest": digest,
        "logo": logo,
        "error": None,
    }
    return logo, None


def _save_company_logo(
    access: CompanyAccess,
    logo: NormalizedCompanyLogo,
    previous_reference: str | None,
    *,
    trace=None,
) -> None:
    fresh = _current_access(access)
    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)
    persist_company_logo(
        client=client,
        company_id=fresh.company_id,
        png_bytes=logo.png_bytes,
        previous_reference=previous_reference,
        trace=trace,
    )


def _render_company_logo_card(
    access: CompanyAccess,
    profile: dict,
    *,
    editable: bool,
    trace=None,
) -> None:
    reference = _clean(profile.get("logo_url"))
    current_logo = None
    if reference:
        try:
            if trace is None:
                current_logo = _load_company_logo_preview(str(access.company_id), reference)
            else:
                with trace.span("server.company_logo_load"):
                    current_logo = _load_company_logo_preview(str(access.company_id), reference)
        except Exception:
            logger.exception("Company logo preview load failed")

    with st.container(key="company_logo_card"):
        st.markdown(
            '<div class="company-logo-table-heading">Company Logo</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="company_logo_body"):
            pending_logo = None
            pending_error = None
            uploaded_file = None
            notice = st.session_state.pop("_company_logo_notice", None)
            if editable:
                uploader_version = int(
                    st.session_state.get("_company_logo_uploader_version") or 0
                )
                uploader_key = f"company_logo_upload_{uploader_version}"
                selected_file = st.session_state.get(uploader_key)
                if selected_file is not None:
                    pending_logo, pending_error = _pending_company_logo(
                        selected_file,
                        trace=trace,
                    )

                def render_logo_uploader(container_key: str):
                    with st.container(key=container_key):
                        return st.file_uploader(
                            "Company logo",
                            type=["png", "svg", "pdf"],
                            accept_multiple_files=False,
                            key=uploader_key,
                            label_visibility="collapsed",
                        )

                preview = (
                    pending_logo.png_bytes
                    if pending_logo is not None
                    else current_logo
                )
                if preview is not None:
                    upload_column, preview_column = st.columns(
                        2,
                        gap="medium",
                        vertical_alignment="top",
                    )
                    with upload_column:
                        uploaded_file = render_logo_uploader(
                            "company_logo_pending_upload"
                        )
                    with preview_column:
                        st.markdown(
                            _logo_preview_html(preview),
                            unsafe_allow_html=True,
                        )
                else:
                    uploaded_file = render_logo_uploader("company_logo_empty_upload")

                if uploaded_file is not None and selected_file is None:
                    _pending_company_logo(uploaded_file, trace=trace)
                    st.rerun()
            elif current_logo is not None:
                st.markdown(_logo_preview_html(current_logo), unsafe_allow_html=True)

            if pending_error:
                st.error(pending_error)
            if notice:
                st.success(notice)

            button_label = "Change Logo" if reference else "Save Logo"
            if editable and reference:
                st.markdown(
                    '<div class="company-logo-change-mode" style="display:none"></div>',
                    unsafe_allow_html=True,
                )
                install_company_logo_picker_guard()
            if pending_logo is not None:
                st.markdown(
                    '<div class="company-logo-pending" style="display:none"></div>',
                    unsafe_allow_html=True,
                )
            logo_action_clicked = editable and st.button(
                button_label,
                key="save_company_logo",
                type="primary",
                use_container_width=True,
                disabled=pending_logo is None and not reference,
            )
            if logo_action_clicked and pending_logo is not None:
                try:
                    _save_company_logo(
                        access,
                        pending_logo,
                        reference,
                        trace=trace,
                    )
                except PermissionError:
                    st.error("Only the company owner can save the logo.")
                except Exception:
                    logger.exception("Company logo save failed")
                    st.error("The company logo was not saved. Try again in a moment.")
                else:
                    st.session_state.pop("_company_logo_pending", None)
                    st.session_state._company_logo_uploader_version = (
                        int(st.session_state.get("_company_logo_uploader_version") or 0) + 1
                    )
                    st.session_state._company_logo_notice = "Company logo saved"
                    st.rerun()


def _price_source_supplier(source: dict) -> str:
    supplier = source.get("company_suppliers")
    if isinstance(supplier, dict):
        return str(supplier.get("supplier_name") or "Unknown supplier")
    if isinstance(supplier, list) and supplier:
        return str(supplier[0].get("supplier_name") or "Unknown supplier")
    return "Unknown supplier"


def _price_catalog_number(value: object) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    if number == int(number):
        text = f"{int(number):,}"
    else:
        text = f"{number:,.2f}".rstrip("0").rstrip(".")
    return text.replace(",", "\u202f")


def _price_catalog_value(row: dict) -> str:
    currency = str(row.get("currency") or "").upper()
    prefix = "₪" if currency == "ILS" else f"{currency} " if currency else ""
    unit = str(row.get("normalized_unit") or row.get("calculation_unit") or "")
    suffix = f" / {escape(unit)}" if unit else ""
    return f"{prefix}{_price_catalog_number(row.get('normalized_price'))}{suffix}"


def _price_catalog_date(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "—"
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except ValueError:
        return escape(text[:10])


def _price_catalog_count(count: int) -> str:
    return f"{count} {'price' if count == 1 else 'prices'}"


def _price_catalog_url_label(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    label = f"{parsed.netloc}{parsed.path}".rstrip("/")
    return label or value


def _price_source_category_label(value: str) -> str:
    return canonical_price_source_category(value)


def _price_source_department(category: str) -> str:
    return PRICE_CATALOG_DEPARTMENTS.get(canonical_price_source_category(category), "Wood")


def _price_source_department_label(value: str) -> str:
    return "Coating" if value == "Finishing" else value


def _price_source_material_types(source: dict) -> list[str]:
    summary = source.get("processing_summary") or {}
    values = summary.get("material_types") or []
    material_types = sorted(
        {
            canonical_price_source_category(str(value))
            for value in values
            if str(value).strip()
        },
        key=str.casefold,
    )
    if material_types:
        return material_types
    category = canonical_price_source_category(str(source.get("category") or "Other"))
    return [] if category == "Mixed" else [category]


def _price_source_classification(source: dict) -> tuple[str, str]:
    material_types = _price_source_material_types(source)
    departments = sorted(
        {
            PRICE_CATALOG_DEPARTMENTS.get(material_type, "Wood")
            for material_type in material_types
        }
    )
    department_label = (
        _price_source_department_label(departments[0])
        if len(departments) == 1
        else "Multiple departments"
    )
    material_label = material_types[0] if len(material_types) == 1 else "Mixed materials"
    return department_label, material_label


def _price_source_document_date(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%m/%d/%y")
    except ValueError:
        return text


def _price_source_context_label(value: object) -> str:
    return {
        "public_list": "Public list",
        "supplier_quote": "Supplier quote",
        "customer_transaction": "Customer transaction",
        "unknown": "Unknown context",
    }.get(str(value or ""), str(value or "").replace("_", " ").title())


def _price_source_tc(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "TC unavailable"
    if number > 0 and number < 0.001:
        return "TC <0.001"
    return f"TC {number:.3f}"


def _price_source_money(value: object, currency: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number <= 0:
        return ""
    code = str(currency or "").upper()
    prefix = "₪" if code == "ILS" else f"{code} " if code else ""
    return f"{prefix}{_price_catalog_number(number)}"


def _price_source_row_material_type(row: dict, source: dict) -> str:
    evidence = row.get("evidence")
    if isinstance(evidence, dict) and evidence.get("material_type"):
        return canonical_price_source_category(str(evidence["material_type"]))
    return canonical_price_source_category(str(source.get("category") or "Other"))


def _render_price_catalog(catalog: list[dict]) -> None:
    department = "All departments"
    material_type = "All material types"
    supplier = "All suppliers"
    if catalog:
        department_column, type_column, supplier_column = st.columns(3)
        department_options = ["All departments"] + [
            item for item in ("Wood", "Metal", "Finishing")
            if any(row.get("department") == item for row in catalog)
        ]
        with department_column:
            department = st.selectbox(
                "Department",
                department_options,
                format_func=_price_source_department_label,
                key="price_catalog_department",
            )
        type_options = ["All material types"] + sorted(
            {
                str(row.get("material_type") or "Other")
                for row in catalog
                if department == "All departments" or row.get("department") == department
            },
            key=str.casefold,
        )
        with type_column:
            material_type = st.selectbox(
                "Material type",
                type_options,
                format_func=_price_source_category_label,
                key="price_catalog_material_type",
            )
        supplier_options = ["All suppliers"] + sorted(
            {str(row.get("supplier_name") or "Unknown supplier") for row in catalog},
            key=str.casefold,
        )
        with supplier_column:
            supplier = st.selectbox(
                "Supplier",
                supplier_options,
                key="price_catalog_supplier",
            )

    visible = [
        row for row in catalog
        if (department == "All departments" or row.get("department") == department)
        and (material_type == "All material types" or row.get("material_type") == material_type)
        and (supplier == "All suppliers" or row.get("supplier_name") == supplier)
    ]
    if catalog and not visible:
        st.info("No material prices match these filters.")
        return

    departments: dict[str, list[dict]] = {}
    for row in visible:
        departments.setdefault(str(row["department"]), []).append(row)

    department_markup: list[str] = []
    department_labels = {"Wood": "Wood", "Metal": "Metal", "Finishing": "Coating"}
    for department_name in ("Wood", "Metal", "Finishing"):
        rows = departments.get(department_name) or []
        table_rows: list[str] = []
        for row in rows:
            canonical_name = str(row.get("canonical_name") or "Material")
            original_name = str(row.get("original_name") or "")
            supplier_name = str(row.get("supplier_name") or "Unknown supplier")
            source_url = str(row.get("source_url") or "")
            source_name = str(row.get("source_name") or "")
            source_id = str(row.get("source_id") or "")
            supplier_link = (
                '<a class="price-catalog-link" href="'
                f'{escape(source_url, quote=True)}" target="_blank" rel="noopener noreferrer" '
                f'title="{escape(source_url, quote=True)}">'
                f'{escape(_price_catalog_url_label(source_url))}</a>'
                if source_url else ""
            )
            source_cell = (
                '<a class="price-catalog-source-button" href="#source-library" '
                f'data-source-id="{escape(source_id, quote=True)}" '
                f'title="{escape(source_name or "View source in library", quote=True)}" '
                'aria-label="View source in library"><span aria-hidden="true"></span></a>'
            )
            table_rows.append(
                "<tr>"
                '<td class="price-catalog-material">'
                f'<strong title="{escape(canonical_name, quote=True)}">{escape(canonical_name)}</strong>'
                + (
                    f'<span title="{escape(original_name, quote=True)}">{escape(original_name)}</span>'
                    if original_name and original_name.casefold() != canonical_name.casefold()
                    else ""
                )
                + "</td>"
                '<td class="price-catalog-supplier">'
                f'<strong>{escape(supplier_name)}</strong>{supplier_link}</td>'
                f'<td class="price-catalog-price"><strong>{_price_catalog_value(row)}</strong></td>'
                f'<td class="price-catalog-date">{_price_catalog_date(row.get("updated_at"))}</td>'
                f'<td class="price-catalog-source">{source_cell}</td>'
                "</tr>"
            )
        department_body = (
            '<div class="price-catalog-table-wrap"><table>'
            '<thead><tr><th>Material</th><th>Supplier</th><th>Price</th>'
            '<th>Updated</th><th aria-label="Source"></th></tr></thead>'
            f'<tbody>{"".join(table_rows)}</tbody></table></div>'
            if table_rows
            else '<div class="price-catalog-department-empty">No active prices</div>'
        )
        department_markup.append(
            '<details class="price-catalog-department" open>'
            f'<summary><span>{escape(department_labels[department_name])}</span>'
            f'<span>{_price_catalog_count(len(rows))}</span></summary>'
            f'{department_body}</details>'
        )

    st.markdown(
        '<div class="price-catalog-card price-catalog-main">'
        '<div class="price-catalog-title"><span>Material prices</span>'
        f'<span>{len(visible)} active {"price" if len(visible) == 1 else "prices"}</span></div>'
        f'{"".join(department_markup)}</div>',
        unsafe_allow_html=True,
    )


def _render_price_source_details(access: CompanyAccess, source: dict) -> None:
    rows = load_price_source_rows(access, str(source["source_id"]))
    summary = source.get("processing_summary") or {}
    department_label, material_label = _price_source_classification(source)
    original = None
    if source.get("source_kind") != "url" and source.get("storage_path"):
        try:
            original = load_price_source_bytes(access, str(source["storage_path"]))
        except Exception:
            logger.exception("Price source original load failed")

    with st.container(key="price_source_detail_top"):
        detail_column, action_column = st.columns(
            [4, 1.35],
            gap="large",
            vertical_alignment="center",
        )
        with detail_column:
            st.markdown(
                '<div class="price-source-detail-heading">'
                f'<strong>{escape(_price_source_supplier(source))}</strong>'
                f'<span>{escape(str(source.get("source_name") or ""))}</span>'
                f'<small>{escape(department_label)}</small>'
                f'<small>{escape(material_label)}</small>'
                '</div>',
                unsafe_allow_html=True,
            )
        with action_column:
            if source.get("source_kind") == "url" and source.get("source_url"):
                st.link_button(
                    "Open Original Source",
                    str(source["source_url"]),
                    use_container_width=True,
                )
            elif original:
                st.download_button(
                    "Download Original Source",
                    data=original,
                    file_name=Path(str(source.get("source_name") or "price-source")).name,
                    mime=str(source.get("mime_type") or "application/octet-stream"),
                    key=f'download_price_source_{source["source_id"]}',
                    use_container_width=True,
                )
    st.caption(
        f'{int(summary.get("ready") or 0)} prices updated · '
        f'{int(summary.get("unresolved") or 0)} unresolved · '
        f'{int(summary.get("excluded") or 0)} excluded'
    )
    metadata = []
    if summary.get("document_number"):
        metadata.append(f'Document {summary["document_number"]}')
    document_date = _price_source_document_date(source.get("document_date"))
    if document_date:
        metadata.append(document_date)
    if summary.get("price_context"):
        metadata.append(_price_source_context_label(summary.get("price_context")))
    for label, key in (
        ("Subtotal", "document_subtotal"),
        ("VAT", "document_vat_amount"),
        ("Total", "document_total"),
    ):
        formatted = _price_source_money(summary.get(key), source.get("currency"))
        if formatted:
            metadata.append(f"{label} {formatted}")
    duration = summary.get("agent_duration_seconds")
    if isinstance(duration, (int, float)):
        metadata.append(f"Agent {duration:.1f}s")
    metadata.append(_price_source_tc(summary.get("token_cost")))
    st.caption(" · ".join(metadata))
    mime_type = str(source.get("mime_type") or "application/octet-stream")
    if original and mime_type in {"image/jpeg", "image/png"}:
        st.image(original, caption="Original source", use_container_width=True)
    if not rows:
        st.info("No product rows were extracted from this source.")
        return
    table_rows = []
    for row in rows:
        source_price = row.get("raw_price")
        normalized_price = row.get("normalized_price")
        source_value = (
            f'{escape(str(row.get("raw_currency") or ""))} {source_price:g} / '
            f'{escape(str(row.get("raw_unit") or "?"))}'
            if isinstance(source_price, (int, float)) and source_price > 0
            else ""
        )
        normalized_value = (
            f'{normalized_price:g} / '
            f'{escape(str(row.get("calculation_unit") or row.get("normalized_unit") or "?"))}'
            if isinstance(normalized_price, (int, float)) and normalized_price > 0
            else ""
        )
        purchase_unit = str(row.get("purchase_unit") or "")
        calculation_unit = str(row.get("calculation_unit") or row.get("normalized_unit") or "")
        conversion_factor = row.get("conversion_factor")
        if (
            normalized_value
            and purchase_unit
            and calculation_unit
            and isinstance(conversion_factor, (int, float))
            and (purchase_unit != calculation_unit or conversion_factor != 1)
        ):
            normalized_value += (
                f'<br><small>{escape(purchase_unit)} = '
                f'{conversion_factor:g} {escape(calculation_unit)}</small>'
            )
        table_rows.append(
            "<tr>"
            f'<td>{escape(str(row.get("raw_description") or ""))}</td>'
            f'<td>{escape(_price_source_row_material_type(row, source))}</td>'
            f'<td>{source_value}</td>'
            f'<td>{normalized_value}</td>'
            f'<td>{"Included" if row.get("raw_vat_included") is True else "Excluded" if row.get("raw_vat_included") is False else "Unknown"}</td>'
            f'<td>{escape(str(row.get("result_status") or "").title())}</td>'
            f'<td>{float(row.get("confidence") or 0):.0f}%</td>'
            "</tr>"
        )
    st.markdown(
        '<div class="price-source-table"><table><thead><tr>'
        '<th>Source Item</th><th>Material Type</th><th>Source Price</th>'
        '<th>Estimation Price</th><th>VAT</th><th>Result</th><th>Confidence</th>'
        '</tr></thead><tbody>'
        + "".join(table_rows)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _queue_price_source_processing(uploader_key: str, url_key: str) -> None:
    """Capture the selected source before the Price Lists fragment reruns."""
    st.session_state._price_source_pending = {
        "uploaded_files": list(st.session_state.get(uploader_key) or []),
        "department": "",
        "source_url": str(st.session_state.get(url_key) or ""),
    }
    st.session_state._price_source_processing = True
    st.session_state.pop("_price_source_error", None)
    st.session_state.pop("_price_source_notice", None)


def _price_source_notice_text(source: dict | None) -> str:
    if not source:
        return "Price source processed"
    summary = source.get("processing_summary") or {}
    total = int(summary.get("total") or 0)
    ready = int(summary.get("ready") or 0)
    unresolved = int(summary.get("unresolved") or 0)
    excluded = int(summary.get("excluded") or 0)
    parts = [
        f'{total} {"row" if total == 1 else "rows"} extracted',
        f"{ready} active",
        f"{unresolved} unresolved",
    ]
    if excluded:
        parts.append(f"{excluded} excluded")
    duration = summary.get("agent_duration_seconds")
    if isinstance(duration, (int, float)):
        parts.append(f"{duration:.1f} s")
    parts.append(_price_source_tc(summary.get("token_cost")))
    return " · ".join(parts)


def _render_price_source_add(access: CompanyAccess, *, trace=None) -> None:
    processing = bool(st.session_state.get("_price_source_processing"))
    with st.container(key="price_source_add_card"):
        st.markdown(
            '<div class="company-logo-table-heading">Add price source</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="price_source_add_body"):
            uploader_version = int(st.session_state.get("_price_source_uploader_version") or 0)
            uploader_key = f"price_source_upload_{uploader_version}"
            url_key = f"price_source_url_{uploader_version}"
            file_column, details_column = st.columns(2, gap="large")
            with file_column:
                st.file_uploader(
                    "Upload file or photos",
                    accept_multiple_files=True,
                    key=uploader_key,
                    disabled=processing,
                    label_visibility="collapsed",
                    help=(
                        "Upload one PDF or spreadsheet, or select several JPEG/PNG photos "
                        "that belong to the same document"
                    ),
                )
                install_upload_dragover_guard()
            with details_column:
                st.text_input(
                    "Paste supplier page URL",
                    placeholder="https://supplier.example/prices",
                    key=url_key,
                    disabled=processing,
                )
                if processing:
                    st.markdown(
                        '<span class="price-source-processing-marker"></span>',
                        unsafe_allow_html=True,
                    )
                st.button(
                    "Extracting prices" if processing else "Extract prices",
                    key="process_price_source",
                    type="primary",
                    use_container_width=True,
                    disabled=processing,
                    on_click=_queue_price_source_processing,
                    args=(uploader_key, url_key),
                )
                install_price_source_processing_guard()

def _process_pending_price_source(access: CompanyAccess, *, trace=None) -> None:
    if not st.session_state.get("_price_source_processing"):
        return

    uploader_version = int(st.session_state.get("_price_source_uploader_version") or 0)
    pending = st.session_state.get("_price_source_pending") or {}
    try:
        uploaded_file = combine_price_source_files(pending.get("uploaded_files") or [])
        source_id = process_price_source(
            access,
            department=str(pending.get("department") or ""),
            uploaded_file=uploaded_file,
            source_url=str(pending.get("source_url") or ""),
            trace=trace,
        )
    except PriceSourceError as exc:
        st.session_state._price_source_error = str(exc)
    except PermissionError:
        st.session_state._price_source_error = "Only the company owner can add price sources."
    except Exception:
        logger.exception("Price source processing failed")
        st.session_state._price_source_error = (
            "The price source could not be processed. Try again in a moment."
        )
    else:
        st.session_state._price_source_uploader_version = uploader_version + 1
        st.session_state._price_source_notice = source_id
    finally:
        st.session_state._price_source_processing = False
        st.session_state.pop("_price_source_pending", None)


@st.fragment
def _render_price_lists(access: CompanyAccess, *, trace=None) -> None:
    if access.role != "owner":
        st.info("Price sources are available to the company owner.")
        return

    _process_pending_price_source(access, trace=trace)

    try:
        sources = list_price_sources(access)
    except Exception:
        logger.exception("Price source list failed")
        st.info("Price Sources storage is not configured yet.")
        return

    try:
        catalog = list_price_catalog(access)
    except Exception:
        logger.exception("Price catalog list failed")
        st.info("The material price catalog is unavailable right now.")
        return

    _render_price_source_add(access, trace=trace)

    notice_source_id = st.session_state.pop("_price_source_notice", None)
    if notice_source_id:
        notice_source = next(
            (
                source
                for source in sources
                if str(source.get("source_id")) == str(notice_source_id)
            ),
            None,
        )
        st.success(_price_source_notice_text(notice_source))
    error = st.session_state.pop("_price_source_error", None)
    if error:
        st.error(error)

    with st.container(key="price_catalog_shell"):
        with st.container(key="price_catalog_section"):
            _render_price_catalog(catalog)

        with st.container(key="price_source_library_section"):
            st.markdown(
                '<span id="source-library" class="price-source-library-anchor"></span>',
                unsafe_allow_html=True,
            )
            with st.expander(f'Source library · {len(sources)}', expanded=False):
                if not sources:
                    st.info("No source documents yet.")
                else:
                    with st.container(key="price_source_list_card"):
                        for source in sources:
                            summary = source.get("processing_summary") or {}
                            left, category_col, status_col, items_col, action_col = st.columns(
                                [2.3, 1.45, 0.8, 0.65, 0.65],
                                vertical_alignment="center",
                            )
                            with left:
                                st.markdown(
                                    f'**{escape(_price_source_supplier(source))}**  \n'
                                    f'<span class="price-source-file" title="{escape(str(source.get("source_name") or ""), quote=True)}">'
                                    f'{escape(str(source.get("source_name") or ""))}</span>',
                                    unsafe_allow_html=True,
                                )
                            with category_col:
                                department_label, material_label = (
                                    _price_source_classification(source)
                                )
                                st.markdown(
                                    '<span class="price-source-library-department">'
                                    f'{escape(department_label)}'
                                    '</span>'
                                    '<span class="price-source-library-material-type">'
                                    f'{escape(material_label)}'
                                    '</span>',
                                    unsafe_allow_html=True,
                                )
                            with status_col:
                                st.write(str(source.get("status") or "").title())
                            with items_col:
                                ready_count = int(summary.get("ready") or 0)
                                st.write(f"{ready_count} {'price' if ready_count == 1 else 'prices'}")
                            with action_col:
                                if st.button(
                                    "View",
                                    key=f'view_price_source_{source["source_id"]}',
                                ):
                                    st.session_state._selected_price_source_id = source["source_id"]

                selected_id = st.session_state.get("_selected_price_source_id")
                selected = next(
                    (source for source in sources if source["source_id"] == selected_id),
                    None,
                )
                if selected:
                    with st.container(key="price_source_detail_card"):
                        st.markdown(
                            '<div class="company-logo-table-heading">Source details</div>',
                            unsafe_allow_html=True,
                        )
                        _render_price_source_details(access, selected)



def _render_owner_bank_details(access: CompanyAccess, profile: dict) -> None:
    with st.form("company_profile_company_details"):
        first_left, first_right = st.columns(2)
        with first_left:
            company_name = _text_input(profile, "Company name", "company_name")
        with first_right:
            registration = _text_input(
                profile, "Company registration number", "company_registration_number"
            )

        legal_name_left, legal_name_right = st.columns(2)
        with legal_name_left:
            legal_name_hebrew = _text_input(
                profile,
                "Company legal name (Hebrew)",
                "legal_name_hebrew",
            )
        with legal_name_right:
            legal_name = _text_input(
                profile,
                "Company legal name (English)",
                "legal_name",
            )

        bank_first_left, bank_first_right = st.columns(2)
        with bank_first_left:
            bank_name = _text_input(profile, "Bank name", "bank_name")
        with bank_first_right:
            bank_number = _text_input(profile, "Bank number", "bank_number")

        bank_second_left, bank_second_right = st.columns(2)
        with bank_second_left:
            branch_number = _text_input(profile, "Branch number", "branch_number")
        with bank_second_right:
            account_number = _text_input(profile, "Account number", "account_number")

        international_left, international_right = st.columns(2)
        with international_left:
            iban = _text_input(profile, "IBAN", "iban")
        with international_right:
            swift = _text_input(profile, "BIC", "swift")
        saved = _profile_save_button("Save Bank Details")
    if saved:
        _save_profile_section(access, {
            "company_name": company_name,
            "company_registration_number": registration,
            "legal_name_hebrew": legal_name_hebrew,
            "bank_name": bank_name,
            "bank_number": bank_number,
            "branch_number": branch_number,
            "account_number": account_number,
            "legal_name": legal_name,
            "iban": iban,
            "swift": swift,
        }, success_message="Bank details saved")


def _render_owner_contacts(access: CompanyAccess, profile: dict, *, trace=None) -> None:
    with st.form("company_profile_contacts"):
        contact_left, contact_right = st.columns(2)
        with contact_left:
            official_email = _text_input(
                profile, "Official email", "public_email", placeholder="office@company.com"
            )
        with contact_right:
            phone = st.text_input(
                "Phone",
                value=_format_israeli_phone(profile.get("public_phone")),
                key="profile_public_phone",
                placeholder="+972 00 000 0000",
            )
        website = _text_input(profile, "Website", "website_url", placeholder="https://company.com")

        address_first_left, address_first_right = st.columns(2)
        with address_first_left:
            street = _text_input(profile, "Street", "address_street")
        with address_first_right:
            house_number = _text_input(profile, "House Number", "address_house_number")
        address_second_left, address_second_right = st.columns(2)
        with address_second_left:
            city = _text_input(profile, "City", "address_city")
        with address_second_right:
            postal_code = _text_input(profile, "Postal code", "address_postal_code")

        social_left, social_middle, social_right = st.columns(3)
        with social_left:
            facebook = _text_input(
                profile, "Facebook", "facebook_url", placeholder="https://facebook.com/..."
            )
        with social_middle:
            linkedin = _text_input(
                profile, "LinkedIn", "linkedin_url", placeholder="https://linkedin.com/company/..."
            )
        with social_right:
            instagram = _text_input(
                profile, "Instagram", "instagram_url", placeholder="https://instagram.com/..."
            )
        saved = _profile_save_button("Save Contacts")
    if saved:
        _save_profile_section(access, {
            "public_email": official_email,
            "public_phone": _format_israeli_phone(phone),
            "website_url": website,
            "address_street": street,
            "address_house_number": house_number,
            "address_city": city,
            "address_postal_code": postal_code,
            "linkedin_url": linkedin,
            "instagram_url": instagram,
            "facebook_url": facebook,
        }, success_message="Contacts saved")
    _render_company_logo_card(access, profile, editable=True, trace=trace)


def _render_member_bank_details(profile: dict) -> None:
    _read_only_group("Bank Details", [
        ("Company name", profile.get("company_name")),
        ("Company registration number", profile.get("company_registration_number")),
        ("Company legal name (Hebrew)", profile.get("legal_name_hebrew")),
        ("Bank name", profile.get("bank_name")),
        ("Bank number", profile.get("bank_number")),
        ("Branch number", profile.get("branch_number")),
        ("Account number", profile.get("account_number")),
        ("Company legal name (English)", profile.get("legal_name")),
        ("IBAN", profile.get("iban")),
        ("BIC", profile.get("swift")),
    ])


def _render_member_contacts(access: CompanyAccess, profile: dict, *, trace=None) -> None:
    _read_only_group("Contacts", [
        ("Official email", profile.get("public_email")),
        ("Phone", profile.get("public_phone")),
        ("Website", profile.get("website_url")),
        ("Street", profile.get("address_street")),
        ("House Number", profile.get("address_house_number")),
        ("City", profile.get("address_city")),
        ("Postal code", profile.get("address_postal_code")),
        ("Facebook", profile.get("facebook_url")),
        ("LinkedIn", profile.get("linkedin_url")),
        ("Instagram", profile.get("instagram_url")),
    ])
    _render_company_logo_card(access, profile, editable=False, trace=trace)


def _metric_amount(value: object) -> float:
    try:
        cleaned = (
            str(value or "0")
            .replace("₪", "")
            .replace("%", "")
            .replace(",", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .strip()
        )
        return max(0.0, float(cleaned or 0))
    except (TypeError, ValueError):
        return 0.0


def _metric_money(value: object) -> str:
    return f"₪{round(_metric_amount(value)):,}".replace(",", "\u202f")


def _metric_percent_text(value: object) -> str:
    number = min(100.0, _metric_amount(value))
    if number == int(number):
        return f"{int(number)}%"
    text = f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{text}%"


def _ensure_metric_text_state(key: str, default: str) -> None:
    if key not in st.session_state or not isinstance(st.session_state[key], str):
        st.session_state[key] = default


def _normalize_metric_money(key: str) -> None:
    st.session_state[key] = _metric_money(st.session_state.get(key))


def _normalize_metric_percent(key: str) -> None:
    st.session_state[key] = _metric_percent_text(st.session_state.get(key))


def _metric_vat(field: str, net_amount: float, vat_percent: float) -> int:
    if field == "arnona_facilities_cost":
        return 0
    return round(net_amount * vat_percent / 100)


def _consume_company_metrics_snapshot(
    access: CompanyAccess,
    raw_snapshot: str | None,
) -> str | None:
    if not raw_snapshot:
        return None
    snapshot = json.loads(str(raw_snapshot))
    nonce = snapshot.get("nonce") if isinstance(snapshot, dict) else None
    if not isinstance(nonce, str) or not nonce:
        raise ValueError("Overhead expenses payload is invalid.")
    if nonce == st.session_state.get("_company_metrics_consumed_nonce"):
        return None
    st.session_state["_company_metrics_consumed_nonce"] = nonce

    settings_values = snapshot.get("settings")
    monthly_values = snapshot.get("monthly")
    if not isinstance(settings_values, dict) or not isinstance(monthly_values, dict):
        raise ValueError("Overhead expenses payload is invalid.")
    save_company_metrics(
        access,
        settings_values,
        monthly_values,
    )
    return "Overhead expenses saved"


@st.fragment
def _render_metrics_save(access: CompanyAccess) -> None:
    save_message = None
    try:
        with st.container(key="company_metrics_bridge_host"):
            raw_snapshot = company_metrics_bridge(key="company_metrics_bridge")
        save_message = _consume_company_metrics_snapshot(access, raw_snapshot)
    except ValueError as exc:
        st.error(str(exc))
    except PermissionError:
        st.error("Only the company owner can save these overhead expenses.")
    except Exception:
        logger.exception("Company overhead expenses save failed")
        st.error("Overhead expenses were not saved. Try again in a moment.")
        return

    if save_message:
        st.success(save_message)


def _render_metrics(access: CompanyAccess) -> None:
    try:
        settings, monthly = load_company_metrics(access)
    except Exception:
        st.error("Overhead expenses are unavailable right now. Try again in a moment.")
        return

    editable = access.role == "owner"
    with st.container(key="company_metrics_card", border=True):
        vat_key = "profile_metric_vat_percent"
        _ensure_metric_text_state(
            vat_key, _metric_percent_text(settings.get("vat_percent"))
        )
        vat_percent = min(100.0, _metric_amount(st.session_state[vat_key]))

        st.markdown(
            company_metrics_view.table_html(
                METRIC_GROUPS,
                monthly,
                vat_percent,
                editable=editable,
            ),
            unsafe_allow_html=True,
        )

        with st.container(key="company_metrics_settings"):
            vat_column, warranty_column, management_column = st.columns(3)
        with vat_column:
            vat_raw = st.text_input(
                "Ma'am / VAT rate",
                key=vat_key,
                on_change=_normalize_metric_percent,
                args=(vat_key,),
                disabled=not editable,
            )
            vat_percent = min(100.0, _metric_amount(vat_raw))
        with warranty_column:
            warranty_key = "profile_metric_warranty_reserve_percent"
            _ensure_metric_text_state(
                warranty_key,
                _metric_percent_text(settings.get("warranty_reserve_percent")),
            )
            warranty_raw = st.text_input(
                "Warranty reserve",
                key=warranty_key,
                on_change=_normalize_metric_percent,
                args=(warranty_key,),
                disabled=not editable,
            )
            warranty_percent = min(100.0, _metric_amount(warranty_raw))
        with management_column:
            management_key = "profile_metric_management_buffer_percent"
            _ensure_metric_text_state(
                management_key,
                _metric_percent_text(settings.get("management_buffer_percent")),
            )
            management_raw = st.text_input(
                "Management buffer",
                key=management_key,
                on_change=_normalize_metric_percent,
                args=(management_key,),
                disabled=not editable,
            )
            management_percent = min(100.0, _metric_amount(management_raw))

        if editable:
            st.markdown(company_metrics_view.save_action_html(), unsafe_allow_html=True)
            install_company_metrics_input_guard()
            _render_metrics_save(access)


def _render_users(access: CompanyAccess) -> None:
    from state.company_auth import create_company_join_url, remove_company_member

    try:
        members = load_company_members(access)
        removable_members = {
            str(member.get("User ID") or ""): member
            for member in members
            if member.get("Role") != "Owner" and member.get("User ID")
        }
        rows = "".join(
            "<tr>"
            f"<td>{escape(str(member['Email']))}</td>"
            f"<td>{escape(str(member['Role']))}</td>"
            + (
                '<td class="company-user-action-cell">'
                + (
                    '<button type="button" class="company-user-delete" '
                    'data-company-user-delete '
                    f'data-member-id="{escape(str(member.get("User ID") or ""))}" '
                    'aria-label="Remove user access" title="Remove user access">×</button>'
                    if member.get("Role") != "Owner"
                    else ""
                )
                + "</td>"
                if access.role == "owner"
                else ""
            )
            + "</tr>"
            for member in members
        )
        action_header = "<th aria-label=\"Action\"></th>" if access.role == "owner" else ""
        markup = (
            '<div class="company-profile-users"><table>'
            f'<thead><tr><th>Email</th><th>Role</th>{action_header}</tr></thead>'
            f"<tbody>{rows}</tbody></table></div>"
        )
    except Exception:
        st.error("Company users are unavailable right now.")
        return

    st.markdown(markup, unsafe_allow_html=True)

    if access.role != "owner":
        return

    raw_user_request = None
    with st.container(key="company_users_bridge_host"):
        raw_user_request = company_labor_bridge(key="company_users_bridge")
    if raw_user_request:
        try:
            request = json.loads(raw_user_request)
        except (TypeError, json.JSONDecodeError):
            request = None
        if isinstance(request, dict):
            nonce = _clean(request.get("nonce"))
            member_id = _clean(request.get("memberId"))
            if (
                request.get("action") == "user_delete"
                and nonce
                and nonce != st.session_state.get("_company_user_action_nonce")
                and member_id in removable_members
            ):
                st.session_state._company_user_action_nonce = nonce
                st.session_state._company_user_remove_id = member_id

    member_id = _clean(st.session_state.get("_company_user_remove_id"))
    removing = removable_members.get(member_id)
    if removing:
        def cancel_remove() -> None:
            st.session_state._company_user_remove_id = ""

        def confirm_remove() -> None:
            started_at = time.perf_counter()
            try:
                remove_company_member(access, member_id)
                st.session_state._company_user_remove_id = ""
                st.session_state._company_user_removed = True
                st.session_state.company_profile_tab = "Users"
                st.session_state._runtime_completed_action = {
                    "action": "company_member_access_removed",
                    "status": "ok",
                    "duration_ms": (time.perf_counter() - started_at) * 1000,
                }
            except (PermissionError, ValueError) as exc:
                st.session_state._company_user_remove_error = str(exc)
            except Exception:
                logger.exception("Company member removal failed")
                st.session_state._company_user_remove_error = (
                    "The user's access was not removed. Try again in a moment."
                )

        with st.container(key="company_user_remove_confirmation", border=True):
            st.warning(f"Remove access for {removing['Email']}?")
            remove_error = st.session_state.pop("_company_user_remove_error", None)
            if remove_error:
                st.error(remove_error)
            confirm_column, cancel_column = st.columns([3, 1])
            with confirm_column:
                st.button(
                    "Remove Access",
                    key="company_user_remove_confirm",
                    type="primary",
                    use_container_width=True,
                    on_click=confirm_remove,
                )
            with cancel_column:
                st.button(
                    "Cancel",
                    key="company_user_remove_cancel",
                    use_container_width=True,
                    on_click=cancel_remove,
                )
        return

    if st.session_state.pop("_company_user_removed", False):
        st.success("User access removed")

    def generate_invitation() -> None:
        started_at = time.perf_counter()
        try:
            st.session_state._company_generated_invite_url = (
                create_company_join_url(access)
            )
            st.session_state.company_profile_tab = "Users"
            st.session_state.pop("_company_invite_error", None)
            st.session_state._runtime_completed_action = {
                "action": "company_member_invite_created",
                "status": "ok",
                "duration_ms": (time.perf_counter() - started_at) * 1000,
            }
        except Exception:
            logger.exception("Company member invitation creation failed")
            st.session_state._company_invite_error = (
                "The invitation link could not be created. Try again in a moment."
            )

    st.button(
        "Generate Invitation Link",
        key="company_generate_invitation",
        type="primary",
        use_container_width=True,
        on_click=generate_invitation,
    )

    invite_error = st.session_state.pop("_company_invite_error", None)
    if invite_error:
        st.error(invite_error)

    generated_url = str(st.session_state.get("_company_generated_invite_url") or "")
    if generated_url:
        safe_url = escape(generated_url, quote=True)
        st.markdown(
            '<div class="company-profile-users company-profile-invite">'
            '<table><thead><tr><th>Invitation Link · Valid for 24 Hours</th></tr></thead>'
            '<tbody><tr><td><div class="company-profile-invite-value">'
            f'<span class="company-profile-invite-text">{escape(generated_url)}</span>'
            '<button type="button" class="company-invite-copy" '
            f'data-company-invite-copy data-invite-url="{safe_url}" '
            'aria-label="Copy invitation link">Copy</button>'
            '</div></td></tr></tbody></table></div>',
            unsafe_allow_html=True,
        )


def _labor_position_label(position_code: object) -> str:
    code = _clean(position_code)
    for positions in LABOR_POSITIONS.values():
        for candidate, label in positions:
            if candidate == code:
                return label
    if code in LABOR_LEGACY_POSITION_LABELS:
        return LABOR_LEGACY_POSITION_LABELS[code]
    return code.replace("_", " ").title() or "Not set"


def _labor_employment_factor(employee: dict) -> float:
    return round(
        float(
            employee.get("employment_factor")
            or LABOR_DEFAULT_EMPLOYMENT_FACTOR
        ),
        2,
    )


def _labor_hourly_cost(employee: dict) -> float | None:
    if employee.get("pay_type") != "hourly_rate":
        return None
    if employee.get("total_hourly_cost") is not None:
        return round(float(employee.get("total_hourly_cost") or 0), 2)
    return round(
        float(employee.get("gross_hourly_rate") or 0)
        * _labor_employment_factor(employee),
        2,
    )


def _labor_monthly_cost(employee: dict) -> float:
    if employee.get("total_monthly_cost") is not None:
        return round(float(employee.get("total_monthly_cost") or 0), 2)
    base_cost = (
        float(employee.get("gross_hourly_rate") or 0)
        * float(employee.get("monthly_hours") or 0)
        if employee.get("pay_type") == "hourly_rate"
        else float(employee.get("gross_monthly_salary") or 0)
    )
    return round(base_cost * _labor_employment_factor(employee), 2)


def _labor_money(value: object) -> str:
    amount = round(float(value or 0), 2)
    if amount == int(amount):
        return f"₪{int(amount):,}".replace(",", "\u202f")
    return f"₪{amount:,.2f}".replace(",", "\u202f")


def _labor_number(value: object) -> str:
    amount = round(float(value or 0), 2)
    return str(int(amount)) if amount == int(amount) else f"{amount:.2f}".rstrip("0")


def _labor_pay_details(employee: dict) -> str:
    if employee.get("pay_type") == "hourly_rate":
        return (
            f"{_labor_money(employee.get('gross_hourly_rate'))}/h · "
            f"{_labor_number(employee.get('monthly_hours'))}h"
        )
    return _labor_money(employee.get("gross_monthly_salary"))


def _labor_table_pay_type(pay_type: object) -> str:
    return {
        "hourly_rate": "Hourly",
        "monthly_salary": "Monthly",
    }.get(_clean(pay_type), "Not set")


def _render_employee_list(employees: list[dict]) -> None:
    if not employees:
        st.info("No workers have been added yet.")
        return
    rows = "".join(
        "<tr>"
        '<td><div class="company-labor-actions">'
        '<button type="button" class="company-labor-edit" data-company-labor-edit '
        f'data-employee-id="{escape(_clean(employee.get("employee_id")))}" '
        'aria-label="Edit worker" title="Edit worker">✎</button>'
        '<button type="button" class="company-labor-delete" data-company-labor-delete '
        f'data-employee-id="{escape(_clean(employee.get("employee_id")))}" '
        'aria-label="Remove worker" title="Remove worker">×</button>'
        "</div></td>"
        f"<td><strong>{escape(_clean(employee.get('worker_name')))}</strong></td>"
        f"<td>{escape(LABOR_DEPARTMENTS.get(_clean(employee.get('department')), 'Not set'))}</td>"
        f"<td>{escape(_labor_position_label(employee.get('position_code')))}</td>"
        f"<td>{escape(_labor_table_pay_type(employee.get('pay_type')))}</td>"
        f"<td>{escape(_labor_pay_details(employee))}</td>"
        f"<td><strong>{escape(_labor_money(_labor_monthly_cost(employee)))}</strong></td>"
        "</tr>"
        for employee in sorted(
            employees,
            key=lambda item: (
                {"production": 0, "management": 1, "office": 2}.get(
                    _clean(item.get("department")), 3
                ),
                _clean(item.get("worker_name")).lower(),
            ),
        )
    )
    total_hours = sum(
        float(employee.get("monthly_hours") or 0)
        for employee in employees
        if employee.get("pay_type") == "hourly_rate"
    )
    total_cost = sum(_labor_monthly_cost(employee) for employee in employees)
    st.markdown(
        '<div class="company-profile-users company-labor-list"><table>'
        '<colgroup><col class="company-labor-col-actions">'
        '<col class="company-labor-col-worker">'
        '<col class="company-labor-col-department">'
        '<col class="company-labor-col-position">'
        '<col class="company-labor-col-pay-type">'
        '<col class="company-labor-col-details"><col class="company-labor-col-monthly">'
        '</colgroup>'
        '<thead><tr class="company-labor-total-row">'
        '<th colspan="5">Total Monthly</th>'
        f'<th>{escape(_labor_number(total_hours))} h</th>'
        f'<th>{escape(_labor_money(total_cost))}</th></tr>'
        '<tr><th aria-label="Actions"></th><th>Worker</th><th>Department</th>'
        '<th>Position</th><th>Pay Type</th><th>Pay Details</th><th>Monthly</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _apply_labor_form_reset() -> None:
    if not st.session_state.pop("_labor_form_reset_pending", False):
        return
    st.session_state["_labor_form_version"] = int(
        st.session_state.get("_labor_form_version", 0)
    ) + 1
    st.session_state["_labor_edit_employee_id"] = ""
    st.session_state["_labor_delete_employee_id"] = ""
    for key in list(st.session_state):
        if str(key).startswith("labor_form_"):
            st.session_state.pop(key, None)


def _clear_labor_position(position_key: str) -> None:
    st.session_state.pop(position_key, None)


def _labor_input_number(
    value: object,
    *,
    label: str,
    decimals: int,
    whole: bool = False,
) -> float:
    cleaned = (
        str(value or "")
        .replace("₪", "")
        .replace(",", "")
        .replace("\u202f", "")
        .replace(" ", "")
        .strip()
    )
    try:
        number = float(cleaned)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None
    if number <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    if whole and number != int(number):
        raise ValueError(f"{label} must be a whole number.")
    return float(int(number)) if whole else round(number, decimals)


def _labor_form_number(
    value: object,
    *,
    decimals: int = 2,
    grouped: bool = False,
) -> str:
    number = round(float(value or 0), decimals)
    if number == int(number):
        integer = f"{int(number):,}" if grouped else str(int(number))
        return integer.replace(",", "\u202f")
    template = f"{{:,.{decimals}f}}" if grouped else f"{{:.{decimals}f}}"
    return template.format(number).rstrip("0").rstrip(".").replace(",", "\u202f")


def _format_grouped_number_input(widget_key: str, decimals: int = 2) -> None:
    value = st.session_state.get(widget_key)
    if str(value or "").strip() == "":
        return
    st.session_state[widget_key] = _labor_form_number(
        _metric_amount(value),
        decimals=decimals,
        grouped=True,
    )


def _clear_labor_pay_values(key_prefix: str) -> None:
    for suffix in (
        "gross_monthly_salary",
        "gross_hourly_rate",
        "monthly_hours",
        "employment_factor",
        "total_hourly_cost",
        "total_monthly_cost",
    ):
        st.session_state.pop(f"{key_prefix}_{suffix}", None)


def _sync_labor_totals(key_prefix: str, pay_type: str) -> None:
    factor = _metric_amount(
        st.session_state.get(
            f"{key_prefix}_employment_factor",
            LABOR_DEFAULT_EMPLOYMENT_FACTOR,
        )
    )
    st.session_state[f"{key_prefix}_employment_factor"] = f"{factor:.2f}"
    if pay_type == "monthly_salary":
        salary_key = f"{key_prefix}_gross_monthly_salary"
        salary = _metric_amount(st.session_state.get(salary_key))
        st.session_state[salary_key] = _labor_form_number(
            salary,
            decimals=0,
            grouped=True,
        )
        st.session_state[f"{key_prefix}_total_monthly_cost"] = _labor_money(
            salary * factor
        )
        return
    rate_key = f"{key_prefix}_gross_hourly_rate"
    hours_key = f"{key_prefix}_monthly_hours"
    hourly_rate = _metric_amount(st.session_state.get(rate_key))
    monthly_hours = _metric_amount(st.session_state.get(hours_key))
    st.session_state[rate_key] = _labor_form_number(
        hourly_rate,
        decimals=0,
        grouped=True,
    )
    st.session_state[hours_key] = _labor_form_number(
        monthly_hours,
        decimals=0,
        grouped=True,
    )
    st.session_state[f"{key_prefix}_total_hourly_cost"] = _labor_money(
        hourly_rate * factor
    )
    st.session_state[f"{key_prefix}_total_monthly_cost"] = _labor_money(
        hourly_rate * monthly_hours * factor
    )


def _format_labor_total_input(widget_key: str) -> None:
    st.session_state[widget_key] = _labor_money(
        _metric_amount(st.session_state.get(widget_key))
    )


def _consume_labor_action_request(
    raw_request: str | None,
) -> tuple[str, str] | None:
    if not raw_request:
        return None
    try:
        request = json.loads(raw_request)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(request, dict):
        return None
    nonce = _clean(request.get("nonce"))
    employee_id = _clean(request.get("employeeId"))
    action = _clean(request.get("action")) or "edit"
    if not nonce or not employee_id or action not in {"edit", "delete"}:
        return None
    if nonce == st.session_state.get("_labor_action_consumed_nonce"):
        return None
    st.session_state["_labor_action_consumed_nonce"] = nonce
    return action, employee_id


def _consume_labor_edit_request(raw_request: str | None) -> str | None:
    request = _consume_labor_action_request(raw_request)
    if request is None or request[0] != "edit":
        return None
    return request[1]


def _render_labor_costs(access: CompanyAccess, *, trace=None) -> None:
    if access.role != "owner":
        st.info("Labor cost details are available only to the company owner.")
        return

    _apply_labor_form_reset()
    if st.session_state.pop("_labor_employee_added", False):
        st.success("Worker added")
    if st.session_state.pop("_labor_employee_updated", False):
        st.success("Worker updated")
    if st.session_state.pop("_labor_employee_archived", False):
        st.success("Worker removed")

    try:
        if trace is None:
            employees = load_company_employees(access)
        else:
            with trace.span("server.labor_employee_list_load"):
                employees = load_company_employees(access)
    except PermissionError:
        st.error("Only the company owner can view employee costs.")
        return
    except Exception:
        logger.exception("Company employee list load failed")
        st.error("Worker costs are unavailable right now. Try again in a moment.")
        return

    _render_employee_list(employees)
    employee_by_id = {
        str(employee.get("employee_id")): employee
        for employee in employees
        if employee.get("employee_id")
    }
    raw_edit_request = None
    with st.container(key="company_labor_bridge_host"):
        raw_edit_request = company_labor_bridge(key="company_labor_bridge")
    action_request = _consume_labor_action_request(raw_edit_request)
    if action_request is not None and action_request[1] in employee_by_id:
        action, requested_employee_id = action_request
        if action == "edit":
            st.session_state["_labor_delete_employee_id"] = ""
            st.session_state["_labor_edit_employee_id"] = requested_employee_id
            st.session_state["_labor_form_version"] = int(
                st.session_state.get("_labor_form_version", 0)
            ) + 1
        else:
            st.session_state["_labor_edit_employee_id"] = ""
            st.session_state["_labor_delete_employee_id"] = requested_employee_id

    delete_employee_id = _clean(st.session_state.get("_labor_delete_employee_id"))
    deleting = employee_by_id.get(delete_employee_id)
    if deleting:
        with st.container(key="company_labor_delete_confirmation", border=True):
            st.warning(
                f"Remove {_clean(deleting.get('worker_name'))} from active workers? "
                "The saved record will be retained."
            )
            confirm_column, cancel_column = st.columns([3, 1])
            with confirm_column:
                confirmed = st.button(
                    "Remove Worker",
                    key="company_labor_delete_confirm",
                    type="primary",
                    use_container_width=True,
                )
            with cancel_column:
                delete_cancelled = st.button(
                    "Cancel",
                    key="company_labor_delete_cancel",
                    use_container_width=True,
                )
        if delete_cancelled:
            st.session_state["_labor_delete_employee_id"] = ""
            st.rerun()
        if confirmed:
            try:
                action_started_at = time.perf_counter()
                if trace is None:
                    archive_company_employee(access, delete_employee_id)
                else:
                    with trace.span("server.labor_employee_archive"):
                        archive_company_employee(access, delete_employee_id)
                st.session_state["_runtime_completed_action"] = {
                    "action": "labor_employee_archive",
                    "status": "ok",
                    "duration_ms": (time.perf_counter() - action_started_at) * 1000,
                }
                st.session_state["_labor_delete_employee_id"] = ""
                st.session_state["_labor_employee_archived"] = True
                st.rerun()
            except (PermissionError, ValueError) as exc:
                st.error(str(exc))
            except Exception:
                logger.exception("Company employee archive failed")
                st.error("The worker was not removed. Try again in a moment.")
        return
    edit_employee_id = _clean(st.session_state.get("_labor_edit_employee_id"))
    editing = employee_by_id.get(str(edit_employee_id))
    version = int(st.session_state.get("_labor_form_version", 0))
    mode = str(edit_employee_id or "new")
    key_prefix = f"labor_form_{version}_{mode}"

    default_department = _clean(editing.get("department")) if editing else ""
    department_labels = tuple(LABOR_DEPARTMENTS.values())
    default_department_label = LABOR_DEPARTMENTS.get(default_department)
    department_index = (
        department_labels.index(default_department_label)
        if default_department_label in department_labels else None
    )
    default_pay_type = _clean(editing.get("pay_type")) if editing else ""
    pay_labels = tuple(LABOR_PAY_TYPES.values())
    default_pay_label = LABOR_PAY_TYPES.get(default_pay_type)
    pay_index = pay_labels.index(default_pay_label) if default_pay_label in pay_labels else None

    with st.container(key="company_labor_card", border=True):
        worker_column, department_column = st.columns([2, 1])
        with worker_column:
            worker_name = st.text_input(
                "Worker name",
                value=_clean(editing.get("worker_name")) if editing else "",
                key=f"{key_prefix}_worker_name",
                placeholder="Name, nickname, or identifier",
            )

        position_key = f"{key_prefix}_position"
        with department_column:
            department_label = st.selectbox(
                "Department",
                options=department_labels,
                index=department_index,
                placeholder="Select department",
                key=f"{key_prefix}_department",
                on_change=_clear_labor_position,
                args=(position_key,),
            )
        department = next(
            (code for code, label in LABOR_DEPARTMENTS.items() if label == department_label),
            None,
        )
        position_column, pay_type_column = st.columns(2)
        position_options = LABOR_POSITIONS.get(department, ())
        position_labels = tuple(label for _code, label in position_options)
        default_position_label = (
            _labor_position_label(editing.get("position_code"))
            if editing and department == default_department else None
        )
        position_index = (
            position_labels.index(default_position_label)
            if default_position_label in position_labels else None
        )
        with position_column:
            position_label = st.selectbox(
                "Position",
                options=position_labels,
                index=position_index,
                placeholder="Select position",
                disabled=department is None,
                key=position_key,
            )
        position_code = next(
            (code for code, label in position_options if label == position_label),
            None,
        )
        with pay_type_column:
            pay_label = st.selectbox(
                "Pay type",
                options=pay_labels,
                index=pay_index,
                placeholder="Select pay type",
                key=f"{key_prefix}_pay_type",
                on_change=_clear_labor_pay_values,
                args=(key_prefix,),
            )
        pay_type = next(
            (code for code, label in LABOR_PAY_TYPES.items() if label == pay_label),
            None,
        )
        gross_monthly_salary_raw = ""
        gross_hourly_rate_raw = ""
        monthly_hours_raw = ""
        total_hourly_cost_raw = ""
        total_monthly_cost_raw = ""
        employment_factor_raw = (
            f"{_labor_employment_factor(editing):.2f}"
            if editing else f"{LABOR_DEFAULT_EMPLOYMENT_FACTOR:.2f}"
        )
        if pay_type == "monthly_salary":
            salary_column, factor_column, total_column = st.columns(3)
            with salary_column:
                gross_monthly_salary_raw = st.text_input(
                    "Monthly Salary",
                    value=_labor_form_number(
                        editing.get("gross_monthly_salary"),
                        decimals=0,
                        grouped=True,
                    ) if editing else "",
                    key=f"{key_prefix}_gross_monthly_salary",
                    placeholder="0",
                    on_change=_sync_labor_totals,
                    args=(key_prefix, "monthly_salary"),
                )
            with factor_column:
                employment_factor_raw = st.text_input(
                    "Employment Factor",
                    value=employment_factor_raw,
                    key=f"{key_prefix}_employment_factor",
                    help=LABOR_EMPLOYMENT_FACTOR_HELP,
                    on_change=_sync_labor_totals,
                    args=(key_prefix, "monthly_salary"),
                )
            initial_monthly_cost = (
                _labor_monthly_cost(editing) if editing else 0
            )
            with total_column:
                total_monthly_cost_raw = st.text_input(
                    "Total Monthly Cost",
                    value=_labor_money(initial_monthly_cost),
                    key=f"{key_prefix}_total_monthly_cost",
                    on_change=_format_labor_total_input,
                    args=(f"{key_prefix}_total_monthly_cost",),
                )
        elif pay_type == "hourly_rate":
            rate_column, hours_column = st.columns(2)
            with rate_column:
                gross_hourly_rate_raw = st.text_input(
                    "Hourly Rate",
                    value=_labor_form_number(
                        editing.get("gross_hourly_rate"),
                        decimals=0,
                        grouped=True,
                    ) if editing else "",
                    key=f"{key_prefix}_gross_hourly_rate",
                    placeholder="0",
                    on_change=_sync_labor_totals,
                    args=(key_prefix, "hourly_rate"),
                )
            with hours_column:
                monthly_hours_raw = st.text_input(
                    "Average Hours per Month",
                    value=_labor_form_number(
                        editing.get("monthly_hours"),
                        decimals=0,
                        grouped=True,
                    ) if editing else "",
                    key=f"{key_prefix}_monthly_hours",
                    placeholder="0",
                    on_change=_sync_labor_totals,
                    args=(key_prefix, "hourly_rate"),
                )
            factor_column, hourly_total_column, monthly_total_column = st.columns(3)
            with factor_column:
                employment_factor_raw = st.text_input(
                    "Employment Factor",
                    value=employment_factor_raw,
                    key=f"{key_prefix}_employment_factor",
                    help=LABOR_EMPLOYMENT_FACTOR_HELP,
                    on_change=_sync_labor_totals,
                    args=(key_prefix, "hourly_rate"),
                )
            initial_hourly_cost = _labor_hourly_cost(editing) if editing else 0
            initial_monthly_cost = _labor_monthly_cost(editing) if editing else 0
            with hourly_total_column:
                total_hourly_cost_raw = st.text_input(
                    "Total Hourly Cost",
                    value=_labor_money(initial_hourly_cost),
                    key=f"{key_prefix}_total_hourly_cost",
                    on_change=_format_labor_total_input,
                    args=(f"{key_prefix}_total_hourly_cost",),
                )
            with monthly_total_column:
                total_monthly_cost_raw = st.text_input(
                    "Total Monthly Cost",
                    value=_labor_money(initial_monthly_cost),
                    key=f"{key_prefix}_total_monthly_cost",
                    on_change=_format_labor_total_input,
                    args=(f"{key_prefix}_total_monthly_cost",),
                )

        if editing:
            save_column, cancel_column = st.columns([3, 1])
            with save_column:
                submitted = st.button(
                    "Save Worker",
                    key=f"{key_prefix}_save",
                    type="primary",
                    use_container_width=True,
                )
            with cancel_column:
                cancelled = st.button(
                    "Cancel Edit",
                    key=f"{key_prefix}_cancel",
                    use_container_width=True,
                )
        else:
            submitted = st.button(
                "Add Worker",
                key=f"{key_prefix}_add",
                type="primary",
                use_container_width=True,
            )
            cancelled = False
    if cancelled:
        st.session_state["_labor_form_reset_pending"] = True
        st.rerun()
    if submitted:
        try:
            gross_monthly_salary = 0.0
            gross_hourly_rate = 0.0
            monthly_hours = 0.0
            total_hourly_cost = 0.0
            total_monthly_cost = 0.0
            employment_factor = _labor_input_number(
                employment_factor_raw,
                label="Employment factor",
                decimals=2,
            )
            if pay_type == "monthly_salary":
                gross_monthly_salary = _labor_input_number(
                    gross_monthly_salary_raw,
                    label="Monthly salary",
                    decimals=0,
                    whole=True,
                )
                total_monthly_cost = _labor_input_number(
                    total_monthly_cost_raw,
                    label="Total monthly cost",
                    decimals=2,
                )
            elif pay_type == "hourly_rate":
                gross_hourly_rate = _labor_input_number(
                    gross_hourly_rate_raw,
                    label="Hourly rate",
                    decimals=0,
                    whole=True,
                )
                total_hourly_cost = _labor_input_number(
                    total_hourly_cost_raw,
                    label="Total hourly cost",
                    decimals=2,
                )
                total_monthly_cost = _labor_input_number(
                    total_monthly_cost_raw,
                    label="Total monthly cost",
                    decimals=2,
                )
                monthly_hours = _labor_input_number(
                    monthly_hours_raw,
                    label="Average hours per month",
                    decimals=0,
                    whole=True,
                )
            values = {
                "worker_name": worker_name,
                "department": department or "",
                "position_code": position_code or "",
                "pay_type": pay_type or "",
                "gross_monthly_salary": gross_monthly_salary,
                "gross_hourly_rate": gross_hourly_rate,
                "monthly_hours": monthly_hours,
                "employment_factor": employment_factor,
                "total_hourly_cost": total_hourly_cost,
                "total_monthly_cost": total_monthly_cost,
            }
            action_started_at = time.perf_counter()
            if editing and trace is None:
                update_company_employee(access, str(edit_employee_id), **values)
            elif editing:
                with trace.span("server.labor_employee_update"):
                    update_company_employee(access, str(edit_employee_id), **values)
            elif trace is None:
                add_company_employee(access, **values)
            else:
                with trace.span("server.labor_employee_insert"):
                    add_company_employee(access, **values)
            st.session_state["_runtime_completed_action"] = {
                "action": (
                    "labor_employee_update" if editing else "labor_employee_insert"
                ),
                "status": "ok",
                "duration_ms": (time.perf_counter() - action_started_at) * 1000,
            }
            st.session_state["_labor_form_reset_pending"] = True
            st.session_state[
                "_labor_employee_updated" if editing else "_labor_employee_added"
            ] = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except PermissionError:
            st.error("Only the company owner can change worker costs.")
        except Exception:
            logger.exception("Company employee write failed")
            action = "updated" if editing else "added"
            st.error(f"The worker was not {action}. Try again in a moment.")


def _open_upload_screen() -> None:
    """Set navigation state before Streamlit starts the next script render."""
    from state.session import set_screen

    set_screen("upload")


def render_company_profile(access: CompanyAccess, *, trace=None) -> None:
    phase_started_at = time.perf_counter()

    def finish_phase(name: str, summary_key: str) -> None:
        nonlocal phase_started_at
        finished_at = time.perf_counter()
        if trace is not None:
            duration_ms = (finished_at - phase_started_at) * 1000
            trace.event(
                name,
                duration_ms=duration_ms,
            )
            trace.annotate(**{summary_key: round(duration_ms, 3)})
        phase_started_at = finished_at

    apply_company_profile_css()
    apply_object_detail_css()
    st.markdown(
        '<div class="company-profile-active" style="display:none"></div>',
        unsafe_allow_html=True,
    )
    finish_phase("server.company_profile_styles", "p_styles_ms")

    header_left, header_right = st.columns([3.6, 2])
    with header_left:
        st.markdown(
            f'<div class="company-profile-heading"><div class="company-profile-mark">{_brand_mark()}</div>'
            '<h1>Company profile</h1></div>',
            unsafe_allow_html=True,
        )
    with header_right:
        with st.container(key="company_profile_actions"):
            projects_action, estimate_action, sign_out_action = st.columns([1, 1.15, 1])
            with projects_action:
                st.button(
                    "Projects",
                    key="profile_projects_placeholder",
                    use_container_width=True,
                    disabled=True,
                    help="Project history is coming next.",
                )
            with estimate_action:
                st.button(
                    "New Estimate",
                    key="profile_to_upload",
                    use_container_width=True,
                    on_click=_open_upload_screen,
                )
            with sign_out_action:
                from state.company_auth import sign_out

                st.button(
                    "Sign out",
                    key="company_sign_out",
                    use_container_width=True,
                    on_click=sign_out,
                )
    finish_phase("server.company_profile_header", "p_header_ms")

    expenses_tab, labor_tab, machinery_tab, prices_tab, contacts_tab, company_tab, users_tab = st.tabs(
        [
            "Overhead Expenses",
            "Labor Costs",
            "Machinery",
            "Price Lists",
            "Contacts",
            "Bank Details",
            "Users",
        ],
        key="company_profile_tab",
        on_change="rerun",
    )
    finish_phase("server.company_profile_tabs", "p_tabs_ms")

    if expenses_tab.open:
        with expenses_tab:
            if trace is None:
                _render_metrics(access)
            else:
                with trace.span("server.expenses_render"):
                    _render_metrics(access)
    elif labor_tab.open:
        with labor_tab:
            if trace is None:
                _render_labor_costs(access)
            else:
                with trace.span("server.labor_costs_render"):
                    _render_labor_costs(access, trace=trace)
    elif machinery_tab.open:
        with machinery_tab:
            if trace is None:
                _render_machinery(access)
            else:
                with trace.span("server.machinery_render"):
                    _render_machinery(access)
    elif contacts_tab.open or company_tab.open:
        try:
            if trace is None:
                profile = load_company_profile(access)
            else:
                with trace.span("server.company_settings_load"):
                    profile = load_company_profile(access)
        except Exception:
            st.error("Company profile is unavailable right now. Try again in a moment.")
            finish_phase("server.company_profile_content", "p_body_ms")
            return

        if contacts_tab.open:
            with contacts_tab:
                if access.role == "owner":
                    _render_owner_contacts(access, profile, trace=trace)
                else:
                    _render_member_contacts(access, profile, trace=trace)
        else:
            with company_tab:
                if access.role == "owner":
                    _render_owner_bank_details(access, profile)
                else:
                    _render_member_bank_details(profile)
    elif users_tab.open:
        with users_tab:
            if trace is None:
                _render_users(access)
            else:
                with trace.span("server.users_render"):
                    _render_users(access)
    elif prices_tab.open:
        with prices_tab:
            if trace is None:
                _render_price_lists(access)
            else:
                with trace.span("server.price_sources_render"):
                    _render_price_lists(access, trace=trace)

    finish_phase("server.company_profile_content", "p_body_ms")
