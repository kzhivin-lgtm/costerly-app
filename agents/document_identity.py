from __future__ import annotations

import base64
import html
import json
import re
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_DETECTION_MODEL,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
    strip_schema_for_claude,
)


DOCUMENT_IDENTITY_VERSION = "document_identity_v4_semantic_title_block"
DOCUMENT_IDENTITY_PROMPT_PATH = Path(__file__).parent / "prompts" / "document_identity_prompt.md"
_FIELDS = ("project_name", "client", "design_partner", "author", "document_date")
_CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
_ORDER_LABEL_RE = re.compile(r"(?:order|заказ)(?:\s+(?:no\.?|number|№))?", re.I)
_ORDER_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_/-]{1,63}$")

DOCUMENT_IDENTITY_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": list(_FIELDS),
    "properties": {
        field: {
            "type": "object",
            "additionalProperties": False,
            "required": ["value", "source_page", "source_corner", "source_label"],
            "properties": {
                "value": {"type": "string"},
                "source_page": {"type": "integer", "minimum": 0},
                "source_corner": {"type": "string"},
                "source_label": {"type": "string"},
            },
        }
        for field in _FIELDS
    },
}


def load_document_identity_prompt() -> str:
    return DOCUMENT_IDENTITY_PROMPT_PATH.read_text(encoding="utf-8").strip()


def unknown_document_identity() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "value": "unknown", "source_page": 0,
            "source_corner": "", "source_label": "",
        }
        for field in _FIELDS
    }


def _ocr_rows(ocr_package: dict[str, Any]) -> list[tuple[int, list[list[str]]]]:
    evidence = ocr_package.get("evidence") if isinstance(ocr_package, dict) else None
    if not isinstance(evidence, dict):
        return []
    rows: list[tuple[int, list[list[str]]]] = []
    for kind in ("text_blocks", "literal_items"):
        for item in evidence.get(kind) or []:
            if not isinstance(item, dict):
                continue
            try:
                page_number = int(item.get("page_number"))
            except (TypeError, ValueError):
                continue
            raw = html.unescape(str(item.get("text") or ""))
            raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
            raw = re.sub(r"(?i)</tr\s*>", "\n", raw)
            raw = re.sub(r"(?i)</(?:td|th)\s*>", "|", raw)
            plain = re.sub(r"<[^>]+>", " ", raw)
            table_rows = [
                [" ".join(cell.split()) for cell in line.split("|") if " ".join(cell.split())]
                for line in plain.splitlines()
            ]
            table_rows = [row for row in table_rows if row]
            if table_rows:
                rows.append((page_number, table_rows))
    return rows


def _ocr_title_block_entries(ocr_package: dict[str, Any]) -> list[dict[str, Any]]:
    """Return positioned title-block candidates from existing OCR/native text.

    This does not run another model.  The OCR package already carries native
    PDF spans and Mistral literals in rendered-page coordinates.  We use only
    the lower-right/central title-block zone, deliberately excluding ordinary
    drawing annotation from document identity.
    """
    evidence = ocr_package.get("evidence") if isinstance(ocr_package, dict) else None
    if not isinstance(evidence, dict):
        return []
    raw_entries: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    for kind in ("text_blocks", "literal_items"):
        for item in evidence.get(kind) or []:
            if not isinstance(item, dict):
                continue
            try:
                page_number = int(item.get("page_number"))
            except (TypeError, ValueError):
                continue
            bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else {}
            try:
                left = float(bbox["top_left_x"])
                top = float(bbox["top_left_y"])
                right = float(bbox["bottom_right_x"])
                bottom = float(bbox["bottom_right_y"])
            except (KeyError, TypeError, ValueError):
                continue
            text = " ".join(html.unescape(str(item.get("text") or "")).split())
            if not text or right <= left or bottom <= top:
                continue
            key = (page_number, text, round(left), round(top), round(right), round(bottom))
            if key in seen:
                continue
            seen.add(key)
            raw_entries.append({
                "page_number": page_number, "text": text,
                "left": left, "top": top, "right": right, "bottom": bottom,
            })
    page_extents: dict[int, tuple[float, float]] = {}
    for entry in raw_entries:
        page = int(entry["page_number"])
        max_right, max_bottom = page_extents.get(page, (0.0, 0.0))
        page_extents[page] = (max(max_right, entry["right"]), max(max_bottom, entry["bottom"]))
    return [
        entry for entry in raw_entries
        if (
            (extent := page_extents.get(int(entry["page_number"]))) is not None
            and entry["top"] >= extent[1] * 0.78
            and entry["right"] >= extent[0] * 0.35
        )
    ]


