"""Build V8 Block candidates from fresh Front readings and native boundaries."""

from collections import defaultdict
from math import hypot

from use_cases.estimation_block_locator_v8 import link_supported_worktop

from tools.probe_cb_adda_ownership import components, contact, corner_plan, edges, hull
from tools.probe_cb_block_boundaries import (
    ELEVATION_PROJECTIONS, ORTHOGRAPHIC_PLAN_LINK_TYPES, axis_overlap, build_report, compose_v11,
    edge_fraction, envelope, plan_span_matches, rectangular,
)


def orthographic_blocks(*, views, projections, faces, detection):
    elevations = sorted(vid for vid, role in projections.items() if role in ELEVATION_PROJECTIONS)
    report = build_report(views, faces, detection, elevations)
    obj, = [row for row in detection["objects"] if row["object_id"] == report["object_id"]]
    options = set()
    for relation in obj["accepted_observations"]:
        if relation["evidence_type"] not in ORTHOGRAPHIC_PLAN_LINK_TYPES:
            continue
        a, b = relation["group_id_a"], relation["group_id_b"]
        for plan, elevation in ((a, b), (b, a)):
            if projections.get(plan) != "Top view" or elevation not in elevations or not views[plan]["candidates"]:
                continue
            if any(block["basis"] == "tall_stack_candidate" and block["view_id"] == elevation
                   and plan_span_matches(block["bbox"], views[elevation], views[plan]) for block in report["blocks"]):
                options.add((plan, elevation))
    if len(options) == 1:
        plan, elevation = options.pop()
        report = build_report(views, faces, detection, elevations, plan, elevation)
    result = compose_v11(report, views, faces, projections, detection)
    object_parts = []
    supports = []
    for block in result["blocks"]:
        if not (extension := block.get("supported_top")):
            continue
        top, legs = [], []
        retained = []
        for appearance in block["appearances"]:
            component = appearance.get("component")
            if component == "tabletop":
                top.append(appearance)
            elif component == "support":
                legs.append(appearance)
            else:
                retained.append(appearance)
        if top and legs:
            block["appearances"] = retained
            support = {"id": f"B{len(result['blocks']) + len(supports) + 1:02}",
                       "basis": "independently_supported_extension", "appearances": legs,
                       "attachment": {"block_id": block["id"], "side_contour_id": extension["attached_side"]}}
            supports.append(support)
            object_parts.append({"id": f"P{len(object_parts) + 1:02}", "role": "worktop", "quantity": 1,
                                 "attached_block_ids": [support["id"], block["id"]], "appearances": top})
    result["blocks"].extend(supports)
    for vid in elevations:
        native = views[vid]["candidates"]
        used = {row["candidate_id"] for row in faces if row["view_id"] == vid}
        for contour in native:
            left, top, right, bottom = contour["bbox"]
            width = right - left
            if contour["id"] in used or width <= 0 or bottom - top < 5 * width:
                continue
            owners = []
            for block in result["blocks"]:
                for appearance in block["appearances"]:
                    x0, y0, x1, y1 = appearance["bbox"]
                    if (appearance["view_id"] == vid and abs(y1 - top) <= 4
                            and y0 < top and left >= x0 - 1 and right <= x1 + 1):
                        owners.append(block)
                        break
            if len(owners) == 1:
                owners[0].setdefault("fixed_extensions", []).append({"view_id": vid,
                    "contour_id": contour["id"], "bbox": contour["bbox"],
                    "basis": "unique aligned contact under the supported assembly"})
    rails = {}
    attached = set()
    for block in result["blocks"]:
        if block["basis"] in {"matched_framed_panel", "independently_supported_extension"}:
            continue
        for appearance in block["appearances"]:
            vid, box = appearance["view_id"], appearance["bbox"]
            for contour in views[vid]["candidates"]:
                left, top, right, bottom = contour["bbox"]
                width = right - left
                overlap = min(right, box[2]) - max(left, box[0])
                if (width <= 0 or bottom - top > .12 * width or abs(top - box[3]) > max(3, .02 * width)
                        or overlap < .6 * min(width, box[2] - box[0])):
                    continue
                rails[vid, contour["id"]] = {"view_id": vid, "contour_id": contour["id"], "bbox": contour["bbox"]}
                attached.add(block["id"])
    if rails:
        for (vid, _), reading in list(rails.items()):
            left, top, right, bottom = reading["bbox"]
            for contour in views[vid]["candidates"]:
                x0, y0, x1, y1 = contour["bbox"]
                if (x1 - x0 >= y1 - y0 and abs(y0 - top) <= 2 and abs(y1 - bottom) <= 2
                        and min(abs(x1 - left), abs(x0 - right)) <= 3):
                    rails[vid, contour["id"]] = {"view_id": vid, "contour_id": contour["id"], "bbox": contour["bbox"]}
        object_parts.append({"id": "plinth-kit", "role": "plinth", "quantity": 1, "unit": "set",
                             "status": "candidate", "appearances": list(rails.values()),
                             "attached_block_ids": sorted(attached)})
    return link_supported_worktop({**result, "version": "Estimation V8 native Block candidates",
                                   "object_parts": object_parts})


