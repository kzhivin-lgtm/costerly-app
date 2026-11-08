"""Offline CB Planner boundary probe using frozen native contours and Front roles."""

import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont

from agents.estimation_understanding_agent import _json_object
from tools.probe_estimation_v7_4_visual_front import bind_island_faces, prepare
from use_cases.estimation_detection_context_v7 import digest


FRONT_ROLES = {"hinged_door", "drawer", "lift_up", "unresolved_front", "pull_out_shelf"}
ELEVATION_PROJECTIONS = {"Front elevation", "Side view", "Rear view"}
AUDIT_FILENAME = "estimation-offline-all-islands-evidence.json"


def envelope(boxes):
    left, top, right, bottom = zip(*boxes)
    return [min(left), min(top), max(right), max(bottom)]


def axis_overlap(a, b, axis):
    size = max(a[axis + 2] - a[axis], b[axis + 2] - b[axis])
    return (min(a[axis + 2], b[axis + 2]) - max(a[axis], b[axis])) / size


def vertical_neighbor(stack, face):
    first, previous, current = stack[0]["bbox"], stack[-1]["bbox"], face["bbox"]
    gap = current[1] - previous[3]
    width = min(previous[2] - previous[0], current[2] - current[0])
    return (-1 <= gap <= 0.06 * width
            and axis_overlap(previous, current, 0) >= 0.90
            and axis_overlap(first, current, 0) >= 0.90)


def front_positions(faces):
    stacks = []
    for face in sorted(faces, key=lambda row: (row["bbox"][1], row["bbox"][0], row["id"])):
        matches = [stack for stack in stacks if vertical_neighbor(stack, face)]
        if len(matches) == 1:
            matches[0].append(face)
        else:
            stacks.append([face])
    return [{"bbox": envelope(face["bbox"] for face in stack), "faces": stack} for stack in stacks]


def is_tall_stack(position):
    left, top, right, bottom = position["bbox"]
    return (len(position["faces"]) >= 3 and bottom - top >= 2.5 * (right - left)
            and any(face["role"] != "drawer" for face in position["faces"]))


def horizontal_neighbor(previous, current):
    a, b = previous["bbox"], current["bbox"]
    gap = b[0] - a[2]
    return -1 <= gap <= 0.15 * min(a[2] - a[0], b[2] - b[0]) and axis_overlap(a, b, 1) >= 0.85


def elevation_groups(faces):
    positions = front_positions(faces)
    groups, runs = [], []
    for position in sorted(positions, key=lambda row: tuple(row["bbox"])):
        if is_tall_stack(position):
            groups.append(("tall_stack_candidate", [position]))
            continue
        matches = [run for run in runs if horizontal_neighbor(run[-1], position)]
        if len(matches) == 1:
            matches[0].append(position)
        else:
            runs.append([position])
    # A four-position block requires a measured frontage bound to that group.
    # This probe has view-level dimensions but no reliable dimension endpoints.
    for run in runs:
        basis = "assumed_width_split" if len(run) > 3 else "visible_front_band"
        groups.extend((basis, run[index:index + 3]) for index in range(0, len(run), 3))
    return sorted(groups, key=lambda group: tuple(group[1][0]["bbox"]))


def plan_span_matches(bbox, elevation, plan):
    def span(box, frame):
        left, _, right, _ = frame
        return [(box[index] - left) / (right - left) for index in (0, 2)]

    target = span(bbox, envelope(row["bbox"] for row in elevation["candidates"]))
    plan_frame = envelope(row["bbox"] for row in plan["candidates"])
    return [row["id"] for row in plan["candidates"]
            if all(abs(a - b) <= 0.01 for a, b in zip(target, span(row["bbox"], plan_frame)))]


def box_area(box):
    return (box[2] - box[0]) * (box[3] - box[1])


def encloses(outer, inner):
    return box_area(outer) > box_area(inner) and all(
        outer[axis] - 1 <= inner[axis] and outer[axis + 2] + 1 >= inner[axis + 2]
        for axis in (0, 1)
    )


def rectangular(contour):
    return contour["area"] >= 0.95 * box_area(contour["bbox"])


def ordered_band(contours):
    return all(a["bbox"][2] - 1 <= b["bbox"][0] and axis_overlap(a["bbox"], b["bbox"], 1) >= 0.85
               for a, b in zip(contours, contours[1:]))


