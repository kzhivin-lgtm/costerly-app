"""Text-layer preparation for Price Sources before commercial extraction."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import fitz
from PIL import Image, ImageOps, UnidentifiedImageError

from agents.ocr_adapter import run_mistral_ocr
from agents.ocr_rendering import run_mistral_direct_pdf_evidence_ocr


OCR_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".heif"}
OCR_DOCUMENT_SUFFIXES = OCR_IMAGE_SUFFIXES | {".pdf"}
STRUCTURED_TABLE_SUFFIXES = {".xlsx", ".csv"}
PDF_EMBEDDED_TEXT_MIN_CHARS = 120


@dataclass(frozen=True)
class PriceSourceTextLayer:
    text: str
    strategy: str
    ocr_package: dict[str, Any] | None = None
    issuer_evidence_text: str = ""


def _register_heif_decoder() -> None:
    """Enable HEIC/HEIF where the optional Pillow plugin is installed."""
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except ImportError:
        return


def open_price_source_image(file_bytes: bytes) -> Image.Image:
    """Open an image source with orientation normalized."""
    _register_heif_decoder()
    source = Image.open(BytesIO(file_bytes))
    try:
        return ImageOps.exif_transpose(source).convert("RGB")
    finally:
        source.close()


def normalise_ocr_image(file_name: str, file_bytes: bytes) -> tuple[str, bytes]:
    """Convert HEIC/HEIF/TIFF to PNG, leaving ordinary JPEG/PNG bytes intact."""
    suffix = Path(file_name).suffix.lower()
    try:
        image = open_price_source_image(file_bytes)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The image could not be read for OCR.") from exc
    try:
        if suffix in {".jpg", ".jpeg", ".png"}:
            return file_name, file_bytes
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return f"{Path(file_name).stem}.png", output.getvalue()
    finally:
        image.close()


def extract_embedded_pdf_text(file_bytes: bytes) -> str:
    """Read the native text layer from a digital PDF without OCR."""
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        return ""
    try:
        return "\n\n".join(page.get_text("text") for page in document).strip()[:180_000]
    finally:
        document.close()


def ocr_package_text(package: dict[str, Any]) -> str:
    """Flatten OCR text and extracted tables, retaining page boundaries.

    Mistral keeps a compact ``[tbl-0.html]`` reference in page Markdown and
    stores the actual invoice rows separately in ``tables[].content``.  The
    table content is source evidence, not decoration, and must reach Price
    extraction with the surrounding document text.
    """
    parts: list[str] = []
    for position, page in enumerate(package.get("pages") or [], start=1):
        markdown = str(page.get("markdown") or "").strip()
        tables = [
            str(table.get("content") or "").strip()
            for table in (page.get("tables") or [])
            if isinstance(table, dict) and str(table.get("content") or "").strip()
        ]
        if markdown or tables:
            page_text = "\n\n".join(part for part in (markdown, *tables) if part)
            parts.append(f"PAGE {page.get('page_number') or position}:\n{page_text}")
    return "\n\n".join(parts)[:180_000]


def ocr_issuer_evidence_text(package: dict[str, Any]) -> str:
    """Return seller-biased OCR blocks for local supplier resolution.

    OCR Markdown often omits page ``header`` and ``footer`` blocks even when
    the provider extracted them accurately.  Those blocks are the strongest
    invoice issuer evidence, while the body commonly contains the buyer after
    ``לכבוד``.  This evidence stays local and supplements, rather than
    replaces, the full extraction text sent to the commercial agent.
    """
    parts: list[str] = []
    for position, page in enumerate(package.get("pages") or [], start=1):
        page_number = page.get("page_number") or position
        headers = [
            str(block.get("content") or "").strip()
            for block in (page.get("blocks") or [])
            if isinstance(block, dict)
            and str(block.get("type") or "").lower() == "header"
            and str(block.get("content") or "").strip()
        ]
        footers = [
            str(block.get("content") or "").strip()
            for block in (page.get("blocks") or [])
            if isinstance(block, dict)
            and str(block.get("type") or "").lower() == "footer"
            and str(block.get("content") or "").strip()
        ]
        # Some provider revisions expose these aggregates but not typed blocks.
        if not headers and str(page.get("header") or "").strip():
            headers.append(str(page["header"]).strip())
        if not footers and str(page.get("footer") or "").strip():
            footers.append(str(page["footer"]).strip())
        if headers:
            parts.append(f"PAGE {page_number} OCR HEADER:\n" + "\n".join(headers))
        if footers:
            parts.append(f"PAGE {page_number} OCR FOOTER:\n" + "\n".join(footers))
        # Direct-PDF OCR can return page Markdown without promoting the
        # graphical masthead to a typed header block.  Preserve the first page
        # as issuer evidence in that case.  ``issuer_identity_from_source_text``
        # applies the hard ``לכבוד`` buyer boundary before it reads names or
        # identifiers, so this does not turn a buyer in the body into a seller.
        if position == 1 and not headers:
            markdown = str(page.get("markdown") or "").strip()
            if markdown:
                parts.append(f"PAGE {page_number} OCR PAGE LEAD:\n{markdown}")
    return "\n\n".join(parts)[:40_000]


def prepare_price_source_text_layer(
    *,
    file_name: str,
    file_bytes: bytes,
    structured_text: str = "",
    image_ocr: Callable[..., dict[str, Any]] = run_mistral_ocr,
    pdf_ocr: Callable[..., dict[str, Any]] = run_mistral_direct_pdf_evidence_ocr,
) -> PriceSourceTextLayer:
    """Build the auditable text layer consumed by Price extraction.

    Digital PDFs retain their native text for price rows, but their graphical
    masthead is always OCRed as independent issuer evidence.  Supplier identity
    must never depend on whether a PDF happened to contain a text layer.
    """
    suffix = Path(file_name).suffix.lower()
    if suffix in STRUCTURED_TABLE_SUFFIXES:
        return PriceSourceTextLayer(text=structured_text, strategy="structured_table")
    if suffix == ".pdf":
        embedded_text = extract_embedded_pdf_text(file_bytes)
        if len(embedded_text) >= PDF_EMBEDDED_TEXT_MIN_CHARS:
            package = pdf_ocr(file_name=file_name, file_bytes=file_bytes)
            return PriceSourceTextLayer(
                text=embedded_text,
                strategy="pdf_embedded_text_with_header_ocr",
                ocr_package=package,
                issuer_evidence_text=ocr_issuer_evidence_text(package),
            )
        package = pdf_ocr(file_name=file_name, file_bytes=file_bytes)
        text = ocr_package_text(package)
        if not text:
            raise RuntimeError("OCR returned no readable text for this PDF.")
        return PriceSourceTextLayer(
            text=text,
            strategy="pdf_ocr",
            ocr_package=package,
            issuer_evidence_text=ocr_issuer_evidence_text(package),
        )
    if suffix in OCR_IMAGE_SUFFIXES:
        ocr_name, ocr_bytes = normalise_ocr_image(file_name, file_bytes)
        package = dict(image_ocr(file_name=ocr_name, file_bytes=ocr_bytes))
        package["source_file_name"] = file_name
        text = ocr_package_text(package)
        if not text:
            raise RuntimeError("OCR returned no readable text for this image.")
        return PriceSourceTextLayer(
            text=text,
            strategy="image_ocr",
            ocr_package=package,
            issuer_evidence_text=ocr_issuer_evidence_text(package),
        )
    return PriceSourceTextLayer(text=structured_text, strategy="source_text")
