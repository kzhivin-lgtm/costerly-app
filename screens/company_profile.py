from __future__ import annotations

from html import escape
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from db.company_access import assert_company_owner
from db.supabase_client import get_supabase_client
from styles.company_profile import apply_company_profile_css
from styles.object_detail import apply_object_detail_css
from ui import company_metrics_view
from ui.company_metrics_bridge import company_metrics_bridge
from ui.js_guards import install_company_metrics_input_guard
from use_cases.email_addresses import is_valid_email_address

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
        ("purchasing_manager", "Purchasing Manager"),
        ("designer_draftsperson", "Designer / Draftsperson"),
    ),
    "production": (
        ("cabinetmaker_joiner", "Cabinetmaker / Joiner"),
        ("carpenter", "Carpenter"),
        ("welder", "Welder"),
        ("cnc_operator", "CNC Operator"),
        ("painter_finisher", "Painter / Finisher"),
        ("installer", "Installer"),
        ("general_worker", "General Worker"),
    ),
}
LABOR_PAY_TYPES = {
    "monthly_salary": "Monthly Salary",
    "hourly_rate": "Hourly Rate",
}
LABOR_EMPLOYEE_COLUMNS = (
    "employee_id,company_id,worker_name,department,position_code,"
    "pay_type,gross_monthly_salary,gross_hourly_rate,monthly_hours,created_at"
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
        members.append({"Email": email, "Role": "Owner" if row["role"] == "owner" else "Member"})
    return sorted(members, key=lambda item: (item["Role"] != "Owner", item["Email"].lower()))


def _owner_access(access: CompanyAccess) -> tuple[CompanyAccess, object]:
    fresh = _current_access(access)
    if fresh.role != "owner":
        raise PermissionError("Only the company owner can access employee costs.")
    client = get_supabase_client()
    assert_company_owner(client, fresh.user_id, fresh.company_id)
    return fresh, client


def load_company_employees(access: CompanyAccess) -> list[dict]:
    fresh, client = _owner_access(access)
    return (
        client.table("company_employees")
        .select(LABOR_EMPLOYEE_COLUMNS)
        .eq("company_id", fresh.company_id)
        .order("worker_name")
        .execute()
    ).data or []


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
) -> dict:
    payload = _company_employee_payload(
        worker_name=worker_name,
        department=department,
        position_code=position_code,
        pay_type=pay_type,
        gross_monthly_salary=gross_monthly_salary,
        gross_hourly_rate=gross_hourly_rate,
        monthly_hours=monthly_hours,
    )
    fresh, client = _owner_access(access)
    result = client.table("company_employees").insert({
        "company_id": fresh.company_id,
        **payload,
    }).execute()
    rows = result.data or []
    if len(rows) != 1 or str(rows[0].get("company_id")) != fresh.company_id:
        raise RuntimeError("The worker was not added.")
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

    payload = {
        "worker_name": worker_name,
        "department": department,
        "position_code": position_code,
        "pay_type": pay_type,
        "gross_monthly_salary": None,
        "gross_hourly_rate": None,
        "monthly_hours": None,
    }
    if pay_type == "monthly_salary":
        salary = round(float(gross_monthly_salary or 0), 2)
        if salary <= 0:
            raise ValueError("Avg monthly bruto must be greater than zero.")
        payload["gross_monthly_salary"] = salary
    else:
        hourly_rate = round(float(gross_hourly_rate or 0), 1)
        hours_value = float(monthly_hours or 0)
        hours = int(hours_value)
        if hourly_rate <= 0:
            raise ValueError("Hourly rate must be greater than zero.")
        if hours <= 0:
            raise ValueError("Average hours per month must be greater than zero.")
        if hours_value != hours:
            raise ValueError("Average hours per month must be a whole number.")
        payload["gross_hourly_rate"] = hourly_rate
        payload["monthly_hours"] = hours
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


def _save_profile_section(access: CompanyAccess, values: dict[str, object]) -> None:
    try:
        save_company_profile(access, values)
        st.success("Company details saved")
    except ValueError as exc:
        st.error(str(exc))
    except PermissionError:
        st.error("Only the company owner can save these details.")
    except Exception:
        st.error("Company details were not saved. Try again in a moment.")


def _render_owner_company_details(access: CompanyAccess, profile: dict) -> None:
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
        saved = _profile_save_button("Save Company Details")
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
        })