def drawer_leaves(seeds, contours):
    leaves = {}
    for seed in seeds:
        box = seed["bbox"]
        nested = [row for row in contours if rectangular(row) and encloses(box, row["bbox"])
                  and axis_overlap(box, row["bbox"], 1) >= 0.85]
        deepest = sorted(
            (row for row in nested if not any(encloses(row["bbox"], other["bbox"]) for other in nested)),
            key=lambda row: row["bbox"][0],
        )
        covered_width = sum(row["bbox"][2] - row["bbox"][0] for row in deepest)
        if covered_width >= 0.85 * (box[2] - box[0]) and ordered_band(deepest):
            leaves.update((row["id"], row) for row in deepest)
        else:
            leaves[seed["id"]] = seed
    return sorted(leaves.values(), key=lambda row: row["bbox"][0])


def edge_fraction(contour, axis, upper):
    box = contour["bbox"]
    fixed = box[axis + 2 * upper]
    other = 1 - axis
    points = contour["polygon"]
    intervals = sorted(sorted((a[other], b[other]))
                       for a, b in zip(points, points[1:] + points[:1])
                       if abs(a[axis] - fixed) <= 1 and abs(b[axis] - fixed) <= 1)
    covered, end = 0, box[other]
    for left, right in intervals:
        covered += max(0, right - max(left, end))
        end = max(end, right)
    return covered / (box[other + 2] - box[other])


def horizontal_edge_source(frame, contours, bottom):
    if edge_fraction(frame, 1, bottom) >= 0.9:
        return frame["id"]
    x0, y0, x1, y1 = frame["bbox"]
    target = y1 if bottom else y0
    matches = [row["id"] for row in contours
               if abs(row["bbox"][1 if bottom else 3] - target) <= 1
               and row["bbox"][0] <= x0 + 1 and row["bbox"][2] >= x1 - 1
               and edge_fraction(row, 1, not bottom) >= 0.9]
    return matches[0] if len(matches) == 1 else None


def frame_edges(frame, contours):
    if min(edge_fraction(frame, 0, False), edge_fraction(frame, 0, True)) < 0.9:
        return None
    top = horizontal_edge_source(frame, contours, bottom=False)
    bottom = horizontal_edge_source(frame, contours, bottom=True)
    if top and bottom:
        return {"left": frame["id"], "top": top, "right": frame["id"], "bottom": bottom}
    return None


def drawer_frame(view, readings):
    contours = view["candidates"]
    drawer_ids = {row["candidate_id"] for row in readings
                  if row["view_id"] == view["view_id"] and row["role"] == "drawer"}
    leaves = drawer_leaves([row for row in contours if row["id"] in drawer_ids], contours)
    if len(leaves) < 2 or not ordered_band(leaves):
        return None
    face_box = envelope(row["bbox"] for row in leaves)
    frames = []
    for contour in contours:
        box = contour["bbox"]
        if (encloses(box, face_box) and axis_overlap(box, face_box, 0) >= 0.8
                and axis_overlap(box, face_box, 1) >= 0.7
                and contour["area"] <= 0.5 * box_area(box)):
            edges = frame_edges(contour, contours)
            if edges:
                frames.append((contour, edges))
    if len(frames) != 1:
        return None
    contour, edges = frames[0]
    return {"view_id": view["view_id"], "bbox": contour["bbox"], "frame": contour["id"],
            "edges": edges, "drawer_seeds": sorted(drawer_ids),
            "drawer_faces": [row["id"] for row in leaves]}


def framed_panel_appearances(view):
    contours = view["candidates"]
    appearances = []
    for frame in contours:
        x0, y0, x1, y1 = frame["bbox"]
        width, height = x1 - x0, y1 - y0
        if height < 0.6 * width or frame["area"] > 0.5 * box_area(frame["bbox"]):
            continue
        cells = sorted((row for row in contours if rectangular(row)
                        and encloses(frame["bbox"], row["bbox"])
                        and row["bbox"][1] - y0 <= 0.12 * height),
                       key=lambda row: row["bbox"][0])
        if len(cells) < 3 or not ordered_band(cells):
            continue
        edges = frame_edges(frame, contours)
        if edges:
            appearances.append({
                "view_id": view["view_id"], "bbox": frame["bbox"], "frame": frame["id"], "edges": edges,
                "top_cell_ids": [row["id"] for row in cells],
                "bay_spans": [[(row["bbox"][i] - x0) / width for i in (0, 2)] for row in cells],
            })
    return appearances


