"""Match labelled axonometric casework assemblies to orthographic shell boundaries."""

from collections import defaultdict
from itertools import combinations

from tools.estimation_orthographic_geometry import overlap
from tools.probe_cb_block_boundaries import connected_views, envelope, rectangular


def only(values):
    return values[0] if len(values) == 1 else None


def axis_pixels(view, reading):
    size = view["width" if reading["axis"] == "x" else "height"]
    return tuple(value * size / 1000 for value in reading["bounds"])


def isotropic_scale(view, printed):
    anchors = printed[view["view_id"]]
    if not anchors:
        return None
    source = max(anchors, key=lambda row: row["value_mm"])
    low, high = axis_pixels(view, source)
    scale = source["value_mm"] / (high - low)
    consistent = [
        row for row in anchors
        if abs(scale * (axis_pixels(view, row)[1] - axis_pixels(view, row)[0]) / row["value_mm"] - 1) <= .035
    ]
    return (scale, source) if len(consistent) >= max(1, .7 * len(anchors)) else None


def measure(view, axis, ends, names, ids, printed, span, bind_dimension):
    boundary = span(view, axis, ends, *names, ids)
    value = bind_dimension(boundary, printed)
    if value["value_mm"] is not None:
        return value
    anchors = printed[view["view_id"]]
    if any(row["axis"] == axis and all(abs(a - b) <= 3 for a, b in zip(row["bounds"], boundary["bounds_1000"]))
           for row in anchors):
        return value
    calibration = isotropic_scale(view, printed)
    if not calibration:
        return value
    scale, source = calibration
    return {**boundary, "method": "scaled_projection", "value_mm": round(scale * (ends[1] - ends[0]) / 5) * 5,
            "sources": [source]}


def align_views(views, projections, source_vid, observations):
    connected = connected_views(source_vid, observations)
    return {role: [view for vid, view in views.items() if vid in connected and projections[vid] == role]
            for role in ("Front elevation", "Side view", "Section", "Top view")}


def printed_bays(view, printed):
    """Bind horizontal labels to a pair of tall shell edges in the same elevation."""
    tall = [face for face in view["candidates"] if face["bbox"][3] - face["bbox"][1] >= .35 * view["height"]
            and face["bbox"][2] - face["bbox"][0] <= .025 * view["width"]]
    result = []
    for source in printed[view["view_id"]]:
        if source["axis"] != "x":
            continue
        left, right = axis_pixels(view, source)
        if right - left < .12 * view["width"]:
            continue
        sides = []
        for edge in (left, right):
            picks = sorted((abs(x - edge), face["id"], x, face)
                           for face in tall for x in face["bbox"][::2] if abs(x - edge) <= .005 * view["width"])
            if not picks:
                break
            sides.append(picks[0])
        if len(sides) != 2:
            continue
        _, _, low, first = sides[0]
        _, _, high, last = sides[1]
        a, b = first["bbox"], last["bbox"]
        if abs(a[1] - b[1]) <= 2 and abs(a[3] - b[3]) <= 2:
            result.append({"bbox": (low, min(a[1], b[1]), high, max(a[3], b[3])),
                           "ids": [first["id"], last["id"]], "source": source})
    return sorted(result, key=lambda row: row["bbox"][0])


def matched_plan_bays(plan, bays, printed):
    calibration = isotropic_scale(plan, printed)
    if not calibration:
        return None
    scale, _ = calibration
    candidates = [c for c in plan["candidates"] if rectangular(c) and
                  c["bbox"][2] - c["bbox"][0] > 1.6 * (c["bbox"][3] - c["bbox"][1])]
    matches = []
    for faces in combinations(sorted(candidates, key=lambda row: row["bbox"][0]), len(bays)):
        if any(abs(a["bbox"][1] - b["bbox"][1]) > 2 or abs(a["bbox"][3] - b["bbox"][3]) > 2
               for a, b in zip(faces, faces[1:])):
            continue
        if all(abs((face["bbox"][2] - face["bbox"][0]) * scale / bay["source"]["value_mm"] - 1) <= .06
               for face, bay in zip(faces, bays)):
            matches.append(faces)
    return only(matches)


