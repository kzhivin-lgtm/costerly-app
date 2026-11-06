"""V3.5 diagnostic: fixed bay membership, model-associated width spans only.

This does not certify or repair the failed source Parts result. No new runtime
stage, parts compiler, or second width allocator is introduced.
"""
from use_cases.estimation_cb_bays import _fields, _ids, _list
from use_cases.estimation_cb_parts import positive
from use_cases.estimation_cb_spans import _text, _unit, resolve_cb_span_widths


def validate_frozen_topology(topology, *, scope):
    _fields(topology, "blocks", "frozen topology")
    plan = {b["id"]: b for b in scope["planner"]["blocks"] + scope["planner"]["shared_parts"]}
    _list(topology["blocks"], "frozen blocks", len(plan), len(plan))
    seen = set()
    for block in topology["blocks"]:
        _fields(block, "id kind bays front_ids", "frozen block")
        bid = block["id"]
        if not isinstance(bid, str) or bid not in plan or bid in seen:
            raise ValueError("duplicate or foreign frozen block")
        seen.add(bid)
        if block["kind"] == "explicit":
            if block["bays"] != []:
                raise ValueError("explicit block cannot acquire bays")
            _ids(block["front_ids"], plan[bid].get("front_ids", []))
            continue
        if block["kind"] != "carcass" or block["front_ids"] != []:
            raise ValueError("invalid frozen carcass")
        _list(block["bays"], "frozen bays", 1, 30)
        ids, fronts = set(), []
        for bay in block["bays"]:
            _fields(bay, "id front_ids", "frozen bay")
            _text(bay["id"], "bay ID", 80)
            if bay["id"] in ids:
                raise ValueError("duplicate frozen bay")
            ids.add(bay["id"])
            _list(bay["front_ids"], "bay fronts")
            fronts.extend(bay["front_ids"])
        _ids(fronts, plan[bid].get("front_ids", []))


def freeze_cb_topology(raw, *, scope):
    """Whitelist identities from original V3.3, never copy dimension estimates."""
    _fields(raw, "blocks", "source V3.3 reply")
    _list(raw["blocks"], "source blocks", 1, 300)
    blocks = []
    for block in raw["blocks"]:
        if not isinstance(block, dict):
            raise ValueError("source block required")
        if block.get("kind") == "carcass":
            _fields(block, "id kind unit height depth thickness_mm assumptions bays", "source carcass")
            _list(block["bays"], "source bays", 1, 30)
            bays = []
            for bay in block["bays"]:
                _fields(bay, "id width shelves fronts", "source bay")
                _list(bay["fronts"], "source fronts")
                for front in bay["fronts"]:
                    _fields(front, "id height body_height", "source front")
                bays.append({"id": bay["id"], "front_ids": [f["id"] for f in bay["fronts"]]})
            blocks.append({"id": block["id"], "kind": "carcass", "bays": bays, "front_ids": []})
        elif block.get("kind") == "explicit":
            _fields(block, "id kind unit size front_ids assumptions parts", "source explicit block")
            blocks.append({"id": block["id"], "kind": "explicit", "bays": [], "front_ids": list(block["front_ids"])})
        else:
            raise ValueError("unsupported frozen block kind")
    topology = {"blocks": blocks}
    validate_frozen_topology(topology, scope=scope)
    return topology


def resolve_frozen_widths(response, *, scope):
    _fields(response, "width_spans unanchored_widths", "width-only response")
    topology = scope["frozen_topology"]
    validate_frozen_topology(topology, scope=scope)
    # Minimal internal scaffold for the existing allocator. Never a Parts BOM.
    blocks, bays = [], {}
    for block in topology["blocks"]:
        scaffold = {"id": block["id"], "kind": block["kind"], "unit": "mm", "bays": []}
        for bay in block["bays"]:
            entry = {"id": bay["id"], "width": None}
            scaffold["bays"].append(entry)
            bays[(block["id"], bay["id"])] = entry
        blocks.append(scaffold)
    _list(response["unanchored_widths"], "unanchored widths", 0, 9000)
    fallbacks = {}
    for fallback in response["unanchored_widths"]:
        _fields(fallback, "block_id bay_id width unit reason", "unanchored width")
        _text(fallback["block_id"], "fallback block ID", 80)
        _text(fallback["bay_id"], "fallback bay ID", 80)
        key = (fallback["block_id"], fallback["bay_id"])
        if key not in bays or key in fallbacks:
            raise ValueError("foreign or duplicate unanchored bay")
        _text(fallback["reason"], "fallback reason")
        width = positive(fallback["width"], "fallback width") * _unit(fallback["unit"])
        if width > 30000:
            raise ValueError("fallback exceeds furniture bound")
        bays[key]["width"] = width
        fallbacks[key] = fallback["reason"]
    _, audit = resolve_cb_span_widths({"blocks": blocks, "width_spans": response["width_spans"]}, scope=scope)
    for bay in audit["bay_widths"]:
        key = (bay["block_id"], bay["bay_id"])
        if key in fallbacks:
            bay["reason"] = fallbacks[key]
    return audit
