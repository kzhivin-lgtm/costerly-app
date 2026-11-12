"""Compile a preliminary cut list from locked Block Geometry and native evidence."""

from collections import defaultdict
from math import isfinite
from statistics import median

from use_cases.estimation_structural_bom import _hinges_per_facade, _slide_depth_mm


VERSION = "CB Parts Geometry V1.1"
CASEWORK_BASES = {"visible_front_band", "assumed_width_split", "tall_stack_candidate"}
CASEWORK_FRONT_PARTS = {"hinged_door": "door_front", "lift_up": "lift_up_front", "drawer": "drawer_front"}


def dimension(mm, basis, refs=()):
    if mm is None or not isfinite(mm) or mm <= 0:
        return {"mm": None, "basis": "unresolved", "refs": list(refs)}
    return {"mm": round(mm), "basis": basis, "refs": list(refs)}


def geometry_dimension(measurement):
    refs = [source["source_id"] for source in measurement.get("sources", [])]
    refs.extend(f'{measurement["view_id"]}:{cid}' for cid in measurement.get("contour_ids", []))
    return dimension(measurement.get("value_mm"), measurement["method"], refs)


def derived(basis, inputs, formula, *, reason):
    refs = dict.fromkeys(ref for item in inputs for ref in item["refs"])
    values = [item["mm"] for item in inputs]
    result = dimension(formula(*values) if None not in values else None, basis, refs)
    return {**result, "reason": reason}


def stock(mm):
    return {**dimension(mm, "construction_assumption"), "reason": "Provisional sheet stock thickness."}


def part(role, quantity=1, *, material, **dimensions):
    return {"role": role, "quantity": quantity, "material_hint": material, "dimensions": dimensions}


def interval(box, axis):
    index = 0 if axis == "x" else 1
    return box[index], box[index + 2]


def contours(view):
    return {row["id"]: row["bbox"] for row in view["candidates"]}


def projected(view, printed, axis, bounds, ids):
    """Measure along one orthographic axis using a covering printed span."""
    length = view["width" if axis == "x" else "height"]
    low, high = (value * 1000 / length for value in bounds)
    refs = [f'{view["view_id"]}:{cid}' for cid in ids]
    anchors = [row for row in printed.get(view["view_id"], []) if row["axis"] == axis
               and row["bounds"][0] - 3 <= low < high <= row["bounds"][1] + 3]
    if not anchors:
        return dimension(None, "unresolved", refs)
    anchor = min(anchors, key=lambda row: row["bounds"][1] - row["bounds"][0])
    first, last = anchor["bounds"]
    return dimension((high - low) * anchor["value_mm"] / (last - first),
                     "scaled_projection", [*refs, anchor["source_id"]])


def box_dimension(view, printed, axis, contour_id):
    return projected(view, printed, axis, interval(contours(view)[contour_id], axis), [contour_id])


def drawer_box_parts(box_width, face_height, slide_length, *, instance_ref):
    drawer_t, bottom_t = stock(17), stock(6)
    box_height = derived("construction_assumption", [face_height], lambda h: h - 40,
                         reason="Allow 40 mm total clearance behind the visible drawer face.")
    end_width = derived("construction_assumption", [box_width, drawer_t], lambda w, t: w - 2 * t,
                        reason="Drawer box ends fit between the sides.")
    return [{**row, "instance_ref": instance_ref} for row in (
        part("drawer_box_side", 2, material="drawer box sheet stock", length=slide_length,
             width=box_height, thickness=drawer_t),
        part("drawer_box_end", 2, material="drawer box sheet stock", length=end_width,
             width=box_height, thickness=drawer_t),
        part("drawer_box_bottom", material="backing sheet stock", length=slide_length,
             width=box_width, thickness=bottom_t),
    )]


