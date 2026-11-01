from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from agents.anthropic_adapter import (
    DetectionVisualRegistryValidationError,
    _source_dimensions_by_page,
    build_detection_page_evidence_inventory,
    build_detection_v5_membership_view_crops,
    build_detection_v5_review_coordinate_frames,
    build_detection_v5_review_page_context_images,
    run_anthropic_detection_v627_scope_scout,
    run_anthropic_detection_v5_source_degraded_pairwise_structural_admission_audit,
    run_anthropic_detection_visual_registry_agent,
)
from agents.detection_source_capability import assess_detection_source_capability
from agents.detection_document_classifier import (
    DEFAULT_CLAUDE_DETECTION_BOUNDARY_MODEL,
    DEFAULT_CLAUDE_DETECTION_MODEL,
    classify_detection_document,
)
from agents.detection_page_images import (
    DEFAULT_PAGE_IMAGE_DPI,
    build_detection_registry_regions,
    render_detection_pdf_pages,
)
from agents.prompt_loader import load_detection_visual_registry_prompt
from agents.schemas.detection_schema import validate_detection_result

# Preserve the established import surface while V6.12 replaces the old binary
# router with scenario categorization. The configured secret names remain V4.
DEFAULT_CLAUDE_DETECTION_V4_MODEL = DEFAULT_CLAUDE_DETECTION_MODEL
DEFAULT_CLAUDE_DETECTION_V4_BOUNDARY_MODEL = DEFAULT_CLAUDE_DETECTION_BOUNDARY_MODEL


_PRESENTATION_REPRESENTATION_PRIORITY = {
    "elevation": 0,
    "front_elevation": 0,
    "front": 0,
    "section": 1,
    "detail": 2,
}


def _ada_scope_scout_bypass_reason(route: dict) -> str | None:
    """Keep evidenced Ada boundary risks on Sonnet before scope reasoning.

    A page package with many native graphic anchors but little recoverable
    coordinate evidence can show several complete assemblies as a single
    orthographic drawing set.  A short document-scope answer is not enough to
    safely collapse that ambiguity to one Assembly Set.  This guard does not
    identify an object or assert that multiple objects exist.  It only retains
    the pre-existing Ada boundary contract.
    """
    signals = route.get("signals") if isinstance(route.get("signals"), dict) else {}
    if signals.get("v6_32_single_page_mistral_graphic_region_risk") is True:
        return "v6_32_single_page_mistral_graphics_preserve_ada"
    source_capability = (
        signals.get("source_capability")
        if isinstance(signals.get("source_capability"), dict)
        else {}
    )
    try:
        native_graphic_anchor_count = int(signals.get("native_graphic_anchor_count") or 0)
        source_fact_count = int(source_capability.get("source_fact_count") or 0)
    except (TypeError, ValueError):
        return None
    if (
        native_graphic_anchor_count >= 24
        and native_graphic_anchor_count > source_fact_count * 4
    ):
        return "v6_29_sparse_native_graphics_preserve_ada"
    return None


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


