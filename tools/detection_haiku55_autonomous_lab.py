"""Run the ordinary Haiku 5.5 experiment with fresh providers and no fixtures."""

from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from time import perf_counter
from unittest.mock import patch

from agents import anthropic_adapter as adapter
from agents.detection_agent import run_detection_agent
from agents.detection_document_classifier import classify_detection_document
from agents.detection_page_images import render_detection_pdf_pages
from agents.detection_source_capability import assess_detection_source_capability
from agents.ocr_rendering import run_mistral_document_evidence_ocr
from config import CLAUDE_HAIKU_MODEL

BATCH_SIZE = 3
ROLE_RULE = (
    "First decide whether the target is a fabricated item depiction, building context, or annotations alone. "
    "A whole floor, multiple rooms or suites, circulation with doors, architectural walls and room tags are building "
    "context and must return document_context even with construction dimensions, section marks or furniture outlines. "
    "A cluster or strip of dimensions, numbers, or labels without drawn fabricated parts also returns document_context. "
    "A real cabinet plan, small technical section, or detail showing physical parts can be object evidence even "
    "when small or dimensioned. A crop's boundary by itself cannot create a new depiction. "
    "Keep each visual_witness to one sentence of at most 150 characters.\n\n"
)
PRIMARY_RULE = """You review the membership of fixed Views in technical fabrication drawings. Find which Views show the same physical fabricated object.
Work through every page from start to finish. Compare every pair in the required same-page queue using identifier, topology, geometry, dimensions, and construction. Then check supported cross-page relations. Use the full page to locate every View and its individual crop to verify the fact. Return a complete set of supported multi-View object_hypotheses across the whole document. Continue after finding the first match.
A group must be supported by object-specific visual evidence. Use distinctive shared geometry or component layout that can be named and checked, or a direct author cross-reference. Different products can share materials, generic cabinet layouts, standard profiles, a room, a sheet, or a project title. Those alone are not evidence of identity. Preserve independent objects. Do not change the fixed View IDs, roles, or geometry.
Report each concrete supporting visual fact. If a view match has one specific visual fact, report it. The runtime independently corroborates proposed relationships with source dimensions and other evidence. Prefer two independent facts when visible. Never invent a second fact. For matching_topology, unique_geometry, and direct_shared_structure use strength standard. Cite only the bare source token before the equals sign. For visual details cite registry_view:<ID> for the supported Views. Cite at most three source IDs per fact. When the pixels independently show both a distinctive construction layout and distinctive measured geometry, give one matching_topology row and one unique_geometry row. A repeated dimension without visible correspondence is insufficient. The two observations must describe different concrete facts, and neither is mandatory when it is not visible. For each page, start with the first supported pair and continue checking every remaining View. Include every additional View supported by the same object-specific witness. Return complete non-overlapping groups, and finish the rest of the Views on that page after finding a pair. Keep distinct objects separate. A hypothesis may use several complementary facts only when each claim applies to every member it describes. Use direct_shared_structure only with a visible containing View or third fixed View showing the two parts physically joined, and provide the structural_witness fields.
Do not emit singleton hypotheses. For every K=presentation_render View, return exactly one row in presentation_render_decisions, even when the candidate technical View is on another page. Use attach only for one non-render View with exactly matching_topology or unique_geometry and a concrete configuration visible in both images. Use no_match when no such proof exists and unresolved only when pixels prevent comparison. For no_match or unresolved, set technical_group_id to an empty string and evidence_type to none. Render membership comes only from this decision list. Colour, finish, room context, proximity, material and approximate proportions are never proof. If no View is marked K=presentation_render, return an empty decision array. Return JSON only."""
PAIR_RULE = (
    "Review every fabrication sheet in order. The fixed Views and all required pairs are in the inventory. "
    "For each pair compare identifiers, topology, geometry, dimensions and construction. "
    "Record same-page object identity in same_page_witnesses, using one row per positively supported pair. "
    "Use exactly the two Q endpoints in view_ids. Describe the same distinctive arrangement of components in topology, "
    "and the same distinctive measured outline, return, openings or spans in geometry. Each must be visible in both Views. "
    "Use an empty string for any unavailable witness. At least one concrete witness is required to emit a pair. "
    "Choose the strongest witnesses and keep checking every page after the first match. "
    "Independent products may share a sheet, dimensions or material. Preserve them separately. "
    "Cite only bare source tokens before the equals sign or exact registry_view:<ID> tokens. "
    "Q labels enumerate comparisons and never serve as evidence. Keep all View IDs, roles and boxes fixed. "
    "Review only same-page evidence. Leave cross_page_hypotheses and presentation_render_decisions empty. "
    "Compare features across elevations, plans and sections with allowance for the difference in viewpoint. "
    "Find visually corresponding components even when the two crops show different overall silhouettes."
)
IMAGE_PAGE = re.compile(r"PDF page (\d+)\b")
VIEW_ROW = re.compile(r"^([^|]+)\|P(\d+)\|K=([^|]+)\|")
CONTEXT_ROW = re.compile(r"^P(\d+)\|")
QUEUE_ROW = re.compile(r"^Q\d+\|A=([^|]+)\|B=([^|]+)$")
DISPLAY_SOURCE = re.compile(r'\[(SF\d+)\] ("(?:[^"\\]|\\.)*")')
CALLBACK_KEYS = {"max_stream_seconds", "on_stream_phase", "cancel_requested"}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def request_hash(request):
    stable = {key: value for key, value in request.items() if key not in CALLBACK_KEYS}
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def kind_of(request):
    props = request.get("output_config", {}).get("format", {}).get("schema", {}).get("properties", {})
    if "object_hypotheses" in props:
        return "membership"
    if "decisions" in props and "independent visual conflict resolver" in str(request.get("system")):
        return "role"
    return "discovery"