def matching_bays(a, b):
    first, second = a["bay_spans"], b["bay_spans"]
    if a["view_id"] == b["view_id"] or len(first) != len(second):
        return False
    mirrored = [[1 - right, 1 - left] for left, right in reversed(second)]
    return any(all(abs(x - y) <= 0.025 for pair_a, pair_b in zip(first, spans)
                   for x, y in zip(pair_a, pair_b)) for spans in (second, mirrored))


def structural_candidates(views, readings):
    drawer_frames = [frame for view in views if (frame := drawer_frame(view, readings))]
    framed_panels = [appearance for view in views for appearance in framed_panel_appearances(view)]
    matches = [(a, b) for a, b in combinations(framed_panels, 2) if matching_bays(a, b)]
    candidates = [("shared_drawer_frame", [frame]) for frame in drawer_frames]
    if len(matches) == 1:
        candidates.append(("matched_framed_panel", list(matches[0])))
    return [{"id": f"B{index:02}", "basis": basis, "appearances": appearances}
            for index, (basis, appearances) in enumerate(candidates, 1)]


def connected_views(start, observations):
    reachable = {start}
    for _ in observations:
        for row in observations:
            pair = {row["group_id_a"], row["group_id_b"]}
            if pair & reachable:
                reachable.update(pair)
    return reachable


def supported_extensions(view):
    contours = view["candidates"]
    plates = [c for c in contours if rectangular(c)
              and c["bbox"][2] - c["bbox"][0] >= 8 * (c["bbox"][3] - c["bbox"][1])]
    extensions = []
    for plate in plates:
        left, top, right, bottom = plate["bbox"]
        sides = [c for c in contours if abs(c["bbox"][2] - left) <= 1
                 and c["bbox"][1] < top < bottom < c["bbox"][3]
                 and edge_fraction(c, 0, True) >= 0.9]
        legs = [c for c in contours if rectangular(c) and abs(c["bbox"][1] - bottom) <= 1
                and left <= c["bbox"][0] < c["bbox"][2] <= right
                and c["bbox"][3] - c["bbox"][1] >= 3 * (c["bbox"][2] - c["bbox"][0])]
        if len(sides) != 1 or not legs:
            continue
        upper = [c for c in plates if abs(c["bbox"][3] - top) <= 1
                 and abs(c["bbox"][0] - left) <= 1 and axis_overlap(c["bbox"], plate["bbox"], 0) >= 0.85]
        layers = upper + [plate]
        extensions.append({
            "view_id": view["view_id"],
            "top": {"bbox": envelope(c["bbox"] for c in layers), "contour_ids": [c["id"] for c in layers]},
            "supports": [{"bbox": c["bbox"], "contour_id": c["id"]} for c in legs],
            "attached_side": sides[0]["id"],
        })
    return extensions


def attach_supported_top(blocks, views, readings, projections, observations):
    frames = [block for block in blocks if block["basis"] == "shared_drawer_frame"]
    if len(frames) != 1:
        return
    block = frames[0]
    view_id = block["appearances"][0]["view_id"]
    linked = connected_views(view_id, observations)
    extensions = [extension for vid, kind in projections.items() if kind == "Side view" and vid in linked
                  for extension in supported_extensions(views[vid])]
    if len(extensions) != 1:
        return
    extension = extensions[0]
    side_view = extension["view_id"]
    directly_linked = {other for row in observations if side_view in (row["group_id_a"], row["group_id_b"])
                       for other in (row["group_id_a"], row["group_id_b"])} - {side_view}
    support_sets = {}
    for reading in readings:
        vid = reading["view_id"]
        if reading["role"] == "support_leg" and vid in directly_linked and vid in linked:
            for c in views[vid]["candidates"]:
                x0, y0, x1, y1 = c["bbox"]
                if c["id"] == reading["candidate_id"] and y1 - y0 >= 3 * (x1 - x0):
                    support_sets.setdefault(vid, []).append(c)
    ranked = sorted(support_sets.items(), key=lambda pair: (-len(pair[1]), pair[0]))
    block["supported_top"] = extension
    block["appearances"].extend([
        {"view_id": side_view, "bbox": extension["top"]["bbox"], "component": "tabletop"},
        *({"view_id": side_view, "bbox": row["bbox"], "component": "support"}
          for row in extension["supports"]),
    ])
    if ranked and (len(ranked) == 1 or len(ranked[0][1]) > len(ranked[1][1])):
        vid, legs = ranked[0]
        block["supports_evidence"] = {"view_id": vid, "contour_ids": [leg["id"] for leg in legs]}
        block["appearances"].extend({"view_id": vid, "bbox": leg["bbox"], "component": "support"}
                                    for leg in legs)


