"""Anthropic transport for the bounded Detection V8 pipeline.

The semantic pipeline lives in :mod:`agents.detection_v8`.  This module has a
strictly smaller job: render the fixed inputs for each stage, make at most two
ordinary provider calls, and materialize deterministic output for the existing
Detection handoff.  It must not import V7 candidate, resolver, render-adapter
or membership logic.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from io import BytesIO
import json
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
from agents.detection_v8 import (
    DETECTION_V8_CONFLICT_SCHEMA,
    DETECTION_V8_DISCOVERY_SCHEMA,
    DETECTION_V8_MEMBERSHIP_SCHEMA,
    DetectionV8ContractError,
    run_detection_v8_pipeline,
)
from agents.prompt_loader import (
    load_detection_v8_conflict_prompt,
    load_detection_v8_discovery_prompt,
    load_detection_v8_membership_prompt,
)
from agents.schemas.detection_registry_schema import validate_detection_registry


DETECTION_V8_PROMPT_VERSION = "detection_v8_stage_separated"
DETECTION_V8_DISCOVERY_MAX_TOKENS = 10_240
DETECTION_V8_MEMBERSHIP_MAX_TOKENS = 8_192
DETECTION_V8_CONFLICT_MAX_TOKENS = 1_536
DETECTION_V8_MAX_STREAM_SECONDS = 90.0
DETECTION_V8_MEMBERSHIP_CROP_MAX_SIDE = 1_600
DETECTION_V8_CONFLICT_CROP_MAX_SIDE = 1_600
DETECTION_V8_CONFLICT_CONTEXT_MAX_SIDE = 1_000


class DetectionV8ProviderError(RuntimeError):
    """One V8 provider stage returned invalid or unusable data."""


V8Request = Callable[[str, str, dict[str, Any], list[dict[str, Any]], int], tuple[dict[str, Any], dict[str, Any]]]


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
    return (
        max(left["top_left_x"], right["top_left_x"])
        < min(left["bottom_right_x"], right["bottom_right_x"])
        and max(left["top_left_y"], right["top_left_y"])
        < min(left["bottom_right_y"], right["bottom_right_y"])
    )


def _scale_fusion_bbox_to_review(
    bbox: dict[str, int],
    *,
    frame: dict[str, Any],
) -> dict[str, int]:
    fusion = frame["fusion_dimensions"]
    review = frame["review_dimensions"]
    fusion_width, fusion_height = int(fusion["width"]), int(fusion["height"])
    review_width, review_height = int(review["width"]), int(review["height"])
    if min(fusion_width, fusion_height, review_width, review_height) <= 0:
        raise DetectionV8ProviderError("V8 review coordinate frame is invalid")
    left = max(0, min(review_width - 1, round(bbox["top_left_x"] * review_width / fusion_width)))
    top = max(0, min(review_height - 1, round(bbox["top_left_y"] * review_height / fusion_height)))
    right = max(left + 1, min(review_width, round(bbox["bottom_right_x"] * review_width / fusion_width)))
    bottom = max(top + 1, min(review_height, round(bbox["bottom_right_y"] * review_height / fusion_height)))
    return {
        "top_left_x": left, "top_left_y": top,
        "bottom_right_x": right, "bottom_right_y": bottom,
    }


def _scale_review_bbox_to_fusion(
    bbox: dict[str, int],
    *,
    frame: dict[str, Any],
) -> dict[str, int]:
    fusion = frame["fusion_dimensions"]
    review = frame["review_dimensions"]
    fusion_width, fusion_height = int(fusion["width"]), int(fusion["height"])
    review_width, review_height = int(review["width"]), int(review["height"])
    if min(fusion_width, fusion_height, review_width, review_height) <= 0:
        raise DetectionV8ProviderError("V8 review coordinate frame is invalid")
    left = max(0, min(fusion_width - 1, round(bbox["top_left_x"] * fusion_width / review_width)))
    top = max(0, min(fusion_height - 1, round(bbox["top_left_y"] * fusion_height / review_height)))
    right = max(left + 1, min(fusion_width, round(bbox["bottom_right_x"] * fusion_width / review_width)))
    bottom = max(top + 1, min(fusion_height, round(bbox["bottom_right_y"] * fusion_height / review_height)))
    return {
        "top_left_x": left, "top_left_y": top,
        "bottom_right_x": right, "bottom_right_y": bottom,
    }


def _candidate_context(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "CANDIDATE RECALL REGIONS:",
        "Each row is a source observation only. It cannot create, split, merge or bound an island.",
        "CR=id|P=page|B=x1,y1,x2,y2|S=sources|F=source fact IDs.",
    ]
    for candidate in candidates:
        bbox = candidate["bbox"]
        lines.append(
            f"{candidate['candidate_region_id']}|P{candidate['page_number']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},{bbox['bottom_right_x']},{bbox['bottom_right_y']}|"
            f"S={','.join(candidate['sources'])}|F={','.join(candidate['source_fact_ids']) or '-'}"
        )
    return "\n".join(lines)


def _facts_for_membership(
    source_facts: list[dict[str, Any]],
    object_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Supply only local immutable facts, never V7-derived relation hints."""
    selected: list[dict[str, Any]] = []
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
        if any(
            page_number == int(view["page_number"])
            and _overlaps(bbox, view["bbox"])
            for view in object_evidence
        ):
            selected.append(deepcopy(fact))
    return selected


