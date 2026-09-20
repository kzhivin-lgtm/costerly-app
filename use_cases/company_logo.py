from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from io import BytesIO
import logging
import re
from uuid import uuid4
import warnings

import pymupdf
from PIL import Image, ImageChops, ImageDraw, ImageOps


logger = logging.getLogger(__name__)

COMPANY_LOGO_BUCKET = "company-logos"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_SOURCE_PIXELS = 40_000_000
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
OUTPUT_SIZE = 1024
CONTENT_SIZE = 768
MIN_PNG_CONTENT_EDGE = 512
CARD_RADIUS = 64
CARD_BORDER_WIDTH = 2
CARD_BORDER_COLOR = (229, 220, 237, 255)


class CompanyLogoError(ValueError):
    """A safe, user-facing company-logo validation or conversion error."""


@dataclass(frozen=True)
class NormalizedCompanyLogo:
    png_bytes: bytes
    source_format: str
    source_width: int
    source_height: int
    content_width: int
    content_height: int


def _source_format(source: bytes) -> str:
    if source.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if source.startswith(b"%PDF-"):
        return "pdf"
    prefix = source[:4096].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
    if prefix.startswith(b"<svg") or (
        prefix.startswith(b"<?xml") and b"<svg" in prefix
    ):
        return "svg"
    raise CompanyLogoError("Upload a PNG, SVG, or PDF logo.")


def _validate_svg(source: bytes) -> None:
    lowered = source.lower()
    blocked = (
        b"<!doctype",
        b"<!entity",
        b"<script",
        b"<foreignobject",
    )
    references = re.findall(
        rb"(?:href|xlink:href)\s*=\s*['\"]\s*([^'\"]+)",
        lowered,
    )
    css_references = re.findall(
        rb"url\(\s*['\"]?\s*([^'\")\s]+)",
        lowered,
    )

    def reference_is_safe(reference: bytes) -> bool:
        reference = reference.strip()
        if reference.startswith(b"#"):
            return True
        return bool(
            re.match(
                rb"data:image/(?:png|jpe?g|webp)(?:;[^,]*)?,",
                reference,
            )
        )

    unsafe_reference = any(
        not reference_is_safe(reference)
        for reference in (*references, *css_references)
    )
    event_handler = re.search(rb"\son[a-z]+\s*=", lowered)
    if (
        any(marker in lowered for marker in blocked)
        or b"@import" in lowered
        or unsafe_reference
        or event_handler
    ):
        raise CompanyLogoError(
            "The SVG includes a linked or unsupported resource. Export it with images embedded."
        )


