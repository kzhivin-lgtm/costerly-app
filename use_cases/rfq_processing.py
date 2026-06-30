from __future__ import annotations

from collections.abc import Iterable
from typing import Any
import re

import pandas as pd

from agents.detection_agent import run_detection_agent
from db.repositories import (
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    insert_agent_usage_event,
    update_rfq_detected_object,
    upsert_rfq_detection_result,
)
from db.supabase_client import get_supabase_client
from use_cases.retry import read_with_retry


def process_uploaded_rfq(*, file_name: str, file_bytes: bytes, company_id: str) -> dict:
    """Run RFQ detection once and persist the validated result to Supabase."""
    detection_result = run_detection_agent(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
    )
    usage_event = detection_result.pop("_agent_usage", None)
    run_id = detection_result["rfq_run"]["run_id"]

    client = get_supabase_client()
    upsert_rfq_detection_result(client, detection_result)

    if usage_event:
        try:
            insert_agent_usage_event(client, usage_event)
        except Exception as exc:
            print(f"[Usage Ledger] Could not save detection usage: {exc}")

    return {
        "run_id": run_id,
        "detection_result": detection_result,
    }


def load_file_review_data(run_id: str) -> dict[str, Any]:
    """Load persisted detection data and adapt it for the File Review renderer."""
    client = get_supabase_client()
    run_df = read_with_retry(lambda: fetch_rfq_run(client, run_id))
    objects_df = read_with_retry(lambda: fetch_rfq_detected_objects(client, run_id))

    if run_df.empty:
        raise RuntimeError(f"RFQ run not found in Supabase: {run_id}")

    run = run_df.iloc[0].to_dict()
    objects = [row.to_dict() for _, row in objects_df.iterrows()]

    return {
        "run": _normalize_run(run),
        "objects": [_normalize_object(item) for item in objects],
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
    return {
        "project_name": run.get("project_name"),
        "partner": run.get("client_or_design_partner"),
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
        return [part.strip(" -•") for part in parts if part.strip(" -•")]

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict)):
        return [str(item).strip() for item in value if str(item).strip()]

    return [str(value)]


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