def compose_v11(report, views, readings, projections, detection):
    elevations = report["elevation_ids"]
    structural = structural_candidates([views[vid] for vid in elevations], readings)
    obj, = [obj for obj in detection["objects"] if obj["object_id"] == report["object_id"]]
    observations = obj["accepted_observations"]
    attach_supported_top(structural, views, readings, projections, observations)
    roles = {(row["view_id"], row["candidate_id"]): row["role"] for row in readings}
    retained, unassigned = [], []
    for block in report["blocks"]:
        vid, box = block["view_id"], block["bbox"]
        covered = any(appearance["view_id"] == vid and encloses(appearance["bbox"], box)
                      for parent in structural for appearance in parent["appearances"])
        if covered:
            continue
        if all(roles[(vid, cid)] == "unresolved_front" for slot in block["positions"] for cid in slot):
            unassigned.append(block)
            continue
        retained.append({"basis": block["basis"], "positions": block["positions"], "appearances": [
            {k: block[k] for k in ("view_id", "bbox", "matching_plan_spans") if k in block}
        ]})
    blocks = [{**block, "id": f"B{index:02}"}
              for index, block in enumerate(structural + retained, 1)]
    return {**report, "version": "CB Planner V11 offline", "blocks": blocks,
            "unassigned_candidates": unassigned,
            "non_grouped_front_observations": [
                {k: row[k] for k in ("view_id", "candidate_id", "role")}
                for row in readings if row["view_id"] not in elevations or row["role"] == "mirror"
            ]}


