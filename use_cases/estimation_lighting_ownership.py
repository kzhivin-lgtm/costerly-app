"""Match printed lighting observations to physical Blocks."""

from collections import defaultdict
from math import hypot

from tools.estimation_native_islands import inside
from tools.probe_cb_block_boundaries import rectangular
from use_cases.estimation_v9_inventory import lighting_temperature_readings


def _point_distance(point, box):
    x, y = point
    left, top, right, bottom = box
    return hypot(max(left - x, x - right, 0), max(top - y, y - bottom, 0))


def _label_leader(reading, view):
    if reading.get("annotation_id") and reading.get("tips"):
        return reading["annotation_id"], reading["tips"]
    box = reading.get("callout_bbox_normalized", reading.get("bbox_normalized"))
    if not box:
        return None
    left, top, right, bottom = view["bbox_normalized"]
    scale_x = view["width"] / (right - left)
    scale_y = view["height"] / (bottom - top)
    box = [(box[0] - left) * scale_x, (box[1] - top) * scale_y,
           (box[2] - left) * scale_x, (box[3] - top) * scale_y]
    leaders = [(index, arrow) for index, arrow in enumerate(view.get("arrows", ()), 1)
               if arrow["tips"] and any(
                   abs(tip["xy"][0] - arrow["root"][0]) > 3 and abs(tip["xy"][1] - arrow["root"][1]) > 3
                   for tip in arrow["tips"])]
    tolerance = (.06 if reading.get("callout_bbox_normalized") else .12) * min(view["width"], view["height"])
    close = [(index, arrow) for index, arrow in leaders if _point_distance(arrow["root"], box) <= tolerance]
    if not close and "callout_bbox_normalized" not in reading:
        # Older responses often located the target instead of the printed label.
        close = [(index, arrow) for index, arrow in leaders if len(arrow["tips"]) >= 2 and all(
            _point_distance(tip["xy"], box) <= .04 * min(view["width"], view["height"])
            for tip in arrow["tips"])]
    if len(close) != 1:
        return None
    index, arrow = close[0]
    return f"A{index:02}", [{"xy_px": tip["xy"], "contours": tip.get("hits", [])} for tip in arrow["tips"]]


def _projected_regions(view, measurements):
    vid = view["view_id"]
    width, height = measurements.get("width", {}), measurements.get("height", {})
    if all(row.get("view_id") == vid and row.get("bounds_1000") for row in (width, height)):
        left, right = (value * view["width"] / 1000 for value in width["bounds_1000"])
        top, bottom = (value * view["height"] / 1000 for value in height["bounds_1000"])
        yield [[left, top], [right, top], [right, bottom], [left, bottom]]
    depth = measurements.get("depth", {})
    # A single closed footprint measures the Block itself on the plan.
    if view.get("projection") == "Top view" and depth.get("view_id") == vid and len(depth.get("contour_ids", ())) == 1:
        contour_id, = depth["contour_ids"]
        yield from (row["polygon"] for row in view["candidates"] if row["id"] == contour_id)


def _mirror_owner(tips, items, view_id):
    """Opposite edge witnesses can locate a mirror even when the tips touch its frame."""
    if len(tips) < 2:
        return None
    points = [tip["xy_px"] for tip in tips]
    owners = set()
    for block in items:
        for mirror in block["children"]:
            if mirror["role"] != "mirror":
                continue
            for ref in mirror["source_refs"]:
                if ref["view_id"] != view_id or not ref.get("bbox_px"):
                    continue
                left, top, right, bottom = ref["bbox_px"]
                tolerance = max(3, .05 * (right - left))
                if (all(_point_distance(point, ref["bbox_px"]) <= tolerance for point in points)
                        and all(any(abs(point[0] - x) <= tolerance for point in points) for x in (left, right))
                        and all(top <= point[1] <= bottom for point in points)):
                    owners.add(block["id"])
    return next(iter(owners)) if len(owners) == 1 else None


def _continuous_contour(tips, view):
    """A shared leader caption alone does not prove a continuous physical run."""
    common = set.intersection(*(set(tip.get("contours", ())) for tip in tips))
    candidates = []
    for face in view["candidates"]:
        if face["id"] not in common:
            continue
        left, top, right, bottom = face["bbox"]
        width, height = right - left, bottom - top
        if min(width, height) > 0 and max(width, height) >= 12 * min(width, height):
            candidates.append(face["id"])
    return candidates[0] if len(candidates) == 1 else None


