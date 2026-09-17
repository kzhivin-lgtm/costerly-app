from __future__ import annotations

from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from db.company_access import assert_company_owner
from db.supabase_client import get_supabase_client
from styles.company_profile import apply_company_profile_css
from use_cases.email_addresses import is_valid_email_address

if TYPE_CHECKING:
    from state.company_auth import CompanyAccess


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
)
METRIC_MONTHLY_FIELDS = tuple(
    field for _group, rows in METRIC_GROUPS for field, _label in rows
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
    fresh = _current_access(access)
    rows = (
        get_supabase_client().table("companies")
        .select(PROFILE_COLUMNS)
        .eq("company_id", fresh.company_id)
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
    monthly_rows = (
        client.table("overhead_monthly")
        .select("company_id," + ",".join(METRIC_MONTHLY_FIELDS))
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
        settings_payload[field] = round(value, 4)

    monthly_payload = {"company_id": fresh.company_id}
    for field in METRIC_MONTHLY_FIELDS:
        value = float(monthly_values.get(field) or 0)
        if value < 0:
            raise ValueError("Monthly overhead costs cannot be negative.")
        monthly_payload[field] = int(round(value))

    client.table("overhead_settings").upsert(
        settings_payload, on_conflict="company_id"
    ).execute()
    client.table("overhead_monthly").upsert(
        monthly_payload, on_conflict="company_id"
    ).execute()
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
        st.success("Company details saved.")
    except ValueError as exc:
        st.error(str(exc))
    except PermissionError:
        st.error("Only the company owner can save these details.")
    except Exception:
        st.error("Company details were not saved. Try again in a moment.")


def _render_owner_general(access: CompanyAccess, profile: dict) -> None:
    with st.form("company_profile_general"):
        first_left, first_right = st.columns(2)
        with first_left:
            company_name = _text_input(profile, "Company name", "company_name")
        with first_right:
            legal_name_hebrew = _text_input(
                profile, "Company legal name (Hebrew)", "legal_name_hebrew"
            )
        second_left, second_right = st.columns(2)
        with second_left:
            registration = _text_input(
                profile, "Company registration number", "company_registration_number"
            )
        with second_right:
            legal_name = _text_input(
                profile, "Company legal name (English)", "legal_name"
            )
        saved = _profile_save_button("Save General Details")
    if saved:
        _save_profile_section(access, {
            "company_name": company_name,
            "legal_name_hebrew": legal_name_hebrew,
            "company_registration_number": registration,
            "legal_name": legal_name,
        })


def _render_owner_contacts(access: CompanyAccess, profile: dict) -> None:
    with st.form("company_profile_contacts"):
        contact_left, contact_right = st.columns(2)
        with contact_left:
            official_email = _text_input(
                profile, "Official email", "public_email", placeholder="office@company.com"
            )
        with contact_right:
            phone = _text_input(profile, "Phone", "public_phone", placeholder="+972 00 000 0000")
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
            "public_phone": phone,
            "website_url": website,
            "address_street": street,
            "address_house_number": house_number,
            "address_city": city,
            "address_postal_code": postal_code,
            "linkedin_url": linkedin,
            "instagram_url": instagram,
            "facebook_url": facebook,
        })


def _render_owner_bank_details(access: CompanyAccess, profile: dict) -> None:
    with st.form("company_profile_bank_details"):
        domestic_name_column, _domestic_name_space = st.columns(2)
        with domestic_name_column:
            _text_input(
                profile,
                "Company legal name (Hebrew)",
                "legal_name_hebrew",
                widget_key="profile_bank_legal_name_hebrew",
                disabled=True,
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

        international_name_column, _international_name_space = st.columns(2)
        with international_name_column:
            _text_input(
                profile,
                "Company legal name (English)",
                "legal_name",
                widget_key="profile_bank_legal_name_english",
                disabled=True,
            )

        international_left, international_right = st.columns(2)
        with international_left:
            iban = _text_input(profile, "IBAN", "iban")
        with international_right:
            swift = _text_input(profile, "BIC", "swift")
        saved = _profile_save_button("Save Bank Details")
    if saved:
        _save_profile_section(access, {
            "bank_name": bank_name,
            "bank_number": bank_number,
            "branch_number": branch_number,
            "account_number": account_number,
            "iban": iban,
            "swift": swift,
        })


def _render_member_general(profile: dict) -> None:
    _read_only_group("General Details", [
        ("Company name", profile.get("company_name")),
        ("Company legal name (Hebrew)", profile.get("legal_name_hebrew")),
        ("Company registration number", profile.get("company_registration_number")),
        ("Company legal name (English)", profile.get("legal_name")),
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
        ("LinkedIn", profile.get("linkedin_url")),
        ("Instagram", profile.get("instagram_url")),
        ("Facebook", profile.get("facebook_url")),
    ])


def _render_member_bank_details(profile: dict) -> None:
    _read_only_group("Bank details", [
        ("Company legal name (Hebrew)", profile.get("legal_name_hebrew")),
        ("Bank name", profile.get("bank_name")),
        ("Bank number", profile.get("bank_number")),
        ("Branch number", profile.get("branch_number")),
        ("Account number", profile.get("account_number")),
        ("Company legal name (English)", profile.get("legal_name")),
        ("IBAN", profile.get("iban")),
        ("BIC", profile.get("swift")),
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
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


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


def _metric_readonly_amount(value: float, *, unavailable: bool = False) -> None:
    display = "—" if unavailable else _metric_money(value)
    st.markdown(
        f'<div class="company-metric-readonly">{display}</div>',
        unsafe_allow_html=True,
    )


def _render_metrics(access: CompanyAccess) -> None:
    try:
        settings, monthly = load_company_metrics(access)
    except Exception:
        st.error("Company metrics are unavailable right now. Try again in a moment.")
        return

    editable = access.role == "owner"
    with st.container(key="company_metrics_card", border=True):
        vat_column, _vat_space = st.columns([1, 3])
        with vat_column:
            vat_key = "profile_metric_vat_percent"
            _ensure_metric_text_state(
                vat_key, _metric_percent_text(settings.get("vat_percent"))
            )
            vat_raw = st.text_input(
                "Ma'am / VAT rate, %",
                key=vat_key,
                on_change=_normalize_metric_percent,
                args=(vat_key,),
                disabled=not editable,
            )
            vat_percent = min(100.0, _metric_amount(vat_raw))

        with st.container(key="company_metrics_header"):
            header_name, header_net, header_vat, header_total = st.columns(
                [2.2, 1.2, 1, 1]
            )
            header_name.markdown("Expense")
            header_net.markdown("Monthly cost")
            header_vat.markdown("VAT")
            header_total.markdown("Total")

        monthly_values: dict[str, float] = {}
        for group_name, rows in METRIC_GROUPS:
            st.markdown(
                f'<div class="company-metric-group">{escape(group_name)}</div>',
                unsafe_allow_html=True,
            )
            for row_index, (field, label) in enumerate(rows):
                row_suffix = "_last" if row_index == len(rows) - 1 else ""
                with st.container(key=f"company_metric_row_{field}{row_suffix}"):
                    name_column, net_column, row_vat_column, total_column = st.columns(
                        [2.2, 1.2, 1, 1]
                    )
                    name_column.markdown(
                        f'<div class="company-metric-name">{escape(label)}</div>',
                        unsafe_allow_html=True,
                    )
                    with net_column:
                        metric_key = f"profile_metric_{field}"
                        _ensure_metric_text_state(
                            metric_key, _metric_money(monthly.get(field))
                        )
                        net_raw = st.text_input(
                            f"{label}, monthly cost",
                            key=metric_key,
                            on_change=_normalize_metric_money,
                            args=(metric_key,),
                            label_visibility="collapsed",
                            disabled=not editable,
                        )
                        net_amount = round(_metric_amount(net_raw))
                    vat_amount = _metric_vat(field, net_amount, vat_percent)
                    with row_vat_column:
                        _metric_readonly_amount(
                            vat_amount,
                            unavailable=field == "arnona_facilities_cost",
                        )
                    with total_column:
                        _metric_readonly_amount(net_amount + vat_amount)
                monthly_values[field] = net_amount

        st.markdown(
            '<div class="company-metric-group">Project Reserves</div>',
            unsafe_allow_html=True,
        )
        reserve_left, reserve_right = st.columns(2)
        with reserve_left:
            warranty_key = "profile_metric_warranty_reserve_percent"
            _ensure_metric_text_state(
                warranty_key,
                _metric_percent_text(settings.get("warranty_reserve_percent")),
            )
            warranty_raw = st.text_input(
                "Warranty reserve, %",
                key=warranty_key,
                on_change=_normalize_metric_percent,
                args=(warranty_key,),
                disabled=not editable,
            )
            warranty_percent = min(100.0, _metric_amount(warranty_raw))
        with reserve_right:
            management_key = "profile_metric_management_buffer_percent"
            _ensure_metric_text_state(
                management_key,
                _metric_percent_text(settings.get("management_buffer_percent")),
            )
            management_raw = st.text_input(
                "Management buffer, %",
                key=management_key,
                on_change=_normalize_metric_percent,
                args=(management_key,),
                disabled=not editable,
            )
            management_percent = min(100.0, _metric_amount(management_raw))

        if editable and st.button(
            "Save Metrics",
            key="save_profile_metrics",
            type="primary",
            use_container_width=True,
        ):
            try:
                save_company_metrics(
                    access,
                    {
                        "vat_percent": vat_percent,
                        "warranty_reserve_percent": warranty_percent,
                        "management_buffer_percent": management_percent,
                    },
                    monthly_values,
                )
                st.success("Company metrics saved.")
            except ValueError as exc:
                st.error(str(exc))
            except PermissionError:
                st.error("Only the company owner can save these metrics.")
            except Exception:
                st.error("Company metrics were not saved. Try again in a moment.")


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


def render_company_profile(access: CompanyAccess) -> None:
    apply_company_profile_css()
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
                if st.button(
                    "Continue to upload",
                    key="profile_to_upload",
                    use_container_width=True,
                ):
                    st.session_state.screen = "upload"
                    st.rerun()
            with sign_out_action:
                if st.button("Sign out", key="company_sign_out", use_container_width=True):
                    from state.company_auth import sign_out

                    sign_out()
                    st.rerun()

    try:
        profile = load_company_profile(access)
    except Exception:
        st.error("Company profile is unavailable right now. Try again in a moment.")
        return

    general_tab, contacts_tab, bank_tab, metrics_tab, users_tab, prices_tab = st.tabs(
        ["General Details", "Contacts", "Bank Details", "Metrics", "Users", "Price List"]
    )
    with general_tab:
        if access.role == "owner":
            _render_owner_general(access, profile)
        else:
            _render_member_general(profile)

    with contacts_tab:
        if access.role == "owner":
            _render_owner_contacts(access, profile)
        else:
            _render_member_contacts(profile)

    with bank_tab:
        if access.role == "owner":
            _render_owner_bank_details(access, profile)
        else:
            _render_member_bank_details(profile)

    with metrics_tab:
        _render_metrics(access)

    with users_tab:
        _render_users(access)

    with prices_tab:
        st.info("Company price lists and the shared fallback library will be configured here.")
