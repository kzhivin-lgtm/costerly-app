"""Recover a visible fixed shelf stack when its render and native elevation agree."""

from collections import deque
from io import BytesIO
from statistics import median

from PIL import Image

from use_cases.estimation_cb_geometry_parts import dimension, part
from use_cases.estimation_v9_inventory import page_box, refresh_source_coverage


ROLE = "fixed_open_shelf"


def _regions(image, box):
    """Flood-fill faces bounded by the ink in a small rendering crop."""
    w, h = image.size
    l, t, r, b = box
    x0, y0 = max(0, int(l - (r - l))), max(0, int(t - .35 * (b - t)))
    x1, y1 = min(w, int(r + (r - l))), min(h, int(b + .35 * (b - t)))
    if x1 <= x0 or y1 <= y0 or (x1 - x0) * (y1 - y0) > 220_000:
        return
    crop = image.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    mask = bytearray(crop.point(lambda value: int(value > 62)).tobytes())
    for start in range(len(mask)):
        if not mask[start]:
            continue
        mask[start] = 0
        queue = deque([start])
        points = []
        while queue:
            i = queue.popleft()
            y, x = divmod(i, cw)
            points.append((x, y))
            for neighbor, valid in ((i - 1, x > 0), (i + 1, x < cw - 1),
                                    (i - cw, y > 0), (i + cw, y < ch - 1)):
                if valid and mask[neighbor]:
                    mask[neighbor] = 0
                    queue.append(neighbor)
        if len(points) < 70:
            continue
        left = min(x for x, _ in points)
        right = max(x for x, _ in points)
        top = min(y for _, y in points)
        bottom = max(y for _, y in points)
        if left == 0 or top == 0 or right == cw - 1 or bottom == ch - 1:
            continue
        yield {"box": [left + x0, top + y0, right + x0, bottom + y0],
               "top_x": median(x for x, y in points if y == top) + x0,
               "bottom_x": median(x for x, y in points if y == bottom) + x0,
               "left_y": median(y for x, y in points if x == left) + y0,
               "right_y": median(y for x, y in points if x == right) + y0,
               "fill": len(points) / ((right - left + 1) * (bottom - top + 1))}


def _axes(face):
    l, t, r, _ = face["box"]
    mid = (face["top_x"] + face["bottom_x"]) / 2
    if not (.4 <= face["fill"] <= .65 and abs(face["top_x"] - face["bottom_x"]) <= .12 * (r - l)
            and l + .2 * (r - l) < mid < r - .2 * (r - l)):
        return None
    a, d = mid - l, r - mid
    slopes = ((face["left_y"] - t) / a, (face["right_y"] - t) / d)
    if all(.45 <= slope <= .75 for slope in slopes) and abs(slopes[0] - slopes[1]) <= .13:
        return a, d
    return None


def _stack_and_neighbor(image, target):
    """Accept distinct repeated top faces, with a full-height adjacent front for scale."""
    l, t, r, b = target
    regions = list(_regions(image, target))
    planes = []
    for face in regions:
        a, c, d, e = face["box"]
        if (l - .35 * (r - l) <= (a + d) / 2 <= r + .35 * (r - l)
                and t <= (c + e) / 2 <= b + .15 * (b - t) and (axes := _axes(face))):
            planes.append((face, axes))
    if len(planes) < 2:
        return None
    planes.sort(key=lambda pair: pair[0]["box"][1])
    boxes = [face["box"] for face, _ in planes]
    left, right = median(box[0] for box in boxes), median(box[2] for box in boxes)
    span = right - left
    if (any(abs(a - left) > .12 * span or abs(d - right) > .12 * span for a, _, d, _ in boxes)
            or any(first[3] >= second[1] for first, second in zip(boxes, boxes[1:]))):
        return None
    neighbors = []
    for face in regions:
        a, c, d, e = face["box"]
        width = d - a
        if width <= 0:
            continue
        slope = (face["right_y"] - face["left_y"]) / width
        side = "left" if 0 <= a - right <= .35 * span else "right" if 0 <= left - d <= .35 * span else None
        height = e - c - abs(slope) * width
        if (side and .45 <= abs(slope) <= .75 and face["fill"] >= .7
                and abs(face["top_x"] - face["bottom_x"]) >= .8 * width
                and c < boxes[0][1] and e >= boxes[-1][3] - .3 * span
                and height >= boxes[-1][1] - boxes[0][1]):
            neighbors.append((side, slope, width, height))
    if len(neighbors) == 1:
        return planes, neighbors[0]
    return None