def marked_assembly_blocks(*, view, typed, raw, marks, leaders, rejected_mirrors=()):
    """Use source roles from this invocation. No reference labels enter grouping."""
    direct = {row["id"] for row in raw["direct_labels"] if row["source_text"]}
    mirrors = sorted(direct & {row["candidate_id"] for row in typed["items"] if row["role"] == "mirror"})
    annotation_roles = defaultdict(list)
    for row in raw["leader_readings"]:
        if row["source_text"]:
            annotation_roles[row["role"]].append(row["id"])
    rejected = set(rejected_mirrors)
    role_review = {"matches_by_role": {"mirror": {"matched": [ident for ident in mirrors if ident not in rejected],
                                                 "extra": [ident for ident in mirrors if ident in rejected]}},
                   "annotations_by_role": defaultdict(list, annotation_roles)}
    sides = {row["candidate_id"]: row["apex_side_on_view"] for row in marks}
    plan = corner_plan(view, typed, role_review, sides, leaders)
    contours = {row["id"]: row for row in view["candidates"]}
    shelves = {row["candidate_id"] for row in typed["items"] if row["role"] == "fixed_open_shelf"}
    attached_mirrors = []
    for block in plan["blocks"]:
        if block["basis"] != "mirror_upright":
            continue
        ident, = block["members"]
        owners = [owner for owner in plan["blocks"] if owner["basis"] == "return_door_band"
                  and any(contact(contours[ident], contours[shelf]) >= 20
                          for shelf in shelves.intersection(owner["members"]))]
        if len(owners) == 1:
            owners[0]["members"].append(ident)
            owners[0]["role_counts"]["mirror"] = owners[0]["role_counts"].get("mirror", 0) + 1
            attached_mirrors.append(block)
    plan["blocks"] = [block for block in plan["blocks"] if block not in attached_mirrors]
    for index, block in enumerate(plan["blocks"], 1):
        block["id"] = f"B{index:02}"
        block["appearances"] = {view["view_id"]: block["members"]}
    owners = {ident: block["id"] for block in plan["blocks"] for ident in block["members"]}
    label_bindings, pending = [], []
    for annotation in plan["annotation_ownership_pending"]:
        targets = {row["candidate_id"] for row in typed["items"] if annotation["id"] in row["source_ids"]}
        if targets and targets <= owners.keys():
            label_bindings.append({**annotation, "contour_ids": sorted(targets),
                                   "block_ids": sorted({owners[ident] for ident in targets})})
        else:
            pending.append(annotation)
    plan["annotation_ownership_pending"] = pending
    plan["annotation_bindings"] = label_bindings
    plan["object_parts"] = ([{"id": "plinth-kit", "role": "plinth", "quantity": 1, "unit": "set",
                              "source_view_id": view["view_id"], "contour_ids": plan["shared_rails"]}]
                            if plan["shared_rails"] else [])
    return plan


