from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from agents.anthropic_adapter import (
    DetectionVisualRegistryValidationError,
    _source_dimensions_by_page,
    build_detection_page_evidence_inventory,
    run_anthropic_detection_v5_source_degraded_full_page_registry_experiment,
    run_anthropic_detection_visual_registry_agent,
)
from agents.detection_source_capability import assess_detection_source_capability
from agents.detection_model_router import (
    DEFAULT_CLAUDE_DETECTION_V4_BOUNDARY_MODEL,
    DEFAULT_CLAUDE_DETECTION_V4_MODEL,
    detection_v42_model_route,
)
from agents.detection_page_images import build_detection_registry_regions, render_detection_pdf_pages
from agents.prompt_loader import load_detection_visual_registry_prompt
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


def _merge_registry_evidence(
    result: dict,
    registry: dict,
    *,
    review_required_object_ids: set[str] | None = None,
) -> dict:
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
    fallback_ids = set(review_required_object_ids or ())
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
        if str(detected.get("object_id") or "") in fallback_ids:
            # A proof-graph package exists, but its descriptive Registry row
            # was unavailable.  Preserve the safe default quantity and make
            # the uncertainty visible in File Review instead of failing the
            # entire RFQ cycle.
            detected["review_required"] = True
        # The Evidence pass may describe the object visually, but it has no
        # authority to replace the Registry's source-label transport. Naming
        # uses this field to retain an architect's exact identifier.
        transport_label = str(locked_object.get("transport_label") or "").strip()
        if transport_label:
            detected["object_name"] = transport_label
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


def _registry_to_detection_result(
    registry: dict,
    *,
    company_id: str,
    file_name: str,
    page_count: int,
    review_required_object_ids: set[str] | None = None,
) -> dict:
    """Materialize the Registry's locked packages as the V4 result.

    V4 ends after package construction.  It must not send a second model a
    narrowed dossier merely to restate object IDs, quantities and pages.  The
    Registry is already the authority for those fields, so this adapter only
    supplies the persistent File Review transport shape.
    """
    created_at = datetime.now(UTC).isoformat()
    run_id = f"run_{uuid4().hex}"
    flagged_ids = set(review_required_object_ids or ())
    objects = []
    for item in registry.get("objects") or []:
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("object_id") or "")
        evidence_pages = sorted({
            int(page)
            for page in item.get("estimation_evidence_pages") or []
            if isinstance(page, int) and 1 <= page <= page_count
        })
        if not object_id or not evidence_pages:
            continue
        objects.append({
            "run_id": run_id,
            "company_id": company_id,
            "object_id": object_id,
            "object_name": str(item.get("transport_label") or "Unlabelled"),
            "quantity": item.get("quantity"),
            "quantity_explicit": item.get("quantity_explicit"),
            "review_required": object_id in flagged_ids,
            "evidence_pages": ",".join(str(page) for page in evidence_pages),
            "evidence_page_refs": [
                {"page_number": page, "source_label": f"P{page}", "regions": []}
                for page in evidence_pages
            ],
            "approved": False,
            "created_at": created_at,
        })
    return {
        "rfq_run": {
            "run_id": run_id,
            "company_id": company_id,
            "project_name": "unknown",
            "file_name": file_name,
            "source_type": "pdf" if file_name.lower().endswith(".pdf") else "image",
            "design_partner": "unknown",
            "client": "unknown",
            "author": "unknown",
            "document_date": "unknown",
            "pages_detected": page_count,
            "language": "unknown",
            "file_quality_level": 2,
            "file_quality_label": "partial_information",
            "file_quality_confidence": 0.0,
            "file_quality_notes": "Registry-only V4 package construction",
            "status": "intake_parsed",
            "created_at": created_at,
        },
        "detected_objects": objects,
    }


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def _attach_detection_model_route(event: object, route: dict) -> object:
    """Persist the deterministic routing basis beside the provider usage."""
    if not isinstance(event, dict):
        return event
    raw_usage = dict(event.get("raw_usage") or {})
    raw_usage["detection_v4_2_model_route"] = route
    event["raw_usage"] = raw_usage
    return event


def _record_locked_evidence_handoff_audit(
    event: object,
    *,
    registry: dict,
    result: dict,
    fallback_review_required_object_ids: set[str] | None = None,
) -> object:
    """Persist the final invariant check after Evidence packaging.

    Registry owns commercial-object boundaries.  The post-Registry model may
    enrich evidence regions, but it must not become a second owner of identity
    or quantity.  This is a deterministic audit record, not model reasoning.
    """
    if not isinstance(event, dict):
        return event
    registry_objects = [
        item for item in registry.get("objects") or [] if isinstance(item, dict)
    ]
    detected_objects = [
        item for item in result.get("detected_objects") or [] if isinstance(item, dict)
    ]
    expected_ids = [str(item.get("object_id") or "") for item in registry_objects]
    actual_ids = [str(item.get("object_id") or "") for item in detected_objects]
    expected_quantities = {
        str(item.get("object_id") or ""): item.get("quantity")
        for item in registry_objects
    }
    actual_quantities = {
        str(item.get("object_id") or ""): item.get("quantity")
        for item in detected_objects
    }
    expected_pages = {
        str(item.get("object_id") or ""): list(item.get("estimation_evidence_pages") or [])
        for item in registry_objects
    }
    actual_pages = {
        str(item.get("object_id") or ""): [
            int(ref["page_number"])
            for ref in item.get("evidence_page_refs") or []
            if isinstance(ref, dict) and isinstance(ref.get("page_number"), int)
        ]
        for item in detected_objects
    }
    raw_usage = dict(event.get("raw_usage") or {})
    raw_usage["locked_evidence_handoff_audit"] = {
        "registry_object_ids": expected_ids,
        "result_object_ids": actual_ids,
        "object_sequence_preserved": actual_ids == expected_ids,
        "registry_quantities": expected_quantities,
        "result_quantities": actual_quantities,
        "quantity_preserved": actual_quantities == expected_quantities,
        "registry_evidence_pages": expected_pages,
        "result_evidence_pages": actual_pages,
        "evidence_page_contract_preserved": actual_pages == expected_pages,
        "fallback_review_required_object_ids": sorted(
            fallback_review_required_object_ids or ()
        ),
    }
    event["raw_usage"] = raw_usage
    return event


