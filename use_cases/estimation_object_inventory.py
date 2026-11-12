"""Build the per-object inventory from locked Analyze evidence and attach Parts."""

from collections import defaultdict
from copy import deepcopy

from use_cases.estimation_cb_parts_coverage import planner_owners


def _appearances(row):
    appearances = row.get("appearances", ())
    if isinstance(appearances, dict):
        return [{"view_id": view_id, "contour_ids": ids} for view_id, ids in appearances.items()]
    if not appearances and (view_id := row.get("view_id") or row.get("source_view_id")):
        appearance = {"view_id": view_id}
        if row.get("contour_ids"):
            appearance["contour_ids"] = row["contour_ids"]
        if row.get("annotation"):
            appearance["annotation_id"] = row["annotation"]
        if row.get("outline_px"):
            appearance["outline_px"] = row["outline_px"]
        return [appearance]
    return appearances


def _source_refs(row, views):
    return [{**appearance, "page": views[appearance["view_id"]]["page"]}
            for appearance in _appearances(row)]


def _observation(row, kind, views, owner_ids):
    source = {"view_id": row["view_id"], "page": views[row["view_id"]]["page"]}
    for field in ("candidate_id", "bbox_px", "annotation_id", "source_text", "tips", "evidence", "role_basis"):
        if field in row:
            source[field] = row[field]
    owner_ids = sorted(owner_ids)
    status = {0: "ownership_pending", 1: "assigned"}.get(len(owner_ids), "ownership_conflict")
    return {"kind": kind, "role": row["role"], "source": source,
            "candidate_owner_ids": owner_ids, "status": status}


def _object_inventory(obj, views):
    planner = obj["planner"]
    owners = planner_owners(planner)
    items = [{"id": block["id"], "kind": "block", "role": block["basis"],
              "source_refs": _source_refs(block, views), "children": []}
             for block in planner["blocks"]]
    blocks = {item["id"]: item for item in items}
    seen_ids = set(blocks)
    if len(seen_ids) != len(items):
        raise ValueError("Object Inventory requires unique Block IDs within an object")

    annotation_owners = defaultdict(set)
    for row in [*planner.get("object_parts", ()), *planner.get("independent_elements", ())]:
        ident = row["id"]
        if ident in seen_ids:
            raise ValueError(f"Duplicate Object Inventory ID: {ident}")
        seen_ids.add(ident)
        item = {"id": ident, "kind": "element", "role": row["role"],
                "source_refs": _source_refs(row, views), "children": []}
        for field in ("quantity", "unit", "attached_block_ids"):
            if field in row:
                item[field] = row[field]
        parent = row.get("envelope_block_id")
        if parent:
            blocks[parent]["children"].append(item)
        else:
            items.append(item)
        if row.get("annotation") and row.get("view_id"):
            annotation_owners[(row["view_id"], row["annotation"])].add(ident)

    observations = []
    # Some assemblies retain a footprint rather than a contour ID.
    footprints = defaultdict(set)
    for block in blocks.values():
        for ref in block["source_refs"]:
            if ref.get("bbox"):
                footprints[(ref["view_id"], tuple(ref["bbox"]))].add(block["id"])
    seen_faces = set()
    for face in obj["front"]["faces"]:
        ref = (face["view_id"], face.get("candidate_id"), face["role"])
        if ref[1] and ref in seen_faces:
            continue
        seen_faces.add(ref)
        owner_ids = owners[f"{ref[0]}:{ref[1]}"]
        if not owner_ids and face.get("bbox_px"):
            owner_ids = footprints[(ref[0], tuple(face["bbox_px"]))]
        observations.append(_observation(face, "front", views, owner_ids))
    for block in planner["blocks"]:
        for fixed in block.get("fixed_extensions", ()):
            ref = f"{fixed['view_id']}:{fixed['contour_id']}"
            observations.append(_observation(
                {**fixed, "candidate_id": fixed["contour_id"], "role": "fixed_panel"},
                "fixed_panel", views, owners[ref]))
    for row in planner.get("component_callouts", ()):
        observations.append(_observation(
            row, "printed_callout", views, annotation_owners[(row["view_id"], row["annotation_id"])]))

    return {"view_ids": sorted(views), "items": items, "observations": observations}


def build_object_inventory(analyze, views, *, page_count):
    """Register all PDF pages and project known observations onto locked owners."""
    by_object = {oid: {} for oid in analyze["objects"]}
    sheets = [{"page": page, "views": [], "review_status": "pending_independent_review"}
              for page in range(1, page_count + 1)]
    seen_views = set()
    for view in views:
        vid, oid, page = view["view_id"], view["object_id"], view["page"]
        if vid in seen_views or oid not in by_object or not 1 <= page <= page_count:
            raise ValueError(f"Invalid Object Inventory source view: {vid}")
        seen_views.add(vid)
        by_object[oid][vid] = view
        sheets[page - 1]["views"].append({"id": vid, "object_id": oid, "type": analyze["islands"][vid]})
    if seen_views != analyze["islands"].keys():
        raise ValueError("Object Inventory requires the same views as the Island Map")
    for sheet in sheets:
        sheet["views"].sort(key=lambda view: view["id"])
    return {"stage": "Object Inventory", "version": 1,
            "source_audit_sha256": analyze["source_audit_sha256"],
            "source_coverage": "pending_independent_review", "sheets": sheets,
            "objects": {oid: _object_inventory(obj, by_object[oid]) for oid, obj in analyze["objects"].items()}}


def _attach_parts(item, rows, review=()):
    item["children"].extend({**row, "kind": "part"} for row in rows)
    if review:
        item["review"] = list(review)
    has_parts = rows or any(child.get("parts_status") == "preliminary" for child in item["children"])
    item["parts_status"] = "preliminary" if has_parts else "pending_decomposition"


def reconcile_object_inventory(inventory, parts):
    """Attach existing physical Parts once under their inventory owner."""
    if (inventory["source_audit_sha256"] != parts["source_audit_sha256"]
            or inventory["objects"].keys() != parts["objects"].keys()):
        raise ValueError("Object Inventory and Parts must describe the same source and objects")
    result = deepcopy(inventory)
    for oid, obj in result["objects"].items():
        output = parts["objects"][oid]
        scopes = {}
        for scope in [*output["blocks"], *output["shared_parts"]]:
            scope_id = scope.get("block_id") or scope["id"]
            if scope_id in scopes:
                raise ValueError(f"Duplicate Parts scope in {oid}: {scope_id}")
            scopes[scope_id] = scope

        for item in obj["items"]:
            scope = scopes.pop(item["id"], None)
            scope = scope or {"parts": []}
            rows = deepcopy(scope["parts"])
            for child in item["children"]:
                owned = [row for row in rows if row.get("inventory_item_id") == child["id"]]
                if owned:
                    _attach_parts(child, owned)
                    rows = [row for row in rows if row.get("inventory_item_id") != child["id"]]
                elif scope.get("object_part_id") == child["id"]:
                    # The supported extension compiler emits the top and its
                    # underlayer alongside the supports in the Block scope.
                    top_roles = {"tabletop", "tabletop_underlayer"}
                    _attach_parts(child, [row for row in rows if row["role"] in top_roles])
                    rows = [row for row in rows if row["role"] not in top_roles]
                else:
                    _attach_parts(child, ())
            _attach_parts(item, rows, scope.get("review", ()))
        obj["unowned_part_scopes"] = list(scopes.values())
    return result