def _render_owner_contacts(access: CompanyAccess, profile: dict) -> None:
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
        })


def _render_member_company_details(profile: dict) -> None:
    _read_only_group("Company Details", [
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


def _render_member_contacts(profile: dict) -> None:
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
    from state.company_auth import company_join_url

    try:
        members = load_company_members(access)
        rows = "".join(
            f"<tr><td>{escape(member['Email'])}</td><td>{escape(member['Role'])}</td></tr>"
            for member in members
        )
        st.markdown(
            '<div class="company-profile-users"><table>'
            '<thead><tr><th>Email</th><th>Role</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        st.error("Company users are unavailable right now.")
    if access.role == "owner":
        st.markdown("### Team invitation link")
        try:
            st.code(company_join_url(access), language=None)
        except Exception:
            st.error("The team invitation link is unavailable right now.")


def _labor_position_label(position_code: object) -> str:
    code = _clean(position_code)
    for positions in LABOR_POSITIONS.values():
        for candidate, label in positions:
            if candidate == code:
                return label
    return code.replace("_", " ").title() or "Not set"


def _labor_monthly_gross(employee: dict) -> float:
    if employee.get("pay_type") == "hourly_rate":
        return round(
            float(employee.get("gross_hourly_rate") or 0)
            * float(employee.get("monthly_hours") or 0),
            2,
        )
    return round(float(employee.get("gross_monthly_salary") or 0), 2)


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
            f"{_labor_money(employee.get('gross_hourly_rate'))} / h · "
            f"{_labor_number(employee.get('monthly_hours'))} h"
        )
    return _labor_money(employee.get("gross_monthly_salary"))


def _render_employee_list(employees: list[dict]) -> None:
    if not employees:
        st.info("No workers have been added yet.")
        return
    rows = "".join(
        "<tr>"
        f"<td><strong>{escape(_clean(employee.get('worker_name')))}</strong></td>"
        f"<td>{escape(LABOR_DEPARTMENTS.get(_clean(employee.get('department')), 'Not set'))}</td>"
        f"<td>{escape(_labor_position_label(employee.get('position_code')))}</td>"
        f"<td>{escape(LABOR_PAY_TYPES.get(_clean(employee.get('pay_type')), 'Not set'))}</td>"
        f"<td>{escape(_labor_pay_details(employee))}</td>"
        f"<td><strong>{escape(_labor_money(_labor_monthly_gross(employee)))}</strong></td>"
        "</tr>"
        for employee in employees
    )
    total = sum(_labor_monthly_gross(employee) for employee in employees)
    st.markdown(
        '<div class="company-labor-summary">'
        '<span>Total Monthly Bruto</span>'
        f'<strong>{escape(_labor_money(total))}</strong></div>'
        '<div class="company-profile-users company-labor-list"><table>'
        '<thead><tr><th>Worker</th><th>Department</th><th>Position</th>'
        '<th>Pay Type</th><th>Pay Details</th><th>Monthly Bruto</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _apply_labor_form_reset() -> None:
    if not st.session_state.pop("_labor_form_reset_pending", False):
        return
    st.session_state["_labor_form_version"] = int(
        st.session_state.get("_labor_form_version", 0)
    ) + 1
    st.session_state["labor_edit_worker"] = ""
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


def _labor_form_number(value: object, *, decimals: int = 2) -> str:
    number = round(float(value or 0), decimals)
    if number == int(number):
        return str(int(number))
    return f"{number:.{decimals}f}".rstrip("0").rstrip(".")


def _labor_worker_option(employee: dict) -> str:
    return (
        f"{_clean(employee.get('worker_name'))} · "
        f"{_labor_position_label(employee.get('position_code'))}"
    )


def _render_labor_costs(access: CompanyAccess, *, trace=None) -> None:
    if access.role != "owner":
        st.info("Labor cost details are available only to the company owner.")
        return

    _apply_labor_form_reset()
    if st.session_state.pop("_labor_employee_added", False):
        st.success("Worker added")
    if st.session_state.pop("_labor_employee_updated", False):
        st.success("Worker updated")

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
    edit_employee_id = ""
    if employee_by_id:
        edit_employee_id = st.selectbox(
            "Edit worker",
            options=("", *employee_by_id),
            format_func=lambda employee_id: (
                "Select a worker" if not employee_id
                else _labor_worker_option(employee_by_id[employee_id])
            ),
            key="labor_edit_worker",
        )
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
        worker_name = st.text_input(
            "Worker name",
            value=_clean(editing.get("worker_name")) if editing else "",
            key=f"{key_prefix}_worker_name",
            placeholder="Name, nickname, or identifier",
        )

        department_column, position_column, pay_type_column = st.columns(3)
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
            )
        pay_type = next(
            (code for code, label in LABOR_PAY_TYPES.items() if label == pay_label),
            None,
        )
        gross_monthly_salary_raw = ""
        gross_hourly_rate_raw = ""
        monthly_hours_raw = ""
        if pay_type == "monthly_salary":
            gross_monthly_salary_raw = st.text_input(
                "Avg Monthly Bruto",
                value=_labor_form_number(editing.get("gross_monthly_salary")) if editing else "",
                key=f"{key_prefix}_gross_monthly_salary",
                placeholder="12000",
            )
        elif pay_type == "hourly_rate":
            rate_column, hours_column, bruto_column = st.columns(3)
            with rate_column:
                gross_hourly_rate_raw = st.text_input(
                    "Hourly Rate",
                    value=_labor_form_number(
                        editing.get("gross_hourly_rate"), decimals=1
                    ) if editing else "",
                    key=f"{key_prefix}_gross_hourly_rate",
                    placeholder="50.0",
                )
            with hours_column:
                monthly_hours_raw = st.text_input(
                    "Average Hours per Month",
                    value=_labor_form_number(
                        editing.get("monthly_hours"), decimals=0
                    ) if editing else "",
                    key=f"{key_prefix}_monthly_hours",
                    placeholder="160",
                )
            estimated_bruto = (
                _metric_amount(gross_hourly_rate_raw)
                * _metric_amount(monthly_hours_raw)
            )
            with bruto_column:
                st.text_input(
                    "Avg Monthly Bruto",
                    value=_labor_money(estimated_bruto),
                    disabled=True,
                    key=f"{key_prefix}_calculated_bruto",
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
            if pay_type == "monthly_salary":
                gross_monthly_salary = _labor_input_number(
                    gross_monthly_salary_raw,
                    label="Avg monthly bruto",
                    decimals=2,
                )
            elif pay_type == "hourly_rate":
                gross_hourly_rate = _labor_input_number(
                    gross_hourly_rate_raw,
                    label="Hourly rate",
                    decimals=1,
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
            }
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
    st.session_state.screen = "upload"


def render_company_profile(access: CompanyAccess, *, trace=None) -> None:
    apply_company_profile_css()
    apply_object_detail_css()
    st.markdown('<div class="company-profile-active" style="display:none"></div>', unsafe_allow_html=True)
    header_left, header_right = st.columns([4, 1.6])
    with header_left:
        st.markdown(
            f'<div class="company-profile-heading"><div class="company-profile-mark">{_brand_mark()}</div>'
            '<h1>Company profile</h1></div>',
            unsafe_allow_html=True,
        )
    with header_right:
        with st.container(key="company_profile_actions"):
            upload_action, sign_out_action = st.columns([1.4, 0.8])
            with upload_action:
                st.button(
                    "Continue to upload",
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

    expenses_tab, labor_tab, contacts_tab, company_tab, users_tab, prices_tab = st.tabs(
        [
            "Overhead Expenses",
            "Labor Costs",
            "Contacts",
            "Company Details",
            "Users",
            "Price Lists",
        ],
        key="company_profile_tab",
        on_change="rerun",
    )

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
    elif contacts_tab.open or company_tab.open:
        try:
            if trace is None:
                profile = load_company_profile(access)
            else:
                with trace.span("server.company_settings_load"):
                    profile = load_company_profile(access)
        except Exception:
            st.error("Company profile is unavailable right now. Try again in a moment.")
            return

        if contacts_tab.open:
            with contacts_tab:
                if access.role == "owner":
                    _render_owner_contacts(access, profile)
                else:
                    _render_member_contacts(profile)
        else:
            with company_tab:
                if access.role == "owner":
                    _render_owner_company_details(access, profile)
                else:
                    _render_member_company_details(profile)
    elif users_tab.open:
        with users_tab:
            if trace is None:
                _render_users(access)
            else:
                with trace.span("server.users_render"):
                    _render_users(access)
    elif prices_tab.open:
        with prices_tab:
            st.info("Company price lists and the shared fallback library will be configured here.")