def drawer_frame_parts(block, measurements, views, printed, front):
    appearance, = block["appearances"]
    view = views[appearance["view_id"]]
    ids = appearance["drawer_faces"]
    accepted = {row.get("candidate_id") for row in front if row["view_id"] == view["view_id"]
                and row["role"] == "drawer"}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= accepted:
        raise ValueError("Drawer frame requires unique accepted drawer faces on its source elevation")
    boxes = contours(view)
    ids = sorted(ids, key=lambda cid: boxes[cid][0])
    if any(boxes[a][2] > boxes[b][0] for a, b in zip(ids, ids[1:])):
        raise ValueError("Drawer faces must form a non-overlapping horizontal row")
    seat_id = appearance["edges"]["top"]
    side = views[measurements["depth"]["view_id"]]
    case_id = measurements["depth"]["contour_ids"][-1]
    depth = box_dimension(side, printed, "x", case_id)
    height = box_dimension(side, printed, "y", case_id)
    width = geometry_dimension(measurements["carcass_width"])
    seat_t = box_dimension(view, printed, "y", seat_id)
    carcass = "carcass sheet stock"
    visible = "visible panel stock, substrate and finish to verify"
    back = "backing sheet stock"
    carcass_t, backing_t, face_t = stock(17), stock(6), stock(20)
    inside_w = derived("construction_assumption", [width, carcass_t], lambda w, t: w - 2 * t,
                       reason="Bottom and back fit between the carcass sides.")
    divider_h = derived("construction_assumption", [height, carcass_t], lambda h, t: h - t,
                        reason="Dividers sit between the bottom and the seat.")
    parts = [
        part("seat_cover", material=visible, length=geometry_dimension(measurements["width"]),
             width=geometry_dimension(measurements["depth"]), thickness=seat_t),
        part("carcass_side", 2, material=carcass, length=height, width=depth, thickness=carcass_t),
        part("carcass_bottom", material=carcass, length=inside_w, width=depth, thickness=carcass_t),
        part("carcass_back", material=back, length=inside_w, width=divider_h, thickness=backing_t),
    ]
    if len(ids) > 1:
        divider_depth = derived("construction_assumption", [depth, backing_t], lambda d, t: d - t,
                                reason="Dividers stop against the carcass back.")
        parts.append(part("drawer_bay_divider", len(ids) - 1, material=carcass,
                          length=divider_h, width=divider_depth, thickness=carcass_t))
    slide_length = derived("construction_assumption", [depth], _slide_depth_mm,
                           reason="Cabinet depth minus 100 mm, rounded down to a 100 mm step.")
    left, right = interval(appearance["bbox"], "x")
    edges = [left, *((boxes[a][2] + boxes[b][0]) / 2 for a, b in zip(ids, ids[1:])), right]
    for index, cid in enumerate(ids):
        face_width = box_dimension(view, printed, "x", cid)
        face_height = box_dimension(view, printed, "y", cid)
        bay_width = projected(view, printed, "x", edges[index:index + 2], [appearance["frame"], cid])
        wall_factor = (1.0 if index == 0 else .5) + (1.0 if index == len(ids) - 1 else .5)
        box_width = derived("construction_assumption", [bay_width, carcass_t],
                            lambda w, t: w - wall_factor * t - 26,
                            reason="Bay between assumed dividers and sides, less 13 mm slide clearance per side.")
        ref = f'{view["view_id"]}:{cid}'
        parts.append({**part("drawer_front", material=visible, length=face_width, width=face_height,
                             thickness=face_t), "instance_ref": ref})
        parts.extend(drawer_box_parts(box_width, face_height, slide_length, instance_ref=ref))
    parts.append({**part("drawer_slide", 2 * len(ids), material="drawer slide hardware", length=slide_length),
                  "unit": "piece"})
    return parts, ["Drawer internals, divider count, slide clearances and joint layout are provisional."]


