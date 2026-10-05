from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import csv
import ipaddress
import json
import logging
import re
import socket
import time
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote, urljoin, urlsplit
from uuid import uuid4

import httpx
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from agents.material_identity_agent import run_material_identity_agent
from agents.price_source_agent import run_price_source_agent
from agents.schemas.price_source_schema import (
    CANONICAL_UNIT_CODES,
    PRICE_SOURCE_CATEGORIES,
)
from db.company_access import assert_company_owner
from db.repositories import insert_agent_usage_event
from db.supabase_client import get_supabase_client
from use_cases.price_source_ocr import (
    OCR_IMAGE_SUFFIXES,
    open_price_source_image,
    prepare_price_source_text_layer,
)
from use_cases.price_source_material_resolution import (
    resolve_price_source_material_identities,
)


PRICE_SOURCE_BUCKET = "company-price-sources"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
WORDPRESS_ACCEPTED_RETRY_DELAYS_SECONDS = (1, 2, 3)
SUPPLIER_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
}
LEGACY_EXTREME_RATIO = 3.0
LEGACY_CONFIDENCE_PENALTY = 15.0
SUPPORTED_SUFFIXES = {".pdf", ".xlsx", ".csv", *OCR_IMAGE_SUFFIXES}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

PRICE_SOURCE_DEPARTMENTS = ("Wood", "Metal", "Finishing")
PRICE_CATALOG_DEPARTMENTS = {
    "Wood Sheets": "Wood",
    "Solid Wood": "Wood",
    "Wood Supplies": "Wood",
    "Hardware": "Wood",
    "Glass": "Wood",
    "Metal Sheets": "Metal",
    "Metal Profiles": "Metal",
    "Metal Supplies": "Metal",
    "Metal": "Metal",
    "Paints & Coatings": "Finishing",
    "Coating Supplies": "Finishing",
    "Other": "Wood",
}
LEGACY_PRICE_SOURCE_CATEGORIES = {
    "Sheet Materials": "Wood Sheets",
    "Edgebanding": "Wood Supplies",
    "Adhesives and Consumables": "Wood Supplies",
    "Finishes and Coatings": "Paints & Coatings",
    "Abrasives and Sanding": "Coating Supplies",
}
PRICE_CATALOG_DEPARTMENT_ORDER = {"Wood": 0, "Metal": 1, "Finishing": 2}
_CONSUMABLE_MARKERS = (
    "screw", "screws", "fastener", "dowel", "dowels", "lamello", "biscuit",
    "glue", "adhesive", "sandpaper", "abrasive", "ברג", "דיבל", "למלו", "דבק",
    "נייר לטש", "נייר שיוף", "שוחק",
)
_HARDWARE_MARKERS = (
    "hinge", "drawer slide", "drawer runner", "drawer rail", "runner",
    "bracket", "mounting plate", "mounting bracket", "clip", "latch",
    "handle", "knob", "furniture leg", "plinth leg", "hardware",
    "ציר", "מסילה", "מגירה", "תושבת", "פלטת חיבור", "קליפ", "פרפר",
    "רגלית", "ידית", "לחצן",
)
_GLASS_MARKERS = ("glass", "זכוכית")
_IDENTITY_DESCRIPTOR_MARKERS = {
    "construction": (
        ("perforated", ("perforated", "perforation", "מחורר", "מבוקע")),
    ),
    "finish": (
        ("glossy", ("high gloss", "glossy", "gloss", "מבריק")),
        ("matte", ("matte", "matt", "מט")),
        ("rough", ("rough", "textured", "texture", "מחוספס", "טקסטור")),
        ("sanded", ("sanded", "sanding", "שיוף", "משויף")),
        ("polished", ("polished", "polish", "מלוטש")),
        ("mirror", ("mirror", "mirrored", "מראה")),
    ),
}


class PriceSourceError(ValueError):
    pass


def normalize_price_source_sheet_rows(result: dict[str, Any]) -> dict[str, Any]:
    """Apply deterministic sheet-material evidence after OCR extraction."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("item_kind") != "material":
            continue
        text = " ".join(
            str(row.get(key) or "")
            for key in ("raw_description", "normalized_name", "material_family")
        ).casefold()
        source_text = str(row.get("raw_description") or "").casefold()
        attributes = row.get("identity_attributes") or {}
        # Only normalise descriptors which are literally present in the source.
        # This makes equivalent OCR/translations share an identity without making
        # a brand or trade name prove a material family or category.
        for attribute, descriptors in _IDENTITY_DESCRIPTOR_MARKERS.items():
            for canonical, markers in descriptors:
                if any(marker in source_text for marker in markers):
                    attributes[attribute] = canonical
                    if canonical == "perforated":
                        row["normalized_name"] = re.sub(
                            r"\b(?:cut to size|split)\b", "perforated",
                            str(row.get("normalized_name") or ""), flags=re.IGNORECASE,
                        )
                    break
        row["identity_attributes"] = attributes
        has_sheet_evidence = (
            row.get("material_type") == "Wood Sheets"
            or "sheet" in text
            or "לוח" in text
            or (
                float(attributes.get("thickness_mm") or 0) > 0
                and max(
                    float(attributes.get("width_mm") or 0),
                    float(attributes.get("length_mm") or 0),
                ) >= 1000
            )
        )
        if row.get("material_type") == "Glass" and not any(
            marker in source_text for marker in _GLASS_MARKERS
        ):
            # The extractor must positively prove glass. A trade name, a size,
            # or a generic sheet is not such proof. Keep the row editable,
            # rather than inventing a wrong catalogue category.
            row["material_type"] = "Other"
            row["material_family"] = "other"
            if "glass" in str(row.get("normalized_name") or "").casefold():
                row["normalized_name"] = (
                    "Unclassified sheet material"
                    if has_sheet_evidence
                    else "Unclassified material"
                )
        if row.get("material_type") != "Wood Sheets":
            continue
        thickness = float(attributes.get("thickness_mm") or 0)
        name = str(row.get("normalized_name") or "")
        # Category already conveys sheet form. Keep only identity-bearing words;
        # never lose a proven thickness.
        name = re.sub(r"\b(?:sheet|sheets|panel|board|\d+\s*[- ]?sheet)\b", "", name, flags=re.I)
        name = re.sub(r"\s+", " ", name).strip(" ,-")
        if thickness:
            thickness_label = f"{int(thickness)} mm"
            if re.search(r"\b\d+(?:\.\d+)?\s*mm\b", name, flags=re.I):
                name = re.sub(r"\b\d+(?:\.\d+)?\s*mm\b", thickness_label, name, count=1, flags=re.I)
            else:
                name = f"{name} {thickness_label}".strip()
        row["normalized_name"] = name
        # A full wood sheet quoted as a piece is still the same purchasable sheet.
        # Cut parts are represented by supplier Material Jobs, not by a second
        # material unit.
        if _normalized_unit(str(row.get("raw_unit") or "")) == "piece":
            row["raw_unit"] = "sheet"
            row["purchase_unit"] = "sheet"
            row["calculation_unit"] = "sheet"
            row["conversion_factor"] = 1
            raw_price = row.get("raw_price")
            if isinstance(raw_price, (int, float)):
                row["normalized_price"] = raw_price
    return result


def material_structural_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str, str]:
    """Return the deterministic private-material identity.

    The key deliberately ignores prose, SKU, colour and décor.  A supplier can
    write the same sheet in many ways, but thickness, dimensions and a proven
    construction such as perforated are real catalog distinctions.
    """
    attributes = row.get("identity_attributes") or {}

    def number(field: str) -> str:
        try:
            value = float(attributes.get(field) or 0)
        except (TypeError, ValueError):
            return ""
        return str(int(value)) if value > 0 and value.is_integer() else (str(value) if value > 0 else "")

    family_tokens = _normalized_name(str(row.get("material_family") or "")).split()
    return (
        " ".join(sorted(family_tokens)),
        number("thickness_mm"),
        number("width_mm"),
        number("length_mm"),
        number("diameter_mm"),
        _normalized_name(str(attributes.get("construction") or "")),
    )


def material_source_description_key(row: Mapping[str, Any]) -> str:
    """Return stable source wording for same-supplier repeat matching."""
    return _normalized_name(str(row.get("raw_description") or ""))


def discard_price_source_consumables(result: dict[str, Any]) -> int:
    """Discard low-value consumables before any private row or offer is stored."""
    retained: list[dict[str, Any]] = []
    discarded = 0
    for row in result.get("rows") or []:
        text = " ".join(str(row.get(key) or "") for key in ("raw_description", "normalized_name", "material_family")).casefold()
        is_hardware = (
            row.get("material_type") == "Hardware"
            or any(marker in text for marker in _HARDWARE_MARKERS)
        )
        if (
            row.get("item_kind") == "material"
            and not is_hardware
            and any(marker in text for marker in _CONSUMABLE_MARKERS)
        ):
            discarded += 1
            continue
        retained.append(row)
    result["rows"] = retained
    return discarded


def discard_price_source_non_candidates(result: dict[str, Any]) -> int:
    """Do not persist rows that cannot ever be a price candidate.

    A source file remains available for audit, but a row without a meaningful
    name or a positive price must not become Review noise or a hidden entity.
    """
    retained: list[dict[str, Any]] = []
    discarded = 0
    for row in result.get("rows") or []:
        name = str(row.get("normalized_name") or row.get("raw_description") or "").strip()
        try:
            price = float(row.get("raw_price") or 0)
        except (TypeError, ValueError):
            price = 0
        if not name or price <= 0:
            discarded += 1
            continue
        retained.append(row)
    result["rows"] = retained
    return discarded


def price_source_service_operation_code(row: Mapping[str, Any]) -> str | None:
    """Map an extracted supplier service to an existing reference operation."""
    text = " ".join(str(row.get(key) or "") for key in ("raw_description", "normalized_name", "material_family")).casefold()
    if ("חיתוך" in text or "cut" in text) and ("קנט" in text or "edge" in text):
        return "supplier_cut_and_edge_banding"
    for markers, code in (
        (("קנט", "edge"), "edge_banding"),
        (("חיתוך", "cut"), "panel_saw_cutting"),
        (("כרסום", "cnc", "router"), "cnc_router_profile_cutting"),
        (("קידוח", "drill"), "cnc_vertical_drilling"),
        (("חריץ", "groove", "dado"), "cnc_grooving"),
        (("הרכב", "assembly"), "carcass_assembly"),
    ):
        if any(marker in text for marker in markers):
            return code
    return None


def prepare_price_source_operation_rows(result: dict[str, Any]) -> dict[int, str]:
    """Retain only safely normalised supplier services for operation-offer storage."""
    mapped: dict[int, str] = {}
    for row in result.get("rows") or []:
        if row.get("item_kind") != "operation_service":
            continue
        code = price_source_service_operation_code(row)
        if code:
            # The canonical operation itself supplies the department and the
            # supplier-defined billing basis. An invoice's missing reusable
            # estimation unit must not push a known cut, edge-band, metal or
            # coating service into Review.
            if float(row.get("raw_price") or 0) > 0 and row.get("raw_vat_mode") != "unknown":
                row["status"] = "ready"
                row["reason_codes"] = sorted(
                    set(row.get("reason_codes") or [])
                    - {"missing_unit", "operation_service_unit_unclear", "package_conversion_unresolved"}
                )
                mapped[int(row["source_row_number"])] = code
            continue
        if row.get("status") != "excluded":
            row["status"] = "unresolved"
            row["reason_codes"] = sorted(set(row.get("reason_codes") or []) | {"operation_type_unresolved"})
    return mapped


def supplier_service_pricing_basis(
    raw_unit: object,
    *,
    operation_code: str | None = None,
) -> str:
    """Return a billing basis only when the source unit actually proves one."""
    # A combined cut-and-edge order is normally a supplier-defined detail.
    # "piece" in the invoice does not prove a reusable per-piece rate.
    if operation_code == "supplier_cut_and_edge_banding":
        return "supplier_defined"
    unit = _normalized_name(str(raw_unit or ""))
    if unit in {"m", "meter", "metre", "linear m", "linear meter"}:
        return "linear_meter"
    if unit in {"m2", "sqm", "square meter", "square metre"}:
        return "square_meter"
    if unit in {"sheet", "panel", "board"}:
        return "sheet"
    if unit in {"hour", "hr"}:
        return "hour"
    if unit in {"job", "order"}:
        return "job"
    if unit in {"piece", "pc", "unit", "each"}:
        return "piece"
    return "supplier_defined"


def supplier_merge_key(name: object) -> str:
    """Compare supplier cores, ignoring legal wrappers and punctuation."""
    text = str(name or "").casefold()
    text = re.sub(r"[\s\-‐‑‒–—―'\".,/()\\]+", " ", text)
    for token in ("בעמ", "בע מ", "חברה", "חברה בעמ", "ltd", "limited", "llc", "inc", "corp", "co", "ооо", "ooo"):
        text = re.sub(rf"\b{re.escape(token)}\b", " ", text)
    # OCR produces many remaining variants of the Israeli legal suffix, for
    # example בעיים and בעימו. It never identifies the commercial supplier.
    text = re.sub(r"\bבע[\w]{0,4}\b", " ", text, flags=re.UNICODE)
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def clean_supplier_name(name: object) -> str:
    """Keep the first readable supplier spelling, without legal OCR noise."""
    text = str(name or "").strip()
    text = re.sub(r"(?:\s|[,.\-])*בע[\w]{0,4}\s*$", "", text, flags=re.IGNORECASE | re.UNICODE)
    text = re.sub(r"(?:\s|[,.\-])*(?:ltd|limited|llc|inc|corp|co|ooo|ооо)\.?\s*$", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip() or str(name or "").strip()


def supplier_merge_max_distance(core_length: int) -> int:
    """Allow proportionate OCR variance, but keep short names conservative."""
    if core_length <= 5:
        return 1
    # Supplier names in invoices often arrive through OCR. Once the meaningful
    # core is long enough, favour one unique close candidate over creating a
    # duplicate supplier that splits its price history. Ties are still refused
    # by ``match_existing_supplier`` below.
    return max(1, round(core_length * 0.45))


def _damerau_levenshtein(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    previous_previous: list[int] | None = None
    for index, left_char in enumerate(left, start=1):
        current = [index]
        for right_index, right_char in enumerate(right, start=1):
            replace = previous[right_index - 1] + (left_char != right_char)
            insert = current[right_index - 1] + 1
            delete = previous[right_index] + 1
            transpose = (
                previous_previous[right_index - 2] + 1
                if previous_previous is not None and right_index > 1
                and left_char == right[right_index - 2]
                and left[index - 2] == right_char
                else replace + 1
            )
            current.append(min(replace, insert, delete, transpose))
        previous_previous, previous = previous, current
    return previous[-1]


def match_existing_supplier(
    supplier_name: str,
    candidates: Sequence[Mapping[str, Any]],
    *,
    supplier_hp: str = "",
) -> Mapping[str, Any] | None:
    """Return the canonical supplier for a safe OCR-level match.

    If an incoming name is equally close to aliases already accumulated for one
    supplier, production callers provide ``created_at``.  The first stored
    supplier is the product's canonical spelling, so it wins that tie.  Test
    and import callers without a creation timestamp retain the conservative
    ambiguous-match behaviour.
    """
    normalized_hp = re.sub(r"[^a-z0-9]", "", str(supplier_hp or "").casefold())
    if normalized_hp:
        hp_matches = [
            candidate for candidate in candidates
            if re.sub(r"[^a-z0-9]", "", str(candidate.get("supplier_hp") or "").casefold())
            == normalized_hp
        ]
        if hp_matches:
            return min(
                hp_matches,
                key=lambda candidate: (str(candidate.get("created_at") or "~"), str(candidate.get("supplier_id") or "")),
            )
    incoming = supplier_merge_key(supplier_name)
    if not incoming:
        return None
    scored = []
    for candidate in candidates:
        core = supplier_merge_key(candidate.get("supplier_name") or candidate.get("normalized_name"))
        if not core:
            continue
        distance = _damerau_levenshtein(incoming, core)
        if distance <= supplier_merge_max_distance(max(len(incoming), len(core))):
            scored.append((distance, candidate))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0])
    # In production every supplier row is timestamped.  Once all safe matches
    # have timestamps, the first accepted spelling is canonical, even when a
    # later OCR variant is a few edits closer to this particular invoice.
    dated = [candidate for _, candidate in scored if candidate.get("created_at")]
    if len(dated) == len(scored):
        dated.sort(key=lambda candidate: (str(candidate["created_at"]), str(candidate.get("supplier_id") or "")))
        return dated[0]
    best_distance = scored[0][0]
    best = [candidate for distance, candidate in scored if distance == best_distance]
    return best[0] if len(best) == 1 else None


@dataclass(frozen=True)
class CombinedPriceSource:
    name: str
    data: bytes

    def getvalue(self) -> bytes:
        return self.data


@dataclass(frozen=True)
class PriceSourceProcessResult:
    source_id: str
    summary: dict[str, object]


logger = logging.getLogger(__name__)


def validate_price_source_upload_selection(files: list) -> None:
    """Reject multi-file selections that cannot represent one logical document."""
    selected = [item for item in files if item is not None]
    if len(selected) <= 1:
        return
    suffixes = [Path(str(item.name)).suffix.lower() for item in selected]
    if any(suffix not in OCR_IMAGE_SUFFIXES for suffix in suffixes):
        raise PriceSourceError(
            "Select one PDF or spreadsheet, or several photos from the same document"
        )


def accepted_price_source_uploads(files: list) -> list:
    """Apply the one-document MVP contract to a native multi-file selection."""
    selected = [item for item in files if item is not None]
    if len(selected) <= 1:
        return selected
    suffixes = [Path(str(item.name)).suffix.lower() for item in selected]
    photo_suffixes = OCR_IMAGE_SUFFIXES
    if suffixes[0] in photo_suffixes:
        return [
            item
            for item, suffix in zip(selected, suffixes, strict=True)
            if suffix in photo_suffixes
        ]
    return selected[:1]


def render_price_source_pdf_preview(
    file_bytes: bytes,
    *,
    max_width: int = 240,
    max_height: int = 140,
) -> bytes | None:
    """Render a small first-page PNG without affecting source acceptance."""
    if not file_bytes:
        return None
    try:
        import pymupdf

        document = pymupdf.open(stream=file_bytes, filetype="pdf")
        try:
            if document.needs_pass or document.page_count < 1:
                return None
            page = document[0]
            width = max(float(page.rect.width), 1.0)
            height = max(float(page.rect.height), 1.0)
            scale = max(0.1, min(2.0, max_width / width, max_height / height))
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale),
                colorspace=pymupdf.csRGB,
                alpha=False,
            )
            return pixmap.tobytes("png")
        finally:
            document.close()
    except Exception:
        logger.info("Price source PDF preview unavailable", exc_info=True)
        return None


def _price_source_preview_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_price_source_table_preview(rows: list[list[object]]) -> bytes | None:
    if not rows:
        return None
    width, height = 240, 140
    visible_rows = rows[:7]
    column_count = min(max((len(row) for row in visible_rows), default=0), 6)
    if column_count < 1:
        return None
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _price_source_preview_font(10)
    row_height = height / len(visible_rows)
    column_width = width / column_count
    for row_index, row in enumerate(visible_rows):
        top = round(row_index * row_height)
        bottom = round((row_index + 1) * row_height)
        fill = "#F1EBFA" if row_index == 0 else ("#FFFFFF" if row_index % 2 else "#FAF8FC")
        draw.rectangle((0, top, width, bottom), fill=fill)
        for column_index in range(column_count):
            left = round(column_index * column_width)
            right = round((column_index + 1) * column_width)
            draw.rectangle((left, top, right, bottom), outline="#DED8E5", width=1)
            value = (
                ""
                if column_index >= len(row) or row[column_index] is None
                else str(row[column_index])
            )
            value = value.replace("\n", " ").strip()
            max_chars = max(3, int(column_width / 6.2) - 1)
            if len(value) > max_chars:
                value = value[: max_chars - 1] + "…"
            draw.text((left + 3, top + 3), value, font=font, fill="#302A36")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    image.close()
    return output.getvalue()


def render_price_source_preview(
    file_name: str,
    file_bytes: bytes,
    *,
    max_width: int = 240,
    max_height: int = 140,
) -> bytes | None:
    """Render a bounded preview for every accepted Price Source format."""
    suffix = Path(str(file_name)).suffix.lower()
    if not file_bytes:
        return None
    if suffix == ".pdf":
        return render_price_source_pdf_preview(
            file_bytes,
            max_width=max_width,
            max_height=max_height,
        )
    if suffix in OCR_IMAGE_SUFFIXES:
        try:
            image = open_price_source_image(file_bytes)
            try:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                return output.getvalue()
            finally:
                image.close()
        except (UnidentifiedImageError, OSError):
            logger.info("Price source image preview unavailable", exc_info=True)
            return None
    if suffix == ".xlsx":
        try:
            from openpyxl import load_workbook

            workbook = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
            try:
                worksheet = next(
                    (sheet for sheet in workbook.worksheets if sheet.sheet_state == "visible"),
                    workbook.worksheets[0],
                )
                rows = [list(row[:6]) for row in worksheet.iter_rows(max_row=7, values_only=True)]
            finally:
                workbook.close()
            return _render_price_source_table_preview(rows)
        except Exception:
            logger.info("Price source spreadsheet preview unavailable", exc_info=True)
            return None
    if suffix == ".csv":
        try:
            text = file_bytes.decode("utf-8-sig", errors="replace")
            rows = [row[:6] for _, row in zip(range(7), csv.reader(text.splitlines()))]
            return _render_price_source_table_preview(rows)
        except Exception:
            logger.info("Price source CSV preview unavailable", exc_info=True)
            return None
    return None


def combine_price_source_files(files: list) -> object | None:
    """Freeze one upload or combine ordered image pages into one PDF."""
    selected = accepted_price_source_uploads(files)
    if not selected:
        return None
    if len(selected) == 1:
        item = selected[0]
        return CombinedPriceSource(name=str(item.name), data=item.getvalue())
    validate_price_source_upload_selection(selected)
    if sum(len(item.getvalue()) for item in selected) > MAX_SOURCE_BYTES:
        raise PriceSourceError("The combined price source must be 50 MB or smaller")
    pages: list[Image.Image] = []
    try:
        for item in selected:
            pages.append(open_price_source_image(item.getvalue()))
        output = BytesIO()
        pages[0].save(output, format="PDF", save_all=True, append_images=pages[1:])
    except (UnidentifiedImageError, OSError) as exc:
        raise PriceSourceError("One of the selected photos could not be read") from exc
    finally:
        for page in pages:
            page.close()
    return CombinedPriceSource(
        name=f"photo-document-{len(selected)}-pages.pdf",
        data=output.getvalue(),
    )


def _emit_duration(trace, name: str, started_at: float, **metadata: object) -> None:
    if trace is not None:
        trace.event(
            name,
            duration_ms=(time.perf_counter() - started_at) * 1000,
            metadata=metadata,
        )


def _emit_marker(trace, name: str, **metadata: object) -> None:
    if trace is not None:
        trace.event(name, metadata=metadata)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._ignored += 1
        if tag.lower() in {"p", "div", "tr", "li", "br", "h1", "h2", "h3", "td", "th"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._ignored:
            self._ignored -= 1
        if tag.lower() in {"p", "div", "tr", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"[ \t]+", " ", "".join(self.parts)).strip()


def _visible_text_from_html(value: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(value)
    return parser.text()


def _same_host_wordpress_json_alternate(
    page_url: str,
    link_header: str,
) -> str | None:
    page_host = (urlsplit(page_url).hostname or "").casefold()
    for part in str(link_header or "").split(","):
        match = re.match(r'\s*<([^>]+)>\s*;(.*)$', part)
        if not match:
            continue
        attributes = match.group(2).casefold()
        candidate = urljoin(page_url, match.group(1).strip())
        if (
            'rel="alternate"' in attributes
            and 'type="application/json"' in attributes
            and (urlsplit(candidate).hostname or "").casefold() == page_host
        ):
            return _validate_public_url(candidate)
    return None


def _same_host_wordpress_slug_endpoint(page_url: str) -> str | None:
    parsed = urlsplit(page_url)
    slug = parsed.path.strip("/").split("/")[-1]
    if not slug or not parsed.hostname:
        return None
    candidate = (
        f"{parsed.scheme}://{parsed.netloc}/wp-json/wp/v2/pages"
        f"?slug={quote(slug, safe='')}&_fields=content,link"
    )
    return _validate_public_url(candidate)


def _same_host_wordpress_query_route_endpoint(page_url: str) -> str | None:
    """Use WordPress' query route when the pretty REST path is intercepted."""
    parsed = urlsplit(page_url)
    slug = parsed.path.strip("/").split("/")[-1]
    if not slug or not parsed.hostname:
        return None
    candidate = (
        f"{parsed.scheme}://{parsed.netloc}/?rest_route=/wp/v2/pages"
        f"&slug={quote(slug, safe='')}&_fields=content,link"
    )
    return _validate_public_url(candidate)