def _elevation_bay(view, tips):
    # A horizontal cap with two tall sides gives a bay outline before scaling.
    sides = [row["bbox"] for row in view["candidates"] if row["bbox"][3] - row["bbox"][1] > .35 * view["height"]
             and row["bbox"][2] - row["bbox"][0] < .025 * view["width"]]
    matches = set()
    for row in view["candidates"]:
        left, top, right, bottom = row["bbox"]
        if right - left < .12 * view["width"] or bottom - top > .02 * view["height"]:
            continue
        left_sides = [box for box in sides if abs(box[2] - left) <= 2 and abs(box[1] - top) <= 2]
        right_sides = [box for box in sides if abs(box[0] - right) <= 2 and abs(box[1] - top) <= 2]
        for a in left_sides:
            for b in right_sides:
                if abs(a[3] - b[3]) <= 2:
                    box = (a[0], top, b[2], max(a[3], b[3]))
                    if all(_point_distance(tip["xy_px"], box) == 0 for tip in tips):
                        matches.add(box)
    return next(iter(matches)) if len(matches) == 1 else None


def _display_regions_without_dimensions(blocks, planner, views, labels):
    """Bind repeated glazed bays using matching plan and elevation topology."""
    glazed = {bid: [child for child in block["children"] if child["role"] == "glazed_zone"]
              for bid, block in blocks.items()}
    glazed = {bid: zones[0] for bid, zones in glazed.items() if len(zones) == 1}
    if len(glazed) < 2:
        return {}
    source_views = {ref["view_id"] for zone in glazed.values() for ref in zone["source_refs"]}
    if len(source_views) != 1:
        return {}
    source_view, = source_views
    axon = {}
    for block in planner:
        if block["id"] in glazed:
            points = [point for polygon in block.get("envelopes", {}).get(source_view, {}).get("polygons_px", ())
                      for point in polygon]
            if not points:
                return {}
            axon[block["id"]] = (min(x for x, _ in points), max(x for x, _ in points))
    ordered = sorted(axon, key=lambda bid: axon[bid][0])
    if any(axon[a][1] >= axon[b][0] for a, b in zip(ordered, ordered[1:])):
        return {}

    elevations = defaultdict(set)
    plans = defaultdict(set)
    for (vid, _), readings in labels.items():
        view, tips = views[vid], readings[0]["tips"]
        if view["projection"] == "Front elevation":
            if bay := _elevation_bay(view, tips):
                elevations[vid].add(bay)
        elif view["projection"] == "Top view":
            footprints = [tuple(face["bbox"]) for face in view["candidates"] if rectangular(face)
                          and face["bbox"][2] - face["bbox"][0] > 1.6 * (face["bbox"][3] - face["bbox"][1])]
            owners = [[box for box in footprints if _point_distance(tip["xy_px"], box) == 0] for tip in tips]
            if all(len(matches) == 1 for matches in owners):
                plans[vid].update(matches[0] for matches in owners)

    fronts = [(vid, sorted(boxes)) for vid, boxes in elevations.items() if len(boxes) == len(ordered)]
    tops = [(vid, sorted(boxes)) for vid, boxes in plans.items() if len(boxes) == len(ordered)]
    if len(fronts) != 1 or len(tops) != 1:
        return {}
    front, top = fronts[0], tops[0]
    for _, boxes in (front, top):
        if any(a[2] >= b[0] or abs(a[1] - b[1]) > 2 or abs(a[3] - b[3]) > 2
               for a, b in zip(boxes, boxes[1:])):
            return {}
    widths = [[box[2] - box[0] for box in boxes] for _, boxes in (front, top)]
    if any(abs(a / sum(widths[0]) - b / sum(widths[1])) > .04 for a, b in zip(*widths)):
        return {}
    anchor_widths = [axon[bid][1] - axon[bid][0] for bid in ordered]
    if any(abs(a - b) < .1 * max(a, b) or (a > b) != (c > d)
           for a, b, c, d in zip(anchor_widths, anchor_widths[1:], widths[0], widths[0][1:])):
        return {}
    return {vid: {bid: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
                  for bid, (x0, y0, x1, y1) in zip(ordered, boxes)} for vid, boxes in (front, top)}


