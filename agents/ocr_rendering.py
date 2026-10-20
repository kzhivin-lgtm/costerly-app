from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from agents.ocr_adapter import (
    OCR_CONTRACT_VERSION,
    build_ocr_evidence,
    run_mistral_ocr,
    wait_for_mistral_http_warmup,
    warm_mistral_http_client_async,
)
from agents.ocr_contract import OCR_PROFILE_BASIC, OCR_PROFILE_EVIDENCE


DEFAULT_RENDER_DPI = 200
DEFAULT_RENDER_WORKERS = 4
DEFAULT_PAGE_WORKERS = 4


def extract_native_pdf_text_blocks(
    file_bytes: bytes,
    *,
    dpi: int = DEFAULT_RENDER_DPI,
) -> list[dict[str, Any]]:
    """Extract PDF text spans in the same pixel coordinates as rendered pages.

    This is not OCR and makes no semantic claim about a drawing.  It preserves
    authored text that exists in the PDF text layer, including rotated labels,
    so Mistral remains a fallback source for scans and raster-only text.
    """
    try:
        import fitz  # PyMuPDF
    except (ImportError, ModuleNotFoundError):
        return []

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        blocks: list[dict[str, Any]] = []
        for page_index, page in enumerate(document):
            # Text coordinates are reported in the unrotated PDF coordinate
            # system.  The Detection image uses the rotated rendered page.
            # Apply the page rotation first, then map points to its pixel grid.
            # Rendering a second pixel image solely to obtain its dimensions
            # would duplicate the active OCR pipeline's work. PDF points map
            # to rendered pixels at exactly dpi / 72; rounding happens only at
            # the final evidence boundary.
            scale_x = dpi / 72
            scale_y = dpi / 72
            page_dict = page.get_text("dict")
            for source_block in page_dict.get("blocks") or []:
                for line in source_block.get("lines") or []:
                    for span in line.get("spans") or []:
                        text = str(span.get("text") or "").strip()
                        if not text:
                            continue
                        source_bbox = span.get("bbox")
                        if not isinstance(source_bbox, (list, tuple)) or len(source_bbox) != 4:
                            continue
                        rendered_bbox = fitz.Rect(source_bbox) * page.rotation_matrix
                        blocks.append(
                            {
                                "page_number": page_index + 1,
                                "text": text,
                                "bbox": {
                                    "top_left_x": round(rendered_bbox.x0 * scale_x),
                                    "top_left_y": round(rendered_bbox.y0 * scale_y),
                                    "bottom_right_x": round(rendered_bbox.x1 * scale_x),
                                    "bottom_right_y": round(rendered_bbox.y1 * scale_y),
                                },
                            }
                        )
        return blocks
    finally:
        document.close()


def direct_pdf_ocr_enabled() -> bool:
    """Enable one-PDF/one-request OCR only for an explicit experiment."""
    if "--ocr-direct-pdf" in sys.argv:
        return True
    value = os.getenv("MISTRAL_DIRECT_PDF_EXPERIMENT", "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def run_mistral_direct_pdf_evidence_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
    document_ocr: Callable[..., dict[str, Any]] = run_mistral_ocr,
) -> dict[str, Any]:
    """Send the original document through Mistral's core OCR in one request."""
    package = document_ocr(
        file_name=file_name,
        file_bytes=file_bytes,
        profile=OCR_PROFILE_BASIC,
    )
    result = dict(package)
    provider_seconds = float(result.get("processing_seconds") or 0.0)
    result["transport"] = {
        "mode": "direct_pdf",
        "request_count": 1,
        "source_bytes": len(file_bytes),
    }
    result["rendering"] = {
        "dpi": None,
        "rendered_page_count": 0,
        "rendered_bytes_total": 0,
        "parallel_workers": 0,
        "render_workers": 0,
        "pipeline_enabled": False,
    }
    result["timings"] = {
        "render_seconds": 0.0,
        "warmup_wait_seconds": 0.0,
        "provider_wall_seconds": round(provider_seconds, 3),
        "pipeline_seconds": round(provider_seconds, 3),
        "pipeline_overlap_seconds": 0.0,
        "assembly_seconds": 0.0,
        "unattributed_seconds": 0.0,
    }
    return result