def lower_band(view, top, horizontal):
    """Use the repeated shell faces directly below the known tier boundary."""
    left, right = horizontal
    eligible = [face for face in view["candidates"] if rectangular(face)
                and abs(face["bbox"][1] - top) <= 2
                and face["bbox"][3] - top > .06 * view["height"]
                and overlap((left, right), face["bbox"][::2]) >= .6 * (face["bbox"][2] - face["bbox"][0])]
    groups = defaultdict(list)
    for face in eligible:
        groups[round(face["bbox"][3] / 2) * 2].append(face)
    fits = [faces for faces in groups.values() if len(faces) >= 2 and
            sum(overlap((left, right), face["bbox"][::2]) for face in faces) >= .85 * (right - left)]
    return only(fits)


def return_elevation(view, printed):
    """Find a tall return with a printed overall and lower-tier floor datum."""
    y_dims = [row for row in printed[view["view_id"]] if row["axis"] == "y"]
    if len(y_dims) < 2:
        return None
    overall = max(y_dims, key=lambda row: row["value_mm"])
    top, floor = axis_pixels(view, overall)
    trims = [c for c in view["candidates"] if abs(c["bbox"][1] - top) <= 2 and
             c["bbox"][2] - c["bbox"][0] >= .35 * view["width"] and
             c["bbox"][3] - c["bbox"][1] <= .03 * view["height"]]
    rim = only(trims)
    if rim is None:
        return None
    x0, y0, x1, _ = rim["bbox"]
    choices = []
    for source in y_dims:
        tier, datum = axis_pixels(view, source)
        if not (abs(datum - floor) <= 2 and .12 <= source["value_mm"] / overall["value_mm"] <= .45):
            continue
        shell = [c for c in view["candidates"] if abs(c["bbox"][1] - y0) <= 2
                 and abs(c["bbox"][3] - tier) <= 2 and c["bbox"][2] - c["bbox"][0] < .025 * view["width"]
                 and (abs(c["bbox"][2] - x0) <= 2 or abs(c["bbox"][0] - x1) <= 2)]
        if len(shell) != 2:
            continue
        edges = envelope([rim["bbox"], *(c["bbox"] for c in shell)])
        row = lower_band(view, tier, edges[::2])
        if row:
            bottom = max(c["bbox"][3] for c in row)
            plinth = only([c for c in view["candidates"] if abs(c["bbox"][1] - bottom) <= 2
                           and abs(c["bbox"][3] - floor) <= 2 and
                           overlap(edges[::2], c["bbox"][::2]) >= .85 * (edges[2] - edges[0])])
            if plinth:
                choices.append((edges, tier, plinth["bbox"][3], [rim["id"], *(c["id"] for c in shell)],
                                row, plinth["id"], overall, source))
    return only(choices)


def compare_tier_height(measurement, overall, installed):
    if measurement["value_mm"] is None:
        return measurement
    height = overall["value_mm"] - installed["value_mm"]
    if abs(measurement["value_mm"] - height) > max(10, .025 * height):
        return measurement
    return {**measurement, "value_mm": height, "method": "shared_floor_difference",
            "sources": [overall, installed], "projection_check_mm": measurement["value_mm"]}


