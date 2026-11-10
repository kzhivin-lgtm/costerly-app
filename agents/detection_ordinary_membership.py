"""Run the verified ordinary Haiku membership recovery inside a single RFQ."""

from base64 import standard_b64encode
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import re
from threading import Lock

import pymupdf

from agents import anthropic_adapter as adapter
from agents.detection_dimension_anchors import dimension_anchors
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
LOCAL_RULE = (
    "\nFor this sheet, prioritize each View marked for another look in the handoff. Compare it with every "
    "other technical View on its page. First locate concrete shared construction in both crops, allowing "
    "for different projection directions. Look for the same distinctive feature sequence, a matching "
    "cut or return, or a measured outline that corresponds to the same physical part. A standalone View "
    "can depict an independent object. Keep it separate when the visual link is uncertain. Return only "
    "positively evidenced pairs involving at least one marked View. Cite the two registry_view source "
    "IDs for the inspected crops. Compare matching object-specific features and their position in each crop. "
    "An author section mark can corroborate a match if it points to that same drawn feature. "
    "Do not describe unavailable evidence in topology or geometry. Leave that field empty."
)
ABSENT_PROOF = re.compile(
    r"\b(?:no|without)\s+(?:visible\s+)?(?:matching|shared|common|corresponding)\b"
    r"|\b(?:no|insufficient)\s+(?:positive\s+)?evidence\b"
    r"|\b(?:cannot|can't|does not|do not)\s+(?:visually\s+)?(?:establish|confirm|prove|verify)\b",
    re.IGNORECASE,
)
VIEW_IMAGE_LABEL = re.compile(r"^Object View (.+), PDF page (\d+)$")
IMAGE_PAGE = re.compile(r"PDF page (\d+)\b")
VIEW_ROW = re.compile(r"^([^|]+)\|P(\d+)\|K=([^|]+)\|")
CONTEXT_ROW = re.compile(r"^P(\d+)\|")
QUEUE_ROW = re.compile(r"^Q\d+\|A=([^|]+)\|B=([^|]+)$")
DISPLAY_SOURCE = re.compile(r'\[(SF\d+)\] ("(?:[^"\\]|\\.)*")')
CALLBACK_KEYS = {"max_stream_seconds", "on_stream_phase", "cancel_requested"}


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
        if views[pair[0]][0] != views[pair[1]][0]:
            continue
        evidence = [
            {"evidence_type": kind, "strength": "standard", "observation": row[key],
             "source_fact_ids": row["source_fact_ids"]}
            for key, kind in (("topology", "matching_topology"), ("geometry", "unique_geometry"))
            if row[key].strip() and not ABSENT_PROOF.search(row[key])
        ]
        if evidence:
            hypotheses.append({
                "group_ids": pair, "hypothesis_reason": " ".join(row["observation"] for row in evidence),
                "evidence": evidence,
            })
    return hypotheses


def improve_local_crops(request, pdf_bytes, ocr, usage, page_number):
    """Render the same fixed crop boxes at a higher local review resolution."""
    frame = next(page["dimensions"] for page in ocr["pages"] if page["page_number"] == page_number)
    audit_by_id = {
        row["group_id"]: row["source_bbox"] for row in usage["v5_9_review_crop_audit"]
        if row.get("page_number") == page_number and row.get("source_bbox")
    }
    blocks = request["messages"][0]["content"]
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        page = document[page_number - 1]
        for label, image in zip(blocks[:-1:2], blocks[1:-1:2], strict=True):
            match = VIEW_IMAGE_LABEL.fullmatch(label["text"])
            if not match or match[1] not in audit_by_id:
                continue
            box = audit_by_id[match[1]]
            clip = pymupdf.Rect(
                box["top_left_x"] / frame["width"] * page.rect.width,
                box["top_left_y"] / frame["height"] * page.rect.height,
                box["bottom_right_x"] / frame["width"] * page.rect.width,
                box["bottom_right_y"] / frame["height"] * page.rect.height,
            )
            margin_x, margin_y = clip.width * 0.04, clip.height * 0.04
            clip = (clip + (-margin_x, -margin_y, margin_x, margin_y)) & page.rect
            if clip.is_empty:
                continue
            scale = 1440 / max(clip.width, clip.height)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
            image["source"]["data"] = standard_b64encode(pixmap.tobytes("jpeg", jpg_quality=87)).decode("ascii")