def _wordpress_rendered_html(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        return ""
    content = payload.get("content") or {}
    return str(content.get("rendered") or "") if isinstance(content, dict) else ""


def _normalized_name(value: str) -> str:
    return re.sub(r"[^\w]+", " ", value.casefold(), flags=re.UNICODE).strip()


def _normalized_unit(value: str) -> str:
    unit = _normalized_name(value).replace(" ", "")
    aliases = {
        "sqm": "m2",
        "m²": "m2",
        "squaremeter": "m2",
        "squaremeters": "m2",
        "m2": "m2",
        "sqmeter": "m2",
        "sqmeters": "m2",
        "squaremetre": "m2",
        "squaremetres": "m2",
        "lm": "linear_m",
        "linm": "linear_m",
        "runningmeter": "linear_m",
        "runningmeters": "linear_m",
        "linearmeter": "linear_m",
        "linearmeters": "linear_m",
        "unit": "piece",
        "units": "piece",
        "pcs": "piece",
        "pc": "piece",
        "sheet": "sheet",
        "sheets": "sheet",
    }
    return aliases.get(unit, unit)


def _decimal_equal(left: object, right: object, places: str) -> bool:
    try:
        quantum = Decimal(places)
        return Decimal(str(left)).quantize(quantum) == Decimal(str(right)).quantize(quantum)
    except (InvalidOperation, TypeError, ValueError):
        return False


def price_offer_matches_row(
    offer: dict,
    row: dict,
    *,
    default_currency: str = "",
) -> bool:
    """Compare persisted price-affecting values at their database precision."""
    currency = str(row.get("raw_currency") or default_currency or "").strip().upper()
    vat_included = (
        True
        if row.get("raw_vat_mode") == "included"
        else False if row.get("raw_vat_mode") == "excluded" else None
    )
    return all(
        (
            _decimal_equal(offer.get("source_price"), row.get("raw_price"), "0.0001"),
            _normalized_unit(str(offer.get("source_unit") or ""))
            == _normalized_unit(str(row.get("raw_unit") or "")),
            _normalized_unit(str(offer.get("purchase_unit") or ""))
            == _normalized_unit(str(row.get("purchase_unit") or "")),
            _normalized_unit(str(offer.get("calculation_unit") or ""))
            == _normalized_unit(str(row.get("calculation_unit") or "")),
            _decimal_equal(
                offer.get("conversion_factor"), row.get("conversion_factor"), "0.00000001"
            ),
            _decimal_equal(
                offer.get("normalized_price"), row.get("normalized_price"), "0.0001"
            ),
            str(offer.get("currency") or "").strip().upper() == currency,
            offer.get("vat_included") is vat_included,
        )
    )


def supplier_operation_offer_matches_row(
    offer: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    pricing_basis: str,
    default_currency: str = "",
) -> bool:
    """Compare one supplier job without treating its raw wording as identity.

    ``supplier_defined`` proves a supplier's finished-detail price, not a
    reusable rate per unit. A printed ``piece`` and an omitted unit therefore
    describe the same offer. Measured bases still require equal units.
    """
    vat_included = (
        True if row.get("raw_vat_mode") == "included"
        else False if row.get("raw_vat_mode") == "excluded" else None
    )
    unit_matches = (
        True
        if pricing_basis == "supplier_defined"
        else _normalized_unit(str(offer.get("source_unit_label") or ""))
        == _normalized_unit(str(row.get("raw_unit") or ""))
    )
    return all(
        (
            _decimal_equal(offer.get("source_price"), row.get("raw_price"), "0.0001"),
            str(offer.get("pricing_basis") or "") == pricing_basis,
            unit_matches,
            str(offer.get("currency") or "").strip().upper()
            == str(row.get("raw_currency") or default_currency or "").strip().upper(),
            offer.get("vat_included") is vat_included,
        )
    )


def supplier_operation_offer_catalog_key(offer: Mapping[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    """Return the user-facing identity of one supplier Material Job offer."""
    basis = str(offer.get("pricing_basis") or "")
    try:
        price = Decimal(str(offer.get("source_price") or "0")).quantize(Decimal("0.0001"))
    except (InvalidOperation, ValueError):
        price = Decimal("0")
    source_unit = "" if basis == "supplier_defined" else _normalized_unit(
        str(offer.get("source_unit_label") or "")
    )
    return (
        str(offer.get("operation_id") or ""),
        str(offer.get("supplier_id") or ""),
        basis,
        str(price),
        str(offer.get("currency") or "").strip().upper(),
        str(offer.get("vat_included")),
        source_unit,
    )


def material_offer_matches_extracted_row(
    offer: Mapping[str, Any],
    material: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    default_currency: str = "",
) -> bool:
    """Recognise a repeat material despite invoice-only wording differences.

    This is deliberately narrower than an open-ended fuzzy material merge. It
    needs the same supplier-lane price, source unit, VAT basis, material family
    and every available structural size. Extra invoice words such as colour,
    line quantity or "split" cannot make a second company material.
    """
    if not _decimal_equal(offer.get("source_price"), row.get("raw_price"), "0.0001"):
        return False
    if offer.get("calculation_unit"):
        offer_unit = _normalized_unit(str(offer.get("calculation_unit") or ""))
        row_unit = _normalized_unit(str(row.get("calculation_unit") or ""))
    elif offer.get("purchase_unit"):
        offer_unit = _normalized_unit(str(offer.get("purchase_unit") or ""))
        row_unit = _normalized_unit(str(row.get("purchase_unit") or ""))
    else:
        offer_unit = _normalized_unit(str(offer.get("source_unit") or ""))
        row_unit = _normalized_unit(str(row.get("raw_unit") or ""))
    if offer_unit != row_unit:
        return False
    currency = str(row.get("raw_currency") or default_currency or "").strip().upper()
    if str(offer.get("currency") or "").strip().upper() != currency:
        return False
    vat_included = (
        True if row.get("raw_vat_mode") == "included"
        else False if row.get("raw_vat_mode") == "excluded" else None
    )
    if offer.get("vat_included") is not vat_included:
        return False

    specifications = material.get("specifications") or {}
    material_row = {
        "material_family": material.get("material_family") or specifications.get("material_family") or "",
        "identity_attributes": specifications,
    }
    if not material_row["identity_attributes"]:
        # Read-only compatibility for catalog rows created before structural
        # specifications existed. New rows never take this wording path.
        family = _normalized_name(str(row.get("material_family") or ""))
        material_name = _normalized_name(
            str(material.get("canonical_name") or material.get("normalized_name") or "")
        )
        if not family or family not in material_name:
            return False
        evidence = row.get("identity_attributes") or {}
        material_numbers = {int(value) for value in re.findall(r"\d+(?:\.0+)?", material_name)}
        for field in ("thickness_mm", "width_mm", "length_mm", "diameter_mm"):
            try:
                value = float(evidence.get(field) or 0)
            except (TypeError, ValueError):
                return False
            if value > 0 and int(value) not in material_numbers:
                return False
        return True
    # Pre-existing materials may lack a persisted family.  Their canonical name
    # remains a fallback only for that legacy case.
    if not material_row["material_family"]:
        material_row["material_family"] = str(material.get("canonical_name") or material.get("normalized_name") or "").split(" ")[0]
    return material_structural_key(material_row) == material_structural_key(row)


def material_offer_proves_unknown_family(
    offer: Mapping[str, Any],
    material: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    default_currency: str = "",
) -> str:
    """Return a known family only when a same-lane offer proves it.

    A brand name is not enough to invent plywood, MDF, or another family.  It
    is enough to inherit a prior family when the supplier SKU, price, unit,
    VAT and structural attributes all point to one existing private offer.
    """
    family = str((material.get("specifications") or {}).get("material_family") or "").strip()
    if not family:
        return ""
    candidate = dict(row)
    candidate["material_family"] = family
    return family if material_offer_matches_extracted_row(
        offer, material, candidate, default_currency=default_currency,
    ) else ""


def material_offer_matches_same_supplier_description(
    offer: Mapping[str, Any],
    material: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    default_currency: str = "",
) -> bool:
    """Match a repeated source line despite a changed AI family label."""
    specifications = material.get("specifications") or {}
    if specifications.get("source_description_key") != material_source_description_key(row):
        return False
    if not _decimal_equal(offer.get("source_price"), row.get("raw_price"), "0.0001"):
        return False
    offer_unit = _normalized_unit(str(
        offer.get("calculation_unit")
        or offer.get("purchase_unit")
        or offer.get("source_unit")
        or ""
    ))
    row_unit = _normalized_unit(str(
        row.get("calculation_unit") or row.get("purchase_unit") or row.get("raw_unit") or ""
    ))
    if offer_unit != row_unit:
        return False
    currency = str(row.get("raw_currency") or default_currency or "").strip().upper()
    if str(offer.get("currency") or "").strip().upper() != currency:
        return False
    vat_included = (
        True if row.get("raw_vat_mode") == "included"
        else False if row.get("raw_vat_mode") == "excluded" else None
    )
    if offer.get("vat_included") is not vat_included:
        return False
    row_attributes = row.get("identity_attributes") or {}
    for field in ("thickness_mm", "width_mm", "length_mm", "diameter_mm"):
        try:
            material_value = float(specifications.get(field) or 0)
            row_value = float(row_attributes.get(field) or 0)
        except (TypeError, ValueError):
            return False
        if material_value > 0 and row_value > 0 and material_value != row_value:
            return False
    return True


def price_offer_lane_key(
    *,
    supplier_id: object,
    source_summary: dict | None,
    source_id: object,
) -> str:
    """Return the isolated identity lane used to version one material offer."""
    supplier_key = str(supplier_id or "").strip()
    if supplier_key:
        return f"supplier:{supplier_key}"

    summary = source_summary or {}
    family_key = str(summary.get("source_family_sha256") or "").strip()
    fallback_key = family_key or str(source_id or "").strip() or "unidentified"
    if summary.get("source_origin") == "company_internal":
        return f"internal:{fallback_key}"
    return f"supplier-unknown:{fallback_key}"


def price_source_supplier_name(result: dict) -> str:
    """Keep company-owned calculations out of the supplier registry."""
    if result.get("source_origin") == "company_internal":
        return ""
    return str(result.get("supplier_name") or "").strip()


def price_source_extraction_diagnostics(
    result: Mapping[str, Any],
    *,
    text_layer_strategy: str,
    text_layer_characters: int,
    ocr_pages: int,
) -> dict[str, object]:
    """Return compact, source-safe evidence for a single extraction attempt."""
    rows = list(result.get("rows") or [])
    return {
        "text_layer_strategy": text_layer_strategy,
        "text_layer_characters": max(0, int(text_layer_characters)),
        "ocr_pages": max(0, int(ocr_pages)),
        "agent_row_count": len(rows),
        "agent_ready_row_count": sum(row.get("status") == "ready" for row in rows),
        "agent_unresolved_row_count": sum(row.get("status") == "unresolved" for row in rows),
        "agent_excluded_row_count": sum(row.get("status") == "excluded" for row in rows),
        "document_type": str(result.get("document_type") or ""),
        "source_origin": str(result.get("source_origin") or ""),
    }


def apply_legacy_price_benchmark(result: dict, legacy_materials: list[dict]) -> dict:
    """Use exact legacy identity/unit matches only as a negative confidence signal."""
    benchmark: dict[tuple[str, str], float] = {}
    for material in legacy_materials:
        name = _normalized_name(str(material.get("material_name") or ""))
        unit = _normalized_unit(str(material.get("price_unit") or ""))
        price = material.get("price")
        if name and unit and isinstance(price, (int, float)) and price > 0:
            benchmark[(name, unit)] = float(price)

    for row in result.get("rows") or []:
        if row.get("status") != "ready":
            continue
        key = (
            _normalized_name(str(row.get("normalized_name") or "")),
            _normalized_unit(str(row.get("calculation_unit") or "")),
        )
        old_price = benchmark.get(key)
        new_price = float(row.get("normalized_price") or 0)
        if not old_price or new_price <= 0:
            continue
        ratio = new_price / old_price
        if ratio > LEGACY_EXTREME_RATIO or ratio < 1 / LEGACY_EXTREME_RATIO:
            row["confidence"] = max(0.0, float(row["confidence"]) - LEGACY_CONFIDENCE_PENALTY)
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["extreme_legacy_price_difference"])
            )
    return result


def canonical_price_source_category(category: str) -> str:
    normalized = category.strip() or "Other"
    return LEGACY_PRICE_SOURCE_CATEGORIES.get(normalized, normalized)


def price_source_material_types(result: dict) -> list[str]:
    return sorted(
        {
            canonical_price_source_category(str(row.get("material_type") or "Other"))
            for row in result.get("rows") or []
            if row.get("status") != "excluded"
        },
        key=str.casefold,
    )


def guard_price_source_department(result: dict, department: str) -> dict:
    """Compatibility no-op after removing source-level department selection.

    Rows are classified individually. An unknown category is a valid catalog
    value, not grounds for Review merely because a source was opened in a
    different department.
    """
    return result


def price_source_semantic_fingerprint(result: dict) -> str:
    """Identify the same commercial document across files, scans, or photos."""
    document_number = _normalized_name(str(result.get("document_number") or ""))
    basis: dict[str, object] = {
        "source_origin": str(result.get("source_origin") or "unknown"),
        "supplier": _normalized_name(str(result.get("supplier_name") or "")),
        "document_number": document_number,
        "document_date": str(result.get("document_date") or ""),
    }
    if not document_number:
        basis.update(
            {
                "document_type": str(result.get("document_type") or ""),
                "currency": str(result.get("currency") or ""),
                "document_total": float(result.get("document_total") or 0),
            }
        )
        basis["rows"] = [
            {
                "description": _normalized_name(str(row.get("raw_description") or "")),
                "sku": _normalized_name(str(row.get("raw_sku") or "")),
                "price": float(row.get("raw_price") or 0),
                "quantity": float(row.get("raw_quantity") or 0),
                "line_total": float(row.get("raw_line_total") or 0),
            }
            for row in result.get("rows") or []
            if row.get("status") != "excluded"
        ]
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def price_source_template_fingerprint(file_name: str, data: bytes) -> str | None:
    """Identify a recurring spreadsheet layout while ignoring row values."""
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        rows = list(csv.reader(data.decode("utf-8-sig", errors="replace").splitlines()))
        if not rows:
            return None
        basis = {
            "format": "csv",
            "columns": len(rows[0]),
            "headers": [_normalized_name(cell) for cell in rows[0]],
        }
    elif suffix == ".xlsx":
        try:
            from openpyxl import load_workbook

            workbook = load_workbook(BytesIO(data), read_only=False, data_only=False)
        except Exception:
            return None
        try:
            sheets: list[dict[str, object]] = []
            cell_reference = re.compile(r"(?<![A-Z0-9_])(\$?[A-Z]{1,3})\$?\d+")
            for sheet in workbook.worksheets:
                row_shapes: list[tuple] = []
                for row in sheet.iter_rows(
                    min_row=1,
                    max_row=min(sheet.max_row, 250),
                    min_col=1,
                    max_col=min(sheet.max_column, 80),
                ):
                    cells: list[tuple] = []
                    for cell in row:
                        value = cell.value
                        if value is None:
                            continue
                        if cell.data_type == "f":
                            kind = "formula"
                            anchor = cell_reference.sub(r"\1#", str(value))
                        elif isinstance(value, bool):
                            kind = "bool"
                            anchor = ""
                        elif isinstance(value, (int, float, Decimal)):
                            kind = "number"
                            anchor = ""
                        elif getattr(cell, "is_date", False):
                            kind = "date"
                            anchor = ""
                        else:
                            kind = "text"
                            anchor = (
                                _normalized_name(str(value))[:80]
                                if cell.row <= 3 or bool(cell.font and cell.font.bold)
                                else ""
                            )
                        style = (
                            bool(cell.font and cell.font.bold),
                            str(cell.number_format or ""),
                            str(cell.alignment.horizontal or ""),
                            str(cell.fill.fill_type or ""),
                        )
                        cells.append((cell.column, kind, anchor, style))
                    shape = tuple(cells)
                    if shape and (not row_shapes or row_shapes[-1] != shape):
                        row_shapes.append(shape)
                sheets.append(
                    {
                        "title": _normalized_name(sheet.title),
                        "state": sheet.sheet_state,
                        "merged": sorted(str(item) for item in sheet.merged_cells.ranges),
                        "row_shapes": row_shapes,
                    }
                )
            basis = {"format": "xlsx", "sheets": sheets}
        finally:
            workbook.close()
    else:
        return None
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def price_source_family_identity(
    result: dict,
    *,
    source_name: str,
    source_kind: str,
    template_sha256: str | None = None,
) -> tuple[str, str]:
    """Return a stable internal identity for successive revisions of one source."""
    if source_kind == "url":
        parsed = urlsplit(source_name)
        origin = f"{(parsed.hostname or '').casefold()}{parsed.path.rstrip('/').casefold()}"
    elif template_sha256:
        origin = f"template:{template_sha256}"
    else:
        origin = _normalized_name(Path(source_name).name)
    basis: dict[str, str] = {
        "source_origin": _normalized_name(str(result.get("source_origin") or "unknown")),
        "supplier": _normalized_name(str(result.get("supplier_name") or "")),
        "source_kind": source_kind,
        "origin": origin,
    }
    if not template_sha256:
        basis["document_type"] = _normalized_name(
            str(result.get("document_type") or "")
        )
    if origin.startswith("photo document"):
        basis["document_number"] = _normalized_name(
            str(result.get("document_number") or "")
        )
        basis["document_date"] = str(result.get("document_date") or "")
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = sha256(encoded.encode("utf-8")).hexdigest()
    return fingerprint, f"PSF-{fingerprint[:12].upper()}"


def _find_previous_source_revision(
    client,
    company_id: str,
    *,
    family_sha256: str,
    semantic_sha256: str,
) -> tuple[dict | None, int]:
    sources = (
        client.table("company_price_sources")
        .select("source_id,processing_summary,created_at")
        .eq("company_id", company_id)
        .neq("status", "archived")
        .order("created_at", desc=True)
        .execute()
    ).data or []
    family_matches = [
        source
        for source in sources
        if isinstance(source.get("processing_summary"), dict)
        and source["processing_summary"].get("source_family_sha256") == family_sha256
    ]
    if family_matches:
        revision = max(
            int((source.get("processing_summary") or {}).get("source_revision") or 1)
            for source in family_matches
        ) + 1
        return family_matches[0], revision
    semantic_match = next(
        (
            source
            for source in sources
            if isinstance(source.get("processing_summary"), dict)
            and source["processing_summary"].get("semantic_sha256") == semantic_sha256
        ),
        None,
    )
    return semantic_match, 2 if semantic_match else 1


def _unchanged_duplicate_summary(source: dict) -> dict[str, object]:
    previous = dict(source.get("processing_summary") or {})
    total = int(previous.get("total") or 0)
    ready = int(previous.get("ready") or 0)
    summary = {
        "total": total,
        "ready": ready,
        "new": 0,
        "updated": 0,
        "unchanged": ready,
        "unresolved": int(previous.get("unresolved") or 0),
        "excluded": int(previous.get("excluded") or 0),
        "exact_duplicate": True,
        "agent_duration_seconds": 0.0,
        "token_cost": 0.0,
    }
    for key in (
        "source_family_sha256",
        "source_family_code",
        "template_sha256",
        "source_revision",
        "previous_source_id",
    ):
        if previous.get(key) is not None:
            summary[key] = previous[key]
    return summary


def _validate_department(department: str) -> str:
    normalized = department.strip()
    if normalized and normalized not in PRICE_SOURCE_DEPARTMENTS:
        raise PriceSourceError("Choose a department.")
    return normalized


def _validate_public_url(url: str) -> str:
    candidate = url.strip()
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PriceSourceError("Enter a public HTTP or HTTPS URL.")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise PriceSourceError("The URL must not contain credentials or a custom port.")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except OSError as exc:
        raise PriceSourceError("The supplier page could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise PriceSourceError("Only public supplier pages can be imported.")
    return candidate


def fetch_public_page(url: str, *, client: httpx.Client | None = None) -> tuple[str, bytes, str]:
    current = _validate_public_url(url)
    http = client or httpx.Client(timeout=20, headers=SUPPLIER_PAGE_HEADERS)
    owns_client = client is None
    try:
        for _ in range(4):
            response = http.get(current, follow_redirects=False)
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise PriceSourceError("The supplier page returned an invalid redirect.")
                current = _validate_public_url(urljoin(current, location))
                continue
            for delay_seconds in WORDPRESS_ACCEPTED_RETRY_DELAYS_SECONDS:
                if response.status_code != 202:
                    break
                # Some WordPress/CDN origins acknowledge a page request before
                # the rendered page is available. Retry this bounded state before
                # falling back to a REST endpoint.
                time.sleep(delay_seconds)
                response = http.get(current, follow_redirects=False)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
            if content_type not in {"text/html", "text/plain"}:
                raise PriceSourceError("The URL must point to a readable supplier webpage.")
            content = response.content
            if len(content) > MAX_SOURCE_BYTES:
                raise PriceSourceError("The supplier page is too large to process.")
            visible_text = _visible_text_from_html(response.text)
            primary_diagnostic = f"status_{response.status_code}_bytes_{len(content)}"
            wordpress_diagnostics: list[str] = []
            if not visible_text:
                alternate_urls = [
                    _same_host_wordpress_json_alternate(
                        current,
                        response.headers.get("link", ""),
                    ),
                    _same_host_wordpress_query_route_endpoint(current),
                    _same_host_wordpress_slug_endpoint(current),
                ]
                tried_alternate_urls: set[str] = set()
                accepted_alternate_urls: list[str] = []
                for alternate_url in alternate_urls:
                    if not alternate_url or alternate_url in tried_alternate_urls:
                        continue
                    tried_alternate_urls.add(alternate_url)
                    try:
                        alternate = http.get(alternate_url, follow_redirects=False)
                        if alternate.status_code == 202:
                            accepted_alternate_urls.append(alternate_url)
                            wordpress_diagnostics.append(
                                f"accepted_{len(alternate.content)}"
                            )
                            continue
                        alternate.raise_for_status()
                        if len(alternate.content) > MAX_SOURCE_BYTES:
                            raise PriceSourceError("The supplier page is too large to process.")
                        try:
                            payload = alternate.json()
                        except (AttributeError, ValueError):
                            payload = None
                        rendered = _wordpress_rendered_html(payload)
                        visible_text = _visible_text_from_html(str(rendered or ""))
                        wordpress_diagnostics.append(
                            f"status_{alternate.status_code}_bytes_{len(alternate.content)}_text_{len(visible_text)}"
                        )
                        if visible_text:
                            return current, alternate.content, visible_text
                    except httpx.HTTPError as exc:
                        status_code = getattr(getattr(exc, "response", None), "status_code", "network")
                        wordpress_diagnostics.append(f"error_{status_code}")
                for delay_seconds in WORDPRESS_ACCEPTED_RETRY_DELAYS_SECONDS:
                    if visible_text or not accepted_alternate_urls:
                        break
                    time.sleep(delay_seconds)
                    retry_urls = accepted_alternate_urls
                    accepted_alternate_urls = []
                    for alternate_url in retry_urls:
                        try:
                            alternate = http.get(alternate_url, follow_redirects=False)
                            if alternate.status_code == 202:
                                accepted_alternate_urls.append(alternate_url)
                                continue
                            alternate.raise_for_status()
                            if len(alternate.content) > MAX_SOURCE_BYTES:
                                raise PriceSourceError("The supplier page is too large to process.")
                            try:
                                payload = alternate.json()
                            except (AttributeError, ValueError):
                                payload = None
                            rendered = _wordpress_rendered_html(payload)
                            visible_text = _visible_text_from_html(str(rendered or ""))
                            wordpress_diagnostics.append(
                                f"retry_status_{alternate.status_code}_bytes_{len(alternate.content)}_text_{len(visible_text)}"
                            )
                            if visible_text:
                                return current, alternate.content, visible_text
                        except httpx.HTTPError as exc:
                            status_code = getattr(getattr(exc, "response", None), "status_code", "network")
                            wordpress_diagnostics.append(f"retry_error_{status_code}")
            if not visible_text:
                raise PriceSourceError(
                    "This supplier page does not expose readable text. "
                    "Upload its PDF, screenshot, or photo instead. "
                    f"[url-fetch-v6 primary={primary_diagnostic} wordpress={','.join(wordpress_diagnostics) or 'not_attempted'}]"
                )
            return current, content, visible_text
        raise PriceSourceError("The supplier page redirected too many times.")
    except httpx.HTTPError as exc:
        raise PriceSourceError("The supplier page could not be downloaded.") from exc
    finally:
        if owns_client:
            http.close()


def extract_spreadsheet_text(file_name: str, data: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        text = data.decode("utf-8-sig", errors="replace")
        rows = list(csv.reader(text.splitlines()))
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)[:180_000]
    if suffix == ".xlsx":
        sheets = pd.read_excel(BytesIO(data), sheet_name=None, dtype=str)
        parts: list[str] = []
        for sheet_name, frame in sheets.items():
            parts.append(f"SHEET: {sheet_name}")
            parts.append(frame.fillna("").to_csv(index=False))
        return "\n".join(parts)[:180_000]
    return ""


def _source_extension(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise PriceSourceError("Upload PDF, XLSX, CSV, JPEG, PNG, TIFF, or HEIC")
    return suffix


def _date_or_none(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat() if value else None
    except ValueError:
        return None


def list_price_sources(access) -> list[dict]:
    client = get_supabase_client()
    assert_company_owner(client, str(access.user_id), str(access.company_id))
    return (
        client.table("company_price_sources")
        .select(
            "source_id,source_name,source_kind,source_url,storage_path,mime_type,"
            "category,document_type,document_date,currency,vat_mode,status,"
            "processing_summary,created_at,processed_at,company_suppliers(supplier_name)"
        )
        .eq("company_id", str(access.company_id))
        .neq("status", "archived")
        .order("created_at", desc=True)
        .execute()
    ).data or []


def list_price_catalog(access) -> list[dict]:
    """Return active normalized supplier offers enriched for catalog display."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    offers = (
        client.table("company_material_offers")
        .select(
            "offer_id,company_material_id,supplier_id,source_id,source_row_id,"
            "source_price,source_unit,purchase_unit,calculation_unit,conversion_factor,"
            "normalized_price,normalized_unit,currency,vat_included,valid_from,"
            "confidence,created_at"
        )
        .eq("company_id", company_id)
        .eq("status", "active")
        .execute()
    ).data or []
    if not offers:
        return []

    materials = (
        client.table("company_material_items")
        .select("company_material_id,category,canonical_name,preferred_unit")
        .eq("company_id", company_id)
        .neq("status", "archived")
        .execute()
    ).data or []
    suppliers = (
        client.table("company_suppliers")
        .select("supplier_id,supplier_name")
        .eq("company_id", company_id)
        .eq("active", True)
        .execute()
    ).data or []
    source_rows = (
        client.table("company_price_source_rows")
        .select(
            "row_id,raw_description,normalized_name,raw_price,raw_currency,raw_unit,"
            "raw_vat_included,purchase_unit,calculation_unit,conversion_factor,"
            "normalized_unit,result_status,evidence,reason_codes"
        )
        .eq("company_id", company_id)
        .execute()
    ).data or []
    sources = (
        client.table("company_price_sources")
        .select(
            "source_id,source_name,source_kind,source_url,processing_summary,"
            "currency,vat_mode,processed_at,created_at"
        )
        .eq("company_id", company_id)
        .execute()
    ).data or []

    material_by_id = {
        str(row["company_material_id"]): row for row in materials
    }
    supplier_by_id = {str(row["supplier_id"]): row for row in suppliers}
    source_row_by_id = {str(row["row_id"]): row for row in source_rows}
    source_by_id = {str(row["source_id"]): row for row in sources}
    catalog: list[dict] = []
    for offer in offers:
        material = material_by_id.get(str(offer.get("company_material_id")))
        if not material:
            continue
        supplier = supplier_by_id.get(str(offer.get("supplier_id")), {})
        source_row = source_row_by_id.get(str(offer.get("source_row_id")), {})
        source = source_by_id.get(str(offer.get("source_id")), {})
        category = canonical_price_source_category(str(material.get("category") or "Other"))
        department = PRICE_CATALOG_DEPARTMENTS.get(category, "Wood")
        source_summary = source.get("processing_summary") or {}
        supplier_name = str(supplier.get("supplier_name") or "Unknown supplier")
        if source_summary.get("source_origin") == "company_internal":
            supplier_name = "Internal estimate"
        catalog.append(
            {
                **offer,
                "department": department,
                "material_type": category,
                "canonical_name": str(material.get("canonical_name") or "Material"),
                "original_name": str(source_row.get("raw_description") or ""),
                "source_row": source_row,
                "supplier_name": supplier_name,
                "source_name": str(source.get("source_name") or ""),
                "source_kind": str(source.get("source_kind") or ""),
                "source_url": str(source.get("source_url") or ""),
                "updated_at": (
                    offer.get("valid_from")
                    or source.get("processed_at")
                    or offer.get("created_at")
                    or source.get("created_at")
                ),
            }
        )
    return sorted(
        catalog,
        key=lambda row: (
            PRICE_CATALOG_DEPARTMENT_ORDER.get(str(row["department"]), 99),
            str(row["material_type"]).casefold(),
            str(row["canonical_name"]).casefold(),
            str(row["supplier_name"]).casefold(),
        ),
    )


def list_material_jobs(access) -> list[dict]:
    """Return active supplier material-job offers, separate from material offers."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    offers = (
        client.table("company_supplier_operation_offers")
        .select(
            "operation_offer_id,operation_id,supplier_id,source_id,source_row_id,"
            "raw_service_name,source_price,pricing_basis,source_unit_label,currency,"
            "vat_included,valid_from,confidence,created_at"
        )
        .eq("company_id", company_id)
        .eq("status", "active")
        .execute()
    ).data or []
    if not offers:
        return []

    operation_ids = list({str(row.get("operation_id")) for row in offers if row.get("operation_id")})
    operations = []
    if operation_ids:
        operations = (
            client.table("reference_operations")
            .select("operation_id,operation_code,department,operation_name")
            .in_("operation_id", operation_ids)
            .execute()
        ).data or []
    suppliers = (
        client.table("company_suppliers")
        .select("supplier_id,supplier_name")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    sources = (
        client.table("company_price_sources")
        .select(
            "source_id,source_name,source_kind,source_url,processing_summary,"
            "currency,vat_mode,processed_at,created_at"
        )
        .eq("company_id", company_id)
        .neq("status", "archived")
        .execute()
    ).data or []
    operation_by_id = {str(row["operation_id"]): row for row in operations}
    supplier_by_id = {str(row["supplier_id"]): row for row in suppliers}
    source_by_id = {str(row["source_id"]): row for row in sources}
    jobs: list[dict] = []
    for offer in offers:
        operation = operation_by_id.get(str(offer.get("operation_id")))
        source = source_by_id.get(str(offer.get("source_id")))
        if not operation or not source:
            continue
        supplier = supplier_by_id.get(str(offer.get("supplier_id")), {})
        summary = source.get("processing_summary") or {}
        supplier_name = str(supplier.get("supplier_name") or "Unknown supplier")
        if summary.get("source_origin") == "company_internal":
            supplier_name = "Internal estimate"
        operation_department = str(operation.get("department") or "").casefold()
        jobs.append(
            {
                **offer,
                "operation_name": str(operation.get("operation_name") or "Material job"),
                "operation_code": str(operation.get("operation_code") or ""),
                "department": {
                    "metal": "Metal",
                    "coating": "Finishing",
                }.get(operation_department, "Wood"),
                "supplier_name": supplier_name,
                "source": source,
                "updated_at": (
                    offer.get("valid_from")
                    or source.get("processed_at")
                    or offer.get("created_at")
                    or source.get("created_at")
                ),
            }
        )
    # A previous build could store both an omitted and a "piece" unit for the
    # same supplier-defined job. Keep source history, but display one current
    # catalog offer, choosing the newest evidence deterministically.
    visible_jobs: dict[tuple[str, str, str, str, str, str, str], dict] = {}
    for job in jobs:
        identity = supplier_operation_offer_catalog_key(job)
        prior = visible_jobs.get(identity)
        if prior is None or str(job.get("updated_at") or "") > str(prior.get("updated_at") or ""):
            visible_jobs[identity] = job
    return sorted(
        visible_jobs.values(),
        key=lambda row: (
            str(row["department"]).casefold(),
            str(row["operation_name"]).casefold(),
            str(row["supplier_name"]).casefold(),
        ),
    )


def load_price_source_bytes(access, reference: str | None) -> bytes | None:
    prefix = f"storage://{PRICE_SOURCE_BUCKET}/"
    if not reference or not reference.startswith(prefix):
        return None
    object_path = reference.removeprefix(prefix)
    company_prefix = f"{access.company_id}/"
    if not object_path.startswith(company_prefix):
        raise PermissionError("Price source is not available to this company.")
    client = get_supabase_client()
    assert_company_owner(client, str(access.user_id), str(access.company_id))
    return client.storage.from_(PRICE_SOURCE_BUCKET).download(object_path)


def create_price_source_download_url(
    access,
    reference: str | None,
    *,
    file_name: str,
    expires_in: int = 3600,
) -> str | None:
    """Return a short-lived direct-download URL for an owned source file."""
    prefix = f"storage://{PRICE_SOURCE_BUCKET}/"
    if not reference or not reference.startswith(prefix):
        return None
    object_path = reference.removeprefix(prefix)
    company_prefix = f"{access.company_id}/"
    if not object_path.startswith(company_prefix):
        raise PermissionError("Price source is not available to this company.")
    client = get_supabase_client()
    assert_company_owner(client, str(access.user_id), str(access.company_id))
    response = client.storage.from_(PRICE_SOURCE_BUCKET).create_signed_url(
        object_path,
        expires_in,
        {"download": Path(file_name).name},
    )
    if isinstance(response, dict):
        return response.get("signedURL") or response.get("signed_url")
    return getattr(response, "signedURL", None) or getattr(response, "signed_url", None)


def load_price_source_rows(access, source_id: str) -> list[dict]:
    client = get_supabase_client()
    assert_company_owner(client, str(access.user_id), str(access.company_id))
    return (
        client.table("company_price_source_rows")
        .select("*")
        .eq("company_id", str(access.company_id))
        .eq("source_id", source_id)
        .order("source_row_number")
        .execute()
    ).data or []


def list_unresolved_price_source_rows(access) -> list[dict]:
    """Return reviewable rows from non-archived sources with source context."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    rows = (
        client.table("company_price_source_rows")
        .select("*")
        .eq("company_id", company_id)
        .eq("result_status", "unresolved")
        .order("created_at", desc=True)
        .execute()
    ).data or []
    if not rows:
        return []
    sources = (
        client.table("company_price_sources")
        .select(
            "source_id,source_name,source_kind,source_url,storage_path,mime_type,"
            "category,document_date,currency,status,processing_summary,"
            "company_suppliers(supplier_name)"
        )
        .eq("company_id", company_id)
        .neq("status", "archived")
        .execute()
    ).data or []
    sources_by_id = {str(source["source_id"]): source for source in sources}
    return [
        {**row, "source": sources_by_id[str(row["source_id"])]}
        for row in rows
        if str(row.get("source_id")) in sources_by_id
    ]


def _owned_price_source(client, company_id: str, source_id: str) -> dict:
    rows = (
        client.table("company_price_sources")
        .select("*")
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows or rows[0].get("status") == "archived":
        raise PriceSourceError("Price source not found")
    return rows[0]


def _refresh_price_source_summary(client, company_id: str, source_id: str) -> None:
    source = _owned_price_source(client, company_id, source_id)
    rows = (
        client.table("company_price_source_rows")
        .select("result_status,raw_vat_included,evidence")
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .execute()
    ).data or []
    ready = sum(row.get("result_status") in {"new", "updated"} for row in rows)
    new = sum(
        row.get("result_status") == "new"
        and (row.get("evidence") or {}).get("comparison_status") != "unchanged"
        for row in rows
    )
    unchanged = sum(
        row.get("result_status") in {"new", "updated"}
        and (row.get("evidence") or {}).get("comparison_status") == "unchanged"
        for row in rows
    )
    updated = ready - new - unchanged
    unresolved = sum(row.get("result_status") == "unresolved" for row in rows)
    excluded = sum(row.get("result_status") == "excluded" for row in rows)
    material_types = sorted(
        {
            canonical_price_source_category(str((row.get("evidence") or {}).get("material_type") or "Other"))
            for row in rows
            if row.get("result_status") != "excluded"
        },
        key=str.casefold,
    )
    vat_values = {
        row.get("raw_vat_included")
        for row in rows
        if row.get("result_status") != "excluded"
    }
    vat_mode = (
        "included" if vat_values == {True}
        else "excluded" if vat_values == {False}
        else "unknown" if vat_values in (set(), {None})
        else "mixed"
    )
    summary = dict(source.get("processing_summary") or {})
    summary.update(
        {
            "ready": ready,
            "new": new,
            "updated": updated,
            "unchanged": unchanged,
            "unresolved": unresolved,
            "excluded": excluded,
            "total": len(rows),
            "material_types": material_types,
        }
    )
    category = material_types[0] if len(material_types) == 1 else "Mixed"
    client.table("company_price_sources").update(
        {
            "category": category,
            "vat_mode": vat_mode,
            "status": "ready" if unresolved == 0 else "partial",
            "processing_summary": summary,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("company_id", company_id).eq("source_id", source_id).execute()


def _record_identity_resolution_summary(
    client,
    *,
    company_id: str,
    source_id: str,
    summary: Mapping[str, Any],
) -> None:
    source = _owned_price_source(client, company_id, source_id)
    processing_summary = dict(source.get("processing_summary") or {})
    processing_summary["material_identity"] = dict(summary)
    client.table("company_price_sources").update(
        {"processing_summary": processing_summary}
    ).eq("company_id", company_id).eq("source_id", source_id).execute()


def _resolve_and_record_price_source_identities(
    client,
    *,
    company_id: str,
    source_id: str,
    row_id: str | None = None,
    force: bool = False,
    trace=None,
) -> dict[str, Any]:
    """Run the additive identity stage without invalidating a completed import."""
    try:
        batch = resolve_price_source_material_identities(
            client,
            company_id=company_id,
            source_id=source_id,
            row_id=row_id,
            force=force,
            identity_agent=run_material_identity_agent,
            trace=trace,
        )
        summary: dict[str, Any] = {"status": "complete", **batch.as_summary()}
    except Exception:
        logger.exception("Price source material identity resolution failed")
        summary = {"status": "retry_required"}
    _record_identity_resolution_summary(
        client,
        company_id=company_id,
        source_id=source_id,
        summary=summary,
    )
    return summary


_SOURCE_DEFAULT_RESOLVED_REASONS = {
    "below_auto_activation_threshold",
    "unknown_currency",
    "unknown_vat",
    "vat_basis_unknown",
    "zero_quantity",
}
_SOURCE_DEFAULT_BLOCKING_REASONS = {
    "ambiguous_material",
    "ambiguous_unit",
    "document_total_mismatch",
    "material_type_unresolved",
    "missing_unit",
    "package_conversion_unresolved",
    "unsupported_material",
}
_INTERNAL_NON_MATERIAL_PATTERN = re.compile(
    r"\b(?:assembly|delivery|electricity|grand\s+total|installation|labor|labour|"
    r"margin|markup|overhead|rent|salary|shipping|subtotal|total|wages?|"
    r"амортизация|аренда|доставка|зарплата|итого|маржа|монтаж|накладные|наценка|"
    r"работа|работы|сборка|труд|הרכבה|התקנה|משלוח|עבודה|תקורה)\b",
    re.IGNORECASE,
)


def prepare_internal_estimate_row_defaults(
    row: dict,
    *,
    currency: str,
    vat_mode: str,
) -> dict:
    """Apply confirmed source defaults without hiding unresolved row evidence."""
    prepared = dict(row)
    reasons = set(prepared.get("reason_codes") or [])
    description = " ".join(
        str(prepared.get(key) or "")
        for key in ("raw_description", "normalized_name")
    ).casefold()
    if _INTERNAL_NON_MATERIAL_PATTERN.search(description):
        prepared["result_status"] = "excluded"
        prepared["reason_codes"] = sorted(reasons | {"internal_non_material_cost"})
        return prepared

    if not prepared.get("raw_currency"):
        prepared["raw_currency"] = currency
    if prepared.get("raw_vat_included") is None:
        prepared["raw_vat_included"] = vat_mode == "included"
    reasons -= _SOURCE_DEFAULT_RESOLVED_REASONS
    prepared["reason_codes"] = sorted(reasons)

    evidence = prepared.get("evidence") or {}
    material_type = canonical_price_source_category(
        str(evidence.get("material_type") or "Other")
    )
    purchase_unit = str(prepared.get("purchase_unit") or "")
    calculation_unit = str(prepared.get("calculation_unit") or "")
    try:
        raw_price = float(prepared.get("raw_price") or 0)
        conversion_factor = float(prepared.get("conversion_factor") or 0)
    except (TypeError, ValueError):
        raw_price = 0
        conversion_factor = 0
    can_activate = all(
        (
            raw_price > 0,
            bool(str(prepared.get("normalized_name") or "").strip()),
            bool(str(prepared.get("raw_unit") or "").strip()),
            len(str(prepared.get("raw_currency") or "").strip()) == 3,
            material_type in PRICE_SOURCE_CATEGORIES,
            purchase_unit in CANONICAL_UNIT_CODES - {"unknown", "other"},
            calculation_unit in CANONICAL_UNIT_CODES - {"unknown", "other"},
            conversion_factor > 0,
            not (reasons & _SOURCE_DEFAULT_BLOCKING_REASONS),
        )
    )
    if can_activate:
        prepared["normalized_price"] = raw_price / conversion_factor
        prepared["normalized_unit"] = calculation_unit
        prepared["result_status"] = "ready"
    else:
        prepared["result_status"] = "unresolved"
    return prepared


def apply_price_source_defaults(
    access,
    source_id: str,
    *,
    currency: str,
    vat_mode: str,
) -> dict[str, int]:
    """Confirm one internal source's currency and VAT, then activate safe rows."""
    normalized_currency = currency.strip().upper()
    if len(normalized_currency) != 3:
        raise PriceSourceError("Enter a three-letter currency code")
    if vat_mode not in {"included", "excluded"}:
        raise PriceSourceError("Choose whether VAT is included")

    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    source = _owned_price_source(client, company_id, source_id)
    summary = dict(source.get("processing_summary") or {})
    if summary.get("source_origin") != "company_internal":
        raise PriceSourceError("Source defaults are available for internal estimates")
    rows = (
        client.table("company_price_source_rows")
        .select("*")
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .order("source_row_number")
        .execute()
    ).data or []
    prepared_rows = [
        prepare_internal_estimate_row_defaults(
            row,
            currency=normalized_currency,
            vat_mode=vat_mode,
        )
        for row in rows
    ]
    ready_rows = [row for row in prepared_rows if row["result_status"] == "ready"]

    materials = (
        client.table("company_material_items")
        .select("company_material_id,category,normalized_name,status")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    material_by_identity = {
        (str(item.get("category") or ""), str(item.get("normalized_name") or "")):
        item["company_material_id"]
        for item in materials
    }
    archived_material_ids = {
        str(item["company_material_id"])
        for item in materials
        if item.get("status") == "archived"
    }
    missing_materials: dict[tuple[str, str], dict] = {}
    for row in ready_rows:
        evidence = dict(row.get("evidence") or {})
        category = canonical_price_source_category(
            str(evidence.get("material_type") or "Other")
        )
        normalized_name = _normalized_name(str(row.get("normalized_name") or ""))
        identity = (category, normalized_name)
        if identity not in material_by_identity:
            missing_materials.setdefault(
                identity,
                {
                    "company_id": company_id,
                    "category": category,
                    "canonical_name": str(row["normalized_name"]),
                    "normalized_name": normalized_name,
                    "preferred_unit": row["calculation_unit"],
                    "created_from_source_id": source_id,
                },
            )
    if missing_materials:
        inserted = client.table("company_material_items").upsert(
            list(missing_materials.values()),
            on_conflict="company_id,category,normalized_name",
        ).execute().data or []
        material_by_identity.update(
            {
                (str(item["category"]), str(item["normalized_name"])):
                item["company_material_id"]
                for item in inserted
            }
        )
        if any(identity not in material_by_identity for identity in missing_materials):
            refreshed_materials = (
                client.table("company_material_items")
                .select("company_material_id,category,normalized_name,status")
                .eq("company_id", company_id)
                .execute()
            ).data or []
            material_by_identity.update(
                {
                    (str(item["category"]), str(item["normalized_name"])):
                    item["company_material_id"]
                    for item in refreshed_materials
                }
            )
    reused_archived_ids = {
        str(material_by_identity[
            (
                canonical_price_source_category(
                    str((row.get("evidence") or {}).get("material_type") or "Other")
                ),
                _normalized_name(str(row.get("normalized_name") or "")),
            )
        ])
        for row in ready_rows
    } & archived_material_ids
    if reused_archived_ids:
        client.table("company_material_items").update({"status": "private"}).in_(
            "company_material_id", sorted(reused_archived_ids)
        ).execute()

    active_offers = (
        client.table("company_material_offers")
        .select(
            "offer_id,company_material_id,supplier_id,source_id,supplier_sku,"
            "source_price,source_unit,purchase_unit,calculation_unit,conversion_factor,"
            "normalized_price,currency,vat_included,status"
        )
        .eq("company_id", company_id)
        .eq("status", "active")
        .execute()
    ).data or []
    offer_sources = (
        client.table("company_price_sources")
        .select("source_id,supplier_id,processing_summary")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    source_by_id = {str(item["source_id"]): item for item in offer_sources}
    current_lane = price_offer_lane_key(
        supplier_id=source.get("supplier_id"),
        source_summary=summary,
        source_id=source_id,
    )
    offers_by_identity: dict[tuple[str, str], list[dict]] = {}
    for offer in active_offers:
        offer_source = source_by_id.get(str(offer.get("source_id") or ""), {})
        lane = price_offer_lane_key(
            supplier_id=offer_source.get("supplier_id") or offer.get("supplier_id"),
            source_summary=offer_source.get("processing_summary"),
            source_id=offer.get("source_id"),
        )
        offers_by_identity.setdefault(
            (str(offer.get("company_material_id") or ""), lane), []
        ).append(offer)

    offers_to_supersede: set[str] = set()
    offers_to_insert: list[dict] = []
    activated = 0
    unchanged = 0
    for row in ready_rows:
        evidence = dict(row.get("evidence") or {})
        category = canonical_price_source_category(
            str(evidence.get("material_type") or "Other")
        )
        identity = (category, _normalized_name(str(row.get("normalized_name") or "")))
        material_id = material_by_identity[identity]
        row["company_material_id"] = material_id
        matching = offers_by_identity.get((str(material_id), current_lane), [])
        comparison_row = {
            "raw_price": row.get("raw_price"),
            "raw_currency": row.get("raw_currency"),
            "raw_unit": row.get("raw_unit"),
            "raw_vat_mode": vat_mode,
            "purchase_unit": row.get("purchase_unit"),
            "calculation_unit": row.get("calculation_unit"),
            "conversion_factor": row.get("conversion_factor"),
            "normalized_price": row.get("normalized_price"),
        }
        is_unchanged = any(
            price_offer_matches_row(
                offer,
                comparison_row,
                default_currency=normalized_currency,
            )
            for offer in matching
        )
        comparison_status = "unchanged" if is_unchanged else (
            "updated" if matching else "new"
        )
        evidence["comparison_status"] = comparison_status
        row["evidence"] = evidence
        row["result_status"] = "updated" if is_unchanged else comparison_status
        if is_unchanged:
            unchanged += 1
            continue
        offers_to_supersede.update(str(offer["offer_id"]) for offer in matching)
        offers_to_insert.append(
            {
                "company_id": company_id,
                "company_material_id": material_id,
                "supplier_id": source.get("supplier_id"),
                "source_id": source_id,
                "source_row_id": row["row_id"],
                "supplier_sku": row.get("raw_sku"),
                "source_price": row["raw_price"],
                "source_unit": row["raw_unit"],
                "purchase_unit": row["purchase_unit"],
                "calculation_unit": row["calculation_unit"],
                "conversion_factor": row["conversion_factor"],
                "normalized_price": row["normalized_price"],
                "normalized_unit": row["calculation_unit"],
                "currency": normalized_currency,
                "vat_included": vat_mode == "included",
                "valid_from": source.get("document_date"),
                "confidence": row.get("confidence") or 0,
            }
        )
        activated += 1

    if offers_to_supersede:
        client.table("company_material_offers").update({"status": "superseded"}).in_(
            "offer_id", sorted(offers_to_supersede)
        ).execute()
    if offers_to_insert:
        client.table("company_material_offers").insert(offers_to_insert).execute()
    if prepared_rows:
        client.table("company_price_source_rows").upsert(
            prepared_rows,
            on_conflict="row_id",
        ).execute()
    client.table("company_price_sources").update(
        {
            "currency": normalized_currency,
            "vat_mode": vat_mode,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("company_id", company_id).eq("source_id", source_id).execute()
    _resolve_and_record_price_source_identities(
        client,
        company_id=company_id,
        source_id=source_id,
    )
    _refresh_price_source_summary(client, company_id, source_id)
    return {
        "activated": activated,
        "unchanged": unchanged,
        "unresolved": sum(row["result_status"] == "unresolved" for row in prepared_rows),
        "excluded": sum(row["result_status"] == "excluded" for row in prepared_rows),
    }


def save_price_source_row(access, source_id: str, row_id: str, values: dict) -> dict:
    """Validate a reviewed row, activate its offer, and retain its source evidence."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    source = _owned_price_source(client, company_id, source_id)
    matches = (
        client.table("company_price_source_rows")
        .select("*")
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .eq("row_id", row_id)
        .limit(1)
        .execute()
    ).data or []
    if not matches:
        raise PriceSourceError("Price row not found")
    row = matches[0]

    normalized_name = str(values.get("normalized_name") or "").strip()
    material_type = canonical_price_source_category(str(values.get("material_type") or ""))
    raw_unit = str(values.get("raw_unit") or "").strip()
    raw_currency = str(values.get("raw_currency") or source.get("currency") or "ILS").strip().upper()
    purchase_unit = str(values.get("purchase_unit") or "").strip()
    calculation_unit = str(values.get("calculation_unit") or "").strip()
    vat_mode = str(values.get("vat_mode") or "unknown")
    try:
        raw_price = float(values.get("raw_price") or 0)
        conversion_factor = float(values.get("conversion_factor") or 0)
    except (TypeError, ValueError) as exc:
        raise PriceSourceError("Enter a valid price and conversion quantity") from exc
    if not normalized_name:
        raise PriceSourceError("Enter a material name")
    if material_type not in PRICE_SOURCE_CATEGORIES:
        raise PriceSourceError("Choose a material type")
    if raw_price <= 0:
        raise PriceSourceError("Enter a positive price")
    if len(raw_currency) != 3:
        raise PriceSourceError("Enter a three-letter currency code")
    if not raw_unit:
        raise PriceSourceError("Enter the source unit")
    if purchase_unit not in CANONICAL_UNIT_CODES or purchase_unit in {"unknown", "other"}:
        raise PriceSourceError("Choose the purchase unit")
    if calculation_unit not in CANONICAL_UNIT_CODES or calculation_unit in {"unknown", "other"}:
        raise PriceSourceError("Choose the calculation unit")
    if conversion_factor <= 0:
        raise PriceSourceError("Enter a positive conversion quantity")
    if vat_mode not in {"included", "excluded"}:
        raise PriceSourceError("Choose whether VAT is included")

    normalized_price = raw_price / conversion_factor
    normalized_key = _normalized_name(normalized_name)
    existing = (
        client.table("company_material_items")
        .select("company_material_id")
        .eq("company_id", company_id)
        .eq("category", material_type)
        .eq("normalized_name", normalized_key)
        .limit(1)
        .execute()
    ).data or []
    source_lane = price_offer_lane_key(
        supplier_id=source.get("supplier_id"),
        source_summary=source.get("processing_summary"),
        source_id=source_id,
    )
    active_material_offers = []
    if existing:
        material_id = existing[0]["company_material_id"]
        active_material_offers = (
            client.table("company_material_offers")
            .select("offer_id,source_id,source_row_id")
            .eq("company_id", company_id)
            .eq("company_material_id", material_id)
            .eq("status", "active")
            .execute()
        ).data or []
        offer_source_ids = {
            str(offer.get("source_id") or "") for offer in active_material_offers
        }
        offer_sources = (
            client.table("company_price_sources")
            .select("source_id,supplier_id,status,processing_summary")
            .eq("company_id", company_id)
            .execute()
        ).data or []
        source_by_id = {
            str(candidate.get("source_id") or ""): candidate
            for candidate in offer_sources
            if str(candidate.get("source_id") or "") in offer_source_ids
        }
        matching_lane_offers = [
            offer
            for offer in active_material_offers
            if price_offer_lane_key(
                supplier_id=(source_by_id.get(str(offer.get("source_id") or "")) or {}).get(
                    "supplier_id"
                ),
                source_summary=(
                    source_by_id.get(str(offer.get("source_id") or "")) or {}
                ).get("processing_summary"),
                source_id=offer.get("source_id"),
            )
            == source_lane
        ]
        result_status = "updated" if matching_lane_offers else "new"
    else:
        material = client.table("company_material_items").insert(
            {
                "company_id": company_id,
                "category": material_type,
                "canonical_name": normalized_name,
                "normalized_name": normalized_key,
                "preferred_unit": calculation_unit,
                "created_from_source_id": source_id,
            }
        ).execute().data[0]
        material_id = material["company_material_id"]
        result_status = "new"

    for previous_offer in matching_lane_offers if existing else []:
        client.table("company_material_offers").update({"status": "superseded"}).eq(
            "offer_id", previous_offer["offer_id"]
        ).execute()
    evidence = dict(row.get("evidence") or {})
    evidence["material_type"] = material_type
    evidence["item_kind"] = "material"
    evidence["comparison_status"] = result_status
    resolved_codes = {
        "below_auto_activation_threshold",
        "material_type_unresolved",
        "internal_price_lane_pending",
        "package_conversion_unresolved",
        "vat_basis_unknown",
    }
    reason_codes = sorted(
        (set(row.get("reason_codes") or []) - resolved_codes) | {"reviewed_by_user"}
    )
    updated = client.table("company_price_source_rows").update(
        {
            "raw_price": raw_price,
            "raw_currency": raw_currency,
            "raw_unit": raw_unit,
            "raw_vat_included": vat_mode == "included",
            "normalized_name": normalized_name,
            "normalized_price": normalized_price,
            "purchase_unit": purchase_unit,
            "calculation_unit": calculation_unit,
            "conversion_factor": conversion_factor,
            "normalized_unit": calculation_unit,
            "conversion_basis": {"description": "Reviewed by company owner"},
            "company_material_id": material_id,
            "result_status": result_status,
            "reason_codes": reason_codes,
            "evidence": evidence,
        }
    ).eq("company_id", company_id).eq("source_id", source_id).eq("row_id", row_id).execute().data[0]
    client.table("company_material_offers").insert(
        {
            "company_id": company_id,
            "company_material_id": material_id,
            "supplier_id": source.get("supplier_id"),
            "source_id": source_id,
            "source_row_id": row_id,
            "supplier_sku": row.get("raw_sku"),
            "source_price": raw_price,
            "source_unit": raw_unit,
            "purchase_unit": purchase_unit,
            "calculation_unit": calculation_unit,
            "conversion_factor": conversion_factor,
            "normalized_price": normalized_price,
            "normalized_unit": calculation_unit,
            "currency": raw_currency,
            "vat_included": vat_mode == "included",
            "valid_from": source.get("document_date"),
            "confidence": row.get("confidence") or 0,
        }
    ).execute()
    _resolve_and_record_price_source_identities(
        client,
        company_id=company_id,
        source_id=source_id,
        row_id=row_id,
        force=True,
    )
    if not source.get("currency"):
        client.table("company_price_sources").update({"currency": raw_currency}).eq(
            "company_id", company_id
        ).eq("source_id", source_id).execute()
    _refresh_price_source_summary(client, company_id, source_id)
    return updated


def remove_price_source_row(access, source_id: str, row_id: str) -> None:
    """Remove one offer from active pricing while retaining its audit record."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    _owned_price_source(client, company_id, source_id)
    matches = (
        client.table("company_price_source_rows")
        .select("reason_codes")
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .eq("row_id", row_id)
        .limit(1)
        .execute()
    ).data or []
    if not matches:
        raise PriceSourceError("Price row not found")
    client.table("company_material_offers").update({"status": "archived"}).eq(
        "company_id", company_id
    ).eq("source_row_id", row_id).neq("status", "archived").execute()
    reason_codes = sorted(set((matches[0].get("reason_codes") or []) + ["removed_by_user"]))
    client.table("company_price_source_rows").update(
        {"result_status": "excluded", "reason_codes": reason_codes}
    ).eq("company_id", company_id).eq("source_id", source_id).eq("row_id", row_id).execute()
    _refresh_price_source_summary(client, company_id, source_id)


def archive_price_source(access, source_id: str) -> dict[str, int]:
    """Remove one source from active company pricing while preserving its audit."""
    client = get_supabase_client()
    company_id = str(access.company_id)
    assert_company_owner(client, str(access.user_id), company_id)
    _owned_price_source(client, company_id, source_id)
    result = client.rpc(
        "archive_company_price_source",
        {
            "p_company_id": company_id,
            "p_source_id": source_id,
        },
    ).execute().data
    if isinstance(result, list):
        result = result[0] if result else {}
    if not isinstance(result, dict):
        result = {}
    return {
        "archived_offers": int(result.get("archived_offers") or 0),
        "archived_materials": int(result.get("archived_materials") or 0),
    }


def process_price_source(
    access,
    *,
    department: str,
    uploaded_file=None,
    source_url: str = "",
    trace=None,
    client=None,
    owner_authorized: bool = False,
) -> PriceSourceProcessResult:
    """Process and persist one source. Ambiguous rows stay non-active."""
    process_started = time.perf_counter()
    department = _validate_department(department)
    if (uploaded_file is None) == (not source_url.strip()):
        raise PriceSourceError("Add one file or one supplier URL.")

    company_id = str(access.company_id)
    client = client or get_supabase_client()
    _emit_marker(
        trace,
        "server.price_source_process_started",
        source_kind="file" if uploaded_file is not None else "url",
    )
    if not owner_authorized:
        assert_company_owner(client, str(access.user_id), company_id)
    source_id = str(uuid4())

    if uploaded_file is not None:
        _emit_marker(trace, "server.price_source_input_read_started", source_kind="file")
        source_read_started = time.perf_counter()
        source_name = str(uploaded_file.name)
        suffix = _source_extension(source_name)
        source_bytes = uploaded_file.getvalue()
        if not source_bytes or len(source_bytes) > MAX_SOURCE_BYTES:
            raise PriceSourceError("The price source must be between 1 byte and 50 MB")
        source_kind = "file"
        resolved_url = None
        _emit_duration(
            trace,
            "server.price_source_read",
            source_read_started,
            source_bytes=len(source_bytes),
        )
        parse_started = time.perf_counter()
        structured_text = extract_spreadsheet_text(source_name, source_bytes)
        template_sha256 = price_source_template_fingerprint(source_name, source_bytes)
        _emit_duration(
            trace,
            "server.price_source_spreadsheet_parse",
            parse_started,
            extracted_chars=len(structured_text),
        )
        mime_type = CONTENT_TYPES[suffix]
    else:
        _emit_marker(trace, "server.price_source_input_read_started", source_kind="url")
        fetch_started = time.perf_counter()
        resolved_url, source_bytes, structured_text = fetch_public_page(source_url)
        _emit_duration(
            trace,
            "server.price_source_url_fetch",
            fetch_started,
            source_bytes=len(source_bytes),
            extracted_chars=len(structured_text),
        )
        source_name = resolved_url
        source_kind = "url"
        suffix = ".html"
        mime_type = "text/html"
        template_sha256 = None

    source_digest = sha256(source_bytes).hexdigest()
    _emit_marker(trace, "server.price_source_duplicate_check_started")
    duplicate = (
        client.table("company_price_sources")
        .select("source_id,processing_summary")
        .eq("company_id", company_id)
        .eq("source_sha256", source_digest)
        .neq("status", "archived")
        .limit(1)
        .execute()
    ).data or []
    if duplicate:
        _emit_marker(trace, "server.price_source_duplicate_found")
        duplicate_summary = _unchanged_duplicate_summary(duplicate[0])
        duplicate_summary["processing_duration_seconds"] = time.perf_counter() - process_started
        return PriceSourceProcessResult(
            source_id=str(duplicate[0]["source_id"]),
            summary=duplicate_summary,
        )

    text_layer_started = time.perf_counter()
    _emit_marker(trace, "server.price_source_text_layer_started", suffix=suffix)
    try:
        text_layer = prepare_price_source_text_layer(
            file_name=source_name,
            file_bytes=source_bytes,
            structured_text=structured_text,
        )
    except Exception as exc:
        _emit_duration(
            trace,
            "server.price_source_text_layer_failed",
            text_layer_started,
            suffix=suffix,
            error_type=type(exc).__name__,
        )
        raise PriceSourceError(f"Price source OCR failed: {exc}") from exc
    _emit_duration(
        trace,
        "server.price_source_text_layer",
        text_layer_started,
        strategy=text_layer.strategy,
        extracted_chars=len(text_layer.text),
        ocr_pages=len((text_layer.ocr_package or {}).get("pages") or []),
    )
    if text_layer.ocr_package:
        ocr_package = text_layer.ocr_package
        try:
            insert_agent_usage_event(
                client,
                {
                    "company_id": company_id,
                    "run_id": source_id,
                    "file_name": source_name,
                    "object_id": None,
                    "object_name": None,
                    "agent_name": "ocr",
                    "operation": "company_price_source_ocr",
                    "model": str(ocr_package.get("model") or "unknown"),
                    "prompt_version": str(ocr_package.get("contract_version") or "ocr_v2"),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": "succeeded",
                    "duration_seconds": float(ocr_package.get("processing_seconds") or 0),
                    "started_at": str(ocr_package.get("started_at") or datetime.now(timezone.utc).isoformat()),
                    "finished_at": str(ocr_package.get("finished_at") or datetime.now(timezone.utc).isoformat()),
                    "raw_usage": {
                        "provider_usage": dict(ocr_package.get("usage") or {}),
                        "ocr_result": ocr_package,
                        "text_layer_strategy": text_layer.strategy,
                    },
                },
            )
        except Exception:
            logger.exception("Price source OCR usage persistence failed")

    agent_started = time.perf_counter()
    _emit_marker(trace, "server.price_source_agent_started")
    result = run_price_source_agent(
        company_id=company_id,
        department=department,
        source_name=source_name,
        source_kind=source_kind,
        # The commercial agent receives an auditable text layer only.  This
        # keeps image/scanned-PDF interpretation in the dedicated OCR stage.
        source_bytes=None,
        extracted_text=text_layer.text,
        import_id=source_id,
        trace=trace,
    )
    normalize_price_source_sheet_rows(result)
    discarded_non_candidates = discard_price_source_non_candidates(result)
    discarded_consumables = discard_price_source_consumables(result)
    operation_code_by_row_number = prepare_price_source_operation_rows(result)
    guard_price_source_department(result, department)
    material_types = price_source_material_types(result)
    category = material_types[0] if len(material_types) == 1 else "Mixed"
    semantic_sha256 = price_source_semantic_fingerprint(result)
    source_family_sha256, source_family_code = price_source_family_identity(
        result,
        source_name=source_name,
        source_kind=source_kind,
        template_sha256=template_sha256,
    )
    _emit_duration(
        trace,
        "server.price_source_agent",
        agent_started,
        extracted_rows=len(result.get("rows") or []),
    )
    usage_event = result.pop("_agent_usage", None)
    extraction_diagnostics = price_source_extraction_diagnostics(
        result,
        text_layer_strategy=text_layer.strategy,
        text_layer_characters=len(text_layer.text),
        ocr_pages=len((text_layer.ocr_package or {}).get("pages") or []),
    )
    if usage_event:
        raw_usage = dict(usage_event.get("raw_usage") or {})
        raw_usage["price_source_extraction"] = extraction_diagnostics
        usage_event["raw_usage"] = raw_usage
        usage_started = time.perf_counter()
        try:
            insert_agent_usage_event(client, usage_event)
        except Exception:
            logger.exception("Price source agent usage persistence failed")
        _emit_duration(trace, "server.price_source_usage_persist", usage_started)
    if not result.get("rows"):
        _emit_marker(trace, "server.price_source_agent_zero_rows", **extraction_diagnostics)
        raise PriceSourceError(
            "No priced rows were extracted from this source. "
            "The OCR and agent diagnostics were saved for analysis."
        )
    previous_revision, source_revision = _find_previous_source_revision(
        client,
        company_id,
        family_sha256=source_family_sha256,
        semantic_sha256=semantic_sha256,
    )

    benchmark_started = time.perf_counter()
    legacy_materials = (
        client.table("materials")
        .select("material_name,price,price_unit")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    apply_legacy_price_benchmark(result, legacy_materials)
    _emit_duration(
        trace,
        "server.price_source_legacy_benchmark",
        benchmark_started,
        benchmark_rows=len(legacy_materials),
    )
    object_path = f"{company_id}/{source_id}{suffix}"
    storage_started = time.perf_counter()
    _emit_marker(trace, "server.price_source_storage_started")
    client.storage.from_(PRICE_SOURCE_BUCKET).upload(
        object_path,
        source_bytes,
        file_options={"content-type": mime_type, "upsert": "false"},
    )
    _emit_duration(
        trace,
        "server.price_source_storage_upload",
        storage_started,
        source_bytes=len(source_bytes),
    )

    superseded_offer_ids: list[str] = []
    try:
        database_started = time.perf_counter()
        _emit_marker(trace, "server.price_source_database_started")
        source_record_started = time.perf_counter()
        supplier_name = price_source_supplier_name(result)
        supplier_hp = str(result.get("supplier_hp") or "").strip()
        supplier_id = None
        if supplier_name:
            existing_suppliers = (
                client.table("company_suppliers")
                .select("supplier_id,supplier_name,normalized_name,supplier_hp,categories,created_at")
                .eq("company_id", company_id)
                .execute()
            ).data or []
            matched_supplier = match_existing_supplier(
                supplier_name, existing_suppliers, supplier_hp=supplier_hp,
            )
            canonical_supplier_name = clean_supplier_name(
                (matched_supplier or {}).get("supplier_name") or supplier_name
            )
            canonical_supplier_key = supplier_merge_key(canonical_supplier_name)
            categories = sorted(
                set(((matched_supplier or {}).get("categories") or []) + material_types)
            ) if matched_supplier else material_types
            supplier_payload = {
                "company_id": company_id,
                "supplier_name": canonical_supplier_name,
                "normalized_name": canonical_supplier_key,
                "supplier_hp": supplier_hp or (matched_supplier or {}).get("supplier_hp") or None,
                "categories": categories,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if matched_supplier:
                # Keep the first accepted supplier as the canonical row even
                # when its old normalized key still contained OCR legal noise.
                supplier_row = (
                    client.table("company_suppliers")
                    .update(supplier_payload)
                    .eq("supplier_id", matched_supplier["supplier_id"])
                    .execute()
                ).data[0]
            else:
                supplier_row = (
                    client.table("company_suppliers")
                    .upsert(supplier_payload, on_conflict="company_id,normalized_name")
                    .execute()
                ).data[0]
            supplier_id = supplier_row["supplier_id"]
        ready_count = sum(row["status"] == "ready" for row in result["rows"])
        unresolved_count = sum(row["status"] == "unresolved" for row in result["rows"])
        excluded_count = sum(row["status"] == "excluded" for row in result["rows"])
        new_count = 0
        updated_count = 0
        unchanged_count = 0
        status = "ready" if not unresolved_count else "partial"
        source_summary = {
            "ready": ready_count,
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "unresolved": unresolved_count,
            "excluded": excluded_count,
            "discarded_non_candidates": discarded_non_candidates,
            "discarded_consumables": discarded_consumables,
            "operation_services": len(operation_code_by_row_number),
            "total": len(result["rows"]),
            "document_number": result["document_number"],
            "supplier_hp": supplier_hp or None,
            "source_origin": result["source_origin"],
            "price_context": result["price_context"],
            "document_subtotal": result["document_subtotal"],
            "document_vat_amount": result["document_vat_amount"],
            "document_total": result["document_total"],
            "material_types": material_types,
            "semantic_sha256": semantic_sha256,
            "template_sha256": template_sha256,
            "source_family_sha256": source_family_sha256,
            "source_family_code": source_family_code,
            "source_revision": source_revision,
            "previous_source_id": (
                str(previous_revision.get("source_id")) if previous_revision else None
            ),
            "agent_duration_seconds": (
                usage_event.get("duration_seconds") if usage_event else None
            ),
            "token_cost": usage_event.get("total_cost_usd") if usage_event else None,
            "input_tokens": usage_event.get("input_tokens") if usage_event else None,
            "output_tokens": usage_event.get("output_tokens") if usage_event else None,
            "model": usage_event.get("model") if usage_event else None,
            "prompt_version": usage_event.get("prompt_version") if usage_event else None,
            "text_layer": {
                "strategy": text_layer.strategy,
                "characters": len(text_layer.text),
                "ocr_pages": len((text_layer.ocr_package or {}).get("pages") or []),
                "ocr_seconds": float((text_layer.ocr_package or {}).get("processing_seconds") or 0),
                "ocr_model": (text_layer.ocr_package or {}).get("model"),
            },
        }
        client.table("company_price_sources").insert(
            {
                "source_id": source_id,
                "company_id": company_id,
                "supplier_id": supplier_id,
                "source_supplier_name": supplier_name or None,
                "category": category,
                "source_kind": source_kind,
                "source_name": source_name,
                "source_url": resolved_url,
                "storage_path": f"storage://{PRICE_SOURCE_BUCKET}/{object_path}",
                "mime_type": mime_type,
                "source_sha256": source_digest,
                "document_type": result["document_type"],
                "document_date": _date_or_none(result["document_date"]),
                "currency": result["currency"] or None,
                "vat_mode": result["vat_mode"],
                "status": status,
                "processing_summary": source_summary,
                "created_by": str(access.user_id),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        _emit_duration(trace, "server.price_source_database_source_record", source_record_started)
        if supplier_id and supplier_name:
            client.table("company_supplier_aliases").upsert(
                {
                    "company_id": company_id,
                    "supplier_id": supplier_id,
                    "alias_name": supplier_name,
                    "normalized_name": _normalized_name(supplier_name),
                    "alias_kind": "source_observed",
                    "source_id": source_id,
                },
                on_conflict="company_id,normalized_name",
            ).execute()

        operation_ids_by_code = {
            str(row["operation_code"]): str(row["operation_id"])
            for row in (
                client.table("reference_operations")
                .select("operation_id,operation_code")
                .in_("operation_code", sorted(set(operation_code_by_row_number.values())))
                .execute().data or []
            )
        } if operation_code_by_row_number else {}
        if set(operation_code_by_row_number.values()) - set(operation_ids_by_code):
            raise RuntimeError("Prepared supplier operation is missing from the reference catalog")

        offer_index_started = time.perf_counter()
        active_offers = (
            client.table("company_material_offers")
            .select(
                "offer_id,company_material_id,supplier_id,source_id,supplier_sku,source_price,source_unit,"
                "purchase_unit,calculation_unit,conversion_factor,normalized_price,"
                "currency,vat_included,status"
            )
            .eq("company_id", company_id)
            .eq("status", "active")
            .execute()
        ).data or []
        offer_sources = (
            client.table("company_price_sources")
            .select("source_id,supplier_id,status,processing_summary")
            .eq("company_id", company_id)
            .execute()
        ).data or []
        source_by_id = {
            str(candidate.get("source_id") or ""): candidate
            for candidate in offer_sources
        }
        active_operation_offers = (
            client.table("company_supplier_operation_offers")
            .select(
                "operation_offer_id,operation_id,supplier_id,source_id,source_price,"
                "pricing_basis,source_unit_label,currency,vat_included,status"
            )
            .eq("company_id", company_id)
            .eq("status", "active")
            .execute()
            .data
            or []
        )
        current_lane = price_offer_lane_key(
            supplier_id=supplier_id,
            source_summary=source_summary,
            source_id=source_id,
        )
        offers_by_identity: dict[tuple[str, str], list[dict]] = {}
        offers_by_sku: dict[tuple[str, str], list[dict]] = {}
        material_ids_to_restore: set[str] = set()
        for offer in active_offers:
            offer_source = source_by_id.get(str(offer.get("source_id") or ""), {})
            offer_lane = price_offer_lane_key(
                supplier_id=offer_source.get("supplier_id") or offer.get("supplier_id"),
                source_summary=offer_source.get("processing_summary"),
                source_id=offer.get("source_id"),
            )
            identity = (
                str(offer.get("company_material_id") or ""),
                offer_lane,
            )
            offers_by_identity.setdefault(identity, []).append(offer)
            sku = _normalized_name(str(offer.get("supplier_sku") or ""))
            if sku:
                offers_by_sku.setdefault((offer_lane, sku), []).append(
                    offer
                )
        operation_offers_by_identity: dict[tuple[str, str], list[dict]] = {}
        for offer in active_operation_offers:
            offer_source = source_by_id.get(str(offer.get("source_id") or ""), {})
            # A deleted source must not silently suppress a new visible job.
            # Older archive RPCs left operation offers active, so ignore those
            # stale records even before the repaired archive function runs.
            if offer_source.get("status") == "archived":
                continue
            offer_lane = price_offer_lane_key(
                supplier_id=offer_source.get("supplier_id") or offer.get("supplier_id"),
                source_summary=offer_source.get("processing_summary"),
                source_id=offer.get("source_id"),
            )
            identity = (str(offer.get("operation_id") or ""), offer_lane)
            operation_offers_by_identity.setdefault(identity, []).append(offer)

        _emit_duration(
            trace,
            "server.price_source_database_offer_index",
            offer_index_started,
            active_offers=len(active_offers),
            active_operation_offers=len(active_operation_offers),
            source_count=len(offer_sources),
        )

        material_index_started = time.perf_counter()
        current_lane_material_ids = sorted(
            {
                str(offer.get("company_material_id") or "")
                for identity, candidates in offers_by_identity.items()
                if identity[1] == current_lane
                for offer in candidates
                if str(offer.get("company_material_id") or "")
            }
        )
        current_lane_materials = (
            client.table("company_material_items")
            .select(
                "company_material_id,status,category,canonical_name,normalized_name,specifications"
            )
            .eq("company_id", company_id)
            .in_("company_material_id", current_lane_material_ids)
            .execute()
            .data
            or []
        ) if current_lane_material_ids else []
        material_by_id = {
            str(material.get("company_material_id")): material
            for material in current_lane_materials
            if material.get("company_material_id")
        }
        # A brand-only row is normally Review.  The one safe exception is a
        # prior offer from this same canonical supplier that proves the SKU,
        # price, unit, VAT and structure already map to one material family.
        for row in result["rows"]:
            if (
                row.get("item_kind") != "material"
                or row.get("status") != "unresolved"
                or "unknown_material_family" not in (row.get("reason_codes") or [])
            ):
                continue
            sku = _normalized_name(str(row.get("raw_sku") or ""))
            if not sku:
                continue
            candidates: dict[str, tuple[dict, str]] = {}
            for offer in offers_by_sku.get((current_lane, sku), []):
                material = material_by_id.get(str(offer.get("company_material_id") or ""))
                if not material or canonical_price_source_category(
                    str(material.get("category") or "")
                ) != canonical_price_source_category(str(row.get("material_type") or "")):
                    continue
                family = material_offer_proves_unknown_family(
                    offer, material, row,
                    default_currency=str(result.get("currency") or ""),
                )
                if family:
                    candidates[str(material["company_material_id"])] = (material, family)
            if len(candidates) == 1:
                _, family = next(iter(candidates.values()))
                row["material_family"] = family
                row["status"] = "ready"
                row["reason_codes"] = sorted(
                    (set(row.get("reason_codes") or set()) - {"unknown_material_family"})
                    | {"family_inherited_from_supplier_offer"}
                )

        ready_material_keys = {
            (
                canonical_price_source_category(str(row["material_type"])),
                material_structural_key(row),
            )
            for row in result["rows"]
            if row["status"] == "ready" and row["item_kind"] == "material"
        }
        existing_material_rows = (
            client.table("company_material_items")
            .select("company_material_id,status,category,canonical_name,normalized_name,specifications")
            .eq("company_id", company_id)
            .execute()
            .data
            or []
        ) if ready_material_keys else []
        material_by_id.update({
            str(material.get("company_material_id")): material
            for material in existing_material_rows
            if material.get("company_material_id")
        })
        materials_by_key: dict[tuple[str, tuple[str, str, str, str, str, str]], dict] = {}
        for material in existing_material_rows:
            specifications = material.get("specifications") or {}
            key = (
                canonical_price_source_category(str(material.get("category") or "")),
                material_structural_key({
                    "material_family": specifications.get("material_family") or "",
                    "identity_attributes": specifications,
                }),
            )
            if key in ready_material_keys and key not in materials_by_key:
                materials_by_key[key] = material

        inferred_material_by_row_number: dict[int, dict] = {}
        for row in result["rows"]:
            if row["status"] != "ready" or row["item_kind"] != "material":
                continue
            candidates = []
            for identity, offers in offers_by_identity.items():
                if identity[1] != current_lane:
                    continue
                material = material_by_id.get(identity[0])
                if not material or canonical_price_source_category(
                    str(material.get("category") or "")
                ) != canonical_price_source_category(str(row["material_type"])):
                    continue
                if any(
                    material_offer_matches_extracted_row(
                        offer,
                        material,
                        row,
                        default_currency=str(result.get("currency") or ""),
                    ) or material_offer_matches_same_supplier_description(
                        offer,
                        material,
                        row,
                        default_currency=str(result.get("currency") or ""),
                    )
                    for offer in offers
                ):
                    candidates.append(material)
            unique_candidates = {
                str(material["company_material_id"]): material for material in candidates
            }
            if len(unique_candidates) == 1:
                inferred_material_by_row_number[int(row["source_row_number"])] = next(
                    iter(unique_candidates.values())
                )

        new_material_payloads: list[dict] = []
        for row in result["rows"]:
            if row["status"] != "ready" or row["item_kind"] != "material":
                continue
            if int(row["source_row_number"]) in inferred_material_by_row_number:
                continue
            key = (
                canonical_price_source_category(str(row["material_type"])),
                material_structural_key(row),
            )
            if key in materials_by_key:
                continue
            identity_attributes = {
                attribute: value
                for attribute, value in (row.get("identity_attributes") or {}).items()
                if value not in (None, "", 0, 0.0, [])
            }
            identity_attributes["material_family"] = str(row.get("material_family") or "")
            identity_attributes["source_description_key"] = material_source_description_key(row)
            new_material_payloads.append(
                {
                    "company_id": company_id,
                    "category": key[0],
                    "canonical_name": row["normalized_name"],
                    "normalized_name": key[1],
                    "preferred_unit": row["calculation_unit"],
                    "specifications": identity_attributes,
                    "created_from_source_id": source_id,
                }
            )
            # Reserve the key now so duplicate rows from one source still share
            # one private material, as they did in the sequential path.
            materials_by_key[key] = {}
        if new_material_payloads:
            created_materials = (
                client.table("company_material_items")
                .insert(new_material_payloads)
                .execute()
                .data
                or []
            )
            for material in created_materials:
                key = (
                    canonical_price_source_category(str(material.get("category") or "")),
                    material_structural_key({
                        "material_family": (material.get("specifications") or {}).get("material_family") or "",
                        "identity_attributes": material.get("specifications") or {},
                    }),
                )
                materials_by_key[key] = material
        _emit_duration(
            trace,
            "server.price_source_database_material_index",
            material_index_started,
            existing_materials=len(existing_material_rows),
            created_materials=len(new_material_payloads),
        )

        rows_apply_started = time.perf_counter()
        source_row_payloads: list[dict[str, Any]] = []
        offer_intents: list[dict[str, Any]] = []
        operation_offer_intents: list[dict[str, Any]] = []
        prior_offer_ids_to_supersede: set[str] = set()
        for row in result["rows"]:
            row_category = canonical_price_source_category(str(row["material_type"]))
            material_id = None
            result_status = row["status"]
            operation_code = operation_code_by_row_number.get(int(row["source_row_number"]))
            operation_id = operation_ids_by_code.get(operation_code or "")
            if result_status == "ready" and row["item_kind"] == "material":
                structural_key = material_structural_key(row)
                sku = _normalized_name(str(row.get("raw_sku") or ""))
                sku_offers = offers_by_sku.get((current_lane, sku), []) if sku else []
                sku_materials = [
                    material_by_id.get(str(offer.get("company_material_id") or ""))
                    for offer in sku_offers
                    if material_by_id.get(str(offer.get("company_material_id") or ""))
                    and material_offer_matches_extracted_row(
                        offer,
                        material_by_id[str(offer.get("company_material_id") or "")],
                        row,
                        default_currency=str(result.get("currency") or ""),
                    )
                ]
                existing = (
                    [sku_materials[0]]
                    if len({str(item.get("company_material_id")): item for item in sku_materials}) == 1
                    else [
                        inferred_material_by_row_number[int(row["source_row_number"])]
                    ]
                    if int(row["source_row_number"]) in inferred_material_by_row_number
                    else [
                        materials_by_key[(row_category, structural_key)]
                    ] if (row_category, structural_key) in materials_by_key else []
                )
                if existing:
                    material_id = existing[0]["company_material_id"]
                    if existing[0].get("status") == "archived":
                        material_ids_to_restore.add(str(material_id))
                    identity = (str(material_id), current_lane)
                    matching_offers = offers_by_identity.get(identity, [])
                    if matching_offers and any(
                        price_offer_matches_row(
                            offer,
                            row,
                            default_currency=str(result.get("currency") or ""),
                        )
                        for offer in matching_offers
                    ):
                        result_status = "unchanged"
                        unchanged_count += 1
                    else:
                        result_status = "updated" if matching_offers else "new"
                        if matching_offers:
                            updated_count += 1
                        else:
                            new_count += 1
                else:
                    raise RuntimeError("Prepared company material was not available")
            elif result_status == "ready" and operation_id:
                pricing_basis = supplier_service_pricing_basis(
                    row.get("raw_unit"), operation_code=operation_code
                )
                identity = (str(operation_id), current_lane)
                matching_operation_offers = operation_offers_by_identity.get(identity, [])
                if any(
                    supplier_operation_offer_matches_row(
                        offer,
                        row,
                        pricing_basis=pricing_basis,
                        default_currency=str(result.get("currency") or ""),
                    )
                    for offer in matching_operation_offers
                ):
                    result_status = "unchanged"
                    unchanged_count += 1
                else:
                    result_status = "new"
                    new_count += 1

            source_row_payloads.append(
                {
                    "source_id": source_id,
                    "company_id": company_id,
                    "source_row_number": row["source_row_number"],
                    "raw_description": row["raw_description"],
                    "raw_sku": row["raw_sku"] or None,
                    "raw_price": row["raw_price"],
                    "raw_currency": row["raw_currency"] or None,
                    "raw_unit": row["raw_unit"] or None,
                    "raw_package_quantity": row["raw_package_quantity"] or None,
                    "raw_quantity": row["raw_quantity"] or None,
                    "raw_line_total": row["raw_line_total"] or None,
                    "raw_vat_included": True if row["raw_vat_mode"] == "included" else False if row["raw_vat_mode"] == "excluded" else None,
                    "normalized_name": row["normalized_name"] or None,
                    "normalized_price": row["normalized_price"] or None,
                    "purchase_unit": row["purchase_unit"] or None,
                    "calculation_unit": row["calculation_unit"] or None,
                    "conversion_factor": row["conversion_factor"] or None,
                    "normalized_unit": row["calculation_unit"] or None,
                    "conversion_basis": {"description": row["conversion_basis"]},
                    "company_material_id": material_id,
                    "row_kind": "operation_service" if operation_id else "material" if row["item_kind"] == "material" else "non_catalog",
                    "reference_operation_id": operation_id,
                    "result_status": "updated" if result_status == "unchanged" else result_status,
                    "confidence": row["confidence"],
                    "reason_codes": row["reason_codes"],
                    "evidence": {
                        "reference": row["evidence_reference"],
                        "material_type": row_category,
                        "item_kind": row["item_kind"],
                        "material_family": row["material_family"],
                        "identity_attributes": row["identity_attributes"],
                        "discount_percent": row["raw_discount_percent"],
                        "discount_amount": row["raw_discount_amount"],
                        "comparison_status": result_status,
                    },
                }
            )

            if material_id and result_status in {"new", "updated"}:
                identity = (str(material_id), current_lane)
                for previous_offer in offers_by_identity.get(identity, []):
                    pending_intent_index = previous_offer.get("_pending_intent_index")
                    if pending_intent_index is not None:
                        offer_intents[pending_intent_index]["status"] = "superseded"
                    else:
                        prior_offer_ids_to_supersede.add(str(previous_offer["offer_id"]))
                offer_intent = {
                    "source_row_number": row["source_row_number"],
                    "status": "active",
                    "payload": {
                        "company_id": company_id,
                        "company_material_id": material_id,
                        "supplier_id": supplier_id,
                        "source_id": source_id,
                        "supplier_sku": row["raw_sku"] or None,
                        "source_price": row["raw_price"],
                        "source_unit": row["raw_unit"],
                        "purchase_unit": row["purchase_unit"],
                        "calculation_unit": row["calculation_unit"],
                        "conversion_factor": row["conversion_factor"],
                        "normalized_price": row["normalized_price"],
                        "normalized_unit": row["calculation_unit"],
                        "currency": row["raw_currency"] or result["currency"],
                        "vat_included": True if row["raw_vat_mode"] == "included" else False if row["raw_vat_mode"] == "excluded" else None,
                        "valid_from": _date_or_none(result["document_date"]),
                        "confidence": row["confidence"],
                    },
                }
                offer_intents.append(offer_intent)
                pending_offer = dict(offer_intent["payload"])
                pending_offer["_pending_intent_index"] = len(offer_intents) - 1
                offers_by_identity[identity] = [pending_offer]
                if sku:
                    offers_by_sku[(current_lane, sku)] = [pending_offer]
            elif operation_id and result_status == "new":
                pricing_basis = supplier_service_pricing_basis(
                    row.get("raw_unit"), operation_code=operation_code
                )
                operation_offer_intents.append(
                    {
                        "source_row_number": row["source_row_number"],
                        "operation_id": operation_id,
                        "raw_service_name": row["raw_description"] or row["normalized_name"],
                        "supplier_sku": row["raw_sku"] or None,
                        "source_price": row["raw_price"],
                        "pricing_basis": pricing_basis,
                        "source_unit_label": row["raw_unit"] or None,
                        "currency": row["raw_currency"] or result["currency"],
                        "vat_included": True if row["raw_vat_mode"] == "included" else False if row["raw_vat_mode"] == "excluded" else None,
                        "valid_from": _date_or_none(result["document_date"]),
                        "confidence": row["confidence"],
                        "evidence": {"reference": row["evidence_reference"], "operation_code": operation_code},
                    }
                )
                operation_offers_by_identity[(str(operation_id), current_lane)] = [
                    {
                        "source_price": row["raw_price"],
                        "pricing_basis": pricing_basis,
                        "source_unit_label": row["raw_unit"],
                        "currency": row["raw_currency"] or result["currency"],
                        "vat_included": (
                            True if row["raw_vat_mode"] == "included"
                            else False if row["raw_vat_mode"] == "excluded" else None
                        ),
                    }
                ]

        inserted_rows = (
            client.table("company_price_source_rows").insert(source_row_payloads).execute().data
            or []
        ) if source_row_payloads else []
        row_id_by_number = {
            str(inserted.get("source_row_number")): inserted.get("row_id")
            for inserted in inserted_rows
        }
        if len(row_id_by_number) != len(source_row_payloads) or any(
            not row_id_by_number.get(str(row["source_row_number"]))
            for row in source_row_payloads
        ):
            raise RuntimeError("Inserted source rows could not be identified")

        if prior_offer_ids_to_supersede:
            client.table("company_material_offers").update(
                {"status": "superseded"}
            ).in_("offer_id", sorted(prior_offer_ids_to_supersede)).execute()
            superseded_offer_ids.extend(sorted(prior_offer_ids_to_supersede))

        offer_payloads: list[dict[str, Any]] = []
        for intent in offer_intents:
            payload = dict(intent["payload"])
            payload["source_row_id"] = row_id_by_number[str(intent["source_row_number"])]
            payload["status"] = intent["status"]
            offer_payloads.append(payload)
        if offer_payloads:
            client.table("company_material_offers").insert(offer_payloads).execute()

        operation_offer_payloads = []
        for intent in operation_offer_intents:
            payload = dict(intent)
            payload["source_row_id"] = row_id_by_number[str(payload.pop("source_row_number"))]
            payload.update({
                "company_id": company_id,
                "supplier_id": supplier_id,
                "source_id": source_id,
                "status": "active",
            })
            operation_offer_payloads.append(payload)
        if operation_offer_payloads:
            client.table("company_supplier_operation_offers").insert(operation_offer_payloads).execute()

        _emit_duration(
            trace,
            "server.price_source_database_rows_apply",
            rows_apply_started,
            extracted_rows=len(result["rows"]),
            active_rows=ready_count,
            source_rows_inserted=len(source_row_payloads),
            offers_inserted=len(offer_payloads),
            offers_superseded=len(prior_offer_ids_to_supersede),
        )

        if material_ids_to_restore:
            client.table("company_material_items").update(
                {"status": "private", "updated_at": datetime.now(timezone.utc).isoformat()}
            ).eq("company_id", company_id).in_(
                "company_material_id", sorted(material_ids_to_restore)
            ).execute()

        identity_started = time.perf_counter()
        identity_summary = _resolve_and_record_price_source_identities(
            client,
            company_id=company_id,
            source_id=source_id,
            trace=trace,
        )
        _emit_duration(
            trace,
            "server.price_source_identity_stage",
            identity_started,
            examined=int(identity_summary.get("examined") or 0),
            resolved=int(identity_summary.get("resolved") or 0),
            shortlisted=int(identity_summary.get("shortlisted") or 0),
        )

        source_summary.update(
            {
                "new": new_count,
                "updated": updated_count,
                "unchanged": unchanged_count,
                "material_identity": identity_summary,
                "processing_duration_seconds": time.perf_counter() - process_started,
            }
        )
        client.table("company_price_sources").update(
            {"processing_summary": source_summary}
        ).eq("company_id", company_id).eq("source_id", source_id).execute()
        _emit_duration(
            trace,
            "server.price_source_database_apply",
            database_started,
            extracted_rows=len(result["rows"]),
            active_rows=ready_count,
            unresolved_rows=unresolved_count,
            excluded_rows=excluded_count,
        )
        _emit_duration(
            trace,
            "server.price_source_total",
            process_started,
            extracted_rows=len(result["rows"]),
        )
        return PriceSourceProcessResult(source_id=source_id, summary=source_summary)
    except Exception:
        cleanup_started = time.perf_counter()
        try:
            client.table("company_material_offers").delete().eq("source_id", source_id).execute()
            for offer_id in superseded_offer_ids:
                client.table("company_material_offers").update({"status": "active"}).eq(
                    "offer_id", offer_id
                ).execute()
            client.table("company_price_source_rows").delete().eq("source_id", source_id).execute()
            client.table("company_material_items").delete().eq("created_from_source_id", source_id).execute()
            client.table("company_price_sources").delete().eq("source_id", source_id).execute()
        except Exception:
            pass
        client.storage.from_(PRICE_SOURCE_BUCKET).remove([object_path])
        _emit_duration(trace, "server.price_source_cleanup", cleanup_started)
        raise
