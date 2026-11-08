"""Replay Adda ownership and explicit paired leaves from frozen drawing evidence."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from math import hypot
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def read_json(path):
    return json.loads(path.read_bytes())


def edges(contour):
    points = contour["polygon"]
    return list(zip(points, points[1:] + points[:1]))


def overlap(a, b):
    (x, y), (u, v) = a
    length = hypot(u - x, v - y)
    if length < 1:
        return 0
    dx, dy = (u - x) / length, (v - y) / length
    (p, q), (r, s) = b
    if max(abs((p - x) * dy - (q - y) * dx), abs((r - x) * dy - (s - y) * dx)) > 1.2:
        return 0
    start, end = sorted(((p - x) * dx + (q - y) * dy, (r - x) * dx + (s - y) * dy))
    return max(0, min(length, end) - max(0, start))


def contact(a, b, *, vertical=False):
    return max((overlap(edge, other) for edge in edges(a) for other in edges(b)
                if not vertical or abs(edge[0][0] - edge[1][0]) <= 0.06 * abs(edge[0][1] - edge[1][1])),
               default=0)


def components(ids, joined):
    pending = list(ids)
    groups = []
    while pending:
        group = [pending.pop(0)]
        for member in group:
            connected = [item for item in pending if joined(member, item)]
            group.extend(connected)
            pending = [item for item in pending if item not in connected]
        groups.append(group)
    return groups


def horizontal_overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0]))


def center_y(contour):
    box = contour["bbox"]
    return (box[1] + box[3]) / 2


def spans_side_tips(contour, tips):
    if len(tips) != 2:
        return False
    left, top, right, bottom = contour["bbox"]
    a, b = sorted(tips)
    return abs(a[0] - left) <= 3 and abs(b[0] - right) <= 3 and all(top < y < bottom for _, y in (a, b))


def door_groups(view, contours, typed, marks):
    doors = [key for key, row in typed.items() if row["role"] == "hinged_door"]
    rows = components(doors, lambda a, b: contact(contours[a], contours[b], vertical=True) >= 20)
    pairs = []
    for mark in view["x_marks"]:
        if len(mark["leaf_candidates"]) != 2:
            continue
        left, right = sorted(mark["leaf_candidates"], key=lambda key: contours[key]["bbox"][0])
        if left not in doors or right not in doors or marks.get(left) != "right" or marks.get(right) != "left":
            continue
        seam = contact(contours[left], contours[right], vertical=True)
        supports = [key for key, row in contours.items() if key not in doors
                    and min(contact(contours[left], row), contact(contours[right], row)) >= 20]
        if seam >= 20 and supports:
            pairs.append({"leaves": [left, right], "apex": mark["center"],
                          "shared_seam_px": round(seam, 2), "shared_border_contours": supports})
    blocks = []
    for row in sorted(rows, key=lambda ids: min(contours[key]["bbox"][1] for key in ids)):
        paired = [pair for pair in pairs if set(pair["leaves"]) <= set(row)]
        covered = [key for pair in paired for key in pair["leaves"]]
        if len(set(covered)) != len(covered):
            raise ValueError("overlapping leaf-pair evidence")
        positions = [pair["leaves"] for pair in paired] + [[key] for key in row if key not in covered]
        for index in range(0, len(positions), 3):
            slots = positions[index:index + 3]
            blocks.append({"basis": "return_door_band", "positions": slots,
                           "members": [key for slot in slots for key in slot]})
    return blocks, pairs


def lower_structure(contours, occupied):
    candidates = []
    for key, rail in contours.items():
        x0, _, x1, _ = rail["bbox"]
        width = x1 - x0
        if width == 0 or rail["area"] > 0.05 * width * width:
            continue
        margin = max(2, 0.01 * width)
        above = [ident for ident, row in contours.items()
                 if ident != key and ident not in occupied and row["area"] >= 0.3 * rail["area"]
                 and row["bbox"][0] >= x0 - margin and row["bbox"][2] <= x1 + margin
                 and row["bbox"][1] < rail["bbox"][1] and contact(rail, row) >= 35]
        if len(above) >= 3:
            candidates.append((key, sorted(above, key=lambda ident: contours[ident]["bbox"][0])))
    if len(candidates) != 1:
        return [], []
    rail, members = candidates[0]
    blocks = [{"basis": "assumed_lower_frame_split", "members": members[index:index + 3], "rail": rail}
              for index in range(0, len(members), 3)]
    return blocks, [rail]


def corner_plan(view, typed_result, role_review, marks, leaders):
    contours = {row["id"]: row for row in view["candidates"]}
    typed = {row["candidate_id"]: row for row in typed_result["items"]}
    blocks, pairs = door_groups(view, contours, typed, marks)
    assigned = {key for block in blocks for key in block["members"]}
    for block in blocks:
        block["border_evidence"] = sorted({key for pair in pairs if set(pair["leaves"]) <= set(block["members"])
                                            for key in pair["shared_border_contours"]})
    for key, row in typed.items():
        if row["role"] != "drawer":
            continue
        owners = [block for block in blocks if key in block["border_evidence"] and any(
            typed[member]["role"] == "hinged_door" and center_y(contours[member]) < center_y(contours[key])
            and contact(contours[member], contours[key]) >= 20 for member in block["members"])]
        if len(owners) == 1:
            owners[0]["members"].append(key)
            assigned.add(key)
    accessories = [key for key, row in typed.items()
                   if row["role"] in {"drawer", "pull_out_shelf"} and key not in assigned]
    def accessory_neighbor(a, b):
        first, second = typed[a], typed[b]
        if first["role"] == second["role"] == "pull_out_shelf":
            return bool(set(first["source_ids"]) & set(second["source_ids"]))
        boxes = contours[a]["bbox"], contours[b]["bbox"]
        return horizontal_overlap(*boxes) >= 0.5 * min(box[2] - box[0] for box in boxes)
    for group in components(accessories, accessory_neighbor):
        blocks.append({"basis": "drawer_and_pull_out_bay", "members": group})
        assigned.update(group)
    matches = set(role_review["matches_by_role"]["mirror"]["matched"])
    for key, row in typed.items():
        if row["role"] == "mirror" and key in matches:
            blocks.append({"basis": "mirror_upright", "members": [key]})
            assigned.add(key)
    for key, row in typed.items():
        if row["role"] != "fixed_open_shelf":
            continue
        owners = [block for block in blocks if block["basis"] == "return_door_band"
                  and max(contact(contours[key], contours[member])
                          for member in block["members"] + block["border_evidence"]) >= 20]
        if len(owners) == 1:
            owners[0]["members"].append(key)
            assigned.add(key)
    for block in blocks:
        if block["basis"] == "return_door_band":
            for key in block["border_evidence"]:
                if key not in assigned and sum(key in owner.get("border_evidence", []) for owner in blocks) == 1:
                    block["members"].append(key)
                    assigned.add(key)
    mirror_rebindings = []
    lighting = role_review["annotations_by_role"]["lighting"]
    for key in role_review["matches_by_role"]["mirror"]["extra"]:
        if key not in typed:
            continue
        original = contours[key]["bbox"]
        supported = [(candidate_id, annotation) for candidate_id, candidate in contours.items()
                     if candidate_id not in assigned and candidate_id != key
                     and min(abs(original[2] - candidate["bbox"][0]), abs(original[0] - candidate["bbox"][2])) <= 5
                     and abs(center_y(contours[key]) - center_y(candidate)) <= 0.1 * (original[3] - original[1])
                     for annotation in lighting
                     if spans_side_tips(candidate, [tip["xy_px"] for tip in leaders[annotation]["tips"]])]
        if len(supported) != 1:
            continue
        candidate_id, annotation = supported[0]
        owners = [block for block in blocks if block["basis"] == "return_door_band" and any(
            typed.get(member, {}).get("role") == "fixed_open_shelf"
            and contact(contours[candidate_id], contours[member]) >= 20 for member in block["members"])]
        if len(owners) == 1:
            owners[0]["members"].append(candidate_id)
            assigned.update((key, candidate_id))
            mirror_rebindings.append({"rejected_contour": key, "source_contour": candidate_id, "leader": annotation})
    for block in blocks:
        if block["basis"] != "return_door_band":
            continue
        shelves = [contours[key] for key in block["members"]
                   if typed.get(key, {}).get("role") == "fixed_open_shelf"]
        for shelf in shelves:
            for key, contour in contours.items():
                if (key not in block["members"] and (key not in assigned or any(
                        row["rejected_contour"] == key for row in mirror_rebindings))
                        and center_y(contour) < center_y(shelf) and contact(contour, shelf) >= 20):
                    block["members"].append(key)
                    assigned.add(key)
    lower, rails = lower_structure(contours, assigned)
    blocks.extend(lower)
    assigned.update(key for block in lower for key in block["members"])
    owners = Counter(key for block in blocks for key in block["members"])
    if any(count != 1 for count in owners.values()):
        raise ValueError("a native member was assigned more than once")
    unresolved = [{"candidate_id": key, "role": row["role"]} for key, row in typed.items() if key not in assigned]
    rejected_mirrors = {row["rejected_contour"] for row in mirror_rebindings}
    roles = {key: row["role"] for key, row in typed.items() if key not in rejected_mirrors}
    roles.update((row["source_contour"], "mirror") for row in mirror_rebindings)
    for block in blocks:
        block["role_counts"] = dict(sorted(Counter(roles[key] for key in block["members"] if key in roles).items()))
    annotations_pending = []
    mirror_ids = matches | {row["source_contour"] for row in mirror_rebindings}
    for role, annotation_ids in role_review["annotations_by_role"].items():
        for ident in annotation_ids:
            tips = [tip["xy_px"] for tip in leaders[ident]["tips"]]
            owners = []
            for block in blocks:
                bounds = [contours[key]["bbox"] for key in block["members"]]
                if (role == "glazed_zone" and block["basis"] == "drawer_and_pull_out_bay"
                        and all(min(b[0] for b in bounds) <= x <= max(b[2] for b in bounds) for x, _ in tips)):
                    owners.append(block)
                if role == "lighting" and any(spans_side_tips(contours[key], tips)
                                               for key in mirror_ids.intersection(block["members"])):
                    owners.append(block)
            if len(owners) == 1:
                owners[0].setdefault("annotations", []).append({"id": ident, "role": role})
            else:
                annotations_pending.append({"id": ident, "role": role})
    return {"blocks": blocks, "pairs": pairs, "shared_rails": rails, "unresolved": unresolved,
            "mirror_rebindings": mirror_rebindings, "annotation_ownership_pending": annotations_pending}


def straight_plan(views, readings, baseline, observations):
    base, = baseline["blocks"]
    face = base["appearances"][0]["view_id"]
    members = [key for slot in base["positions"] for key in slot]
    drawers = {row["candidate_id"] for row in readings if row["view_id"] == face and row["role"] == "drawer"}
    blocks = [{"basis": "continuous_base", "appearances": {face: members},
               "role_counts": {"drawer": len(drawers.intersection(members))}}]
    mirror, = [row for row in readings if row["role"] == "mirror" and row["candidate_id"]]
    vid = mirror["view_id"]
    drawer_ids = {row["candidate_id"] for row in readings if row["role"] == "drawer" and row["view_id"] == vid}
    mirror_id = mirror["candidate_id"]
    blocks.append({"basis": "mirror_upright", "appearances": {vid: [mirror_id]}, "role_counts": {"mirror": 1}})
    fronts = [{key for tip in leader["tips"] for key in tip["hits"]} for leader in views[vid]["arrows"]]
    matches = [group for group in fronts if len(group) == len(base["positions"]) and group <= drawer_ids]
    if len(matches) == 1:
        blocks[0]["appearances"][vid] = sorted(matches[0])
    face_contours = {row["id"]: row for row in views[face]["candidates"]}
    unresolved = []
    for block in baseline["unassigned_candidates"]:
        other_view = block["view_id"]
        for key in (key for slot in block["positions"] for key in slot):
            if other_view == face and sum(contact(face_contours[key], face_contours[member]) >= 20
                                          for member in members) >= 2:
                blocks[0]["appearances"][face].append(key)
                continue
            if any({edge["group_id_a"], edge["group_id_b"]} == {vid, other_view} for edge in observations):
                side = {row["id"]: row for row in views[other_view]["candidates"]}
                supports = [row["candidate_id"] for row in readings if row["view_id"] == other_view
                            and row["role"] == "support_leg" and row["candidate_id"] in side
                            and center_y(side[row["candidate_id"]]) > center_y(side[key])
                            and contact(side[key], side[row["candidate_id"]]) >= 20]
                if supports:
                    blocks[0]["appearances"][other_view] = [key] + supports
                    continue
            unresolved.append({"view_id": other_view, "candidate_id": key})
    return {"blocks": blocks, "unresolved": unresolved}


def hull(points):
    points = sorted(set(map(tuple, points)))
    def chain(sequence):
        result = []
        for point in sequence:
            while len(result) >= 2:
                a, b = result[-2:]
                cross = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
                if cross > 0:
                    break
                result.pop()
            result.append(point)
        return result[:-1]
    return chain(points) + chain(reversed(points))


def overlay(result, views, geometry, output):
    palette = ("#2257a6", "#8c2da7", "#c3411c", "#007c6a", "#a35b00",
               "#007ca0", "#563c95", "#2e782a", "#b62469")
    width, height, gap, header = 700, 600, 16, 94
    sheet = Image.new("RGB", (2 * width + 3 * gap, header + 4 * (height + 36)), "#eef4f8")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    draw.text((gap, 9), "Adda | Offline Planner ownership and explicit door pairs",
              font=ImageFont.load_default(size=25), fill="#183048")
    draw.text((gap, 47), "Outlined envelopes show assigned evidence. Context-only views have no new blocks.",
              font=font, fill="#183048")
    for row_index, (obj, plan) in enumerate(result.items()):
        for index, view in enumerate(sorted((v for v in views.values() if v["object_id"] == obj),
                                            key=lambda v: v["view_id"])):
            vid = view["view_id"]
            contours = {row["id"]: row for row in view["candidates"]}
            with Image.open(geometry / "full" / f"adda-{view['number']:02}.png") as image:
                tile = image.convert("RGB")
            painter = ImageDraw.Draw(tile)
            for block_index, block in enumerate(plan["blocks"]):
                members = block["appearances"].get(vid, [])
                if not members:
                    continue
                points = hull(point for key in members for point in contours[key]["polygon"])
                color = palette[block_index % len(palette)]
                painter.line(points + points[:1], fill=color, width=5)
                left, top = min(x for x, _ in points), min(y for _, y in points)
                painter.text((left + 5, top + 5), block["id"], fill=color, font=font,
                             stroke_width=2, stroke_fill="white")
            for element in plan.get("independent_elements", []):
                if element["view_id"] == vid:
                    points = [tuple(point) for point in element["outline_px"]]
                    painter.line(points + points[:1], fill="#475569", width=4)
                    x0, y0 = points[0]
                    painter.text((x0 + 4, y0 + 4), element["id"], fill="#475569", font=font)
            tile.thumbnail((width, height), Image.Resampling.LANCZOS)
            x = gap + index % 2 * (width + gap)
            y = header + (2 * row_index + index // 2) * (height + 36)
            draw.text((x, y), f"{obj} | {vid}", fill="#183048", font=font)
            sheet.paste(tile, (x + (width - tile.width) // 2, y + 25))
    sheet.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--front", type=Path, required=True, help="Restored V7.5 checkpoint package")
    parser.add_argument("--typed", type=Path, required=True, help="Restored V7.4 checkpoint package")
    parser.add_argument("--baseline", type=Path, required=True, help="Restored V11 result directory")
    parser.add_argument("--detection", type=Path, required=True, help="Saved Adda Analyze witness")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    geometry = args.front / "geometry"
    audit = (geometry / "estimation-offline-all-islands-evidence.json").read_bytes()
    mark_audit = read_json(args.typed / "geometry" / "all-island-mark-sweep.json")
    if sha256(audit).hexdigest() != mark_audit["audit_sha256"]:
        raise ValueError("opening marks use a different contour archive")
    views = {view["view_id"]: view for view in json.loads(audit)["documents"]["adda"]}
    role_review = read_json(args.typed / "reports" / "adda-v01-single-run.json")
    witness = (args.typed / "witnesses" / "adda-combined.json").read_bytes()
    if sha256(witness).hexdigest() != role_review["witness_sha256"]:
        raise ValueError("the typed Front witness does not match the frozen report")
    vid = role_review["view_id"]
    mark_view, = [view for view in mark_audit["documents"]["adda"] if view["view_id"] == vid]
    marks = {mark["candidate_id"]: mark["apex_side_on_view"] for mark in mark_view["opening_marks"]}
    leaders = read_json(args.typed / "geometry" / "neutral-geometry.json")["leaders"]
    corner = corner_plan(views[vid], json.loads(witness)["bound_fronts"], role_review, marks, leaders)
    reference = (args.typed / "geometry" / "adda-v01-full-review.json").read_bytes()
    if sha256(reference).hexdigest() != role_review["reference_sha256"]:
        raise ValueError("the archived structural reference does not match the frozen report")
    cover = json.loads(reference)["window_closure"]
    corner["independent_elements"] = []
    for annotation in list(corner["annotation_ownership_pending"]):
        if (annotation["role"] == "cover" and cover["count"] == 1
                and hypot(*(a - b for a, b in zip(cover["leader"]["root"], leaders[annotation["id"]]["root_px"]))) <= 2):
            corner["independent_elements"].append({
                "id": "S01", "role": "window_closure", "view_id": vid, "annotation": annotation["id"],
                "outline_px": cover["outline_px"], "native_path_ids": cover["path_ids"],
                "basis": "archived window closure geometry with a matching leader",
            })
            corner["annotation_ownership_pending"].remove(annotation)
    for block in corner["blocks"]:
        block["appearances"] = {vid: block["members"]}
    corner["context_only"] = sorted(key for key, view in views.items() if view["object_id"] == mark_view["object_id"] and key != vid)
    straight_baseline = read_json(args.baseline / "adda-object-001" / "boundaries.json")
    front = read_json(args.front / "witnesses" / "adda-object-001.json")["bound_fronts"]["faces"]
    detection = read_json(args.detection)["detection_context"]
    obj, = [row for row in detection["objects"] if row["object_id"] == straight_baseline["object_id"]]
    straight = straight_plan(views, front, straight_baseline, obj["accepted_observations"])
    result = {straight_baseline["object_id"]: straight, mark_view["object_id"]: corner}
    for plan in result.values():
        for index, block in enumerate(plan["blocks"], 1):
            block["id"] = f"B{index:02}"
    args.output_dir.mkdir(mode=0o700)
    (args.output_dir / "ownership.json").write_text(json.dumps({"provider_calls": 0, "objects": result}, indent=2) + "\n")
    overlay(result, views, geometry, args.output_dir / "overlay.png")


if __name__ == "__main__":
    main()