def resolve_lighting_ownership(inventory, analyze, geometry, views):
    """Replace the draft callout group with locally owned features and open evidence."""
    views = {vid: {**view, "projection": analyze["islands"][vid]} for vid, view in views.items()}
    for oid, obj in inventory["objects"].items():
        group = next((row for row in obj["items"] if row["id"] == "lighting"), None)
        if group is None:
            continue
        obj["items"].remove(group)
        blocks = {row["id"]: row for row in obj["items"] if row["kind"] == "block"}
        analyzed_object = analyze["objects"][oid]
        planner = analyzed_object["planner"]["blocks"]
        typed = {(vid, row["id"]): row["role"]
                 for vid, rows in analyzed_object["front"].get("typed_leaders", {}).items() for row in rows}
        measurements = {row["block_id"]: row["measurements"] for row in geometry["objects"][oid]["blocks"]}
        regions = {
            vid: {row["id"]: [
                *row.get("envelopes", {}).get(vid, {}).get("polygons_px", ()),
                *_projected_regions(views[vid], measurements[row["id"]]),
            ] for row in planner}
            for vid in obj["view_ids"]
        }
        labels = defaultdict(list)
        for reading in lighting_temperature_readings(group, include_unspecified=True):
            vid = reading["view_id"]
            if match := _label_leader(reading, views[vid]):
                annotation, tips = match
                if typed.get((vid, annotation), "lighting") == "lighting":
                    labels[vid, annotation].append({**reading, "annotation_id": annotation, "tips": tips})

        aligned = set()
        for vid, matched in _display_regions_without_dimensions(blocks, planner, views, labels).items():
            for bid, polygon in matched.items():
                if not regions[vid][bid]:
                    regions[vid][bid].append(polygon)
                    aligned.add((vid, bid))

        routed = []
        for (vid, annotation), readings in labels.items():
            view = views[vid]
            tips = readings[0]["tips"]
            per_tip = [{bid for bid, polygons in regions[vid].items()
                        if any(inside(tip["xy_px"], polygon) for polygon in polygons)} for tip in tips]
            if owner := _mirror_owner(tips, blocks.values(), vid):
                per_tip = [{owner}] * len(tips)
            if any(len(owners) != 1 for owners in per_tip):
                continue
            owners = sorted(set.union(*per_tip))
            continuous = _continuous_contour(tips, view) if len(owners) > 1 else None
            routed.append((vid, annotation, readings, owners, continuous))

        bindings = {}
        by_scope = defaultdict(list)
        for vid, annotation, readings, owners, continuous in sorted(
                routed, key=lambda row: (len(row[3]), row[0], row[1])):
            scopes = [None] if continuous else owners
            values = sorted({value for row in readings for value in row["kelvin_values"]})
            bindings[vid, annotation] = []
            for block_id in scopes:
                existing = [item for item in by_scope[block_id] if item["kelvin_values"] == values
                            and all(ref["view_id"] != vid for ref in item["source_refs"])]
                # A multi-target note in another projection can corroborate a
                # unique already-located section in each Block.
                if len(existing) == 1 and len(owners) > 1 and block_id is not None:
                    item = existing[0]
                    item["source_refs"].extend(readings)
                else:
                    ident = f"lighting:{block_id or 'shared'}:{vid}:{annotation}"
                    basis = "continuous_cross_block_contour" if continuous else "leader_targets_in_block"
                    if (vid, block_id) in aligned:
                        basis = "leader_targets_in_matched_elevation_and_plan"
                    item = {"id": ident, "kind": "element", "role": "lighting",
                            "quantity": 1 if continuous else None,
                            "source_refs": list(readings), "kelvin_values": values, "children": [],
                            "attached_block_ids": [block_id] if block_id else owners,
                            "ownership_basis": basis}
                    if continuous:
                        item["continuous_contour_id"] = continuous
                    (blocks[block_id]["children"] if block_id else obj["items"]).append(item)
                    by_scope[block_id].append(item)
                bindings[vid, annotation].append(item["id"])

        for row in [*obj["observations"], *obj["source_review_findings"]]:
            if row["role"] != "lighting":
                continue
            source = row["source"]
            vid = source["view_id"]
            match = _label_leader(source, views[vid])
            item_ids = bindings.get((vid, match[0]), []) if match else []
            row["candidate_owner_ids"] = item_ids
            row["status"] = "assigned" if item_ids else "ownership_pending"
            row["ownership_basis"] = "localized_lighting_note" if item_ids else None
