"""Detection V8: a small, stage-separated evidence pipeline.

V8 deliberately has five boundaries only:

``Fusion candidates -> Discovery islands -> exceptional resolver -> Membership
links -> deterministic object components``.

No candidate is a provisional object, no resolver admission has a special
membership path, and a presentation render is an ordinary Object Evidence view
with a narrower proof rule.  This module is intentionally provider-agnostic.
The Anthropic adapter supplies visual callbacks, while this module owns the
deterministic contracts and the complete audit trail.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Callable


_BBOX_KEYS = (
    "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
)
_DIMENSION_RE = re.compile(r"[+\-±]?\d+(?:[.,]\d+)?")
_PLAN_KINDS = {"floor_plan", "location_plan"}
_RENDER_KIND = "presentation_render"
_TECHNICAL_LINK_TYPES = {
    "explicit_document_relation",
    "matching_topology",
    "unique_geometry",
    "direct_shared_structure",
    "dimension_equality",
}
_RENDER_LINK_TYPES = {"matching_topology", "unique_geometry"}


class DetectionV8ContractError(ValueError):
    """Raised when a stage violates its narrow V8 contract."""


DETECTION_V8_DISCOVERY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["islands"],
    "properties": {
        "islands": {
            "type": "array",
            "maxItems": 128,
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
                    "representation_kind": {"type": "string", "minLength": 1, "maxLength": 64},
                    "decision": {"type": "string", "enum": ["object_evidence", "exclude"]},
                    "exclusion_kind": {"type": "string", "maxLength": 48},
                    "visual_description": {"type": "string", "maxLength": 180},
                    "reason": {"type": "string", "minLength": 1, "maxLength": 180},
                },
            },
        },
    },
    "$defs": {
        "bbox": {
            "type": "object",
            "additionalProperties": False,
            "required": list(_BBOX_KEYS),
            "properties": {
                "top_left_x": {"type": "integer", "minimum": 0},
                "top_left_y": {"type": "integer", "minimum": 0},
                "bottom_right_x": {"type": "integer", "minimum": 1},
                "bottom_right_y": {"type": "integer", "minimum": 1},
            },
        },
    },
}

DETECTION_V8_CONFLICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["target_id", "decision", "reason"],
    "properties": {
        "target_id": {"type": "string", "minLength": 1, "maxLength": 48},
        "decision": {"type": "string", "enum": ["object_evidence", "exclude"]},
        "bbox": {"$ref": "#/$defs/bbox"},
        "core_bbox": {"$ref": "#/$defs/bbox"},
        "representation_kind": {"type": "string", "maxLength": 64},
        "visual_description": {"type": "string", "maxLength": 180},
        "reason": {"type": "string", "minLength": 1, "maxLength": 180},
    },
    "$defs": deepcopy(DETECTION_V8_DISCOVERY_SCHEMA["$defs"]),
}

DETECTION_V8_MEMBERSHIP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["links"],
    "properties": {
        "links": {
            "type": "array",
            "maxItems": 256,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["group_id_a", "group_id_b", "evidence"],
                "properties": {
                    "group_id_a": {"type": "string", "minLength": 1, "maxLength": 48},
                    "group_id_b": {"type": "string", "minLength": 1, "maxLength": 48},
                    "evidence": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["evidence_type", "observation", "source_fact_ids"],
                            "properties": {
                                "evidence_type": {"type": "string", "enum": sorted(_TECHNICAL_LINK_TYPES)},
                                "observation": {"type": "string", "minLength": 1, "maxLength": 180},
                                "source_fact_ids": {
                                    "type": "array", "minItems": 2, "maxItems": 4,
                                    "items": {"type": "string", "minLength": 1, "maxLength": 64},
                                },
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
        bbox = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    if (
        bbox["bottom_right_x"] <= bbox["top_left_x"]
        or bbox["bottom_right_y"] <= bbox["top_left_y"]
    ):
        return None
    return bbox


def _area(bbox: dict[str, int]) -> int:
    return (
        (bbox["bottom_right_x"] - bbox["top_left_x"])
        * (bbox["bottom_right_y"] - bbox["top_left_y"])
    )


def _intersection_area(left: dict[str, int], right: dict[str, int]) -> int:
    width = max(
        0,
        min(left["bottom_right_x"], right["bottom_right_x"])
        - max(left["top_left_x"], right["top_left_x"]),
    )
    height = max(
        0,
        min(left["bottom_right_y"], right["bottom_right_y"])
        - max(left["top_left_y"], right["top_left_y"]),
    )
    return width * height


def _overlaps(left: dict[str, int], right: dict[str, int]) -> bool:
    return _intersection_area(left, right) > 0


def _contains(outer: dict[str, int], inner: dict[str, int]) -> bool:
    return (
        outer["top_left_x"] <= inner["top_left_x"]
        and outer["top_left_y"] <= inner["top_left_y"]
        and outer["bottom_right_x"] >= inner["bottom_right_x"]
        and outer["bottom_right_y"] >= inner["bottom_right_y"]
    )


def _same_region(left: dict[str, int], right: dict[str, int]) -> bool:
    """Return true only for practically identical source observations.

    Adjacent drawings must stay separate.  Containment is accepted only when
    the smaller source box is almost fully covered, which lets two suppliers
    describe one drawing without turning broad source clusters into authority.
    """
    intersection = _intersection_area(left, right)
    if not intersection:
        return False
    smallest = min(_area(left), _area(right))
    union = _area(left) + _area(right) - intersection
    return (
        (smallest > 0 and intersection / smallest >= 0.90)
        or (union > 0 and intersection / union >= 0.65)
    )


def _union_bbox(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {
        "top_left_x": min(left["top_left_x"], right["top_left_x"]),
        "top_left_y": min(left["top_left_y"], right["top_left_y"]),
        "bottom_right_x": max(left["bottom_right_x"], right["bottom_right_x"]),
        "bottom_right_y": max(left["bottom_right_y"], right["bottom_right_y"]),
    }


def _stable_id(prefix: str, page_number: int, bbox: dict[str, int]) -> str:
    payload = ":".join(str(bbox[key]) for key in _BBOX_KEYS)
    digest = sha256(f"{page_number}:{payload}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-P{page_number:03d}-{digest}"


def _page_dimensions(page: dict[str, Any], facts: list[dict[str, Any]]) -> tuple[int, int]:
    dimensions = page.get("dimensions") if isinstance(page.get("dimensions"), dict) else {}
    for width_key, height_key in (("width", "height"), ("image_width", "image_height")):
        try:
            width, height = int(dimensions[width_key]), int(dimensions[height_key])
        except (KeyError, TypeError, ValueError):
            continue
        if width > 0 and height > 0:
            return width, height
    max_x = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_x", 0) for fact in facts), default=1)
    max_y = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_y", 0) for fact in facts), default=1)
    return max(1, max_x), max(1, max_y)


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


def _mypdf_dimension_clusters(
    *,
    page_number: int,
    page: dict[str, Any],
    source_facts: list[dict[str, Any]],
    gap_px: int = 500,
) -> list[dict[str, Any]]:
    """Build bounded MyPDF candidate regions from substantive dimensions only."""
    entries = [
        (fact, bbox)
        for fact in source_facts
        if fact.get("page_number") == page_number
        and _is_native_dimension(fact)
        and (bbox := _bbox(fact.get("bbox"))) is not None
    ]
    # A connected graph with a fixed pair distance is not a spatial cluster:
    # an arbitrary chain of labels can bridge distinct drawings.  Candidate
    # Regions are recall-only in V8, so use compact fixed cells instead.  A
    # numeric label can belong to just one deterministic cell and cannot pull
    # an unrelated island into a broad transitive component.
    cells: dict[tuple[int, int], list[int]] = {}
    for index, (_fact, box) in enumerate(entries):
        centre_x = (box["top_left_x"] + box["bottom_right_x"]) / 2
        centre_y = (box["top_left_y"] + box["bottom_right_y"]) / 2
        cell = (int(centre_x // gap_px), int(centre_y // gap_px))
        cells.setdefault(cell, []).append(index)
    components = [
        sorted(indices)
        for _cell, indices in sorted(cells.items())
        if len(indices) >= 2
    ]

    page_width, page_height = _page_dimensions(page, [fact for fact, _ in entries])
    clusters: list[dict[str, Any]] = []
    for component in components:
        boxes = [entries[index][1] for index in component]
        left = max(0, min(box["top_left_x"] for box in boxes) - 80)
        top = max(0, min(box["top_left_y"] for box in boxes) - 80)
        right = min(page_width, max(box["bottom_right_x"] for box in boxes) + 80)
        bottom = min(page_height, max(box["bottom_right_y"] for box in boxes) + 80)
        # Do not create tiny numeric labels as drawing candidates.  The floor
        # keeps dimension grids visible while leaving final island geometry to
        # Discovery.
        centre_x, centre_y = (left + right) / 2, (top + bottom) / 2
        width, height = max(page_width * 0.18, right - left), max(page_height * 0.30, bottom - top)
        bbox = {
            "top_left_x": max(0, round(centre_x - width / 2)),
            "top_left_y": max(0, round(centre_y - height / 2)),
            "bottom_right_x": min(page_width, round(centre_x + width / 2)),
            "bottom_right_y": min(page_height, round(centre_y + height / 2)),
        }
        if _bbox(bbox) is None:
            continue
        clusters.append({
            "page_number": page_number,
            "bbox": bbox,
            "source_fact_ids": sorted(str(entries[index][0].get("fact_id") or "") for index in component),
            "dimension_fact_count": len(component),
        })
    return sorted(clusters, key=lambda item: (
        item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"],
    ))


def build_detection_v8_candidate_regions(
    ocr_package: dict[str, Any] | None,
    source_facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fuse Mistral and MyPDF observations without creating object proxies.

    Every visual Mistral region and every MyPDF dimension cluster is retained
    unless both suppliers observed effectively the same region.  No output of
    this function can enter dimensions, Q, Membership or package assembly.
    """
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
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            bbox = _bbox(block)
            if bbox is None:
                continue
            fact_ids = sorted(
                str(fact.get("fact_id") or "")
                for fact in source_facts
                if fact.get("page_number") == page_number
                and (fact_bbox := _bbox(fact.get("bbox"))) is not None
                and _contains(bbox, fact_bbox)
                and str(fact.get("fact_id") or "")
            )
            proposals.append({
                "page_number": page_number,
                "bbox": bbox,
                "sources": {"mistral_graphic"},
                "source_fact_ids": set(fact_ids),
                "dimension_fact_count": sum(
                    1 for fact in source_facts
                    if str(fact.get("fact_id") or "") in fact_ids and _is_native_dimension(fact)
                ),
            })
        for cluster in _mypdf_dimension_clusters(
            page_number=page_number, page=page, source_facts=source_facts,
        ):
            proposals.append({
                "page_number": page_number,
                "bbox": cluster["bbox"],
                "sources": {"mypdf_dimensions"},
                "source_fact_ids": set(cluster["source_fact_ids"]),
                "dimension_fact_count": cluster["dimension_fact_count"],
            })

    canonical: list[dict[str, Any]] = []
    for proposal in sorted(proposals, key=lambda item: (
        item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"],
        tuple(sorted(item["sources"])),
    )):
        existing = next((
            item for item in canonical
            if item["page_number"] == proposal["page_number"]
            and _same_region(item["bbox"], proposal["bbox"])
        ), None)
        if existing is None:
            canonical.append(deepcopy(proposal))
            continue
        existing["sources"].update(proposal["sources"])
        existing["source_fact_ids"].update(proposal["source_fact_ids"])
        existing["bbox"] = _union_bbox(existing["bbox"], proposal["bbox"])
        existing["dimension_fact_count"] = max(
            int(existing["dimension_fact_count"]), int(proposal["dimension_fact_count"]),
        )

    candidates: list[dict[str, Any]] = []
    for item in canonical:
        bbox = item["bbox"]
        candidates.append({
            "candidate_region_id": _stable_id("V8-C", item["page_number"], bbox),
            "page_number": item["page_number"],
            "bbox": deepcopy(bbox),
            "sources": sorted(item["sources"]),
            "source_fact_ids": sorted(item["source_fact_ids"]),
            # This is only an exceptional-resolver eligibility signal.  It is
            # never an Object Evidence claim or a graph seed.
            "technical_signal": int(item["dimension_fact_count"]) >= 2,
        })
    return sorted(candidates, key=lambda item: (
        item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"],
        item["candidate_region_id"],
    ))


