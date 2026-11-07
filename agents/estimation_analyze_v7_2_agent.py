"""One document-level V7.2 Analyze, reusing Front/Planner policies and gates."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from agents import estimation_analyze_v7_agent as previous
from agents import estimation_understanding_agent as existing

VERSION = "Estimation V7.2"
FOLDER = previous.PROMPT_PATH.parent
PROMPT_PATH = FOLDER / "estimation_analyze_v7_2.md"


def prompt():
    front = (FOLDER / "cb_front_v3.md").read_text()
    front = front[front.index("TASK 2:"):front.index("TASK 5:")].strip()
    planner = (FOLDER / "cb_planner_v7.md").read_text()
    planner = planner[:planner.index("Return English JSON only")].strip()
    planner = planner.replace("Use the supplied CB Front result", "Use the Front section of this same response")
    template = (FOLDER / "estimation_analyze_v7_2_output.json").read_text().strip()
    return "\n\n".join([PROMPT_PATH.read_text().strip(),
        "EXISTING CB FRONT POLICY (FRONT SECTION ONLY)\n" + front,
        "EXISTING CB PLANNER POLICY (PLANNER SECTION ONLY)\n" + planner,
        "SINGLE AUTHORITATIVE RESPONSE TEMPLATE\n" + template])


def validate_result(result, *, detection_context, inputs, island_observation_required=True,
                    allow_unlocalized_fronts=False):
    if detection_context.get("contract_version") != "estimation_detection_context_v7_2":
        raise ValueError("V7.2 requires normalized Detection measurements")
    if not isinstance(result, dict) or set(result) != {"objects"} or not isinstance(result["objects"], list):
        raise ValueError("V7.2 objects required")
    context = {o["object_id"]: o for o in detection_context["objects"]}
    projected = deepcopy(result)
    island_fields = {"island_id", "projection", "elevation_index", "content_role"}
    if island_observation_required:
        island_fields.add("observation")
    for obj, basic in zip(result["objects"], projected["objects"]):
        if not isinstance(obj, dict) or set(obj) != {"object_id", "islands", "understanding", "front", "planner"}:
            raise ValueError("invalid V7.2 object fields")
        oid = obj["object_id"]
        if oid not in context:
            raise ValueError("foreign V7.2 object")
        if not isinstance(obj["islands"], list):
            raise ValueError("V7.2 islands required")
        fronts = []
        for island, basic_island in zip(obj["islands"], basic["islands"]):
            if not isinstance(island, dict) or set(island) != island_fields:
                raise ValueError("invalid V7.2 island fields")
            index = island["elevation_index"]
            if island["projection"] == "Front elevation":
                if type(index) is not int or index <= 0:
                    raise ValueError("front elevation needs a positive index")
                fronts.append(index)
            elif index is not None:
                raise ValueError("only front elevations have an elevation_index")
            basic_island.pop("elevation_index")
        if fronts != list(range(1, len(fronts) + 1)):
            raise ValueError("front elevations must be numbered in island order")
        measurements = {m["occurrence_id"]: m for row in context[oid]["dimension_inventory"]
                        for m in row.get("occurrences", [])}
        for material, basic_material in zip(obj["understanding"]["materials"], basic["understanding"]["materials"]):
            if "material_kind" not in material or "thickness_measurement_id" not in material:
                raise ValueError("material kind and thickness provenance required")
            kind = material["material_kind"]
            if kind not in {"sheet", "glass", "stone", "metal_profile", "other"}:
                raise ValueError("invalid material kind")
            if kind == "sheet" and material["thickness_mm"] is None:
                raise ValueError("sheet material requires a thickness")
            mid = material["thickness_measurement_id"]
            if mid is not None:
                if mid not in measurements or material["thickness_mm"] is None:
                    raise ValueError("foreign/missing thickness measurement")
                if Decimal(str(material["thickness_mm"])) != Decimal(str(measurements[mid]["value_mm"])):
                    raise ValueError("thickness differs from normalized Detection value")
                if not any(m["occurrence_id"] == mid for group in context[oid]["dimension_inventory"]
                           if group["group_id"] in material["island_ids"] for m in group.get("occurrences", [])):
                    raise ValueError("thickness measurement outside material islands")
            basic_material.pop("material_kind")
            basic_material.pop("thickness_measurement_id")
        known = {i["island_id"] for i in context[oid]["islands"]}
        f = obj["front"]
        if not isinstance(f, dict) or set(f) != {"front_groups", "excluded_surfaces", "tabletop_supports", "totals"}:
            raise ValueError("invalid V7.2 Front fields")
        front_contract = {**f, "island_types": [dict(view_id=i["island_id"], type=i["projection"]) for i in obj["islands"]]}
        existing.validate_front_count(front_contract, known, require_annotations=True, require_supports=True,
                                      allow_unlocalized_fronts=allow_unlocalized_fronts)
        front_ids = existing.planner_front_ids(f, known)
        existing.validate_assembly_plan(obj["planner"], known, front_ids)
        basic.pop("front")
        basic.pop("planner")
    previous.validate_result(projected, detection_context=detection_context, inputs=inputs,
                             island_observation_required=island_observation_required)
    return result


def hardware_preview(result):
    """Existing one-kit-per-front policy, not a BOM or provider assertion."""
    return {o["object_id"]: dict(drawer_slide_sets=o["front"]["totals"]["drawers"],
                                lift_system_sets=o["front"]["totals"]["lift_up_fronts"],
                                basis="one set per drawer / lift-up front; not individual rail/strut counts")
            for o in result["objects"]}


def run_analyze(*, inputs, page_bytes, detection_context, record):
    if detection_context.get("contract_version") != "estimation_detection_context_v7_2":
        raise ValueError("V7.2 normalized measurement context required before provider")
    content = previous.prepare_content(inputs=inputs, page_bytes=page_bytes, detection_context=detection_context)
    system = prompt()
    request = dict(model=existing.MODEL, max_tokens=14000, output_config={"effort": "low"},
        thinking={"type": "disabled"}, system=system, messages=[dict(role="user", content=content)])
    record("request", request, None)
    response = existing._create_message_with_hard_timeout(
        existing.get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
    record("response", request, response)
    if getattr(response, "stop_reason", None) != "end_turn":
        raise ValueError("V7.2 Analyze response incomplete")
    result = existing._json_object(existing.extract_text_from_claude_response(response))
    return validate_result(result, detection_context=detection_context, inputs=inputs)