def build_report(views, readings, detection, elevations, plan_view=None, aligned_elevation=None):
    if not elevations or len(set(elevations)) != len(elevations):
        raise ValueError("unique elevation IDs are required")
    if (plan_view is None) != (aligned_elevation is None):
        raise ValueError("plan alignment requires both a plan and its matching elevation")
    object_id = views[elevations[0]]["object_id"]
    obj, = [obj for obj in detection["objects"] if obj["object_id"] == object_id]
    owned = {row["island_id"]: row for row in obj["islands"]}
    requested = set(elevations)
    if plan_view is not None:
        requested.add(plan_view)
    if (aligned_elevation is not None and aligned_elevation not in elevations) or not requested <= owned.keys():
        raise ValueError("the requested views must belong to one saved Detection object")
    for view_id in requested:
        view, island = views[view_id], owned[view_id]
        box = island["bbox"]
        coordinates = [box[key] for key in ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")]
        normalized = [value / island["coordinate_frame_pixels"][index % 2]
                      for index, value in enumerate(coordinates)]
        if (view["object_id"] != object_id or island["page_number"] != view["page"]
                or any(abs(a - b) >= 0.0003 for a, b in zip(normalized, view["bbox_normalized"], strict=True))):
            raise ValueError(f"Offline Vector and Detection Island frames disagree: {view_id}")
    observations = [row for row in obj["accepted_observations"]
                    if row["evidence_type"] == "matching_topology"
                    and {row["group_id_a"], row["group_id_b"]} == {plan_view, aligned_elevation}]
    if plan_view is not None and not observations:
        raise ValueError("no saved Detection topology observation for the requested plan alignment")

    blocks, unbound, omitted = [], [], {}
    for view_id in elevations:
        view = views[view_id]
        candidates = {row["id"]: row for row in view["candidates"]}
        selected = {}
        for reading in readings:
            if reading["view_id"] != view_id or reading["role"] not in FRONT_ROLES:
                continue
            ident = reading["candidate_id"]
            if ident not in candidates:
                unbound.append({"view_id": view_id, "role": reading["role"], "candidate_id": ident})
            elif ident in selected:
                raise ValueError(f"duplicate front contour: {view_id} {ident}")
            else:
                selected[ident] = {"id": ident, "role": reading["role"], "bbox": candidates[ident]["bbox"]}
        for basis, positions in elevation_groups(selected.values()):
            bbox = envelope(position["bbox"] for position in positions)
            block = {
                "id": f"B{len(blocks) + 1:02}", "view_id": view_id, "bbox": bbox, "basis": basis,
                "positions": [[face["id"] for face in position["faces"]] for position in positions],
            }
            if basis == "tall_stack_candidate" and view_id == aligned_elevation:
                block["matching_plan_spans"] = plan_span_matches(bbox, view, views[plan_view])
            blocks.append(block)
        omitted[view_id] = sorted(candidates.keys() - selected.keys())
    return {"object_id": object_id, "elevation_ids": elevations,
            "plan_view_id": plan_view, "aligned_elevation_id": aligned_elevation,
            "blocks": blocks, "unbound_fronts": unbound,
            "other_native_contours": omitted, "detection_topology_observations": observations,
            "width_policy": "Three positions unless the frontage of a four-position group is verified.",
            "provider_calls": 0}


def render_report(report, views, geometry_dir, document, output, *, structural=False, v11=False):
    blocks = report["blocks"]
    view_ids = sorted(report["elevation_ids"])
    palette = ("#2257a6", "#8c2da7", "#c3411c", "#007c6a", "#a35b00",
               "#007ca0", "#563c95", "#2e782a", "#b62469")
    colors = {ident: palette[index % len(palette)] for index, ident in enumerate(dict.fromkeys(
        block["id"] for block in blocks))}
    width, height, gap, header = 730, 640, 16, 78
    columns = min(2, len(view_ids)) if v11 else len(view_ids)
    rows = (len(view_ids) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (width + gap) + gap, rows * (height + 32) + header), "#eef4f8")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=17)
    title = "Offline structural contours" if structural else "Offline Block boundary candidates"
    caption = ("Outer edges from native contours. Same color = same candidate across views." if structural
               else "* Assumed split. Boxes enclose the assigned front contours.")
    if v11:
        title = "CB Planner V11 offline"
        caption = "* Assumed split. Repeated IDs show parts of one candidate. Plan/3D views are context only."
    draw.text((gap, 8), f"{document.capitalize()} {report['object_id']} | {title}",
              font=ImageFont.load_default(size=25), fill="#183048")
    draw.text((gap, 43), caption, font=font, fill="#183048")
    for index, view_id in enumerate(view_ids):
        view = views[view_id]
        with Image.open(geometry_dir / "full" / f"{document}-{view['number']:02}.png") as source:
            if source.size != (view["width"], view["height"]):
                raise ValueError(f"unexpected native crop size: {view_id}")
            tile = source.convert("RGB")
        painter = ImageDraw.Draw(tile)
        for block in blocks:
            if block["view_id"] != view_id:
                continue
            color = colors[block["id"]]
            painter.rectangle(block["bbox"], outline=color, width=4)
            left, top, _, _ = block["bbox"]
            mark = "*" if block["basis"] == "assumed_width_split" else ""
            component = " " + block["component"] if block.get("component") else ""
            painter.text((left + 5, top + 5), block["id"] + mark + component, fill=color, font=font,
                         stroke_width=2, stroke_fill="white")
        tile.thumbnail((width, height), Image.Resampling.LANCZOS)
        left = gap + index % columns * (width + gap)
        top = header + index // columns * (height + 32)
        count = sum(block["view_id"] == view_id for block in blocks)
        kind = report.get("island_projections", {}).get(view_id)
        label = f"{view_id} | {kind}" if v11 and kind else f"{view_id} | {count} candidates"
        draw.text((left, top - 20), label, font=font, fill="#183048")
        sheet.paste(tile, (left + (width - tile.width) // 2, top))
    sheet.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--front", type=Path, required=True)
    parser.add_argument("--detection", type=Path, required=True)
    parser.add_argument("--document", required=True)
    parser.add_argument("--object-id")
    elevation_source = parser.add_mutually_exclusive_group(required=True)
    elevation_source.add_argument("--elevations", nargs="+")
    elevation_source.add_argument("--saved-island-map", action="store_true",
                                  help="Read elevation types from the saved Analyze response in --detection")
    parser.add_argument("--plan-view")
    parser.add_argument("--aligned-elevation")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--structural-contours", action="store_true",
                       help="Probe shared drawer frames and repeated framed panels")
    modes.add_argument("--planner-v11", action="store_true",
                       help="Compose V11 offline Block candidates from structural and Front evidence")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    geometry = (args.geometry / AUDIT_FILENAME).read_bytes()
    all_views = json.loads(geometry)["documents"][args.document]
    object_ids = {row["object_id"] for row in all_views}
    object_id = args.object_id or (next(iter(object_ids)) if len(object_ids) == 1 else None)
    if object_id not in object_ids:
        parser.error("--object-id must identify one object in the geometry archive")
    selected_views = [row for row in all_views if row["object_id"] == object_id]
    views = {view["view_id"]: view for view in selected_views}
    witness = json.loads(args.front.read_bytes())
    if selected_views == all_views:
        request, frames, _ = prepare(args.geometry, args.document, per_island=True)
    else:
        with TemporaryDirectory() as folder:
            scoped = Path(folder)
            (scoped / "full").symlink_to(args.geometry.resolve() / "full", target_is_directory=True)
            (scoped / AUDIT_FILENAME).write_text(json.dumps({"documents": {args.document: selected_views}}))
            request, frames, _ = prepare(scoped, args.document, per_island=True)
    if (witness["source_request_sha256"] != sha256(geometry).hexdigest() or witness["provider_request"] != request
            or witness["request_sha256"] != digest(request)):
        raise ValueError("Front witness is not bound to this Offline Vector archive")
    front = bind_island_faces(witness["model_readings"], frames)
    if front != witness["bound_fronts"]:
        raise ValueError("saved Front bindings do not replay against the source contours")
    saved = json.loads(args.detection.read_bytes())
    detection = saved["detection_context"]
    elevations, projections = args.elevations, {}
    plan_view, aligned_elevation = args.plan_view, args.aligned_elevation
    pairs = set()
    if args.saved_island_map:
        if saved["stop_reason"] != "end_turn":
            raise ValueError("saved Island Map response is incomplete")
        result = _json_object(saved["raw_response_text"])
        obj, = [obj for obj in result["objects"] if obj["object_id"] == object_id]
        projections = {row["island_id"]: row["projection"] for row in obj["islands"]}
        if len(projections) != len(obj["islands"]) or projections.keys() != views.keys():
            raise ValueError("saved Island Map does not match the frozen object membership")
        elevations = sorted(view_id for view_id, kind in projections.items() if kind in ELEVATION_PROJECTIONS)
        if plan_view is None and aligned_elevation is None:
            detected, = [obj for obj in detection["objects"] if obj["object_id"] == object_id]
            for observation in detected["accepted_observations"]:
                if observation["evidence_type"] != "matching_topology":
                    continue
                a, b = observation["group_id_a"], observation["group_id_b"]
                for top, elevation in ((a, b), (b, a)):
                    if projections.get(top) == "Top view" and elevation in elevations:
                        pairs.add((top, elevation))
            if len(pairs) == 1:
                plan_view, aligned_elevation = pairs.pop()
    report = build_report(views, front["faces"], detection, elevations, plan_view, aligned_elevation)
    if args.planner_v11 and len(pairs) > 1:
        matching_pairs = {(plan, elevation) for plan, elevation in pairs
                          if views[plan]["candidates"] and any(
                              block["basis"] == "tall_stack_candidate" and block["view_id"] == elevation
                              and plan_span_matches(block["bbox"], views[elevation], views[plan])
                              for block in report["blocks"])}
        if len(matching_pairs) == 1:
            plan_view, aligned_elevation = matching_pairs.pop()
            report = build_report(views, front["faces"], detection, elevations, plan_view, aligned_elevation)
    if projections:
        report["island_projections"] = projections
        report["skipped_projections"] = {view_id: kind for view_id, kind in projections.items()
                                         if view_id not in elevations}
    display = report
    if args.structural_contours:
        report["baseline_blocks"] = report["blocks"]
        report["blocks"] = structural_candidates([views[view_id] for view_id in elevations], front["faces"])
        shapes = [{**appearance, "id": block["id"], "basis": block["basis"]}
                  for block in report["blocks"] for appearance in block["appearances"]]
        display = {**report, "blocks": shapes,
                   "elevation_ids": sorted({shape["view_id"] for shape in shapes}) or elevations}
    if args.planner_v11:
        report = compose_v11(report, views, front["faces"], projections, detection)
        display = {**report, "elevation_ids": sorted(views), "blocks": [
            {**appearance, "id": block["id"], "basis": block["basis"]}
            for block in report["blocks"] for appearance in block["appearances"]
        ]}
    args.output_dir.mkdir(mode=0o700)
    (args.output_dir / "boundaries.json").write_text(json.dumps(report, indent=2) + "\n")
    render_report(display, views, args.geometry, args.document, args.output_dir / "overlay.png",
                  structural=args.structural_contours, v11=args.planner_v11)


if __name__ == "__main__":
    main()