def framed_panel_parts(block, measurements, views, printed, projections):
    appearance = next(row for row in block["appearances"] if row["view_id"] == measurements["width"]["view_id"])
    view = views[appearance["view_id"]]
    width, depth, height = (geometry_dimension(measurements[key]) for key in ("width", "depth", "height"))
    facing = "visible panel stock, substrate and finish to verify"
    sheet = stock(20)
    inner_w = derived("construction_assumption", [width, sheet], lambda w, t: w - 2 * t,
                      reason="Caps and backing fit between the two outer cheeks.")
    inner_h = derived("construction_assumption", [height, sheet], lambda h, t: h - 2 * t,
                      reason="Ribs and backing fit between the caps.")
    parts = [
        part("frame_side", 2, material=facing, length=height, width=depth, thickness=sheet),
        part("frame_cap", 2, material=facing, length=inner_w, width=depth, thickness=sheet),
        part("frame_backing", material=facing, length=inner_h, width=inner_w, thickness=sheet),
    ]
    faces = {projections[row["view_id"]] for row in block["appearances"]}
    if not {"Front elevation", "Rear view"} <= faces:
        raise ValueError("Symmetric frame assumption requires matching front and rear projections")
    cells = appearance["top_cell_ids"]
    boxes = contours(view)
    cells = sorted(cells, key=lambda cid: boxes[cid][0])
    rib_depth = derived("construction_assumption", [depth, sheet], lambda d, t: (d - t) / 2,
                        reason="Two matching faces around one assumed central backing sheet.")
    ribs = defaultdict(list)
    for left, right in zip(cells, cells[1:]):
        gap = projected(view, printed, "x", (boxes[left][2], boxes[right][0]), [left, right])
        ribs[gap["mm"]].append(gap)
    for mm, gaps in ribs.items():
        refs = dict.fromkeys(ref for gap in gaps for ref in gap["refs"])
        parts.append(part("vertical_rib", 2 * len(gaps), material=facing,
                          length=inner_h, width=rib_depth, thickness=dimension(mm, "scaled_projection", refs)))
    return parts, ["The visible dividers are measured as projected gaps between bays. The cut list assumes a symmetric frame with a central backing; verify rib profiles, joints and backing before fabrication."]


def supported_top_parts(block, measurements, views, printed, front, owner):
    top, = owner["appearances"]
    view = views[top["view_id"]]
    width, depth, height = (geometry_dimension(measurements[key]) for key in ("width", "depth", "leg_height"))
    crosscheck = measurements["depth"].get("axis_crosscheck")
    if crosscheck and crosscheck["view_id"] == view["view_id"] and depth["mm"] is not None:
        printed = {**printed, view["view_id"]: [*printed[view["view_id"]], {
            "axis": crosscheck["axis"], "bounds": crosscheck["bounds_1000"],
            "value_mm": depth["mm"], "source_id": depth["refs"][0],
        }]}
    top_ids = measurements["height"]["contour_ids"]
    boxes = contours(view)
    plate_ids = [cid for cid in top_ids if cid in boxes and
                 top["bbox"][1] - 1 <= boxes[cid][1] < boxes[cid][3] <= top["bbox"][3] + 1]
    plate_ids.sort(key=lambda cid: boxes[cid][1])
    if not plate_ids:
        raise ValueError("Supported top lacks an owned section contour")
    parts = []
    for index, cid in enumerate(plate_ids):
        thickness = box_dimension(view, printed, "y", cid)
        layer_depth = depth if index == 0 else box_dimension(view, printed, "x", cid)
        layer_width = width if index == 0 else derived(
            "construction_assumption", [width], lambda w: w,
            reason="Underlayer lateral extent provisionally follows the upper tabletop.")
        parts.append(part("tabletop" if index == 0 else "tabletop_underlayer", material="tabletop stock, finish to verify",
                          length=layer_width, width=layer_depth, thickness=thickness))
    grouped = defaultdict(set)
    for face in front:
        if face["role"] == "support_leg" and any(
                row.get("component") == "support" and row["view_id"] == face["view_id"]
                and row["bbox"] == face["bbox_px"] for row in block["appearances"]):
            grouped[face["view_id"]].add(face["candidate_id"])
    if not grouped or not grouped.get(view["view_id"]):
        raise ValueError("Supported top has no corroborated leg contours")
    count = max(map(len, grouped.values()))
    profiles = [box_dimension(view, printed, "x", cid) for cid in sorted(grouped[view["view_id"]])]
    profile = profiles[0] if len({value["mm"] for value in profiles}) == 1 else dimension(None, "unresolved")
    parts.append({**part("support_leg", count, material="support hardware, section and finish to verify",
                         length=height, section_width=profile),
                  "count_refs": [f"{vid}:{cid}" for vid, ids in grouped.items() for cid in sorted(ids)]})
    return parts, ["The support section width is a projection. Confirm section shape, wall thickness and attachment hardware with the supplier."]


