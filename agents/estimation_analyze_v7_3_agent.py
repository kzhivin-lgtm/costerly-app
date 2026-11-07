"""Opt-in economical V7.3 Analyze; source provenance and totals are code-owned."""
from copy import deepcopy
import json

from agents import estimation_analyze_v7_2_agent as previous

VERSION = "Estimation V7.3"
PROMPT_PATH = previous.FOLDER / "estimation_analyze_v7_3.md"


def prompt():
    template = json.loads((previous.FOLDER / "estimation_analyze_v7_2_output.json").read_text())
    del template["objects"][0]["front"]["totals"]
    return PROMPT_PATH.read_text().strip() + "\n\nRESPONSE TEMPLATE\n" + json.dumps(template, ensure_ascii=False)


def derive_totals(groups):
    mapping = dict(drawers="drawer", hinged_doors="hinged", lift_up_fronts="lift_up", unresolved_fronts="unresolved")
    if not isinstance(groups, list):
        raise ValueError("front groups must be a list")
    for group in groups:
        if not isinstance(group, dict) or group.get("type") not in mapping.values() or "count" not in group:
            raise ValueError("invalid front group type")
        count = group.get("count")
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError("invalid front group count")
    totals = {}
    for field, kind in mapping.items():
        counts = [g["count"] for g in groups if g["type"] == kind]
        totals[field] = None if None in counts else sum(counts)
    totals["total_fronts"] = None if None in totals.values() else sum(totals.values())
    return totals


def validate_result(raw, *, detection_context, inputs):
    if not isinstance(raw, dict) or set(raw) != {"objects"} or not isinstance(raw["objects"], list):
        raise ValueError("V7.3 objects required")
    result = deepcopy(raw)
    for obj in result["objects"]:
        front = obj["front"]
        if not isinstance(front, dict) or "totals" in front:
            raise ValueError("V7.3 totals are code-owned")
        front["totals"] = derive_totals(front.get("front_groups"))
    return previous.validate_result(result, detection_context=detection_context, inputs=inputs)


def island_normalization(context):
    """Display saved values and unit provenance; never parse/re-infer source numbers."""
    rows = []
    for obj in context["objects"]:
        for island in obj["dimension_inventory"]:
            readings = []
            for measurement in island.get("occurrences", []):
                unit = measurement.get("unit_basis")
                readings.append(dict(occurrence_id=measurement["occurrence_id"],
                    original_text=measurement["original_text"], source_unit=unit,
                    value_mm=measurement["value_mm"], target_unit="mm",
                    conversion_required=False if unit == "mm" else True if unit in {"cm", "m", "in", "inch", "ft"} else None,
                    source_refs=deepcopy(measurement.get("source_refs", []))))
            rows.append(dict(object_id=obj["object_id"], island_id=island["group_id"],
                readings=readings, unit_context=deepcopy(context["unit_context"])))
    return rows


def run_analyze(*, inputs, page_bytes, detection_context, record):
    if detection_context.get("contract_version") != "estimation_detection_context_v7_2":
        raise ValueError("V7.3 requires saved normalized Detection measurements")
    content = previous.previous.prepare_content(inputs=inputs, page_bytes=page_bytes, detection_context=detection_context)
    request = dict(model=previous.existing.MODEL, max_tokens=14000,
        output_config={"effort": "low"}, thinking={"type": "disabled"},
        system=prompt(), messages=[dict(role="user", content=content)])
    record("request", request, None)
    response = previous.existing._create_message_with_hard_timeout(
        previous.existing.get_anthropic_client().with_options(timeout=120, max_retries=0),
        timeout_seconds=120, **request)
    record("response", request, response)
    if getattr(response, "stop_reason", None) != "end_turn":
        raise ValueError("V7.3 Analyze response incomplete")
    raw = previous.existing._json_object(previous.existing.extract_text_from_claude_response(response))
    return validate_result(raw, detection_context=detection_context, inputs=inputs)


hardware_preview = previous.hardware_preview
