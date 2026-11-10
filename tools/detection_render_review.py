"""Bounded render evidence review for the autonomous ordinary Detection lab."""

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import re

from agents import anthropic_adapter as adapter

RENDER_KIND = "presentation_render"
VIEW_IMAGE_LABEL = re.compile(r"^Object View (.+), PDF page (\d+)$")
PAGE_IMAGE_LABEL = re.compile(r"^PDF page (\d+) full-page context\.")
VIEW_ROW = re.compile(r"^([^|]+)\|P(\d+)\|K=([^|]+)\|")
CALLBACK_KEYS = {"max_stream_seconds", "on_stream_phase", "cancel_requested"}

RENDER_RULE = (
    "Review only the listed presentation renders and the fixed technical Views on their sheet. "
    "For each listed render, examine the render crop and compare it with all the supplied technical crops. "
    "A render can show only part of an object. Allow for different viewpoint, lighting and occlusion. "
    "Use attach only when one technical View visibly shows the same distinctive configuration of actual "
    "parts, for example a particular sequence of divisions, an asymmetric return or a distinctive opening "
    "in the same location. Briefly describe that common feature in visual_witness. A similar room, material, "
    "finish or generic furniture category cannot prove identity. If two different fabricated items remain "
    "plausible or a part cannot be resolved, choose unresolved. Choose no_match when the available views "
    "provide no supported local match and describe the concrete discrepancy or missing comparable feature. "
    "Use exactly one row per listed render. Every disposition requires a short, nonempty visual_witness. "
    "For attach, use matching_topology or unique_geometry and the bare ID of one displayed technical crop. "
    "For no_match and unresolved, use an empty technical_group_id and evidence_type none. Return JSON only."
)


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


def render_request(request, views, page, targets):
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
    handoff = (
        "Required presentation render IDs: " + ", ".join(sorted(visible_targets))
        + "\nFixed view descriptions for orientation:\n" + "\n".join(descriptions)
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


def review_render_rows(request, views, primary_rows, send, reject_absent_proof, workers):
    """Keep grounded primary positives and review other renders once locally."""
    all_ids = {key for key, (_, kind) in views.items() if kind == RENDER_KIND}
    accepted = validated_render_rows(primary_rows, views, all_ids, reject_absent_proof)
    pending = defaultdict(set)
    for render in sorted(all_ids):
        if render not in accepted or accepted[render]["disposition"] != "attach":
            pending[views[render][0]].add(render)

    def review(item):
        page, targets = item
        narrowed, visible_targets, visible_ids = render_request(request, views, page, targets)
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
                if row["disposition"] == "attach" or render not in accepted:
                    accepted[render] = row
                    resolution[render] = "focused_same_page"
    for render in sorted(all_ids):
        if render not in accepted:
            accepted[render] = {
                "render_group_id": render,
                "disposition": "unresolved",
                "technical_group_id": "",
                "evidence_type": "none",
                "visual_witness": "Render review did not return a valid decision with a visible witness.",
            }
            resolution[render] = "runtime_unresolved"
        else:
            resolution.setdefault(render, "primary")
    return [accepted[key] for key in sorted(all_ids)], calls, resolution
