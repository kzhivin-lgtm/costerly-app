"""V3.4: conserve model-associated dimension spans across physical bay intervals.

The association with drawing endpoints remains model-authored/unverified.
This resolver allocates known totals, never claims to prove visual association.
The intermediate V3.3 representation and provenance stay separate from raw.
"""
from copy import deepcopy
import math

from use_cases.estimation_cb_parts import positive
from use_cases.estimation_cb_bays import _fields, _list, compose_cb_bay_parts


def _unit(unit):
    if not isinstance(unit, str) or unit not in {"mm", "cm", "m"}:
        raise ValueError("explicit mm/cm/m unit required")
    return {"mm": 1, "cm": 10, "m": 1000}[unit]


def _text(value, label, limit=300):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"bounded nonempty {label} required")


def resolve_cb_span_widths(response, *, scope):
    _fields(response, "width_spans blocks", "CB Parts V3.4")
    _list(response["width_spans"], "width spans")
    _list(response["blocks"], "blocks", 1, 300)
    blocks = deepcopy(response["blocks"])
    plan = scope["planner"]["blocks"] + scope["planner"]["shared_parts"]
    expected = {b["id"] for b in plan}
    known_views = {v for b in plan for v in b.get("view_ids", [])}
    known_views.update(i["view_id"] for i in scope["front"].get("island_types", []))
    seen_blocks, bays = set(), {}
    for block in blocks:
        if not isinstance(block, dict) or not isinstance(block.get("id"), str):
            raise ValueError("block ID required")
        bid = block["id"]
        if bid not in expected or bid in seen_blocks:
            raise ValueError("duplicate or foreign block")
        seen_blocks.add(bid)
        if block.get("kind") == "carcass":
            factor = _unit(block.get("unit"))
            _list(block.get("bays"), "bays", 1, 30)
            for bay in block["bays"]:
                if not isinstance(bay, dict):
                    raise ValueError("bay object required")
                _text(bay.get("id"), "bay ID", 80)
                key = (bid, bay["id"])
                if key in bays:
                    raise ValueError("duplicate bay ID")
                bays[key] = (bay, factor)
    if seen_blocks != expected:
        raise ValueError("every planned block required")
    assigned, span_ids, traces = {}, set(), []
    for span in response["width_spans"]:
        _fields(span, "id view_id value unit source_label endpoints_1000 members", "width span")
        _text(span["id"], "span ID", 80)
        if span["id"] in span_ids:
            raise ValueError("duplicate span ID")
        span_ids.add(span["id"])
        if not isinstance(span["view_id"], str) or span["view_id"] not in known_views:
            raise ValueError("unknown span view")
        total = positive(span["value"], "span value") * _unit(span["unit"])
        if total > 30000:
            raise ValueError("span exceeds furniture bound")
        _text(span["source_label"], "source label")
        ends = span["endpoints_1000"]
        if (not isinstance(ends, list) or len(ends) != 4 or
            any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1000 for v in ends)
            or ends[0] >= ends[2]):
            raise ValueError("left-to-right normalized span endpoints required")
        _list(span["members"], "span members", 1, 100)
        weights = []
        for member in span["members"]:
            _fields(member, "block_id bay_id weight label", "span member")
            _text(member["label"], "interval label")
            weights.append(positive(member["weight"], "interval weight"))
        weight_total = sum(weights)
        if not math.isfinite(weight_total):
            raise ValueError("finite weight sum required")
        allocated, member_traces, bay_count = 0.0, [], 0
        for index, (member, weight) in enumerate(zip(span["members"], weights)):
            # Last interval receives only floating point residual, not a model
            # geometry repair. No independent rounded estimates are normalized.
            width = total - allocated if index == len(weights) - 1 else total * (weight / weight_total)
            if not math.isfinite(width) or width < 1:
                raise ValueError("allocated coarse interval must be at least 1 mm")
            allocated += width
            bid, bay_id = member["block_id"], member["bay_id"]
            if bid is None and bay_id is None:
                pass  # Explicit non-bay interval, retained in the span audit.
            else:
                if not isinstance(bid, str) or not isinstance(bay_id, str) or (bid, bay_id) not in bays:
                    raise ValueError("span must reference an existing carcass bay")
                key = (bid, bay_id)
                if key in assigned:
                    raise ValueError("bay allocated more than once")
                bay, factor = bays[key]
                if bay.get("width", "missing") is not None:
                    raise ValueError("span-allocated bay width must be null")
                bay["width"] = width / factor
                assigned[key] = {"block_id": bid, "bay_id": bay_id, "width_mm": width,
                    "basis": "allocated_from_model_associated_span", "span_id": span["id"]}
                bay_count += 1
            member_traces.append({**member, "width_mm": width})
        if not bay_count:
            raise ValueError("span must allocate at least one bay")
        traces.append({"id": span["id"], "view_id": span["view_id"], "source_label": span["source_label"],
            "endpoints_1000": list(ends), "span_mm": total, "allocated_mm": allocated,
            "association_verified": False, "members": member_traces})
    widths = []
    for key, (bay, factor) in bays.items():
        if key in assigned:
            widths.append(assigned[key])
        else:
            width = positive(bay.get("width"), "unanchored bay width") * factor
            widths.append({"block_id": key[0], "bay_id": key[1], "width_mm": width,
                "basis": "unanchored_model_assumption", "span_id": None})
    return {"blocks": blocks}, {"spans": traces, "bay_widths": widths}


def compose_cb_span_parts(response, *, scope):
    resolved, audit = resolve_cb_span_widths(response, scope=scope)
    result = compose_cb_bay_parts(resolved, scope=scope)
    result["width_allocation"] = audit
    return result
