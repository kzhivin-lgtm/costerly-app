"""Bounded render evidence review for the autonomous ordinary Detection lab."""

from base64 import standard_b64encode
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import BytesIO
import json
import re

from PIL import Image

from agents import anthropic_adapter as adapter

RENDER_KIND = "presentation_render"
VIEW_IMAGE_LABEL = re.compile(r"^Object View (.+), PDF page (\d+)$")
PAGE_IMAGE_LABEL = re.compile(r"^PDF page (\d+) full-page context\.")
VIEW_ROW = re.compile(r"^([^|]+)\|P(\d+)\|K=([^|]+)\|")
CALLBACK_KEYS = {"max_stream_seconds", "on_stream_phase", "cancel_requested"}

RENDER_RULE = (
    "Review only the listed presentation renders and the fixed technical Views on their sheet. "
    "For each listed render, examine the render crop and compare it with all the supplied technical crops. "
    "First check the actual pixels of the proposed technical target. It must visibly be a fabrication "
    "drawing such as a line-drawn plan, section, elevation or technical perspective. A photograph, "
    "rendered detail or a set of rendered thumbnails cannot be the technical target even when labelled as a detail. "
    "A render can show only part of an object. Allow for different viewpoint, lighting and occlusion. "
    "Use attach only when a technical View visibly shows the same distinctive configuration of actual "
    "parts, for example a particular sequence of divisions, an asymmetric return or a distinctive opening "
    "in the same location. Briefly describe that common feature in visual_witness. A similar room, material, "
    "finish or generic furniture category cannot prove identity. The technical groups listed below "
    "were formed independently of render evidence. Matching multiple Views in the same technical group "
    "is consistent with one item: choose its clearest technical witness. Do not use group size, or group "
    "membership alone, as evidence. If two different fabricated items remain "
    "plausible or a part cannot be resolved, choose unresolved. Choose no_match when the available views "
    "provide no supported local match and describe the concrete discrepancy or missing comparable feature. "
    "Use exactly one row per listed render. Every disposition requires a short, nonempty visual_witness. "
    "For attach, use matching_topology or unique_geometry and the bare ID of one displayed technical crop. "
    "For no_match and unresolved, use an empty technical_group_id and evidence_type none. Return JSON only."
)


ROLE_CUE = re.compile(r"\b(?:render(?:ed|ing)?s?|photos?|photographs?|thumbnails?|perspectives?|visuali[sz]ations?)\b", re.IGNORECASE)
TECHNICAL_ROLES = ("line_drawing_plan", "line_drawing_elevation", "line_drawing_section", "technical_detail", "technical_isometric")
ROLE_REVIEW_RULE = (
    "Review only the visual representation of each fixed crop. A photographic image, shaded presentation "
    "render, or sheet of rendered thumbnails is presentation_render when it depicts fabricated parts. "
    "When the crop visibly consists of a technical drawing, identify it using the matching drawing role. "
    "Use retain_original for mixed or unclear crops. Preserve all crop boundaries. Give one decision "
    "per supplied ID, with a short nonempty witness describing the visible visual style. Return JSON only."
)


def render_role_candidates(payload):
    object_ids = {
        row["group_id"] for row in payload.get("classifications", [])
        if row["evidence_class"] == "object_evidence"
    }
    return [
        {**group, "evidence_class": "object_evidence", "bbox": group.get("core_bbox") or group["bbox"]}
        for group in payload.get("visual_groups", [])
        if group["group_id"] in object_ids
    ]


def render_role_candidate_crops(groups, crops):
    """Send possible role mismatches for visual confirmation."""
    presented = {group["group_id"] for group in groups if group["representation_kind"] == RENDER_KIND}
    described = {
        group["group_id"] for group in groups
        if ROLE_CUE.search(" ".join(group.get(key, "") for key in (
            "representation_kind", "visual_description", "location_hint",
        )).replace("_", " "))
    }
    described -= presented
    selected = []
    for crop in crops:
        group_id = crop["group_id"]
        if group_id in described:
            selected.append(crop)
            continue
        with Image.open(BytesIO(crop["bytes"])) as image:
            sample = image.convert("L")
            sample.thumbnail((96, 96), Image.Resampling.BOX)
        # Downsample fine ink lines. Shading is a trigger for review, never a role.
        shaded = 3 * sum(sample.histogram()[:210]) >= sample.width * sample.height
        if shaded != (group_id in presented):
            selected.append(crop)
    return selected


