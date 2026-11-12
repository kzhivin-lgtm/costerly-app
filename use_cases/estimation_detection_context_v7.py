"""Object-scoped export of saved Detection proof, without rerunning Detection."""
from copy import deepcopy
from hashlib import sha256
import json
from decimal import Decimal, InvalidOperation

from use_cases.estimation_dimension_graph import build_dimension_graph

VERSION = "estimation_detection_context_v7_1"


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build_context(*, inputs, event, ocr_package=None, include_measurements=False, published_partition=False):
    """Support the saved hypothesis-review route; fail explicitly on other routes.

    Membership is taken from frozen input regions and matched exactly to the
    normalized Detection inventory. Accepted hypotheses are supporting model
    observations, not independent source facts or a new membership decision.
    """
    if not inputs or not event.get("id"):
        raise ValueError("inputs and Detection event identity required")
    run_ids = {r["input_payload"]["run_id"] for r in inputs}
    companies = {str(r["input_payload"]["company_id"]) for r in inputs}
    if run_ids != {event.get("run_id")} or companies != {str(event.get("company_id"))}:
        raise ValueError("Detection event belongs to another run/company")
    audit = event["raw_usage"]
    source_fact_mapping = {}
    if ocr_package is not None:
        from agents.anthropic_adapter import build_detection_page_evidence_inventory
        source_items = {x["block_ref"]: x for row in inputs for container in ("evidence", "document_context")
                        for kind in ("ocr_blocks", "ocr_literal_items")
                        for x in row["input_payload"].get(container, {}).get(kind, []) if x.get("block_ref")}
        for fact in build_detection_page_evidence_inventory(ocr_package):
            matches = [ref for ref,x in source_items.items() if x.get("page_number") == fact["page_number"]
                       and x.get("text") == fact["text"] and x.get("bbox") == fact["bbox"]]
            if len(matches) > 1:
                raise ValueError("ambiguous OCR source-fact mapping")
            if matches:
                source_fact_mapping[fact["fact_id"]] = matches[0]
    packages = audit.get("view_evidence_packages") or []
    hypotheses = ((audit.get("semantic_ledger_audit") or {}).get("object_hypotheses") or {}).get("accepted") or []
    if not packages or (not hypotheses and not published_partition):
        raise ValueError("supported normalized inventory/accepted hypothesis audit missing")
    ids = [p["visual_group_id"] for p in packages]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate Detection island")
    # Preserve raw proposal aliases appearing inside verbatim observations.
    aliases = {}
    for group in (audit.get("registry_decision_audit") or {}).get("visual_groups", []):
        matches = [p for p in packages if p["page_number"] == group["page_number"] and p["bbox"] == group["bbox"]]
        if published_partition and not matches:
            continue
        if len(matches) != 1:
            raise ValueError("ambiguous Detection alias mapping")
        aliases[group["group_id"]] = matches[0]["visual_group_id"]
    objects, owned = [], set()
    packages_by_id = {p["visual_group_id"]: p for p in packages}
    frames = {f["page_number"]: f for f in audit.get("v5_9_coordinate_frame_audit", [])}
    for row in inputs:
        payload = row["input_payload"]
        islands = []
        for local in build_dimension_graph(input_row=row)["views"]:
            matches = [p for p in packages if p["page_number"] == local["page_number"] and p["bbox"] == local["bbox"]]
            if len(matches) != 1:
                raise ValueError("missing/ambiguous exact island mapping")
            p = matches[0]
            sid = p["visual_group_id"]
            if sid in owned:
                raise ValueError("Detection island assigned to multiple objects")
            owned.add(sid)
            island = dict(island_id=sid, local_view_id=local["view_id"],
                          page_number=local["page_number"], bbox=deepcopy(local["bbox"]))
            frame = frames.get(local["page_number"])
            if frame and (frame.get("source") == "mistral_page_dimensions" or published_partition):
                dims = frame["fusion_dimensions"]
                if not all(type(dims.get(k)) in (int, float) and dims[k] > 0 for k in ("width", "height")):
                    raise ValueError("invalid Detection coordinate frame")
                island["coordinate_frame_pixels"] = [dims["width"], dims["height"]]
                island["coordinate_frame_source"] = "detection_audit:" + frame["source"]
            if published_partition and "coordinate_frame_pixels" not in island:
                raise ValueError("published Detection island has no verified coordinate frame")
            islands.append(island)
        members = {i["island_id"] for i in islands}
        selected = [deepcopy(h) for h in hypotheses if set(h["group_ids"]) <= members]
        covered = set().union(*(set(h["group_ids"]) for h in selected)) if selected else set()
        render_audit = (audit.get("semantic_ledger_audit") or {}).get("v7_11_presentation_render") or {}
        render_decisions = [deepcopy(r) for r in render_audit.get("decisions", [])
                            if r.get("disposition") == "attach" and r.get("render_group_id") in members
                            and r.get("technical_group_id") in covered]
        covered.update(r["render_group_id"] for r in render_decisions)
        if (not selected or covered != members) and not published_partition:
            raise ValueError("accepted hypotheses do not cover frozen membership")
        refs = {x["block_ref"] for container in ("evidence", "document_context")
                for kind in ("ocr_blocks", "ocr_literal_items")
                for x in payload.get(container, {}).get(kind, []) if x.get("block_ref")}
        # Explicit mappings are needed before accepting source-fact references.
        # Saved Ada hypotheses cite registry_view IDs only; do not invent SF links.
        if published_partition:
            for sid in members:
                for fact in packages_by_id[sid].get("source_facts", ()):
                    if fact.get("fact_id"):
                        ref = fact["fact_id"]
                        source_fact_mapping.setdefault(ref, f"detection:{event['id']}:{ref}")
                        refs.add(source_fact_mapping[ref])
        for h in selected if not published_partition else ():
            for fact in h.get("evidence", []):
                for ref in fact.get("source_fact_ids", []):
                    if ref.startswith("registry_view:"):
                        if ref.removeprefix("registry_view:") not in members:
                            raise ValueError("foreign hypothesis island reference")
                    elif ref not in refs and source_fact_mapping.get(ref) not in refs:
                        raise ValueError("unmapped Detection source fact")
        facts = [deepcopy(f) for f in (audit.get("semantic_ledger_audit") or {}).get("accepted", [])
                 if {f.get("group_id_a"), f.get("group_id_b")} <= members]
        for index, fact in enumerate(facts, 1):
            fact["observation_id"] = f"detection:{event['id']}:{payload['object']['object_id']}:observation-{index:03d}"
        objects.append(dict(input_id=row["input_id"], object_id=payload["object"]["object_id"],
                            quantity=payload["object"]["quantity"], islands=islands,
                            accepted_hypotheses=selected, accepted_observations=facts,
                            presentation_render_decisions=render_decisions,
                            source_fact_mapping={k:v for k,v in source_fact_mapping.items() if v in refs},
                            observation_aliases={k: v for k, v in aliases.items() if v in members}))
    result = dict(contract_version=VERSION, run_id=event["run_id"], detection_event_id=event["id"],
                source_audit_sha256=digest(audit),
                compiler_version=(audit.get("v5_merge_audit") or {}).get("compiler_version"),
                authority="Frozen membership; prior model observations support interpretation and must be checked against source pixels/text.",
                objects=objects)
    if include_measurements:
        available = audit.get("dimension_inventory_valid") and isinstance(audit.get("dimension_inventory"), list)
        if not available and not published_partition:
            raise ValueError("saved Detection dimension inventory unavailable")
        graph = audit.get("dimension_graph_audit") or {}
        result.update(contract_version="estimation_detection_context_v7_2",
            authority="Reuse frozen membership, established island correspondences and normalized measurements. Resolve concrete conflicts only; no repeated membership proof.",
            unit_context=dict(declared=deepcopy(audit.get("document_dimension_unit_profile") or {}),
                effective_unit=graph.get("effective_document_dimension_unit", "unknown"),
                reason=graph.get("effective_document_dimension_unit_reason", "unknown"),
                source="saved_detection_audit"))
        for obj in objects:
            members = {i["island_id"] for i in obj["islands"]}
            inventory = [deepcopy(row) for row in (audit["dimension_inventory"] if available else ())
                         if row["group_id"] in members]
            if not published_partition and {r["group_id"] for r in inventory} != members:
                raise ValueError("dimension inventory must cover all owned islands, including empty rows")
            seen_measurements = set()
            for row in inventory:
                kept = []
                for measurement in row.get("occurrences", []):
                    mid = measurement["occurrence_id"]
                    if mid in seen_measurements:
                        raise ValueError("duplicate Detection measurement")
                    seen_measurements.add(mid)
                    try:
                        value = Decimal(str(measurement["value_mm"]))
                    except InvalidOperation as exc:
                        if published_partition:
                            continue
                        raise ValueError("invalid normalized Detection value") from exc
                    if not value.is_finite() or value <= 0:
                        # Zero-level annotations are valid source datums, but
                        # this inventory is used only for physical dimensions.
                        if published_partition:
                            continue
                        raise ValueError("invalid normalized Detection value")
                    refs = measurement.get("source_fact_ids") or []
                    if not refs or any(ref not in obj["source_fact_mapping"] for ref in refs):
                        if published_partition:
                            continue
                        raise ValueError("measurement has unmapped OCR provenance")
                    measurement["source_refs"] = [obj["source_fact_mapping"][ref] for ref in refs]
                    kept.append(measurement)
                row["occurrences"] = kept
            if published_partition:
                present = {row["group_id"] for row in inventory}
                inventory.extend({"group_id": sid, "occurrences": []} for sid in sorted(members - present))
            obj["dimension_inventory"] = inventory
            obj["dimension_correspondences"] = [
                dict(group_id_a=edge["group_id_a"], group_id_b=edge["group_id_b"],
                     evidence_facts=deepcopy(edge["evidence_facts"]))
                for edge in audit.get("positive_relation_edges", [])
                if {edge.get("group_id_a"), edge.get("group_id_b")} <= members
                and any(f.get("evidence_type") in {"dimension_equality", "dimension_transform", "visual_dimension_similarity"}
                        for f in edge.get("evidence_facts", []))]
    return result
