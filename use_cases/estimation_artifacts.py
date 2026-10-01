"""Private immutable evidence artifact storage."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from use_cases.estimation_evidence import EvidenceArtifact


EVIDENCE_BUCKET = "rfq-estimation-evidence"


def download_evidence_artifact(*, client: Any, storage_ref: str) -> bytes:
    """Download one private evidence artifact from its immutable storage ref."""
    prefix = f"storage://{EVIDENCE_BUCKET}/"
    ref = str(storage_ref or "").strip()
    if not ref.startswith(prefix):
        raise ValueError("evidence storage_ref must use the private evidence bucket")
    object_path = ref[len(prefix):]
    if not object_path or object_path.startswith("/") or ".." in object_path.split("/"):
        raise ValueError("evidence storage_ref has an invalid object path")
    payload = client.storage.from_(EVIDENCE_BUCKET).download(object_path)
    if not isinstance(payload, (bytes, bytearray)) or not payload:
        raise RuntimeError("private evidence artifact download returned no bytes")
    return bytes(payload)


def persist_preview_artifact(*, client: Any, company_id: str, run_id: str, object_id: str, page_number: int, webp_bytes: bytes) -> EvidenceArtifact:
    if not all((company_id, run_id, object_id, page_number > 0, webp_bytes)):
        raise ValueError("preview identity and bytes are required")
    digest = sha256(webp_bytes).hexdigest()
    path = f"{company_id}/{run_id}/{object_id}/{digest}.webp"
    client.storage.from_(EVIDENCE_BUCKET).upload(
        # Content-addressed paths are immutable by definition. Upsert makes a
        # repeated File Review revision idempotent when the crop did not change.
        path, webp_bytes, file_options={"content-type": "image/webp", "upsert": "true"}
    )
    return EvidenceArtifact(
        storage_ref=f"storage://{EVIDENCE_BUCKET}/{path}",
        page_number=page_number,
        artifact_kind="preview",
    )