def labelled_bank_blocks(*, view, faces):
    """Group directly labelled drawers by native contact and retain independent mirrors."""
    vid = view["view_id"]
    contours = {row["id"]: row for row in view["candidates"]}
    drawers = [row["candidate_id"] for row in faces if row["role"] == "drawer" and row["candidate_id"] in contours]
    mirrors = [row["candidate_id"] for row in faces if row["role"] == "mirror" and row["candidate_id"] in contours]

    def neighbor(first, second):
        a, b = sorted((contours[first], contours[second]), key=lambda row: row["bbox"][0])
        x0, y0, x1, y1 = a["bbox"]
        u0, v0, _, v1 = b["bbox"]
        return (contact(a, b) >= 4 or (abs(u0 - x1) <= .02 * (x1 - x0)
                                      and max(abs(v0 - y0), abs(v1 - y1)) <= .55 * (y1 - y0)))

    groups = [("source_labelled_drawer_bank", ids) for ids in components(drawers, neighbor)]
    groups.extend(("mirror_upright", [ident]) for ident in mirrors)
    blocks = [{"id": f"B{index:02}", "basis": basis, "members": members, "appearances": {vid: members}}
              for index, (basis, members) in enumerate(groups, 1)]
    assigned = set(drawers + mirrors)
    for block in blocks:
        if block["basis"] != "source_labelled_drawer_bank":
            continue
        backing = []
        for ident in block["members"]:
            a = contours[ident]
            ranked = sorted((contact(a, b), key) for key, b in contours.items() if key not in assigned
                            and b["bbox"][3] > a["bbox"][3] and b["area"] > a["area"])
            if ranked and ranked[-1][0] > .5 * (a["bbox"][2] - a["bbox"][0]) and (
                    len(ranked) == 1 or ranked[-2][0] < .5 * ranked[-1][0]):
                backing.append(ranked[-1][1])
        block["supporting_contours"] = sorted(set(backing))
    return {"blocks": blocks, "object_parts": [], "unresolved": [row for row in faces
            if row["candidate_id"] not in assigned]}


def isolated_callout_outline(page, view, tip):
    """Find a unique small closed native line cycle under a labelled tip."""
    left, top, right, bottom = view["bbox_normalized"]
    page_width, page_height = page.rect.width, page.rect.height
    sx = view["width"] / ((right - left) * page_width)
    sy = view["height"] / ((bottom - top) * page_height)
    nodes, edges = [], defaultdict(dict)

    def point(raw):
        p = raw * page.rotation_matrix
        return ((p.x - left * page_width) * sx, (p.y - top * page_height) * sy)

    def snap(xy):
        for i, original in enumerate(nodes):
            if hypot(xy[0] - original[0], xy[1] - original[1]) <= 2.1:
                return i
        nodes.append(xy)
        return len(nodes) - 1

    for index, path in enumerate(page.get_drawings()):
        for item in path["items"]:
            if item[0] != "l":
                continue
            a, b = map(point, item[1:3])
            if max(hypot(p[0] - tip[0], p[1] - tip[1]) for p in (a, b)) > .22 * view["width"]:
                continue
            first, last = snap(a), snap(b)
            if first != last:
                edges[first][last] = edges[last][first] = index

    cycles = {}
    for start in edges:
        pending = [[start]]
        for path in pending:
            for neighbor in edges[path[-1]]:
                if neighbor == start and len(path) == 4:
                    outline = [nodes[i] for i in path]
                    hits = 0
                    for (x, y), (u, v) in zip(outline, outline[1:] + outline[:1]):
                        if (y > tip[1]) != (v > tip[1]) and tip[0] < x + (u - x) * (tip[1] - y) / (v - y):
                            hits += 1
                    if hits % 2:
                        keys = sorted(edges[a][b] for a, b in zip(path, path[1:] + path[:1]))
                        cycles[tuple(keys)] = {"outline_px": outline, "native_path_ids": keys}
                elif neighbor > start and neighbor not in path and len(path) < 4:
                    pending.append(path + [neighbor])
    return next(iter(cycles.values())) if len(cycles) == 1 else None


def attach_reviewed_sides(plan, views, reviewed):
    pending = []
    for row in reviewed:
        if row["role"] != "fixed_surface":
            continue
        vid, ident = row["view_id"], row["candidate_id"]
        contour, = [c for c in views[vid]["candidates"] if c["id"] == ident]
        box = contour["bbox"]
        width = box[2] - box[0]
        owners = []
        for block in plan["blocks"]:
            for appearance in block["appearances"]:
                if appearance["view_id"] != vid:
                    continue
                other = appearance["bbox"]
                distance = max(box[0] - other[2], other[0] - box[2])
                if (0 <= distance <= .1 * min(width, other[2] - other[0]) and axis_overlap(box, other, 1) >= .9
                        and box[3] - box[1] >= 2 * width):
                    owners.append(block)
                    break
        if len(owners) == 1:
            target = owners[0].setdefault("fixed_extensions", [])
            if all((r["view_id"], r["contour_id"]) != (vid, ident) for r in target):
                target.append({"view_id": vid, "contour_id": ident, "bbox": box,
                               "basis": "reviewed fixed side aligned with a unique adjacent assembly"})
        else:
            pending.append(row)
    plan["fixed_review_pending"] = pending


