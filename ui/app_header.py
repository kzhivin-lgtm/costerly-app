from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitDuplicateElementKey


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
    on_projects=None,
    show_admin: bool = False,
    show_projects: bool = False,
    show_new_estimate: bool = False,
    show_last_estimate: bool = False,
    show_profile: bool = True,
) -> None:
    """Render authenticated actions with navigation applied before the next run."""
    def render_actions(*, container_key: str, recovered: bool) -> None:
        """Render one isolated control rail.

        A Streamlit fragment may retain a keyed container while its parent
        screen is being replaced.  A second instance of the same key is an
        exception, not a valid reason to strand the entire target screen.
        Keep the ordinary rail stable, and use a visibly equivalent, uniquely
        keyed recovery rail only for that framework-level collision.
        """
        key_suffix = "_recovery" if recovered else ""
        with st.container(key=container_key):
            actions: list[tuple[str, str, object, bool, str | None]] = []
            if show_admin:
                actions.append(("Admin", "open_platform_admin", on_admin, False, None))
            if show_new_estimate:
                actions.append(("New Estimate", "header_new_estimate", on_new_estimate, False, None))
            if show_last_estimate:
                actions.append(("Last Estimate", "header_last_estimate", on_last_estimate, False, None))
            if show_projects:
                actions.append(("Projects", "open_projects", on_projects, False, None))
            if show_profile:
                actions.append(("Profile", "open_company_account", on_profile, False, None))
            actions.append(("Sign out", "company_sign_out", on_sign_out, False, None))
            columns = st.columns(len(actions))
            for column, (label, key, callback, disabled, help_text) in zip(columns, actions):
                with column:
                    st.button(
                        label,
                        key=f"{key}{key_suffix}",
                        use_container_width=True,
                        on_click=callback,
                        disabled=disabled,
                        help=help_text,
                    )

    try:
        render_actions(container_key="costerly_header_controls", recovered=False)
    except StreamlitDuplicateElementKey:
        # Preserve a usable destination screen if Streamlit reports a stale
        # keyed-container collision during a transition.  The replacement
        # uses distinct element keys, so it cannot repeat the same collision.
        render_actions(
            container_key="costerly_header_controls_recovery",
            recovered=True,
        )