def corner_casework(roles, candidates, printed, measure_one, axono_box, *, require_return_match=False):
    displays = sorted(roles["drawer_and_pull_out_bay"], key=lambda block: axono_box(block)[0])
    mirrors = roles["mirror_upright"]
    lower = sorted(roles["assumed_lower_frame_split"], key=lambda block: axono_box(block)[0])
    returns = sorted(roles["return_door_band"], key=lambda block: axono_box(block)[1])
    if len(displays) < 2 or len(mirrors) != 1 or len(returns) != 2:
        return {}
    mirror, = mirrors
    centers = [sum(axono_box(row)[::2]) / 2 for row in displays]
    mirror_center = sum(axono_box(mirror)[::2]) / 2
    insert_at = only([i for i, (left, right) in enumerate(zip(centers, centers[1:]), 1)
                      if left < mirror_center < right])
    a, b = (axono_box(block)[::2] for block in returns)
    if insert_at is None or overlap(a, b) < .8 * max(a[1] - a[0], b[1] - b[0]):
        return {}
    front = only(candidates["Front elevation"])
    side = only(candidates["Side view"])
    plan = only(candidates["Top view"])
    if not all((front, side, plan)):
        return {}
    bays = printed_bays(front, printed)
    if len(bays) != len(displays) or any(a["bbox"][2] >= b["bbox"][0] for a, b in zip(bays, bays[1:])):
        return {}
    plan_bays = matched_plan_bays(plan, bays, printed)
    if not plan_bays:
        return {}
    lower_row = lower_band(front, bays[0]["bbox"][3], (bays[0]["bbox"][0], bays[-1]["bbox"][2]))
    if not lower_row:
        return {}
    return_bounds = return_elevation(side, printed)
    if return_bounds is None:
        return {}
    edges, tier, floor, return_ids, return_row, plinth_id, overall, installed = return_bounds
    x0, y0, x1, _ = edges
    scale = isotropic_scale(plan, printed)
    return_scale = isotropic_scale(side, printed)
    if not scale or not return_scale:
        return {}
    plan_return = only([c for c in plan["candidates"] if rectangular(c) and
                        c["bbox"][3] - c["bbox"][1] > 2.5 * (c["bbox"][2] - c["bbox"][0]) and
                        c["bbox"][0] >= plan_bays[-1]["bbox"][2] - 5 and
                        abs((c["bbox"][3] - c["bbox"][1]) * scale[0] /
                            ((x1 - x0) * return_scale[0]) - 1) <= .06])
    if require_return_match and plan_return is None:
        return {}
    left_plan, right_plan = plan_bays[insert_at - 1:insert_at + 1]
    bridge = only([c for c in plan["candidates"] if rectangular(c)
                   and abs(c["bbox"][0] - left_plan["bbox"][2]) <= 5
                   and abs(c["bbox"][2] - right_plan["bbox"][0]) <= 5
                   and abs(c["bbox"][3] - left_plan["bbox"][3]) <= 2
                   and c["bbox"][1] > left_plan["bbox"][1]])
    results = {}
    for block, face, footprint in zip(displays, bays, plan_bays):
        a, t, b, e = face["bbox"]
        ids = face["ids"]
        results[block["id"]] = {
            "width": measure_one(front, "x", (a, b), ("outer left bay side", "outer right bay side"), ids),
            "height": compare_tier_height(measure_one(front, "y", (t, e), ("top of display", "display to lower tier seam"), ids),
                                          overall, installed),
            "depth": measure_one(plan, "y", footprint["bbox"][1::2], ("rear edge", "outer face"), [footprint["id"]]),
        }
    left_bay, right_bay = bays[insert_at - 1:insert_at + 1]
    left, right = left_bay["bbox"][2], right_bay["bbox"][0]
    ids = [left_bay["ids"][1], right_bay["ids"][0]]
    values = {
        "width": measure_one(front, "x", (left, right), ("left edge of centre bay", "right edge of centre bay"), ids),
        "height": compare_tier_height(measure_one(front, "y", bays[0]["bbox"][1::2],
                         ("top of centre bay", "centre bay to lower tier seam"), ids), overall, installed),
    }
    if bridge:
        values["depth"] = measure_one(plan, "y", bridge["bbox"][1::2], ("rear of centre bridge", "face of centre bridge"),
                                      [bridge["id"]])
    results[mirror["id"]] = values

    # Match each lower shell to the upper bays by relative overlap on the
    # common axonometric projection. Their plan depth is not inherited.
    upper = [*displays[:insert_at], mirror, *displays[insert_at:]]
    footprints = [*(b["bbox"][::2] for b in bays[:insert_at]), (left, right),
                  *(b["bbox"][::2] for b in bays[insert_at:])]
    matched = []
    for low in lower:
        coverages = [overlap(axono_box(low)[::2], axono_box(high)[::2]) for high in upper]
        best = max(coverages)
        matched.append([index for index, length in enumerate(coverages) if best and length >= .2 * best])
    if all(indexes and indexes == list(range(indexes[0], indexes[-1] + 1)) for indexes in matched) and (
            [index for indexes in matched for index in indexes] == list(range(len(upper)))):
        lower_limits = [(footprints[indexes[0]][0], footprints[indexes[-1]][1]) for indexes in matched]
        for block, limits in zip(lower, lower_limits):
            members = [c for c in lower_row if overlap(limits, c["bbox"][::2]) >= .6 * (c["bbox"][2] - c["bbox"][0])]
            if not members:
                continue
            shell = envelope(c["bbox"] for c in members)
            ids = [c["id"] for c in members]
            results[block["id"]] = {
                "width": {**measure_one(front, "x", limits, ("outer lower run edge", "assumed split or outer edge"), ids),
                          "ownership_basis": "Planner split projected using aligned upper and lower bays"},
                "height": measure_one(front, "y", shell[1::2], ("upper tier seam", "body bottom above shared plinth"), ids),
            }

    if plan_return:
        top_block, low_block = returns
        upper_result = {
            "width": measure_one(side, "x", (x0, x1), ("first return side", "opposite return side"), return_ids),
            "depth": measure_one(plan, "x", plan_return["bbox"][::2], ("rear return edge", "outer return edge"),
                                 [plan_return["id"]]),
            "height": compare_tier_height(measure_one(side, "y", (y0, tier), ("return upper edge", "tier seam"),
                                                    return_ids), overall, installed),
        }
        if upper_result["width"]["value_mm"] is not None:
            plan_width = measure_one(plan, "y", plan_return["bbox"][1::2], ("near end of return", "far end of return"),
                                     [plan_return["id"]])
            upper_result["width"]["plan_crosscheck"] = plan_width
        shell = envelope(c["bbox"] for c in return_row)
        ids = [c["id"] for c in return_row]
        results[top_block["id"]] = upper_result
        results[low_block["id"]] = {
            "width": measure_one(side, "x", (x0, x1), ("first return side", "opposite return side"), return_ids + ids),
            "height": measure_one(side, "y", shell[1::2], ("tier seam", "body bottom above shared plinth"), ids),
            "installed_height": measure_one(side, "y", (tier, floor), ("tier seam", "floor"), [*ids, plinth_id]),
        }
    return results


