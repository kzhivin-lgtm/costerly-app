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
        f'<img src="{_brand_logo_src()}" alt="Costerly" />'
        '</header>',
        unsafe_allow_html=True,
    )


def render_account_header_controls(*, on_sign_out) -> str | None:
    """Render authenticated actions and return a non-callback navigation action."""
    with st.container(key="costerly_header_controls"):
        left, right = st.columns(2)
        with left:
            if st.button("Profile", key="open_company_account", use_container_width=True):
                return "profile"
        with right:
            st.button(
                "Sign out",
                key="company_sign_out",
                use_container_width=True,
                on_click=on_sign_out,
            )
    return None
