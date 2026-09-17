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
        st.info("Rent, payroll, utilities, equipment and other cost drivers will be configured here.")

    with users_tab:
        _render_users(access)

    with prices_tab:
        st.info("Company price lists and the shared fallback library will be configured here.")