def _compile_confirmed_assembly_set_registry(
    registry: dict,
    *,
    visual_map: dict | None,
    document_scope: object,
    page_count: int,
) -> tuple[dict, dict]:
    """Publish one locked package for a confirmed document-scale assembly.

    Discovery still owns Island extraction and scope observation.  This
    compiler runs only after that observation has passed its strict validator,
    so common title-block metadata alone can never collapse a document.  The
    resulting commercial boundary is deliberately document-wide: all
    Registry-owned Islands stay attached to one object and every physical page
    remains available to Estimation for authored notes, materials and details.
    """
    audit = {
        "version": "detection_v6_26_assembly_set_compiler_v1",
        "applied": False,
        "reason": "document_scope_not_confirmed",
    }
    if not isinstance(document_scope, dict):
        return registry, audit
    if str(document_scope.get("decision") or "") != "assembly_set_candidate":
        return registry, audit

    original_objects = [
        item for item in registry.get("objects") or [] if isinstance(item, dict)
    ]
    ordered_group_ids: list[str] = []
    for item in original_objects:
        for group_id in item.get("visual_group_ids") or []:
            normalized = str(group_id or "")
            if normalized and normalized not in ordered_group_ids:
                ordered_group_ids.append(normalized)
    if not ordered_group_ids:
        audit["reason"] = "confirmed_scope_has_no_registry_owned_islands"
        return registry, audit

    owned_groups = _registry_owned_visual_groups(visual_map)
    root_group_ids = [
        str(group_id)
        for group_id in document_scope.get("root_group_ids") or []
        if str(group_id)
    ]
    if not root_group_ids or not set(root_group_ids).issubset(ordered_group_ids):
        audit["reason"] = "confirmed_scope_roots_are_not_registry_owned"
        return registry, audit
    root_pages = sorted({
        int(owned_groups[group_id]["page_number"])
        for group_id in root_group_ids
        if isinstance(owned_groups.get(group_id), dict)
        and isinstance(owned_groups[group_id].get("page_number"), int)
        and 1 <= int(owned_groups[group_id]["page_number"]) <= page_count
    })
    if not root_pages:
        audit["reason"] = "confirmed_scope_roots_have_no_page_evidence"
        return registry, audit

    evidence_pages = list(range(1, page_count + 1))
    compiled = {
        "objects": [{
            "object_id": "object-001",
            "transport_label": "Built-in joinery set",
            "quantity": 1,
            "quantity_explicit": False,
            "identity_pages": root_pages,
            "estimation_evidence_pages": evidence_pages,
            "visual_group_ids": ordered_group_ids,
            "visual_identity": (
                "One confirmed built-in joinery assembly set with overview "
                "and connected component evidence."
            ),
            "boundary_basis": (
                "V6.26 confirmed document scope: cited overview/root views "
                "and connected component witnesses. All Registry-owned "
                "Islands and uploaded sheets are retained for Estimation."
            ),
        }],
    }
    audit.update({
        "applied": True,
        "reason": "confirmed_scope_compiled_to_one_document_assembly",
        "original_object_ids": [
            str(item.get("object_id") or "") for item in original_objects
        ],
        "root_group_ids": root_group_ids,
        "identity_pages": root_pages,
        "retained_visual_group_ids": ordered_group_ids,
        "retained_evidence_pages": evidence_pages,
        "source_fact_policy": "all_source_facts_on_retained_uploaded_pages",
    })
    return compiled, audit


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


def _registry_owned_visual_groups(visual_map: dict | None) -> dict[str, dict]:
    """Index private post-Registry bbox evidence by immutable View ID."""
    return {
        str(group.get("group_id") or ""): group
        for group in (visual_map or {}).get("_registry_owned_evidence") or []
        if isinstance(group, dict) and str(group.get("group_id") or "")
    }


def _registry_group_bbox(group: dict | None) -> dict[str, float] | None:
    """Return one valid Registry-owned bbox in the Fusion coordinate frame."""
    if not isinstance(group, dict):
        return None
    bbox = group.get("bbox")
    try:
        normalized = {
            key: float(bbox[key])
            for key in (
                "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
            )
        }
    except (KeyError, TypeError, ValueError):
        return None
    if (
        normalized["bottom_right_x"] <= normalized["top_left_x"]
        or normalized["bottom_right_y"] <= normalized["top_left_y"]
    ):
        return None
    return normalized


def _select_presentation_view(
    item: dict,
    *,
    visual_groups_by_id: dict[str, dict],
    evidence_pages: set[int],
) -> dict | None:
    """Choose one Registry View for UI presentation without changing evidence.

    A front/elevation is the most useful isolated File Review preview.  The
    same source View can be supplied as a bounded Naming magnifier, but the
    UI-only ``presentation_preview_bbox`` itself is never passed as Naming
    evidence.
    """
    candidates: list[tuple[tuple[float | int | str, ...], dict]] = []
    for raw_group_id in item.get("visual_group_ids") or []:
        group = visual_groups_by_id.get(str(raw_group_id) or "")
        bbox = _registry_group_bbox(group)
        try:
            page_number = int(group.get("page_number")) if isinstance(group, dict) else 0
        except (TypeError, ValueError):
            page_number = 0
        if bbox is None or page_number not in evidence_pages:
            continue
        representation = str(group.get("representation_kind") or "").casefold()
        priority = _PRESENTATION_REPRESENTATION_PRIORITY.get(representation, 3)
        area = (
            (bbox["bottom_right_x"] - bbox["top_left_x"])
            * (bbox["bottom_right_y"] - bbox["top_left_y"])
        )
        candidates.append((
            (priority, -area, page_number, str(group.get("group_id") or "")),
            group,
        ))
    return min(candidates, key=lambda candidate: candidate[0])[1] if candidates else None


