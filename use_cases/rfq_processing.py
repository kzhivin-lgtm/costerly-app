from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
import json
import math
import re
import time

import pandas as pd

from agents.anthropic_adapter import (
    DetectionVisualRegistryValidationError,
    build_detection_ocr_context,
    detection_naming_split_enabled,
    get_secret,
)
from agents.detection_agent import run_detection_agent
from agents.document_identity import (
    DOCUMENT_IDENTITY_VERSION,
    document_identity_multilingual_signal,
    derive_document_identity_from_ocr,
    merge_document_identity_fallback,
    run_document_identity_call,
)
from agents.detection_page_images import (
    DEFAULT_PAGE_IMAGE_DPI,
    estimated_inline_pdf_bytes,
    render_detection_pdf_pages,
    should_use_detection_page_images,
)
from agents.naming_lab import (
    NAMING_LAB_VERSION,
    apply_name_mapping,
    assign_ocr_drawing_indices,
    build_locked_naming_input,
    ensure_provisional_object_names,
    ensure_unique_object_ids,
    run_naming_lab_call,
)
from agents.ocr_rendering import (
    run_mistral_document_evidence_ocr,
)
from agents.ocr_adapter import DEFAULT_MISTRAL_OCR_MODEL
from config import agent_cost_category, calculate_llm_cost_usd, calculate_ocr_page_cost_usd
from db.repositories import (
    fetch_deferred_naming_status,
    fetch_deferred_document_identity_status,
    fetch_deferred_preview_status,
    fetch_agent_usage_events,
    fetch_rfq_detected_objects,
    fetch_rfq_detected_object_names,
    fetch_rfq_run,
    insert_agent_usage_event,
    insert_agent_usage_event_returning_id,
    insert_agent_usage_events,
    update_rfq_detected_object,
    update_rfq_detected_object_name_if_unchanged,
    update_rfq_run,
    update_rfq_run_field_if_unchanged,
    upsert_rfq_detection_result,
)
from db.supabase_client import get_supabase_client
from db.company_access import assert_run_owned
from state.session import get_company_id
from use_cases.retry import read_with_retry
from use_cases.platform_admin import record_rfq_upload
from use_cases.estimation_originals import persist_estimation_original
from use_cases.detection_previews import create_detection_previews


_DIAGNOSTICS_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="rfq-diagnostics",
)
_NAMING_EXECUTOR = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="rfq-naming",
)
_PREVIEW_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rfq-preview")


