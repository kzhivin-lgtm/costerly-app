"""Anthropic transport for Detection V8.2.

This file has no dependency on the experimental V8.1 transport.  It converts
the fixed V8.2 stage inputs to provider messages and returns their audit only;
all semantic decisions live in :mod:`agents.detection_v82`.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from io import BytesIO
import json
from math import ceil, sqrt
from typing import Any, Callable

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_DETECTION_MODEL,
    DETECTION_VISUAL_REGISTRY_TEMPERATURE,
    DetectionVisualRegistryValidationError,
    build_detection_content_blocks,
    build_detection_page_evidence_inventory,
    build_detection_system_content,
    build_detection_v5_review_coordinate_frames,
    create_claude_message_streamed,
    extract_text_from_claude_response,
    format_detection_page_evidence_inventory,
    format_detection_v5_coordinate_frame_context,
    get_anthropic_client,
    get_secret,
    strip_schema_for_claude,
    summarize_detection_provider_call,
)
from agents.detection_v82 import (
    DETECTION_V82_CONFLICT_SCHEMA,
    DETECTION_V82_DISCOVERY_SCHEMA,
    DETECTION_V82_MEMBERSHIP_SCHEMA,
    DetectionV82ContractError,
    run_detection_v82_pipeline,
)
from agents.prompt_loader import (
    load_detection_v82_conflict_prompt,
    load_detection_v82_discovery_prompt,
    load_detection_v82_membership_prompt,
)
from agents.schemas.detection_registry_schema import validate_detection_registry


DETECTION_V82_RELEASE = "8.2.1"
DETECTION_V82_PROMPT_VERSION = "detection_v8_2_1"
DETECTION_V82_DISCOVERY_MAX_TOKENS = 12_288
DETECTION_V82_MEMBERSHIP_MAX_TOKENS = 8_192
DETECTION_V82_CONFLICT_MAX_TOKENS = 1_536
DETECTION_V82_MAX_STREAM_SECONDS = 90.0
DETECTION_V82_MEMBERSHIP_CROP_MAX_SIDE = 1_400
DETECTION_V82_CONFLICT_CROP_MAX_SIDE = 1_600
DETECTION_V82_CONFLICT_CONTEXT_MAX_SIDE = 1_000


class DetectionV82ProviderError(RuntimeError):
    """The provider did not produce a usable V8.2 stage response."""


V82Request = Callable[[str, str, dict[str, Any], list[dict[str, Any]], int], tuple[dict[str, Any], dict[str, Any]]]


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    try:
        bbox = {key: int(value[key]) for key in keys}
    except (KeyError, TypeError, ValueError):
        return None
    if bbox["bottom_right_x"] <= bbox["top_left_x"] or bbox["bottom_right_y"] <= bbox["top_left_y"]:
        return None
    return bbox


def _scale_fusion_to_review(bbox: dict[str, int], *, frame: dict[str, Any]) -> dict[str, int]:
    fusion, review = frame["fusion_dimensions"], frame["review_dimensions"]
    try:
        fw, fh, rw, rh = int(fusion["width"]), int(fusion["height"]), int(review["width"]), int(review["height"])
    except (KeyError, TypeError, ValueError):
        raise DetectionV82ProviderError("V8.2 review coordinate frame is invalid") from None
    if min(fw, fh, rw, rh) <= 0:
        raise DetectionV82ProviderError("V8.2 review coordinate frame is invalid")
    left, top = max(0, min(rw - 1, round(bbox["top_left_x"] * rw / fw))), max(0, min(rh - 1, round(bbox["top_left_y"] * rh / fh)))
    return {
        "top_left_x": left,
        "top_left_y": top,
        "bottom_right_x": max(left + 1, min(rw, round(bbox["bottom_right_x"] * rw / fw))),
        "bottom_right_y": max(top + 1, min(rh, round(bbox["bottom_right_y"] * rh / fh))),
    }


def _scale_review_to_fusion(bbox: dict[str, int], *, frame: dict[str, Any]) -> dict[str, int]:
    fusion, review = frame["fusion_dimensions"], frame["review_dimensions"]
    try:
        fw, fh, rw, rh = int(fusion["width"]), int(fusion["height"]), int(review["width"]), int(review["height"])
    except (KeyError, TypeError, ValueError):
        raise DetectionV82ProviderError("V8.2 review coordinate frame is invalid") from None
    if min(fw, fh, rw, rh) <= 0:
        raise DetectionV82ProviderError("V8.2 review coordinate frame is invalid")
    left, top = max(0, min(fw - 1, round(bbox["top_left_x"] * fw / rw))), max(0, min(fh - 1, round(bbox["top_left_y"] * fh / rh)))
    return {
        "top_left_x": left,
        "top_left_y": top,
        "bottom_right_x": max(left + 1, min(fw, round(bbox["bottom_right_x"] * fw / rw))),
        "bottom_right_y": max(top + 1, min(fh, round(bbox["bottom_right_y"] * fh / rh))),
    }


def _candidate_context(candidates: list[dict[str, Any]]) -> str:
    rows = [
        "CANDIDATE RECALL REGIONS: source observations only, never island geometry.",
        "CR=id|P=page|B=x1,y1,x2,y2|S=sources|D=dimension fact count.",
    ]
    for candidate in candidates:
        bbox = candidate["bbox"]
        rows.append(
            f"{candidate['candidate_region_id']}|P{candidate['page_number']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},{bbox['bottom_right_x']},{bbox['bottom_right_y']}|"
            f"S={','.join(candidate['sources'])}|D={candidate['dimension_fact_count']}"
        )
    return "\n".join(rows)


def _point_in_bbox(point: tuple[float, float], bbox: dict[str, int]) -> bool:
    return bbox["top_left_x"] <= point[0] <= bbox["bottom_right_x"] and bbox["top_left_y"] <= point[1] <= bbox["bottom_right_y"]


def _owned_facts_by_view(source_facts: list[dict[str, Any]], views: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Attach a fact only when exactly one normalized core owns its centre."""
    owned = {str(view["group_id"]): [] for view in views}
    for fact in source_facts:
        if not isinstance(fact, dict):
            continue
        bbox = _bbox(fact.get("bbox"))
        try:
            page_number = int(fact.get("page_number"))
        except (TypeError, ValueError):
            continue
        if bbox is None:
            continue
        point = ((bbox["top_left_x"] + bbox["bottom_right_x"]) / 2, (bbox["top_left_y"] + bbox["bottom_right_y"]) / 2)
        matches = [view for view in views if int(view["page_number"]) == page_number and _point_in_bbox(point, view["core_bbox"])]
        if len(matches) == 1:
            owned[str(matches[0]["group_id"])].append(deepcopy(fact))
    return owned


