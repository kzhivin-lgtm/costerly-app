import os

import httpx
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions


_SUPABASE_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_PRICE_SOURCE_SUPABASE_TIMEOUT = httpx.Timeout(20.0, connect=8.0)
_SUPABASE_LIMITS = httpx.Limits(
    max_connections=50,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)


def _create_http_client(timeout: httpx.Timeout = _SUPABASE_TIMEOUT) -> httpx.Client:
    """Use HTTP/1.1 for the shared synchronous Supabase client.

    Streamlit reruns and the background Estimation worker share this cached
    client. Disabling HTTP/2 avoids poisoning later UI reads when one multiplexed
    stream fails under concurrent database traffic.
    """
    return httpx.Client(
        http2=False,
        timeout=timeout,
        limits=_SUPABASE_LIMITS,
    )


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
    return _create_supabase_client(_SUPABASE_TIMEOUT)


def _create_supabase_client(timeout: httpx.Timeout) -> Client:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and Supabase API key in Streamlit secrets."
        )

    return create_client(
        url,
        key,
        options=SyncClientOptions(
            postgrest_client_timeout=timeout,
            httpx_client=_create_http_client(timeout),
        ),
    )


def create_price_source_supabase_client() -> Client:
    """Return an isolated short-timeout client for one extraction worker.

    A stalled worker must never hold the shared Streamlit Supabase pool and
    make later Price Source clicks appear to run forever before any source is
    created. This client is intentionally not cached.
    """
    return _create_supabase_client(_PRICE_SOURCE_SUPABASE_TIMEOUT)
