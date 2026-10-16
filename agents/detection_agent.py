from __future__ import annotations

from datetime import UTC, datetime
import re
import time

from agents.anthropic_adapter import (
    DETECTION_ASSEMBLY_ISLAND_REVIEW_PROMPT_VERSION,
    run_anthropic_detection_agent_with_fallback,
    run_anthropic_detection_assembly_island_review_agent,
    run_anthropic_detection_visual_registry_agent,
)
from agents.detection_page_images import build_detection_registry_regions, render_detection_pdf_pages
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_visual_registry_prompt,
)
from agents.schemas.detection_schema import validate_detection_result


def _enforce_shared_track_door_system_quantity(registry: dict) -> dict:
    """Resolve an internal registry contradiction for a shared-track door set.

    This is a domain invariant, not a Page 23 special case: leaves on one
    continuous track are construction components of one commercial door system.
    The registry has already identified that boundary in ``boundary_basis``;
    this guard prevents a conflicting leaf count from becoming the quote count.
    """
    shared_track_markers = (
        "continuous track", "shared track", "common track", "same track",
        "single track", "one track", "overhead track", "continuous guide",
        "shared guide", "common guide", "same guide", "single guide",
    )
    door_markers = ("door", "leaf", "leaves", "sliding")
    for item in registry.get("objects") or []:
        if not isinstance(item, dict):
            continue
        basis = " ".join(
            str(item.get(key) or "")
            for key in ("transport_label", "visual_identity", "boundary_basis")
        ).casefold()
        if (
            float(item.get("quantity") or 0) > 1
            and any(marker in basis for marker in shared_track_markers)
            and any(marker in basis for marker in door_markers)
        ):
            item["quantity"] = 1
            item["quantity_explicit"] = False
    return registry


def build_complete_assembly_island_review_signal(
    visual_map: dict,
    registry: dict,
    visual_registry_usage: dict,
) -> dict:
    """Find a same-page complete-assembly conflict worth independent review."""
    objects = registry.get("objects") if isinstance(registry, dict) else None
    audit = (visual_registry_usage.get("raw_usage") or {}).get("complete_assembly_island_audit")
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in (visual_map.get("visual_groups") or [])
        if isinstance(group, dict)
    }
    islands_by_page: dict[int, list[str]] = {}
    for island in audit if isinstance(audit, list) else []:
        if not isinstance(island, dict):
            continue
        group = groups_by_id.get(str(island.get("visual_group_id") or ""))
        page_number = group.get("page_number") if isinstance(group, dict) else None
        island_id = str(island.get("island_id") or "")
        if isinstance(page_number, int) and page_number > 0 and island_id:
            islands_by_page.setdefault(page_number, []).append(island_id)
    multi_island_pages = [
        {"page_number": page_number, "island_ids": island_ids}
        for page_number, island_ids in sorted(islands_by_page.items())
        if len(island_ids) >= 2
    ]
    triggered = bool(isinstance(objects, list) and len(objects) == 1 and multi_island_pages)
    return {
        "triggered": triggered,
        "reason": (
            "one_object_registry_with_multiple_complete_assembly_islands_on_one_page"
            if triggered
            else "no_same_page_complete_assembly_conflict"
        ),
        "multi_island_pages": multi_island_pages,
    }


def _mark_review_required(result: dict, object_ids: set[str]) -> dict:
    for item in result.get("detected_objects") or []:
        if isinstance(item, dict) and str(item.get("object_id") or "") in object_ids:
            item["review_required"] = True
    return result


def _assembly_island_review_failure_usage(
    *,
    company_id: str,
    file_name: str,
    started_at: str,
    duration_seconds: float,
    signal: dict,
    error: Exception,
) -> dict:
    return {
        "company_id": company_id,
        "run_id": None,
        "file_name": file_name,
        "object_id": None,
        "object_name": None,
        "agent_name": "detection",
        "operation": "rfq_detection_assembly_island_review",
        "model": "claude-sonnet-4-6",
        "prompt_version": DETECTION_ASSEMBLY_ISLAND_REVIEW_PROMPT_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "input_cost_usd": 0.0,
        "output_cost_usd": 0.0,
        "total_cost_usd": 0.0,
        "status": "failed",
        "duration_seconds": round(duration_seconds, 3),
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "raw_usage": {
            "assembly_island_review_trigger": signal,
            "error": str(error),
            "primary_registry_retained": True,
        },
    }


