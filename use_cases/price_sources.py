from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import httpx
import pandas as pd
from PIL import Image, UnidentifiedImageError

from agents.price_source_agent import run_price_source_agent
from db.company_access import assert_company_owner
from db.repositories import insert_agent_usage_event
from db.supabase_client import get_supabase_client


PRICE_SOURCE_BUCKET = "company-price-sources"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
AUTO_ACTIVATION_CONFIDENCE = 85
LEGACY_EXTREME_RATIO = 3.0
LEGACY_CONFIDENCE_PENALTY = 15.0
SUPPORTED_SUFFIXES = {".pdf", ".xlsx", ".csv", ".jpg", ".jpeg", ".png"}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

PRICE_SOURCE_DEPARTMENTS = ("Wood", "Metal", "Finishing")
PRICE_CATALOG_DEPARTMENTS = {
    "Wood Sheets": "Wood",
    "Solid Wood": "Wood",
    "Wood Supplies": "Wood",
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
    "Hardware": "Wood Supplies",
    "Edgebanding": "Wood Supplies",
    "Adhesives and Consumables": "Wood Supplies",
    "Finishes and Coatings": "Paints & Coatings",
    "Abrasives and Sanding": "Coating Supplies",
}
PRICE_CATALOG_DEPARTMENT_ORDER = {"Wood": 0, "Metal": 1, "Finishing": 2}


class PriceSourceError(ValueError):
    pass


@dataclass(frozen=True)
class CombinedPriceSource:
    name: str
    data: bytes

    def getvalue(self) -> bytes:
        return self.data


logger = logging.getLogger(__name__)


def combine_price_source_files(files: list) -> object | None:
    """Keep one upload as-is or combine ordered JPEG/PNG pages into one PDF."""
    selected = [item for item in files if item is not None]
    if not selected:
        return None
    if len(selected) == 1:
        return selected[0]
    suffixes = [Path(str(item.name)).suffix.lower() for item in selected]
    if any(suffix not in {".jpg", ".jpeg", ".png"} for suffix in suffixes):
        raise PriceSourceError(
            "Select one PDF or spreadsheet, or select several JPEG/PNG photos from the same document."
        )
    if sum(len(item.getvalue()) for item in selected) > MAX_SOURCE_BYTES:
        raise PriceSourceError("The combined price source must be 50 MB or smaller.")
    pages: list[Image.Image] = []
    try:
        for item in selected:
            with Image.open(BytesIO(item.getvalue())) as image:
                page = image.convert("RGB")
                page.load()
                pages.append(page)
        output = BytesIO()
        pages[0].save(output, format="PDF", save_all=True, append_images=pages[1:])
    except (UnidentifiedImageError, OSError) as exc:
        raise PriceSourceError("One of the selected photos could not be read.") from exc
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
    """Keep rows outside an explicitly selected department non-active."""
    if not department:
        return result
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") == "excluded":
            continue
        material_type = canonical_price_source_category(
            str(row.get("material_type") or "Other")
        )
        detected_department = PRICE_CATALOG_DEPARTMENTS.get(material_type)
        if material_type != "Other" and detected_department != department:
            row["status"] = "unresolved"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["selected_department_mismatch"])
            )
    return result


