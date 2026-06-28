from __future__ import annotations


_RFQ_FILE_CACHE: dict[str, tuple[str, bytes]] = {}


def remember_rfq_file(*, run_id: str, file_name: str, file_bytes: bytes) -> None:
    """Keep uploaded bytes available across Streamlit browser navigations."""
    _RFQ_FILE_CACHE[run_id] = (file_name, file_bytes)


def get_rfq_file(run_id: str) -> tuple[str, bytes] | None:
    return _RFQ_FILE_CACHE.get(run_id)


def clear_uploaded_files() -> None:
    _RFQ_FILE_CACHE.clear()
