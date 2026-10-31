"""Bounded, image-first resolution for post-Discovery source conflicts.

This module deliberately knows nothing about OCR wording, Candidate Region
roles, or the first model's rejection reason.  Those signals select a target
outside this module; the resolver receives a neutral crop and may only add a
visually observed Island or confirm document context.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DOCUMENT_CONTEXT_KINDS = {
    "title_block",
    "schedule",
    "legend",
    "navigation",
    "generic_plan",
    "other_document_context",
}
RESOLUTION_DISPOSITIONS = {
    "admit_object_evidence",
    "document_context",
    "unresolved",
}


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    try:
        result = {key: int(value[key]) for key in keys}
    except (KeyError, TypeError, ValueError):
        return None
    if (
        result["bottom_right_x"] <= result["top_left_x"]
        or result["bottom_right_y"] <= result["top_left_y"]
    ):
        return None
    return result


def _overlaps(left: dict[str, int], right: dict[str, int]) -> bool:
    return not (
        left["bottom_right_x"] <= right["top_left_x"]
        or left["top_left_x"] >= right["bottom_right_x"]
        or left["bottom_right_y"] <= right["top_left_y"]
        or left["top_left_y"] >= right["bottom_right_y"]
    )


def _iou(left: dict[str, int], right: dict[str, int]) -> float:
    intersection_width = max(
        0,
        min(left["bottom_right_x"], right["bottom_right_x"])
        - max(left["top_left_x"], right["top_left_x"]),
    )
    intersection_height = max(
        0,
        min(left["bottom_right_y"], right["bottom_right_y"])
        - max(left["top_left_y"], right["top_left_y"]),
    )
    intersection = intersection_width * intersection_height
    if not intersection:
        return 0.0
    left_area = (
        (left["bottom_right_x"] - left["top_left_x"])
        * (left["bottom_right_y"] - left["top_left_y"])
    )
    right_area = (
        (right["bottom_right_x"] - right["top_left_x"])
        * (right["bottom_right_y"] - right["top_left_y"])
    )
    return intersection / (left_area + right_area - intersection)


def _contains(outer: dict[str, int], inner: dict[str, int]) -> bool:
    return (
        outer["top_left_x"] <= inner["top_left_x"]
        and outer["top_left_y"] <= inner["top_left_y"]
        and outer["bottom_right_x"] >= inner["bottom_right_x"]
        and outer["bottom_right_y"] >= inner["bottom_right_y"]
    )


def translate_detection_conflict_crop_decisions(
    *,
    decisions: object,
    crop_frames: dict[str, dict[str, Any]],
    page_frames: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map provider-local crop geometry into the ordinary Fusion page frame.

    The independent visual resolver is never told where a crop lies on the
    page. It returns coordinates in its own displayed-pixel frame; this
    deterministic adapter is the only code that knows the crop placement.
    """
    if not isinstance(decisions, list):
        raise ValueError("V7.5 conflict decisions must be a list")
    translated: list[dict[str, Any]] = []
    for raw_decision in decisions:
        if not isinstance(raw_decision, dict):
            translated.append(raw_decision)
            continue
        decision = deepcopy(raw_decision)
        if decision.get("disposition") != "admit_object_evidence":
            translated.append(decision)
            continue
        target_id = str(decision.get("target_id") or "")
        crop_frame = crop_frames.get(target_id)
        if not isinstance(crop_frame, dict):
            raise ValueError("V7.5 admitted decision has no crop frame")
        crop_bbox = _bbox(crop_frame.get("review_crop_bbox"))
        dimensions = crop_frame.get("crop_dimensions")
        try:
            crop_width = int(dimensions["width"])
            crop_height = int(dimensions["height"])
            page_number = int(crop_frame["page_number"])
            scale_x = float(page_frames[page_number]["scale_x"])
            scale_y = float(page_frames[page_number]["scale_y"])
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            raise ValueError("V7.5 admitted decision has an invalid crop frame") from None
        if crop_bbox is None or crop_width <= 0 or crop_height <= 0 or scale_x <= 0 or scale_y <= 0:
            raise ValueError("V7.5 admitted decision has an invalid crop frame")

        def translate_box(value: object) -> dict[str, int] | None:
            local = _bbox(value)
            if (
                local is None
                or local["top_left_x"] < 0 or local["top_left_y"] < 0
                or local["bottom_right_x"] > crop_width
                or local["bottom_right_y"] > crop_height
            ):
                return None
            review_width = crop_bbox["bottom_right_x"] - crop_bbox["top_left_x"]
            review_height = crop_bbox["bottom_right_y"] - crop_bbox["top_left_y"]
            return {
                "top_left_x": round((crop_bbox["top_left_x"] + local["top_left_x"] / crop_width * review_width) / scale_x),
                "top_left_y": round((crop_bbox["top_left_y"] + local["top_left_y"] / crop_height * review_height) / scale_y),
                "bottom_right_x": round((crop_bbox["top_left_x"] + local["bottom_right_x"] / crop_width * review_width) / scale_x),
                "bottom_right_y": round((crop_bbox["top_left_y"] + local["bottom_right_y"] / crop_height * review_height) / scale_y),
            }

        decision["bbox"] = translate_box(decision.get("bbox"))
        decision["core_bbox"] = translate_box(decision.get("core_bbox"))
        translated.append(decision)
    return translated