def review_render_roles(payload, request, crops, send):
    """Correct a confirmed render/drawing confusion without changing boxes."""
    if not crops:
        return None, {}
    blocks = []
    for crop in crops:
        blocks.extend((
            {"type": "text", "text": "Fixed View " + crop["group_id"]},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": standard_b64encode(crop["bytes"]).decode("ascii"),
            }},
        ))
    row = {
        "type": "object", "additionalProperties": False,
        "required": ["group_id", "role", "visual_witness"],
        "properties": {
            "group_id": {"type": "string"},
            "role": {"type": "string", "enum": [RENDER_KIND, *TECHNICAL_ROLES, "retain_original"]},
            "visual_witness": {"type": "string"},
        },
    }
    focused = {
        "model": request["model"], "max_tokens": min(request["max_tokens"], 2048),
        "system": [{"type": "text", "text": ROLE_REVIEW_RULE}],
        "messages": [{"role": "user", "content": blocks}],
        "output_config": {"format": {"type": "json_schema", "schema": {
            "type": "object", "additionalProperties": False, "required": ["decisions"],
            "properties": {"decisions": {"type": "array", "items": row}},
        }}},
    }
    response, metadata = send(focused)
    if response.stop_reason != "end_turn":
        return metadata, {}
    try:
        decisions = json.loads(adapter.extract_text_from_claude_response(response))["decisions"]
    except (ValueError, KeyError):
        return metadata, {}
    counts = Counter(decision["group_id"] for decision in decisions)
    shown = {crop["group_id"] for crop in crops}
    confirmed = {
        decision["group_id"]: decision
        for decision in decisions
        if decision["group_id"] in shown and counts[decision["group_id"]] == 1
        and decision["role"] in (RENDER_KIND, *TECHNICAL_ROLES) and decision["visual_witness"].strip()
    }
    corrected = {}
    for group in payload["visual_groups"]:
        decision = confirmed.get(group["group_id"])
        if decision and (decision["role"] == RENDER_KIND) != (group["representation_kind"] == RENDER_KIND):
            group["representation_kind"] = decision["role"]
            corrected[group["group_id"]] = decision["visual_witness"]
    return metadata, corrected


def validated_render_rows(rows, views, render_ids, reject_absent_proof):
    """Validate rows with the existing V7.11 contract, independently by render."""
    if not isinstance(rows, list):
        return {}
    counts = Counter(
        row.get("render_group_id") for row in rows
        if isinstance(row, dict) and isinstance(row.get("render_group_id"), str)
    )
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        render = row.get("render_group_id")
        if not isinstance(render, str) or render not in render_ids or counts[render] != 1:
            continue
        target = row.get("technical_group_id")
        group_ids = [render]
        if isinstance(target, str) and target in views and target != render and views[target][1] != RENDER_KIND:
            group_ids.append(target)
        groups = [
            {"group_id": key, "evidence_class": "object_evidence", "representation_kind": views[key][1]}
            for key in group_ids
        ]
        try:
            adapter.normalize_detection_v711_presentation_render_decisions(
                [row], visual_groups=groups, group_id_mapping={},
            )
        except ValueError:
            continue
        if row["disposition"] == "attach" and reject_absent_proof(row["visual_witness"]):
            continue
        result[render] = row
    return result


