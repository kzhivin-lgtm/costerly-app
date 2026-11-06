"""CB Parts V3.3: explicit bay topology -> coarse parts, no model repair.

Only straight rectangular carcasses use these construction rules. Explicit
geometry remains model-authored and visibly unverified. Raw replies are never
modified. Front type/membership come from the saved, fallible upstream scope.
"""
from use_cases.estimation_cb_parts import positive, compose_cb_sized_parts
from use_cases.estimation_structural_bom import _slide_depth_mm


def _fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError(f"invalid {label} fields")


def _list(value, label, minimum=0, maximum=100):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"bounded {label} list required")


def _ids(value, expected):
    _list(value, "front IDs")
    if any(not isinstance(x, str) for x in value) or len(set(value)) != len(value) or set(value) != set(expected):
        raise ValueError("front IDs must cover exactly the assigned block fronts")


def compose_cb_bay_parts(response, *, scope):
    _fields(response, "blocks", "CB Parts V3.3")
    plan = {b["id"]: b for b in scope["planner"]["blocks"] + scope["planner"]["shared_parts"]}
    _list(response["blocks"], "blocks", len(plan), len(plan))
    types = {}
    for group in scope["front"]["front_groups"]:
        for front in group["fronts"]:
            if front["id"] in types:
                raise ValueError("duplicate upstream front ID")
            types[front["id"]] = group["type"]
    converted, traces, seen = [], {}, set()
    for block in response["blocks"]:
        if not isinstance(block, dict) or not isinstance(block.get("id"), str):
            raise ValueError("block ID required")
        bid = block["id"]
        if bid not in plan or bid in seen:
            raise ValueError("duplicate or foreign block")
        seen.add(bid)
        expected = plan[bid].get("front_ids", [])
        if block.get("kind") == "explicit":
            _fields(block, "id kind unit size front_ids assumptions parts", "explicit block")
            _ids(block["front_ids"], expected)
            converted.append({k: v for k, v in block.items() if k not in {"kind", "front_ids"}})
            traces[bid] = {"mode": "explicit_model_geometry", "front_ids": list(block["front_ids"])}
            continue
        _fields(block, "id kind unit height depth thickness_mm assumptions bays", "carcass block")
        if block["kind"] != "carcass":
            raise ValueError("unknown block kind")
        unit = block["unit"]
        if not isinstance(unit, str) or unit not in {"mm", "cm", "m"}:
            raise ValueError("explicit unit required")
        factor = {"mm": 1, "cm": 10, "m": 1000}[unit]
        height, depth = (positive(block[k], k) * factor for k in ("height", "depth"))
        if max(height, depth) > 30000:
            raise ValueError("carcass exceeds furniture bound")
        thickness = block["thickness_mm"]
        if thickness is not None and positive(thickness, "thickness") > 500:
            raise ValueError("thickness exceeds bound")
        _list(block["bays"], "bays", 1, 30)
        bays, front_ids, bay_ids = [], [], set()
        for bay in block["bays"]:
            _fields(bay, "id width shelves fronts", "bay")
            if not isinstance(bay["id"], str) or not bay["id"].strip() or len(bay["id"]) > 80 or bay["id"] in bay_ids:
                raise ValueError("unique bounded bay ID required")
            bay_ids.add(bay["id"])
            width = positive(bay["width"], "bay width") * factor
            if type(bay["shelves"]) is not int or not 0 <= bay["shelves"] <= 100:
                raise ValueError("bounded nonnegative shelf count required")
            _list(bay["fronts"], "bay fronts")
            fronts = []
            for front in bay["fronts"]:
                _fields(front, "id height body_height", "bay front")
                fid = front["id"]
                if not isinstance(fid, str) or fid not in expected or fid not in types:
                    raise ValueError("foreign bay front")
                kind = types[fid]
                if kind not in {"hinged", "lift_up", "drawer"}:
                    raise ValueError("unsupported upstream front type")
                fh = positive(front["height"], "front height") * factor
                if kind == "drawer":
                    body = positive(front["body_height"], "drawer body height") * factor
                    if body > fh:
                        raise ValueError("drawer body exceeds facade height")
                else:
                    if front["body_height"] is not None:
                        raise ValueError("non-drawer body height must be null")
                    body = None
                fronts.append({"id": fid, "type": kind, "height_mm": fh, "body_height_mm": body})
                front_ids.append(fid)
            if sum(f["height_mm"] for f in fronts) > height + 1:
                raise ValueError(f"{bid}/{bay['id']}: stacked front heights exceed carcass height")
            bays.append({"id": bay["id"], "width_mm": width, "shelves": bay["shelves"], "fronts": fronts,
                "has_drawers": any(f["type"] == "drawer" for f in fronts)})
        _ids(front_ids, expected)
        width = sum(b["width_mm"] for b in bays)
        if width > 30000:
            raise ValueError("summed carcass width exceeds furniture bound")
        # Group equal geometry only; explicit assumptions remain separate from raw.
        rows = {}
        def add(name, qty, length, breadth):
            if not qty:
                return
            key = (name, round(length, 3), round(breadth, 3))
            if key not in rows:
                rows[key] = {"name": name, "quantity": 0, "role": "panel", "size": list(key[1:]),
                    "thickness_mm": thickness, "approximate": True}
            rows[key]["quantity"] += qty
        add("Carcass side wall", 2, height, depth)
        add("Carcass top", 1, width, depth)
        add("Carcass bottom", 1, width, depth)
        add("Back panel", 1, width, height)
        boundaries = []
        for left, right in zip(bays, bays[1:]):
            if left["has_drawers"] or right["has_drawers"]:
                add("Shared mounting partition", 1, height, depth)
                boundaries.append([left["id"], right["id"]])
        for bay in bays:
            bw = bay["width_mm"]
            add("Shelf", bay["shelves"], bw, depth)
            for front in bay["fronts"]:
                label = {"hinged": "Hinged door", "lift_up": "Lift-up front", "drawer": "Drawer front"}[front["type"]]
                add(label, 1, bw, front["height_mm"])
                if front["type"] == "drawer":
                    drawer_depth = _slide_depth_mm(depth)
                    add("Drawer body side", 2, drawer_depth, front["body_height_mm"])
                    add("Drawer body end panel", 2, bw, front["body_height_mm"])
                    add("Drawer bottom", 1, bw, drawer_depth)
        converted.append({"id": bid, "unit": "mm", "size": [width, height, depth],
            "assumptions": block["assumptions"], "parts": list(rows.values())})
        traces[bid] = {"mode": "derived_straight_carcass", "bays": bays,
            "width_sum_mm": width, "partition_boundaries": boundaries,
            "construction_basis": "coarse rectangular carcass with full top/bottom/back; not source-proven"}
    result = compose_cb_sized_parts({"blocks": converted}, scope=scope)
    for block in result["blocks"]:
        block["derivation"] = traces[block["id"]]
        if traces[block["id"]]["mode"] == "derived_straight_carcass":
            for part in block["parts"]:
                part["drawer_depth_derived"] = part["name"] in {"Drawer body side", "Drawer bottom"}
    return result
