"""Reconcile model Front readings with neutral native drawing evidence."""

from collections import defaultdict
from itertools import combinations

from tools.probe_cb_block_boundaries import (
    axis_overlap, connected_views, drawer_leaves, encloses, ordered_band, rectangular, supported_extensions,
)
from tools.probe_cb_adda_ownership import door_groups


def ground_opening_pairs(view, marks, rows):
    """Bind paired opening strokes without asking the model to read them again."""
    contours = {row["id"]: row for row in view["candidates"]}
    sides = {mark["candidate_id"]: mark["apex_side_on_view"] for mark in marks}
    _, pairs = door_groups(view, contours, {ident: {"role": "hinged_door"} for ident in sides}, sides)
    occupied = {row["candidate_id"] for row in rows}
    additions, conflicts = [], []
    for pair in pairs:
        for ident in pair["leaves"]:
            if ident in occupied:
                conflicts.append({"candidate_id": ident, "reason": "opening mark conflicts with a labelled role"})
                continue
            additions.append({"candidate_id": ident, "role": "hinged_door", "bbox_px": contours[ident]["bbox"],
                              "source_ids": [ident], "role_basis": "paired native opening strokes"})
    return {"items": [*rows, *additions], "pairs": pairs, "conflicts": conflicts}


def ground_front(rows, *, views, projections):
    """Keep observed roles traceable and separate from geometry inferences."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["view_id"]].append(row)
    kept, audit = [], []
    for view_id, readings in groups.items():
        contours = {row["id"]: row for row in views[view_id]["candidates"]}
        if projections.get(view_id) == "Top view":
            audit.extend({**row, "reason": "plan appearance is context only"} for row in readings)
            continue
        drawers = {row["candidate_id"]: row for row in readings
                   if row["role"] == "drawer" and row["candidate_id"] in contours}
        occupied = {row["candidate_id"] for row in readings}
        leaves = drawer_leaves([contours[ident] for ident in drawers], list(contours.values()))
        leaf_ids = {contour["id"] for contour in leaves}
        for leaf in leaves:
            ident = leaf["id"]
            if ident in occupied:
                continue
            enclosing = [seed for seed in drawers if encloses(contours[seed]["bbox"], leaf["bbox"])]
            kept.append({**drawers[enclosing[0]], "candidate_id": ident, "bbox_px": leaf["bbox"],
                         "geometry_basis": "native drawer leaf within model-identified drawer region"})
        local = []
        for row in readings:
            ident, role = row["candidate_id"], row["role"]
            if role == "drawer" and ident in drawers and ident not in leaf_ids:
                audit.append({**row, "reason": "drawer rim or group resolved to separate native leaves"})
                continue
            box = row["bbox_px"]
            if (box and role == "support_leg" and projections.get(view_id) in
                    {"Front elevation", "Rear view", "Side view"} and box[3] - box[1] < 3 * (box[2] - box[0])):
                audit.append({**row, "reason": "orthographic support does not have a vertical leg silhouette"})
                continue
            if ident in contours and role == "unresolved_front":
                enclosed = [other for other in readings if other["candidate_id"] in contours
                            and other["role"] in {"hinged_door", "lift_up"}
                            and encloses(box, other["bbox_px"])]
                if len(enclosed) >= 2:
                    audit.append({**row, "reason": "enclosing contour of separate identified leaves"})
                    continue
            local.append(row)

        if projections.get(view_id) == "Front elevation":
            flaps = [row for row in local if row["role"] in {"hinged_door", "lift_up"}
                     and row["candidate_id"] in contours
                     and row["bbox_px"][2] - row["bbox_px"][0] >= 2 * (row["bbox_px"][3] - row["bbox_px"][1])]
            pairs = set()
            for a, b in combinations(flaps, 2):
                first, second = sorted((a["bbox_px"], b["bbox_px"]))
                width = first[2] - first[0]
                if not (ordered_band([{"bbox": first}, {"bbox": second}])
                        and 0 <= second[0] - first[2] <= .04 * width
                        and abs(width - (second[2] - second[0])) <= .15 * width):
                    continue
                below = [row["bbox_px"] for row in local if row["role"] in {"hinged_door", "drawer"}
                         and row["bbox_px"] and row["bbox_px"][1] > max(first[3], second[3])]
                if all(any(axis_overlap(box, other, 0) > .15 for other in below) for box in (first, second)):
                    pairs.update((a["candidate_id"], b["candidate_id"]))
            for row in local:
                if row["candidate_id"] in pairs and row["role"] == "hinged_door":
                    audit.append({**row, "reason": "matching wide short upper leaves above a separate base row"})
                    row = {**row, "role": "lift_up", "role_basis": "inferred from matching upper flap geometry"}
                kept.append(row)
        else:
            kept.extend(local)
    return {"faces": kept, "audit": audit}


def review_front_roles(rows, review):
    """Keep physical review decisions separate from the original observations."""
    corrections = {(r["view_id"], r["candidate_id"]): r for r in review}
    result, audit = [], []
    for row in rows:
        corrected = corrections.get((row["view_id"], row["candidate_id"]))
        if not corrected:
            result.append(row)
            continue
        role = corrected["role"]
        if role != row["role"]:
            audit.append({**row, "reviewed_role": role, "reason": corrected["evidence"]})
        if role != "fixed_surface":
            result.append({**row, "role": role, "evidence": corrected["evidence"]})
    return {"faces": result, "audit": audit}


def unresolved_adjacent_profiles(faces, *, views, reviewed_fixed, primary_elevations):
    """Abstain on a blank full-height profile beside a fixed part of the same height."""
    fixed = defaultdict(set)
    for row in reviewed_fixed:
        fixed[row["view_id"]].add(row["candidate_id"])
    retained, audit = [], []
    for face in faces:
        box = face["bbox_px"]
        vid = face["view_id"]
        if (face["role"] != "hinged_door" or not box or not face["candidate_id"] or vid in primary_elevations
                or box[3] - box[1] < 4 * (box[2] - box[0])):
            retained.append(face)
            continue
        x0, y0, x1, y1 = box
        neighbor = any(
            row["id"] in fixed[vid] and abs(row["bbox"][1] - y0) <= 3 and abs(row["bbox"][3] - y1) <= 3
            and min(abs(row["bbox"][2] - x0), abs(row["bbox"][0] - x1)) <= 3
            for row in views[vid]["candidates"])
        if neighbor:
            reason = "blank adjacent profile on a secondary elevation; the opening role is unconfirmed"
            audit.append({**face, "reason": reason})
            face = {**face, "role": "unresolved_front", "evidence": reason}
        retained.append(face)
    return {"faces": retained, "audit": audit}


def linked_support_faces(views, projections, observations):
    """Recover a support pair where a linked elevation exposes both legs."""
    extensions = [item for vid, view in views.items() if projections[vid] == "Side view"
                  for item in supported_extensions(view)]
    if len(extensions) != 1:
        return []
    linked = connected_views(extensions[0]["view_id"], observations)
    candidates = []
    for vid in sorted(linked & views.keys()):
        if projections[vid] not in {"Front elevation", "Rear view"}:
            continue
        contours = [row for row in views[vid]["candidates"] if rectangular(row)]
        for top in contours:
            x0, y0, x1, y1 = top["bbox"]
            width = x1 - x0
            if width < 8 * (y1 - y0):
                continue
            legs = [row for row in contours if abs(row["bbox"][1] - y1) <= 2
                    and row["bbox"][0] >= x0 - 1 and row["bbox"][2] <= x1 + 1
                    and row["bbox"][3] - row["bbox"][1] >= 4 * (row["bbox"][2] - row["bbox"][0])]
            if len(legs) != 2:
                continue
            a, b = sorted(legs, key=lambda row: row["bbox"][0])
            left, right = a["bbox"], b["bbox"]
            if (abs(left[3] - right[3]) <= 2 and right[0] - left[2] >= .5 * width
                    and abs(left[0] - x0 - (x1 - right[2])) <= .08 * width):
                candidates.append((vid, legs))
    if len(candidates) != 1:
        return []
    vid, legs = candidates[0]
    return [{"view_id": vid, "candidate_id": row["id"], "bbox_px": row["bbox"], "role": "support_leg",
             "role_basis": "paired floor supports contacting one top in a linked elevation"} for row in legs]