def primary_request(request):
    prepared = deepcopy(request)
    blocks = prepared["messages"][0]["content"]
    image_pairs = list(zip(blocks[:-1:2], blocks[1:-1:2], strict=True))
    image_pairs.sort(key=lambda pair: int(IMAGE_PAGE.search(pair[0]["text"])[1]))
    inventory = DISPLAY_SOURCE.sub(r"\1=\2", blocks[-1]["text"])
    prepared["messages"][0]["content"] = [
        block for pair in image_pairs for block in pair
    ] + [{"type": "text", "text": inventory}]
    prompt = PRIMARY_RULE
    schema = prepared["output_config"]["format"]["schema"]
    if "conflict_pair_decisions" in schema["properties"]:
        marker = "V7.14 TARGETED CONFLICT-ADMISSION MEMBERSHIP MATRIX:"
        existing = "\n".join(block["text"] for block in request["system"])
        _, separator, remaining = existing.partition(marker)
        if not separator:
            raise ValueError("Conflict decision schema is missing its required matrix.")
        matrix, _, _ = remaining.partition("V7.11 PRESENTATION RENDER DECISIONS:")
        prompt += "\n\n" + marker + matrix.rstrip()
    prepared["system"] = [{"type": "text", "text": prompt}]
    return prepared


def inventory_of(request):
    blocks = request["messages"][0]["content"]
    views = {
        match[1]: (int(match[2]), match[3])
        for line in blocks[-1]["text"].splitlines() if (match := VIEW_ROW.match(line))
    }
    queue = {
        frozenset(match.groups())
        for line in blocks[-1]["text"].splitlines() if (match := QUEUE_ROW.fullmatch(line))
    }
    return views, queue


def batch_request(request, pages, views):
    prepared = deepcopy(request)
    blocks = prepared["messages"][0]["content"]
    lines = []
    for line in blocks[-1]["text"].splitlines():
        if (view := VIEW_ROW.match(line)) and int(view[2]) not in pages:
            continue
        if (context := CONTEXT_ROW.match(line)) and int(context[1]) not in pages:
            continue
        if (pair := QUEUE_ROW.fullmatch(line)) and not all(views[g][0] in pages for g in pair.groups()):
            continue
        lines.append(line)
    images = [
        block
        for label, image in zip(blocks[:-1:2], blocks[1:-1:2], strict=True)
        if int(IMAGE_PAGE.search(label["text"])[1]) in pages
        for block in (label, image)
    ]
    prepared["messages"][0]["content"] = [*images, {"type": "text", "text": "\n".join(lines)}]
    prepared["system"] = [{"type": "text", "text": PAIR_RULE}]
    schema = prepared["output_config"]["format"]["schema"]
    original = schema["properties"]
    id_list = {"type": "array", "items": {"type": "string"}}
    fields = {"view_ids": id_list, "topology": {"type": "string"},
              "geometry": {"type": "string"}, "source_fact_ids": id_list}
    schema["properties"] = {
        "same_page_witnesses": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": fields, "required": list(fields),
        }},
        "cross_page_hypotheses": original["object_hypotheses"],
        "presentation_render_decisions": original["presentation_render_decisions"],
    }
    schema["required"] = list(schema["properties"])
    for key in CALLBACK_KEYS:
        prepared.pop(key, None)
    return prepared


