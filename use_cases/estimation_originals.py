"""Private immutable storage for RFQ originals used by Estimation v2."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import mimetypes
from pathlib import Path
from typing import Any


ORIGINALS_BUCKET = "rfq-estimation-originals"


@dataclass(frozen=True)
class StoredOriginal:
    storage_ref: str
    content_sha256: str
    mime_type: str
    size_bytes: int


def describe_estimation_original(*, company_id: str, file_name: str, file_bytes: bytes) -> StoredOriginal:
    if not company_id or not file_bytes:
        raise ValueError("company_id and file_bytes are required")
    digest = sha256(file_bytes).hexdigest()
    suffix = Path(file_name).suffix.lower() or ".bin"
    mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    object_path = f"{company_id}/{digest}{suffix}"
    return StoredOriginal(
        storage_ref=f"storage://{ORIGINALS_BUCKET}/{object_path}",
        content_sha256=digest,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
    )


def persist_estimation_original(
    *,
    client: Any,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
) -> StoredOriginal:
    """Upload once under a deterministic content path. Caller owns run persistence."""
    if not company_id or not file_bytes:
        raise ValueError("company_id and file_bytes are required")
    stored = describe_estimation_original(
        company_id=company_id, file_name=file_name, file_bytes=file_bytes
    )
    object_path = stored.storage_ref.removeprefix(f"storage://{ORIGINALS_BUCKET}/")
    client.storage.from_(ORIGINALS_BUCKET).upload(
        object_path,
        file_bytes,
        file_options={"content-type": stored.mime_type, "upsert": "false"},
    )
    return stored
