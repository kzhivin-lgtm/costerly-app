"""Private immutable evidence artifact storage."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from typing import Any

from PIL import Image

from use_cases.estimation_evidence import EvidenceArtifact


EVIDENCE_BUCKET = "rfq-estimation-evidence"


def evidence_signed_url(*, client: Any, storage_ref: str, company_id: str) -> str | None:
    """Return a short-lived URL only for evidence owned by this company."""
    prefix = f"storage://{EVIDENCE_BUCKET}/"
    if not storage_ref.startswith(prefix):
        return None
    object_path = storage_ref.removeprefix(prefix)
    if not company_id or not object_path.startswith(f"{company_id}/"):
        return None
    try:
        response = client.storage.from_(EVIDENCE_BUCKET).create_signed_url(object_path, 3600)
    except Exception:
        return None
    if isinstance(response, dict):
        return response.get("signedURL") or response.get("signed_url")
    return getattr(response, "signedURL", None) or getattr(response, "signed_url", None)


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


def persist_page_artifact(*, client: Any, company_id: str, run_id: str, object_id: str, page_number: int, page_bytes: bytes) -> EvidenceArtifact:
    """Persist one full, object-relevant drawing page as private evidence."""
    if not all((company_id, run_id, object_id, page_number > 0, page_bytes)):
        raise ValueError("page evidence identity and bytes are required")
    image = Image.open(BytesIO(page_bytes)).convert("RGB")
    output = BytesIO()
    image.save(output, "WEBP", quality=88, method=6)
    payload = output.getvalue()
    digest = sha256(payload).hexdigest()
    path = f"{company_id}/{run_id}/{object_id}/page-{page_number}-{digest}.webp"
    client.storage.from_(EVIDENCE_BUCKET).upload(
        path, payload, file_options={"content-type": "image/webp", "upsert": "true"}
    )
    return EvidenceArtifact(
        storage_ref=f"storage://{EVIDENCE_BUCKET}/{path}",
        page_number=page_number,
        artifact_kind="page",
    )