def _membership_view_sort_key(view: dict[str, Any]) -> tuple[int, int, int, str]:
    """Keep the model's Membership evidence order independent of upstream order."""
    bbox = view["bbox"]
    return (
        int(view["page_number"]),
        int(bbox["top_left_y"]),
        int(bbox["top_left_x"]),
        str(view["group_id"]),
    )


def _membership_context(*, views: list[dict[str, Any]], owned_facts: dict[str, list[dict[str, Any]]]) -> str:
    rows = [
        "FIXED OBJECT EVIDENCE VIEWS:",
        "V=id|P=page|K=representation kind|B=x1,y1,x2,y2|D=visual description|F=owned source text.",
        "A fact occurs under at most one view. It is context only, not a merge command.",
    ]
    for view in sorted(views, key=_membership_view_sort_key):
        bbox = view["bbox"]
        fact_text = "; ".join(
            str(fact.get("text") or "")[:48]
            for fact in owned_facts.get(str(view["group_id"]), [])[:24]
            if str(fact.get("text") or "")
        ) or "-"
        rows.append(
            f"{view['group_id']}|P{view['page_number']}|K={view['representation_kind']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},{bbox['bottom_right_x']},{bbox['bottom_right_y']}|"
            f"D={json.dumps(view['visual_description'], ensure_ascii=False)}|F={json.dumps(fact_text, ensure_ascii=False)}"
        )
    return "\n".join(rows)