def run_detection_agent(
    file_name: str,
    company_id: str = "001",
    file_bytes: bytes | None = None,
    ocr_package: dict | None = None,
    page_images: list[bytes] | None = None,
    page_image_diagnostics: dict | None = None,
    model: str | None = None,
    stage_callback: Callable[[str], None] | None = None,
) -> dict:
    """
    Detection Agent entrypoint.

    Runs the real Claude-backed Detection Agent.
    """

    # Fail loudly if the active Registry prompt is missing or empty.
    _visual_registry_prompt = load_detection_visual_registry_prompt()

    if file_bytes is None:
        raise ValueError("Detection Agent requires uploaded file bytes.")

    base_model = get_secret(
        "CLAUDE_DETECTION_V4_MODEL",
        DEFAULT_CLAUDE_DETECTION_V4_MODEL,
    )
    boundary_model = get_secret(
        "CLAUDE_DETECTION_V4_BOUNDARY_MODEL",
        DEFAULT_CLAUDE_DETECTION_V4_BOUNDARY_MODEL,
    )
    route = detection_v42_model_route(
        ocr_package=ocr_package,
        base_model=str(base_model),
        boundary_model=str(boundary_model),
        explicit_model=model,
    )

    registry_images = page_images
    if registry_images is None and file_name.lower().endswith(".pdf"):
        registry_images, _ = render_detection_pdf_pages(file_bytes)
    elif registry_images is None:
        registry_images = [file_bytes]
    if not registry_images:
        raise ValueError("Detection registry requires rendered PDF pages.")
    source_capability = assess_detection_source_capability(
        source_facts=build_detection_page_evidence_inventory(ocr_package),
        page_count=len(registry_images),
        page_dimensions=_source_dimensions_by_page(ocr_package),
    )
    if stage_callback:
        stage_callback("Detection Registry started")
    try:
        if source_capability["route_eligible"]:
            # The visual-only route is deliberately a separate contract. It is
            # reached only when every page lacks usable coordinate evidence, so
            # it cannot weaken ordinary V5's OCR/Fusion/Dimension path.
            if file_name.lower().endswith(".pdf"):
                registry_images, _ = render_detection_pdf_pages(file_bytes, dpi=200)
            source_degraded_route = {
                **route,
                "decision": "source_degraded_visual_registry",
                "reasons": [
                    *route.get("reasons", []),
                    "all_pages_lack_usable_coordinate_evidence",
                    "source_degraded_route_forces_base_model",
                ],
                "registry_model": str(base_model),
                "source_capability": source_capability,
            }
            _visual_map, visual_registry_usage = (
                run_anthropic_detection_v5_source_degraded_full_page_registry_experiment(
                    file_name=file_name,
                    company_id=company_id,
                    file_bytes=file_bytes,
                    page_images=registry_images,
                    ocr_package=ocr_package,
                    model=source_degraded_route["registry_model"],
                    post_discovery_view_crops=True,
                )
            )
            registry = _visual_map["registry"]
            route = source_degraded_route
        else:
            regions = build_detection_registry_regions(registry_images)
            _visual_map, registry, visual_registry_usage = run_anthropic_detection_visual_registry_agent(
                file_name=file_name, company_id=company_id, file_bytes=file_bytes,
                page_images=registry_images, regions=regions,
                ocr_package=ocr_package, model=route["registry_model"],
            )
    except DetectionVisualRegistryValidationError as exc:
        if stage_callback:
            stage_callback("Detection Registry failed")
        _attach_detection_model_route(exc.usage_event, route)
        raise
    if stage_callback:
        stage_callback("Detection Registry completed")
    visual_registry_usage = _attach_detection_model_route(visual_registry_usage, route)
    fallback_review_required_object_ids = {
        str(object_id)
        for object_id in (
            (visual_registry_usage.get("raw_usage") or {}).get(
                "registry_metadata_fallback_object_ids", []
            )
            if isinstance(visual_registry_usage, dict)
            else []
        )
        if str(object_id)
    }
    graph_review_required_object_ids = {
        str(object_id)
        for object_id in (
            (visual_registry_usage.get("raw_usage") or {}).get(
                "registry_graph_review_required_object_ids", []
            )
            if isinstance(visual_registry_usage, dict)
            else []
        )
        if str(object_id)
    }
    registry = _enforce_shared_track_door_system_quantity(registry)
    _validate_registry_evidence_pages(registry, page_count=len(registry_images))
    result = _registry_to_detection_result(
        registry,
        company_id=company_id,
        file_name=file_name,
        page_count=len(registry_images),
        review_required_object_ids=(
            fallback_review_required_object_ids | graph_review_required_object_ids
        ),
    )
    result = _normalize_evidence_source_labels(result, ocr_package)
    validated = validate_detection_result(result)
    validated["_agent_usage_events"] = [visual_registry_usage] if visual_registry_usage else []
    return validated
