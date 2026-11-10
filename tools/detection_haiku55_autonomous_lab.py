"""Run the ordinary Haiku 5.5 experiment with fresh providers and no fixtures."""

from argparse import ArgumentParser
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
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
DISCOVERY_ROLE_RULE = (
    "When classifying fixed drawing regions, require a visible depiction of a physical fabricated part for "
    "object_evidence. A row of dimension text, arrows, ticks, or leaders without a drawn part outline "
    "is document_context, even next to an elevation. Keep dimension evidence with its relevant drawing. "
    "A thin profile is object_evidence when its physical outline is visible.\n\n"
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
LOCAL_RULE = (
    "\nFor this sheet, prioritize each View marked for another look in the handoff. Compare it with every "
    "other technical View on its page. First locate concrete shared construction in both crops, allowing "
    "for different projection directions. Look for the same distinctive feature sequence, a matching "
    "cut or return, or a measured outline that corresponds to the same physical part. A standalone View "
    "can depict an independent object. Keep it separate when the visual link is uncertain. Return only "
    "positively evidenced pairs involving at least one marked View."
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


def dimensional_review_context(usage, canonical_ids, views, queue, page, marked):
    """Supply same-run OCR corroboration without proposing identity."""
    raw_ids = {canonical: raw for raw, canonical in canonical_ids.items() if raw in views}
    ranked = defaultdict(list)
    for row in usage["dimension_graph_audit"]["dimension_similarity_candidates"]:
        if row["page_a"] != page or row["page_b"] != page:
            continue
        left, right = (raw_ids.get(canonical) for canonical in edge_endpoints(row))
        pair = frozenset((left, right))
        if pair not in queue or not pair.intersection(marked):
            continue
        features = sorted(row["features"], key=lambda feature: -feature["points"])
        if not features:
            continue
        spans = ", ".join(
            feature["left_mm"] if feature["left_mm"] == feature["right_mm"]
            else f"{feature['left_mm']} vs {feature['right_mm']}"
            for feature in features[:4]
        )
        item = (float(row["dimension_similarity_score"]), left, right, spans)
        for view_id in pair.intersection(marked):
            ranked[view_id].append(item)
    selected = {item for candidates in ranked.values() for item in sorted(candidates, reverse=True)[:2]}
    return "\n".join(f"{left} and {right}: {spans} mm" for _, left, right, spans in sorted(selected, reverse=True))


def edge_endpoints(edge):
    return edge["group_id_a"], edge["group_id_b"]


def unambiguous_recovery_edges(edges, components):
    """Allow direct additions around one anchor while preserving existing groups."""
    roots = {member: members[0] for members in components for member in members}
    protected = {members[0] for members in components if len(members) > 1}
    projected = []
    originals = []
    for edge in edges:
        a, b = edge_endpoints(edge)
        left, right = roots[a], roots[b]
        if left == right:
            continue
        projected.append({"group_id_a": left, "group_id_b": right, "relationship": "same_object_view"})
        originals.append(edge)
    clusters = adapter.derive_detection_proof_components(
        projected, visual_group_ids={v for edge in projected for v in edge_endpoints(edge)},
    )
    accepted = []
    for cluster in clusters:
        members = set(cluster)
        rows = [(original, set(edge_endpoints(edge))) for original, edge in zip(originals, projected, strict=True)
                if set(edge_endpoints(edge)) <= members]
        if rows and len(members & protected) <= 1 and set.intersection(*(endpoints for _, endpoints in rows)):
            accepted.extend(original for original, _ in rows)
    return accepted


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
    original_normalize = adapter.normalize_detection_visual_map_group_ids
    original_semantics = adapter.compile_detection_v5_semantic_facts
    original_merge = adapter.compile_detection_v5_merge_edges
    records, calls = [], []
    canonical_ids = {}

    def capture_ids(visual_map):
        raw_ids = [group["group_id"] for group in visual_map["visual_groups"]]
        normalized = original_normalize(visual_map)
        canonical_ids.update(zip(raw_ids, (group["group_id"] for group in normalized["visual_groups"]), strict=True))
        return normalized

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
        if model == CLAUDE_HAIKU_MODEL and stage == "discovery":
            props = request["output_config"]["format"]["schema"]["properties"]
            if {"visual_groups", "classifications"} <= set(props):
                prepared = deepcopy(request)
                prepared["system"][-1]["text"] = DISCOVERY_ROLE_RULE + prepared["system"][-1]["text"]
        response, diagnostics, metadata = send(client, prepared, stage, f"primary-{len(records)+1:02}")
        records.append((request_hash(request), stage, prepared, response, diagnostics))
        calls.append(metadata)
        return response, diagnostics

    print("Fresh OCR complete. Running Discovery and complete Membership.", flush=True)
    with (
        patch.object(adapter, "create_claude_message_streamed", side_effect=observe),
        patch.object(adapter, "normalize_detection_visual_map_group_ids", side_effect=capture_ids),
    ):
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

    original_text = next(block for block in membership.content if block.type == "text")
    payload = json.loads(original_text.text)

    def recompile(payload, overrides=None):
        derived = membership.model_copy(update={"content": [
            original_text.model_copy(update={"text": json.dumps(payload, ensure_ascii=False)})
        ]})
        # Reuse only provider replies from this invocation. A changed request
        # fails the compilation instead of consuming any older response.
        iterator = iter(records)
        def same_run_transport(_client, **repeated_request):
            expected, _, _, response, diagnostics = next(iterator)
            actual = request_hash(repeated_request)
            if actual != expected:
                raise ValueError("A request changed during same-run compilation.")
            return (derived if actual == original_request_hash else response), diagnostics
        with ExitStack() as stack:
            stack.enter_context(patch.object(adapter, "create_claude_message_streamed", side_effect=same_run_transport))
            stack.enter_context(patch.object(adapter, "create_claude_message", side_effect=AssertionError("Unexpected new provider request")))
            for name, action in (overrides or {}).items():
                stack.enter_context(patch.object(adapter, name, side_effect=action))
            result = run_detection_agent(**arguments)
        if next(iterator, None) is not None:
            raise ValueError("Not all same-run responses were used during compilation.")
        return result

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
            payload["object_hypotheses"] = [
                hypothesis for hypothesis in payload["object_hypotheses"]
                if not any(all(group in views and views[group][0] == page for group in hypothesis["group_ids"])
                           for page in covered_pages)
            ] + sorted(additional, key=lambda hypothesis: -len(hypothesis["evidence"]))
            write_json(output / "combined-membership.json", payload)
            final = recompile(payload)

    intermediate_usage = audit(final)
    components = [row["visual_group_ids"] for row in intermediate_usage["proof_graph_components"]]
    singleton_ids = {row[0] for row in components if len(row) == 1}
    unresolved = defaultdict(set)
    for view_id, (page, role) in views.items():
        if counts[page] > 1 and role != "presentation_render" and canonical_ids.get(view_id) in singleton_ids:
            unresolved[page].add(view_id)
    accepted_recovery = []

    def local_review(item):
        page, marked = item
        prepared = batch_request(request, {page}, views)
        prepared["system"][0]["text"] += LOCAL_RULE
        prepared["messages"][0]["content"][-1]["text"] += (
            "\nViews marked for another look: " + ", ".join(sorted(marked))
        )
        dimension_context = dimensional_review_context(intermediate_usage, canonical_ids, views, queue, page, marked)
        if dimension_context:
            prepared["messages"][0]["content"][-1]["text"] += (
                "\nSame-page OCR dimension comparisons, normalized to millimeters. "
                "Check which feature the dimension spans in each crop. Matching numbers alone do not establish identity.\n"
                + dimension_context
            )
        client = adapter.get_anthropic_client()
        response, _, metadata = send(client, prepared, "local_membership_recovery", f"local-{page:02}")
        metadata["pages"] = [page]
        if response.stop_reason != "end_turn":
            return [], metadata
        data = json.loads(adapter.extract_text_from_claude_response(response))
        hypotheses = candidate_hypotheses(data, {page}, views, queue)
        return [h for h in hypotheses if marked.intersection(h["group_ids"])], metadata

    if unresolved:
        print(f"Running local proof review on {len(unresolved)} sheets with unresolved Views.", flush=True)
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            local = list(pool.map(local_review, sorted(unresolved.items())))
        calls.extend(metadata for _, metadata in local)
        facts = []
        for rows, _ in local:
            for hypothesis in rows:
                left, right = sorted(canonical_ids[group] for group in hypothesis["group_ids"])
                facts.extend({"group_id_a": left, "group_id_b": right, **fact} for fact in hypothesis["evidence"])

        if facts:
            validated = []

            def validate_local(facts_from_primary, **kwargs):
                base, ledger = original_semantics(facts_from_primary, **kwargs)
                accepted, local_audit = original_semantics(facts, **kwargs)
                validated[:] = accepted
                ledger["local_membership_recovery"] = local_audit
                return base, ledger

            def merge_local(dimension_edges, semantics, **kwargs):
                base, ledger = original_merge(dimension_edges, semantics, **kwargs)
                pairs = {edge_endpoints(fact) for fact in validated}
                local_dimensions = [edge for edge in dimension_edges if edge_endpoints(edge) in pairs]
                local_options = {**kwargs, "allow_batch_confirmation": False}
                local_graph, _ = original_merge(local_dimensions, validated, **local_options)
                accepted_recovery[:] = unambiguous_recovery_edges(
                    [edge for edge in local_graph if edge["relationship"] == "same_object_view"],
                    components,
                )
                recovered_pairs = {edge_endpoints(edge) for edge in accepted_recovery}
                ledger["local_membership_recovery"] = accepted_recovery
                return [edge for edge in base if edge_endpoints(edge) not in recovered_pairs] + accepted_recovery, ledger

            final = recompile(payload, {
                "compile_detection_v5_semantic_facts": validate_local,
                "compile_detection_v5_merge_edges": merge_local,
            })

    final_usage = audit(final)
    final_groups = partition(final_usage)
    summary = {
        "source_file": pdf.name, "source_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "route": route["category"], "run_id": final["rfq_run"]["run_id"],
        "ocr_seconds": round(ocr_seconds, 3), "total_seconds": round(perf_counter()-started, 3),
        "calls": calls, "primary_groups": primary_partition, "revisited_pages": sorted(missing),
        "supplement_hypothesis_count": replacement_count, "final_groups": final_groups,
        "local_review_pages": sorted(unresolved), "local_proven_edges": [edge_endpoints(edge) for edge in accepted_recovery],
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
