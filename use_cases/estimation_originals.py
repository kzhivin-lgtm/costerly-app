"""Private immutable storage for RFQ originals used by Estimation."""

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


def stored_original_metadata(stored: StoredOriginal) -> dict[str, object]:
    """Return the durable, non-content identity needed to restore an original."""
    return {
        "storage_ref": stored.storage_ref,
        "content_sha256": stored.content_sha256,
        "mime_type": stored.mime_type,
        "size_bytes": stored.size_bytes,
    }


def stored_original_from_metadata(metadata: Any) -> StoredOriginal | None:
    """Validate a persisted original identity without accepting an arbitrary URL."""
    if not isinstance(metadata, dict):
        return None
    storage_ref = str(metadata.get("storage_ref") or "")
    content_sha256 = str(metadata.get("content_sha256") or "")
    mime_type = str(metadata.get("mime_type") or "")
    try:
        size_bytes = int(metadata.get("size_bytes") or 0)
    except (TypeError, ValueError):
        return None
    if (
        not storage_ref.startswith(f"storage://{ORIGINALS_BUCKET}/")
        or len(content_sha256) != 64
        or any(char not in "0123456789abcdef" for char in content_sha256.lower())
        or not mime_type
        or size_bytes <= 0
    ):
        return None
    return StoredOriginal(
        storage_ref=storage_ref,
        content_sha256=content_sha256,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )


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
    bucket = client.storage.from_(ORIGINALS_BUCKET)
    try:
        bucket.upload(
            object_path,
            file_bytes,
            file_options={"content-type": stored.mime_type, "upsert": "false"},
        )
    except Exception:
        # The deterministic content address may already be present when the
        # same RFQ is re-uploaded. Accept only an exact read-back match, never
        # an arbitrary conflicting Storage object.
        existing = bucket.download(object_path)
        if (
            not isinstance(existing, (bytes, bytearray))
            or len(existing) != stored.size_bytes
            or sha256(bytes(existing)).hexdigest() != stored.content_sha256
        ):
            raise
    return stored


def load_estimation_original(
    *, client: Any, company_id: str, stored: StoredOriginal,
) -> bytes:
    """Restore a company-owned original and verify its immutable identity."""
    prefix = f"storage://{ORIGINALS_BUCKET}/"
    if not company_id or not stored.storage_ref.startswith(prefix):
        raise PermissionError("RFQ source is not available to this company.")
    object_path = stored.storage_ref.removeprefix(prefix)
    if (
        not object_path.startswith(f"{company_id}/")
        or object_path.startswith("/")
        or ".." in object_path.split("/")
    ):
        raise PermissionError("RFQ source is not available to this company.")
    payload = client.storage.from_(ORIGINALS_BUCKET).download(object_path)
    if not isinstance(payload, (bytes, bytearray)):
        raise RuntimeError("Stored RFQ source returned no bytes.")
    source = bytes(payload)
    if len(source) != stored.size_bytes or sha256(source).hexdigest() != stored.content_sha256:
        raise RuntimeError("Stored RFQ source integrity check failed.")
    return source