def _membership_context(
    *,
    object_evidence: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
) -> str:
    lines = [
        "FIXED OBJECT EVIDENCE VIEWS:",
        "V=id|P=page|K=representation kind|B=x1,y1,x2,y2|D=visual description.",
    ]
    for view in object_evidence:
        bbox = view["bbox"]
        lines.append(
            f"{view['group_id']}|P{view['page_number']}|K={view['representation_kind']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},{bbox['bottom_right_x']},{bbox['bottom_right_y']}|"
            f"D={json.dumps(view['visual_description'], ensure_ascii=False)}"
        )
    return "\n".join(lines) + "\n\n" + format_detection_page_evidence_inventory(
        source_facts, max_chars=70_000,
    )


def _build_v8_membership_crops(
    *,
    page_images: list[bytes],
    object_evidence: list[dict[str, Any]],
    coordinate_frames: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create fixed view crops. This is transport, never a new island pass."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise DetectionV8ProviderError("V8 Membership requires Pillow for fixed view crops") from exc

    crops: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for view in object_evidence:
        group_id = str(view["group_id"])
        page_number = int(view["page_number"])
        if not 1 <= page_number <= len(page_images) or page_number not in coordinate_frames:
            raise DetectionV8ProviderError(f"V8 Membership crop unavailable for {group_id}")
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as source:
                image = source.convert("RGB")
            review_bbox = _scale_fusion_bbox_to_review(
                view["bbox"], frame=coordinate_frames[page_number],
            )
            width, height = image.size
            margin_x = max(8, round((review_bbox["bottom_right_x"] - review_bbox["top_left_x"]) * 0.04))
            margin_y = max(8, round((review_bbox["bottom_right_y"] - review_bbox["top_left_y"]) * 0.04))
            crop_box = {
                "top_left_x": max(0, review_bbox["top_left_x"] - margin_x),
                "top_left_y": max(0, review_bbox["top_left_y"] - margin_y),
                "bottom_right_x": min(width, review_bbox["bottom_right_x"] + margin_x),
                "bottom_right_y": min(height, review_bbox["bottom_right_y"] + margin_y),
            }
            crop = image.crop((
                crop_box["top_left_x"], crop_box["top_left_y"],
                crop_box["bottom_right_x"], crop_box["bottom_right_y"],
            ))
            crop.thumbnail((DETECTION_V8_MEMBERSHIP_CROP_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
            encoded = BytesIO()
            crop.save(encoded, format="JPEG", quality=82)
        except DetectionV8ProviderError:
            raise
        except Exception as exc:
            raise DetectionV8ProviderError(
                f"V8 Membership crop unavailable for {group_id}: {type(exc).__name__}"
            ) from exc
        crops.append({"group_id": group_id, "page_number": page_number, "bytes": encoded.getvalue()})
        audit.append({
            "group_id": group_id, "page_number": page_number,
            "review_bbox": review_bbox, "crop_bbox": crop_box,
            "crop_dimensions": {"width": crop.width, "height": crop.height},
        })
    return crops, audit


def _membership_content(*, user_text: str, crops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for crop in crops:
        blocks.append({
            "type": "text",
            "text": f"Fixed Object Evidence {crop['group_id']}, PDF page {crop['page_number']}.",
        })
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": base64.standard_b64encode(crop["bytes"]).decode("ascii"),
            },
        })
    blocks.append({"type": "text", "text": user_text})
    return blocks


def _build_v8_conflict_crop(
    *,
    page_images: list[bytes],
    target: dict[str, Any],
    coordinate_frames: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any], bytes]:
    """Return one neutral crop and a small page orientation image."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise DetectionV8ProviderError("V8 Conflict Resolver requires Pillow") from exc

    page_number = int(target["page_number"])
    if not 1 <= page_number <= len(page_images) or page_number not in coordinate_frames:
        raise DetectionV8ProviderError("V8 Conflict Resolver target page is unavailable")
    try:
        with Image.open(BytesIO(page_images[page_number - 1])) as source:
            image = source.convert("RGB")
        review_bbox = _scale_fusion_bbox_to_review(
            target["bbox"], frame=coordinate_frames[page_number],
        )
        width, height = image.size
        margin_x = max(16, round((review_bbox["bottom_right_x"] - review_bbox["top_left_x"]) * 0.08))
        margin_y = max(16, round((review_bbox["bottom_right_y"] - review_bbox["top_left_y"]) * 0.08))
        crop_bbox = {
            "top_left_x": max(0, review_bbox["top_left_x"] - margin_x),
            "top_left_y": max(0, review_bbox["top_left_y"] - margin_y),
            "bottom_right_x": min(width, review_bbox["bottom_right_x"] + margin_x),
            "bottom_right_y": min(height, review_bbox["bottom_right_y"] + margin_y),
        }
        crop = image.crop((
            crop_bbox["top_left_x"], crop_bbox["top_left_y"],
            crop_bbox["bottom_right_x"], crop_bbox["bottom_right_y"],
        ))
        raw_crop_dimensions = {"width": crop.width, "height": crop.height}
        crop.thumbnail((DETECTION_V8_CONFLICT_CROP_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
        crop_output = BytesIO()
        crop.save(crop_output, format="JPEG", quality=86)
        context = image.copy()
        context.thumbnail((DETECTION_V8_CONFLICT_CONTEXT_MAX_SIDE,) * 2, Image.Resampling.LANCZOS)
        context_output = BytesIO()
        context.save(context_output, format="JPEG", quality=76)
    except Exception as exc:
        raise DetectionV8ProviderError(
            f"V8 Conflict Resolver crop unavailable: {type(exc).__name__}"
        ) from exc
    return {
        "target_id": str(target["target_id"]), "page_number": page_number,
        "bytes": crop_output.getvalue(), "review_crop_bbox": crop_bbox,
        "raw_crop_dimensions": raw_crop_dimensions,
        "crop_dimensions": {"width": crop.width, "height": crop.height},
    }, context_output.getvalue()


def _conflict_content(crop: dict[str, Any], context: bytes) -> list[dict[str, Any]]:
    return [
        {"type": "text", "text": f"PDF page {crop['page_number']} orientation context."},
        {"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.standard_b64encode(context).decode("ascii"),
        }},
        {"type": "text", "text": (
            f"Inspection target {crop['target_id']} on PDF page {crop['page_number']}. "
            "The next image is the target crop. Return bbox coordinates in this crop's "
            f"pixel frame {crop['crop_dimensions']['width']}x{crop['crop_dimensions']['height']}."
        )},
        {"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.standard_b64encode(crop["bytes"]).decode("ascii"),
        }},
    ]


def _map_crop_box_to_fusion(
    value: object,
    *,
    crop: dict[str, Any],
    frame: dict[str, Any],
) -> dict[str, int] | None:
    local = _bbox(value)
    if local is None:
        return None
    output = crop["crop_dimensions"]
    raw = crop["raw_crop_dimensions"]
    source = crop["review_crop_bbox"]
    try:
        scaled = {
            "top_left_x": source["top_left_x"] + round(local["top_left_x"] * raw["width"] / output["width"]),
            "top_left_y": source["top_left_y"] + round(local["top_left_y"] * raw["height"] / output["height"]),
            "bottom_right_x": source["top_left_x"] + round(local["bottom_right_x"] * raw["width"] / output["width"]),
            "bottom_right_y": source["top_left_y"] + round(local["bottom_right_y"] * raw["height"] / output["height"]),
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return _scale_review_bbox_to_fusion(scaled, frame=frame)


def _published_v8_output(pipeline: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply terminal presentation IDs after all V8 membership decisions end."""
    # An unattached presentation render is Object Evidence during Membership,
    # but intentionally has no final object component.  It must therefore not
    # be published as registry Object Evidence, whose contract requires every
    # such group to belong to exactly one object.
    retained_group_ids = {
        str(group_id)
        for component in pipeline["components"]
        for group_id in component
    }
    views = [
        view for view in pipeline["discovery"]["object_evidence"]
        if str(view["group_id"]) in retained_group_ids
    ]
    view_order = sorted(views, key=lambda item: (
        int(item["page_number"]),
        int(item["bbox"]["top_left_y"]),
        int(item["bbox"]["top_left_x"]),
        int(item["bbox"]["bottom_right_y"]),
        int(item["bbox"]["bottom_right_x"]),
        str(item["group_id"]),
    ))
    public_id = {
        str(view["group_id"]): f"view-{index:03d}"
        for index, view in enumerate(view_order, start=1)
    }
    visual_groups = [{
        "group_id": public_id[str(view["group_id"])],
        "page_number": int(view["page_number"]),
        "location_hint": f"P{view['page_number']}",
        "visual_description": str(view["visual_description"]),
        "representation_kind": str(view["representation_kind"]),
    } for view in view_order]
    private_groups = [{
        **group,
        "bbox": deepcopy(view["bbox"]),
        "core_bbox": deepcopy(view["core_bbox"]),
        "evidence_class": "object_evidence",
    } for group, view in zip(visual_groups, view_order, strict=True)]
    visual_map = {
        "visual_groups": visual_groups,
        "_registry_owned_evidence": private_groups,
    }

    links_by_component: dict[str, list[dict[str, Any]]] = {}
    for link in pipeline["membership"]["accepted_links"]:
        for group_id in (str(link["group_id_a"]), str(link["group_id_b"])):
            links_by_component.setdefault(group_id, []).append(link)
    view_by_id = {str(view["group_id"]): view for view in views}
    objects: list[dict[str, Any]] = []
    for index, component in enumerate(pipeline["components"], start=1):
        component_ids = sorted(component)
        component_views = [view_by_id[group_id] for group_id in component_ids]
        pages = sorted({int(view["page_number"]) for view in component_views})
        evidence_types = sorted({
            row["evidence_type"]
            for group_id in component_ids
            for link in links_by_component.get(group_id, [])
            for row in link["evidence"]
        })
        objects.append({
            "object_id": f"object-{index:03d}",
            "transport_label": "Unlabelled",
            "quantity": 1,
            "quantity_explicit": False,
            "identity_pages": pages,
            "estimation_evidence_pages": pages,
            "visual_group_ids": sorted(
                (public_id[group_id] for group_id in component_ids),
            ),
            "visual_identity": "; ".join(
                str(view["visual_description"]) for view in component_views
            )[:900],
            "boundary_basis": (
                "Singleton Object Evidence view."
                if not evidence_types else
                "Accepted V8 Membership evidence: " + ", ".join(evidence_types) + "."
            ),
        })
    registry = validate_detection_registry(
        {"objects": objects},
        visual_group_ids={group["group_id"] for group in visual_groups},
        object_evidence_group_ids={group["group_id"] for group in visual_groups},
    )
    return visual_map, registry