def casework_span(view, printed, axis, bounds, ids):
    local = projected(view, printed, axis, bounds, ids)
    if local["mm"] is not None:
        return local
    size = view["width" if axis == "x" else "height"]
    scales = [(row["value_mm"] * 1000 / (size * (row["bounds"][1] - row["bounds"][0])), row)
              for row in printed.get(view["view_id"], []) if row["axis"] == axis]
    if len(scales) < 2:
        return local
    reference = median(scale for scale, _ in scales)
    if any(abs(scale / reference - 1) >= .045 for scale, _ in scales):
        return local
    scale, anchor = max(scales, key=lambda pair: pair[1]["value_mm"])
    return dimension((bounds[1] - bounds[0]) * scale, "scaled_projection",
                     [*local["refs"], anchor["source_id"]])


def casework_parts(block, measurements, views, printed, front):
    appearance, = block["appearances"]
    view = views[appearance["view_id"]]
    vid = view["view_id"]
    boxes = contours(view)
    face_rows = {row["candidate_id"]: row for row in front if row["view_id"] == vid and row.get("candidate_id")}
    groups = block["positions"]
    ids = [cid for group in groups for cid in group]
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= face_rows.keys() & boxes.keys():
        raise ValueError("Casework requires unique locked facade contours")

    def size(box, axis, ids):
        return casework_span(view, printed, axis, interval(box, axis), ids)

    width, height, depth = (geometry_dimension(measurements[key]) for key in ("width", "height", "depth"))
    review = ["Cabinet box layout and stock thicknesses are preliminary. Shelf and fitting layouts require evidence."]
    if depth["mm"] is None and "depth_proxy" in measurements:
        proxy = geometry_dimension(measurements["depth_proxy"])
        depth = derived("construction_assumption", [proxy], lambda d: min(600, d - 20),
                        reason="600 mm standard cabinet depth, capped to leave at least 20 mm within the worktop proxy.")
        review.append("Base depth is provisional. Geometry only binds the shared worktop depth, and local return shape may differ.")

    parts = []
    body = appearance["bbox"]
    extensions = [row for row in block.get("fixed_extensions", []) if row["view_id"] == vid]
    if any(row["bbox"][3] > body[3] + 8 for row in extensions):
        height = size(body, "y", ids)
        review.append("Cabinet height comes from the facade band. A lower fixed panel is listed separately.")
    if any(row["bbox"][0] < body[0] - 8 or row["bbox"][2] > body[2] + 8 for row in extensions):
        width = size(body, "x", ids)
        review.append("Cabinet width excludes the separately owned lateral panel.")

    sheet, back_t = stock(17), stock(6)
    inside_w = derived("construction_assumption", [width, sheet], lambda w, t: w - 2 * t,
                       reason="Horizontal panels and backing fit between the two sides.")
    inside_h = derived("construction_assumption", [height, sheet], lambda h, t: h - 2 * t,
                       reason="Backing and vertical divisions fit between the top and bottom panels.")
    carcass = "carcass sheet stock"
    parts += [part("carcass_side", 2, material=carcass, length=height, width=depth, thickness=sheet),
              part("carcass_top", material=carcass, length=inside_w, width=depth, thickness=sheet),
              part("carcass_bottom", material=carcass, length=inside_w, width=depth, thickness=sheet),
              part("carcass_back", material="backing sheet stock", length=inside_w, width=inside_h, thickness=back_t)]
    for row in extensions:
        cid = row["contour_id"]
        panel = part("fixed_panel", material="visible panel stock, profile to verify",
                     length=size(row["bbox"], "y", [cid]), width=size(row["bbox"], "x", [cid]), thickness=sheet)
        parts.append({**panel, "instance_ref": f"{vid}:{cid}"})

    group_kinds = [{face_rows[cid]["role"] for cid in group} for group in groups]
    partitions = sum(("drawer" in left) != ("drawer" in right) for left, right in zip(group_kinds, group_kinds[1:]))
    if partitions:
        clear_depth = derived("construction_assumption", [depth, back_t], lambda d, t: d - t,
                              reason="Vertical divisions stop against the backing.")
        parts.append(part("drawer_bay_divider", partitions, material=carcass,
                          length=inside_h, width=clear_depth, thickness=sheet))
    for cid in ids:
        role = face_rows[cid]["role"]
        length, face_h = (size(boxes[cid], axis, [cid]) for axis in ("x", "y"))
        ref = f"{vid}:{cid}"
        face_part = part(CASEWORK_FRONT_PARTS.get(role, "unresolved_front"), material="visible facade stock",
                         length=length, width=face_h, thickness=sheet)
        parts.append({**face_part, "instance_ref": ref})
        if role == "drawer":
            slide = derived("construction_assumption", [depth], _slide_depth_mm,
                            reason="Cabinet depth minus 100 mm, rounded down to a 100 mm step.")
            drawer_width = derived("construction_assumption", [length, sheet], lambda w, t: w - 2 * t - 26,
                                   reason="Use facade span as a bay proxy, allowing side panels and slide clearances.")
            parts.extend(drawer_box_parts(drawer_width, face_h, slide, instance_ref=ref))
            parts.append({**part("drawer_slide", 2, material="drawer slide hardware", length=slide),
                          "unit": "piece", "instance_ref": ref})
        elif role == "hinged_door" and face_h["mm"] is not None:
            parts.append({**part("hinge", _hinges_per_facade(face_h["mm"]), material="hinge hardware"),
                          "unit": "piece", "instance_ref": ref})
        elif role == "lift_up":
            parts.append({**part("gas_lift", material="lift-up hardware, load class to verify"),
                          "unit": "set", "instance_ref": ref})
    return parts, review