def candidate_hypotheses(payload, pages, views, queue):
    hypotheses = []
    for row in payload["same_page_witnesses"]:
        pair = [group if group in views else group.removeprefix("registry_view:")
                for group in row["view_ids"]]
        if len(pair) != 2 or frozenset(pair) not in queue:
            continue
        if any(views[group][0] not in pages or views[group][1] == "presentation_render" for group in pair):
            continue
        evidence = [
            {"evidence_type": kind, "strength": "standard", "observation": row[key],
             "source_fact_ids": row["source_fact_ids"]}
            for key, kind in (("topology", "matching_topology"), ("geometry", "unique_geometry"))
            if row[key].strip()
        ]
        if evidence:
            hypotheses.append({
                "group_ids": pair, "hypothesis_reason": " ".join(row["observation"] for row in evidence),
                "evidence": evidence,
            })
    return hypotheses


def audit(result):
    return next(event["raw_usage"] for event in result["_agent_usage_events"]
                if "proof_graph_components" in event["raw_usage"])


def partition(usage):
    labels = {v["visual_group_id"]: v["page_view_ref"] for v in usage["view_evidence_packages"]}
    return sorted(sorted(labels[g] for g in group["visual_group_ids"])
                  for group in usage["proof_graph_components"])


def run(pdf, output):
    started = perf_counter()
    output.mkdir(mode=0o700)
    pdf_bytes = pdf.read_bytes()
    ocr = run_mistral_document_evidence_ocr(file_name=pdf.name, file_bytes=pdf_bytes)
    write_json(output / "ocr.json", ocr)
    ocr_seconds = perf_counter() - started
    page_images, _ = render_detection_pdf_pages(pdf_bytes)
    capability = assess_detection_source_capability(
        source_facts=adapter.build_detection_page_evidence_inventory(ocr),
        page_count=len(page_images), page_dimensions=adapter._source_dimensions_by_page(ocr),
    )
    route = classify_detection_document(ocr_package=ocr, source_capability=capability)
    if route["category"] != "ordinary_object_set":
        raise ValueError(f"The lab requires the ordinary Detection route. Detected {route['category']}.")
    arguments = dict(file_name=pdf.name, file_bytes=pdf_bytes, ocr_package=ocr, page_images=page_images)
    original_transport = adapter.create_claude_message_streamed
    records, calls = [], []

    def send(client, request, stage, suffix):
        before = perf_counter()
        response, diagnostics = original_transport(client, **request)
        raw = adapter.extract_text_from_claude_response(response)
        metadata = dict(stage=stage, model=response.model, message_id=response.id,
                        stop_reason=response.stop_reason, input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens, seconds=round(perf_counter()-before, 3),
                        request_sha256=request_hash(request))
        write_json(output / f"{suffix}.json", {**metadata, "text": raw})
        return response, diagnostics, metadata

    def observe(client, **request):
        stage = kind_of(request)
        prepared = request
        model = adapter._claude_runtime_model(request.get("model"))
        if model == CLAUDE_HAIKU_MODEL and stage == "role":
            prepared = deepcopy(request)
            for block in prepared["system"]:
                block["text"] = block["text"].replace(
                    "For each supplied target crop, decide only",
                    ROLE_RULE + "For each supplied target crop, decide only", 1,
                )
        if model == CLAUDE_HAIKU_MODEL and stage == "membership":
            prepared = primary_request(request)
        response, diagnostics, metadata = send(client, prepared, stage, f"primary-{len(records)+1:02}")
        records.append((request_hash(request), stage, prepared, response, diagnostics))
        calls.append(metadata)
        return response, diagnostics

    print("Fresh OCR complete. Running Discovery and complete Membership.", flush=True)
    with patch.object(adapter, "create_claude_message_streamed", side_effect=observe):
        primary = run_detection_agent(**arguments)
    usage = audit(primary)
    if usage["detection_v6_12_document_category"]["category"] != route["category"]:
        raise ValueError("The runtime route changed after the lab admission check.")
    grouping = [row for row in records if row[1] == "membership"]
    if len(grouping) != 1 or grouping[0][3].model != CLAUDE_HAIKU_MODEL:
        raise ValueError("Expected one Haiku 5.5 primary Membership response.")
    original_request_hash, _, request, membership, _ = grouping[0]
    views, queue = inventory_of(request)
    primary_partition = partition(usage)
    pages_with_merge = {int(view.split(".")[0][1:]) for group in primary_partition
                        if len(group) > 1 for view in group}
    counts = Counter(page for page, role in views.values() if role != "presentation_render")
    missing = {page for page, count in counts.items() if count > 1} - pages_with_merge
    pages = sorted(counts)
    batches = [set(pages[offset:offset+BATCH_SIZE]) for offset in range(0, len(pages), BATCH_SIZE)]
    active = [batch for batch in batches if batch & missing]
    print(f"Primary returned {len(primary_partition)} groups. Revisiting {len(missing)} pages in {len(active)} batches.", flush=True)

    def supplement(index_batch):
        index, batch = index_batch
        prepared = batch_request(request, batch, views)
        client = adapter.get_anthropic_client()
        response, _, metadata = send(client, prepared, "same_page_supplement", f"supplement-{index:02}")
        metadata["pages"] = sorted(batch)
        if response.stop_reason != "end_turn":
            return [], metadata
        payload = json.loads(adapter.extract_text_from_claude_response(response))
        return candidate_hypotheses(payload, batch & missing, views, queue), metadata

    final = primary
    replacement_count = 0
    if active:
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            supplements = list(pool.map(supplement, enumerate(active, 1)))
        calls.extend(metadata for _, metadata in supplements)
        additional = [hypothesis for rows, _ in supplements for hypothesis in rows]
        replacement_count = len(additional)
        covered_pages = {views[hypothesis["group_ids"][0]][0] for hypothesis in additional}
        if covered_pages:
            combined = json.loads(adapter.extract_text_from_claude_response(membership))
            combined["object_hypotheses"] = [
                hypothesis for hypothesis in combined["object_hypotheses"]
                if not any(all(group in views and views[group][0] == page for group in hypothesis["group_ids"])
                           for page in covered_pages)
            ] + sorted(additional, key=lambda hypothesis: -len(hypothesis["evidence"]))
            write_json(output / "combined-membership.json", combined)
            original_text = next(block for block in membership.content if block.type == "text")
            derived = membership.model_copy(update={"content": [
                original_text.model_copy(update={"text": json.dumps(combined, ensure_ascii=False)})
            ]})
            # Only the same-run inputs are reused for compilation. This
            # phase has no external transport and cannot load earlier results.
            iterator = iter(records)
            def recompile_same_run(_client, **repeated_request):
                expected, _, _, response, diagnostics = next(iterator)
                actual = request_hash(repeated_request)
                if actual != expected:
                    raise ValueError("A request changed during same-run compilation.")
                return (derived if actual == original_request_hash else response), diagnostics
            with (
                patch.object(adapter, "create_claude_message_streamed", side_effect=recompile_same_run),
                patch.object(adapter, "create_claude_message", side_effect=AssertionError("Unexpected new provider request")),
            ):
                final = run_detection_agent(**arguments)
            if next(iterator, None) is not None:
                raise ValueError("Not all same-run responses were used during compilation.")

    final_usage = audit(final)
    final_groups = partition(final_usage)
    summary = {
        "source_file": pdf.name, "source_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "route": route["category"], "run_id": final["rfq_run"]["run_id"],
        "ocr_seconds": round(ocr_seconds, 3), "total_seconds": round(perf_counter()-started, 3),
        "calls": calls, "primary_groups": primary_partition, "revisited_pages": sorted(missing),
        "supplement_hypothesis_count": replacement_count, "final_groups": final_groups,
        "retained_view_count": len(final_usage["view_evidence_packages"]),
        "required_same_page_pairs": final_usage["dimension_graph_audit"]["v6_67_review_same_page_queue"]["required_same_page_pair_count"],
    }
    final.pop("_naming_annotated_pages", None)
    final.pop("_naming_source_crops", None)
    write_json(output / "result.json", final)
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.pdf, args.output)