def audit(result):
    return result[2]["raw_usage"]


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


class RegistryReplayError(RuntimeError):
    """A derived compile requested evidence outside the current RFQ."""


def run_ordinary_haiku_membership(run_registry, *, file_bytes, ocr_package, stage_callback):
    """Use current-run replies for deterministic recompilation only."""
    records = defaultdict(list)
    token_counts = defaultdict(list)
    memberships = []
    canonical_ids = {}
    lock = Lock()
    calls = []
    failures = []

    def capture_ids(visual_map):
        raw_ids = [group["group_id"] for group in visual_map["visual_groups"]]
        normalized = adapter.normalize_detection_visual_map_group_ids(visual_map)
        canonical_ids.update(zip(raw_ids, (g["group_id"] for g in normalized["visual_groups"]), strict=True))
        return normalized

    def observe(client, **request):
        stage = kind_of(request)
        prepared = request
        if adapter._claude_runtime_model(request.get("model")) == CLAUDE_HAIKU_MODEL:
            if stage == "role":
                prepared = deepcopy(request)
                for block in prepared["system"]:
                    block["text"] = block["text"].replace(
                        "For each supplied target crop, decide only",
                        ROLE_RULE + "For each supplied target crop, decide only", 1,
                    )
            if stage == "membership":
                prepared = primary_request(request)
        response, diagnostics = adapter.create_claude_message_streamed(client, **prepared)
        key = request_hash(request)
        with lock:
            record_index = len(records[key])
            records[key].append((response, diagnostics))
            if stage == "membership":
                memberships.append((key, record_index, prepared, response))
        return response, diagnostics

    def count_input_tokens(*, client, **request):
        count = adapter._v641_count_input_tokens(client=client, **request)
        with lock:
            token_counts[request_hash(request)].append(count)
        return count

    original_semantics = adapter.compile_detection_v5_semantic_facts
    original_merge = adapter.compile_detection_v5_merge_edges
    primary = run_registry(
        stage_callback=stage_callback,
        review_hooks=adapter.DetectionRegistryHooks(
            observe, capture_ids, original_semantics, original_merge, count_input_tokens,
        ),
    )
    if not memberships:
        return primary

    membership_hash, membership_index, request, membership = memberships[-1]
    multilingual = audit(primary).get("v6_42_multilingual_evidence_fallback") or {}
    if multilingual.get("language_signal", {}).get("eligible"):
        return primary
    views, queue = inventory_of(request)
    original_text = next(block for block in membership.content if block.type == "text")
    payload = json.loads(original_text.text)

    def recompile(candidate_payload, *, compile_semantics=original_semantics, compile_merge=original_merge):
        derived = membership.model_copy(update={"content": [
            original_text.model_copy(update={"text": json.dumps(candidate_payload, ensure_ascii=False)})
        ]})
        queues = {key: deque(enumerate(values)) for key, values in records.items()}
        count_queues = {key: deque(values) for key, values in token_counts.items()}

        def replay_input_count(*, client, **request):
            key = request_hash(request)
            with lock:
                values = count_queues.get(key)
                if not values:
                    raise RegistryReplayError("A token budget request changed during current-run recompilation.")
                return values.popleft()

        def replay(_client, **repeated_request):
            key = request_hash(repeated_request)
            with lock:
                queue = queues.get(key)
                if not queue:
                    raise RegistryReplayError("A registry request changed during current-run recompilation.")
                index, (response, diagnostics) = queue.popleft()
            return (derived if (key, index) == (membership_hash, membership_index) else response), diagnostics

        result = run_registry(
            stage_callback=None,
            review_hooks=adapter.DetectionRegistryHooks(
                replay, adapter.normalize_detection_visual_map_group_ids, compile_semantics, compile_merge, replay_input_count,
            ),
        )
        if any(queues.values()) or any(count_queues.values()):
            raise RegistryReplayError("Registry recompilation did not use all current-run replies.")
        return result

    def review(stage, pages, marked=None, usage=None):
        try:
            prepared = batch_request(request, pages, views)
            if marked:
                page = min(pages)
                improve_local_crops(prepared, file_bytes, ocr_package, usage, page)
                prepared["system"][0]["text"] += LOCAL_RULE
                prepared["messages"][0]["content"][-1]["text"] += (
                    "\nViews marked for another look: " + ", ".join(sorted(marked))
                )
                dimension_context = dimensional_review_context(usage, canonical_ids, views, queue, page, marked)
                if dimension_context:
                    prepared["messages"][0]["content"][-1]["text"] += (
                        "\nSame-page OCR dimension comparisons, normalized to millimeters. "
                        "Check which feature the dimension spans in each crop. Matching numbers alone do not establish identity.\n"
                        + dimension_context
                    )
            response, diagnostics = adapter.create_claude_message_streamed(adapter.get_anthropic_client(), **prepared)
            content = prepared["messages"][0]["content"]
            summary = adapter.summarize_detection_provider_call(
                response=response, diagnostics=diagnostics, requested_model=prepared["model"],
                prompt_characters=len(prepared["system"][0]["text"]),
                context_characters=len(content[-1]["text"]), image_count=(len(content) - 1) // 2,
                image_bytes=sum(len(block["source"]["data"]) * 3 // 4 for block in content if block["type"] == "image"),
            )
            with lock:
                calls.append({"stage": stage, "pages": sorted(pages), "message_id": response.id, **summary})
            if response.stop_reason != "end_turn":
                return []
            data = json.loads(adapter.extract_text_from_claude_response(response))
            hypotheses = candidate_hypotheses(data, pages if marked else pages & missing, views, queue)
            if marked:
                return [
                    h for h in hypotheses if marked.intersection(h["group_ids"])
                    and {f"registry_view:{group}" for group in h["group_ids"]}
                    <= set(h["evidence"][0]["source_fact_ids"])
                ]
            return hypotheses
        except (RuntimeError, ValueError, KeyError) as exc:
            with lock:
                failures.append({"stage": stage, "pages": sorted(pages), "error_type": type(exc).__name__})
            return []

    final = primary
    prior_components = [row["visual_group_ids"] for row in audit(primary)["proof_graph_components"]]
    eligible_ids = {
        canonical_ids[group] for group, (_, role) in views.items()
        if group in canonical_ids and role != "presentation_render"
    } & {group for component in prior_components for group in component}
    anchor_proofs = unambiguous_recovery_edges(dimension_anchors(audit(primary), eligible_ids), prior_components)
    anchor_pairs = {edge_endpoints(proof) for proof in anchor_proofs}

    def merge_with_dimensions(dimension_edges, semantics, **kwargs):
        return original_merge(dimension_edges, semantics, **kwargs, dimension_anchor_pairs=anchor_pairs)

    accepted_recovery = []
    missing = set()
    unresolved = defaultdict(set)
    try:
        if anchor_pairs:
            candidate = recompile(payload, compile_merge=merge_with_dimensions)
            old_groups = {
                group: i for i, component in enumerate(prior_components)
                if len(component) > 1 for group in component
            }
            new_components = [row["visual_group_ids"] for row in audit(candidate)["proof_graph_components"]]
            if any(len({old_groups[g] for g in component if g in old_groups}) > 1 for component in new_components):
                anchor_pairs.clear()
            else:
                final = candidate

        pages_with_merge = {int(view.split(".")[0][1:]) for group in partition(audit(final))
                            if len(group) > 1 for view in group}
        counts = Counter(page for page, role in views.values() if role != "presentation_render")
        missing = {page for page, count in counts.items() if count > 1} - pages_with_merge
        pages = sorted(counts)
        batches = [set(pages[offset:offset+BATCH_SIZE]) for offset in range(0, len(pages), BATCH_SIZE)]
        active = [batch for batch in batches if batch & missing]
        if active:
            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
                additional = [h for rows in pool.map(lambda batch: review("same_page_supplement", batch), active) for h in rows]
            covered_pages = {views[h["group_ids"][0]][0] for h in additional}
            if covered_pages:
                payload["object_hypotheses"] = [
                    hypothesis for hypothesis in payload["object_hypotheses"]
                    if not any(all(group in views and views[group][0] == page for group in hypothesis["group_ids"])
                               for page in covered_pages)
                ] + sorted(additional, key=lambda hypothesis: -len(hypothesis["evidence"]))
                final = recompile(payload, compile_merge=merge_with_dimensions)

        intermediate_usage = audit(final)
        components = [row["visual_group_ids"] for row in intermediate_usage["proof_graph_components"]]
        singleton_ids = {row[0] for row in components if len(row) == 1}
        for view_id, (page, role) in views.items():
            if counts[page] > 1 and role != "presentation_render" and canonical_ids.get(view_id) in singleton_ids:
                unresolved[page].add(view_id)
        if unresolved:
            def review_local(item):
                page, marked = item
                return review("local_membership_recovery", {page}, marked, intermediate_usage)

            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
                local = list(pool.map(review_local, sorted(unresolved.items())))
            facts = []
            for rows in local:
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
                    base, ledger = merge_with_dimensions(dimension_edges, semantics, **kwargs)
                    pairs = {edge_endpoints(fact) for fact in validated}
                    local_dimensions = [edge for edge in dimension_edges if edge_endpoints(edge) in pairs]
                    local_graph, _ = original_merge(
                        local_dimensions, validated, **{**kwargs, "allow_batch_confirmation": False},
                    )
                    accepted_recovery[:] = unambiguous_recovery_edges(
                        [edge for edge in local_graph if edge["relationship"] == "same_object_view"],
                        components,
                    )
                    recovered_pairs = {edge_endpoints(edge) for edge in accepted_recovery}
                    ledger["local_membership_recovery"] = accepted_recovery
                    return [edge for edge in base if edge_endpoints(edge) not in recovered_pairs] + accepted_recovery, ledger

                final = recompile(payload, compile_semantics=validate_local, compile_merge=merge_local)
    except (RegistryReplayError, adapter.DetectionVisualRegistryValidationError) as exc:
        failures.append({"stage": "recompile", "error_type": type(exc).__name__})

    usage = final[2]
    raw = audit(final)
    raw["ordinary_haiku_membership_recovery"] = {
        "primary_group_count": len(prior_components),
        "revisited_pages": sorted(missing),
        "local_review_pages": sorted(unresolved),
        "provider_calls": sorted(calls, key=lambda row: (row["stage"], row["pages"])),
        "dimension_anchor_pairs": sorted(anchor_pairs),
        "local_proven_edges": [edge_endpoints(edge) for edge in accepted_recovery],
        "failures": failures,
    }
    if calls:
        for field in ("input_tokens", "output_tokens"):
            usage[field] = raw[field] = int(usage[field]) + sum(int(call[field]) for call in calls)
        for field in ("input_cost_usd", "output_cost_usd", "total_cost_usd"):
            values = [usage.get(field), *(call[field] for call in calls)]
            usage[field] = (str(sum(Decimal(str(v)) for v in values).quantize(Decimal("0.000001")))
                            if all(v is not None for v in values) else None)
        raw["v5_9_total_provider_duration_seconds"] = round(
            float(raw["v5_9_total_provider_duration_seconds"])
            + sum(float(call.get("duration_seconds") or 0) for call in calls), 3,
        )
    return final