def render_request(request, views, page, targets, technical_components):
    """Use existing immutable crop blocks. A target cannot be selected off-sheet."""
    blocks = request["messages"][0]["content"]
    images = []
    visible_ids = set()
    for label, image in zip(blocks[:-1:2], blocks[1:-1:2], strict=True):
        if match := VIEW_IMAGE_LABEL.fullmatch(label["text"]):
            key = match[1]
            if key in views and views[key][0] == page and (key in targets or views[key][1] != RENDER_KIND):
                visible_ids.add(key)
                images.extend((label, image))
        elif (match := PAGE_IMAGE_LABEL.match(label["text"])) and int(match[1]) == page:
            images.extend((label, image))
    visible_targets = visible_ids & targets
    if not visible_targets or not visible_ids - targets:
        return None, set(), set()
    descriptions = [
        line.split("|SRC=",1)[0] for line in blocks[-1]["text"].splitlines()
        if (match := VIEW_ROW.match(line)) and match[1] in visible_ids
    ]
    visible_technical = visible_ids - targets
    groups = sorted(sorted(visible_technical.intersection(component)) for component in technical_components)
    confirmed = [" + ".join(group) for group in groups if len(group) > 1]
    handoff = (
        "Required presentation render IDs: " + ", ".join(sorted(visible_targets))
        + "\nFixed view descriptions for orientation:\n" + "\n".join(descriptions)
        + "\nPreviously grouped technical Views visible on this sheet:\n"
        + ("\n".join(confirmed) or "No multi-view group confirmed.")
    )
    narrowed = {key: value for key, value in request.items() if key not in CALLBACK_KEYS}
    narrowed["system"] = [{"type": "text", "text": RENDER_RULE}]
    narrowed["messages"] = [{"role": "user", "content": [*images, {"type": "text", "text": handoff}]}]
    original_schema = request["output_config"]["format"]["schema"]
    field = "presentation_render_decisions"
    narrowed["output_config"] = {
        "format": {"type": "json_schema", "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [field],
            "properties": {field: deepcopy(original_schema["properties"][field])},
        }},
    }
    return narrowed, visible_targets, visible_ids


def unresolved_render(render):
    return {
        "render_group_id": render,
        "disposition": "unresolved",
        "technical_group_id": "",
        "evidence_type": "none",
        "visual_witness": "No valid provider decision with a visible witness was returned.",
    }


def provisional_render_rows(views, primary_rows, reject_absent_proof):
    """Keep valid primary rows and give missing rows a fail-closed disposition."""
    all_ids = {key for key, (_, kind) in views.items() if kind == RENDER_KIND}
    accepted = validated_render_rows(primary_rows, views, all_ids, reject_absent_proof)
    return [accepted[key] if key in accepted else unresolved_render(key) for key in sorted(all_ids)]


def review_render_rows(request, views, primary_rows, send, reject_absent_proof, workers, technical_components):
    """Keep grounded primary positives and review other renders once locally."""
    all_ids = {key for key, (_, kind) in views.items() if kind == RENDER_KIND}
    accepted = validated_render_rows(primary_rows, views, all_ids, reject_absent_proof)
    pending = defaultdict(set)
    for render in sorted(all_ids):
        if render not in accepted or accepted[render]["disposition"] != "attach":
            pending[views[render][0]].add(render)

    def review(item):
        page, targets = item
        narrowed, visible_targets, visible_ids = render_request(request, views, page, targets, technical_components)
        if narrowed is None:
            return {}, None
        response, metadata = send(narrowed, page)
        metadata["pages"] = [page]
        if response.stop_reason != "end_turn":
            return {}, metadata
        try:
            payload = json.loads(adapter.extract_text_from_claude_response(response))
        except ValueError:
            return {}, metadata
        checked = validated_render_rows(
            payload.get("presentation_render_decisions"),
            {key: views[key] for key in visible_ids},
            visible_targets,
            reject_absent_proof,
        )
        return checked, metadata

    calls = []
    resolution = {
        render: "primary" for render, row in accepted.items() if row["disposition"] == "attach"
    }
    if pending:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(review, sorted(pending.items())))
        for rows, metadata in results:
            if metadata is not None:
                calls.append(metadata)
            for render, row in rows.items():
                accepted[render] = row
                resolution[render] = "focused_same_page"
    for render in sorted(all_ids):
        if render not in accepted:
            accepted[render] = unresolved_render(render)
            resolution[render] = "runtime_unresolved"
        else:
            resolution.setdefault(render, "primary")
    return [accepted[key] for key in sorted(all_ids)], calls, resolution