_TITLE_BLOCK_ADDRESS_RE = re.compile(
    r"(?:\baddress\b|\bby\s+address\b|адрес(?:у|:)?|по\s+адресу|"
    r"ул(?:ица|\.)?|просп(?:ект|\.)?|street|st\.)",
    re.IGNORECASE,
)
_TITLE_BLOCK_DESIGN_RE = re.compile(
    r"(?:arch(?:i|itect|itecture)|архи|архитект|дизайн|designer?|design|"
    r"bureau|бюро|проектн|עיצוב|אדריכל)",
    re.IGNORECASE,
)
_TITLE_BLOCK_ORGANIZATION_RE = re.compile(
    r"(?:\b(?:llc|ltd|inc|corp|studio|bureau)\b|ооо|зао|ао|ип|бюро|студия|"
    r"компания|company)",
    re.IGNORECASE,
)
_TITLE_BLOCK_ADMIN_RE = re.compile(
    r"(?:архитектурная\s+часть|architectural\s+part|stage|стадия|лист(?:ов)?|"
    r"изм\.?|кол\.?(?:уч\.)?|подпись|дата|architect|дизайнер|designer|"
    r"док\.?|sheet|revision|gspublisherversion)",
    re.IGNORECASE,
)
_TITLE_BLOCK_DESIGN_PERSON_ROLE_RE = re.compile(
    r"(?:architect|архитектор|дизайнер|designer|design\s+lead)",
    re.IGNORECASE,
)
_TITLE_BLOCK_AUTHOR_ROLE_RE = re.compile(
    r"(?:\bauthor\b|автор|drawn\s+by|разработал)",
    re.IGNORECASE,
)
_TITLE_BLOCK_PERSON_RE = re.compile(
    r"(?:^[A-ZА-ЯЁ]\.?\s*[A-Za-zА-Яа-яЁё-]{2,}$|"
    r"^[A-ZА-ЯЁ][a-zа-яё-]{1,}\s+[A-ZА-ЯЁ][a-zа-яё-]{1,}$)"
)


def _identity_value(entry: dict[str, Any], *, source_label: str) -> dict[str, Any]:
    return {
        "value": str(entry["text"]),
        "source_page": int(entry["page_number"]),
        "source_corner": "ocr_title_block",
        "source_label": source_label,
    }


