"""Private immutable evidence artifact storage."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from use_cases.estimation_evidence import EvidenceArtifact


EVIDENCE_BUCKET = "rfq-estimation-evidence"


def persist_preview_artifact(*, client: Any, company_id: str, run_id: str, object_id: str, page_number: int, webp_bytes: bytes) -> EvidenceArtifact:
    if not all((company_id, run_id, object_id, page_number > 0, webp_bytes)):
        raise ValueError("preview identity and bytes are required")
    digest = sha256(webp_bytes).hexdigest()
    path = f"{company_id}/{run_id}/{object_id}/{digest}.webp"
    client.storage.from_(EVIDENCE_BUCKET).upload(
        path, webp_bytes, file_options={"content-type": "image/webp", "upsert": "false"}
    )
    return EvidenceArtifact(
        storage_ref=f"storage://{EVIDENCE_BUCKET}/{path}",
        page_number=page_number,
        artifact_kind="preview",
    )