def price_source_semantic_fingerprint(result: dict) -> str:
    """Identify the same commercial document across files, scans, or photos."""
    document_number = _normalized_name(str(result.get("document_number") or ""))
    basis: dict[str, object] = {
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


def _semantic_source_exists(client, company_id: str, fingerprint: str) -> bool:
    sources = (
        client.table("company_price_sources")
        .select("source_id,processing_summary")
        .eq("company_id", company_id)
        .neq("status", "archived")
        .execute()
    ).data or []
    return any(
        isinstance(source.get("processing_summary"), dict)
        and source["processing_summary"].get("semantic_sha256") == fingerprint
        for source in sources
    )


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
    http = client or httpx.Client(timeout=20, headers={"User-Agent": "CosterlyAIPriceImporter/1.0"})
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
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
            if content_type not in {"text/html", "text/plain"}:
                raise PriceSourceError("The URL must point to a readable supplier webpage.")
            content = response.content
            if len(content) > MAX_SOURCE_BYTES:
                raise PriceSourceError("The supplier page is too large to process.")
            parser = _VisibleTextParser()
            parser.feed(response.text)
            visible_text = parser.text()
            if not visible_text:
                raise PriceSourceError(
                    "This supplier page does not expose readable text. "
                    "Upload its PDF, screenshot, or photo instead."
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
        raise PriceSourceError("Upload PDF, XLSX, CSV, JPEG, or PNG.")
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
        .select("row_id,raw_description")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    sources = (
        client.table("company_price_sources")
        .select("source_id,source_name,source_kind,source_url,processed_at,created_at")
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
        catalog.append(
            {
                **offer,
                "department": department,
                "material_type": category,
                "canonical_name": str(material.get("canonical_name") or "Material"),
                "original_name": str(source_row.get("raw_description") or ""),
                "supplier_name": str(supplier.get("supplier_name") or "Unknown supplier"),
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


def process_price_source(
    access,
    *,
    department: str,
    uploaded_file=None,
    source_url: str = "",
    trace=None,
) -> str:
    """Process and persist one source. Ambiguous rows stay non-active."""
    process_started = time.perf_counter()
    department = _validate_department(department)
    if (uploaded_file is None) == (not source_url.strip()):
        raise PriceSourceError("Add one file or one supplier URL.")

    company_id = str(access.company_id)
    client = get_supabase_client()
    assert_company_owner(client, str(access.user_id), company_id)
    source_id = str(uuid4())

    if uploaded_file is not None:
        source_read_started = time.perf_counter()
        source_name = str(uploaded_file.name)
        suffix = _source_extension(source_name)
        source_bytes = uploaded_file.getvalue()
        if not source_bytes or len(source_bytes) > MAX_SOURCE_BYTES:
            raise PriceSourceError("The price source must be between 1 byte and 50 MB.")
        source_kind = "file"
        resolved_url = None
        _emit_duration(
            trace,
            "server.price_source_read",
            source_read_started,
            source_bytes=len(source_bytes),
        )
        parse_started = time.perf_counter()
        extracted_text = extract_spreadsheet_text(source_name, source_bytes)
        _emit_duration(
            trace,
            "server.price_source_spreadsheet_parse",
            parse_started,
            extracted_chars=len(extracted_text),
        )
        mime_type = CONTENT_TYPES[suffix]
    else:
        fetch_started = time.perf_counter()
        resolved_url, source_bytes, extracted_text = fetch_public_page(source_url)
        _emit_duration(
            trace,
            "server.price_source_url_fetch",
            fetch_started,
            source_bytes=len(source_bytes),
            extracted_chars=len(extracted_text),
        )
        source_name = resolved_url
        source_kind = "url"
        suffix = ".html"
        mime_type = "text/html"

    source_digest = sha256(source_bytes).hexdigest()
    duplicate = (
        client.table("company_price_sources")
        .select("source_id")
        .eq("company_id", company_id)
        .eq("source_sha256", source_digest)
        .neq("status", "archived")
        .limit(1)
        .execute()
    ).data or []
    if duplicate:
        raise PriceSourceError("This price source has already been added.")

    agent_started = time.perf_counter()
    result = run_price_source_agent(
        company_id=company_id,
        department=department,
        source_name=source_name,
        source_bytes=source_bytes if suffix in {".pdf", ".jpg", ".jpeg", ".png"} else None,
        extracted_text=extracted_text,
        import_id=source_id,
        trace=trace,
    )
    guard_price_source_department(result, department)
    material_types = price_source_material_types(result)
    category = material_types[0] if len(material_types) == 1 else "Mixed"
    semantic_sha256 = price_source_semantic_fingerprint(result)
    _emit_duration(
        trace,
        "server.price_source_agent",
        agent_started,
        extracted_rows=len(result.get("rows") or []),
    )
    usage_event = result.pop("_agent_usage", None)
    if usage_event:
        usage_started = time.perf_counter()
        try:
            insert_agent_usage_event(client, usage_event)
        except Exception:
            logger.exception("Price source agent usage persistence failed")
        _emit_duration(trace, "server.price_source_usage_persist", usage_started)
    if _semantic_source_exists(client, company_id, semantic_sha256):
        raise PriceSourceError(
            "This document has already been added, even if it was uploaded as another file or photo"
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

    try:
        database_started = time.perf_counter()
        supplier_name = str(result["supplier_name"]).strip()
        supplier_id = None
        if supplier_name:
            existing_suppliers = (
                client.table("company_suppliers")
                .select("supplier_id,categories")
                .eq("company_id", company_id)
                .eq("normalized_name", _normalized_name(supplier_name))
                .limit(1)
                .execute()
            ).data or []
            categories = sorted(
                set((existing_suppliers[0].get("categories") or []) + material_types)
            ) if existing_suppliers else material_types
            supplier_row = (
                client.table("company_suppliers")
                .upsert(
                    {
                        "company_id": company_id,
                        "supplier_name": supplier_name,
                        "normalized_name": _normalized_name(supplier_name),
                        "categories": categories,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    on_conflict="company_id,normalized_name",
                )
                .execute()
            ).data[0]
            supplier_id = supplier_row["supplier_id"]
        for row in result["rows"]:
            if row["status"] == "ready" and row["confidence"] < AUTO_ACTIVATION_CONFIDENCE:
                row["status"] = "unresolved"
                row["reason_codes"] = sorted(set(row["reason_codes"] + ["below_auto_activation_threshold"]))
        ready_count = sum(row["status"] == "ready" for row in result["rows"])
        unresolved_count = sum(row["status"] == "unresolved" for row in result["rows"])
        excluded_count = sum(row["status"] == "excluded" for row in result["rows"])
        status = "ready" if not unresolved_count else "partial"
        client.table("company_price_sources").insert(
            {
                "source_id": source_id,
                "company_id": company_id,
                "supplier_id": supplier_id,
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
                "processing_summary": {
                    "ready": ready_count,
                    "unresolved": unresolved_count,
                    "excluded": excluded_count,
                    "total": len(result["rows"]),
                    "document_number": result["document_number"],
                    "price_context": result["price_context"],
                    "document_subtotal": result["document_subtotal"],
                    "document_vat_amount": result["document_vat_amount"],
                    "document_total": result["document_total"],
                    "material_types": material_types,
                    "semantic_sha256": semantic_sha256,
                    "agent_duration_seconds": (
                        usage_event.get("duration_seconds") if usage_event else None
                    ),
                    "token_cost": usage_event.get("total_cost_usd") if usage_event else None,
                    "input_tokens": usage_event.get("input_tokens") if usage_event else None,
                    "output_tokens": usage_event.get("output_tokens") if usage_event else None,
                    "model": usage_event.get("model") if usage_event else None,
                    "prompt_version": usage_event.get("prompt_version") if usage_event else None,
                },
                "created_by": str(access.user_id),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()

        for row in result["rows"]:
            row_category = canonical_price_source_category(str(row["material_type"]))
            material_id = None
            result_status = row["status"]
            if result_status == "ready":
                normalized = _normalized_name(row["normalized_name"])
                existing = (
                    client.table("company_material_items")
                    .select("company_material_id")
                    .eq("company_id", company_id)
                    .eq("category", row_category)
                    .eq("normalized_name", normalized)
                    .limit(1)
                    .execute()
                ).data or []
                if existing:
                    material_id = existing[0]["company_material_id"]
                    result_status = "updated"
                else:
                    material = client.table("company_material_items").insert(
                        {
                            "company_id": company_id,
                            "category": row_category,
                            "canonical_name": row["normalized_name"],
                            "normalized_name": normalized,
                            "preferred_unit": row["calculation_unit"],
                            "created_from_source_id": source_id,
                        }
                    ).execute().data[0]
                    material_id = material["company_material_id"]
                    result_status = "new"

            inserted_row = client.table("company_price_source_rows").insert(
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
                    "result_status": result_status,
                    "confidence": row["confidence"],
                    "reason_codes": row["reason_codes"],
                    "evidence": {
                        "reference": row["evidence_reference"],
                        "material_type": row_category,
                        "discount_percent": row["raw_discount_percent"],
                        "discount_amount": row["raw_discount_amount"],
                    },
                }
            ).execute().data[0]

            if material_id and result_status in {"new", "updated"}:
                if supplier_id:
                    client.table("company_material_offers").update({"status": "superseded"}).eq(
                        "company_id", company_id
                    ).eq("company_material_id", material_id).eq("supplier_id", supplier_id).eq(
                        "status", "active"
                    ).execute()
                client.table("company_material_offers").insert(
                    {
                        "company_id": company_id,
                        "company_material_id": material_id,
                        "supplier_id": supplier_id,
                        "source_id": source_id,
                        "source_row_id": inserted_row["row_id"],
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
                    }
                ).execute()
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
        return source_id
    except Exception:
        cleanup_started = time.perf_counter()
        try:
            client.table("company_material_offers").delete().eq("source_id", source_id).execute()
            client.table("company_price_source_rows").delete().eq("source_id", source_id).execute()
            client.table("company_material_items").delete().eq("created_from_source_id", source_id).execute()
            client.table("company_price_sources").delete().eq("source_id", source_id).execute()
        except Exception:
            pass
        client.storage.from_(PRICE_SOURCE_BUCKET).remove([object_path])
        _emit_duration(trace, "server.price_source_cleanup", cleanup_started)
        raise