def _build_v621_naming_source_crops(
    *,
    registry: dict,
    visual_map: dict | None,
    ocr_package: dict | None,
    page_images: list[bytes],
) -> tuple[dict[str, dict], dict]:
    """Build one compact, source-derived magnifier for each locked object.

    Full annotated pages preserve document context.  A bounded crop of the
    selected Registry View restores local legibility for category Naming,
    without asking Naming to make a new grouping or boundary decision.
    """
    owned_groups = _registry_owned_visual_groups(visual_map)
    frames, frame_audit = build_detection_v5_review_coordinate_frames(
        ocr_package=ocr_package,
        page_images=page_images,
    )
    selected_by_object: dict[str, dict] = {}
    crop_groups: list[dict] = []
    for item in registry.get("objects") or []:
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("object_id") or "")
        evidence_pages = {
            int(page) for page in item.get("estimation_evidence_pages") or []
            if isinstance(page, int) and page > 0
        }
        selected = _select_presentation_view(
            item,
            visual_groups_by_id=owned_groups,
            evidence_pages=evidence_pages,
        )
        if not object_id or selected is None:
            continue
        selected_by_object[object_id] = selected
        crop_groups.append({**selected, "evidence_class": "object_evidence"})

    crops, crop_audit = build_detection_v5_membership_view_crops(
        page_images=page_images,
        visual_groups=crop_groups,
        coordinate_frames=frames,
        max_side=1024,
    )
    crops_by_group_id = {
        str(crop.get("group_id") or ""): crop
        for crop in crops
        if isinstance(crop, dict) and isinstance(crop.get("bytes"), bytes)
    }
    result: dict[str, dict] = {}
    for object_id, group in selected_by_object.items():
        crop = crops_by_group_id.get(str(group.get("group_id") or ""))
        if crop is None:
            continue
        result[object_id] = {
            "page_number": int(crop["page_number"]),
            "group_id": str(group.get("group_id") or ""),
            "representation_kind": str(group.get("representation_kind") or ""),
            "bytes": crop["bytes"],
        }
    return result, {
        "coordinate_frame_audit": frame_audit,
        "selected_group_ids": {
            object_id: str(group.get("group_id") or "")
            for object_id, group in selected_by_object.items()
        },
        "requested_crop_count": len(selected_by_object),
        "created_crop_count": len(result),
        "crop_audit": crop_audit,
        "crop_image_bytes": sum(len(crop["bytes"]) for crop in result.values()),
    }


