"""Opt-in shared V7 Analyze: Island Map and Understanding, no continuation."""
from pathlib import Path
import json

from agents import estimation_understanding_agent as existing
from agents.estimation_composition_analyze_agent import _page_manifest
from agents.estimation_visual_evidence import page_content
from use_cases.estimation_detection_context_v7 import digest

VERSION = "Estimation V7 Analyze V1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_analyze_v7.md"
CATALOG_PATH = PROMPT_PATH.with_name("estimation_item_types_v7.json")
CONTENT_ROLES = {"technical_drawing", "render", "component_detail", "room_layout",
                 "general_plan", "legend", "text_information", "undetermined"}


def prepare_content(*, inputs, page_bytes, detection_context):
    if {r["input_id"] for r in inputs} != {o["input_id"] for o in detection_context["objects"]}:
        raise ValueError("context/input mismatch")
    pages, _ = _page_manifest(inputs, page_bytes)
    views = [{"view_id": i["island_id"], "page_number": i["page_number"], "bbox": i["bbox"],
              "object_id": obj["object_id"], **({"coordinate_frame_pixels": i["coordinate_frame_pixels"]} if "coordinate_frame_pixels" in i else {})}
             for obj in detection_context["objects"] for i in obj["islands"]]
    content = []
    detailed_ids = []
    for page in pages:
        visual, _ = page_content(page_bytes=page["bytes"], storage_ref=page["storage_ref"],
            page_number=page["page_number"], payloads=[r["input_payload"] for r in inputs],
            views=views, detail_budget=64, include_single_detail=True)
        content.extend(visual)
        for block in visual:
            if block["type"] == "text":
                metadata = json.loads(block["text"])
                if "detail_of_existing_view" in metadata:
                    detailed_ids.append(metadata["detail_of_existing_view"]["view_id"])
    if sorted(detailed_ids) != sorted(v["view_id"] for v in views):
        raise ValueError("each owned island requires exactly one labelled crop")
    source_text = {x["block_ref"]: x for r in inputs for container in ("evidence", "document_context")
                   for kind in ("ocr_blocks", "ocr_literal_items")
                   for x in r["input_payload"].get(container, {}).get(kind, []) if x.get("block_ref")}
    context = dict(detection_context=detection_context, source_text=list(source_text.values()),
                   item_type_catalog=json.loads(CATALOG_PATH.read_text()))
    text = json.dumps(context, ensure_ascii=False)
    images = sum(b["type"] == "image" for b in content)
    if not pages or images > 64 or len(text) > 100000:
        raise ValueError("V7 evidence bounds exceeded; do not truncate")
    content.append(dict(type="text", text=text))
    return content


def validate_result(result, *, detection_context, inputs, island_observation_required=True):
    expected = {o["object_id"]: o for o in detection_context["objects"]}
    rows = {r["input_payload"]["object"]["object_id"]: r for r in inputs}
    codes = {t["code"] for t in json.loads(CATALOG_PATH.read_text())}
    if not isinstance(result, dict) or set(result) != {"objects"} or not isinstance(result["objects"], list):
        raise ValueError("V7 objects required")
    seen = set()
    for obj in result["objects"]:
        if set(obj) != {"object_id", "islands", "understanding"}:
            raise ValueError("invalid V7 object fields")
        oid = obj["object_id"]
        if oid not in expected or oid in seen:
            raise ValueError("foreign/duplicate V7 object")
        seen.add(oid)
        owned = {i["island_id"] for i in expected[oid]["islands"]}
        known_refs = {f["observation_id"] for f in expected[oid]["accepted_observations"]}
        known_refs.update(m["occurrence_id"] for group in expected[oid].get("dimension_inventory", [])
                          for m in group.get("occurrences", []))
        known_refs.update(x["block_ref"] for container in ("evidence", "document_context")
                          for kind in ("ocr_blocks", "ocr_literal_items")
                          for x in rows[oid]["input_payload"].get(container, {}).get(kind, []) if x.get("block_ref"))
        mapped = set()
        island_fields = {"island_id", "projection", "content_role"}
        if island_observation_required:
            island_fields.add("observation")
        for island in obj["islands"]:
            if set(island) != island_fields:
                raise ValueError("invalid Island Map fields")
            iid = island["island_id"]
            if iid not in owned or iid in mapped:
                raise ValueError("foreign/duplicate island")
            mapped.add(iid)
            if island["projection"] not in existing.ISLAND_TYPES or island["content_role"] not in CONTENT_ROLES:
                raise ValueError("invalid Island Map classification")
            if island_observation_required:
                _text(island["observation"])
        if mapped != owned:
            raise ValueError("omitted island")
        u = obj["understanding"]
        if set(u) != {"name", "type_code", "proposed_type", "description", "characteristics", "materials", "assumptions", "conflicts"}:
            raise ValueError("invalid Understanding fields")
        _text(u["name"])
        if len(u["name"].split()) > 3:
            raise ValueError("item name exceeds three words")
        if u["type_code"] is None:
            _text(u["proposed_type"])
            if len(u["proposed_type"].split()) > 3:
                raise ValueError("proposed type exceeds three words")
        elif u["type_code"] not in codes or u["proposed_type"] is not None:
            raise ValueError("invalid item type")
        _text(u["description"])
        for field in ("characteristics", "materials", "assumptions", "conflicts"):
            if not isinstance(u[field], list):
                raise ValueError("Understanding lists required")
        for field in ("assumptions", "conflicts"):
            for value in u[field]:
                _text(value)
        if not u["characteristics"] or not u["materials"]:
            raise ValueError("characteristics/materials required")
        for item in u["characteristics"] + u["materials"]:
            if not isinstance(item.get("island_ids"), list) or not item["island_ids"] or not set(item["island_ids"]) <= owned:
                raise ValueError("foreign/missing Understanding island refs")
            if not isinstance(item.get("source_refs"), list) or not set(item["source_refs"]) <= known_refs:
                raise ValueError("foreign Understanding source refs")
            if item.get("basis") not in {"specified", "inferred", "default"}:
                raise ValueError("invalid evidence basis")
        for item in u["characteristics"]:
            if set(item) != {"statement", "basis", "island_ids", "source_refs"}:
                raise ValueError("invalid characteristic fields")
            _text(item["statement"])
        for item in u["materials"]:
            if set(item) != {"part", "material", "finish", "thickness_mm", "basis", "island_ids", "source_refs", "reason"}:
                raise ValueError("invalid material fields")
            for key in ("part", "material", "finish", "reason"):
                _text(item[key])
            value = item["thickness_mm"]
            if value is not None and (type(value) not in (int, float) or not 0 < value <= 1000):
                raise ValueError("invalid material thickness")
    if seen != set(expected):
        raise ValueError("omitted object")
    return result


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2500:
        raise ValueError("bounded nonempty text required")


def run_analyze(*, inputs, page_bytes, detection_context, record):
    content = prepare_content(inputs=inputs, page_bytes=page_bytes, detection_context=detection_context)
    request = dict(model=existing.MODEL, max_tokens=12000, output_config={"effort": "low"},
        thinking={"type": "disabled"}, system=PROMPT_PATH.read_text().strip(),
        messages=[dict(role="user", content=content)])
    record("request", request, None)
    response = existing._create_message_with_hard_timeout(
        existing.get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
    record("response", request, response)
    if getattr(response, "stop_reason", None) != "end_turn":
        raise ValueError("Analyze V7 response incomplete")
    text = existing.extract_text_from_claude_response(response)
    return validate_result(existing._json_object(text), detection_context=detection_context, inputs=inputs)