def attach_native_sides(plan, views, faces):
    """Recover unclaimed side panels on the elevation independently matched to the plan."""
    vid = plan.get("aligned_elevation_id")
    if vid is None:
        return
    contours = views[vid]["candidates"]
    frame = envelope(row["bbox"] for row in contours)
    groups = [(block, appearance["bbox"]) for block in plan["blocks"] if "positions" in block
              for appearance in block["appearances"] if appearance["view_id"] == vid]
    occupied = {row["candidate_id"] for row in faces if row["view_id"] == vid}
    occupied.update(row["contour_id"] for block in plan["blocks"]
                    for row in block.get("fixed_extensions", ()) if row["view_id"] == vid)
    choices = defaultdict(list)

    for contour in contours:
        box = contour["bbox"]
        width, height = box[2] - box[0], box[3] - box[1]
        if (contour["id"] in occupied or width <= 0 or height < 3 * width or not rectangular(contour)
                or min(edge_fraction(contour, 0, side) for side in (False, True)) < .9):
            continue
        owners = []
        for block, group in groups:
            frontage = group[2] - group[0]
            if not .08 * frontage <= width <= .67 * frontage or axis_overlap(box, group, 1) < .94:
                continue
            for side in (0, 2):
                opposite = 2 - side
                gap = (group[side] - box[opposite]) if side == 0 else (box[opposite] - group[side])
                if not 0 <= gap <= .1 * min(width, frontage):
                    continue
                # An exposed edge or a second, adjoining cabinet closes the seam.
                boundary = abs(box[side] - frame[side]) <= 2
                neighbor = any(
                    other is not block
                    and abs(edge[opposite] - box[side]) <= .1 * width
                    and edge[1] <= box[1] + 2 and edge[3] >= box[3] - 2
                    for other, edge in groups
                )
                if boundary or neighbor:
                    owners.append((block, side))
        if len(owners) == 1:
            block, side = owners[0]
            choices[block["id"], side].append((block, contour))

    for candidates in choices.values():
        if len(candidates) == 1:
            block, contour = candidates[0]
            block.setdefault("fixed_extensions", []).append({
                "view_id": vid, "contour_id": contour["id"], "bbox": contour["bbox"],
                "basis": "native full-height side at a uniquely owned assembly boundary",
            })


