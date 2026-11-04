"""Bounded geometric consistency candidates, never physical-ownership proof.

Only printed numbers are used. Pixel spans check correspondence, not new
dimensions. No projection, unit, material or object identity is inferred here.
"""
from itertools import combinations
from math import isclose
from copy import deepcopy

MAX_RELATION_SEGMENTS = 256
MAX_RELATIONS = 80
MAX_ASSIGNMENT_STATES = 4096


def dimension_axis_candidates(evidence: dict) -> dict[str, list[str]]:
    """Candidate axes from existing view assumptions, not component ownership."""
    from use_cases.estimation_2vn_resolver import _expected_axis
    views = {v["view_id"]: v for v in evidence["view_readings"]}
    axes = {}
    for number in evidence["dimensions"]:
        candidates = set()
        for vid in number["view_candidates"]:
            if vid not in views:
                continue
            view = views[vid]
            for line in number["line_candidates"]:
                axis = _expected_axis(projection=view["projection"], orientation=line["orientation"],
                                      top_plan_axis=view.get("horizontal_axis"))
                if axis is not None:
                    candidates.add(axis)
        axes[number["dimension_id"]] = sorted(candidates)
    return axes


def reconcile_projection_assumptions(evidence: dict, *, reobserve_ownership: bool = False) -> dict:
    """Diagnostic-only minimal-edit hypotheses, never source certification.

    Bounded exhaustive search is required here: arc consistency alone cannot
    establish uniqueness. Ambiguity, truncation or a non-orthographic visual
    reading preserves the original map. No numeric value is altered.
    """
    result = deepcopy(evidence)
    graph = dimension_relations(evidence)
    views = {v["view_id"]: v for v in evidence["view_readings"]}
    domains = {v["view_id"]: v["axis_candidates"] for v in graph["projection_hypotheses"]["views"]}
    audit = {"status": "not_applied", "authority": "estimating_assumption_not_source",
             "graph": graph, "changes": []}
    result["projection_assumption_audit"] = audit
    if (graph["truncated"] or len(graph["relations"]) < 2 or not domains
            or any(not d for d in domains.values())
            or any(views.get(vid, {}).get("projection") not in {"front_elevation", "side_elevation", "top_plan", "section"} for vid in domains)):
        audit["reason"] = "Insufficient, ambiguous or non-orthographic evidence; keep visual readings."
        return result
    for vid in domains:
        if views[vid]["projection"] == "section":
            # Existing 2VN section contract has vertical=height. Its missing
            # horizontal axis may be width/depth, never silently a top view.
            domains[vid] = [c for c in domains[vid] if c["vertical_axis"] == "height"]
    edges = [(a, b) for r in graph["relations"] for a, b in combinations(r["members"], 2)
             if a["view_id"] != b["view_id"]]
    ids = sorted(domains, key=lambda vid: len(domains[vid]))
    best, answers, states = float("inf"), [], 0

    def visit(assigned, cost):
        nonlocal best, states, answers
        states += 1
        if states > MAX_ASSIGNMENT_STATES or cost > best:
            return
        for a, b in edges:
            if a["view_id"] in assigned and b["view_id"] in assigned:
                if assigned[a["view_id"]][a["orientation"] + "_axis"] != assigned[b["view_id"]][b["orientation"] + "_axis"]:
                    return
        if len(assigned) == len(ids):
            if cost < best:
                best, answers = cost, []
            answers.append(deepcopy(assigned))
            return
        vid = ids[len(assigned)]
        original = views[vid]
        for candidate in domains[vid]:
            changed = candidate["projection"] != original["projection"] or (
                candidate["projection"] == "top_plan" and candidate["horizontal_axis"] != original.get("horizontal_axis"))
            if original["projection"] == "section":
                # A section with no declared cut axis is an unanchored
                # orthographic hypothesis, not a known front/side direction.
                changed = bool(original.get("horizontal_axis") and candidate["horizontal_axis"] != original["horizontal_axis"])
            assigned[vid] = candidate
            visit(assigned, cost + int(changed))
            del assigned[vid]

    visit({}, 0)
    audit.update(search_states=states, minimum_changed_views=best if answers else None, best_assignment_count=len(answers))
    if states > MAX_ASSIGNMENT_STATES or not answers:
        audit["reason"] = "Search incomplete or inconsistent; keep visual readings."
        return result
    for vid in ids:
        choices = {tuple(a[vid][k] for k in ("projection", "horizontal_axis", "vertical_axis")) for a in answers}
        if len(choices) != 1:
            continue
        projection, horizontal, _ = choices.pop()
        original = views[vid]
        if projection == original["projection"] and (projection != "top_plan" or horizontal == original.get("horizontal_axis")):
            continue
        replacement = {"view_id": vid, "projection": projection, "horizontal_axis": horizontal}
        audit["changes"].append({"original": deepcopy(original), "assumed": replacement,
            "reason": "Unique minimum-edit cross-view assignment under the graph's explicit drafting/correspondence assumptions."})
        next(v for v in result["view_readings"] if v["view_id"] == vid).update(replacement)
        for reading in result["dimension_readings"]:
            if reading["view_id"] == vid:
                # Changing projection invalidates prior physical ownership.
                # Calculation may estimate anew, but may not reuse it as proof.
                reading["prior_visual_ownership"] = {key: reading[key] for key in ("scope_id", "axis")}
                reading.update(scope_id=None, axis=None, ownership_status="conflicting",
                    validation="prior_ownership_invalidated_by_projection_assumption")
    if audit["changes"]:
        audit["status"] = "applied_as_assumption"
        audit["section_note"] = "Sections retain the existing 2VN vertical=height convention; principal-plane direction is an assumption, not an oblique-cut proof."
        result["status"] = "needs_review"
        if reobserve_ownership:
            # Joint view reasoning can invalidate ownership in OTHER views.
            # Preserve the original outside Calculation transport so it cannot
            # anchor a fresh measurement. Source numbers/views remain intact.
            result["superseded_interpretation"] = {key: deepcopy(evidence.get(key))
                for key in ("dimension_readings", "conflicts", "uninterpreted_dimension_ids")}
            result["dimension_readings"] = []
            result["conflicts"] = []
            result["uninterpreted_dimension_ids"] = sorted(n["dimension_id"] for n in evidence["dimensions"])
            audit["ownership_action"] = "All prior physical ownership withdrawn for fresh Calculation; source numbers unchanged."
    return result


