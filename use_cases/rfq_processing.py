from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
import re
import time

import pandas as pd

from agents.anthropic_adapter import (
    build_detection_ocr_context,
    detection_naming_split_enabled,
)
from agents.detection_agent import run_detection_agent
from agents.naming_lab import (
    NAMING_LAB_VERSION,
    apply_name_mapping,
    build_locked_naming_input,
    ensure_unique_object_ids,
    run_naming_lab_call,
)
from agents.ocr_rendering import (
    direct_pdf_ocr_enabled,
    run_mistral_direct_pdf_evidence_ocr,
    run_mistral_document_evidence_ocr,
)
from db.repositories import (
    fetch_agent_usage_events,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    insert_agent_usage_event,
    update_rfq_detected_object,
    upsert_rfq_detection_result,
)
from db.supabase_client import get_supabase_client
from use_cases.retry import read_with_retry


def _runtime_event(
    *,
    agent_name: str,
    operation: str,
    company_id: str,
    run_id: str,
    file_name: str,
    model: str,
    prompt_version: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    raw_usage: dict[str, Any] | None = None,
    status: str = "succeeded",
) -> dict[str, Any]:
    usage = dict(raw_usage or {})
    usage["duration_seconds"] = duration_seconds
    return {
        "company_id": company_id,
        "run_id": run_id,
        "file_name": file_name,
        "object_id": None,
        "object_name": None,
        "agent_name": agent_name,
        "operation": operation,
        "model": model,
        "prompt_version": prompt_version,
        "input_tokens": 0,
        "output_tokens": 0,
        "input_cost_usd": None,
        "output_cost_usd": None,
        "total_cost_usd": None,
        "status": status,
        "duration_seconds": duration_seconds,
        "started_at": started_at,
        "finished_at": finished_at,
        "raw_usage": usage,
    }


def _ocr_storage_usage(
    ocr_package: dict[str, Any],
    *,
    detection_context: str | None = None,
) -> dict[str, Any]:
    """Build the complete, auditable OCR payload stored with the usage event."""
    return {
        "provider_usage": dict(ocr_package.get("usage") or {}),
        "ocr_result": ocr_package,
        "candidate_ocr_context": build_detection_ocr_context(ocr_package),
        "detection_context": detection_context
        if detection_context is not None
        else build_detection_ocr_context(ocr_package),
    }