def build_detection_conflict_targets(
    *,
    candidate_regions: list[dict[str, Any]],
    visual_groups: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
    closed_document_context_boxes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return only source regions whose visual disposition conflicts.

    The returned records are private routing metadata.  They must never be
    passed verbatim to the vision resolver: in particular, ``trigger`` and
    ``candidate_region_id`` would bias the independent visual decision.
    """
    classification_by_group_id = {
        str(row.get("group_id") or ""): str(row.get("evidence_class") or "")
        for row in classifications if isinstance(row, dict)
    }
    object_boxes: list[tuple[int, dict[str, int]]] = []
    closed_context_boxes: list[tuple[int, dict[str, int]]] = []
    for item in closed_document_context_boxes or []:
        if not isinstance(item, dict):
            continue
        try:
            page_number = int(item.get("page_number"))
        except (TypeError, ValueError):
            continue
        if (bbox := _bbox(item.get("bbox"))) is not None:
            closed_context_boxes.append((page_number, bbox))
    for group in visual_groups:
        if not isinstance(group, dict):
            continue
        try:
            page_number = int(group.get("page_number"))
        except (TypeError, ValueError):
            continue
        if classification_by_group_id.get(str(group.get("group_id") or "")) != "object_evidence":
            continue
        if (bbox := _bbox(group.get("bbox"))) is not None:
            object_boxes.append((page_number, bbox))

    targets: list[dict[str, Any]] = []
    for candidate in candidate_regions:
        if not isinstance(candidate, dict):
            continue
        try:
            page_number = int(candidate.get("page_number"))
        except (TypeError, ValueError):
            continue
        bbox = _bbox(candidate.get("bbox"))
        candidate_id = str(candidate.get("candidate_region_id") or "")
        if not candidate_id or bbox is None:
            continue
        # Discovery has already closed this same visual region as document
        # context. Do not reopen it merely because Candidate Regions is an
        # independent recall source. The high IoU requirement keeps distinct
        # object islands inside a plan eligible for review.
        if any(
            context_page == page_number and _iou(bbox, context_bbox) >= 0.8
            for context_page, context_bbox in closed_context_boxes
        ):
            continue
        has_object_evidence = any(
            object_page == page_number and _overlaps(bbox, object_bbox)
            for object_page, object_bbox in object_boxes
        )
        if has_object_evidence:
            continue
        if candidate.get("role") == "coverage_only":
            trigger = "coverage_only_without_object_evidence"
        elif candidate.get("basis") == "mistral_graphic_region":
            trigger = "graphic_region_without_object_evidence"
        else:
            continue
        targets.append({
            "target_id": "",
            "page_number": page_number,
            "bbox": bbox,
            "trigger": trigger,
            "candidate_region_ids": [candidate_id],
        })

    # Candidate suppliers sometimes emit duplicate boxes. One neutral crop is
    # enough, and avoids treating duplicated source geometry as two objects.
    deduplicated: list[dict[str, Any]] = []
    for target in sorted(
        targets,
        key=lambda item: (
            item["page_number"], item["bbox"]["top_left_y"],
            item["bbox"]["top_left_x"], item["candidate_region_ids"],
        ),
    ):
        match = next((
            existing for existing in deduplicated
            if existing["page_number"] == target["page_number"]
            and existing["bbox"] == target["bbox"]
        ), None)
        if match is not None:
            match["candidate_region_ids"].extend(target["candidate_region_ids"])
            match["trigger"] = "multiple_source_conflicts"
            continue
        deduplicated.append(deepcopy(target))
    for ordinal, target in enumerate(deduplicated, start=1):
        target["target_id"] = f"V75-C{ordinal:03d}"
        target["candidate_region_ids"] = sorted(set(target["candidate_region_ids"]))
    return deduplicated


def validate_detection_conflict_decisions(
    *,
    decisions: object,
    targets: list[dict[str, Any]],
    page_frames: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate a complete neutral visual verdict for every conflict target."""
    if not isinstance(decisions, list):
        raise ValueError("V7.5 conflict decisions must be a list")
    targets_by_id = {str(target["target_id"]): target for target in targets}
    by_target: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError("V7.5 conflict decision must be an object")
        target_id = str(decision.get("target_id") or "")
        disposition = str(decision.get("disposition") or "")
        witness = str(decision.get("visual_witness") or "").strip()
        if (
            target_id not in targets_by_id
            or target_id in by_target
            or disposition not in RESOLUTION_DISPOSITIONS
            or not witness
            or len(witness) > 180
        ):
            raise ValueError("V7.5 conflict decision is invalid")
        normalized = {
            "target_id": target_id,
            "disposition": disposition,
            "visual_witness": witness,
        }
        if disposition == "admit_object_evidence":
            bbox = _bbox(decision.get("bbox"))
            core_bbox = _bbox(decision.get("core_bbox"))
            representation_kind = str(decision.get("representation_kind") or "").strip()
            target = targets_by_id[target_id]
            frame = page_frames.get(int(target["page_number"])) or {}
            dimensions = frame.get("fusion_dimensions") if isinstance(frame, dict) else None
            try:
                width = int(dimensions["width"])
                height = int(dimensions["height"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("V7.5 conflict decision has no page frame") from None
            if (
                bbox is None or core_bbox is None or not representation_kind
                or len(representation_kind) > 64
                or not _contains(bbox, core_bbox)
                or not _overlaps(bbox, target["bbox"])
                or bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0
                or bbox["bottom_right_x"] > width or bbox["bottom_right_y"] > height
            ):
                raise ValueError("V7.5 admitted Island geometry is invalid")
            normalized.update({
                "bbox": bbox,
                "core_bbox": core_bbox,
                "representation_kind": representation_kind,
            })
        elif disposition == "document_context":
            context_kind = str(decision.get("document_context_kind") or "")
            if context_kind not in DOCUMENT_CONTEXT_KINDS:
                raise ValueError("V7.5 document-context decision is invalid")
            normalized["document_context_kind"] = context_kind
        by_target[target_id] = normalized
    if set(by_target) != set(targets_by_id):
        raise ValueError("V7.5 conflict decisions must cover every target exactly once")
    return [by_target[str(target["target_id"])] for target in targets]


def apply_detection_conflict_admissions(
    *,
    payload: dict[str, Any],
    targets: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Append only visually admitted Islands to the ordinary Discovery ledger."""
    result = deepcopy(payload)
    visual_groups = result.get("visual_groups")
    classifications = result.get("classifications")
    if not isinstance(visual_groups, list) or not isinstance(classifications, list):
        raise ValueError("V7.5 requires an ordinary Discovery payload")
    target_by_id = {str(target["target_id"]): target for target in targets}
    audit: list[dict[str, Any]] = []
    existing_group_ids = {
        str(group.get("group_id") or "")
        for group in visual_groups if isinstance(group, dict)
    }
    for ordinal, decision in enumerate(decisions, start=1):
        target = target_by_id[str(decision["target_id"])]
        audit_row = {
            "target_id": decision["target_id"],
            "page_number": target["page_number"],
            "candidate_region_ids": list(target["candidate_region_ids"]),
            "trigger": target["trigger"],
            **deepcopy(decision),
        }
        if decision["disposition"] == "admit_object_evidence":
            group_id = f"v75-conflict-{ordinal:03d}"
            if group_id in existing_group_ids:
                raise ValueError("V7.5 generated a duplicate Island ID")
            existing_group_ids.add(group_id)
            visual_groups.append({
                "group_id": group_id,
                "page_number": int(target["page_number"]),
                "location_hint": "independent visual conflict adjudication",
                "visual_description": decision["visual_witness"],
                "representation_kind": decision["representation_kind"],
                "bbox": deepcopy(decision["bbox"]),
                "core_bbox": deepcopy(decision["core_bbox"]),
            })
            classifications.append({
                "group_id": group_id,
                "evidence_class": "object_evidence",
                "classification_reason": decision["visual_witness"],
            })
            audit_row["admitted_group_id"] = group_id
        audit.append(audit_row)
    return result, audit