def _merge_registry_evidence(result: dict, registry: dict) -> dict:
    """Preserve the compact visual dossier while retaining Estimation evidence.

    The registry intentionally selects only a small set of pages for the
    second Detection pass.  Those pages are not the object evidence boundary:
    a kitchen's block and assembly sheets, for example, remain required by
    Estimation even when Detection did not need to inspect every sheet again.
    """
    registry_objects = {
        str(item["object_id"]): item
        for item in registry["objects"]
    }
    for detected in result.get("detected_objects") or []:
        if not isinstance(detected, dict):
            continue
        locked_object = registry_objects.get(str(detected.get("object_id")))
        if not isinstance(locked_object, dict):
            continue
        # The registry locks the commercial-object boundary and complete-unit
        # quantity before the richer dossier pass sees component dimensions.
        # Do not let a leaf, panel, view, or repeated detail replace that
        # locked quantity in the final commercial object.
        detected["quantity"] = locked_object["quantity"]
        detected["quantity_explicit"] = locked_object["quantity_explicit"]
        required_pages = set(locked_object["estimation_evidence_pages"])
        refs_by_page: dict[int, dict] = {}
        for raw_ref in detected.get("evidence_page_refs") or []:
            if not isinstance(raw_ref, dict):
                continue
            try:
                page_number = int(raw_ref.get("page_number"))
            except (TypeError, ValueError):
                continue
            if page_number in required_pages:
                refs_by_page[page_number] = dict(raw_ref)
        for page_number in sorted(required_pages):
            ref = refs_by_page.get(page_number)
            if ref is None:
                refs_by_page[page_number] = {
                    "page_number": page_number,
                    "source_label": str(page_number),
                    "regions": [],
                }
                continue
            ref.pop("roles", None)
            ref.setdefault("regions", [])
            refs_by_page[page_number] = ref
        refs = [refs_by_page[page_number] for page_number in sorted(refs_by_page)]
        detected["evidence_page_refs"] = refs
        detected["evidence_pages"] = ",".join(
            str(ref["page_number"]) for ref in refs
        )
    return result


def _validate_registry_evidence_pages(registry: dict, *, page_count: int) -> None:
    """Prevent a registry page reference from inventing a page outside the upload."""
    for item in registry.get("objects") or []:
        for field in ("identity_pages", "estimation_evidence_pages"):
            invalid = [
                page for page in item.get(field) or []
                if not isinstance(page, int) or not 1 <= page <= page_count
            ]
            if invalid:
                raise ValueError(
                    f"Detection registry {field} references pages outside the upload: {invalid}"
                )


def _literal_page_texts(ocr_package: dict | None) -> dict[int, str]:
    """Index OCR text by physical page without adding model interpretation."""
    evidence = (ocr_package or {}).get("evidence")
    if not isinstance(evidence, dict):
        return {}
    texts: dict[int, list[str]] = {}
    for kind in ("text_blocks", "literal_items"):
        for item in evidence.get(kind) or []:
            if not isinstance(item, dict):
                continue
            try:
                page_number = int(item.get("page_number"))
            except (TypeError, ValueError):
                continue
            text = str(item.get("text") or "").strip()
            if page_number > 0 and text:
                texts.setdefault(page_number, []).append(text)
    return {page_number: "\n".join(values) for page_number, values in texts.items()}


def _normalized_text(value: object) -> str:
    return " ".join(re.findall(r"[^\W_]+", str(value or "").casefold(), re.UNICODE))