def projection_hypotheses(relations: list[dict]) -> dict:
    """Arc consistency under stated drafting assumptions, not a classifier.

    Keeping only supported domains is conservative: a surviving domain is not
    proof of a globally realizable construction, nor proof that input matches
    refer to the same physical span. Rotated elevations invalidate this model.
    """
    choices = (
        ("front_elevation", "width", "height"),
        ("side_elevation", "depth", "height"),
        ("top_plan", "width", "depth"),
        ("top_plan", "depth", "width"),
    )
    edges = []
    for relation in relations:
        for first, second in combinations(relation["members"], 2):
            if first["view_id"] != second["view_id"]:
                edges.append((first["view_id"], 1 if first["orientation"] == "horizontal" else 2,
                              second["view_id"], 1 if second["orientation"] == "horizontal" else 2))
    domains = {vid: set(choices) for edge in edges for vid in (edge[0], edge[2])}
    pairs = {}
    for a, ai, b, bi in edges:
        if a > b:
            a, ai, b, bi = b, bi, a, ai
        pairs.setdefault((a, b), set()).add((ai, bi))
    changed = True
    while changed:
        changed = False
        for (a, b), constraints in pairs.items():
            compatible = [(left, right) for left in domains[a] for right in domains[b]
                          if all(left[ai] == right[bi] for ai, bi in constraints)]
            for vid, index in ((a, 0), (b, 1)):
                supported = {pair[index] for pair in compatible}
                if supported != domains[vid]:
                    domains[vid] = supported
                    changed = True
    return {"status": "inconsistent_assumptions" if any(not d for d in domains.values()) else "conditional_candidates",
        "assumptions": ["Linked printed spans refer to the same physical direction, not coincidental numbers.",
            "Participating views are orthographic, not isometric, oblique or perspective.",
            "Elevations are upright on the page; a rotated elevation invalidates these domains."],
        "views": [{"view_id": vid,
            "projection_candidates": sorted({c[0] for c in domain}),
            "axis_candidates": [{"projection": c[0], "horizontal_axis": c[1], "vertical_axis": c[2]}
                                for c in sorted(domain)]} for vid, domain in sorted(domains.items())],
        "authority": "conditional_geometric_hypothesis_not_source_fact"}