def _render_document(source: bytes, source_format: str) -> Image.Image:
    if source_format == "svg":
        _validate_svg(source)
    try:
        document = pymupdf.open(stream=source, filetype=source_format)
    except Exception as exc:
        raise CompanyLogoError(f"The {source_format.upper()} logo could not be opened.") from exc
    try:
        if document.needs_pass:
            raise CompanyLogoError("Password-protected PDF logos are not supported.")
        if document.page_count < 1:
            raise CompanyLogoError("The logo document has no visible page.")
        page = document[0]
        longest = max(float(page.rect.width), float(page.rect.height), 1.0)
        scale = min(8.0, 2048.0 / longest)
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            colorspace=pymupdf.csRGB,
            alpha=True,
        )
        return Image.frombytes(
            "RGBA",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
    except CompanyLogoError:
        raise
    except Exception as exc:
        raise CompanyLogoError(
            f"The {source_format.upper()} logo could not be rendered."
        ) from exc
    finally:
        document.close()


def _open_png(source: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(source)) as image:
                if image.format != "PNG":
                    raise CompanyLogoError("The uploaded file is not a valid PNG.")
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > MAX_SOURCE_PIXELS:
                    raise CompanyLogoError("The PNG dimensions are too large to process safely.")
                return ImageOps.exif_transpose(image).convert("RGBA")
    except CompanyLogoError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise CompanyLogoError("The PNG dimensions are too large to process safely.") from exc
    except Exception as exc:
        raise CompanyLogoError("The PNG logo could not be opened.") from exc


def _content_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = image.getchannel("A")
    alpha_mask = alpha.point(lambda value: 255 if value > 8 else 0)
    alpha_bbox = alpha_mask.getbbox()
    if alpha_bbox is None:
        raise CompanyLogoError("The logo is fully transparent.")

    if alpha.getextrema() == (255, 255):
        rgb = image.convert("RGB")
        white = Image.new("RGB", rgb.size, "white")
        difference = ImageChops.difference(rgb, white).convert("L")
        visible = difference.point(lambda value: 255 if value > 8 else 0)
        white_bbox = visible.getbbox()
        if white_bbox is None:
            raise CompanyLogoError("The logo is blank on a white background.")
        return white_bbox
    return alpha_bbox


def normalize_company_logo(source: bytes) -> NormalizedCompanyLogo:
    if not source:
        raise CompanyLogoError("Choose a logo file first.")
    if len(source) > MAX_SOURCE_BYTES:
        raise CompanyLogoError("The source logo must be 50 MB or smaller.")

    source_format = _source_format(source)
    image = _open_png(source) if source_format == "png" else _render_document(source, source_format)
    source_width, source_height = image.size
    if source_width * source_height > MAX_SOURCE_PIXELS:
        raise CompanyLogoError("The logo dimensions are too large to process safely.")

    bbox = _content_bbox(image)
    content = image.crop(bbox)
    content_width, content_height = content.size
    if source_format == "png" and max(content_width, content_height) < MIN_PNG_CONTENT_EDGE:
        raise CompanyLogoError(
            "The PNG logo is too small. Upload a PNG at least 512 px wide or tall, "
            "or use SVG or PDF."
        )

    content.thumbnail((CONTENT_SIZE, CONTENT_SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (1, 1, OUTPUT_SIZE - 2, OUTPUT_SIZE - 2),
        radius=CARD_RADIUS,
        fill=(255, 255, 255, 255),
        outline=CARD_BORDER_COLOR,
        width=CARD_BORDER_WIDTH,
    )
    paste_at = (
        (OUTPUT_SIZE - content.width) // 2,
        (OUTPUT_SIZE - content.height) // 2,
    )
    canvas.alpha_composite(content, dest=paste_at)

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True, compress_level=9)
    png_bytes = output.getvalue()
    if len(png_bytes) > MAX_OUTPUT_BYTES:
        raise CompanyLogoError(
            "The normalized logo is still too complex. Use a simpler SVG, PDF, or PNG logo."
        )
    return NormalizedCompanyLogo(
        png_bytes=png_bytes,
        source_format=source_format,
        source_width=source_width,
        source_height=source_height,
        content_width=content_width,
        content_height=content_height,
    )


def _trace_span(trace, name: str, **metadata: object):
    return trace.span(name, **metadata) if trace is not None else nullcontext()


def _stored_logo_path(reference: str | None, company_id: str) -> str | None:
    prefix = f"storage://{COMPANY_LOGO_BUCKET}/"
    if not reference or not reference.startswith(prefix):
        return None
    object_path = reference.removeprefix(prefix)
    if not object_path.startswith(f"{company_id}/"):
        return None
    return object_path


def load_company_logo_bytes(*, client, company_id: str, reference: str | None) -> bytes | None:
    object_path = _stored_logo_path(reference, company_id)
    if object_path is None:
        return None
    return client.storage.from_(COMPANY_LOGO_BUCKET).download(object_path)


def persist_company_logo(
    *,
    client,
    company_id: str,
    png_bytes: bytes,
    previous_reference: str | None,
    trace=None,
) -> str:
    object_path = f"{company_id}/{uuid4().hex}.png"
    reference = f"storage://{COMPANY_LOGO_BUCKET}/{object_path}"
    bucket = client.storage.from_(COMPANY_LOGO_BUCKET)
    try:
        with _trace_span(
            trace,
            "server.company_logo_storage_upload",
            output_bytes=len(png_bytes),
        ):
            bucket.upload(
                object_path,
                png_bytes,
                file_options={
                    "content-type": "image/png",
                    "cache-control": "31536000",
                    "upsert": "false",
                },
            )
        with _trace_span(trace, "server.company_logo_profile_update"):
            response = (
                client.table("companies")
                .update({"logo_url": reference})
                .eq("company_id", company_id)
                .execute()
            )
        rows = response.data or []
        if len(rows) != 1 or str(rows[0].get("company_id")) != company_id:
            raise RuntimeError("The company logo reference was not saved.")
    except Exception:
        try:
            bucket.remove([object_path])
        except Exception:
            logger.warning("company_logo_rollback_remove_failed", exc_info=True)
        raise

    previous_path = _stored_logo_path(previous_reference, company_id)
    if previous_path and previous_path != object_path:
        try:
            with _trace_span(trace, "server.company_logo_previous_remove"):
                bucket.remove([previous_path])
        except Exception:
            logger.warning("company_logo_previous_remove_failed", exc_info=True)
    return reference
