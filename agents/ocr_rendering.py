from __future__ import annotations

import hashlib
from io import BytesIO
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

from PIL import Image

from agents.ocr_adapter import (
    OCR_CONTRACT_VERSION,
    build_page_title_fields,
    build_ocr_evidence,
    run_mistral_ocr,
    wait_for_mistral_http_warmup,
    warm_mistral_http_client_async,
)
from agents.ocr_contract import OCR_PROFILE_BASIC, OCR_PROFILE_EVIDENCE
from agents.detection_visual_embedding import (
    maybe_preload_detection_native_xobject_encoder,
)
from agents.pdf_page_inspection import (
    PDF_PAGE_INSPECTION_CONTRACT_VERSION,
    inspect_native_pdf_pages_isolated,
    measure_rendered_page_visual_coverage,
    start_native_pdf_pages_isolated,
)


DEFAULT_RENDER_DPI = 200
DEFAULT_RENDER_WORKERS = 4
DEFAULT_PAGE_WORKERS = 4


def _title_block_search_image(page_bytes: bytes) -> bytes:
    """Make one compact search image from the two title-block-prone page bands.

    This is a file-local fallback only after the ordinary OCR/Fusion path has
    already established repeated labelled title fields elsewhere in the file.
    It avoids a second full-page request while covering the conventional left
    vertical and lower horizontal title-block layouts.
    """
    with Image.open(BytesIO(page_bytes)) as source:
        image = source.convert("RGB")
    width, height = image.size
    left = image.crop((0, 0, max(1, round(width * 0.23)), height))
    lower = image.crop((0, round(height * 0.72), width, height))
    canvas = Image.new("RGB", (max(left.width, lower.width), left.height + lower.height), "white")
    canvas.paste(left, (0, 0))
    canvas.paste(lower, (0, left.height))
    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _recover_missing_repeated_title_fields(
    *,
    pages: list[dict[str, Any]],
    title_fields: list[dict[str, Any]],
    rendered_pages_by_index: dict[int, bytes],
    file_name: str,
    page_ocr: Callable[..., dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """OCR bounded title bands only when the document proves a repeated form."""
    resolved_pages = {
        int(field["page_number"])
        for field in title_fields
        if isinstance(field, dict)
        and field.get("field_type") == "drawing_sheet_code"
        and field.get("status") in {"verified", "single_source"}
        and field.get("value")
    }
    page_numbers = {
        int(page.get("page_number"))
        for page in pages
        if isinstance(page, dict) and isinstance(page.get("page_number"), int)
    }
    missing_pages = sorted(page_numbers - resolved_pages)
    audit: dict[str, Any] = {
        "status": "not_needed",
        "eligible_page_count": len(resolved_pages),
        "requested_pages": [],
        "recovered_pages": [],
        "errors": [],
    }
    # One labelled hit may be a cover or one-off table. Require a repeated
    # document-level pattern before spending extra OCR or applying this layout
    # fallback to otherwise unresolved pages.
    if len(resolved_pages) < 2 or not missing_pages:
        return title_fields, audit
    audit["status"] = "attempted"
    fields = list(title_fields)
    for page_number in missing_pages:
        page_bytes = rendered_pages_by_index.get(page_number - 1)
        if not page_bytes:
            continue
        audit["requested_pages"].append(page_number)
        try:
            response = page_ocr(
                file_name=f"{Path(file_name).stem}-title-block-page-{page_number}.png",
                file_bytes=_title_block_search_image(page_bytes),
                profile=OCR_PROFILE_BASIC,
            )
            markdown = "\n".join(
                str(page.get("markdown") or "")
                for page in response.get("pages") or []
                if isinstance(page, dict)
            )
            recovered = build_page_title_fields(
                [{"page_number": page_number, "markdown": markdown}],
                {"text_blocks": [], "literal_items": []},
            )
            for field in recovered:
                if field.get("value"):
                    field["sources"] = ["mistral_title_block_fallback"]
                    field["status"] = "single_source"
                    fields.append(field)
                    audit["recovered_pages"].append(page_number)
        except Exception as exc:  # fallback must not block the primary OCR route
            audit["errors"].append({"page_number": page_number, "error": str(exc)})
    return fields, audit


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


def extract_native_pdf_graphic_regions(
    file_bytes: bytes,
    *,
    dpi: int = DEFAULT_RENDER_DPI,
) -> list[dict[str, Any]]:
    """Extract native PDF image placements without assigning object meaning.

    PDF image XObjects carry a source-authored placement rectangle.  They are
    graphic geometry, not OCR text and not detected objects.  Later Fusion and
    Registry stages may use them as bounded candidate regions when the PDF has
    a small number of independent placed drawings.
    """
    try:
        import fitz  # PyMuPDF
    except (ImportError, ModuleNotFoundError):
        return []

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        regions: list[dict[str, Any]] = []
        for page_index, page in enumerate(document):
            scale = dpi / 72
            rotated_page = page.rect * page.rotation_matrix
            seen_placements: set[tuple[int, float, float, float, float]] = set()
            for image_index, image in enumerate(page.get_images(full=True), start=1):
                xref = int(image[0])
                image_width = int(image[2])
                image_height = int(image[3])
                for placement_index, source_rect in enumerate(
                    page.get_image_rects(xref, transform=False), start=1,
                ):
                    rendered_rect = source_rect * page.rotation_matrix
                    if rendered_rect.width <= 0 or rendered_rect.height <= 0:
                        continue
                    placement_key = (
                        xref,
                        round(rendered_rect.x0, 6),
                        round(rendered_rect.y0, 6),
                        round(rendered_rect.x1, 6),
                        round(rendered_rect.y1, 6),
                    )
                    if placement_key in seen_placements:
                        continue
                    seen_placements.add(placement_key)
                    regions.append({
                        "graphic_id": (
                            f"NPIG-P{page_index + 1:03d}-"
                            f"X{xref}-I{image_index:03d}-R{placement_index:03d}"
                        ),
                        "page_number": page_index + 1,
                        "bbox": {
                            "top_left_x": round(rendered_rect.x0 * scale),
                            "top_left_y": round(rendered_rect.y0 * scale),
                            "bottom_right_x": round(rendered_rect.x1 * scale),
                            "bottom_right_y": round(rendered_rect.y1 * scale),
                        },
                        "source_bbox_points": {
                            "top_left_x": round(rendered_rect.x0, 6),
                            "top_left_y": round(rendered_rect.y0, 6),
                            "bottom_right_x": round(rendered_rect.x1, 6),
                            "bottom_right_y": round(rendered_rect.y1, 6),
                        },
                        "source_page_width_points": round(rotated_page.width, 6),
                        "source_page_height_points": round(rotated_page.height, 6),
                        "image_width": image_width,
                        "image_height": image_height,
                    })
        return regions
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
    native_inspection = inspect_native_pdf_pages_isolated(
        file_bytes, dpi=DEFAULT_RENDER_DPI,
    )
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
    result["native_pdf_inspection"] = {
        "status": native_inspection.get("sources", {}).get("status", "failed"),
        "profile_count": len(native_inspection.get("page_profiles") or []),
        "extraction_seconds": native_inspection.get("sources", {}).get("extraction_seconds"),
        "error": native_inspection.get("sources", {}).get("error"),
    }
    result["evidence"] = build_ocr_evidence(
        result.get("pages") or [],
        native_text_blocks=native_inspection.get("text_blocks") or [],
        native_graphic_regions=native_inspection.get("graphic_regions") or [],
        page_profiles=native_inspection.get("page_profiles") or [],
    )
    result["page_title_fields"] = build_page_title_fields(
        result.get("pages") or [], result["evidence"],
    )
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
    native_text_extractor: Callable[..., list[dict[str, Any]]] | None = None,
    native_graphic_extractor: Callable[..., list[dict[str, Any]]] | None = None,
    native_page_inspector: Callable[..., dict[str, Any]] = inspect_native_pdf_pages_isolated,
    native_embedding_preloader: Callable[[list[dict[str, Any]]], dict[str, Any]] = (
        maybe_preload_detection_native_xobject_encoder
    ),
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
    # Production uses one PyMuPDF document traversal for text, image
    # placements, Form XObjects and compact vector profiles. Tests and
    # experiments may still inject the older individual extractors.
    use_legacy_native_extractors = (
        native_text_extractor is not None or native_graphic_extractor is not None
    )
    preflight_native_inspection: dict[str, Any] | None = None
    native_inspection_future = None
    native_inspection_executor = None
    preflight_native_embedding_preload: dict[str, Any] = {"status": "not_requested"}
    if not use_legacy_native_extractors:
        # Start the isolated traversal before the renderer creates threads.
        # The child can parse heavy vector content while the parent renders and
        # sends pages to OCR, so passive profiling stays off the critical path.
        try:
            if native_page_inspector is inspect_native_pdf_pages_isolated:
                inspection_job = start_native_pdf_pages_isolated(file_bytes, dpi=dpi)

                def collect_inspection_and_preload() -> tuple[dict[str, Any], dict[str, Any]]:
                    inspection = inspection_job.collect()
                    try:
                        preload = native_embedding_preloader(
                            list(inspection.get("graphic_regions") or [])
                        )
                    except Exception as exc:  # pragma: no cover - optional warm-up
                        preload = {"status": "failed", "reason": str(exc)}
                    return inspection, preload

                native_inspection_executor = ThreadPoolExecutor(max_workers=1)
                native_inspection_future = native_inspection_executor.submit(
                    collect_inspection_and_preload,
                )
            else:
                # An injected test or experimental inspector keeps its simple,
                # synchronous contract rather than requiring a process handle.
                inspection = native_page_inspector(file_bytes, dpi=dpi)
                preflight_native_embedding_preload = native_embedding_preloader(
                    list(inspection.get("graphic_regions") or [])
                )
                native_inspection_future = None
                preflight_native_inspection = inspection
        except Exception as exc:
            preflight_native_inspection = {
                "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
                "text_blocks": [], "graphic_regions": [], "page_profiles": [],
                "sources": {"status": "failed", "error": str(exc)},
            }
            preflight_native_embedding_preload = {
                "status": "failed", "reason": str(exc),
            }

    def extract_native_text() -> tuple[list[dict[str, Any]], float]:
        extraction_started = time.perf_counter()
        extractor = native_text_extractor or extract_native_pdf_text_blocks
        blocks = extractor(file_bytes, dpi=dpi)
        return blocks, time.perf_counter() - extraction_started

    def extract_native_graphics() -> tuple[list[dict[str, Any]], float, dict[str, Any]]:
        extraction_started = time.perf_counter()
        extractor = native_graphic_extractor or extract_native_pdf_graphic_regions
        regions = extractor(file_bytes, dpi=dpi)
        try:
            # This runs in the native-extraction worker while rendered-page OCR
            # is still in flight, hiding DINOv2's one-time CPU initialization.
            embedding_preload = native_embedding_preloader(regions)
        except Exception as exc:  # pragma: no cover - preload is strictly optional
            embedding_preload = {"status": "failed", "reason": str(exc)}
        return regions, time.perf_counter() - extraction_started, embedding_preload

    native_executor = (
        ThreadPoolExecutor(max_workers=2) if use_legacy_native_extractors else None
    )
    native_text_future = None
    native_graphic_future = None

    def start_native_extraction_after_render() -> None:
        """Avoid concurrent PyMuPDF render and vector-content traversals."""
        nonlocal native_text_future, native_graphic_future
        if native_text_future is not None:
            return
        if use_legacy_native_extractors:
            assert native_executor is not None
            native_text_future = native_executor.submit(extract_native_text)
            native_graphic_future = native_executor.submit(extract_native_graphics)
    warm_mistral_http_client_async()
    render_started = time.perf_counter()
    # A page render can be much larger than its final OCR request. Measure it
    # while that one buffer is already live, rather than decoding several full
    # page PNGs in a second concurrent pool. This keeps density analysis
    # bounded for large multi-page construction sets.
    rendered_page_measurements: dict[int, dict[str, Any]] = {}
    rendered_pages_by_index: dict[int, bytes] = {}

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
                rendered_pages_by_index[page_index] = page_bytes
                rendered_page_measurements[page_index + 1] = (
                    measure_rendered_page_visual_coverage(page_bytes)
                )
                ocr_futures.append(executor.submit(recognize, (page_index, page_bytes)))
            render_seconds = time.perf_counter() - render_started
            start_native_extraction_after_render()
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
        start_native_extraction_after_render()
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            recognized = list(executor.map(recognize, enumerate(rendered_pages)))
        rendered_page_sizes = {
            page_index: len(page_bytes)
            for page_index, page_bytes in enumerate(rendered_pages)
        }
        rendered_pages_by_index = {
            page_index: page_bytes
            for page_index, page_bytes in enumerate(rendered_pages)
        }
        rendered_page_measurements = {
            page_index + 1: measure_rendered_page_visual_coverage(page_bytes)
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
    native_graphic_error: str | None = None
    native_graphic_seconds = 0.0
    native_embedding_preload: dict[str, Any] = {"status": "not_requested"}
    native_inspection: dict[str, Any] = {
        "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
        "text_blocks": [], "graphic_regions": [], "page_profiles": [],
        "sources": {"status": "unavailable"},
    }
    try:
        start_native_extraction_after_render()
        if use_legacy_native_extractors:
            try:
                native_text_blocks, native_text_seconds = native_text_future.result()
            except Exception as exc:
                native_text_blocks = []
                native_text_error = str(exc)
            try:
                (
                    native_graphic_regions,
                    native_graphic_seconds,
                    native_embedding_preload,
                ) = native_graphic_future.result()
            except Exception as exc:
                native_graphic_regions = []
                native_graphic_error = str(exc)
        else:
            try:
                if native_inspection_future is not None:
                    native_inspection, native_embedding_preload = (
                        native_inspection_future.result()
                    )
                else:
                    native_inspection = dict(preflight_native_inspection or {})
                    native_embedding_preload = preflight_native_embedding_preload
            except Exception as exc:
                native_inspection = {
                    "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
                    "text_blocks": [], "graphic_regions": [], "page_profiles": [],
                    "sources": {"status": "failed", "error": str(exc)},
                }
            native_text_blocks = list(native_inspection.get("text_blocks") or [])
            native_graphic_regions = list(native_inspection.get("graphic_regions") or [])
            source_status = native_inspection.get("sources") or {}
            native_text_seconds = float(
                (source_status.get("timings_seconds") or {}).get("native_text") or 0.0
            )
            native_graphic_seconds = float(
                (source_status.get("timings_seconds") or {}).get("image_xobjects") or 0.0
            )
            source_error = source_status.get("error")
            if source_status.get("status") != "succeeded":
                native_text_error = str(source_error or "native page inspection failed")
                native_graphic_error = native_text_error
    finally:
        if native_executor is not None:
            native_executor.shutdown(wait=True)
        if native_inspection_executor is not None:
            native_inspection_executor.shutdown(wait=True)
    page_profiles = []
    for profile in native_inspection.get("page_profiles") or []:
        if not isinstance(profile, dict):
            continue
        profile_with_render = dict(profile)
        page_number = profile_with_render.get("page_number")
        profile_with_render["rendered_page"] = rendered_page_measurements.get(
            page_number, {"status": "unavailable"},
        )
        page_profiles.append(profile_with_render)

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
        "native_pdf_graphics": {
            "status": "failed" if native_graphic_error else "succeeded",
            "region_count": len(native_graphic_regions),
            "extraction_seconds": round(native_graphic_seconds, 3),
            "error": native_graphic_error,
            "embedding_preload": native_embedding_preload,
        },
        "native_pdf_inspection": {
            "status": (native_inspection.get("sources") or {}).get(
                "status", "unavailable",
            ),
            "profile_count": len(page_profiles),
            "extraction_seconds": (native_inspection.get("sources") or {}).get(
                "extraction_seconds",
            ),
            "error": (native_inspection.get("sources") or {}).get("error"),
            "timings_seconds": (native_inspection.get("sources") or {}).get(
                "timings_seconds", {},
            ),
        },
        "raw_response": {
            "rendered_page_responses": raw_page_responses,
        },
    }
    result["evidence"] = build_ocr_evidence(
        pages,
        native_text_blocks=native_text_blocks,
        native_graphic_regions=native_graphic_regions,
        page_profiles=page_profiles,
    )
    result["page_title_fields"] = build_page_title_fields(
        pages, result["evidence"],
    )
    result["page_title_fields"], title_fallback_audit = _recover_missing_repeated_title_fields(
        pages=pages,
        title_fields=result["page_title_fields"],
        rendered_pages_by_index=rendered_pages_by_index,
        file_name=file_name,
        page_ocr=page_ocr,
    )
    result["title_block_ocr_fallback"] = title_fallback_audit
    result["usage"]["title_block_fallback_pages_processed"] = len(
        title_fallback_audit["requested_pages"]
    )
    result["usage"]["pages_processed"] += len(title_fallback_audit["requested_pages"])
    return result
