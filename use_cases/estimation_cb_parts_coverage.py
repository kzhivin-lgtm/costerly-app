"""Reconcile grounded Analyze observations with a preliminary Parts report."""

from collections import defaultdict


FRONT_PART_ROLES = {
    "drawer": "drawer_front", "hinged_door": "door_front", "lift_up": "lift_up_front",
    "support_leg": "support_leg", "mirror": "mirror", "pull_out_shelf": "pull_out_shelf",
    "fixed_open_shelf": "fixed_open_shelf",
}


def retained_component_callouts(view_id, readings, leaders):
    """Keep printed component notes at their original scope without assigning quantities."""
    return [
        {"id": f"{view_id}:{row['id']}", "view_id": view_id, "annotation_id": row["id"],
         "role": row["role"], "source_text": row["source_text"], "tips": leaders[row["id"]]["tips"],
         "kind": "component_callout"}
        for row in readings["leader_readings"]
        if row["role"] in {"glazed_zone", "lighting", "cover"} and row.get("source_text")
    ]


def planner_owners(planner):
    owners = defaultdict(set)
    for block in planner["blocks"]:
        appearances = block.get("appearances", ())
        if isinstance(appearances, dict):
            for view_id, contour_ids in appearances.items():
                for contour_id in contour_ids:
                    owners[f"{view_id}:{contour_id}"].add(block["id"])
        else:
            for appearance in appearances:
                contours = [*appearance.get("drawer_faces", ()), *appearance.get("contour_ids", ())]
                contours.extend(cid for group in block.get("positions", ()) for cid in group)
                for contour_id in contours:
                    owners[f"{appearance['view_id']}:{contour_id}"].add(block["id"])
        for extension in block.get("fixed_extensions", ()):
            owners[f"{extension['view_id']}:{extension['contour_id']}"].add(block["id"])
    return owners


def _part_status(rows):
    if not rows:
        return "pending_decomposition"
    if any(value.get("mm") is None for row in rows for value in row.get("dimensions", {}).values()):
        return "dimensions_pending"
    return "represented"


def _object_coverage(obj, output):
    planner = obj["planner"]
    owners = planner_owners(planner)
    parts_by_ref = defaultdict(list)
    parts_by_scope = {}
    for scope in [*output["blocks"], *output["shared_parts"]]:
        scope_id = scope.get("block_id") or scope["id"]
        parts_by_scope[scope_id] = scope["parts"]
        if scope.get("object_part_id"):
            parts_by_scope[scope["object_part_id"]] = [row for row in scope["parts"] if row["role"] == "tabletop"]
        for row in scope["parts"]:
            refs = [*row.get("count_refs", ())]
            if row.get("instance_ref"):
                refs.append(row["instance_ref"])
            for ref in dict.fromkeys(refs):
                parts_by_ref[ref].append((scope_id, row))

    components = []
    seen_front = set()
    for face in obj["front"]["faces"]:
        role = face["role"]
        ref = f'{face["view_id"]}:{face.get("candidate_id") or "unlocalized"}'
        key = (role, ref)
        if key in seen_front and face.get("candidate_id"):
            continue
        seen_front.add(key)
        matching = [(sid, row) for sid, row in parts_by_ref[ref] if row["role"] == FRONT_PART_ROLES.get(role)]
        block_ids = owners[ref] | {sid for sid, _ in matching}
        status = _part_status([row for _, row in matching]) if block_ids else "ownership_pending"
        if len(block_ids) > 1 or len(matching) > 1:
            status = "ownership_conflict"
        components.append({"id": ref, "role": role, "source": "front", "scope_ids": sorted(block_ids),
                           "status": status})

    for block in planner["blocks"]:
        scope = block["id"]
        for row in block.get("fixed_extensions", ()):
            ref = f'{row["view_id"]}:{row["contour_id"]}'
            matching = [part for _, part in parts_by_ref[ref] if part["role"] == "fixed_panel"]
            status = "ownership_conflict" if len(owners[ref]) > 1 else _part_status(matching)
            components.append({"id": ref, "role": "fixed_panel", "source": "planner",
                               "scope_ids": [scope], "status": status})
    independent = planner.get("independent_elements", ())
    callouts = {row["id"]: row for row in planner.get("component_callouts", ())}
    for row in [*planner.get("object_parts", ()), *independent]:
        scope = row["id"]
        source_ref = f'{row["view_id"]}:{row["annotation"]}' if row.get("annotation") and row.get("view_id") else None
        callout = callouts.get(source_ref)
        components.append({"id": scope, "role": row["role"], "source": "planner", "scope_ids": [scope],
                           "status": _part_status(parts_by_scope.get(scope)),
                           **({"source_ref": source_ref} if source_ref else {}),
                           **({"source_text": callout["source_text"]} if callout else {})})
    isolated = {(row.get("view_id"), row.get("annotation")) for row in independent}
    for row in planner.get("component_callouts", ()):
        if (row["view_id"], row["annotation_id"]) not in isolated:
            components.append({**row, "source": "printed_callout", "scope_ids": [], "status": "ownership_pending"})

    blocks = [{"id": row["id"], "basis": row["basis"], "status": _part_status(parts_by_scope.get(row["id"]))}
              for row in planner["blocks"]]
    diagnostics = {key: planner[key] for key in (
        "unassigned_candidates", "unresolved", "locator_issues", "reported_unresolved_edges", "annotation_ownership_pending",
    ) if planner.get(key)}
    has_gaps = not (components or blocks) or diagnostics or any(row["status"] != "represented" for row in [*components, *blocks])
    return {"status": "gaps_found" if has_gaps else "tracked_sources_reconciled", "blocks": blocks,
            "components": components, "planner_diagnostics": diagnostics,
            "front_instance_counts": obj["front"].get("instance_counts", {})}


def audit_cb_parts_coverage(analyze, parts):
    if (analyze["source_audit_sha256"] != parts["source_audit_sha256"]
            or analyze["objects"].keys() != parts["objects"].keys()):
        raise ValueError("Parts coverage requires matching Analyze and Parts inputs")
    return {"stage": "CB Parts Coverage", "source_audit_sha256": analyze["source_audit_sha256"],
            "scope": "tracked_analyze_observations", "source_inventory_verified": False,
            "objects": {oid: _object_coverage(obj, parts["objects"][oid]) for oid, obj in analyze["objects"].items()}}