def _normalize_evidence_source_labels(result: dict, ocr_package: dict | None) -> dict:
    """Keep source labels only when literal OCR on that page supports them.

    A Detection-generated visual description is useful while selecting a
    region, but it is not source evidence. Passing it to Naming or Estimation
    would silently reintroduce Detection's semantic conclusion into later
    stages. Unsupported labels become an unambiguous physical-page reference.
    """
    page_texts = {
        page_number: _normalized_text(text)
        for page_number, text in _literal_page_texts(ocr_package).items()
    }
    for detected_object in result.get("detected_objects") or []:
        if not isinstance(detected_object, dict):
            continue
        for page_ref in detected_object.get("evidence_page_refs") or []:
            if not isinstance(page_ref, dict):
                continue
            try:
                page_number = int(page_ref.get("page_number"))
            except (TypeError, ValueError):
                continue
            label = _normalized_text(page_ref.get("source_label"))
            if not label or label not in page_texts.get(page_number, ""):
                page_ref["source_label"] = f"P{page_number}"
    return result


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def run_detection_agent(
    file_name: str,
    company_id: str = "001",
    file_bytes: bytes | None = None,
    ocr_package: dict | None = None,
    page_images: list[bytes] | None = None,
    page_image_diagnostics: dict | None = None,
    model: str | None = None,
) -> dict:
    """
    Detection Agent entrypoint.

    Runs the real Claude-backed Detection Agent.
    """

    # Fail loudly if the prompt file is missing or empty.
    _prompt = load_detection_agent_prompt()
    _visual_registry_prompt = load_detection_visual_registry_prompt()

    if file_bytes is None:
        raise ValueError("Detection Agent requires uploaded file bytes.")

    registry_images = page_images
    if registry_images is None and file_name.lower().endswith(".pdf"):
        registry_images, _ = render_detection_pdf_pages(file_bytes)
    elif registry_images is None:
        registry_images = [file_bytes]
    if not registry_images:
        raise ValueError("Detection registry requires rendered PDF pages.")
    regions = build_detection_registry_regions(registry_images)
    visual_map, registry, visual_registry_usage = run_anthropic_detection_visual_registry_agent(
        file_name=file_name, company_id=company_id, file_bytes=file_bytes,
        page_images=registry_images, regions=regions,
        ocr_package=ocr_package, model=model,
    )
    registry_usage_events = [visual_registry_usage]
    forced_review_object_ids: set[str] = set()
    review_signal = build_complete_assembly_island_review_signal(
        visual_map, registry, visual_registry_usage,
    )
    if review_signal["triggered"]:
        review_started_at = datetime.now(UTC).isoformat()
        review_started = time.perf_counter()
        try:
            registry, review_usage = run_anthropic_detection_assembly_island_review_agent(
                file_name=file_name,
                company_id=company_id,
                file_bytes=file_bytes,
                page_images=registry_images,
                regions=regions,
                visual_map=visual_map,
                complete_assembly_island_audit=(
                    (visual_registry_usage.get("raw_usage") or {}).get("complete_assembly_island_audit")
                    or []
                ),
                ocr_package=ocr_package,
            )
            registry_usage_events.append(review_usage)
        except RuntimeError as exc:
            forced_review_object_ids = {
                str(item.get("object_id") or "")
                for item in registry.get("objects") or []
                if isinstance(item, dict) and str(item.get("object_id") or "")
            }
            registry_usage_events.append(_assembly_island_review_failure_usage(
                company_id=company_id,
                file_name=file_name,
                started_at=review_started_at,
                duration_seconds=time.perf_counter() - review_started,
                signal=review_signal,
                error=exc,
            ))
    registry = _enforce_shared_track_door_system_quantity(registry)
    _validate_registry_evidence_pages(registry, page_count=len(registry_images))
    evidence_page_numbers = sorted({page for item in registry["objects"] for page in item["estimation_evidence_pages"]})
    evidence_images = [registry_images[page - 1] for page in evidence_page_numbers]
    evidence_regions = [region for region in regions if region["page_number"] in evidence_page_numbers]
    result = run_anthropic_detection_agent_with_fallback(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
        ocr_package=ocr_package,
        page_images=evidence_images,
        page_image_diagnostics=page_image_diagnostics,
        primary_model_override=model,
        locked_registry=registry,
        allow_sonnet_fallback=False,
        focus_regions=evidence_regions,
        page_image_numbers=evidence_page_numbers,
    )

    usage_event = result.pop("_agent_usage", None)
    result = _merge_registry_evidence(result, registry)
    result = _normalize_evidence_source_labels(result, ocr_package)
    result = _mark_review_required(result, forced_review_object_ids)
    validated = validate_detection_result(result)
    validated["_agent_usage_events"] = [event for event in (*registry_usage_events, usage_event) if event]
    return validated