def _run_optional_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return stored OCR diagnostics plus OCR evidence for Detection when available."""
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    try:
        if direct_pdf_ocr_enabled():
            package = run_mistral_direct_pdf_evidence_ocr(
                file_name=file_name,
                file_bytes=file_bytes,
            )
        else:
            package = run_mistral_document_evidence_ocr(
                file_name=file_name,
                file_bytes=file_bytes,
            )
    except Exception as exc:
        finished_at = datetime.now(UTC).isoformat()
        elapsed_seconds = round(time.perf_counter() - started, 3)
        error = str(exc)
        print(f"[OCR fallback] Detection will use the original file only: {error}")
        return (
            {
                "model": "mistral-ocr-4-0",
                "contract_version": "ocr_v2",
                "profile": "evidence",
                "status": "failed",
                "error": error,
                "pages": [],
                "evidence": {"text_blocks": [], "literal_items": []},
                "usage": {},
                "processing_seconds": elapsed_seconds,
                "started_at": started_at,
                "finished_at": finished_at,
            },
            None,
        )
    return package, package


def process_uploaded_rfq(
    *,
    file_name: str,
    file_bytes: bytes,
    company_id: str,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    """Run RFQ detection once and persist the validated result to Supabase."""
    cycle_started_at = datetime.now(UTC).isoformat()
    cycle_started = time.perf_counter()
    if progress_callback:
        progress_callback("OCR reading document")
    ocr_package, detection_ocr_package = _run_optional_ocr(
        file_name=file_name,
        file_bytes=file_bytes,
    )
    detection_context = build_detection_ocr_context(detection_ocr_package)
    if progress_callback:
        progress_callback("Detection Agent")
    detection_started = time.perf_counter()
    detection_result = run_detection_agent(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
        ocr_package=detection_ocr_package,
    )
    detection_seconds = round(time.perf_counter() - detection_started, 3)
    usage_event = detection_result.pop("_agent_usage", None)
    naming_seconds = 0.0
    naming_event = None
    if detection_naming_split_enabled() and detection_result["detected_objects"]:
        ensure_unique_object_ids(detection_result["detected_objects"])
        if progress_callback:
            progress_callback("Naming Agent")
        naming_started_at = datetime.now(UTC).isoformat()
        locked_objects = build_locked_naming_input(
            detection_result["detected_objects"],
            ocr_package,
        )
        naming_result = run_naming_lab_call(
            locked_objects,
            file_name=file_name,
            file_bytes=file_bytes,
        )
        naming_seconds = float(naming_result["duration_seconds"])
        apply_name_mapping(
            detection_result["detected_objects"],
            locked_objects,
            naming_result,
        )
        naming_event = _runtime_event(
            agent_name="naming",
            operation="locked_object_naming",
            company_id=company_id,
            run_id=detection_result["rfq_run"]["run_id"],
            file_name=file_name,
            model=str(naming_result["model"]),
            prompt_version=NAMING_LAB_VERSION,
            started_at=naming_started_at,
            finished_at=datetime.now(UTC).isoformat(),
            duration_seconds=naming_seconds,
            raw_usage={
                "input_tokens": naming_result["input_tokens"],
                "output_tokens": naming_result["output_tokens"],
                "validation": naming_result["validation"],
            },
        )
    run_id = detection_result["rfq_run"]["run_id"]

    if progress_callback:
        progress_callback("Saving results")
    client = get_supabase_client()
    upsert_rfq_detection_result(client, detection_result)

    ocr_seconds = float(ocr_package.get("processing_seconds") or 0)
    ocr_event = _runtime_event(
        agent_name="ocr",
        operation="document_ocr",
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        model=str(ocr_package.get("model") or "unknown"),
        prompt_version=str(ocr_package.get("contract_version") or "ocr_v2"),
        started_at=str(ocr_package.get("started_at") or cycle_started_at),
        finished_at=str(ocr_package.get("finished_at") or datetime.now(UTC).isoformat()),
        duration_seconds=ocr_seconds,
        raw_usage=_ocr_storage_usage(
            ocr_package,
            detection_context=detection_context,
        ),
        status="failed" if ocr_package.get("status") == "failed" else "succeeded",
    )

    for event, label in (
        (ocr_event, "OCR"),
        (usage_event, "Detection"),
        (naming_event, "Naming"),
    ):
        if not event:
            continue
        try:
            insert_agent_usage_event(client, event)
        except Exception as exc:
            print(f"[Usage Ledger] Could not save {label} usage: {exc}")

    cycle_finished_at = datetime.now(UTC).isoformat()
    total_seconds = round(time.perf_counter() - cycle_started, 3)
    cycle_event = _runtime_event(
        agent_name="orchestration",
        operation="rfq_processing_cycle",
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        model="deterministic",
        prompt_version="rfq_processing_v1",
        started_at=cycle_started_at,
        finished_at=cycle_finished_at,
        duration_seconds=total_seconds,
        raw_usage={
            "ocr_seconds": ocr_seconds,
            "detection_seconds": detection_seconds,
            "naming_seconds": naming_seconds,
        },
    )
    try:
        insert_agent_usage_event(client, cycle_event)
    except Exception as exc:
        print(f"[Usage Ledger] Could not save cycle timing: {exc}")

    return {
        "run_id": run_id,
        "detection_result": detection_result,
        "ocr_package": ocr_package,
        "timings": {
            "ocr_seconds": ocr_seconds,
            "detection_seconds": detection_seconds,
            "naming_seconds": naming_seconds,
            "total_seconds": total_seconds,
        },
    }


def load_file_review_data(run_id: str) -> dict[str, Any]:
    """Load persisted detection data and adapt it for the File Review renderer."""
    client = get_supabase_client()
    run_df = read_with_retry(lambda: fetch_rfq_run(client, run_id))
    objects_df = read_with_retry(lambda: fetch_rfq_detected_objects(client, run_id))
    usage_df = read_with_retry(lambda: fetch_agent_usage_events(client, run_id))

    if run_df.empty:
        raise RuntimeError(f"RFQ run not found in Supabase: {run_id}")

    run = run_df.iloc[0].to_dict()
    objects = [row.to_dict() for _, row in objects_df.iterrows()]

    return {
        "run": _normalize_run(run),
        "objects": [_normalize_object(item) for item in objects],
        "timings": _latest_runtime_timings(usage_df),
    }


def _latest_runtime_timings(usage_df: pd.DataFrame) -> dict[str, float] | None:
    if usage_df.empty:
        return None

    cycle_rows = usage_df[
        usage_df.get("operation", pd.Series(dtype=str)) == "rfq_processing_cycle"
    ]
    if cycle_rows.empty:
        return None

    row = cycle_rows.iloc[-1].to_dict()
    raw_usage = row.get("raw_usage")
    if isinstance(raw_usage, str):
        try:
            import json

            raw_usage = json.loads(raw_usage)
        except (TypeError, ValueError):
            raw_usage = {}
    if not isinstance(raw_usage, dict):
        raw_usage = {}

    total_seconds = row.get("duration_seconds")
    if total_seconds is None or pd.isna(total_seconds):
        total_seconds = raw_usage.get("duration_seconds", 0)

    return {
        "ocr_seconds": float(raw_usage.get("ocr_seconds") or 0),
        "detection_seconds": float(raw_usage.get("detection_seconds") or 0),
        "naming_seconds": float(raw_usage.get("naming_seconds") or 0),
        "total_seconds": float(total_seconds or 0),
    }


def apply_file_review_edits(
    *,
    run_id: str,
    object_edits: dict[str, dict[str, Any]],
) -> set[str]:
    """Save File Review object edits and return object ids ignored for estimation."""
    client = get_supabase_client()
    ignored_object_ids: set[str] = set()

    for object_id, edit in object_edits.items():
        if edit.get("ignored"):
            ignored_object_ids.add(str(object_id))

        values: dict[str, Any] = {}
        object_name = str(edit.get("name") or "").strip()
        quantity = _parse_quantity(edit.get("quantity"))

        if object_name:
            values["object_name"] = object_name
        if quantity is not None:
            values["quantity"] = quantity

        if values:
            update_rfq_detected_object(
                client,
                run_id=run_id,
                object_id=str(object_id),
                values=values,
            )

    return ignored_object_ids


def _normalize_run(run: dict[str, Any]) -> dict[str, Any]:
    """Convert the Supabase RFQ row to the compact UI contract."""
    partner = run.get("design_partner")
    if partner is None or partner == "":
        partner = run.get("client_or_design_partner")
    return {
        "project_name": run.get("project_name"),
        "partner": partner,
        "client": run.get("client"),
        "file_quality": run.get("file_quality_label"),
        "file_name": run.get("file_name"),
        "pages_detected": run.get("pages_detected"),
        "source_type": run.get("source_type"),
        "author": run.get("author"),
        "document_date": run.get("document_date"),
        "language": run.get("language"),
        "file_quality_confidence": _percent(run.get("file_quality_confidence")),
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "missing_information": _split_notes(run.get("missing_information")),
    }


def _normalize_object(item: dict[str, Any]) -> dict[str, Any]:
    """Convert one Supabase detected object row to the File Review card contract."""
    dimensions = item.get("dimensions_json")
    if isinstance(dimensions, str):
        dimensions = {}
    if not isinstance(dimensions, dict):
        dimensions = {}

    return {
        "object_id": item.get("object_id"),
        "name": item.get("object_name"),
        "quantity": _clean_number(item.get("quantity")),
        "confidence": _percent(item.get("confidence")),
        "dimensions": _format_dimensions(dimensions),
        "materials": item.get("detected_materials"),
        "notes": _split_notes(item.get("notes")),
    }


def _split_notes(value: Any) -> list[str]:
    """Normalize agent note strings into bullet-list items for UI rendering."""
    if value is None or _is_missing(value):
        return []

    if isinstance(value, str):
        normalized = value.replace("\n", ";")
        normalized = re.sub(r"(?<=[.!?])\s+(?=[A-ZА-Я])", ";", normalized)
        parts = normalized.split(";")
        return _normalize_note_items(parts)

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict)):
        return _normalize_note_items(str(item) for item in value)

    return _normalize_note_items([str(value)])


def _normalize_note_items(values: Iterable[str]) -> list[str]:
    items = []
    for value in values:
        item = _normalize_note_item(value)
        if item:
            items.append(item)
    return items


def _normalize_note_item(value: str) -> str:
    """Apply File Review bullet copy style."""
    item = value.strip(" -•")
    while item.endswith("."):
        item = item[:-1].rstrip()
    if not item:
        return ""
    return item[0].lower() + item[1:]


def _format_dimensions(dimensions: dict[str, Any]) -> str:
    raw_text = dimensions.get("raw_text")
    if raw_text and not _is_missing(raw_text):
        return str(raw_text)

    unit = dimensions.get("unit") or "mm"
    parts = []
    labels = [
        ("W", dimensions.get("width")),
        ("D", dimensions.get("depth")),
        ("H", dimensions.get("height")),
    ]
    for label, value in labels:
        if value and not _is_missing(value):
            parts.append(f"{label} {_clean_number(value)}")

    if not parts:
        return "—"

    return " × ".join(parts) + f" {unit}"


def _percent(value: Any) -> str:
    if value is None or _is_missing(value):
        return "—"
    return f"{_clean_number(value)}%"


def _clean_number(value: Any) -> str:
    if value is None or _is_missing(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(number)


def _parse_quantity(value: Any) -> float | None:
    """Parse user-entered quantity without failing the whole review save."""
    if value is None or _is_missing(value):
        return None
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _is_missing(value: Any) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