def _derive_semantic_title_block_identity(
    identity: dict[str, dict[str, Any]],
    ocr_package: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Fill useful title-block roles when a drawing omits formal field labels.

    Explicitly-labelled values, resolved earlier, always win.  The fallback is
    intentionally evidence-shaped rather than optimistic: architecture/design
    organisations are Partner candidates, a non-design organisation directly
    attached to an address is a Client candidate, and a document-title phrase
    is Project.  The address itself is a Project fallback only when no title
    survives the filters.
    """
    entries = _ocr_title_block_entries(ocr_package)
    if not entries:
        return identity

    if identity["design_partner"]["value"] == "unknown":
        partner_candidates = [
            entry for entry in entries
            if _TITLE_BLOCK_DESIGN_RE.search(entry["text"])
            and _TITLE_BLOCK_ORGANIZATION_RE.search(entry["text"])
            and not _TITLE_BLOCK_ADMIN_RE.search(entry["text"])
        ]
        if partner_candidates:
            # Prefer the most title-block-like candidate, not a nearby callout.
            partner = max(partner_candidates, key=lambda entry: (entry["bottom"], entry["right"]))
            identity["design_partner"] = _identity_value(
                partner, source_label="SEMANTIC_DESIGN_ORGANIZATION",
            )
        else:
            # A named designer can be the design partner for a sole-practitioner
            # dossier.  Do not repurpose an explicit Author/Drawn-by row.
            design_people: list[dict[str, Any]] = []
            for role in entries:
                if (
                    not _TITLE_BLOCK_DESIGN_PERSON_ROLE_RE.search(role["text"])
                    or _TITLE_BLOCK_AUTHOR_ROLE_RE.search(role["text"])
                ):
                    continue
                for candidate in entries:
                    if candidate["page_number"] != role["page_number"]:
                        continue
                    same_row = abs(
                        (candidate["top"] + candidate["bottom"]) / 2
                        - (role["top"] + role["bottom"]) / 2
                    ) <= 30
                    near_role = -40 <= candidate["left"] - role["right"] <= 280
                    if same_row and near_role and _TITLE_BLOCK_PERSON_RE.fullmatch(candidate["text"]):
                        design_people.append(candidate)
            if design_people:
                partner = max(design_people, key=lambda entry: (entry["bottom"], entry["right"]))
                identity["design_partner"] = _identity_value(
                    partner, source_label="SEMANTIC_DESIGN_PERSON",
                )

    if identity["client"]["value"] == "unknown":
        address_entries = [
            entry for entry in entries if _TITLE_BLOCK_ADDRESS_RE.search(entry["text"])
        ]
        address_linked_candidates: list[dict[str, Any]] = []
        for address in address_entries:
            address_linked_candidates.extend(
                entry for entry in entries
                if entry["page_number"] == address["page_number"]
                and 0 <= address["top"] - entry["bottom"] <= 100
                and _TITLE_BLOCK_ORGANIZATION_RE.search(entry["text"])
                and not _TITLE_BLOCK_DESIGN_RE.search(entry["text"])
            )
        if address_linked_candidates:
            client = min(
                address_linked_candidates,
                key=lambda entry: min(
                    address["top"] - entry["bottom"]
                    for address in address_entries
                    if address["page_number"] == entry["page_number"]
                ),
            )
            identity["client"] = _identity_value(
                client, source_label="ADDRESS_ASSOCIATED_ORGANIZATION",
            )
        else:
            client_candidates = [
                entry for entry in entries
                if _TITLE_BLOCK_ORGANIZATION_RE.search(entry["text"])
                and not _TITLE_BLOCK_DESIGN_RE.search(entry["text"])
                and not _TITLE_BLOCK_ADMIN_RE.search(entry["text"])
            ]
            if client_candidates:
                client = max(client_candidates, key=lambda entry: (entry["bottom"], entry["right"]))
                identity["client"] = _identity_value(
                    client, source_label="SEMANTIC_NON_DESIGN_ORGANIZATION",
                )

    if identity["project_name"]["value"] == "unknown":
        project_candidates = [
            entry for entry in entries
            if len(re.sub(r"[^A-Za-zА-Яа-яЁёא-ת]", "", entry["text"])) >= 5
            and not _TITLE_BLOCK_ADDRESS_RE.search(entry["text"])
            and not _TITLE_BLOCK_DESIGN_RE.search(entry["text"])
            and not _TITLE_BLOCK_ORGANIZATION_RE.search(entry["text"])
            and not _TITLE_BLOCK_ADMIN_RE.search(entry["text"])
        ]
        if project_candidates:
            project = max(
                project_candidates,
                key=lambda entry: (entry["bottom"], entry["right"] - entry["left"]),
            )
            identity["project_name"] = _identity_value(
                project, source_label="TITLE_BLOCK_DOCUMENT_TITLE",
            )
        else:
            address_entries = [
                entry for entry in entries if _TITLE_BLOCK_ADDRESS_RE.search(entry["text"])
            ]
            if address_entries:
                project = max(address_entries, key=lambda entry: (entry["bottom"], entry["right"]))
                identity["project_name"] = _identity_value(
                    project, source_label="ADDRESS_AS_PROJECT_FALLBACK",
                )
    return identity


def _is_administrative_label(value: str) -> bool:
    normalized = value.casefold()
    return any(marker in normalized for marker in (
        "project", "item no", "project no", "drawing name", "file name",
        "date", "scale", "sheet no", "revision", "chief arch", "architect",
        "title", "document status", "dwg no", "approved by", "created by",
        "technical reference",
    ))


def _first_project_value(rows: list[list[str]]) -> str:
    for row_index, row in enumerate(rows):
        for cell_index, cell in enumerate(row):
            if not re.fullmatch(r"project(?:\s+name)?", cell, re.I):
                continue
            for candidate in row[cell_index + 1:]:
                if not _is_administrative_label(candidate) and re.search(r"[A-Za-zА-Яа-яЁё]", candidate):
                    return candidate
            for following in rows[row_index + 1:row_index + 3]:
                for candidate in following:
                    if not _is_administrative_label(candidate) and re.search(r"[A-Za-zА-Яа-яЁё]", candidate):
                        return candidate
    return ""


def _first_document_title(rows: list[list[str]]) -> str:
    """Return only a value locally attached to an explicit Title label."""
    for row_index, row in enumerate(rows):
        for cell_index, cell in enumerate(row):
            if not re.fullmatch(r"(?:document\s+)?title", cell, re.I):
                continue
            for candidate in row[cell_index + 1:]:
                if not _is_administrative_label(candidate) and re.search(
                    r"[A-Za-zА-Яа-яЁё]", candidate,
                ):
                    return candidate
            for following in rows[row_index + 1:row_index + 3]:
                for candidate in following:
                    if not _is_administrative_label(candidate) and re.search(
                        r"[A-Za-zА-Яа-яЁё]", candidate,
                    ):
                        return candidate
    return ""


def _first_order_identifier(rows: list[list[str]]) -> str:
    """Return a package ID only when OCR explicitly labels it as an order.

    An order is not generally a client or author.  It is, however, a useful
    project identifier when the same explicitly labelled value is repeated
    across the document and no project field exists.  Numeric values are safe
    here precisely because the adjacent label supplies their meaning.
    """
    for row in rows:
        for cell_index, cell in enumerate(row):
            normalized = " ".join(cell.split())
            direct = re.fullmatch(
                r"(?:order|заказ)(?:\s+(?:no\.?|number|№))?\s*[:#№-]?\s*"
                r"([A-Za-z0-9][A-Za-z0-9_/-]{1,63})",
                normalized,
                re.I,
            )
            if direct and _ORDER_VALUE_RE.fullmatch(direct.group(1)):
                return direct.group(1)
            if not _ORDER_LABEL_RE.fullmatch(normalized):
                continue
            for candidate in row[cell_index + 1:]:
                value = " ".join(candidate.split())
                if _ORDER_VALUE_RE.fullmatch(value):
                    return value
    return ""


def derive_document_identity_from_ocr(ocr_package: dict[str, Any]) -> dict[str, Any]:
    """Extract only explicitly labelled identity facts from already available OCR."""
    identity = unknown_document_identity()
    project_candidates: list[tuple[int, str]] = []
    title_candidates_by_page: dict[int, set[str]] = {}
    order_candidates_by_page: dict[int, set[str]] = {}
    ocr_rows = _ocr_rows(ocr_package)
    for page_number, rows in ocr_rows:
        project = _first_project_value(rows)
        if project:
            project_candidates.append((page_number, project))
        title = _first_document_title(rows)
        if title:
            title_candidates_by_page.setdefault(page_number, set()).add(title)
        order = _first_order_identifier(rows)
        if order:
            order_candidates_by_page.setdefault(page_number, set()).add(order)
    if project_candidates:
        counts: dict[str, int] = {}
        for _, value in project_candidates:
            counts[value] = counts.get(value, 0) + 1
        value = max(counts, key=counts.get)
        source_page = next(page for page, candidate in project_candidates if candidate == value)
        identity["project_name"] = {
            "value": value,
            "source_page": source_page,
            "source_corner": "ocr_title_block",
            "source_label": "PROJECT",
        }
    elif title_candidates_by_page:
        # A sheet Title can name a local detail rather than the document. Only
        # one identical, explicitly labelled value repeated on a strict page
        # majority is promoted to Project identity.
        page_count = len({page for page, _ in ocr_rows})
        unambiguous_titles = {
            page: next(iter(values))
            for page, values in title_candidates_by_page.items()
            if len(values) == 1
        }
        counts: dict[str, int] = {}
        for value in unambiguous_titles.values():
            counts[value] = counts.get(value, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        value, frequency = ranked[0] if ranked else ("", 0)
        unique_winner = len(ranked) == 1 or ranked[0][1] > ranked[1][1]
        if page_count and unique_winner and frequency > page_count / 2:
            source_page = next(
                page for page, candidate in unambiguous_titles.items()
                if value == candidate
            )
            identity["project_name"] = {
                "value": value,
                "source_page": source_page,
                "source_corner": "ocr_title_block",
                "source_label": "TITLE",
            }
    if (
        identity["project_name"]["value"] == "unknown"
        and order_candidates_by_page
    ):
        # A generic order reference on one sheet is not a project.  A common
        # order label on a strict majority of the document is a stable package
        # identifier and is more useful than leaving the project unknown.
        page_count = len({page for page, _ in ocr_rows})
        counts: dict[str, int] = {}
        for values in order_candidates_by_page.values():
            for value in values:
                counts[value] = counts.get(value, 0) + 1
        value, frequency = max(counts.items(), key=lambda item: item[1])
        if page_count and frequency > page_count / 2:
            source_page = next(
                page for page, values in order_candidates_by_page.items()
                if value in values
            )
            identity["project_name"] = {
                "value": f"Order {value}",
                "source_page": source_page,
                "source_corner": "ocr_title_block",
                "source_label": "ORDER",
            }
    identity = _derive_semantic_title_block_identity(identity, ocr_package)
    return {
        "model": "deterministic_ocr_title_block_v4_semantic_fallback",
        "duration_seconds": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "identity": identity,
        "crop_audit": [],
    }


def _sample_page_numbers(page_count: int) -> list[int]:
    if page_count <= 0:
        return []
    selected = set(range(1, min(page_count, 3) + 1))
    selected.add(page_count)
    return sorted(selected)


def build_document_identity_title_block_crops(
    page_images: list[bytes],
    *,
    max_side: int = 1200,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return bounded corner crops for a title-block-only metadata pass.

    This intentionally samples document administration, not object Islands. It
    runs after Detection is persisted and has no authority over objects.
    """
    try:
        from PIL import Image
    except ImportError:
        return [], [{"reason": "Pillow unavailable"}]

    crops: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for page_number in _sample_page_numbers(len(page_images)):
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as image:
                width, height = image.size
                crop_width, crop_height = max(1, round(width * 0.32)), max(1, round(height * 0.36))
                for corner in _CORNERS:
                    left = 0 if "left" in corner else width - crop_width
                    top = 0 if "top" in corner else height - crop_height
                    crop = image.crop((left, top, left + crop_width, top + crop_height))
                    crop.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                    output = BytesIO()
                    crop.save(output, format="JPEG", quality=85)
                    crops.append({
                        "page_number": page_number,
                        "corner": corner,
                        "bytes": output.getvalue(),
                    })
                    audit.append({
                        "page_number": page_number,
                        "corner": corner,
                        "source_dimensions": {"width": width, "height": height},
                        "crop_dimensions": {"width": crop.width, "height": crop.height},
                    })
        except Exception as exc:
            audit.append({"page_number": page_number, "reason": type(exc).__name__})
    return crops, audit


def validate_document_identity(
    result: object,
    *,
    allowed_pages: set[int],
    allowed_corners: set[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(result, dict) or set(result) != set(_FIELDS):
        raise ValueError("Document identity result is invalid")
    normalized: dict[str, dict[str, Any]] = {}
    for field in _FIELDS:
        item = result.get(field)
        if not isinstance(item, dict) or set(item) != {
            "value", "source_page", "source_corner", "source_label",
        }:
            raise ValueError("Document identity field is invalid")
        value = " ".join(str(item.get("value") or "").split())
        source_label = " ".join(str(item.get("source_label") or "").split())
        source_corner = str(item.get("source_corner") or "")
        try:
            source_page = int(item.get("source_page"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Document identity source page is invalid") from exc
        if not value or len(value) > 160:
            raise ValueError("Document identity value is invalid")
        if value.casefold() == "unknown":
            if source_page != 0 or source_corner or source_label:
                raise ValueError("Unknown document identity cannot cite a source")
            normalized[field] = unknown_document_identity()[field]
            continue
        if source_page not in allowed_pages or source_corner not in allowed_corners or not source_label:
            raise ValueError("Document identity populated value needs visible title-block evidence")
        non_identity_labels = ("file name", "drawing name", "sheet no", "revision")
        if any(marker in source_label.casefold() for marker in non_identity_labels):
            raise ValueError("Document identity value cites a non-identity title-block label")
        normalized[field] = {
            "value": value,
            "source_page": source_page,
            "source_corner": source_corner,
            "source_label": source_label,
        }
    return normalized


def run_document_identity_call(*, page_images: list[bytes]) -> dict[str, Any]:
    """Extract document-level roles after object boundaries are locked."""
    crops, crop_audit = build_document_identity_title_block_crops(page_images)
    if not crops:
        return {
            "model": "deterministic", "duration_seconds": 0.0,
            "input_tokens": 0, "output_tokens": 0,
            "identity": unknown_document_identity(), "crop_audit": crop_audit,
        }
    model = str(
        get_secret("CLAUDE_DOCUMENT_IDENTITY_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
        or DEFAULT_CLAUDE_DETECTION_MODEL
    )
    content: list[dict[str, Any]] = [{
        "type": "text",
        "text": "Return only schema JSON for document-level identity. The supplied images are title-block candidate crops.",
    }]
    for crop in crops:
        content.extend([
            {"type": "text", "text": json.dumps({
                "title_block_crop": {"page_number": crop["page_number"], "corner": crop["corner"]},
            })},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": base64.b64encode(crop["bytes"]).decode("ascii"),
            }},
        ])
    started = time.perf_counter()
    response = create_claude_message(
        get_anthropic_client(), model=model, max_tokens=1024, temperature=0,
        system=load_document_identity_prompt(),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(DOCUMENT_IDENTITY_RESULT_SCHEMA)}},
    )
    raw = json.loads(extract_text_from_claude_response(response))
    identity = validate_document_identity(
        raw,
        allowed_pages={int(crop["page_number"]) for crop in crops},
        allowed_corners={str(crop["corner"]) for crop in crops},
    )
    usage = getattr(response, "usage", None)
    return {
        "model": model,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "identity": identity,
        "crop_audit": crop_audit,
    }