def dimension_relations(evidence: dict) -> dict:
    frames = {p["page_number"]: p["coordinate_frame"] for p in evidence["pages"]}
    segments = []
    for number in evidence["dimensions"]:
        frame = frames.get(number["page_number"])
        value = number.get("interpreted_value_mm")
        # Multiple nearby views are not a resolved locator. Do not pick one.
        if not frame or not value or value <= 0 or len(number["view_candidates"]) != 1:
            continue
        for line in number["line_candidates"]:
            crossings = line.get("endpoint_crossing_candidates") or []
            if len(crossings) != 2 or not all(crossings) or line["orientation"] not in {"horizontal", "vertical"}:
                continue
            axis = "x" if line["orientation"] == "horizontal" else "y"
            a, b = sorted((line["start"][axis], line["end"][axis]))
            segments.append({"dimension_id": number["dimension_id"], "candidate_id": line["segment_id"],
                "view_id": number["view_candidates"][0], "orientation": line["orientation"],
                "page": number["page_number"], "a": a, "b": b, "value": value,
                "tolerance": max(frame) * .002})
    truncated = len(segments) > MAX_RELATION_SEGMENTS
    segments = segments[:MAX_RELATION_SEGMENTS]
    relations, seen = [], set()

    def locator(s):
        return {key: s[key] for key in ("dimension_id", "candidate_id", "view_id", "orientation")}

    def emit(kind, items):
        # Distinct line interpretations must not be collapsed into whichever
        # candidate was encountered first. Conflicting alternatives abstain.
        key = (kind, tuple((s["dimension_id"], s["candidate_id"]) for s in items))
        if key not in seen:
            seen.add(key)
            relations.append({"relation": kind, "members": [locator(s) for s in items],
                "status": "geometric_correspondence_candidate_not_physical_ownership"})

    for left, right in combinations(segments, 2):
        if left["page"] != right["page"] or left["dimension_id"] == right["dimension_id"]:
            continue
        tolerance = max(left["tolerance"], right["tolerance"])
        if (left["view_id"] != right["view_id"]
                and isclose(left["value"], right["value"], rel_tol=.001, abs_tol=.1)
                and abs((left["b"] - left["a"]) - (right["b"] - right["a"])) <= tolerance):
            emit("equal_printed_value_and_span", [left, right])
        if left["orientation"] != right["orientation"]:
            continue
        first, second = sorted((left, right), key=lambda s: s["a"])
        if abs(first["b"] - second["a"]) > tolerance:
            continue
        for total in segments:
            if (total["page"] == first["page"] and total["orientation"] == first["orientation"]
                    and total["dimension_id"] not in {first["dimension_id"], second["dimension_id"]}
                    and abs(total["a"] - first["a"]) <= tolerance
                    and abs(total["b"] - second["b"]) <= tolerance
                    and isclose(total["value"], first["value"] + second["value"], rel_tol=.001, abs_tol=.1)):
                emit("aligned_printed_sum_total_then_parts", [total, first, second])
    return {"relations": relations[:MAX_RELATIONS], "truncated": truncated or len(relations) > MAX_RELATIONS,
        "projection_hypotheses": projection_hypotheses(relations[:MAX_RELATIONS]),
        "limitations": ["Equal numbers and aligned boundaries can be coincidental, verify the depicted physical span.",
            "These relations do not identify front/top/side, certify ownership, or measure missing dimensions.",
            "Different page scales, view translations and ambiguous endpoint candidates can leave valid relations absent."]}