def _owner(obj, output, planner, neighbor, planes, views):
    """Match side, relative front aspect, and the narrow bay's clear width."""
    side, slope, width_px, height_px = neighbor
    # Front edges slope in the same direction as the adjacent facade.
    front_axis = 0 if slope > 0 else 1
    width_ratio = median(axes[front_axis] for _, axes in planes) / width_px
    aspect = width_px * (1 + slope ** 2) ** .5 / height_px
    blocks = {row["id"]: row for row in planner["blocks"]}
    owners = []
    for scope in output["blocks"]:
        block = blocks[scope["block_id"]]
        extensions = {f"{row['view_id']}:{row['contour_id']}": row for row in block.get("fixed_extensions", ())}
        if not extensions or any(p["role"] == ROLE for p in scope["parts"]):
            continue
        item = next((row for row in obj["items"] if row["kind"] == "block" and row["id"] == block["id"]), None)
        if item is None or any(child["role"] == ROLE for child in item["children"]):
            continue
        fronts = [p for p in scope["parts"] if p["role"] == "door_front" and p.get("instance_ref")]
        stock = {p["dimensions"]["thickness"]["mm"] for p in scope["parts"] if p["role"] == "carcass_side"}
        if len(stock) != 1 or not (thickness := next(iter(stock))):
            continue
        for panel in (p for p in scope["parts"] if p["role"] == "fixed_panel" and p.get("instance_ref") in extensions):
            ext = extensions[panel["instance_ref"]]
            a, b, c, d = ext["bbox"]
            panel_width = panel["dimensions"]["width"]["mm"]
            if not panel_width or panel_width <= 2 * thickness:
                continue
            for front in fronts:
                dims = front["dimensions"]
                w, h = dims["length"]["mm"], dims["width"]["mm"]
                if not w or not h or abs(aspect * h / w - 1) > .15:
                    continue
                vid, _, cid = front["instance_ref"].partition(":")
                if vid != ext["view_id"]:
                    continue
                # The specific facade must touch the extension on the same side in the elevation.
                native = next((row["bbox"] for row in views[vid]["candidates"] if row["id"] == cid), None)
                if native is None:
                    continue
                x, y, z, end = native
                gap = x - c if side == "left" else a - z
                if abs(gap) > .15 * (z - x) or abs(y - b) + abs(end - d) > .12 * (d - b):
                    continue
                if abs(width_ratio * w / (panel_width - 2 * thickness) - 1) <= .18:
                    owners.append((item, scope, panel, front, thickness))
    return (owners[0], front_axis) if len(owners) == 1 else None


def recover_fixed_shelves(coverage, inventory, parts, analyze, views, render):
    """Amend a checked gap only when visible instances and one owner are grounded."""
    changes = []
    for oid, obj in inventory["objects"].items():
        if not any(row.get("role") == ROLE and row["reason"] == "ownership_pending"
                   for row in coverage["objects"][oid]["inventory_issues"]):
            continue
        for finding in obj["source_review_findings"]:
            if finding["role"] != ROLE or finding["status"] != "ownership_pending":
                continue
            source = finding["source"]
            vid = source["view_id"]
            if (analyze["islands"].get(vid) not in {"Render", "Axonometric view"}
                    or not source.get("bbox_normalized") or not (content := render(vid))):
                continue
            view = views[vid]
            with Image.open(BytesIO(content)) as image:
                l, t, r, b = view["bbox_normalized"]
                a, c, d, e = source["bbox_normalized"]
                crop = [(a - l) / (r - l) * image.width, (c - t) / (b - t) * image.height,
                        (d - l) / (r - l) * image.width, (e - t) / (b - t) * image.height]
                detected = _stack_and_neighbor(image.convert("L"), crop)
                size = image.size
            if detected is None:
                continue
            planes, neighbor = detected
            ownership = _owner(obj, parts["objects"][oid], analyze["objects"][oid]["planner"],
                               neighbor, planes, views)
            if ownership is None:
                continue
            (item, scope, panel, front, thickness), front_axis = ownership
            facade = front["dimensions"]["length"]
            scale = facade["mm"] / neighbor[2]
            stock = {"mm": thickness, "basis": "construction_assumption", "refs": [],
                     "reason": "Match the provisional sheet stock of the owning carcass."}
            ident = f"fixed-shelf:{item['id']}"
            sources = []
            for index, (face, axes) in enumerate(planes, 1):
                ref = f"{vid}:{ident}:{index}"
                evidence = {"view_id": vid, "page": view["page"], "instance_ref": ref,
                            "bbox_normalized": page_box(face["box"], view, size=size),
                            "evidence": "Distinct closed horizontal plane in the fixed shelf stack."}
                sources.append(evidence)
                refs = list(dict.fromkeys([ref, panel["instance_ref"], front["instance_ref"], *facade["refs"]]))
                reason = "Provisional size from near-isometric projection scaled to the adjacent facade."
                sizes = [{**dimension(axes[axis] * scale, "scaled_projection", refs), "reason": reason}
                         for axis in (front_axis, 1 - front_axis)]
                scope["parts"].append({**part(ROLE, material="cabinet panel stock", length=sizes[0],
                                              width=sizes[1], thickness=stock),
                                       "inventory_item_id": ident, "instance_ref": ref,
                                       "construction_basis": "render_scaled_fixed_shelf"})
            item["children"].append({"id": ident, "kind": "element", "role": ROLE, "quantity": len(planes),
                                     "quantity_basis": "Distinct visible planes in one fixed shelf stack.",
                                     "source_refs": [source, *sources], "children": []})
            finding.update(status="assigned", candidate_owner_ids=[ident], disposition="parts_check_recovered")
            changes.append({"object_id": oid, "block_id": item["id"], "role": ROLE, "quantity": len(planes)})
    if changes:
        refresh_source_coverage(inventory)
    return changes