def resolve_locator_contours(plan, view, proposal):
    """Reconcile locator proposals with continuous rails, seams and top rims."""
    contours = {row["id"]: row for row in view["candidates"]}
    vid = view["view_id"]

    def strip(contour):
        a, b = max(edges(contour), key=lambda e: hypot(e[0][0] - e[1][0], e[0][1] - e[1][1]))
        dx, dy = (b[i] - a[i] for i in range(2))
        length = contour["bbox"][2] - contour["bbox"][0]
        return (contour["area"] / length, length) if length and abs(dx) > 2 * abs(dy) else (0, 0)

    def horizontal_slope(contour):
        a, b = max(edges(contour), key=lambda e: abs(e[0][0] - e[1][0]))
        return (b[1] - a[1]) / (b[0] - a[0]) if b[0] != a[0] else None

    plinth = {ident for part in plan["object_parts"] if part["role"] == "plinth"
              and part.get("source_view_id") == vid for ident in part["contour_ids"]}
    for ident in proposal["plinth"]:
        thickness, length = strip(contours[ident])
        if length and thickness <= .12 * length:
            plinth.add(ident)
    for ident in sorted(contours):
        if not plinth:
            break
        width, length = strip(contours[ident])
        if length >= 1.2 * width and any(.72 * strip(contours[ref])[0] <= width <= 1.28 * strip(contours[ref])[0]
                and contact(contours[ref], contours[ident]) >= .8 * width for ref in plinth):
            plinth.add(ident)

    base = {block["id"]: set(block["appearances"][vid] + block.get("supporting_contours", [])) - plinth
            for block in plan["blocks"]}
    lower = {block["id"] for block in plan["blocks"] if block["basis"] == "assumed_lower_frame_split"}
    occupied = set().union(*base.values()) | plinth
    claims = defaultdict(set)
    for bid, ids in proposal["add"].items():
        for ident in set(ids) - occupied:
            claims[ident].add(bid)

    # Source proposals that tie across assemblies need an actual shared edge.
    additions = {bid: set() for bid in base}
    for ident, bids in claims.items():
        width, length = strip(contours[ident])
        if length and width <= .12 * length:
            direct = [bid for bid in bids if max(contact(contours[ident], contours[ref]) for ref in base[bid]) >= .6 * length]
            if len(direct) != 1:
                continue  # Assign thin horizontal caps after the body is located.
            additions[direct[0]].add(ident)
            continue
        if len(bids) == 1:
            bid, = bids
        else:
            x0, y0, _, _ = contours[ident]["bbox"]
            aligned = [bid for bid in bids if any(abs(contours[ref]["bbox"][0] - x0) <= 2
                       and abs(contours[ref]["bbox"][3] - y0) <= 5
                       for ref in base[bid] | (set(proposal["add"][bid]) - {ident} - plinth))]
            if len(aligned) == 1:
                additions[aligned[0]].add(ident)
                continue
            scores = sorted((max(contact(contours[ident], contours[ref]) for ref in base[bid]), bid) for bid in bids)
            if scores[-1][0] < 12 or scores[-1][0] < 1.5 * scores[-2][0]:
                continue
            bid = scores[-1][1]
        additions[bid].add(ident)

    bodies = {bid: [contours[ident]["bbox"] for ident in base[bid] | additions[bid]] for bid in base}
    occupied.update(set().union(*additions.values()))
    for ident, contour in contours.items():
        if ident in occupied:
            continue
        thickness, length = strip(contour)
        if not length or thickness > .12 * length:
            continue
        left, top, right, bottom = contour["bbox"]
        matches = []
        for bid, boxes in bodies.items():
            if bid in lower:
                continue
            low = min(box[0] for box in boxes)
            high = max(box[2] for box in boxes)
            body_top = min(box[1] for box in boxes)
            overlap = min(high, right) - max(low, left)
            if overlap >= .65 * (right - left) and top <= body_top + 3 and bottom >= body_top - 12:
                matches.append((overlap, bid))
        matches.sort()
        if matches and (len(matches) == 1 or matches[-1][0] >= 1.5 * matches[-2][0]):
            additions[matches[-1][1]].add(ident)
            occupied.add(ident)

    # Close an omitted narrow end panel only when its strongest seam has one owner.
    for ident, contour in contours.items():
        if ident in occupied:
            continue
        left, top, right, bottom = contour["bbox"]
        if bottom - top < 2.5 * (right - left):
            continue
        slope = horizontal_slope(contour)
        scores = []
        for bid in base:
            shared = [(contact(contour, contours[ref]), horizontal_slope(contours[ref]))
                      for ref in base[bid] | additions[bid]]
            score = max((length for length, other in shared if slope is None or other is None or abs(slope - other) <= .10), default=0)
            scores.append((score, bid))
        scores.sort()
        if scores and scores[-1][0] >= .5 * (bottom - top) and (
                len(scores) == 1 or scores[-1][0] >= 1.4 * scores[-2][0]):
            additions[scores[-1][1]].add(ident)
            occupied.add(ident)
    return {"additions": {bid: sorted(ids) for bid, ids in additions.items()}, "plinth_ids": sorted(plinth)}


def close_display_envelopes(plan, view_id):
    """Use one projected exterior for each rectangular display carcass."""
    for block in plan["blocks"]:
        if block["basis"] != "drawer_and_pull_out_bay":
            continue
        envelope = block["envelopes"][view_id]
        polygons = envelope["polygons_px"]
        ys = [y for polygon in polygons for _, y in polygon]
        min_edge = .20 * (max(ys) - min(ys))
        sides = [x for polygon in polygons for (x, y), (u, v) in edges({"polygon": polygon})
                 if abs(v - y) >= min_edge and abs(u - x) <= .10 * abs(v - y)]
        if len(sides) < 2:
            continue
        left, right = min(sides), max(sides)
        if right <= left:
            continue
        points = [(x, y) for polygon in polygons for x, y in polygon if left <= x <= right]
        for polygon in polygons:
            for (x, y), (u, v) in edges({"polygon": polygon}):
                for boundary in (left, right):
                    if min(x, u) < boundary < max(x, u):
                        points.append((boundary, y + (v - y) * (boundary - x) / (u - x)))
        outline = hull(points)
        if len(outline) >= 3:
            envelope["source_polygons_px"] = polygons
            envelope["polygons_px"] = [outline]
            envelope["basis"] = "visible rectangular carcass exterior clipped to native side edges"
    return plan