def _dominant_floor_plan(
    *,
    representation_kind: str,
    bbox: dict[str, int],
    page_dimensions: dict[int, tuple[int, int]],
    page_number: int,
) -> bool:
    if representation_kind not in _PLAN_KINDS:
        return False
    page_width, page_height = page_dimensions.get(page_number, (0, 0))
    return page_width > 0 and page_height > 0 and _area(bbox) / (page_width * page_height) >= 0.75


def normalize_detection_v8_discovery(
    raw_islands: object,
    *,
    page_dimensions: dict[int, tuple[int, int]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate one Discovery decision per visually observed island.

    Discovery has only two outcomes: ``object_evidence`` and ``exclude``.
    A dominant floor plan is terminally excluded here.  It cannot reach the
    resolver or Membership, while a bounded object-specific plan remains a
    normal Object Evidence island.
    """
    if not isinstance(raw_islands, list):
        raise DetectionV8ContractError("V8 Discovery islands must be a list")
    objects: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    seen_geometry: set[tuple[int, int, int, int, int]] = set()
    for raw in raw_islands:
        if not isinstance(raw, dict):
            raise DetectionV8ContractError("V8 Discovery island must be an object")
        try:
            page_number = int(raw.get("page_number"))
        except (TypeError, ValueError):
            raise DetectionV8ContractError("V8 Discovery island page is invalid") from None
        bbox = _bbox(raw.get("bbox"))
        core_bbox = _bbox(raw.get("core_bbox")) or bbox
        decision = str(raw.get("decision") or "")
        kind = str(raw.get("representation_kind") or "").strip().lower()
        reason = " ".join(str(raw.get("reason") or "").split())
        description = " ".join(str(raw.get("visual_description") or "").split())
        if (
            page_number not in page_dimensions
            or bbox is None
            or core_bbox is None
            or not _contains(bbox, core_bbox)
            or decision not in {"object_evidence", "exclude"}
            or not kind
            or not description
            or not reason
        ):
            raise DetectionV8ContractError("V8 Discovery island contract is invalid")
        width, height = page_dimensions[page_number]
        if (
            bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0
            or bbox["bottom_right_x"] > width or bbox["bottom_right_y"] > height
        ):
            raise DetectionV8ContractError("V8 Discovery island bbox is outside its page")
        geometry_key = (page_number, *(bbox[key] for key in _BBOX_KEYS))
        if geometry_key in seen_geometry:
            raise DetectionV8ContractError("V8 Discovery emitted duplicate island geometry")
        seen_geometry.add(geometry_key)
        terminal_floor_plan = _dominant_floor_plan(
            representation_kind=kind,
            bbox=core_bbox,
            page_dimensions=page_dimensions,
            page_number=page_number,
        )
        record = {
            "group_id": _stable_id("V8-I", page_number, bbox),
            "page_number": page_number,
            "bbox": bbox,
            "core_bbox": core_bbox,
            "representation_kind": kind,
            "visual_description": description,
            "reason": reason,
        }
        if decision == "exclude" or terminal_floor_plan:
            exclusions.append({
                **record,
                "decision": "exclude",
                "exclusion_kind": "floor_plan" if terminal_floor_plan else str(
                    raw.get("exclusion_kind") or "other"
                ),
                "reason": (
                    "Dominant whole-level floor plan is excluded during Discovery."
                    if terminal_floor_plan else reason
                ),
            })
        else:
            objects.append({**record, "evidence_class": "object_evidence"})
    return (
        sorted(objects, key=lambda item: (item["page_number"], item["group_id"])),
        sorted(exclusions, key=lambda item: (item["page_number"], item["group_id"])),
    )


def audit_detection_v8_candidate_coverage(
    *,
    candidates: list[dict[str, Any]],
    object_evidence: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Record what happened to every candidate without making candidates objects."""
    audit: list[dict[str, Any]] = []
    for candidate in candidates:
        page_number = int(candidate["page_number"])
        bbox = candidate["bbox"]
        matching_objects = sorted(
            str(view["group_id"])
            for view in object_evidence
            if int(view["page_number"]) == page_number and _overlaps(bbox, view["bbox"])
        )
        matching_exclusions = sorted(
            str(view["group_id"])
            for view in exclusions
            if int(view["page_number"]) == page_number and _overlaps(bbox, view["bbox"])
        )
        status = (
            "covered_by_object_evidence" if matching_objects
            else "covered_by_terminal_exclusion" if matching_exclusions
            else "unexplained"
        )
        audit.append({
            "candidate_region_id": candidate["candidate_region_id"],
            "page_number": page_number,
            "technical_signal": bool(candidate.get("technical_signal")),
            "status": status,
            "object_group_ids": matching_objects,
            "exclusion_group_ids": matching_exclusions,
        })
    return audit


def select_detection_v8_conflict_targets(
    *,
    candidates: list[dict[str, Any]],
    coverage_audit: list[dict[str, Any]],
    max_targets: int = 3,
) -> list[dict[str, Any]]:
    """Select rare, proved Discovery contradictions for independent review.

    An unexplained candidate alone is not enough.  It needs a bounded native
    dimension signal and is capped for the whole document.  This keeps the
    resolver unavailable in the ordinary path and makes its invocation an
    observable product event rather than normal Discovery work.
    """
    if max_targets < 1:
        raise ValueError("V8 Conflict Resolver max_targets must be positive")
    by_id = {str(candidate["candidate_region_id"]): candidate for candidate in candidates}
    targets: list[dict[str, Any]] = []
    for audit in coverage_audit:
        candidate = by_id.get(str(audit.get("candidate_region_id") or ""))
        if (
            candidate is None
            or audit.get("status") != "unexplained"
            or not candidate.get("technical_signal")
        ):
            continue
        targets.append({
            "target_id": _stable_id("V8-R", int(candidate["page_number"]), candidate["bbox"]),
            "candidate_region_id": candidate["candidate_region_id"],
            "page_number": int(candidate["page_number"]),
            "bbox": deepcopy(candidate["bbox"]),
            "source_fact_ids": list(candidate["source_fact_ids"]),
        })
    return sorted(targets, key=lambda item: (
        item["page_number"], item["bbox"]["top_left_y"], item["bbox"]["top_left_x"],
    ))[:max_targets]


def apply_detection_v8_conflict_decisions(
    *,
    object_evidence: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    decisions: object,
    page_dimensions: dict[int, tuple[int, int]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply independent exceptional decisions as ordinary Object Evidence."""
    if not isinstance(decisions, list):
        raise DetectionV8ContractError("V8 Conflict Resolver decisions must be a list")
    targets_by_id = {str(target["target_id"]): target for target in targets}
    decisions_by_id: dict[str, dict[str, Any]] = {}
    for raw in decisions:
        if not isinstance(raw, dict):
            raise DetectionV8ContractError("V8 Conflict Resolver decision must be an object")
        target_id = str(raw.get("target_id") or "")
        if target_id not in targets_by_id or target_id in decisions_by_id:
            raise DetectionV8ContractError("V8 Conflict Resolver target is invalid")
        disposition = str(raw.get("decision") or "")
        reason = " ".join(str(raw.get("reason") or "").split())
        if disposition not in {"object_evidence", "exclude"} or not reason:
            raise DetectionV8ContractError("V8 Conflict Resolver decision is invalid")
        decisions_by_id[target_id] = raw
    if set(decisions_by_id) != set(targets_by_id):
        raise DetectionV8ContractError("V8 Conflict Resolver must decide every selected target once")

    result = [deepcopy(view) for view in object_evidence]
    audit: list[dict[str, Any]] = []
    existing_ids = {str(view["group_id"]) for view in result}
    for target in targets:
        raw = decisions_by_id[str(target["target_id"])]
        disposition = str(raw["decision"])
        reason = " ".join(str(raw["reason"]).split())
        audit_row = {
            "target_id": target["target_id"],
            "candidate_region_id": target["candidate_region_id"],
            "decision": disposition,
            "reason": reason,
        }
        if disposition == "exclude":
            audit.append(audit_row)
            continue
        bbox = _bbox(raw.get("bbox"))
        core_bbox = _bbox(raw.get("core_bbox")) or bbox
        kind = str(raw.get("representation_kind") or "").strip().lower()
        page_number = int(target["page_number"])
        width, height = page_dimensions[page_number]
        if (
            bbox is None or core_bbox is None or not kind or not _contains(bbox, core_bbox)
            or not _overlaps(bbox, target["bbox"])
            or bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0
            or bbox["bottom_right_x"] > width or bbox["bottom_right_y"] > height
            or _dominant_floor_plan(
                representation_kind=kind, bbox=core_bbox,
                page_dimensions=page_dimensions, page_number=page_number,
            )
        ):
            raise DetectionV8ContractError("V8 Conflict Resolver admission is invalid")
        group_id = _stable_id("V8-I", page_number, bbox)
        if group_id in existing_ids:
            raise DetectionV8ContractError("V8 Conflict Resolver duplicated a Discovery island")
        existing_ids.add(group_id)
        result.append({
            "group_id": group_id,
            "page_number": page_number,
            "bbox": bbox,
            "core_bbox": core_bbox,
            "representation_kind": kind,
            "visual_description": " ".join(str(raw.get("visual_description") or "").split()),
            "reason": reason,
            "evidence_class": "object_evidence",
        })
        audit_row["admitted_group_id"] = group_id
        audit.append(audit_row)
    return sorted(result, key=lambda item: (item["page_number"], item["group_id"])), audit


def normalize_detection_v8_membership_links(
    links: object,
    *,
    object_evidence: list[dict[str, Any]],
    known_source_fact_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate explicit pair links without a render-specific adapter.

    Technical links need two independent evidence types.  A render/photo link
    needs one concrete visual topology or geometry proof and one technical
    endpoint.  All inputs and outputs are sorted before graph construction.
    """
    if not isinstance(links, list):
        raise DetectionV8ContractError("V8 Membership links must be a list")
    kinds = {
        str(view["group_id"]): str(view.get("representation_kind") or "").lower()
        for view in object_evidence
    }
    known_sources = set(known_source_fact_ids or set()) | {
        f"registry_view:{group_id}" for group_id in kinds
    }
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(links):
        if not isinstance(raw, dict):
            rejected.append({"index": index, "reason": "link_not_object"})
            continue
        left, right = sorted((str(raw.get("group_id_a") or ""), str(raw.get("group_id_b") or "")))
        evidence = raw.get("evidence")
        if left == right or left not in kinds or right not in kinds or not isinstance(evidence, list):
            rejected.append({"index": index, "reason": "endpoints_or_evidence_invalid"})
            continue
        pair = (left, right)
        if pair in seen:
            rejected.append({"index": index, "reason": "duplicate_pair"})
            continue
        seen.add(pair)
        normalized_evidence: list[dict[str, Any]] = []
        invalid = False
        for row in evidence:
            if not isinstance(row, dict):
                invalid = True
                break
            evidence_type = str(row.get("evidence_type") or "")
            observation = " ".join(str(row.get("observation") or "").split())
            source_fact_ids = sorted({str(value) for value in row.get("source_fact_ids") or [] if str(value)})
            if (
                evidence_type not in _TECHNICAL_LINK_TYPES
                or not observation
                or not {f"registry_view:{left}", f"registry_view:{right}"}.issubset(source_fact_ids)
                or not set(source_fact_ids).issubset(known_sources)
            ):
                invalid = True
                break
            normalized_evidence.append({
                "evidence_type": evidence_type,
                "observation": observation,
                "source_fact_ids": source_fact_ids,
            })
        if invalid or not normalized_evidence:
            rejected.append({"index": index, "reason": "evidence_not_grounded"})
            continue
        render_endpoints = [group_id for group_id in pair if kinds[group_id] == _RENDER_KIND]
        if render_endpoints:
            if (
                len(render_endpoints) != 1
                or any(item["evidence_type"] not in _RENDER_LINK_TYPES for item in normalized_evidence)
            ):
                rejected.append({"index": index, "reason": "render_link_requires_one_technical_endpoint_and_visual_proof"})
                continue
        elif len({item["evidence_type"] for item in normalized_evidence}) < 2:
            rejected.append({"index": index, "reason": "technical_link_requires_two_independent_evidence_types"})
            continue
        accepted.append({
            "group_id_a": left,
            "group_id_b": right,
            "evidence": sorted(normalized_evidence, key=lambda item: (
                item["evidence_type"], item["observation"], tuple(item["source_fact_ids"]),
            )),
        })
    return sorted(accepted, key=lambda item: (item["group_id_a"], item["group_id_b"])), rejected


def compile_detection_v8_components(
    *,
    object_evidence: list[dict[str, Any]],
    membership_links: list[dict[str, Any]],
) -> tuple[list[list[str]], list[str]]:
    """Construct order-invariant components from accepted V8 links only."""
    group_ids = sorted({str(view["group_id"]) for view in object_evidence})
    kind_by_id = {
        str(view["group_id"]): str(view.get("representation_kind") or "").lower()
        for view in object_evidence
    }
    parent = {group_id: group_id for group_id in group_ids}

    def root(group_id: str) -> str:
        while parent[group_id] != group_id:
            parent[group_id] = parent[parent[group_id]]
            group_id = parent[group_id]
        return group_id

    for link in sorted(membership_links, key=lambda item: (item["group_id_a"], item["group_id_b"])):
        left, right = link["group_id_a"], link["group_id_b"]
        left_root, right_root = root(left), root(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)
    components_by_root: dict[str, list[str]] = {}
    for group_id in group_ids:
        components_by_root.setdefault(root(group_id), []).append(group_id)
    components = [sorted(component) for component in components_by_root.values()]
    retained = [
        component for component in components
        if any(kind_by_id[group_id] != _RENDER_KIND for group_id in component)
    ]
    excluded_renders = sorted(
        group_id
        for component in components
        if all(kind_by_id[group_id] == _RENDER_KIND for group_id in component)
        for group_id in component
    )
    return sorted(retained, key=lambda component: tuple(component)), excluded_renders


def run_detection_v8_pipeline(
    *,
    ocr_package: dict[str, Any] | None,
    source_facts: list[dict[str, Any]],
    page_dimensions: dict[int, tuple[int, int]],
    discover: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    review_membership: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    resolve_conflict: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the complete V8 contract with provider-specific callbacks.

    The visual provider cannot mutate a later stage.  It receives candidates,
    exceptional targets or fixed Object Evidence views and returns data only for
    that one boundary.  Production transport can therefore be changed without
    changing Detection semantics.
    """
    candidates = build_detection_v8_candidate_regions(ocr_package, source_facts)
    object_evidence, exclusions = normalize_detection_v8_discovery(
        discover(deepcopy(candidates)), page_dimensions=page_dimensions,
    )
    coverage = audit_detection_v8_candidate_coverage(
        candidates=candidates, object_evidence=object_evidence, exclusions=exclusions,
    )
    targets = select_detection_v8_conflict_targets(
        candidates=candidates, coverage_audit=coverage,
    )
    resolver_audit: list[dict[str, Any]] = []
    if targets and resolve_conflict is not None:
        decisions = [resolve_conflict(deepcopy(target)) for target in targets]
        object_evidence, resolver_audit = apply_detection_v8_conflict_decisions(
            object_evidence=object_evidence,
            targets=targets,
            decisions=decisions,
            page_dimensions=page_dimensions,
        )
    raw_links = review_membership(deepcopy(object_evidence))
    membership_links, rejected_links = normalize_detection_v8_membership_links(
        raw_links,
        object_evidence=object_evidence,
        known_source_fact_ids={
            str(fact.get("fact_id") or "")
            for fact in source_facts
            if isinstance(fact, dict) and str(fact.get("fact_id") or "")
        },
    )
    components, excluded_renders = compile_detection_v8_components(
        object_evidence=object_evidence, membership_links=membership_links,
    )
    return {
        "version": "detection_v8_stage_separated",
        "candidate_regions": candidates,
        "discovery": {
            "object_evidence": object_evidence,
            "excluded": exclusions,
            "candidate_coverage": coverage,
        },
        "conflict_resolver": {
            "attempted": bool(targets and resolve_conflict is not None),
            "targets": targets,
            "decisions": resolver_audit,
        },
        "membership": {
            "accepted_links": membership_links,
            "rejected_links": rejected_links,
        },
        "components": components,
        "excluded_unattached_presentation_renders": excluded_renders,
    }