def _usage_cost_total(events: Iterable[dict[str, Any]]) -> float | None:
    """Sum provider-recorded token cost without inventing a price for OCR or IO."""
    costs: list[float] = []
    for event in events:
        if not isinstance(event, dict) or str(event.get("status") or "") != "succeeded":
            continue
        try:
            cost = float(event.get("total_cost_usd"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(cost) and cost >= 0:
            costs.append(cost)
    return round(sum(costs), 6) if costs else None


def _object_lock_log(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Record the immutable quote-unit decision before Naming can change labels."""
    return [
        {
            "object_id": str(item.get("object_id") or ""),
            "creator_label": str(item.get("object_name") or ""),
            "quantity": item.get("quantity"),
            "evidence_pages": list(item.get("evidence_page_refs") or []),
            "review_required": bool(item.get("review_required")),
        }
        for item in objects
        if isinstance(item, dict)
    ]


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
    usage["cost_category"] = agent_cost_category(agent_name)
    costs = {"input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None}
    if agent_name in {"naming", "document_identity"}:
        costs = calculate_llm_cost_usd(
            model=model,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
        )
    elif agent_name == "ocr":
        provider_usage = usage.get("provider_usage")
        if not isinstance(provider_usage, dict):
            provider_usage = {}
        try:
            pages_processed = int(provider_usage.get("pages_processed") or 0)
        except (TypeError, ValueError):
            pages_processed = -1
        costs = calculate_ocr_page_cost_usd(
            model=model,
            pages_processed=pages_processed,
        )
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
        **costs,
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


def _persist_rfq_diagnostics(
    *,
    client: Any,
    ocr_package: dict[str, Any],
    detection_context: str,
    usage_events: list[dict[str, Any]] | None,
    naming_event: dict[str, Any] | None,
    cycle_event: dict[str, Any],
    company_id: str,
    run_id: str,
    file_name: str,
    cycle_started_at: str,
) -> None:
    """Persist large OCR and runtime diagnostics outside the review critical path."""
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
    events = [*(usage_events or []), *(event for event in (naming_event, cycle_event) if event)]
    try:
        insert_agent_usage_events(client, events)
    except Exception as exc:
        print(f"[Usage Ledger] Could not save RFQ diagnostics: {exc}")


def _persist_detection_audit_before_file_review(
    *,
    client: Any,
    usage_events: list[dict[str, Any]],
) -> None:
    """Durably store the Registry audit before exposing File Review.

    The Registry response contains the only complete record of router choice,
    Islands, roles, evidence, graph decisions and model reasoning.  It cannot
    be relegated to the best-effort diagnostics executor, because its failure
    would leave an apparently successful File Review without an analyzable
    Detection decision.
    """
    for event in usage_events:
        try:
            insert_agent_usage_event(client, event)
        except Exception as exc:
            raise RuntimeError(
                "Detection audit could not be saved; File Review was not shown."
            ) from exc


def _persist_runtime_event(event: dict[str, Any]) -> None:
    """Persist a lightweight runtime marker outside the UI render path."""
    try:
        insert_agent_usage_event(get_supabase_client(), event)
    except Exception as exc:
        print(f"[Usage Ledger] Could not save runtime marker: {exc}")


def _run_optional_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return stored OCR diagnostics plus OCR evidence for Detection when available."""
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    try:
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
                "model": DEFAULT_MISTRAL_OCR_MODEL,
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


def _run_deferred_naming(
    *,
    client: Any,
    detected_objects: list[dict[str, Any]],
    locked_objects: list[dict[str, Any]],
    company_id: str,
    run_id: str,
    file_name: str,
    file_bytes: bytes = b"",
    page_images: list[bytes] | None = None,
    annotated_visual_pages_by_number: dict[int, bytes] | None = None,
    object_source_crops_by_id: dict[str, dict[str, Any]] | None = None,
    provisional_project_name: str | None = None,
) -> dict[str, Any]:
    """Name locked objects after File Review is allowed to open."""
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    persistence_audit: dict[str, Any] = {"write_attempts": []}
    print(f"[Naming Agent] Started deferred naming for run {run_id}")
    try:
        wanted_pages = {
            int(page)
            for item in locked_objects
            for page in item.get("evidence_pages") or []
            if isinstance(page, int) and page > 0
        }
        if annotated_visual_pages_by_number:
            visual_pages = dict(annotated_visual_pages_by_number)
        else:
            source_pages = page_images
            if source_pages is None and file_bytes and file_name.lower().endswith(".pdf"):
                source_pages, _ = render_detection_pdf_pages(file_bytes)
            elif source_pages is None and file_bytes:
                source_pages = [file_bytes]
            elif source_pages is None:
                source_pages = []
            visual_pages = {
                number: source_pages[number - 1]
                for number in wanted_pages
                if number <= len(source_pages)
            }
        naming_kwargs: dict[str, Any] = {}
        if visual_pages:
            naming_kwargs["visual_pages_by_number"] = visual_pages
        if object_source_crops_by_id:
            naming_kwargs["object_source_crops_by_id"] = object_source_crops_by_id
        naming_result = run_naming_lab_call(locked_objects, **naming_kwargs)
        apply_name_mapping(detected_objects, locked_objects, naming_result)
        names: dict[str, str] = {}
        for provisional, named in zip(locked_objects, detected_objects, strict=True):
            object_id = str(named.get("object_id") or "")
            old_name = str(
                provisional.get("persisted_name") or provisional.get("current_name") or ""
            )
            new_name = str(named.get("object_name") or old_name)
            persisted = update_rfq_detected_object_name_if_unchanged(
                client,
                run_id=run_id,
                object_id=object_id,
                expected_name=old_name,
                object_name=new_name,
            )
            persistence_audit["write_attempts"].append(
                {
                    "object_id": object_id,
                    "expected_name": old_name,
                    "requested_name": new_name,
                    "accepted": persisted,
                }
            )
            if not persisted:
                raise RuntimeError(
                    "Naming result was not persisted because the provisional object name changed."
                )
            names[object_id] = new_name

        readback_names = {
            str(row.get("object_id") or ""): str(row.get("object_name") or "")
            for row in fetch_rfq_detected_object_names(client, run_id)
            if str(row.get("object_id") or "")
        }
        readback_mismatches = [
            {
                "object_id": object_id,
                "requested_name": requested_name,
                "readback_name": readback_names.get(object_id, ""),
            }
            for object_id, requested_name in names.items()
            if readback_names.get(object_id) != requested_name
        ]
        persistence_audit["immediate_readback_names"] = readback_names
        persistence_audit["readback_mismatches"] = readback_mismatches
        if readback_mismatches:
            failed_ids = ", ".join(item["object_id"] for item in readback_mismatches)
            raise RuntimeError(
                "Naming persistence read-back mismatch for object IDs: "
                f"{failed_ids}."
            )

        # Project identity belongs exclusively to Document Identity or a user
        # edit. Naming publishes Object names only, even for a one-object RFQ.
        persistence_audit["project_name_fallback"] = {
            "accepted": False,
            "reason": "owned_by_document_identity",
        }

        naming_seconds = float(naming_result["duration_seconds"])
        naming_event = _runtime_event(
            agent_name="naming",
            operation="locked_object_naming_deferred",
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            model=str(naming_result["model"]),
            prompt_version=NAMING_LAB_VERSION,
            started_at=started_at,
            finished_at=datetime.now(UTC).isoformat(),
            duration_seconds=naming_seconds,
            raw_usage={
                "input_tokens": naming_result["input_tokens"],
                "output_tokens": naming_result["output_tokens"],
                "names": names,
                "validation": naming_result["validation"],
                "naming_decision_audit": naming_result.get("naming_decision_audit", []),
                "persistence_audit": persistence_audit,
                "deferred": True,
            },
        )
        insert_agent_usage_event(client, naming_event)
        return {
            "status": "succeeded",
            "names": names,
            "naming_seconds": naming_seconds,
            "token_cost": _usage_cost_total([naming_event]),
        }
    except Exception as exc:
        finished_at = datetime.now(UTC).isoformat()
        naming_seconds = round(time.perf_counter() - started, 3)
        error = str(exc)
        print(f"[Naming Agent] Deferred naming failed for run {run_id}: {error}")
        failure_event = _runtime_event(
            agent_name="naming",
            operation="locked_object_naming_deferred",
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            model="unknown",
            prompt_version=NAMING_LAB_VERSION,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=naming_seconds,
            raw_usage={
                "deferred": True,
                "error": error,
                "persistence_audit": persistence_audit,
            },
            status="failed",
        )
        try:
            insert_agent_usage_event(client, failure_event)
        except Exception as telemetry_exc:
            print(
                "[Naming Agent] Could not persist failure telemetry for run "
                f"{run_id}: {telemetry_exc}"
            )
        return {
            "status": "failed",
            "names": {},
            "naming_seconds": naming_seconds,
            "error": error,
        }


def _run_deferred_document_identity(
    *,
    client: Any,
    company_id: str,
    run_id: str,
    file_name: str,
    ocr_package: dict[str, Any],
    page_images: list[bytes] | None = None,
) -> dict[str, Any]:
    """Fill explicit document fields after File Review is already available."""
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    persistence_audit: list[dict[str, Any]] = []
    try:
        result = derive_document_identity_from_ocr(ocr_package)
        identity = result["identity"]
        visual_fallback: dict[str, Any] | None = None
        fallback_error = ""
        language_signal = document_identity_multilingual_signal(ocr_package)
        if page_images and bool(language_signal["eligible"]):
            try:
                visual_fallback = run_document_identity_call(page_images=page_images)
                identity = merge_document_identity_fallback(
                    identity, visual_fallback["identity"],
                )
            except Exception as exc:
                # Identity is supplementary metadata. A visual fallback cannot
                # invalidate Detection or discard the deterministic fields.
                fallback_error = str(exc)
        for field, evidence in identity.items():
            value = str(evidence.get("value") or "unknown")
            if value == "unknown":
                persistence_audit.append({"field": field, "value": value, "persisted": False})
                continue
            persisted = update_rfq_run_field_if_unchanged(
                client,
                run_id=run_id,
                field=field,
                expected_value="unknown",
                value=value,
            )
            persistence_audit.append({"field": field, "value": value, "persisted": persisted})
        event = _runtime_event(
            agent_name="document_identity",
            operation="document_identity_deferred",
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            model=str((visual_fallback or result)["model"]),
            prompt_version=DOCUMENT_IDENTITY_VERSION,
            started_at=started_at,
            finished_at=datetime.now(UTC).isoformat(),
            duration_seconds=(
                float(result["duration_seconds"])
                + float((visual_fallback or {}).get("duration_seconds") or 0)
            ),
            raw_usage={
                "input_tokens": (
                    int(result["input_tokens"])
                    + int((visual_fallback or {}).get("input_tokens") or 0)
                ),
                "output_tokens": (
                    int(result["output_tokens"])
                    + int((visual_fallback or {}).get("output_tokens") or 0)
                ),
                "identity": identity,
                "crop_audit": (visual_fallback or result)["crop_audit"],
                "visual_fallback": {
                    "attempted": visual_fallback is not None or bool(fallback_error),
                    "succeeded": visual_fallback is not None,
                    "error": fallback_error,
                    "language_signal": language_signal,
                },
                "persistence_audit": persistence_audit,
                "deferred": True,
            },
        )
        insert_agent_usage_event(client, event)
        return {"status": "succeeded", "identity": identity}
    except Exception as exc:
        duration_seconds = round(time.perf_counter() - started, 3)
        error = str(exc)
        print(f"[Document Identity] Deferred metadata failed for run {run_id}: {error}")
        event = _runtime_event(
            agent_name="document_identity",
            operation="document_identity_deferred",
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            model="unknown",
            prompt_version=DOCUMENT_IDENTITY_VERSION,
            started_at=started_at,
            finished_at=datetime.now(UTC).isoformat(),
            duration_seconds=duration_seconds,
            raw_usage={"deferred": True, "error": error, "persistence_audit": persistence_audit},
            status="failed",
        )
        try:
            insert_agent_usage_event(client, event)
        except Exception as telemetry_exc:
            print(f"[Document Identity] Could not persist failure telemetry: {telemetry_exc}")
        return {"status": "failed", "error": error}


def assign_server_run_id(detection_result: dict[str, Any]) -> str:
    """Replace a model-generated RFQ key with a globally unique server key."""
    run_id = f"run_{uuid4().hex}"
    detection_result["rfq_run"]["run_id"] = run_id
    for detected_object in detection_result["detected_objects"]:
        detected_object["run_id"] = run_id
    return run_id


def process_uploaded_rfq(
    *,
    file_name: str,
    file_bytes: bytes,
    company_id: str,
    user_id: str | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> dict:
    """Run RFQ detection once and persist the validated result to Supabase."""
    cycle_started_at = datetime.now(UTC).isoformat()
    cycle_started = time.perf_counter()
    stage_ledger: list[dict[str, Any]] = []
    active_stage: dict[str, Any] | None = None
    progress_plan_input: dict[str, Any] | None = None

    def stage_id(label: str) -> str:
        if label == "Preparing document pages":
            return "page_preparation"
        if label == "OCR reading document":
            return "ocr"
        if label == "Fusion and route started":
            return "fusion_and_route"
        if label == "Detection Registry started":
            return "discovery_preparation"
        if label.startswith("Discovery"):
            return "discovery"
        if label == "Membership review started":
            return "membership_review"
        if label == "Registry assembly started":
            return "registry_and_evidence"
        if label == "Saving results":
            return "publish_file_review"
        return "orchestration"

    def emit_progress(
        label: str,
        page_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record one transition and forward it to the visual-only screen."""
        nonlocal active_stage, progress_plan_input
        now = time.perf_counter()
        if active_stage is not None:
            stage_ledger.append({
                **active_stage,
                "duration_seconds": round(now - float(active_stage["started_at_monotonic"]), 3),
            })
        active_stage = {
            "stage": stage_id(label),
            "label": label,
            "started_at_monotonic": now,
        }
        if page_count is not None:
            active_stage["page_count"] = int(page_count)
        progress_metadata = dict(metadata or {})
        progress_metadata["elapsed_seconds"] = round(now - cycle_started, 3)
        if progress_metadata:
            active_stage["metadata"] = progress_metadata
        if label == "Processing plan prepared" and metadata:
            progress_plan_input = dict(metadata)
        if progress_callback:
            progress_callback(label, page_count, progress_metadata)

    def finalize_stage_ledger() -> list[dict[str, Any]]:
        if active_stage is not None:
            stage_ledger.append({
                **active_stage,
                "duration_seconds": round(
                    time.perf_counter() - float(active_stage["started_at_monotonic"]), 3,
                ),
            })
        return [
            {key: value for key, value in row.items() if key != "started_at_monotonic"}
            for row in stage_ledger
        ]

    client = get_supabase_client()
    try:
        record_rfq_upload(
            client,
            company_id=company_id,
            user_id=user_id,
            file_bytes=file_bytes,
        )
    except Exception as exc:
        print(f"[Product Analytics] Could not record RFQ upload: {exc}")
    original_future = _DIAGNOSTICS_EXECUTOR.submit(
        persist_estimation_original,
        client=client,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )
    page_images = None
    page_image_diagnostics: dict[str, Any] = {}
    use_page_images = should_use_detection_page_images(
        file_name=file_name,
        file_bytes=file_bytes,
    )
    if use_page_images:
        emit_progress("Preparing document pages")
        page_images, page_image_diagnostics = render_detection_pdf_pages(file_bytes)
        ocr_package = {
            "provider": "none",
            "model": "none",
            "contract_version": "jpeg_pages_v1",
            "status": "skipped_for_large_jpeg_route",
            "file_name": file_name,
            "page_count": len(page_images),
            "processing_seconds": 0.0,
            "started_at": cycle_started_at,
            "finished_at": datetime.now(UTC).isoformat(),
            "pages": [],
            "evidence": {"text_blocks": [], "literal_items": []},
            "usage": {},
        }
        detection_ocr_package = None
    else:
        emit_progress("OCR reading document")
        ocr_package, detection_ocr_package = _run_optional_ocr(
            file_name=file_name,
            file_bytes=file_bytes,
        )
    detection_context = build_detection_ocr_context(detection_ocr_package)
    if page_images:
        page_count = len(page_images)
    else:
        pages = ocr_package.get("pages")
        page_count = len(pages) if isinstance(pages, list) and pages else None
    emit_progress("Fusion and route started", page_count)
    detection_started = time.perf_counter()
    try:
        detection_result = run_detection_agent(
            file_name=file_name,
            company_id=company_id,
            file_bytes=file_bytes,
            ocr_package=detection_ocr_package,
            page_images=page_images,
            page_image_diagnostics=page_image_diagnostics,
            # V6.12 categorizes the completed OCR/Fusion package before any
            # Detection model call and selects the scenario-owned model.
            model=None,
            stage_callback=lambda label, metadata=None: emit_progress(
                label, page_count, metadata,
            ),
        )
    except DetectionVisualRegistryValidationError as exc:
        try:
            insert_agent_usage_event(client, exc.usage_event)
        except Exception as telemetry_exc:
            print(
                "[Detection] Could not persist visual-registry validation audit: "
                f"{telemetry_exc}"
            )
        raise
    detection_seconds = round(time.perf_counter() - detection_started, 3)
    naming_annotated_pages = detection_result.pop("_naming_annotated_pages", None)
    naming_source_crops = detection_result.pop("_naming_source_crops", None)
    usage_events = detection_result.pop("_agent_usage_events", [])
    legacy_usage_event = detection_result.pop("_agent_usage", None)
    if isinstance(legacy_usage_event, dict):
        usage_events.append(legacy_usage_event)
    # A model-generated run_id is not globally unique. In multi-company mode,
    # mint it on the server before any service-role upsert can overwrite another
    # company's RFQ with the same model-generated value.
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assign_server_run_id(detection_result)
    # Detection records its usage before authenticated persistence mints the
    # server run ID. Keep every later stage on the same correlation key.
    for usage_event in usage_events:
        usage_event["run_id"] = detection_result["rfq_run"]["run_id"]
    detection_token_cost = _usage_cost_total(usage_events)
    naming_seconds = 0.0
    naming_future = None
    document_identity_future = None
    locked_objects = None
    if detection_naming_split_enabled() and detection_result["detected_objects"]:
        ensure_unique_object_ids(detection_result["detected_objects"])
        ensure_provisional_object_names(detection_result["detected_objects"])
        # Source codes are useful Naming evidence, but not an interim File
        # Review label. Keep persisted Detection objects neutral until terminal
        # Naming applies the code and category together.
        naming_source_objects = deepcopy(detection_result["detected_objects"])
        for source, persisted in zip(
            naming_source_objects,
            detection_result["detected_objects"],
            strict=True,
        ):
            source["_persisted_object_name"] = str(persisted.get("object_name") or "")
        assign_ocr_drawing_indices(naming_source_objects, ocr_package)
        locked_objects = build_locked_naming_input(
            naming_source_objects,
            ocr_package,
        )
    run_id = detection_result["rfq_run"]["run_id"]

    _persist_detection_audit_before_file_review(
        client=client,
        usage_events=usage_events,
    )

    emit_progress("Saving results")
    upsert_rfq_detection_result(client, detection_result)
    preview_future = None
    if detection_result["detected_objects"]:
        preview_future = _PREVIEW_EXECUTOR.submit(
            create_detection_previews,
            client=client, company_id=company_id, run_id=run_id,
            file_name=file_name, file_bytes=file_bytes,
            objects=deepcopy(detection_result["detected_objects"]),
            ocr_package=deepcopy(ocr_package), page_images=page_images,
        )
    if ocr_package:
        document_identity_future = _NAMING_EXECUTOR.submit(
            _run_deferred_document_identity,
            client=client,
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            ocr_package=deepcopy(ocr_package),
            page_images=deepcopy(page_images),
        )
    if locked_objects is not None:
        naming_future = _NAMING_EXECUTOR.submit(
            _run_deferred_naming,
            client=client,
            detected_objects=deepcopy(detection_result["detected_objects"]),
            locked_objects=locked_objects,
            company_id=company_id,
            run_id=run_id,
            file_name=file_name,
            file_bytes=file_bytes,
            annotated_visual_pages_by_number=deepcopy(naming_annotated_pages)
            if isinstance(naming_annotated_pages, dict) else None,
            object_source_crops_by_id=deepcopy(naming_source_crops)
            if isinstance(naming_source_crops, dict) else None,
            provisional_project_name=str(detection_result["rfq_run"].get("project_name") or ""),
        )

    ocr_seconds = float(ocr_package.get("processing_seconds") or 0)
    render_seconds = float(page_image_diagnostics.get("render_seconds") or 0)
    rendered_page_dpi = int(
        page_image_diagnostics.get("requested_dpi")
        or page_image_diagnostics.get("dpi")
        or DEFAULT_PAGE_IMAGE_DPI
    )
    document_route = (
        f"jpeg_pages_{rendered_page_dpi}dpi_haiku_4_5"
        if use_page_images else "inline_base64"
    )
    cycle_finished_at = datetime.now(UTC).isoformat()
    total_seconds = round(time.perf_counter() - cycle_started, 3)
    cycle_event = _runtime_event(
        agent_name="orchestration",
        operation="rfq_processing_cycle",
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        model="deterministic",
        prompt_version="rfq_processing_deferred_naming",
        started_at=cycle_started_at,
        finished_at=cycle_finished_at,
        duration_seconds=total_seconds,
        raw_usage={
            "ocr_seconds": ocr_seconds,
            "render_seconds": render_seconds,
            "document_route": document_route,
            "source_bytes": len(file_bytes),
            "estimated_inline_pdf_bytes": estimated_inline_pdf_bytes(file_bytes),
            # Normal PDFs obtain their pages from OCR, while JPEG-origin files
            # use rendered-page diagnostics. Persist the actual count for both
            # so the next file can use a compatible historical F forecast.
            "page_count": int(
                page_count
                or page_image_diagnostics.get("page_count")
                or 0
            ),
            "detection_seconds": detection_seconds,
            "naming_seconds": naming_seconds,
            "naming_deferred": naming_future is not None,
            "document_identity_deferred": document_identity_future is not None,
            "preview_deferred": preview_future is not None,
            "object_lock_log": _object_lock_log(detection_result["detected_objects"]),
            "stage_aware_progress_plan_input": progress_plan_input,
            "v6_43_processing_stage_ledger": finalize_stage_ledger(),
        },
    )
    ocr_event = _runtime_event(
        agent_name="ocr",
        operation="document_ocr",
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        model=str(ocr_package.get("model") or "unknown"),
        prompt_version=str(ocr_package.get("contract_version") or "ocr_v2"),
        started_at=str(ocr_package.get("started_at") or cycle_started_at),
        finished_at=str(ocr_package.get("finished_at") or cycle_finished_at),
        duration_seconds=ocr_seconds,
        raw_usage=_ocr_storage_usage(ocr_package, detection_context=detection_context),
        status="failed" if ocr_package.get("status") == "failed" else "succeeded",
    )
    ocr_cost = _usage_cost_total([ocr_event])
    tc1 = round((detection_token_cost or 0) + (ocr_cost or 0), 6)
    ocr_event_id = None
    try:
        ocr_event_id = insert_agent_usage_event_returning_id(client, ocr_event)
    except Exception as exc:
        print(f"[Estimation] Could not persist OCR handoff event: {exc}")
    original = None
    original_wait_started = time.perf_counter()
    try:
        original = original_future.result()
    except Exception as exc:
        print(f"[Estimation Original] Could not store source: {exc}")
    cycle_event["raw_usage"]["post_cycle_estimation_original_wait_seconds"] = round(
        time.perf_counter() - original_wait_started,
        3,
    )
    _DIAGNOSTICS_EXECUTOR.submit(
        _persist_rfq_diagnostics,
        client=client,
        ocr_package=ocr_package,
        detection_context=detection_context,
        usage_events=[],
        naming_event=None,
        cycle_event=cycle_event,
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        cycle_started_at=cycle_started_at,
    )

    return {
        "run_id": run_id,
        "detection_result": detection_result,
        "ocr_package": ocr_package,
        "ocr_event_id": ocr_event_id,
        "original": original,
        "naming_future": naming_future,
        "document_identity_future": document_identity_future,
        "preview_future": preview_future,
        "timings": {
            "ocr_seconds": ocr_seconds,
            "render_seconds": render_seconds,
            "document_route": document_route,
            "detection_seconds": detection_seconds,
            "naming_seconds": naming_seconds,
            # Backwards-compatible alias. TC1 covers every completed
            # Detection request, including page-priced OCR.
            "token_cost": tc1,
            "detection_cost": tc1,
            "naming_status": "pending" if naming_future is not None else "not_started",
            "total_seconds": total_seconds,
        },
    }


def load_file_review_data(run_id: str) -> dict[str, Any]:
    """Load persisted detection data and adapt it for the File Review renderer."""
    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assert_run_owned(client, run_id, get_company_id())
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


def record_file_review_first_render(
    *,
    company_id: str,
    run_id: str,
    file_name: str,
    processing_to_render_seconds: float,
) -> None:
    """Record the first server-side File Review render without delaying it."""
    event = _runtime_event(
        agent_name="orchestration",
        operation="file_review_first_render",
        company_id=company_id,
        run_id=run_id,
        file_name=file_name,
        model="deterministic",
        prompt_version="file_review_handoff_timing_v1",
        started_at=datetime.now(UTC).isoformat(),
        finished_at=datetime.now(UTC).isoformat(),
        duration_seconds=round(processing_to_render_seconds, 3),
        raw_usage={
            "processing_to_file_review_first_render_seconds": round(
                processing_to_render_seconds,
                3,
            ),
        },
    )
    _DIAGNOSTICS_EXECUTOR.submit(_persist_runtime_event, event)


def load_file_review_naming_publication(run_id: str) -> dict[str, Any]:
    """Read the durable deferred-Naming result without reloading File Review.

    The Naming worker saves object names before it writes its terminal ledger
    entry.  A terminal event therefore makes the narrow name query safe and
    avoids invalidating the Detection result or the preview cache.
    """
    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assert_run_owned(client, run_id, get_company_id())

    event = fetch_deferred_naming_status(client, run_id)
    if not event:
        return {"status": "pending"}

    status = str(event.get("status") or "failed")
    raw_usage = event.get("raw_usage") or {}
    if isinstance(raw_usage, str):
        try:
            raw_usage = json.loads(raw_usage)
        except (TypeError, ValueError):
            raw_usage = {}
    try:
        duration_seconds = float(
            event.get("duration_seconds")
            or (raw_usage.get("duration_seconds") if isinstance(raw_usage, dict) else 0)
            or 0
        )
    except (TypeError, ValueError):
        duration_seconds = 0.0
    if status != "succeeded":
        return {
            "status": "failed",
            "naming_seconds": duration_seconds,
            "error": str(raw_usage.get("error") or "Naming did not complete."),
        }

    names = {
        str(row.get("object_id") or ""): str(row.get("object_name") or "")
        for row in fetch_rfq_detected_object_names(client, run_id)
        if str(row.get("object_id") or "")
    }
    token_cost = _usage_cost_total([{
        "status": status,
        "total_cost_usd": event.get("total_cost_usd"),
    }])
    return {
        "status": "succeeded",
        "names": names,
        "naming_seconds": duration_seconds,
        "token_cost": token_cost,
    }


def load_file_review_document_identity_publication(run_id: str) -> dict[str, Any]:
    """Read the terminal document-identity result for the live review card."""
    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assert_run_owned(client, run_id, get_company_id())

    event = fetch_deferred_document_identity_status(client, run_id)
    if not event:
        return {"status": "pending"}
    status = str(event.get("status") or "failed")
    if status != "succeeded":
        raw_usage = event.get("raw_usage") or {}
        if isinstance(raw_usage, str):
            try:
                raw_usage = json.loads(raw_usage)
            except (TypeError, ValueError):
                raw_usage = {}
        return {
            "status": "failed",
            "error": str(raw_usage.get("error") or "Document identity did not complete."),
        }

    run_df = fetch_rfq_run(client, run_id)
    if run_df.empty:
        return {"status": "failed", "error": "RFQ run was not found."}
    run = _normalize_run(run_df.iloc[0].to_dict())
    return {
        "status": "succeeded",
        "metadata": {
            field: str(run.get(field) or "unknown")
            for field in ("project_name", "partner", "client")
        },
    }


def load_file_review_preview_publication(run_id: str) -> dict[str, Any]:
    """Read the durable terminal Preview result without reloading File Review."""
    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assert_run_owned(client, run_id, get_company_id())

    event = fetch_deferred_preview_status(client, run_id)
    if not event:
        return {"status": "pending"}

    raw_usage = event.get("raw_usage") or {}
    if isinstance(raw_usage, str):
        try:
            raw_usage = json.loads(raw_usage)
        except (TypeError, ValueError):
            raw_usage = {}
    try:
        duration_seconds = float(
            event.get("duration_seconds")
            or (raw_usage.get("duration_seconds") if isinstance(raw_usage, dict) else 0)
            or 0
        )
    except (TypeError, ValueError):
        duration_seconds = 0.0
    return {
        "status": str(event.get("status") or "failed"),
        "preview_seconds": duration_seconds,
    }


def build_file_review_data(
    detection_result: dict[str, Any],
    *,
    timings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapt the just-persisted Detection result for first File Review render.

    Processing already owns this validated payload. Reusing it avoids an
    immediate ownership lookup plus three sequential reads of the same run.
    Later renders and restored sessions continue to use load_file_review_data().
    """
    run = detection_result.get("rfq_run") or {}
    objects = detection_result.get("detected_objects") or []
    return {
        "run": _normalize_run(run if isinstance(run, dict) else {}),
        "objects": [
            _normalize_object(item)
            for item in objects
            if isinstance(item, dict)
        ],
        "timings": dict(timings or {}),
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

    naming_rows = usage_df[
        usage_df.get("operation", pd.Series(dtype=str)) == "locked_object_naming_deferred"
    ]
    naming_seconds = float(raw_usage.get("naming_seconds") or 0)
    if not naming_rows.empty:
        naming_row = naming_rows.iloc[-1]
        if str(naming_row.get("status") or "") == "succeeded":
            candidate = naming_row.get("duration_seconds")
            if candidate is None or pd.isna(candidate):
                naming_usage = naming_row.get("raw_usage") or {}
                if isinstance(naming_usage, str):
                    try:
                        naming_usage = json.loads(naming_usage)
                    except (TypeError, ValueError):
                        naming_usage = {}
                if isinstance(naming_usage, dict):
                    candidate = naming_usage.get("duration_seconds")
            if candidate is not None and not pd.isna(candidate):
                naming_seconds = float(candidate)

    usage_events = [row.to_dict() for _, row in usage_df.iterrows()]
    def is_naming_event(event: dict[str, Any]) -> bool:
        return (
            str(event.get("agent_name") or "") == "naming"
            or str(event.get("operation") or "") == "locked_object_naming_deferred"
        )

    detection_events = [event for event in usage_events if not is_naming_event(event)]
    detection_cost = _usage_cost_total(detection_events)
    naming_cost = _usage_cost_total([event for event in usage_events if is_naming_event(event)])
    naming_status = "pending"
    if not naming_rows.empty:
        naming_status = str(naming_rows.iloc[-1].get("status") or "failed")
    elif not bool(raw_usage.get("naming_deferred")):
        naming_status = "not_started"
    full_cost = None
    if naming_status == "succeeded" and detection_cost is not None:
        full_cost = round(detection_cost + (naming_cost or 0), 6)

    return {
        "ocr_seconds": float(raw_usage.get("ocr_seconds") or 0),
        "detection_seconds": float(raw_usage.get("detection_seconds") or 0),
        "naming_seconds": naming_seconds,
        "token_cost": detection_cost,
        "detection_cost": detection_cost,
        "full_cost": full_cost,
        "naming_status": naming_status,
        "total_seconds": float(total_seconds or 0),
    }


class FileReviewNameConflict(RuntimeError):
    """A stale File Review card attempted to replace a newer object name."""

    def __init__(self, current_name: str) -> None:
        self.current_name = current_name
        super().__init__("Object name changed while File Review was open.")


def _current_object_name(client: Any, *, run_id: str, object_id: str) -> str:
    """Read the authoritative name after a failed compare-and-set update."""
    for row in fetch_rfq_detected_object_names(client, run_id):
        if str(row.get("object_id") or "") == object_id:
            return str(row.get("object_name") or "")
    return ""


def _queue_object_name_write_audit(
    *,
    company_id: str,
    run_id: str,
    object_id: str,
    expected_name: str | None,
    requested_name: str,
    write_source: str,
) -> None:
    """Durably identify a post-Detection object-name writer without blocking it."""
    event = _runtime_event(
        agent_name="orchestration",
        operation="rfq_object_name_write",
        company_id=company_id,
        run_id=run_id,
        file_name="",
        model="deterministic",
        prompt_version="object_name_write_provenance_v1",
        started_at=datetime.now(UTC).isoformat(),
        finished_at=datetime.now(UTC).isoformat(),
        duration_seconds=0.0,
        raw_usage={
            "write_source": write_source,
            "expected_name": expected_name,
            "requested_name": requested_name,
        },
    )
    event["object_id"] = object_id
    event["object_name"] = requested_name
    _DIAGNOSTICS_EXECUTOR.submit(_persist_runtime_event, event)


def apply_file_review_edits(
    *,
    run_id: str,
    object_edits: dict[str, dict[str, Any]],
    company_id: str | None = None,
) -> set[str]:
    """Save File Review object edits and return object ids ignored for estimation."""
    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        if not company_id:
            raise PermissionError("Company ID is required for background RFQ edits.")
        assert_run_owned(client, run_id, company_id)
    ignored_object_ids: set[str] = set()

    for object_id, edit in object_edits.items():
        if edit.get("ignored"):
            ignored_object_ids.add(str(object_id))

        object_name = str(edit.get("name") or "").strip()
        quantity = _parse_quantity(edit.get("quantity"))

        # Name commits happen immediately in File Review. Continue is only a
        # guarded fallback: it may save a still-pending manual edit, but it
        # must never let a stale placeholder overwrite deferred Naming.
        if object_name and "expected_name" not in edit:
            raise RuntimeError("File Review name edit is missing its observed value.")
        if object_name and object_name != str(edit.get("expected_name") or "").strip():
            expected_name = str(edit.get("expected_name") or "").strip()
            if not update_rfq_detected_object_name_if_unchanged(
                client,
                run_id=run_id,
                object_id=str(object_id),
                expected_name=expected_name,
                object_name=object_name,
            ):
                raise FileReviewNameConflict(
                    _current_object_name(client, run_id=run_id, object_id=str(object_id)),
                )
            _queue_object_name_write_audit(
                company_id=str(company_id or get_company_id()),
                run_id=run_id,
                object_id=str(object_id),
                expected_name=expected_name,
                requested_name=object_name,
                write_source="file_review_continue",
            )

        values: dict[str, Any] = {}
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


_FILE_REVIEW_RUN_FIELDS = {
    "project_name": "project_name",
    "partner": "design_partner",
    "client": "client",
}


def save_file_review_run_metadata(
    *,
    run_id: str,
    values: dict[str, Any],
    company_id: str | None = None,
) -> dict[str, str]:
    """Persist editable File Review project metadata without creating catalogs."""
    normalized: dict[str, str] = {}
    update_values: dict[str, str] = {}
    for field, column in _FILE_REVIEW_RUN_FIELDS.items():
        if field not in values:
            continue
        value = str(values.get(field) or "").strip()
        if not value:
            raise ValueError(f"{field.replace('_', ' ').title()} cannot be empty.")
        if len(value) > 240:
            raise ValueError(f"{field.replace('_', ' ').title()} is too long.")
        normalized[field] = value
        update_values[column] = value

    if not update_values:
        raise ValueError("No editable File Review metadata was provided.")

    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        owner_company_id = company_id or get_company_id()
        if not owner_company_id:
            raise PermissionError("Company ID is required for RFQ metadata edits.")
        assert_run_owned(client, str(run_id), str(owner_company_id))

    update_rfq_run(client, run_id=str(run_id), values=update_values)
    return normalized


def save_file_review_object_name(
    *,
    run_id: str,
    object_id: str,
    object_name: str,
    expected_name: str | None = None,
) -> str:
    """Persist one File Review name without replacing a newer result.

    The optional legacy path is retained for non-File-Review callers created
    before compare-and-set support. Current File Review always supplies its
    observed value and therefore uses the guarded path below.
    """
    normalized_name = str(object_name or "").strip()
    if not normalized_name:
        raise ValueError("Object name cannot be empty.")

    client = get_supabase_client()
    from state.company_auth import company_auth_enabled
    if company_auth_enabled():
        assert_run_owned(client, str(run_id), get_company_id())
    if expected_name is None:
        update_rfq_detected_object(
            client,
            run_id=str(run_id),
            object_id=str(object_id),
            values={"object_name": normalized_name},
        )
        _queue_object_name_write_audit(
            company_id=get_company_id(),
            run_id=str(run_id),
            object_id=str(object_id),
            expected_name=None,
            requested_name=normalized_name,
            write_source="file_review_legacy_direct",
        )
        return normalized_name

    if not update_rfq_detected_object_name_if_unchanged(
        client,
        run_id=str(run_id),
        object_id=str(object_id),
        expected_name=str(expected_name or "").strip(),
        object_name=normalized_name,
    ):
        raise FileReviewNameConflict(
            _current_object_name(client, run_id=str(run_id), object_id=str(object_id)),
        )
    _queue_object_name_write_audit(
        company_id=get_company_id(),
        run_id=str(run_id),
        object_id=str(object_id),
        expected_name=str(expected_name or "").strip(),
        requested_name=normalized_name,
        write_source="file_review_inline",
    )
    return normalized_name


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
    }


def _normalize_object(item: dict[str, Any]) -> dict[str, Any]:
    """Convert one Supabase detected object row to the File Review card contract."""
    normalized = {
        "object_id": item.get("object_id"),
        "name": item.get("object_name"),
        "quantity": _clean_number(item.get("quantity")),
        "review_required": bool(item.get("review_required")),
    }
    preview_ref = _preview_ref(item)
    if preview_ref:
        normalized["preview_ref"] = preview_ref
    elif any(
        isinstance(ref, dict) and isinstance(ref.get("presentation_preview_bbox"), dict)
        for ref in item.get("evidence_page_refs") or []
    ):
        normalized["preview_pending"] = True
    return normalized


def _preview_ref(item: dict[str, Any]) -> str | None:
    for ref in item.get("evidence_page_refs") or []:
        if isinstance(ref, dict) and isinstance(ref.get("preview_ref"), str):
            return ref["preview_ref"]
    return None


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