def plinth_runs(owner, views, printed):
    by_view = defaultdict(list)
    for row in owner["appearances"]:
        by_view[row["view_id"]].append(row)
    parts = []
    for vid, appearances in by_view.items():
        ordered = sorted(appearances, key=lambda row: row["bbox"][0])
        runs = []
        for row in ordered:
            if (runs and abs(runs[-1][-1]["bbox"][2] - row["bbox"][0]) <= 2
                    and max(abs(runs[-1][0]["bbox"][i] - row["bbox"][i]) for i in (1, 3)) <= 2):
                runs[-1].append(row)
            else:
                runs.append([row])
        for run in runs:
            ids = [row["contour_id"] for row in run]
            length = casework_span(views[vid], printed, "x", (run[0]["bbox"][0], run[-1]["bbox"][2]), ids)
            height = casework_span(views[vid], printed, "y", interval(run[0]["bbox"], "y"), ids)
            parts.append(part("plinth_visible_run", material="plinth sheet stock",
                              length=length, width=height, thickness=stock(17)))
    return parts


def shared_part(owner, blocks, views, printed):
    result = {"id": owner["id"], "role": owner["role"], "quantity": owner["quantity"],
              "unit": owner.get("unit", "piece"), "attached_block_ids": owner.get("attached_block_ids", []), "parts": []}
    if owner["role"] == "plinth" and len(owner["appearances"]) == 1 and len(owner["attached_block_ids"]) == 1 and "installed_height" in blocks[owner["attached_block_ids"][0]]:
        appearance, = owner["appearances"]
        view = views[appearance["view_id"]]
        cid = appearance["contour_id"]
        width = box_dimension(view, printed, "x", cid)
        height = box_dimension(view, printed, "y", cid)
        installed = blocks[owner["attached_block_ids"][0]]["installed_height"]
        depth = box_dimension(views[installed["view_id"]], printed, "x", installed["contour_ids"][-1])
        sheet = stock(17)
        return_length = derived("construction_assumption", [depth, sheet], lambda d, t: d - t,
                                reason="Returns fit behind the front rail.")
        result["parts"] = [part("plinth_front", material="plinth sheet stock", length=width, width=height, thickness=sheet),
                           part("plinth_return", 2, material="plinth sheet stock", length=return_length, width=height, thickness=sheet)]
        result["review"] = ["One kit for the object. Two returns are provisional; verify hidden rails and fixing method."]
    elif owner["role"] == "plinth" and owner.get("appearances"):
        result["parts"] = plinth_runs(owner, views, printed)
        result["review"] = ["Visible runs in one kit. Return pieces, corner joints and cut lengths require plan evidence."]
    elif owner["role"] == "worktop":
        result["parts"] = [part("shared_worktop", material="worktop stock, finish to verify",
                                length=dimension(None, "unresolved"), width=dimension(None, "unresolved"), thickness=stock(30))]
        result["review"] = ["One shared worktop scope. Outline, seam placement and cutouts require plan evidence."]
    else:
        result["review"] = ["Shared component construction unresolved."]
    return result


