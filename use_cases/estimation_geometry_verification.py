"""Deterministic trigger and patch boundary for one conditional V6 review.

This detects contradictions, not every plausible semantic mistake. A second
model reading never certifies physical ownership or changes locked materials.
"""
from copy import deepcopy
from hashlib import sha256
import json
import math

from use_cases.estimation_dimension_relations import dimension_axis_candidates

VERIFICATION_VERSION = "geometry_verification_v1"
MAX_TARGETS = 8
MAX_PAGES = 3
MAX_CANDIDATES_PER_TARGET = 24
MAX_CONTEXT_CHARS = 20000


def fingerprint(extraction, scope):
    payload = {k: v for k, v in extraction.items() if k != "geometry_verification"}
    return sha256(json.dumps([payload, scope], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def collect_conflicts(extraction, scope):
    evidence = scope.get("evidence_map") or {}
    if not scope.get("construction_version") or not evidence:
        return []
    numbers = {n["dimension_id"]: n for n in evidence["dimensions"]}
    axes = dimension_axis_candidates(evidence)
    by_ref = {}
    for did, number in numbers.items():
        for ref in number["evidence_refs"]:
            by_ref.setdefault(ref, []).append(did)
    locked_views = {v["view_id"]: v for v in evidence["view_readings"]}
    emitted_views = {v["view_id"]: v for v in extraction.get("view_interpretations") or []}
    bindings = {}
    for binding in extraction.get("dimension_bindings") or []:
        bindings.setdefault((binding.get("assembly_id"), binding.get("axis")), []).append(binding)
    targets = []
    zones = {z["scope_id"]: z for z in scope["zones"]}
    for assembly in extraction.get("assemblies") or []:
        aid = assembly.get("assembly_id")
        if aid not in zones:
            continue  # Existing scope validation owns foreign assemblies.
        for axis, dimension in (assembly.get("dimensions") or {}).items():
            if axis not in {"width", "height", "depth"} or not isinstance(dimension, dict):
                continue
            claimed = set()
            reasons = []
            for binding in bindings.get((aid, axis), []):
                did = binding.get("dimension_id")
                if did in numbers:
                    claimed.add(did)
                vid = binding.get("view_id")
                if vid in locked_views and vid in emitted_views:
                    old, new = locked_views[vid], emitted_views[vid]
                    if (old["projection"], old.get("horizontal_axis")) != (new["projection"], new.get("horizontal_axis")):
                        reasons.append("calculation_changed_locked_view")
            if dimension.get("basis") == "source":
                for ref in dimension.get("evidence_refs") or []:
                    claimed.update(by_ref.get(ref, []))
            for did in claimed:
                if axes[did] and axis not in axes[did]:
                    reasons.append("source_axis_mismatch")
            # Derived arithmetic cannot be compared with one operand.
            if dimension.get("basis") == "source" and claimed:
                unit = dimension.get("unit") or (extraction.get("document_unit") or {}).get("unit")
                try:
                    value = float(dimension["value"]) * {"mm": 1, "cm": 10, "m": 1000}[unit]
                except (TypeError, ValueError, KeyError):
                    value = float("nan")
                if not math.isfinite(value) or not any(numbers[did].get("interpreted_value_mm") is not None
                    and abs(value - numbers[did]["interpreted_value_mm"]) <= max(3, abs(value) * .003) for did in claimed):
                    reasons.append("source_numeric_mismatch")
            if reasons:
                candidates = [{"dimension_id": did, "value_mm": n["interpreted_value_mm"],
                    "view_ids": n["view_candidates"], "page_number": n["page_number"]}
                    for did, n in numbers.items() if axes[did] == [axis] and n.get("interpreted_value_mm") is not None]
                targets.append({"assembly_id": aid, "axis": axis, "current": deepcopy(dimension),
                    "role": zones[aid]["assembly_role"], "description": zones[aid].get("semantic_role", ""),
                    "reasons": sorted(set(reasons)), "claimed_dimension_ids": sorted(claimed), "candidates": candidates})
    return targets


def apply_review(extraction, scope, targets, response):
    """Atomic, allowlisted patches. No free numeric or material substitutions."""
    if not isinstance(response, dict) or set(response) != {"patches", "unresolved"}:
        raise ValueError("review requires patches and unresolved only")
    expected = {(t["assembly_id"], t["axis"]): t for t in targets}
    seen, patches = set(), []
    for key in ("patches", "unresolved"):
        if not isinstance(response[key], list):
            raise ValueError("review lists required")
        for item in response[key]:
            allowed = {"assembly_id", "axis", "reason"} | ({"dimension_id"} if key == "patches" else set())
            if not isinstance(item, dict) or set(item) != allowed:
                raise ValueError("review cannot change fields outside the patch contract")
            target = (item["assembly_id"], item["axis"])
            if target not in expected or target in seen:
                raise ValueError("review has an unknown or duplicate target")
            if not isinstance(item["reason"], str) or not 1 <= len(item["reason"].strip()) <= 600:
                raise ValueError("review needs a bounded decision rationale")
            seen.add(target)
            if key == "patches":
                candidate = next((c for c in expected[target]["candidates"] if c["dimension_id"] == item["dimension_id"]), None)
                if candidate is None or not math.isfinite(candidate["value_mm"]) or candidate["value_mm"] <= 0:
                    raise ValueError("review selected an unavailable source/axis candidate")
                patches.append((item, candidate))
    if seen != set(expected):
        raise ValueError("review must explicitly resolve or leave every target unresolved")
    result = deepcopy(extraction)
    applied = []
    for item, candidate in patches:
        assembly = next(a for a in result["assemblies"] if a["assembly_id"] == item["assembly_id"])
        before = deepcopy(assembly["dimensions"][item["axis"]])
        assembly["dimensions"][item["axis"]] = {"value": candidate["value_mm"], "unit": "mm",
            "basis": "assumption", "unit_basis": "review_source_candidate",
            "evidence_refs": [], "assumption_reason": "Targeted visual review, physical ownership unverified: " + item["reason"]}
        result["dimension_bindings"] = [b for b in result.get("dimension_bindings") or []
            if (b.get("assembly_id"), b.get("axis")) != (item["assembly_id"], item["axis"])]
        applied.append({**item, "before": before, "after_mm": candidate["value_mm"],
                        "basis": "visual_estimating_assumption_not_certified_source"})
    remaining = collect_conflicts(result, scope)
    patched = {(p["assembly_id"], p["axis"]) for p in applied}
    if any((t["assembly_id"], t["axis"]) in patched for t in remaining):
        raise ValueError("review patch retained a detected contradiction")
    return result, applied, remaining