def straight_casework(roles, candidates, printed, measure_one, front_counts):
    banks, mirrors = roles["source_labelled_drawer_bank"], roles["mirror_upright"]
    if len(banks) != 1 or len(mirrors) != 1:
        return {}
    front = only(candidates["Front elevation"])
    plan = only(candidates["Top view"])
    if not front or not plan or not printed[plan["view_id"]]:
        return {}
    rows = defaultdict(list)
    for face in front["candidates"]:
        x0, y0, x1, y1 = face["bbox"]
        if rectangular(face) and x1 - x0 >= .12 * front["width"]:
            rows[(round(y0 / 2), round(y1 / 2))].append(face)
    bank_rows = [faces for faces in rows.values() if len(faces) == front_counts.get("drawer")
                 and envelope(f["bbox"] for f in faces)[2] - envelope(f["bbox"] for f in faces)[0] >= .8 * front["width"]]
    if len(bank_rows) < 2:
        return {}
    faces = [face for group in bank_rows for face in group]
    box = envelope(face["bbox"] for face in faces)
    if any(abs(envelope(face["bbox"] for face in group)[0] - box[0]) > 3 for group in bank_rows):
        return {}
    axes = [r for r in printed[plan["view_id"]] if r["axis"] == "x"]
    longest = max(axes, key=lambda r: r["value_mm"], default=None)
    if longest is None:
        return {}
    a, b = axis_pixels(plan, longest)
    plan_parts = [c for c in plan["candidates"] if a - 3 <= c["bbox"][0] < c["bbox"][2] <= b + 3
                  and c["bbox"][2] - c["bbox"][0] <= b - a + 2]
    footprint = envelope(c["bbox"] for c in plan_parts) if plan_parts else None
    if not footprint or abs(footprint[0] - a) > 3 or abs(footprint[2] - b) > 3:
        return {}
    footprint_width = footprint[2] - footprint[0]
    section_count = front_counts["drawer"]
    rim_rows = [[c for c in plan_parts if abs(c["bbox"][edge] - footprint[edge]) <= 2
                 and c["bbox"][3] - c["bbox"][1] <= .08 * (footprint[3] - footprint[1])
                 and c["bbox"][2] - c["bbox"][0] >= .12 * footprint_width] for edge in (1, 3)]
    if not any(len(row) == section_count and sum(c["bbox"][2] - c["bbox"][0] for c in row) >= .9 * footprint_width
               for row in rim_rows):
        return {}
    ids = [c["id"] for c in plan_parts]
    width = measure_one(plan, "x", footprint[::2], ("left end of drawer bank", "right end of drawer bank"), ids)
    depth = measure_one(plan, "y", footprint[1::2], ("rear bank edge", "front bank edge"), ids)
    # Verify the horizontal bank runs between the same number of sections
    # before transferring the printed plan width into this elevation.
    transfer = {**width, "front_view_id": front["view_id"], "front_bounds_px": box[::2],
                "matched_section_count": len(bank_rows[0])}
    height = measure_one(front, "y", box[1::2], ("top edge of drawer bank", "body bottom above plinth"),
                         [c["id"] for c in faces])
    if height["value_mm"] is None and width["value_mm"]:
        height = {**height, "method": "scaled_from_matching_plan_width",
                  "value_mm": round((box[3] - box[1]) * width["value_mm"] / (box[2] - box[0]) / 5) * 5,
                  "sources": width["sources"], "projection_binding": transfer}
    result = {banks[0]["id"]: {"width": width, "depth": depth, "height": height}}
    mirror_dimensions = {}
    # A single thin perpendicular projection beside the drawer bank can
    # establish the mounting panel span, but not the thickness of the assembly.
    bank_depth = footprint[3] - footprint[1]
    mounting = []
    for contour in plan["candidates"]:
        left, near, right, far = contour["bbox"]
        panel_width = far - near
        side_gap = max(footprint[0] - right, left - footprint[2])
        if (rectangular(contour) and panel_width >= 5 * (right - left)
                and 0 <= side_gap <= .02 * footprint_width
                and abs(near - footprint[1]) <= .05 * bank_depth
                and far >= footprint[3] + .5 * bank_depth):
            mounting.append(contour)
    panel = only(mounting)
    if panel:
        mirror_dimensions["width"] = measure_one(
            plan, "y", panel["bbox"][1::2], ("near end of perpendicular mounting panel",
                                             "far end of perpendicular mounting panel"), [panel["id"]])
    section = only(candidates["Section"])
    if section:
        y_dims = [row for row in printed[section["view_id"]] if row["axis"] == "y"]
        longest = max(y_dims, key=lambda r: r["value_mm"], default=None)
        if longest:
            top, floor = axis_pixels(section, longest)
            upright = only([c for c in section["candidates"] if abs(c["bbox"][1] - top) <= 2
                            and c["bbox"][3] - top >= .6 * (floor - top)])
            if upright:
                matching_floor = only([c for c in section["candidates"] if abs(c["bbox"][3] - floor) <= 2])
                if matching_floor:
                    mirror_dimensions["installed_height"] = measure_one(
                        section, "y", (upright["bbox"][1], matching_floor["bbox"][3]),
                        ("top of mirror mounting panel", "floor datum"), [upright["id"], matching_floor["id"]])
    if mirror_dimensions:
        result[mirrors[0]["id"]] = mirror_dimensions
    return result


