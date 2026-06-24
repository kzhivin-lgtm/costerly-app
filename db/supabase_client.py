import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client, Client


def _get_secret(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        return str(st.secrets.get(name, ""))
    except StreamlitSecretNotFoundError:
        return ""


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and Supabase API key in Streamlit secrets."
        )

    return create_client(url, key)