def _build_membership_crops(*, page_images: list[bytes], views: list[dict[str, Any]], frames: dict[int, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise DetectionV82ProviderError("V8.2 Membership requires Pillow") from exc
    crops, audit = [], []
    for view in sorted(views, key=_membership_view_sort_key):
        group_id, page_number = str(view["group_id"]), int(view["page_number"])
        if page_number not in frames or not 1 <= page_number <= len(page_images):
            raise DetectionV82ProviderError(f"V8.2 Membership crop unavailable for {group_id}")
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as source:
                image = source.convert("RGB")
            review_bbox = _scale_fusion_to_review(view["bbox"], frame=frames[page_number])
            margin_x = max(8, round((review_bbox["bottom_right_x"] - review_bbox["top_left_x"]) * 0.025))
            margin_y = max(8, round((review_bbox["bottom_right_y"] - review_bbox["top_left_y"]) * 0.025))
            crop_box = {
                "top_left_x": max(0, review_bbox["top_left_x"] - margin_x),
                "top_left_y": max(0, review_bbox["top_left_y"] - margin_y),
                "bottom_right_x": min(image.width, review_bbox["bottom_right_x"] + margin_x),
                "bottom_right_y": min(image.height, review_bbox["bottom_right_y"] + margin_y),
            }
            crop = image.crop((crop_box["top_left_x"], crop_box["top_left_y"], crop_box["bottom_right_x"], crop_box["bottom_right_y"]))
            crop.thumbnail((DETECTION_V82_MEMBERSHIP_CROP_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
            encoded = BytesIO()
            crop.save(encoded, format="JPEG", quality=82)
        except Exception as exc:
            raise DetectionV82ProviderError(f"V8.2 Membership crop unavailable for {group_id}: {type(exc).__name__}") from exc
        crops.append({"group_id": group_id, "page_number": page_number, "bytes": encoded.getvalue()})
        audit.append({"group_id": group_id, "page_number": page_number, "review_bbox": review_bbox, "crop_bbox": crop_box, "crop_dimensions": {"width": crop.width, "height": crop.height}})
    return crops, audit


def _build_membership_board(*, crops: list[dict[str, Any]], views: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one labelled, deterministic contact sheet for global comparison.

    Individual crops preserve detail, but a flat sequence encourages a model to
    stop at adjacent same-page links. This remains one Membership request, not
    another classifier or a pair-selection mechanism.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise DetectionV82ProviderError("V8.2 Membership requires Pillow") from exc
    crop_by_id = {str(crop["group_id"]): crop for crop in crops}
    ordered_views = sorted(views, key=_membership_view_sort_key)
    if set(crop_by_id) != {str(view["group_id"]) for view in ordered_views}:
        raise DetectionV82ProviderError("V8.2 Membership board is missing a view crop")
    tile_width, tile_height, label_height = 320, 250, 34
    columns = min(6, max(1, ceil(sqrt(len(ordered_views)))))
    rows = ceil(len(ordered_views) / columns)
    board = Image.new("RGB", (columns * tile_width, rows * tile_height), "#f5f5f5")
    draw = ImageDraw.Draw(board)
    tile_audit: list[dict[str, Any]] = []
    for index, view in enumerate(ordered_views, start=1):
        group_id = str(view["group_id"])
        crop_data = crop_by_id[group_id]
        try:
            with Image.open(BytesIO(crop_data["bytes"])) as raw_crop:
                crop = raw_crop.convert("RGB")
        except Exception as exc:
            raise DetectionV82ProviderError(f"V8.2 Membership board crop unavailable for {group_id}: {type(exc).__name__}") from exc
        crop.thumbnail((tile_width - 12, tile_height - label_height - 10), Image.Resampling.LANCZOS)
        column, row = (index - 1) % columns, (index - 1) // columns
        left, top = column * tile_width, row * tile_height
        draw.rectangle((left, top, left + tile_width - 1, top + label_height), fill="#1f2937")
        tile_id = f"V{index:02d}"
        draw.text((left + 7, top + 9), f"{tile_id}  P{view['page_number']}  {view['representation_kind']}", fill="white")
        crop_left = left + (tile_width - crop.width) // 2
        crop_top = top + label_height + (tile_height - label_height - crop.height) // 2
        board.paste(crop, (crop_left, crop_top))
        tile_audit.append({
            "tile_id": tile_id,
            "group_id": group_id,
            "page_number": int(view["page_number"]),
            "representation_kind": str(view["representation_kind"]),
        })
    encoded = BytesIO()
    board.save(encoded, format="JPEG", quality=82)
    return {
        "bytes": encoded.getvalue(),
        "audit": {
            "tile_count": len(tile_audit),
            "dimensions": {"width": board.width, "height": board.height},
            "tiles": tile_audit,
        },
    }


def _membership_content(*, context: str, crops: list[dict[str, Any]], board: dict[str, Any]) -> list[dict[str, Any]]:
    tile_legend = "; ".join(
        f"{tile['tile_id']}={tile['group_id']} (P{tile['page_number']}, {tile['representation_kind']})"
        for tile in board["audit"]["tiles"]
    )
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "GLOBAL COMPARISON BOARD. Inspect this board before the individual crops. "
                "It is the complete fixed view set, and PDF page boundaries are not object boundaries. "
                "Tile legend: " + tile_legend
            ),
        },
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(board["bytes"]).decode("ascii")}},
    ]
    for crop in crops:
        content.extend((
            {"type": "text", "text": f"Fixed Object Evidence {crop['group_id']}, PDF page {crop['page_number']}."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(crop["bytes"]).decode("ascii")}},
        ))
    content.append({"type": "text", "text": context})
    return content