def run_detection_v8_with_request(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    request_json: V8Request,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run V8 with an injected request function, suitable for live or fake transport."""
    if not page_images:
        raise DetectionV8ProviderError("V8 requires rendered PDF pages")
    source_facts = build_detection_page_evidence_inventory(ocr_package)
    frames, frame_audit = build_detection_v5_review_coordinate_frames(
        ocr_package=ocr_package, page_images=page_images,
    )
    page_dimensions = {
        page_number: (
            int(frame["fusion_dimensions"]["width"]),
            int(frame["fusion_dimensions"]["height"]),
        )
        for page_number, frame in frames.items()
    }
    if set(page_dimensions) != set(range(1, len(page_images) + 1)):
        raise DetectionV8ProviderError("V8 cannot establish every page coordinate frame")
    discovery_prompt = load_detection_v8_discovery_prompt()
    membership_prompt = load_detection_v8_membership_prompt()
    conflict_prompt = load_detection_v8_conflict_prompt()
    calls: list[dict[str, Any]] = []

    def discover(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        user_text = (
            "RFQ Detection V8. Discover every visual island once.\n\n"
            + format_detection_page_evidence_inventory(source_facts, max_chars=90_000)
            + "\n\n" + _candidate_context(candidates)
            + "\n\n" + format_detection_v5_coordinate_frame_context(frames)
        )
        content = build_detection_content_blocks(
            file_name=file_name, file_bytes=file_bytes,
            page_images=page_images, user_text=user_text,
        )
        payload, audit = request_json(
            "discovery", discovery_prompt, DETECTION_V8_DISCOVERY_SCHEMA,
            content, DETECTION_V8_DISCOVERY_MAX_TOKENS,
        )
        calls.append({"stage": "discovery", **audit})
        if not isinstance(payload, dict) or set(payload) != {"islands"}:
            raise DetectionV8ProviderError("V8 Discovery response does not match its contract")
        return payload["islands"]

    def resolve_conflict(target: dict[str, Any]) -> dict[str, Any]:
        crop, context = _build_v8_conflict_crop(
            page_images=page_images, target=target, coordinate_frames=frames,
        )
        payload, audit = request_json(
            "conflict_resolver", conflict_prompt, DETECTION_V8_CONFLICT_SCHEMA,
            _conflict_content(crop, context), DETECTION_V8_CONFLICT_MAX_TOKENS,
        )
        calls.append({"stage": "conflict_resolver", "target_id": target["target_id"], **audit})
        allowed_fields = {
            "target_id", "decision", "bbox", "core_bbox", "representation_kind",
            "visual_description", "reason",
        }
        if (
            not isinstance(payload, dict)
            or not {"target_id", "decision", "reason"}.issubset(payload)
            or not set(payload).issubset(allowed_fields)
        ):
            raise DetectionV8ProviderError("V8 Conflict Resolver response does not match its contract")
        if str(payload.get("target_id") or "") != str(target["target_id"]):
            raise DetectionV8ProviderError("V8 Conflict Resolver returned the wrong target")
        if str(payload.get("decision") or "") == "exclude":
            return payload
        if not {
            "bbox", "core_bbox", "representation_kind", "visual_description",
        }.issubset(payload):
            raise DetectionV8ProviderError("V8 Conflict Resolver admission lacks object evidence fields")
        mapped_bbox = _map_crop_box_to_fusion(
            payload.get("bbox"), crop=crop, frame=frames[int(target["page_number"])],
        )
        mapped_core = _map_crop_box_to_fusion(
            payload.get("core_bbox"), crop=crop, frame=frames[int(target["page_number"])],
        )
        if mapped_bbox is None or mapped_core is None:
            raise DetectionV8ProviderError("V8 Conflict Resolver returned an invalid crop bbox")
        return {**payload, "bbox": mapped_bbox, "core_bbox": mapped_core}

    def review_membership(object_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not object_evidence:
            return []
        local_facts = _facts_for_membership(source_facts, object_evidence)
        crops, crop_audit = _build_v8_membership_crops(
            page_images=page_images,
            object_evidence=object_evidence,
            coordinate_frames=frames,
        )
        payload, audit = request_json(
            "membership", membership_prompt, DETECTION_V8_MEMBERSHIP_SCHEMA,
            _membership_content(
                user_text=_membership_context(
                    object_evidence=object_evidence, source_facts=local_facts,
                ),
                crops=crops,
            ),
            DETECTION_V8_MEMBERSHIP_MAX_TOKENS,
        )
        calls.append({
            "stage": "membership", "crop_count": len(crops),
            "local_source_fact_count": len(local_facts), "crop_audit": crop_audit,
            **audit,
        })
        if not isinstance(payload, dict) or set(payload) != {"links"}:
            raise DetectionV8ProviderError("V8 Membership response does not match its contract")
        return payload["links"]

    try:
        pipeline = run_detection_v8_pipeline(
            ocr_package=ocr_package,
            source_facts=source_facts,
            page_dimensions=page_dimensions,
            discover=discover,
            resolve_conflict=resolve_conflict,
            review_membership=review_membership,
        )
        visual_map, registry = _published_v8_output(pipeline)
    except DetectionV8ContractError as exc:
        raise DetectionV8ProviderError(f"V8 stage contract failed: {exc}") from exc
    return visual_map, registry, {
        "pipeline": pipeline,
        "provider_calls": calls,
        "source_fact_count": len(source_facts),
        "page_coordinate_frame_audit": frame_audit,
    }


def run_anthropic_detection_v8_stage_separated(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    model: str | None,
    stage_callback: Callable[..., None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run V8 through Anthropic without touching the default V7 route."""
    selected_model = model or get_secret("CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
    client = get_anthropic_client()

    def request_json(
        stage: str,
        prompt: str,
        schema: dict[str, Any],
        content: list[dict[str, Any]],
        max_tokens: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if stage_callback is not None:
            stage_callback(f"V8 {stage.replace('_', ' ')} started")
        try:
            response, diagnostics = create_claude_message_streamed(
                client,
                model=selected_model,
                max_tokens=max_tokens,
                max_stream_seconds=DETECTION_V8_MAX_STREAM_SECONDS,
                on_stream_phase=(
                    (lambda phase, elapsed: stage_callback(
                        f"V8 {stage.replace('_', ' ')} {phase} ({elapsed:.1f}s)"
                    )) if stage_callback is not None else None
                ),
                temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
                system=build_detection_system_content(prompt=prompt),
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(schema)}},
            )
            payload = json.loads(extract_text_from_claude_response(response))
        except json.JSONDecodeError as exc:
            raise DetectionV8ProviderError(
                f"V8 {stage} response ended before valid JSON. "
                "No downstream stage was run."
            ) from exc
        except RuntimeError as exc:
            raise DetectionV8ProviderError(f"V8 {stage} request failed: {exc}") from exc
        summary = summarize_detection_provider_call(
            response=response, diagnostics=diagnostics, requested_model=selected_model,
            prompt_characters=len(prompt),
            context_characters=sum(
                len(str(block.get("text") or "")) for block in content
                if isinstance(block, dict)
            ),
            image_count=sum(1 for block in content if block.get("type") == "image"),
            image_bytes=sum(
                len(str((block.get("source") or {}).get("data") or "")) * 3 // 4
                for block in content if block.get("type") == "image"
            ),
        )
        if stage_callback is not None:
            stage_callback(f"V8 {stage.replace('_', ' ')} completed")
        return payload, summary

    try:
        visual_map, registry, audit = run_detection_v8_with_request(
            file_name=file_name, company_id=company_id, file_bytes=file_bytes,
            page_images=page_images, ocr_package=ocr_package,
            request_json=request_json,
        )
    except DetectionV8ProviderError as exc:
        usage = {
            "agent_name": "detection",
            "operation": "rfq_detection_v8_stage_separated",
            "file_name": file_name,
            "company_id": company_id,
            "model": selected_model,
            "prompt_version": DETECTION_V8_PROMPT_VERSION,
            "status": "failed",
            "error_message": str(exc),
            "raw_usage": {"cost_category": "detection", "detection_v8": {"error": str(exc)}},
        }
        raise DetectionVisualRegistryValidationError(
            f"Detection V8 failed: {exc}", usage_event=usage,
        ) from exc

    calls = audit["provider_calls"]
    usage = {
        "agent_name": "detection",
        "operation": "rfq_detection_v8_stage_separated",
        "file_name": file_name,
        "company_id": company_id,
        "model": selected_model,
        "prompt_version": DETECTION_V8_PROMPT_VERSION,
        "status": "succeeded",
        "input_tokens": sum(int(call.get("input_tokens") or 0) for call in calls),
        "output_tokens": sum(int(call.get("output_tokens") or 0) for call in calls),
        "input_cost_usd": round(sum(float(call.get("input_cost_usd") or 0) for call in calls), 8),
        "output_cost_usd": round(sum(float(call.get("output_cost_usd") or 0) for call in calls), 8),
        "total_cost_usd": round(sum(float(call.get("total_cost_usd") or 0) for call in calls), 8),
        "duration_seconds": round(sum(float(call.get("duration_seconds") or 0) for call in calls), 3),
        "raw_usage": {
            "cost_category": "detection",
            "detection_v8": audit,
            "ordinary_provider_call_count": sum(
                1 for call in calls if call.get("stage") in {"discovery", "membership"}
            ),
            "exceptional_conflict_call_count": sum(
                1 for call in calls if call.get("stage") == "conflict_resolver"
            ),
        },
    }
    return visual_map, registry, usage
