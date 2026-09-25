from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st


@lru_cache(maxsize=1)
def _brand_logo_src() -> str:
    logo = Path("assets/brand/costelry_logo_full_cropped.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(logo).decode("ascii")


def render_app_header() -> None:
    """Render the stable brand region shared by auth and product screens."""
    st.markdown(
        '<header class="costerly-app-header">'
        f'<img src="{_brand_logo_src()}" alt="Costerly AI" />'
        '</header>',
        unsafe_allow_html=True,
    )


def render_account_header_controls(
    *,
    on_profile,
    on_sign_out,
    show_projects: bool = False,
) -> None:
    """Render authenticated actions with navigation applied before the next run."""
    with st.container(key="costerly_header_controls"):
        if show_projects:
            projects, profile, sign_out_control = st.columns(3)
            with projects:
                st.button(
                    "Projects",
                    key="open_projects_placeholder",
                    use_container_width=True,
                    disabled=True,
                    help="Project history is coming next.",
                )
        else:
            profile, sign_out_control = st.columns(2)
        with profile:
            st.button(
                "Profile",
                key="open_company_account",
                use_container_width=True,
                on_click=on_profile,
            )
        with sign_out_control:
            st.button(
                "Sign out",
                key="company_sign_out",
                use_container_width=True,
                on_click=on_sign_out,
            )