def _build_v619_naming_annotated_pages(
    *,
    registry: dict,
    visual_map: dict | None,
    ocr_package: dict | None,
    page_images: list[bytes],
) -> tuple[dict[int, bytes], dict]:
    """Create one full source page per Registry-owned Island page for Naming.

    The object partition is already locked.  Naming needs the full drawing
    context to identify a category, while the overlay makes each locked View's
    owner explicit without offering it a new boundary decision.
    """
    owned_groups = _registry_owned_visual_groups(visual_map)
    frames, frame_audit = build_detection_v5_review_coordinate_frames(
        ocr_package=ocr_package,
        page_images=page_images,
    )
    palette = ("#D00000", "#0057B8", "#008A2E", "#9B1C9B", "#A15C00", "#006D77")
    labels_by_group_id: dict[str, str] = {}
    colours_by_group_id: dict[str, str] = {}
    for object_number, item in enumerate(registry.get("objects") or [], start=1):
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("object_id") or "")
        if not object_id:
            continue
        colour = palette[(object_number - 1) % len(palette)]
        for group_id in item.get("visual_group_ids") or []:
            group_key = str(group_id or "")
            if group_key not in owned_groups:
                continue
            labels_by_group_id[group_key] = object_id
            colours_by_group_id[group_key] = colour

    # Registry ownership is stronger than the earlier Discovery class. Hydrate
    # only those groups and mark them as object evidence for the shared overlay
    # renderer, which otherwise excludes non-object groups.
    contexts, overlay_audit = build_detection_v5_review_page_context_images(
        page_images=page_images,
        visual_groups=[
            {**group, "evidence_class": "object_evidence"}
            for group_id, group in owned_groups.items()
            if group_id in labels_by_group_id
        ],
        coordinate_frames=frames,
        # Naming needs the same complete 200-DPI source-page context as the
        # successful V6.14 path. Do not downscale title blocks or annotations.
        max_side=0,
        overlay_labels_by_group_id=labels_by_group_id,
        overlay_colours_by_group_id=colours_by_group_id,
    )
    pages = {
        int(context["page_number"]): context["bytes"]
        for context in contexts
        if isinstance(context, dict)
        and isinstance(context.get("page_number"), int)
        and isinstance(context.get("bytes"), bytes)
    }
    return pages, {
        "coordinate_frame_audit": frame_audit,
        "overlay_audit": overlay_audit,
        "registry_owned_group_count": len(owned_groups),
        "annotated_page_count": len(pages),
        "annotated_page_numbers": sorted(pages),
        "annotated_image_bytes": sum(len(image) for image in pages.values()),
        "overlay_object_count": len(set(labels_by_group_id.values())),
        "overlay_view_count": len(labels_by_group_id),
    }


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
    visual_map: dict | None = None,
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
    visual_groups_by_id = _registry_owned_visual_groups(visual_map)
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
        regions_by_page: dict[int, list[dict]] = {}
        for group_id in item.get("visual_group_ids") or []:
            group = visual_groups_by_id.get(str(group_id) or "")
            bbox = _registry_group_bbox(group)
            try:
                page_number = int(group.get("page_number")) if isinstance(group, dict) else 0
            except (TypeError, ValueError):
                continue
            if page_number in evidence_pages and bbox is not None:
                regions_by_page.setdefault(page_number, []).append(bbox)
        presentation_group = _select_presentation_view(
            item,
            visual_groups_by_id=visual_groups_by_id,
            evidence_pages=set(evidence_pages),
        )
        presentation_bbox = _registry_group_bbox(presentation_group)
        try:
            presentation_page = int(presentation_group.get("page_number")) if presentation_group else 0
        except (TypeError, ValueError):
            presentation_page = 0
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
                {
                    "page_number": page,
                    "source_label": f"P{page}",
                    "regions": regions_by_page.get(page, []),
                    **(
                        {"presentation_preview_bbox": presentation_bbox}
                        if page == presentation_page and presentation_bbox is not None
                        else {}
                    ),
                }
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
    """Persist the deterministic scenario category beside provider usage."""
    if not isinstance(event, dict):
        return event
    raw_usage = dict(event.get("raw_usage") or {})
    raw_usage["detection_v6_12_document_category"] = route
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
        DEFAULT_CLAUDE_DETECTION_MODEL,
    )
    boundary_model = get_secret(
        "CLAUDE_DETECTION_V4_BOUNDARY_MODEL",
        DEFAULT_CLAUDE_DETECTION_BOUNDARY_MODEL,
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
    route = classify_detection_document(
        ocr_package=ocr_package,
        source_capability=source_capability,
        base_model=str(base_model),
        boundary_model=str(boundary_model),
        explicit_model=model,
    )
    scope_scout_usage: dict | None = None
    ada_scope_scout_bypass = (
        route.get("category") == "ada_sparse_multi_object"
        and _ada_scope_scout_bypass_reason(route)
    )
    if ada_scope_scout_bypass:
        # V6.29 and V6.32 do not allow a structurally evidenced boundary risk
        # to be collapsed into one Assembly Set by the short scope observation.
        # Preserve the existing Ada contract without a call that cannot change
        # the route safely.
        route = {
            **route,
            "decision": (
                "ada_boundary_risk_single_page_mistral_graphics"
                if ada_scope_scout_bypass
                == "v6_32_single_page_mistral_graphics_preserve_ada"
                else "ada_boundary_risk_sparse_native_graphics"
            ),
            "reasons": [
                *route.get("reasons", []),
                ada_scope_scout_bypass,
            ],
            "signals": {
                **dict(route.get("signals") or {}),
                (
                    "v6_32_scope_scout"
                    if ada_scope_scout_bypass
                    == "v6_32_single_page_mistral_graphics_preserve_ada"
                    else "v6_29_scope_scout"
                ): {
                    "classification": (
                        "not_run_single_page_mistral_graphics"
                        if ada_scope_scout_bypass
                        == "v6_32_single_page_mistral_graphics_preserve_ada"
                        else "not_run_sparse_native_graphics"
                    ),
                },
            },
        }
    if route.get("category") == "ada_sparse_multi_object" and not ada_scope_scout_bypass:
        # V6.27 narrows the expensive Ada boundary route only after a separate,
        # conservative document-scope observation. The scout cannot create
        # Islands or commercial objects. A failed or uncertain scout preserves
        # the established Sonnet contract.
        if stage_callback:
            stage_callback("Document scope classification started")
        try:
            scope_scout, scope_scout_usage = run_anthropic_detection_v627_scope_scout(
                file_name=file_name,
                company_id=company_id,
                file_bytes=file_bytes,
                page_images=registry_images,
                ocr_package=ocr_package,
                model=str(route.get("evidence_model") or base_model),
            )
            scout_classification = str(scope_scout.get("classification") or "uncertain")
            route = {
                **route,
                "category": (
                    "assembly_set"
                    if scout_classification == "single_assembly_candidate"
                    else "ada_sparse_multi_object"
                ),
                "decision": (
                    "assembly_set_scope_scout"
                    if scout_classification == "single_assembly_candidate"
                    else "ada_boundary_risk_scope_scout"
                ),
                "reasons": [
                    *route.get("reasons", []),
                    f"v6_27_scope_scout:{scout_classification}",
                ],
                "registry_model": (
                    str(route.get("evidence_model") or base_model)
                    if scout_classification == "single_assembly_candidate"
                    else route.get("registry_model")
                ),
                "signals": {
                    **dict(route.get("signals") or {}),
                    "v6_27_scope_scout": scope_scout,
                },
            }
        except Exception as exc:
            scope_scout_usage = {
                "agent_name": "detection",
                "operation": "rfq_detection_v6_27_scope_scout",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "raw_usage": {
                    "cost_category": "detection",
                    "scope_scout": {
                        "version": "detection_v6_27_scope_scout",
                        "classification": "failed_preserve_ada_route",
                        "error_message": str(exc),
                    },
                },
            }
            route = {
                **route,
                "reasons": [
                    *route.get("reasons", []),
                    "v6_27_scope_scout_failed_preserve_ada_route",
                ],
            }
        if stage_callback:
            stage_callback("Document scope classification completed")
    if stage_callback:
        stage_callback("Detection Registry started")
    try:
        if source_capability["route_eligible"]:
            # The visual-only route is deliberately a separate contract. It is
            # reached only when every page lacks usable coordinate evidence, so
            # it cannot weaken ordinary V5's OCR/Fusion/Dimension path.
            if file_name.lower().endswith(".pdf"):
                registry_images, _ = render_detection_pdf_pages(
                    file_bytes, dpi=DEFAULT_PAGE_IMAGE_DPI,
                )
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
                run_anthropic_detection_v5_source_degraded_pairwise_structural_admission_audit(
                    file_name=file_name,
                    company_id=company_id,
                    file_bytes=file_bytes,
                    page_images=registry_images,
                    ocr_package=ocr_package,
                    model=source_degraded_route["registry_model"],
                )
            )
            registry = _visual_map["registry"]
            if _visual_map.get("route") in {
                "v5_35_native_graphic_anchor_pairwise_audit",
                "v5_36_native_graphic_embedding_pairwise_audit",
                "v5_37_native_graphic_embedding_witness_pairwise_audit",
            }:
                source_degraded_route = {
                    **source_degraded_route,
                    "decision": "native_graphic_anchored_embedding_visual_registry",
                    "reasons": [
                        *source_degraded_route["reasons"],
                        "native_pdf_graphic_xobject_anchor_map",
                        "native_xobject_embedding_witness_evidence",
                    ],
                }
            route = source_degraded_route
        else:
            # V6.5 supplies only complete rendered pages before Discovery.
            # A static page grid can divide one authored drawing before its
            # Island boundary is known. Review still receives its separately
            # generated post-Discovery View crops.
            regions = []
            _visual_map, registry, visual_registry_usage = run_anthropic_detection_visual_registry_agent(
                file_name=file_name, company_id=company_id, file_bytes=file_bytes,
                page_images=registry_images, regions=regions,
                ocr_package=ocr_package, model=route["registry_model"],
                # V6.12 is scenario-scoped. Only the documented Ada boundary
                # scenario can elevate real Mistral graphic blocks into initial
                # Island anchors; ordinary, assembly-set and source-degraded
                # scenarios retain their established contracts.
                mistral_anchor_admission=(route.get("category") == "ada_sparse_multi_object"),
                # V6.14 keeps the assembly scope observation out of every
                # ordinary route. The deterministic pre-model category has
                # already made that routing decision.
                document_category=str(route.get("category") or ""),
                stage_callback=stage_callback,
            )
    except DetectionVisualRegistryValidationError as exc:
        if stage_callback:
            stage_callback("Detection Registry failed")
        _attach_detection_model_route(exc.usage_event, route)
        raise
    if stage_callback:
        stage_callback("Detection Registry completed")
    visual_registry_usage = _attach_detection_model_route(visual_registry_usage, route)
    raw_registry_usage = (
        dict(visual_registry_usage.get("raw_usage") or {})
        if isinstance(visual_registry_usage, dict) else {}
    )
    document_scope = raw_registry_usage.get("v6_11_document_scope")
    assembly_set_audit: dict = {
        "version": "detection_v6_26_assembly_set_compiler_v1",
        "applied": False,
        "reason": "document_category_is_not_assembly_set",
    }
    if route.get("category") == "assembly_set":
        registry, assembly_set_audit = _compile_confirmed_assembly_set_registry(
            registry,
            visual_map=_visual_map,
            document_scope=document_scope,
            page_count=len(registry_images),
        )
    if isinstance(visual_registry_usage, dict):
        raw_registry_usage["v6_26_assembly_set_compiler"] = assembly_set_audit
        visual_registry_usage["raw_usage"] = raw_registry_usage
    quantity_review_required_object_ids = {
        str(item.get("object_id") or "")
        for item in (
            raw_registry_usage.get("explicit_quantity_audit", [])
            if isinstance(raw_registry_usage.get("explicit_quantity_audit"), list)
            else []
        )
        if isinstance(item, dict)
        and str(item.get("decision") or "")
        == "conflicting_caption_quantities_preserved_default"
        and str(item.get("object_id") or "")
    }
    registry = _enforce_shared_track_door_system_quantity(registry)
    _validate_registry_evidence_pages(registry, page_count=len(registry_images))
    result = _registry_to_detection_result(
        registry,
        company_id=company_id,
        file_name=file_name,
        page_count=len(registry_images),
        visual_map=_visual_map,
        # File Review uses review_required solely for a physical quantity that
        # needs a human decision. Registry metadata fallback and graph review
        # remain auditable in raw usage, but must not turn a proved quantity or
        # a safe default of one into a red QTY label.
        review_required_object_ids=quantity_review_required_object_ids,
    )
    result = _normalize_evidence_source_labels(result, ocr_package)
    validated = validate_detection_result(result)
    naming_annotated_pages, naming_overlay_audit = _build_v619_naming_annotated_pages(
        registry=registry,
        visual_map=_visual_map,
        ocr_package=ocr_package,
        page_images=registry_images,
    )
    naming_source_crops, naming_crop_audit = _build_v621_naming_source_crops(
        registry=registry,
        visual_map=_visual_map,
        ocr_package=ocr_package,
        page_images=registry_images,
    )
    if isinstance(visual_registry_usage, dict):
        raw_usage = dict(visual_registry_usage.get("raw_usage") or {})
        raw_usage["v6_19_naming_annotated_pages"] = naming_overlay_audit
        raw_usage["v6_21_naming_source_crops"] = naming_crop_audit
        visual_registry_usage["raw_usage"] = raw_usage
    if naming_annotated_pages:
        validated["_naming_annotated_pages"] = naming_annotated_pages
    if naming_source_crops:
        validated["_naming_source_crops"] = naming_source_crops
    validated["_agent_usage_events"] = [
        event for event in (scope_scout_usage, visual_registry_usage) if event
    ]
    return validated
