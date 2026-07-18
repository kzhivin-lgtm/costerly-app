from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from agents.ocr_adapter import (
    OCR_CONTRACT_VERSION,
    build_ocr_evidence,
    run_mistral_ocr,
)
from agents.ocr_contract import OCR_PROFILE_EVIDENCE


DEFAULT_RENDER_DPI = 200
DEFAULT_PAGE_WORKERS = 4


def _render_with_pymupdf(file_bytes: bytes, dpi: int) -> list[bytes]:
    import fitz  # PyMuPDF

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        return [
            page.get_pixmap(dpi=dpi, alpha=False).tobytes("png")
            for page in document
        ]
    finally:
        document.close()


def _render_with_pdftoppm(file_bytes: bytes, dpi: int) -> list[bytes]:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("PDF rendering requires PyMuPDF or pdftoppm")
    with tempfile.TemporaryDirectory(prefix="costerly-ocr-") as directory:
        temp_dir = Path(directory)
        source_path = temp_dir / "source.pdf"
        output_prefix = temp_dir / "page"
        source_path.write_bytes(file_bytes)
        subprocess.run(
            [
                executable,
                "-r",
                str(dpi),
                "-png",
                str(source_path),
                str(output_prefix),
            ],
            check=True,
            capture_output=True,
        )
        return [path.read_bytes() for path in sorted(temp_dir.glob("page-*.png"))]


def render_pdf_pages(file_bytes: bytes, *, dpi: int = DEFAULT_RENDER_DPI) -> list[bytes]:
    """Render PDF pages for OCR; PyMuPDF is production, pdftoppm is local fallback."""
    try:
        pages = _render_with_pymupdf(file_bytes, dpi)
    except (ImportError, ModuleNotFoundError):
        pages = _render_with_pdftoppm(file_bytes, dpi)
    if not pages:
        raise RuntimeError("PDF contains no renderable pages")
    return pages


def run_mistral_document_evidence_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
    dpi: int = DEFAULT_RENDER_DPI,
    page_workers: int = DEFAULT_PAGE_WORKERS,
    renderer: Callable[..., list[bytes]] = render_pdf_pages,
    page_ocr: Callable[..., dict[str, Any]] = run_mistral_ocr,
) -> dict[str, Any]:
    """Render a PDF at useful resolution and OCR its pages concurrently."""
    if Path(file_name).suffix.lower() != ".pdf":
        return page_ocr(
            file_name=file_name,
            file_bytes=file_bytes,
            profile=OCR_PROFILE_EVIDENCE,
        )

    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    rendered_pages = renderer(file_bytes, dpi=dpi)

    def recognize(item: tuple[int, bytes]) -> tuple[int, dict[str, Any]]:
        page_index, page_bytes = item
        package = page_ocr(
            file_name=f"{Path(file_name).stem}-page-{page_index + 1}.png",
            file_bytes=page_bytes,
            profile=OCR_PROFILE_EVIDENCE,
        )
        return page_index, package

    worker_count = max(1, min(page_workers, len(rendered_pages)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        recognized = list(executor.map(recognize, enumerate(rendered_pages)))
    recognized.sort(key=lambda item: item[0])

    pages: list[dict[str, Any]] = []
    raw_page_responses: list[dict[str, Any]] = []
    model = "unknown"
    for page_index, package in recognized:
        model = str(package.get("model") or model)
        raw_page_responses.append(package.get("raw_response") or {})
        for page in package.get("pages") or []:
            normalized_page = dict(page)
            normalized_page["page_number"] = page_index + 1
            normalized_page["source_page_index"] = page_index
            pages.append(normalized_page)

    finished_at = datetime.now(UTC).isoformat()
    result = {
        "contract_version": OCR_CONTRACT_VERSION,
        "provider": "mistral",
        "model": model,
        "profile": OCR_PROFILE_EVIDENCE,
        "file_name": file_name,
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "mime_type": "application/pdf",
        "page_count": len(pages),
        "processing_seconds": round(time.perf_counter() - started, 3),
        "started_at": started_at,
        "finished_at": finished_at,
        "rendering": {
            "dpi": dpi,
            "rendered_page_count": len(rendered_pages),
            "rendered_bytes_total": sum(len(page) for page in rendered_pages),
            "parallel_workers": worker_count,
        },
        "pages": pages,
        "usage": {
            "pages_processed": len(pages),
            "source_doc_size_bytes": len(file_bytes),
        },
        "raw_response": {
            "rendered_page_responses": raw_page_responses,
        },
    }
    result["evidence"] = build_ocr_evidence(pages)
    return result