def _build_conflict_crop(*, page_images: list[bytes], target: dict[str, Any], frames: dict[int, dict[str, Any]]) -> tuple[dict[str, Any], bytes]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise DetectionV82ProviderError("V8.2 Conflict Resolver requires Pillow") from exc
    page_number = int(target["page_number"])
    if page_number not in frames or not 1 <= page_number <= len(page_images):
        raise DetectionV82ProviderError("V8.2 Conflict Resolver target page is unavailable")
    try:
        with Image.open(BytesIO(page_images[page_number - 1])) as source:
            image = source.convert("RGB")
        review_bbox = _scale_fusion_to_review(target["bbox"], frame=frames[page_number])
        margin_x = max(16, round((review_bbox["bottom_right_x"] - review_bbox["top_left_x"]) * 0.08))
        margin_y = max(16, round((review_bbox["bottom_right_y"] - review_bbox["top_left_y"]) * 0.08))
        crop_box = {
            "top_left_x": max(0, review_bbox["top_left_x"] - margin_x),
            "top_left_y": max(0, review_bbox["top_left_y"] - margin_y),
            "bottom_right_x": min(image.width, review_bbox["bottom_right_x"] + margin_x),
            "bottom_right_y": min(image.height, review_bbox["bottom_right_y"] + margin_y),
        }
        crop = image.crop((crop_box["top_left_x"], crop_box["top_left_y"], crop_box["bottom_right_x"], crop_box["bottom_right_y"]))
        raw_size = {"width": crop.width, "height": crop.height}
        crop.thumbnail((DETECTION_V82_CONFLICT_CROP_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
        crop_buffer = BytesIO()
        crop.save(crop_buffer, format="JPEG", quality=86)
        context = image.copy()
        context.thumbnail((DETECTION_V82_CONFLICT_CONTEXT_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
        context_buffer = BytesIO()
        context.save(context_buffer, format="JPEG", quality=76)
    except Exception as exc:
        raise DetectionV82ProviderError(f"V8.2 Conflict Resolver crop unavailable: {type(exc).__name__}") from exc
    return {
        "target_id": str(target["target_id"]), "page_number": page_number, "bytes": crop_buffer.getvalue(),
        "review_crop_bbox": crop_box, "raw_crop_dimensions": raw_size,
        "crop_dimensions": {"width": crop.width, "height": crop.height},
    }, context_buffer.getvalue()


def _conflict_content(crop: dict[str, Any], context: bytes) -> list[dict[str, Any]]:
    return [
        {"type": "text", "text": f"PDF page {crop['page_number']} orientation context."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(context).decode("ascii")}},
        {"type": "text", "text": f"Inspection target {crop['target_id']} on PDF page {crop['page_number']}. The next crop frame is {crop['crop_dimensions']['width']}x{crop['crop_dimensions']['height']} pixels."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(crop["bytes"]).decode("ascii")}},
    ]


def _map_crop_to_fusion(value: object, *, crop: dict[str, Any], frame: dict[str, Any]) -> dict[str, int] | None:
    local = _bbox(value)
    if local is None:
        return None
    raw, output, origin = crop["raw_crop_dimensions"], crop["crop_dimensions"], crop["review_crop_bbox"]
    try:
        review = {
            "top_left_x": origin["top_left_x"] + round(local["top_left_x"] * raw["width"] / output["width"]),
            "top_left_y": origin["top_left_y"] + round(local["top_left_y"] * raw["height"] / output["height"]),
            "bottom_right_x": origin["top_left_x"] + round(local["bottom_right_x"] * raw["width"] / output["width"]),
            "bottom_right_y": origin["top_left_y"] + round(local["bottom_right_y"] * raw["height"] / output["height"]),
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return _scale_review_to_fusion(review, frame=frame)


def _publish_v82(pipeline: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    retained_ids = {group_id for component in pipeline["components"] for group_id in component}
    views = [view for view in pipeline["discovery"]["object_evidence"] if str(view["group_id"]) in retained_ids]
    views = sorted(views, key=lambda item: (int(item["page_number"]), item["bbox"]["top_left_y"], item["bbox"]["top_left_x"], str(item["group_id"])))
    public_ids = {str(view["group_id"]): f"view-{index:03d}" for index, view in enumerate(views, start=1)}
    visual_groups = [{
        "group_id": public_ids[str(view["group_id"])],
        "page_number": int(view["page_number"]),
        "location_hint": f"P{view['page_number']}",
        "visual_description": str(view["visual_description"]),
        "representation_kind": str(view["representation_kind"]),
    } for view in views]
    visual_map = {
        "visual_groups": visual_groups,
        "_registry_owned_evidence": [{
            **group, "bbox": deepcopy(view["bbox"]), "core_bbox": deepcopy(view["core_bbox"]), "evidence_class": "object_evidence",
        } for group, view in zip(visual_groups, views, strict=True)],
    }
    view_by_id = {str(view["group_id"]): view for view in views}
    links = pipeline["membership"]["accepted_links"]
    objects = []
    for index, component in enumerate(pipeline["components"], start=1):
        component_views = [view_by_id[group_id] for group_id in sorted(component)]
        proof_kinds = sorted({proof["kind"] for link in links if link["group_id_a"] in component and link["group_id_b"] in component for proof in link["proofs"]})
        pages = sorted({int(view["page_number"]) for view in component_views})
        objects.append({
            "object_id": f"object-{index:03d}", "transport_label": "Unlabelled", "quantity": 1, "quantity_explicit": False,
            "identity_pages": pages, "estimation_evidence_pages": pages,
            "visual_group_ids": sorted(public_ids[group_id] for group_id in component),
            "visual_identity": "; ".join(str(view["visual_description"]) for view in component_views)[:900],
            "boundary_basis": "Singleton Object Evidence view." if not proof_kinds else "Accepted V8.2 Membership proofs: " + ", ".join(proof_kinds) + ".",
        })
    registry = validate_detection_registry({"objects": objects}, visual_group_ids={group["group_id"] for group in visual_groups}, object_evidence_group_ids={group["group_id"] for group in visual_groups})
    return visual_map, registry


def run_detection_v82_with_request(*, file_name: str, company_id: str, file_bytes: bytes, page_images: list[bytes], ocr_package: dict[str, Any] | None, request_json: V82Request) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run V8.2 with injectable transport for direct contract testing."""
    if not page_images:
        raise DetectionV82ProviderError("V8.2 requires rendered PDF pages")
    source_facts = build_detection_page_evidence_inventory(ocr_package)
    frames, frame_audit = build_detection_v5_review_coordinate_frames(ocr_package=ocr_package, page_images=page_images)
    page_dimensions = {page: (int(frame["fusion_dimensions"]["width"]), int(frame["fusion_dimensions"]["height"])) for page, frame in frames.items()}
    if set(page_dimensions) != set(range(1, len(page_images) + 1)):
        raise DetectionV82ProviderError("V8.2 cannot establish every page coordinate frame")
    calls: list[dict[str, Any]] = []

    def discover(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        content = build_detection_content_blocks(
            file_name=file_name, file_bytes=file_bytes, page_images=page_images,
            user_text=(
                "RFQ Detection V8.2. Discover every visual island once.\n\n"
                + format_detection_page_evidence_inventory(source_facts, max_chars=65_000)
                + "\n\n" + _candidate_context(candidates)
                + "\n\n" + format_detection_v5_coordinate_frame_context(frames)
            ),
        )
        payload, audit = request_json("discovery", load_detection_v82_discovery_prompt(), DETECTION_V82_DISCOVERY_SCHEMA, content, DETECTION_V82_DISCOVERY_MAX_TOKENS)
        calls.append({"stage": "discovery", **audit})
        if not isinstance(payload, dict) or set(payload) != {"islands"}:
            raise DetectionV82ProviderError("V8.2 Discovery response does not match its contract")
        return payload["islands"]

    def resolve_conflict(target: dict[str, Any]) -> dict[str, Any]:
        crop, context = _build_conflict_crop(page_images=page_images, target=target, frames=frames)
        payload, audit = request_json("conflict_resolver", load_detection_v82_conflict_prompt(), DETECTION_V82_CONFLICT_SCHEMA, _conflict_content(crop, context), DETECTION_V82_CONFLICT_MAX_TOKENS)
        calls.append({"stage": "conflict_resolver", "target_id": target["target_id"], **audit})
        if not isinstance(payload, dict) or str(payload.get("target_id") or "") != str(target["target_id"]) or str(payload.get("decision") or "") not in {"object_evidence", "exclude"}:
            raise DetectionV82ProviderError("V8.2 Conflict Resolver response does not match its contract")
        if payload["decision"] == "exclude":
            return payload
        required = {"bbox", "core_bbox", "representation_kind", "visual_description", "reason"}
        if not required.issubset(payload):
            raise DetectionV82ProviderError("V8.2 Conflict Resolver admission lacks required evidence")
        bbox, core_bbox = _map_crop_to_fusion(payload["bbox"], crop=crop, frame=frames[int(target["page_number"])]), _map_crop_to_fusion(payload["core_bbox"], crop=crop, frame=frames[int(target["page_number"])])
        if bbox is None or core_bbox is None:
            raise DetectionV82ProviderError("V8.2 Conflict Resolver returned an invalid crop bbox")
        return {**payload, "bbox": bbox, "core_bbox": core_bbox}

    def review_membership(views: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not views:
            return []
        owned_facts = _owned_facts_by_view(source_facts, views)
        crops, crop_audit = _build_membership_crops(page_images=page_images, views=views, frames=frames)
        board = _build_membership_board(crops=crops, views=views)
        payload, audit = request_json("membership", load_detection_v82_membership_prompt(), DETECTION_V82_MEMBERSHIP_SCHEMA, _membership_content(context=_membership_context(views=views, owned_facts=owned_facts), crops=crops, board=board), DETECTION_V82_MEMBERSHIP_MAX_TOKENS)
        calls.append({"stage": "membership", "crop_count": len(crops), "owned_source_fact_count": sum(len(value) for value in owned_facts.values()), "crop_audit": crop_audit, "global_comparison_board": board["audit"], **audit})
        if not isinstance(payload, dict) or set(payload) != {"links"}:
            raise DetectionV82ProviderError("V8.2 Membership response does not match its contract")
        return payload["links"]

    try:
        pipeline = run_detection_v82_pipeline(ocr_package=ocr_package, source_facts=source_facts, page_dimensions=page_dimensions, discover=discover, resolve_conflict=resolve_conflict, review_membership=review_membership)
        visual_map, registry = _publish_v82(pipeline)
    except (DetectionV82ContractError, DetectionVisualRegistryValidationError) as exc:
        raise DetectionV82ProviderError(f"V8.2 stage contract failed: {exc}") from exc
    return visual_map, registry, {"pipeline": pipeline, "provider_calls": calls, "source_fact_count": len(source_facts), "page_coordinate_frame_audit": frame_audit}


def run_anthropic_detection_v82(*, file_name: str, company_id: str, file_bytes: bytes, page_images: list[bytes], ocr_package: dict[str, Any] | None, model: str | None, stage_callback: Callable[..., None] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run one explicitly versioned V8.2 provider pipeline."""
    selected_model = model or get_secret("CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
    client = get_anthropic_client()
    def request_json(stage: str, prompt: str, schema: dict[str, Any], content: list[dict[str, Any]], max_tokens: int) -> tuple[dict[str, Any], dict[str, Any]]:
        if stage_callback:
            stage_callback(f"V8.2 {stage.replace('_', ' ')} started")
        try:
            response, diagnostics = create_claude_message_streamed(client, model=selected_model, max_tokens=max_tokens, max_stream_seconds=DETECTION_V82_MAX_STREAM_SECONDS, on_stream_phase=(lambda phase, elapsed: stage_callback(f"V8.2 {stage.replace('_', ' ')} {phase} ({elapsed:.1f}s)")) if stage_callback else None, temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE, system=build_detection_system_content(prompt=prompt), messages=[{"role": "user", "content": content}], output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(schema)}})
            payload = json.loads(extract_text_from_claude_response(response))
        except json.JSONDecodeError as exc:
            raise DetectionV82ProviderError(f"V8.2 {stage} response ended before valid JSON. No downstream stage was run.") from exc
        except RuntimeError as exc:
            raise DetectionV82ProviderError(f"V8.2 {stage} request failed: {exc}") from exc
        summary = summarize_detection_provider_call(response=response, diagnostics=diagnostics, requested_model=selected_model, prompt_characters=len(prompt), context_characters=sum(len(str(block.get("text") or "")) for block in content if isinstance(block, dict)), image_count=sum(1 for block in content if block.get("type") == "image"), image_bytes=sum(len(str((block.get("source") or {}).get("data") or "")) * 3 // 4 for block in content if block.get("type") == "image"))
        if stage_callback:
            stage_callback(f"V8.2 {stage.replace('_', ' ')} completed")
        return payload, summary
    try:
        visual_map, registry, audit = run_detection_v82_with_request(file_name=file_name, company_id=company_id, file_bytes=file_bytes, page_images=page_images, ocr_package=ocr_package, request_json=request_json)
    except DetectionV82ProviderError as exc:
        usage = {"agent_name": "detection", "operation": "rfq_detection_v8_2", "file_name": file_name, "company_id": company_id, "model": selected_model, "prompt_version": DETECTION_V82_PROMPT_VERSION, "status": "failed", "error_message": str(exc), "raw_usage": {"cost_category": "detection", "detection_v8_2": {"release": DETECTION_V82_RELEASE, "error": str(exc)}}}
        raise DetectionVisualRegistryValidationError(f"Detection V8.2 failed: {exc}", usage_event=usage) from exc
    calls = audit["provider_calls"]
    usage = {
        "agent_name": "detection", "operation": "rfq_detection_v8_2", "file_name": file_name, "company_id": company_id, "model": selected_model, "prompt_version": DETECTION_V82_PROMPT_VERSION, "status": "succeeded",
        "input_tokens": sum(int(call.get("input_tokens") or 0) for call in calls), "output_tokens": sum(int(call.get("output_tokens") or 0) for call in calls),
        "input_cost_usd": round(sum(float(call.get("input_cost_usd") or 0) for call in calls), 8), "output_cost_usd": round(sum(float(call.get("output_cost_usd") or 0) for call in calls), 8), "total_cost_usd": round(sum(float(call.get("total_cost_usd") or 0) for call in calls), 8), "duration_seconds": round(sum(float(call.get("duration_seconds") or 0) for call in calls), 3),
        "raw_usage": {"cost_category": "detection", "detection_v8_2": audit | {"release": DETECTION_V82_RELEASE}, "ordinary_provider_call_count": sum(1 for call in calls if call.get("stage") in {"discovery", "membership"}), "exceptional_conflict_call_count": sum(1 for call in calls if call.get("stage") == "conflict_resolver")},
    }
    return visual_map, registry, usage