def assemble_native_front_blocks(*, views, projections, detection, faces, review=(),
                                 marked_sources=None, labelled_sources=None, object_features=(),
                                 component_observations=None):
    """One repeatable handoff from fresh source readings to native assembly candidates."""
    from tools.probe_estimation_v8_grounded_front import (
        ground_front, ground_opening_pairs, linked_support_faces, review_front_roles, unresolved_adjacent_profiles,
    )

    marked_sources = marked_sources or {}
    labelled_sources = labelled_sources or {}
    objects = {}
    for obj in detection["objects"]:
        ident = obj["object_id"]
        own_views = {vid: view for vid, view in views.items() if view["object_id"] == ident}
        own_projections = {vid: projections[vid] for vid in own_views}
        raw = [row for row in faces if row["view_id"] in own_views]
        own_marked = [vid for vid in own_views if vid in marked_sources]
        own_labelled = [vid for vid in own_views if vid in labelled_sources]
        if len(own_marked) + len(own_labelled) > 1:
            raise ValueError("select one authoritative labelled face view per object")
        if own_marked:
            vid, = own_marked
            source = marked_sources[vid]
            typed = ground_opening_pairs(own_views[vid], source["marks"], source["items"])
            plan = marked_assembly_blocks(view=own_views[vid], typed=typed, raw=source["readings"],
                                          marks=source["marks"], leaders=source["leaders"])
            grounded = {"faces": [{**row, "view_id": vid} for row in typed["items"]],
                        "audit": [{"view_id": vid, "paired_native_marks": typed["pairs"],
                                   "conflicts": typed["conflicts"]}]}
        elif own_labelled:
            vid, = own_labelled
            grounded = {"faces": labelled_sources[vid], "audit": []}
            plan = labelled_bank_blocks(view=own_views[vid], faces=grounded["faces"])
        else:
            own_review = [row for row in review if row["view_id"] in own_views]
            revised = review_front_roles(raw, own_review)
            seen = {(row["view_id"], row["candidate_id"]) for row in revised["faces"]}
            revised["faces"].extend(row for row in linked_support_faces(own_views, own_projections,
                obj["accepted_observations"]) if (row["view_id"], row["candidate_id"]) not in seen)
            grounded = ground_front(revised["faces"], views=own_views, projections=own_projections)
            plan = orthographic_blocks(views=own_views, projections=own_projections,
                                       faces=grounded["faces"], detection=detection)
            primary = {appearance["view_id"] for block in plan["blocks"] for appearance in block["appearances"]
                       if appearance.get("matching_plan_spans")}
            if primary and own_review:
                reviewed_fixed = [row for row in own_review if row["role"] == "fixed_surface"]
                profiles = unresolved_adjacent_profiles(revised["faces"], views=own_views,
                    reviewed_fixed=reviewed_fixed, primary_elevations=primary)
                if profiles["audit"]:
                    grounded = ground_front(profiles["faces"], views=own_views, projections=own_projections)
                    grounded["audit"].extend(profiles["audit"])
                    plan = orthographic_blocks(views=own_views, projections=own_projections,
                                               faces=grounded["faces"], detection=detection)
            grounded["audit"].extend(revised["audit"])
            attach_reviewed_sides(plan, own_views, own_review)
            attach_native_sides(plan, own_views, grounded["faces"])

        for feature in object_features:
            if feature["view_id"] not in own_views:
                continue
            if feature.get("kind") == "component_callout":
                plan.setdefault("component_callouts", []).append(feature)
            elif feature["role"] == "window_closure":
                plan.setdefault("independent_elements", []).append(feature)
                plan["annotation_ownership_pending"] = [row for row in plan.get("annotation_ownership_pending", [])
                    if row["id"] != feature["annotation"]]
            elif feature["role"] == "worktop" and not any(row["role"] == "worktop" for row in plan["object_parts"]):
                plan["object_parts"].append(feature)
        if component_observations is not None:
            grounded["components"] = [row for row in component_observations
                                      if row["source"]["view_id"] in own_views]
        objects[ident] = {"front": grounded, "planner": plan,
                          "context_only_views": sorted(own_views.keys() - {row["view_id"] for row in grounded["faces"]})}
    return objects
