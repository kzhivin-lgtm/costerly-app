"""Detection V8.2, a clean evidence-to-component pipeline.

The module deliberately owns only five irreversible boundaries:

``source recall -> Discovery -> exceptional conflict review -> Membership -> components``.

Candidate regions are recall observations, never provisional islands or graph
nodes.  Discovery has one terminal decision for each observed island.  The
resolver may add an ordinary island only when Discovery contradicts compact
native dimension evidence.  Membership is the only grouping operation.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Callable


_BBOX_KEYS = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
_DIMENSION_RE = re.compile(r"[+\-±]?\d+(?:[.,]\d+)?")
_REPRESENTATION_KINDS = (
    "technical_plan",
    "technical_elevation",
    "technical_section",
    "technical_detail",
    "technical_perspective",
    "presentation_render",
    "floor_plan",
    "document_context",
)
_PLAN_KINDS = {"floor_plan"}
_RENDER_KIND = "presentation_render"
_PROOF_KINDS = {
    "explicit_document_relation",
    "matching_topology",
    "unique_geometry",
    "direct_shared_structure",
    "dimension_equality",
}
_RENDER_PROOF_KINDS = {"matching_topology", "unique_geometry"}


class DetectionV82ContractError(ValueError):
    """A stage returned data outside the V8.2 contract."""


def _bbox_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(_BBOX_KEYS),
        "properties": {
            "top_left_x": {"type": "integer", "minimum": 0},
            "top_left_y": {"type": "integer", "minimum": 0},
            "bottom_right_x": {"type": "integer", "minimum": 1},
            "bottom_right_y": {"type": "integer", "minimum": 1},
        },
    }


DETECTION_V82_DISCOVERY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["islands"],
    "properties": {
        "islands": {
            "type": "array",
            "maxItems": 96,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "page_number", "bbox", "core_bbox", "representation_kind",
                    "decision", "exclusion_kind", "visual_description", "reason",
                ],
                "properties": {
                    "page_number": {"type": "integer", "minimum": 1},
                    "bbox": {"$ref": "#/$defs/bbox"},
                    "core_bbox": {"$ref": "#/$defs/bbox"},
                    "representation_kind": {"type": "string", "enum": list(_REPRESENTATION_KINDS)},
                    "decision": {"type": "string", "enum": ["object_evidence", "exclude"]},
                    "exclusion_kind": {"type": "string", "enum": ["floor_plan", "document_context", "other"]},
                    "visual_description": {"type": "string", "minLength": 1, "maxLength": 160},
                    "reason": {"type": "string", "minLength": 1, "maxLength": 160},
                },
            },
        },
    },
    "$defs": {"bbox": _bbox_schema()},
}

DETECTION_V82_CONFLICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["target_id", "decision", "reason"],
    "properties": {
        "target_id": {"type": "string", "minLength": 1, "maxLength": 64},
        "decision": {"type": "string", "enum": ["object_evidence", "exclude"]},
        "bbox": {"$ref": "#/$defs/bbox"},
        "core_bbox": {"$ref": "#/$defs/bbox"},
        "representation_kind": {"type": "string", "enum": list(_REPRESENTATION_KINDS)},
        "visual_description": {"type": "string", "minLength": 1, "maxLength": 160},
        "reason": {"type": "string", "minLength": 1, "maxLength": 160},
    },
    "$defs": {"bbox": _bbox_schema()},
}

DETECTION_V82_MEMBERSHIP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["same_page_decisions", "cross_page_links"],
    "properties": {
        "same_page_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["group_id_a", "group_id_b", "decision", "reason", "proofs"],
                "properties": {
                    "group_id_a": {"type": "string", "minLength": 1, "maxLength": 64},
                    "group_id_b": {"type": "string", "minLength": 1, "maxLength": 64},
                    "decision": {"type": "string", "enum": ["same_object", "different_or_insufficient"]},
                    "reason": {"type": "string", "minLength": 1, "maxLength": 120},
                    "proofs": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["kind", "observation"],
                            "properties": {
                                "kind": {"type": "string", "enum": sorted(_PROOF_KINDS)},
                                "observation": {"type": "string", "minLength": 1, "maxLength": 160},
                            },
                        },
                    },
                },
            },
        },
        "cross_page_links": {
            "type": "array",
            "maxItems": 160,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["group_id_a", "group_id_b", "proofs"],
                "properties": {
                    "group_id_a": {"type": "string", "minLength": 1, "maxLength": 64},
                    "group_id_b": {"type": "string", "minLength": 1, "maxLength": 64},
                    "proofs": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["kind", "observation"],
                            "properties": {
                                "kind": {"type": "string", "enum": sorted(_PROOF_KINDS)},
                                "observation": {"type": "string", "minLength": 1, "maxLength": 160},
                            },
                        },
                    },
                },
            },
        },
    },
}


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        result = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    if result["bottom_right_x"] <= result["top_left_x"] or result["bottom_right_y"] <= result["top_left_y"]:
        return None
    return result


def _area(bbox: dict[str, int]) -> int:
    return (bbox["bottom_right_x"] - bbox["top_left_x"]) * (bbox["bottom_right_y"] - bbox["top_left_y"])


def _intersection(left: dict[str, int], right: dict[str, int]) -> int:
    return max(0, min(left["bottom_right_x"], right["bottom_right_x"]) - max(left["top_left_x"], right["top_left_x"])) * max(0, min(left["bottom_right_y"], right["bottom_right_y"]) - max(left["top_left_y"], right["top_left_y"]))


def _contains(outer: dict[str, int], inner: dict[str, int]) -> bool:
    return all((
        outer["top_left_x"] <= inner["top_left_x"],
        outer["top_left_y"] <= inner["top_left_y"],
        outer["bottom_right_x"] >= inner["bottom_right_x"],
        outer["bottom_right_y"] >= inner["bottom_right_y"],
    ))


def _centre_inside(outer: dict[str, int], inner: dict[str, int]) -> bool:
    x = (inner["top_left_x"] + inner["bottom_right_x"]) / 2
    y = (inner["top_left_y"] + inner["bottom_right_y"]) / 2
    return outer["top_left_x"] <= x <= outer["bottom_right_x"] and outer["top_left_y"] <= y <= outer["bottom_right_y"]


def _stable_id(prefix: str, page_number: int, bbox: dict[str, int]) -> str:
    geometry = ":".join(str(bbox[key]) for key in _BBOX_KEYS)
    return f"{prefix}-P{page_number:03d}-{sha256(f'{page_number}:{geometry}'.encode()).hexdigest()[:12]}"


def _page_dimensions(page: dict[str, Any], facts: list[dict[str, Any]]) -> tuple[int, int]:
    dimensions = page.get("dimensions") if isinstance(page.get("dimensions"), dict) else {}
    try:
        width, height = int(dimensions["width"]), int(dimensions["height"])
    except (KeyError, TypeError, ValueError):
        width = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_x", 0) for fact in facts), default=1)
        height = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_y", 0) for fact in facts), default=1)
    return max(width, 1), max(height, 1)


def _is_native_dimension(fact: dict[str, Any]) -> bool:
    if not str(fact.get("source") or "").startswith("native_pdf_"):
        return False
    text = str(fact.get("text") or "").strip()
    if not _DIMENSION_RE.fullmatch(text):
        return False
    try:
        return abs(float(text.replace("±", "").replace(",", "."))) >= 20
    except ValueError:
        return False


def _mypdf_recall_regions(*, page: dict[str, Any], page_number: int, source_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create compact recall boxes, never broad object envelopes.

    A fixed cell makes numeric labels deterministic and stops a distance chain
    from joining distant drawings.  Unlike V8.1, no minimum page-sized box is
    imposed, so source recall cannot flood Discovery with overlapping regions.
    """
    entries = [
        (fact, bbox)
        for fact in source_facts
        if int(fact.get("page_number") or 0) == page_number
        and _is_native_dimension(fact)
        and (bbox := _bbox(fact.get("bbox"))) is not None
    ]
    cells: dict[tuple[int, int], list[tuple[dict[str, Any], dict[str, int]]]] = {}
    for fact, bbox in entries:
        cx = (bbox["top_left_x"] + bbox["bottom_right_x"]) // 2
        cy = (bbox["top_left_y"] + bbox["bottom_right_y"]) // 2
        cells.setdefault((cx // 500, cy // 500), []).append((fact, bbox))
    width, height = _page_dimensions(page, [fact for fact, _ in entries])
    regions: list[dict[str, Any]] = []
    for entries_in_cell in cells.values():
        if len(entries_in_cell) < 2:
            continue
        boxes = [box for _, box in entries_in_cell]
        bbox = {
            "top_left_x": max(0, min(box["top_left_x"] for box in boxes) - 96),
            "top_left_y": max(0, min(box["top_left_y"] for box in boxes) - 96),
            "bottom_right_x": min(width, max(box["bottom_right_x"] for box in boxes) + 96),
            "bottom_right_y": min(height, max(box["bottom_right_y"] for box in boxes) + 96),
        }
        if _bbox(bbox) is None:
            continue
        regions.append({
            "page_number": page_number,
            "bbox": bbox,
            "sources": {"mypdf_dimensions"},
            "source_fact_ids": {str(fact.get("fact_id") or "") for fact, _ in entries_in_cell if str(fact.get("fact_id") or "")},
            "dimension_fact_count": len(entries_in_cell),
        })
    return regions


def _same_recall_region(left: dict[str, int], right: dict[str, int]) -> bool:
    overlap = _intersection(left, right)
    if not overlap:
        return False
    return overlap / min(_area(left), _area(right)) >= 0.80 and overlap / max(_area(left), _area(right)) >= 0.65


def build_detection_v82_candidate_regions(ocr_package: dict[str, Any] | None, source_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministically union Mistral graphics and MyPDF recall evidence."""
    proposals: list[dict[str, Any]] = []
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number < 1:
            continue
        for block in page.get("blocks") or []:
            bbox = _bbox(block) if isinstance(block, dict) and block.get("type") == "image" else None
            if bbox is None:
                continue
            fact_ids = {
                str(fact.get("fact_id") or "")
                for fact in source_facts
                if int(fact.get("page_number") or 0) == page_number
                and (fact_bbox := _bbox(fact.get("bbox"))) is not None
                and _contains(bbox, fact_bbox)
                and str(fact.get("fact_id") or "")
            }
            proposals.append({
                "page_number": page_number,
                "bbox": bbox,
                "sources": {"mistral_graphic"},
                "source_fact_ids": fact_ids,
                "dimension_fact_count": 0,
            })
        proposals.extend(_mypdf_recall_regions(page=page, page_number=page_number, source_facts=source_facts))

    canonical: list[dict[str, Any]] = []
    for proposal in sorted(proposals, key=lambda item: (item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"], tuple(sorted(item["sources"])) )):
        match = next((current for current in canonical if current["page_number"] == proposal["page_number"] and _same_recall_region(current["bbox"], proposal["bbox"])), None)
        if match is None:
            canonical.append(deepcopy(proposal))
            continue
        match["sources"].update(proposal["sources"])
        match["source_fact_ids"].update(proposal["source_fact_ids"])
        match["dimension_fact_count"] += int(proposal["dimension_fact_count"])
        if "mistral_graphic" in proposal["sources"]:
            match["bbox"] = deepcopy(proposal["bbox"])

    candidates = [{
        "candidate_region_id": _stable_id("V82-C", row["page_number"], row["bbox"]),
        "page_number": row["page_number"],
        "bbox": deepcopy(row["bbox"]),
        "sources": sorted(row["sources"]),
        "source_fact_ids": sorted(row["source_fact_ids"]),
        "dimension_fact_count": int(row["dimension_fact_count"]),
        "technical_signal": int(row["dimension_fact_count"]) >= 2,
    } for row in canonical]
    return sorted(candidates, key=lambda item: (item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"], item["candidate_region_id"]))


def _terminal_discovery_exclusion(kind: str) -> bool:
    """Only Discovery decides the two non-object representation kinds."""
    return kind in _PLAN_KINDS or kind == "document_context"


def _stable_view_sort_key(view: dict[str, Any]) -> tuple[Any, ...]:
    bbox = view["bbox"]
    return (int(view["page_number"]), bbox["top_left_y"], bbox["top_left_x"], bbox["bottom_right_y"], bbox["bottom_right_x"], str(view["group_id"]))


def normalize_detection_v82_discovery(raw_islands: object, *, page_dimensions: dict[int, tuple[int, int]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply one classified Discovery decision per actual visual island."""
    if not isinstance(raw_islands, list):
        raise DetectionV82ContractError("V8.2 Discovery islands must be a list")
    objects: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int, int, int]] = set()
    for raw in raw_islands:
        if not isinstance(raw, dict):
            raise DetectionV82ContractError("V8.2 Discovery island must be an object")
        try:
            page_number = int(raw.get("page_number"))
        except (TypeError, ValueError):
            raise DetectionV82ContractError("V8.2 Discovery page is invalid") from None
        bbox = _bbox(raw.get("bbox"))
        core_bbox = _bbox(raw.get("core_bbox")) or bbox
        kind = str(raw.get("representation_kind") or "").strip()
        decision = str(raw.get("decision") or "")
        description = " ".join(str(raw.get("visual_description") or "").split())
        reason = " ".join(str(raw.get("reason") or "").split())
        if page_number not in page_dimensions or bbox is None or core_bbox is None or not _contains(bbox, core_bbox) or kind not in _REPRESENTATION_KINDS or decision not in {"object_evidence", "exclude"} or not description or not reason:
            raise DetectionV82ContractError("V8.2 Discovery island contract is invalid")
        width, height = page_dimensions[page_number]
        if bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0 or bbox["bottom_right_x"] > width or bbox["bottom_right_y"] > height:
            raise DetectionV82ContractError("V8.2 Discovery bbox is outside its page")
        key = (page_number, *(bbox[field] for field in _BBOX_KEYS))
        if key in seen:
            raise DetectionV82ContractError("V8.2 Discovery emitted duplicate island geometry")
        seen.add(key)
        record = {
            "group_id": _stable_id("V82-I", page_number, bbox),
            "page_number": page_number,
            "bbox": bbox,
            "core_bbox": core_bbox,
            "representation_kind": kind,
            "visual_description": description,
            "reason": reason,
        }
        terminal_exclusion = _terminal_discovery_exclusion(kind)
        if decision == "exclude" or terminal_exclusion:
            exclusions.append({
                **record,
                "decision": "exclude",
                "exclusion_kind": "floor_plan" if kind == "floor_plan" else ("document_context" if kind == "document_context" else str(raw.get("exclusion_kind") or "other")),
                "reason": "Floor plan excluded during Discovery." if kind == "floor_plan" else ("Document context excluded during Discovery." if kind == "document_context" else reason),
            })
        else:
            objects.append({**record, "evidence_class": "object_evidence"})
    return sorted(objects, key=_stable_view_sort_key), sorted(exclusions, key=_stable_view_sort_key)


def _candidate_is_covered(candidate_bbox: dict[str, int], view: dict[str, Any]) -> bool:
    overlap = _intersection(candidate_bbox, view["bbox"])
    return bool(overlap) and (overlap / _area(candidate_bbox) >= 0.55 or _centre_inside(view["core_bbox"], candidate_bbox))


def audit_detection_v82_candidate_coverage(*, candidates: list[dict[str, Any]], object_evidence: list[dict[str, Any]], exclusions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Audit source recall without allowing recall observations to become islands."""
    audit: list[dict[str, Any]] = []
    for candidate in candidates:
        page_number = int(candidate["page_number"])
        object_ids = [str(view["group_id"]) for view in object_evidence if int(view["page_number"]) == page_number and _candidate_is_covered(candidate["bbox"], view)]
        exclusion_ids = [str(view["group_id"]) for view in exclusions if int(view["page_number"]) == page_number and _candidate_is_covered(candidate["bbox"], view)]
        audit.append({
            "candidate_region_id": candidate["candidate_region_id"],
            "page_number": page_number,
            "technical_signal": bool(candidate["technical_signal"]),
            "status": "covered_by_object_evidence" if object_ids else ("covered_by_terminal_exclusion" if exclusion_ids else "unexplained"),
            "object_group_ids": sorted(object_ids),
            "exclusion_group_ids": sorted(exclusion_ids),
        })
    return audit


def select_detection_v82_conflict_targets(*, candidates: list[dict[str, Any]], coverage_audit: list[dict[str, Any]], max_targets: int = 4) -> list[dict[str, Any]]:
    """Select at most one compact unresolved signal per page before another page.

    This round-robin selection keeps the resolver exceptional and prevents the
    first noisy page from suppressing an independent P10 contradiction.
    """
    if max_targets < 1:
        raise ValueError("V8.2 Conflict Resolver max_targets must be positive")
    coverage_by_id = {str(row["candidate_region_id"]): row for row in coverage_audit}
    by_page: dict[int, list[dict[str, Any]]] = {}
    for candidate in candidates:
        coverage = coverage_by_id.get(str(candidate["candidate_region_id"]))
        if not candidate.get("technical_signal") or not coverage or coverage.get("status") != "unexplained":
            continue
        by_page.setdefault(int(candidate["page_number"]), []).append(candidate)
    targets: list[dict[str, Any]] = []
    for page_number in sorted(by_page):
        candidate = sorted(by_page[page_number], key=lambda item: (-int(item["dimension_fact_count"]), _area(item["bbox"]), item["candidate_region_id"]))[0]
        targets.append({
            "target_id": _stable_id("V82-R", page_number, candidate["bbox"]),
            "candidate_region_id": candidate["candidate_region_id"],
            "page_number": page_number,
            "bbox": deepcopy(candidate["bbox"]),
            "source_fact_ids": list(candidate["source_fact_ids"]),
        })
        if len(targets) == max_targets:
            break
    return targets


def apply_detection_v82_conflict_decisions(*, object_evidence: list[dict[str, Any]], targets: list[dict[str, Any]], decisions: object, page_dimensions: dict[int, tuple[int, int]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Admit resolved islands through the same ordinary object-evidence path."""
    if not isinstance(decisions, list):
        raise DetectionV82ContractError("V8.2 Conflict Resolver decisions must be a list")
    targets_by_id = {str(target["target_id"]): target for target in targets}
    by_id: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        target_id = str(decision.get("target_id") or "") if isinstance(decision, dict) else ""
        if not isinstance(decision, dict) or target_id not in targets_by_id or target_id in by_id:
            raise DetectionV82ContractError("V8.2 Conflict Resolver target is invalid")
        if str(decision.get("decision") or "") not in {"object_evidence", "exclude"} or not str(decision.get("reason") or "").strip():
            raise DetectionV82ContractError("V8.2 Conflict Resolver decision is invalid")
        by_id[target_id] = decision
    if set(by_id) != set(targets_by_id):
        raise DetectionV82ContractError("V8.2 Conflict Resolver must decide every target once")

    admitted = [deepcopy(view) for view in object_evidence]
    audit: list[dict[str, Any]] = []
    for target in targets:
        raw = by_id[str(target["target_id"])]
        disposition = str(raw["decision"])
        row = {"target_id": target["target_id"], "candidate_region_id": target["candidate_region_id"], "decision": disposition, "reason": " ".join(str(raw["reason"]).split())}
        if disposition == "exclude":
            audit.append(row)
            continue
        bbox = _bbox(raw.get("bbox"))
        core_bbox = _bbox(raw.get("core_bbox")) or bbox
        kind = str(raw.get("representation_kind") or "").strip()
        description = " ".join(str(raw.get("visual_description") or "").split())
        width, height = page_dimensions[int(target["page_number"])]
        if bbox is None or core_bbox is None or not _contains(bbox, core_bbox) or kind not in _REPRESENTATION_KINDS or not description or bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0 or bbox["bottom_right_x"] > width or bbox["bottom_right_y"] > height or _terminal_discovery_exclusion(kind):
            raise DetectionV82ContractError("V8.2 Conflict Resolver admission is invalid")
        if _intersection(bbox, target["bbox"]) / _area(bbox) < 0.30:
            raise DetectionV82ContractError("V8.2 Conflict Resolver admission is outside its target")
        if any(int(view["page_number"]) == int(target["page_number"]) and _intersection(core_bbox, view["core_bbox"]) / min(_area(core_bbox), _area(view["core_bbox"])) >= 0.80 for view in admitted):
            raise DetectionV82ContractError("V8.2 Conflict Resolver duplicated a Discovery island")
        group_id = _stable_id("V82-I", int(target["page_number"]), bbox)
        if any(str(view["group_id"]) == group_id for view in admitted):
            raise DetectionV82ContractError("V8.2 Conflict Resolver duplicated a group identifier")
        admitted.append({
            "group_id": group_id,
            "page_number": int(target["page_number"]),
            "bbox": bbox,
            "core_bbox": core_bbox,
            "representation_kind": kind,
            "visual_description": description,
            "reason": row["reason"],
            "evidence_class": "object_evidence",
        })
        row["admitted_group_id"] = group_id
        audit.append(row)
    return sorted(admitted, key=_stable_view_sort_key), audit


def normalize_detection_v82_membership_links(raw_links: object, *, object_evidence: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate the one pair-link contract, including presentation renders."""
    if not isinstance(raw_links, list):
        raise DetectionV82ContractError("V8.2 Membership links must be a list")
    kind_by_id = {str(view["group_id"]): str(view["representation_kind"]) for view in object_evidence}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_links):
        if not isinstance(raw, dict):
            rejected.append({"index": index, "reason": "link_not_object"})
            continue
        left, right = sorted((str(raw.get("group_id_a") or ""), str(raw.get("group_id_b") or "")))
        proofs = raw.get("proofs")
        pair = (left, right)
        if left == right or left not in kind_by_id or right not in kind_by_id or not isinstance(proofs, list) or pair in seen:
            rejected.append({"index": index, "reason": "endpoints_or_proofs_invalid"})
            continue
        seen.add(pair)
        normalized: list[dict[str, str]] = []
        invalid = False
        for proof in proofs:
            kind = str(proof.get("kind") or "") if isinstance(proof, dict) else ""
            observation = " ".join(str(proof.get("observation") or "").split()) if isinstance(proof, dict) else ""
            if kind not in _PROOF_KINDS or not observation:
                invalid = True
                break
            normalized.append({"kind": kind, "observation": observation})
        if invalid or not normalized:
            rejected.append({"index": index, "reason": "proof_invalid"})
            continue
        render_count = sum(kind_by_id[group_id] == _RENDER_KIND for group_id in pair)
        proof_kinds = {proof["kind"] for proof in normalized}
        if render_count == 1:
            valid = proof_kinds.issubset(_RENDER_PROOF_KINDS)
            reason = "render_link_requires_visual_proof"
        elif render_count == 0:
            valid = len(proof_kinds) >= 2
            reason = "technical_link_requires_two_independent_proofs"
        else:
            valid = False
            reason = "render_to_render_is_not_membership"
        if not valid:
            rejected.append({"index": index, "reason": reason})
            continue
        accepted.append({"group_id_a": left, "group_id_b": right, "proofs": sorted(normalized, key=lambda item: (item["kind"], item["observation"]))})
    return sorted(accepted, key=lambda item: (item["group_id_a"], item["group_id_b"])), rejected


def _same_page_membership_pair_rule(left: dict[str, Any], right: dict[str, Any]) -> str:
    render_count = sum(
        str(view["representation_kind"]) == _RENDER_KIND
        for view in (left, right)
    )
    if render_count == 2:
        return "must_not_link"
    if render_count == 1:
        return "visual_proof_only"
    return "two_independent_proofs"


def build_detection_v82_same_page_membership_pairs(*, object_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enumerate every valid unordered Membership pair on each page.

    The matrix is deterministic and is a review obligation only. It neither
    creates a link nor suggests that two views belong together.
    """
    by_page: dict[int, list[dict[str, Any]]] = {}
    for view in object_evidence:
        by_page.setdefault(int(view["page_number"]), []).append(view)
    pairs: list[dict[str, Any]] = []
    for page_number in sorted(by_page):
        views = sorted(by_page[page_number], key=_stable_view_sort_key)
        pair_index = 0
        for index, left in enumerate(views):
            for right in views[index + 1:]:
                pair_index += 1
                group_id_a, group_id_b = sorted((str(left["group_id"]), str(right["group_id"])))
                pairs.append({
                    "pair_id": f"V82-SP-P{page_number:03d}-{pair_index:03d}",
                    "page_number": page_number,
                    "group_id_a": group_id_a,
                    "group_id_b": group_id_b,
                    "positive_rule": _same_page_membership_pair_rule(left, right),
                })
    return pairs


def normalize_detection_v82_membership_review(*, raw_review: object, object_evidence: list[dict[str, Any]], required_same_page_pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Require one decision for every deterministic same-page pair.

    Positive pairs are normalized through the ordinary link contract. Negative
    decisions remain an audit record, so omitted pairs cannot silently become
    singleton objects. Cross-page links are optional positive findings, so an
    invalid one is rejected and audited rather than terminating the run.
    """
    if not isinstance(raw_review, dict) or set(raw_review) != {"same_page_decisions", "cross_page_links"}:
        raise DetectionV82ContractError("V8.2 Membership response shape is invalid")
    raw_decisions, raw_cross_page_links = raw_review["same_page_decisions"], raw_review["cross_page_links"]
    if not isinstance(raw_decisions, list) or not isinstance(raw_cross_page_links, list):
        raise DetectionV82ContractError("V8.2 Membership response lists are invalid")
    required_by_pair = {
        (str(pair["group_id_a"]), str(pair["group_id_b"])): pair
        for pair in required_same_page_pairs
    }
    if len(required_by_pair) != len(required_same_page_pairs):
        raise DetectionV82ContractError("V8.2 Membership same-page matrix is invalid")
    decisions_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    positive_same_page_links: list[dict[str, Any]] = []
    positive_pair_ids: list[str] = []
    for raw in raw_decisions:
        if not isinstance(raw, dict):
            raise DetectionV82ContractError("V8.2 Membership decision must be an object")
        left, right = sorted((str(raw.get("group_id_a") or ""), str(raw.get("group_id_b") or "")))
        pair = (left, right)
        decision = str(raw.get("decision") or "")
        reason = " ".join(str(raw.get("reason") or "").split())
        proofs = raw.get("proofs")
        if pair not in required_by_pair or pair in decisions_by_pair or decision not in {"same_object", "different_or_insufficient"} or not reason or not isinstance(proofs, list):
            raise DetectionV82ContractError("V8.2 Membership same-page decision is invalid")
        if decision == "different_or_insufficient" and proofs:
            raise DetectionV82ContractError("V8.2 Membership negative decision must not include positive proofs")
        normalized = {
            "pair_id": required_by_pair[pair]["pair_id"],
            "page_number": required_by_pair[pair]["page_number"],
            "group_id_a": left,
            "group_id_b": right,
            "decision": decision,
            "reason": reason,
        }
        if decision == "same_object":
            rule = str(required_by_pair[pair]["positive_rule"])
            if rule == "must_not_link":
                # A render-to-render edge can never retain either view on its
                # own.  Removing it is deterministic, preserves the normal
                # render contract, and does not decide anything visual.
                normalized.update({
                    "decision": "different_or_insufficient",
                    "reason": "two presentation renders cannot form a Membership link",
                    "normalization": "forced_no_render_to_render_link",
                })
            else:
                accepted_proofs = proofs
                if rule == "visual_proof_only":
                    # The render contract is visual.  A surplus technical
                    # proof must not invalidate an otherwise valid visual
                    # attachment, but no missing visual proof is invented.
                    accepted_proofs = [
                        proof for proof in proofs
                        if isinstance(proof, dict) and str(proof.get("kind") or "") in _RENDER_PROOF_KINDS
                    ]
                positive_same_page_links.append({"group_id_a": left, "group_id_b": right, "proofs": accepted_proofs})
                positive_pair_ids.append(str(required_by_pair[pair]["pair_id"]))
        decisions_by_pair[pair] = normalized
    if set(decisions_by_pair) != set(required_by_pair):
        missing = sorted(set(required_by_pair) - set(decisions_by_pair))
        raise DetectionV82ContractError(f"V8.2 Membership omitted {len(missing)} required same-page pair decisions")

    same_page_links, rejected_same_page = normalize_detection_v82_membership_links(positive_same_page_links, object_evidence=object_evidence)
    if rejected_same_page or len(same_page_links) != len(positive_same_page_links):
        failures = "; ".join(
            f"{positive_pair_ids[int(row['index'])]}:{row['reason']}"
            for row in rejected_same_page
            if isinstance(row.get("index"), int) and int(row["index"]) < len(positive_pair_ids)
        ) or "unknown_pair"
        raise DetectionV82ContractError(
            f"V8.2 Membership same-page positive decision failed link validation ({failures})"
        )
    page_by_id = {str(view["group_id"]): int(view["page_number"]) for view in object_evidence}
    kind_by_id = {str(view["group_id"]): str(view["representation_kind"]) for view in object_evidence}
    same_page_pairs = set(required_by_pair)
    cross_page_inputs: list[object] = []
    for raw in raw_cross_page_links:
        if not isinstance(raw, dict):
            cross_page_inputs.append(raw)
            continue
        candidate = deepcopy(raw)
        endpoints = (str(candidate.get("group_id_a") or ""), str(candidate.get("group_id_b") or ""))
        if sum(kind_by_id.get(endpoint) == _RENDER_KIND for endpoint in endpoints) == 1 and isinstance(candidate.get("proofs"), list):
            # The render contract is visual across pages too.  Preserve valid
            # visual evidence and ignore an irrelevant extra technical proof.
            candidate["proofs"] = [
                proof for proof in candidate["proofs"]
                if isinstance(proof, dict) and str(proof.get("kind") or "") in _RENDER_PROOF_KINDS
            ]
        cross_page_inputs.append(candidate)
    normalized_cross_page_links, rejected_cross_page = normalize_detection_v82_membership_links(
        cross_page_inputs, object_evidence=object_evidence,
    )
    rejected_cross_page_audit = [
        {
            "index": int(row["index"]),
            "group_id_a": str(raw_cross_page_links[int(row["index"])].get("group_id_a") or "") if isinstance(raw_cross_page_links[int(row["index"])], dict) else "",
            "group_id_b": str(raw_cross_page_links[int(row["index"])].get("group_id_b") or "") if isinstance(raw_cross_page_links[int(row["index"])], dict) else "",
            "reason": str(row["reason"]),
        }
        for row in rejected_cross_page
        if isinstance(row.get("index"), int) and int(row["index"]) < len(raw_cross_page_links)
    ]
    cross_page_links: list[dict[str, Any]] = []
    for link in normalized_cross_page_links:
        pair = (str(link["group_id_a"]), str(link["group_id_b"]))
        if page_by_id[pair[0]] == page_by_id[pair[1]] or pair in same_page_pairs:
            rejected_cross_page_audit.append({
                "group_id_a": pair[0],
                "group_id_b": pair[1],
                "reason": "cross_page_link_is_not_cross_page",
            })
            continue
        cross_page_links.append(link)
    combined_by_pair = {
        (str(link["group_id_a"]), str(link["group_id_b"])): link
        for link in [*same_page_links, *cross_page_links]
    }
    if len(combined_by_pair) != len(same_page_links) + len(cross_page_links):
        raise DetectionV82ContractError("V8.2 Membership returned duplicate links")
    return (
        sorted(combined_by_pair.values(), key=lambda item: (item["group_id_a"], item["group_id_b"])),
        [decisions_by_pair[pair] for pair in sorted(decisions_by_pair)],
        rejected_cross_page_audit,
    )


def compile_detection_v82_components(*, object_evidence: list[dict[str, Any]], membership_links: list[dict[str, Any]]) -> tuple[list[list[str]], list[str]]:
    """Construct order-invariant components from accepted Membership links."""
    group_ids = sorted(str(view["group_id"]) for view in object_evidence)
    kind_by_id = {str(view["group_id"]): str(view["representation_kind"]) for view in object_evidence}
    parent = {group_id: group_id for group_id in group_ids}
    def root(group_id: str) -> str:
        while parent[group_id] != group_id:
            parent[group_id] = parent[parent[group_id]]
            group_id = parent[group_id]
        return group_id
    for link in sorted(membership_links, key=lambda item: (item["group_id_a"], item["group_id_b"])):
        left, right = root(link["group_id_a"]), root(link["group_id_b"])
        if left != right:
            parent[max(left, right)] = min(left, right)
    all_components: list[list[str]] = []
    by_root: dict[str, list[str]] = {}
    for group_id in group_ids:
        by_root.setdefault(root(group_id), []).append(group_id)
    for component in by_root.values():
        all_components.append(sorted(component))
    retained = [component for component in all_components if any(kind_by_id[group_id] != _RENDER_KIND for group_id in component)]
    excluded_renders = sorted(group_id for component in all_components if all(kind_by_id[group_id] == _RENDER_KIND for group_id in component) for group_id in component)
    return sorted(retained, key=lambda component: tuple(component)), excluded_renders


def run_detection_v82_pipeline(*, ocr_package: dict[str, Any] | None, source_facts: list[dict[str, Any]], page_dimensions: dict[int, tuple[int, int]], discover: Callable[[list[dict[str, Any]]], list[dict[str, Any]]], review_membership: Callable[[list[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]], resolve_conflict: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run V8.2 with provider callbacks constrained to their own boundaries."""
    candidates = build_detection_v82_candidate_regions(ocr_package, source_facts)
    object_evidence, exclusions = normalize_detection_v82_discovery(discover(deepcopy(candidates)), page_dimensions=page_dimensions)
    coverage = audit_detection_v82_candidate_coverage(candidates=candidates, object_evidence=object_evidence, exclusions=exclusions)
    targets = select_detection_v82_conflict_targets(candidates=candidates, coverage_audit=coverage)
    resolver_audit: list[dict[str, Any]] = []
    if targets and resolve_conflict is not None:
        object_evidence, resolver_audit = apply_detection_v82_conflict_decisions(object_evidence=object_evidence, targets=targets, decisions=[resolve_conflict(deepcopy(target)) for target in targets], page_dimensions=page_dimensions)
    required_same_page_pairs = build_detection_v82_same_page_membership_pairs(object_evidence=object_evidence)
    raw_review = review_membership(deepcopy(object_evidence), deepcopy(required_same_page_pairs))
    links, same_page_decisions, rejected_cross_page_links = normalize_detection_v82_membership_review(
        raw_review=raw_review,
        object_evidence=object_evidence,
        required_same_page_pairs=required_same_page_pairs,
    )
    components, excluded_renders = compile_detection_v82_components(object_evidence=object_evidence, membership_links=links)
    return {
        "version": "detection_v8_2_4",
        "candidate_regions": candidates,
        "discovery": {"object_evidence": object_evidence, "excluded": exclusions, "candidate_coverage": coverage},
        "conflict_resolver": {"attempted": bool(targets and resolve_conflict is not None), "targets": targets, "decisions": resolver_audit},
        "membership": {
            "same_page_required_pairs": required_same_page_pairs,
            "same_page_decisions": same_page_decisions,
            "accepted_links": links,
            "rejected_cross_page_links": rejected_cross_page_links,
        },
        "components": components,
        "excluded_unattached_presentation_renders": excluded_renders,
    }
