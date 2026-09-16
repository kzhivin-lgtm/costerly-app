from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

import streamlit as st

from db.company_access import assert_company_owner
from db.supabase_client import get_supabase_client
from use_cases.email_addresses import is_valid_email_address
from styles.company_profile import apply_company_profile_css

if TYPE_CHECKING:
    from state.company_auth import CompanyAccess


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


def load_company_profile(access: CompanyAccess) -> dict:
    fresh = _current_access(access)
    rows = (
        get_supabase_client().table("companies")
        .select("company_id,company_name,public_email,public_phone")
        .eq("company_id", fresh.company_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise PermissionError("Company profile is unavailable.")
    return rows[0]


def save_company_contacts(
    access: CompanyAccess, name: str, public_email: str, public_phone: str
) -> dict:
    fresh = _current_access(access)
    name = name.strip()
    public_email = public_email.strip()
    public_phone = public_phone.strip()
    if not name:
        raise ValueError("Company name is required.")
    if public_email and not is_valid_email_address(public_email):
        raise ValueError("Enter a contact email like name@company.com.")
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


def render_company_profile(access: CompanyAccess) -> None:
    from state.company_auth import company_join_url

    apply_company_profile_css()
    st.markdown('<div class="company-profile-active" style="display:none"></div>', unsafe_allow_html=True)
    st.title("Company Profile")
    st.caption("Company details and people in one place. Only the owner can make changes.")
    try:
        profile = load_company_profile(access)
    except Exception:
        st.error("Company Profile is unavailable right now. Try again in a moment.")
        return

    st.subheader("Company details")
    if access.role == "owner":
        with st.form("company_contact_details"):
            name = st.text_input("Company name", value=str(profile.get("company_name") or ""))
            email = st.text_input(
                "Contact email", value=str(profile.get("public_email") or access.email),
                placeholder="you@company.com",
            )
            phone = st.text_input("Phone", value=str(profile.get("public_phone") or ""), placeholder="+1 555 000 0000")
            saved = st.form_submit_button("Save company details", type="primary")
        if saved:
            try:
                save_company_contacts(access, name, email, phone)
                st.success("Company details saved.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except PermissionError:
                st.error("Only the company owner can save these details.")
            except Exception:
                st.error("Company details were not saved. Try again in a moment.")
    else:
        st.write(f"**Company name:** {profile.get('company_name') or 'Not set'}")
        st.write(f"**Contact email:** {profile.get('public_email') or 'Not set'}")
        st.write(f"**Phone:** {profile.get('public_phone') or 'Not set'}")
    st.caption("Logo and billing details for proposal PDFs will be added here next.")

    st.divider()
    st.subheader("Company metrics")
    st.info("Rent, payroll, utilities, equipment and other cost drivers will be configured here. No default costs have been assumed.")

    st.divider()
    st.subheader("Users")
    try:
        members = load_company_members(access)
        rows = "".join(
            f"<tr><td>{escape(member['Email'])}</td><td>{escape(member['Role'])}</td></tr>"
            for member in members
        )
        st.markdown(
            '<div class="company-profile-users"><table>'
            '<thead><tr><th>Email</th><th>Role</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.error("Company users are unavailable right now.")
    if access.role == "owner":
        st.caption("Share this reusable link to let teammates register under this company.")
        try:
            st.code(company_join_url(access), language=None)
        except Exception:
            st.error("The company link is unavailable right now.")

    st.divider()
    st.subheader("Price lists")
    st.info("Company price-list uploads and the shared fallback library will appear here in the next step.")

    if st.button("Continue to Upload", type="primary", key="profile_to_upload"):
        st.session_state.screen = "upload"
        st.rerun()