def _render_with_pymupdf(
    file_bytes: bytes,
    dpi: int,
    *,
    render_workers: int = DEFAULT_RENDER_WORKERS,
) -> list[bytes]:
    import fitz  # PyMuPDF

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        page_count = len(document)
    finally:
        document.close()

    def render_page(page_index: int) -> bytes:
        # PyMuPDF documents are not thread-safe, so every worker owns its
        # document handle while pages are rendered concurrently.
        worker_document = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            page = worker_document.load_page(page_index)
            return page.get_pixmap(dpi=dpi, alpha=False).tobytes("png")
        finally:
            worker_document.close()

    worker_count = max(1, min(render_workers, page_count))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(render_page, range(page_count)))


def _render_with_pdftoppm(
    file_bytes: bytes,
    dpi: int,
    *,
    render_workers: int = DEFAULT_RENDER_WORKERS,
) -> list[bytes]:
    executable = shutil.which("pdftoppm")
    pdfinfo = shutil.which("pdfinfo")
    if not executable or not pdfinfo:
        raise RuntimeError("PDF rendering requires PyMuPDF or pdftoppm")
    with tempfile.TemporaryDirectory(prefix="costerly-ocr-") as directory:
        temp_dir = Path(directory)
        source_path = temp_dir / "source.pdf"
        source_path.write_bytes(file_bytes)

        info = subprocess.run(
            [
                pdfinfo,
                str(source_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        page_count = 0
        for line in info.stdout.splitlines():
            if line.startswith("Pages:"):
                page_count = int(line.split(":", 1)[1].strip())
                break
        if page_count < 1:
            raise RuntimeError("Unable to determine PDF page count")

        def render_page(page_number: int) -> bytes:
            output_prefix = temp_dir / f"page-{page_number:06d}"
            subprocess.run(
                [
                    executable,
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-singlefile",
                    "-r",
                    str(dpi),
                    "-png",
                    str(source_path),
                    str(output_prefix),
                ],
                check=True,
                capture_output=True,
            )
            return output_prefix.with_suffix(".png").read_bytes()

        worker_count = max(1, min(render_workers, page_count))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            return list(executor.map(render_page, range(1, page_count + 1)))


def _iter_rendered_with_pdftoppm(
    file_bytes: bytes,
    dpi: int,
    *,
    render_workers: int = DEFAULT_RENDER_WORKERS,
):
    """Yield pdftoppm pages immediately instead of waiting for the full list."""
    executable = shutil.which("pdftoppm")
    pdfinfo = shutil.which("pdfinfo")
    if not executable or not pdfinfo:
        raise RuntimeError("PDF rendering requires PyMuPDF or pdftoppm")
    with tempfile.TemporaryDirectory(prefix="costerly-ocr-") as directory:
        temp_dir = Path(directory)
        source_path = temp_dir / "source.pdf"
        source_path.write_bytes(file_bytes)
        info = subprocess.run(
            [pdfinfo, str(source_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        page_count = 0
        for line in info.stdout.splitlines():
            if line.startswith("Pages:"):
                page_count = int(line.split(":", 1)[1].strip())
                break
        if page_count < 1:
            raise RuntimeError("Unable to determine PDF page count")

        def render_page(page_number: int) -> tuple[int, bytes]:
            output_prefix = temp_dir / f"page-{page_number:06d}"
            subprocess.run(
                [
                    executable,
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-singlefile",
                    "-r",
                    str(dpi),
                    "-png",
                    str(source_path),
                    str(output_prefix),
                ],
                check=True,
                capture_output=True,
            )
            return page_number - 1, output_prefix.with_suffix(".png").read_bytes()

        worker_count = max(1, min(render_workers, page_count))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(render_page, page_number)
                for page_number in range(1, page_count + 1)
            ]
            for future in as_completed(futures):
                yield future.result()


def render_pdf_pages(
    file_bytes: bytes,
    *,
    dpi: int = DEFAULT_RENDER_DPI,
    render_workers: int = DEFAULT_RENDER_WORKERS,
) -> list[bytes]:
    """Render PDF pages for OCR; PyMuPDF is production, pdftoppm is local fallback."""
    try:
        pages = _render_with_pymupdf(
            file_bytes,
            dpi,
            render_workers=render_workers,
        )
    except (ImportError, ModuleNotFoundError):
        pages = _render_with_pdftoppm(
            file_bytes,
            dpi,
            render_workers=render_workers,
        )
    if not pages:
        raise RuntimeError("PDF contains no renderable pages")
    return pages


def iter_rendered_pdf_pages(
    file_bytes: bytes,
    *,
    dpi: int = DEFAULT_RENDER_DPI,
    render_workers: int = DEFAULT_RENDER_WORKERS,
):
    """Yield rendered pages as soon as each concurrent render completes."""
    try:
        import fitz  # PyMuPDF
    except (ImportError, ModuleNotFoundError):
        yield from _iter_rendered_with_pdftoppm(
            file_bytes,
            dpi,
            render_workers=render_workers,
        )
        return

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        page_count = len(document)
    finally:
        document.close()
    if page_count < 1:
        raise RuntimeError("PDF contains no renderable pages")

    def render_page(page_index: int) -> tuple[int, bytes]:
        worker_document = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            page = worker_document.load_page(page_index)
            return page_index, page.get_pixmap(dpi=dpi, alpha=False).tobytes("png")
        finally:
            worker_document.close()

    worker_count = max(1, min(render_workers, page_count))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(render_page, index) for index in range(page_count)]
        for future in as_completed(futures):
            yield future.result()


def run_mistral_document_evidence_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
    dpi: int = DEFAULT_RENDER_DPI,
    page_workers: int = DEFAULT_PAGE_WORKERS,
    render_workers: int = DEFAULT_RENDER_WORKERS,
    renderer: Callable[..., list[bytes]] = render_pdf_pages,
    page_streamer: Callable[..., Any] | None = None,
    page_ocr: Callable[..., dict[str, Any]] = run_mistral_ocr,
    native_text_extractor: Callable[..., list[dict[str, Any]]] = extract_native_pdf_text_blocks,
) -> dict[str, Any]:
    """Render and OCR PDF pages concurrently with an overlapping pipeline."""
    if Path(file_name).suffix.lower() != ".pdf":
        return page_ocr(
            file_name=file_name,
            file_bytes=file_bytes,
            profile=OCR_PROFILE_EVIDENCE,
        )

    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    # Native text extraction is CPU-local and runs alongside the provider OCR.
    # Failure is observable but never prevents a scanned PDF from proceeding.
    def extract_native_text() -> tuple[list[dict[str, Any]], float]:
        extraction_started = time.perf_counter()
        blocks = native_text_extractor(file_bytes, dpi=dpi)
        return blocks, time.perf_counter() - extraction_started

    native_executor = ThreadPoolExecutor(max_workers=1)
    native_text_future = native_executor.submit(extract_native_text)
    warm_mistral_http_client_async()
    render_started = time.perf_counter()

    def recognize(item: tuple[int, bytes]) -> tuple[int, dict[str, Any]]:
        page_index, page_bytes = item
        package = page_ocr(
            file_name=f"{Path(file_name).stem}-page-{page_index + 1}.png",
            file_bytes=page_bytes,
            profile=OCR_PROFILE_EVIDENCE,
        )
        return page_index, package

    use_pipeline = page_streamer is not None or renderer is render_pdf_pages
    rendered_page_sizes: dict[int, int] = {}
    warmup_wait_seconds = 0.0
    provider_started: float | None = None
    if use_pipeline:
        stream = (page_streamer or iter_rendered_pdf_pages)(
            file_bytes,
            dpi=dpi,
            render_workers=render_workers,
        )
        recognized = []
        with ThreadPoolExecutor(max_workers=max(1, page_workers)) as executor:
            ocr_futures = []
            for page_index, page_bytes in stream:
                if provider_started is None:
                    warmup_wait_started = time.perf_counter()
                    wait_for_mistral_http_warmup()
                    warmup_wait_seconds = time.perf_counter() - warmup_wait_started
                    provider_started = time.perf_counter()
                rendered_page_sizes[page_index] = len(page_bytes)
                ocr_futures.append(executor.submit(recognize, (page_index, page_bytes)))
            render_seconds = time.perf_counter() - render_started
            for future in as_completed(ocr_futures):
                recognized.append(future.result())
        if not rendered_page_sizes:
            raise RuntimeError("PDF contains no renderable pages")
    else:
        rendered_pages = renderer(file_bytes, dpi=dpi)
        render_seconds = time.perf_counter() - render_started
        warmup_wait_started = time.perf_counter()
        wait_for_mistral_http_warmup()
        warmup_wait_seconds = time.perf_counter() - warmup_wait_started
        provider_started = time.perf_counter()
        worker_count = max(1, min(page_workers, len(rendered_pages)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            recognized = list(executor.map(recognize, enumerate(rendered_pages)))
        rendered_page_sizes = {
            page_index: len(page_bytes)
            for page_index, page_bytes in enumerate(rendered_pages)
        }
    provider_wall_seconds = (
        time.perf_counter() - provider_started if provider_started is not None else 0.0
    )
    pipeline_seconds = time.perf_counter() - render_started
    pipeline_overlap_seconds = max(
        0.0,
        render_seconds + warmup_wait_seconds + provider_wall_seconds - pipeline_seconds,
    )
    recognized.sort(key=lambda item: item[0])

    assembly_started = time.perf_counter()
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
    assembly_seconds = time.perf_counter() - assembly_started

    native_text_error: str | None = None
    native_text_seconds = 0.0
    try:
        native_text_blocks, native_text_seconds = native_text_future.result()
    except Exception as exc:
        native_text_blocks = []
        native_text_error = str(exc)
    finally:
        native_executor.shutdown(wait=True)

    finished_at = datetime.now(UTC).isoformat()
    total_seconds = time.perf_counter() - started
    result = {
        "contract_version": OCR_CONTRACT_VERSION,
        "provider": "mistral",
        "model": model,
        "profile": OCR_PROFILE_EVIDENCE,
        "file_name": file_name,
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "mime_type": "application/pdf",
        "page_count": len(pages),
        "processing_seconds": round(total_seconds, 3),
        "started_at": started_at,
        "finished_at": finished_at,
        "rendering": {
            "dpi": dpi,
            "rendered_page_count": len(rendered_page_sizes),
            "rendered_bytes_total": sum(rendered_page_sizes.values()),
            "parallel_workers": min(page_workers, len(rendered_page_sizes)),
            "render_workers": min(render_workers, len(rendered_page_sizes)),
            "pipeline_enabled": use_pipeline,
        },
        "transport": {
            "mode": "rendered_pages",
            "request_count": len(rendered_page_sizes),
            "source_bytes": len(file_bytes),
        },
        "timings": {
            "render_seconds": round(render_seconds, 3),
            "warmup_wait_seconds": round(warmup_wait_seconds, 3),
            "provider_wall_seconds": round(provider_wall_seconds, 3),
            "pipeline_seconds": round(pipeline_seconds, 3),
            "pipeline_overlap_seconds": round(pipeline_overlap_seconds, 3),
            "assembly_seconds": round(assembly_seconds, 3),
            "unattributed_seconds": round(
                max(
                    0.0,
                    total_seconds
                    - pipeline_seconds
                    - assembly_seconds,
                ),
                3,
            ),
        },
        "pages": pages,
        "usage": {
            "pages_processed": len(pages),
            "source_doc_size_bytes": len(file_bytes),
        },
        "native_pdf_text": {
            "status": "failed" if native_text_error else "succeeded",
            "span_count": len(native_text_blocks),
            "extraction_seconds": round(native_text_seconds, 3),
            "error": native_text_error,
        },
        "raw_response": {
            "rendered_page_responses": raw_page_responses,
        },
    }
    result["evidence"] = build_ocr_evidence(
        pages,
        native_text_blocks=native_text_blocks,
    )
    return result