def resolve_casework_group(plan, front, views, projections, printed, observations, *, span, bind_dimension):
    roles = defaultdict(list)
    for block in plan["blocks"]:
        if isinstance(block["appearances"], dict):
            roles[block["basis"]].append(block)
    recognized = [block for group in roles.values() for block in group]
    source = {vid for block in recognized for vid in block["appearances"]}
    if len(source) != 1:
        return {}
    vid, = source
    if projections[vid] != "Axonometric view":
        return {}
    source_view = views[vid]
    contours = {row["id"]: row for row in source_view["candidates"]}
    candidates = align_views(views, projections, vid, observations)
    owned_projections = {role: [view for key, view in views.items() if projections[key] == role]
                         for role in candidates}

    def axono_box(block):
        return envelope(contours[ident]["bbox"] for ident in block["appearances"][vid])

    def measure_one(view, axis, ends, names, ids):
        return measure(view, axis, ends, names, ids, printed, span, bind_dimension)

    if roles["drawer_and_pull_out_bay"]:
        linked = {frozenset((r["group_id_a"], r["group_id_b"])) for r in observations
                  if r["evidence_type"] == "matching_topology"}
        front_view = only([v for key, v in views.items() if projections[key] == "Front elevation"])
        side_view = only([v for key, v in views.items() if projections[key] == "Side view"])
        result = {}
        if front_view and side_view and frozenset((front_view["view_id"], side_view["view_id"])) in linked:
            candidates["Front elevation"] = [front_view]
            candidates["Side view"] = [side_view]
            result = corner_casework(roles, candidates, printed, measure_one, axono_box)
        if not result:
            # The plan must corroborate both elevations when their semantic edge is absent.
            result = corner_casework(roles, owned_projections, printed, measure_one, axono_box,
                                     require_return_match=True)
    else:
        result = straight_casework(roles, candidates, printed, measure_one, front["instance_counts"])
        if not result:
            # The drawer section count and the matching rim on the plan provide the link.
            result = straight_casework(roles, owned_projections, printed, measure_one, front["instance_counts"])
    unknown = {"value_mm": None, "method": "unresolved", "reason": "No separately bound physical boundary pair"}
    return {bid: {**dict.fromkeys(("width", "depth", "height"), unknown), **values} for bid, values in result.items()}