def compile_geometry_parts(analyze, geometry, views):
    """Preserve locked identities and report unsupported construction explicitly."""
    if (geometry["stage"] != "Block Geometry" or analyze["version"] != geometry["analyze_version"]
            or analyze["source_audit_sha256"] != geometry["source_audit_sha256"]
            or analyze["objects"].keys() != geometry["objects"].keys()):
        raise ValueError("Analyze and Block Geometry must describe the same source and objects")
    objects = {}
    for oid, obj in analyze["objects"].items():
        evidence = geometry["objects"][oid]
        printed = evidence["printed_dimensions"]
        planner = obj["planner"]
        readings = {row["block_id"]: row for row in evidence["blocks"]}
        blocks = planner["blocks"]
        if (len(readings) != len(evidence["blocks"]) or len(readings) != len(blocks)
                or {row["id"]: row["basis"] for row in blocks} != {bid: row["basis"] for bid, row in readings.items()}):
            raise ValueError(f"{oid} Block Geometry must cover the exact locked Blocks")
        object_views = {view["view_id"]: view for view in views if view["object_id"] == oid}
        front = obj["front"]["faces"]
        owners = defaultdict(list)
        for owner in planner.get("object_parts", []):
            if owner.get("envelope_block_id"):
                owners[owner["envelope_block_id"]].append(owner)
        result = {"blocks": [], "shared_parts": []}
        consumed = set()
        casework_refs = [f'{appearance["view_id"]}:{cid}' for block in blocks
                         if block["basis"] in CASEWORK_BASES for appearance in block["appearances"]
                         for group in block["positions"] for cid in group]
        if len(casework_refs) != len(set(casework_refs)):
            raise ValueError(f"{oid} has multiple Blocks claiming the same facade")
        if casework_refs:
            scope = set(casework_refs) | {f'{appearance["view_id"]}:{cid}' for block in blocks
                                         if block["basis"] == "shared_drawer_frame"
                                         for appearance in block["appearances"] for cid in appearance["drawer_faces"]}
            result["unassigned_fronts"] = [
                {"instance_ref": ref, "role": row["role"], "reason": "No locked casework position owns this observation."}
                for row in front if row["role"] in CASEWORK_FRONT_PARTS.keys() | {"unresolved_front", "pull_out_shelf"}
                and (ref := f'{row["view_id"]}:{row.get("candidate_id")}') not in scope
            ]
        for block in blocks:
            bid = block["id"]
            measurements = readings[bid]["measurements"]
            row = {"block_id": bid, "construction": block["basis"], "envelope": {
                key: geometry_dimension(value) for key, value in measurements.items()}, "parts": []}
            try:
                if block["basis"] == "shared_drawer_frame":
                    row["parts"], row["review"] = drawer_frame_parts(block, measurements, object_views, printed, front)
                elif block["basis"] == "matched_framed_panel":
                    row["parts"], row["review"] = framed_panel_parts(block, measurements, object_views, printed, analyze["islands"])
                elif block["basis"] == "independently_supported_extension":
                    owner, = owners[bid]
                    row["parts"], row["review"] = supported_top_parts(block, measurements, object_views, printed, front, owner)
                    row["object_part_id"] = owner["id"]
                    consumed.add(owner["id"])
                elif block["basis"] in CASEWORK_BASES:
                    row["parts"], row["review"] = casework_parts(block, measurements, object_views, printed, front)
                else:
                    row["review"] = ["Construction pattern unresolved."]
            except (KeyError, ValueError, StopIteration, IndexError) as exc:
                row["review"] = [f"Incomplete construction evidence: {exc}"]
            result["blocks"].append(row)
        for owner in planner.get("object_parts", []):
            if owner["id"] in consumed:
                continue
            try:
                row = shared_part(owner, {bid: item["measurements"] for bid, item in readings.items()}, object_views, printed)
            except (KeyError, IndexError) as exc:
                row = {"id": owner["id"], "role": owner["role"], "parts": [], "review": [f"Incomplete component evidence: {exc}"]}
            result["shared_parts"].append(row)
        objects[oid] = result
    return {"stage": "CB Parts", "version": VERSION, "status": "preliminary_requires_review",
            "source_audit_sha256": analyze["source_audit_sha256"], "provider_calls": 0, "objects": objects}
