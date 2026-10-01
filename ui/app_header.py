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
    on_admin=None,
    on_new_estimate=None,
    on_last_estimate=None,
    show_admin: bool = False,
    show_projects: bool = False,
    show_new_estimate: bool = False,
    show_last_estimate: bool = False,
) -> None:
    """Render authenticated actions with navigation applied before the next run."""
    with st.container(key="costerly_header_controls"):
        actions: list[tuple[str, str, object, bool, str | None]] = []
        if show_admin:
            actions.append(("Admin", "open_platform_admin", on_admin, False, None))
        if show_projects:
            actions.append(("Projects", "open_projects_placeholder", None, True, "Project history is coming next."))
        if show_new_estimate:
            actions.append(("New Estimate", "header_new_estimate", on_new_estimate, False, None))
        if show_last_estimate:
            actions.append(("Last Estimate", "header_last_estimate", on_last_estimate, False, None))
        actions.extend(
            [
                ("Profile", "open_company_account", on_profile, False, None),
                ("Sign out", "company_sign_out", on_sign_out, False, None),
            ]
        )
        columns = st.columns(len(actions))
        for column, (label, key, callback, disabled, help_text) in zip(columns, actions):
            with column:
                st.button(
                    label,
                    key=key,
                    use_container_width=True,
                    on_click=callback,
                    disabled=disabled,
                    help=help_text,
                )
