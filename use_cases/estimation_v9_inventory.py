"""Estimation 9 source reconciliation and Parts Check."""

from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import re

from use_cases.estimation_cb_parts_coverage import audit_cb_parts_coverage

COMPONENT_ROLES = frozenset({
    "mirror", "lighting", "plinth", "worktop", "fixed_open_shelf", "glazed_zone", "glass_box",
    "window_closure", "fixed_panel", "support_leg", "hinged_door", "lift_up",
    "drawer", "pull_out_shelf", "other_component",
})
STANDALONE_ROLES = frozenset({"lighting", "plinth", "worktop", "mirror", "window_closure"})
LED_TEMPERATURE = re.compile(
    r"\bLED\s*[-:]?\s*(\d{4})(?:\s*[KК])?\b(?!\s*(?:W|lm|mm|V|Вт|лм|мм|В)\b)",
    re.IGNORECASE,
)
QUOTED_TEXT = re.compile(r"""['"«“]([^'"»”]+)['"»”]""")


def lighting_temperature_readings(item, *, include_unspecified=False):
    """Read explicit LED callouts without treating observations as circuit counts."""
    readings = []
    for source in item["source_refs"]:
        literal = source.get("source_text")
        basis = "printed_callout"
        if "source_text" not in source:
            # Archived V9 responses placed literal callouts in evidence quotes.
            quotes = QUOTED_TEXT.findall(source.get("evidence", ""))
            literal = " ".join(quote for quote in quotes if LED_TEMPERATURE.search(quote))
            basis = "archived_callout_transcription"
        if not literal:
            continue
        values = sorted({int(match) for match in LED_TEMPERATURE.findall(literal) if int(match) >= 1000})
        if values or include_unspecified and source.get("source_text"):
            readings.append({**source, "literal": literal, "kelvin_values": values, "basis": basis})
    return readings


def _area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _overlap(a, b):
    intersection = _area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))
    union = _area(a) + _area(b) - intersection
    return intersection / union if union else 0


def _contained(box, frame):
    return all((frame[0] <= box[0], frame[1] <= box[1], box[2] <= frame[2], box[3] <= frame[3]))


def page_box(box, view, *, size):
    x0, y0, x1, y1 = view["bbox_normalized"]
    scale_x, scale_y = (x1 - x0) / size[0], (y1 - y0) / size[1]
    return [x0 + box[0] * scale_x, y0 + box[1] * scale_y,
            x0 + box[2] * scale_x, y0 + box[3] * scale_y]


def _items(rows):
    for row in rows:
        yield row
        yield from _items(row.get("children", ()))


def _component(item_id, role, source, *, quantity=None, attached=()):
    return {"id": item_id, "kind": "element", "role": role, "quantity": quantity,
            "source_refs": [source], "attached_block_ids": sorted(set(attached)), "children": []}


def _leader_blocks(source, blocks, inside):
    """Return the possible owner set for every original arrow tip."""
    return [
        {block["id"] for block in blocks if any(
            inside(tip["xy_px"], polygon) for polygon in
            block.get("envelopes", {}).get(source["view_id"], {}).get("polygons_px", ()))}
        for tip in source["tips"]
    ]


def bind_native_components(inventory, analyze):
    """Use existing Front contours and printed leaders as evidence for ownership."""
    from tools.estimation_native_islands import inside

    for oid, obj in inventory["objects"].items():
        blocks = analyze["objects"][oid]["planner"]["blocks"]
        items = {item["id"]: item for item in obj["items"]}
        mirrors = [row for row in obj["observations"] if row["role"] == "mirror"
                   and row["status"] == "assigned" and row["source"].get("candidate_id")]
        # Mirror appearances on different views need identity evidence before counting.
        if len({row["source"]["view_id"] for row in mirrors}) == 1:
            for row in mirrors:
                source = row["source"]
                ident = f"mirror:{source['view_id']}:{source['candidate_id']}"
                if ident not in items:
                    items[ident] = _component(ident, "mirror", source, quantity=1,
                                              attached=row["candidate_owner_ids"])
                    owner, = row["candidate_owner_ids"]
                    items[owner]["children"].append(items[ident])
                row["candidate_owner_ids"] = [ident]
                row["ownership_basis"] = "mirror_contour_owned_by_block"

        for row in obj["observations"]:
            source = row["source"]
            if row["kind"] != "printed_callout" or not source.get("tips"):
                continue
            role = row["role"]
            if role not in {"glazed_zone", "lighting"}:
                continue
            targets = _leader_blocks(source, blocks, inside)
            if role == "lighting":
                # Collect the callouts before matching them to physical runs and Blocks.
                ident = "lighting"
                attached = set().union(*targets)
                if ident not in items:
                    items[ident] = _component(ident, role, source, attached=attached)
                    obj["items"].append(items[ident])
                else:
                    items[ident]["source_refs"].append(source)
                    items[ident]["attached_block_ids"] = sorted(
                        set(items[ident]["attached_block_ids"]) | attached)
            else:
                owners = set().union(*targets)
                if len(owners) != 1 or any(target != owners for target in targets):
                    continue
                owner, = owners
                ident = f"glazing:{source['view_id']}:{source['annotation_id']}"
                items[owner]["children"].append(_component(ident, role, source))
            row["candidate_owner_ids"] = [ident]
            row["status"] = "assigned"
            row["ownership_basis"] = ("all_leader_tips_in_one_block" if role == "glazed_zone"
                                      else "printed_lighting_callout")


def _reference_boxes(ref, view_index, contours):
    if ref.get("bbox_normalized"):
        yield ref["bbox_normalized"]
        return
    view = view_index.get(ref.get("view_id"))
    if not view:
        return
    size = view["width"], view["height"]
    box = ref.get("bbox_px") or ref.get("bbox")
    if box:
        yield page_box(box, view, size=size)
    if ref.get("outline_px"):
        xs, ys = zip(*ref["outline_px"])
        yield page_box((min(xs), min(ys), max(xs), max(ys)), view, size=size)
    for cid in [*ref.get("contour_ids", ()), ref.get("candidate_id")]:
        if cid in contours[view["view_id"]]:
            yield page_box(contours[view["view_id"]][cid], view, size=size)


def _known_components(obj):
    known = defaultdict(list)
    for item in _items(obj["items"]):
        if item["kind"] != "element":
            continue
        for ref in item["source_refs"] or [None]:
            known[item["role"]].append((item, [item["id"]], ref))
    for row in obj["observations"]:
        if row["status"] != "assigned":
            continue
        known[row["role"]].append((None, row["candidate_owner_ids"], row["source"]))
    return known


def _binding(finding, view_index):
    source = finding["source"]
    box = source["bbox_normalized"]
    if box is None and finding["role"] == "lighting":
        box = source.get("callout_bbox_normalized")
    if box is None:
        return None
    if source.get("view_id"):
        view = view_index[source["view_id"]]
        return view if _contained(box, view["bbox_normalized"]) else None
    matches = [view for view in view_index.values()
               if view["page"] == source["page"] and _contained(box, view["bbox_normalized"])]
    return matches[0] if len(matches) == 1 else None


def _same_location(source, ref, views, contours):
    return ref and ref["page"] == source["page"] and any(
        _overlap(source["bbox_normalized"], box) >= .65
        for box in _reference_boxes(ref, views, contours)
    )


def _separate_worktop(source, related, views, contours):
    view = views[source["view_id"]]
    if view.get("projection") != "Top view":
        return False
    vid = view["view_id"]
    native = [page_box(box, view, size=(view["width"], view["height"]))
              for box in contours[vid].values()]
    targets = [box for box in native if _overlap(source["bbox_normalized"], box) >= .65]
    if len(targets) != 1:
        return False
    target, = targets
    # Require a gap against a native outline of every existing worktop on
    # this plan. Other views and a guessed rectangle cannot prove a break.
    for item_id in {item["id"] for item, _, _ in related if item is not None}:
        boxes = [box for item, _, ref in related
                 if item is not None and item["id"] == item_id and ref and ref.get("view_id") == vid
                 for box in _reference_boxes(ref, views, contours)
                 if any(_overlap(box, native_box) >= .65 for native_box in native)]
        if not boxes or any(
            max(target[0] - box[2], box[0] - target[2],
                target[1] - box[3], box[1] - target[3]) <= .005 for box in boxes
        ):
            return False
    return all(item is not None for item, _, _ in related)


def _native_contour_owner(obj, source, views, contours):
    """Require a distinct native contour already assigned to exactly one Block."""
    vid = source["view_id"]
    view = views[vid]
    matches = [cid for cid, box in contours[vid].items() if
               _overlap(source["bbox_normalized"],
                        page_box(box, view, size=(view["width"], view["height"]))) >= .65]
    if len(matches) != 1:
        return None
    cid, = matches
    blocks = [block for block in obj["items"] if block["kind"] == "block" and any(
        ref.get("view_id") == vid and cid in ref.get("contour_ids", ()) for ref in block["source_refs"]
    )]
    if len(blocks) == 1:
        return blocks[0], cid
    return None


def _separate_mirror(source, obj, views, contours):
    blocks = [item for item in obj["items"] if item["kind"] == "block"]
    if not blocks:
        return True
    vid = source["view_id"]
    target = source["bbox_normalized"]
    view = views[vid]
    native = [page_box(box, view, size=(view["width"], view["height"])) for box in contours[vid].values()]
    if sum(_overlap(target, box) >= .65 for box in native) != 1:
        return False
    envelopes = []
    for block in blocks:
        boxes = [box for ref in block["source_refs"] if ref["view_id"] == vid
                 for box in _reference_boxes(ref, views, contours)]
        if boxes:
            envelopes.append([min(box[0] for box in boxes), min(box[1] for box in boxes),
                              max(box[2] for box in boxes), max(box[3] for box in boxes)])
    return bool(envelopes) and all(_overlap(target, box) == 0 for box in envelopes)


def _place_finding(obj, finding, known, views, contours):
    source = finding["source"]
    role = finding["role"]
    related = known[role]
    if role in {"plinth", "lighting"}:
        items = {item["id"]: item for item, _, _ in related if item is not None}
        if len(items) == 1:
            item = next(iter(items.values()))
            if source not in item["source_refs"]:
                item["source_refs"].append(source)
            return {"kind": finding["stage"], "role": role, "source": source,
                    "candidate_owner_ids": [item["id"]], "status": "assigned",
                    "disposition": "added_evidence_to_object_group"}
    matches = [(item, owners) for item, owners, ref in related
               if _same_location(source, ref, views, contours)]
    owner_ids = sorted({owner for _, owners in matches for owner in owners})
    disposition = "unresolved"
    if len(owner_ids) == 1:
        for item, _ in matches:
            if item is not None and source not in item["source_refs"]:
                item["source_refs"].append(source)
        status, disposition = "assigned", "matched_existing"
    elif matches:
        status = "ownership_conflict"
    elif role in {"glass_box", "mirror"} and (
            binding := _native_contour_owner(obj, source, views, contours)):
        block, cid = binding
        if any(not ref or ref.get("view_id") != source["view_id"] or ref.get("candidate_id") == cid
               for _, _, ref in related):
            status = "identity_pending"
        else:
            ident = f"{role.replace('_', '-')}:{source['view_id']}:{cid}"
            source["candidate_id"] = cid
            item = _component(ident, role, source, quantity=1 if role == "mirror" else None)
            block["children"].append(item)
            related.append((item, [ident], source))
            owner_ids, status, disposition = [ident], "assigned", "added_to_inventory"
    elif role == "glass_box":
        status = "ownership_pending"
    elif related and not (role == "worktop" and finding["scope"] == "standalone"
                          and _separate_worktop(source, related, views, contours)):
        status = "identity_pending"
    elif role == "mirror" and not _separate_mirror(source, obj, views, contours):
        status = "ownership_pending"
    elif (finding["scope"] == "standalone" and role in STANDALONE_ROLES) or role == "lighting":
        # An object-level group can collect evidence while physical count is open.
        ident = {"plinth": "plinth-kit", "lighting": "lighting"}.get(role)
        if ident is None:
            ident = "E-" + sha256(repr((role, source["page"], source["bbox_normalized"])).encode()).hexdigest()[:12]
        item = _component(ident, role, source, quantity=1 if role == "plinth" else None)
        if role == "plinth":
            item["unit"] = "set"
        obj["items"].append(item)
        related.append((item, [ident], source))
        owner_ids, status, disposition = [ident], "assigned", "added_to_inventory"
    else:
        status = "ownership_pending"
    return {"kind": finding["stage"], "role": role, "source": source,
            "candidate_owner_ids": owner_ids, "status": status, "disposition": disposition}


def apply_source_findings(inventory, views, findings):
    """Attach supported observations once and keep ambiguous source evidence visible."""
    projections = {view["id"]: view["type"] for sheet in inventory["sheets"] for view in sheet["views"]}
    view_index = {view["view_id"]: {**view, "projection": projections.get(view["view_id"])} for view in views}
    contours = {vid: {row["id"]: row["bbox"] for row in view.get("candidates", ())}
                for vid, view in view_index.items()}
    unassigned = inventory.setdefault("unassigned_source_findings", [])
    for obj in inventory["objects"].values():
        obj.setdefault("source_review_findings", [])
    known = {oid: _known_components(obj) for oid, obj in inventory["objects"].items()}
    for finding in findings:
        view = _binding(finding, view_index)
        if view is None:
            unassigned.append({**finding, "status": "view_ownership_pending"})
            continue
        oid = view["object_id"]
        obj = inventory["objects"][oid]
        localized = {**finding, "source": {**finding["source"], "view_id": view["view_id"]}}
        record = _place_finding(obj, localized, known[oid], view_index, contours)
        obj["source_review_findings"].append(record)
    return inventory


def check_inventory(inventory, views, page_reviews):
    """Compare an independent result for every original PDF page to the draft."""
    expected = {row["page"] for row in inventory["sheets"]}
    by_page = {row["page"]: row for row in page_reviews}
    if expected != by_page.keys() or len(by_page) != len(page_reviews):
        raise ValueError("Inventory Check requires one review record per original PDF page")
    checked = deepcopy(inventory)
    for sheet in checked["sheets"]:
        review = by_page[sheet["page"]]
        sheet["review_status"] = review["status"]
        if review.get("error"):
            sheet["review_error"] = review["error"]
    findings = [finding for review in page_reviews if review["status"] == "reviewed"
                for finding in review["findings"]]
    if any(finding["source"]["page"] != review["page"] for review in page_reviews
           for finding in review.get("findings", ())):
        raise ValueError("Inventory Check finding belongs to a different sheet")
    apply_source_findings(checked, views, findings)
    refresh_source_coverage(checked)
    return checked


def refresh_source_coverage(inventory):
    if any(sheet["review_status"] != "reviewed" for sheet in inventory["sheets"]):
        inventory["source_coverage"] = "incomplete_page_review"
    elif inventory["unassigned_source_findings"] or any(
        row["status"] != "assigned"
        for obj in inventory["objects"].values()
        for row in [*obj["observations"], *obj["source_review_findings"]]
    ):
        inventory["source_coverage"] = "reviewed_with_open_findings"
    else:
        inventory["source_coverage"] = "reviewed"


def add_inventory_geometry(geometry, inventory):
    """Expose the geometry scope for each standalone element without guessing sizes."""
    for oid, obj in inventory["objects"].items():
        measured = geometry["objects"][oid]
        measured["standalone_elements"] = [
            {"id": item["id"], "role": item["role"], "source_refs": item["source_refs"],
             "status": "dimensions_pending"}
            for item in obj["items"] if item["kind"] == "element"
        ]
        lower_blocks = [block["block_id"] for block in measured["blocks"]
                        if block["measurements"].get("depth_proxy", {}).get("method")
                        == "shared_worktop_footprint_proxy"]
        if lower_blocks:
            worktops = [item["id"] for item in obj["items"] if item["role"] == "worktop"]
            # A depth proxy identifies a candidate lower cabinet, but cannot
            # prove continuity or complete coverage of the worktop footprint.
            obj["worktop_coverage"] = {"block_ids": lower_blocks, "worktop_ids": worktops,
                                       "status": "coverage_pending" if worktops else "worktop_not_identified"}
            measured["worktop_coverage"] = obj["worktop_coverage"]


def include_standalone_parts_scopes(parts, inventory):
    """Keep every standalone item in Calculation, even when its recipe is open."""
    for oid, obj in inventory["objects"].items():
        scopes = parts["objects"][oid]["shared_parts"]
        existing = {scope["id"] for scope in scopes}
        for item in obj["items"]:
            if item["kind"] == "element" and item["id"] not in existing:
                scope = {"id": item["id"], "role": item["role"], "parts": [],
                         "review": ["Standalone decomposition requires source geometry and construction."]}
                if item["role"] == "lighting":
                    scope["colour_temperature_readings"] = lighting_temperature_readings(item)
                scopes.append(scope)


def check_parts(analyze, inventory_with_parts, parts):
    """Reconcile physical Parts with both the locked inventory and the original evidence."""
    report = audit_cb_parts_coverage(analyze, parts)
    report["stage"] = "Parts Check"
    report["scope"] = "checked_object_inventory"
    report["source_coverage"] = inventory_with_parts["source_coverage"]
    report["sheets"] = [{"page": row["page"], "status": row["review_status"]}
                        for row in inventory_with_parts["sheets"]]
    report["unassigned_source_findings"] = inventory_with_parts["unassigned_source_findings"]
    for oid, obj in inventory_with_parts["objects"].items():
        result = report["objects"][oid]
        part_blocks = parts["objects"][oid]["blocks"]
        envelopes = {row["block_id"]: row["envelope"] for row in part_blocks if "envelope" in row}
        for block in result["blocks"]:
            if block["id"] in envelopes:
                block["envelope"] = deepcopy(envelopes[block["id"]])
        scopes = {item["id"]: item for item in _items(obj["items"]) if item["kind"] != "part"}
        native_owners = {}
        for observation in obj["observations"]:
            if not observation.get("ownership_basis"):
                continue
            source = observation["source"]
            ref = source.get("annotation_id") or source.get("candidate_id")
            native_owners[observation["role"], f"{source['view_id']}:{ref}"] = observation["candidate_owner_ids"]
        for component in result["components"]:
            scope_ids = native_owners.get((component["role"], component["id"]))
            if scope_ids:
                component["scope_ids"] = scope_ids
                statuses = {scopes[scope_id]["parts_status"] for scope_id in scope_ids}
                component["status"] = statuses.pop() if len(statuses) == 1 else "pending_decomposition"
        issues = [{"item_id": scope["block_id"], "reason": "block_construction_pending"}
                  for scope in part_blocks if scope.get("construction_pending")]
        if coverage := obj.get("worktop_coverage"):
            issues.append({"role": "worktop", "reason": coverage["status"],
                           "block_ids": coverage["block_ids"]})
        for item in _items(obj["items"]):
            if item["kind"] == "part":
                continue
            if item["parts_status"] == "pending_decomposition":
                issues.append({"item_id": item["id"], "reason": "pending_decomposition"})
            if "quantity" in item and item["quantity"] is None:
                issues.append({"item_id": item["id"], "reason": "quantity_pending"})
            missing_dimensions = defaultdict(set)
            for child in item["children"]:
                if child["kind"] == "part":
                    if "quantity" in child and child["quantity"] is None and item.get("quantity", 1) is not None:
                        issues.append({"item_id": item["id"], "role": child["role"],
                                       "source_ref": child.get("instance_ref"), "reason": "part_quantity_pending"})
                    missing_dimensions[child["role"]].update(
                        axis for axis, value in child.get("dimensions", {}).items() if value["mm"] is None)
            for role, axes in missing_dimensions.items():
                if axes:
                    issues.append({"item_id": item["id"], "role": role, "reason": "dimensions_pending",
                                   "missing_dimensions": sorted(axes)})
        for row in obj["source_review_findings"]:
            if row["status"] != "assigned":
                issues.append({"role": row["role"], "source": row["source"], "reason": row["status"]})
        for row in obj["observations"]:
            if row["role"] == "lighting" and row["status"] != "assigned":
                issues.append({"role": row["role"], "source": row["source"], "reason": row["status"]})
        for row in obj["unowned_part_scopes"]:
            issues.append({"item_id": row.get("block_id") or row["id"], "reason": "unowned_parts"})
        seen = set()
        for row in _items(obj["items"]):
            if row["kind"] == "part" and row.get("instance_ref"):
                key = row["role"], row["instance_ref"]
                if key in seen:
                    issues.append({"role": key[0], "source_ref": key[1], "reason": "duplicate_part_evidence"})
                seen.add(key)
                if row.get("colour_temperature_status") in {"temperature_pending", "temperature_conflict"}:
                    issues.append({"role": key[0], "source_ref": key[1],
                                   "reason": row["colour_temperature_status"],
                                   "sources": row["colour_temperature_sources"]})
        result["inventory_issues"] = issues
        result["parts"] = list(_parts_check_rows(obj["items"]))
        if (issues or report["source_coverage"] != "reviewed"
                or any(row["status"] == "review_required" for row in result["parts"])):
            result["status"] = "gaps_found"
    return report


def _parts_check_rows(items, block_id=None):
    for item in items:
        owner_block = item["id"] if item["kind"] == "block" else block_id
        for child in item["children"]:
            if child["kind"] != "part":
                yield from _parts_check_rows([child], owner_block)
                continue
            fields = {key: value for key, value in child.items() if key != "kind"}
            missing = sorted(key for key, value in fields["dimensions"].items() if value["mm"] is None)
            quantity_pending = fields.get("quantity") is None
            status = ("review_required" if missing or quantity_pending or fields.get("construction_basis")
                      or fields.get("colour_temperature_status") in {"temperature_pending", "temperature_conflict"}
                      else "represented")
            yield {**fields, "block_id": owner_block, "owner_id": item["id"], "status": status,
                   "owner_source_refs": item["source_refs"], "missing_dimensions": missing,
                   "quantity_pending": quantity_pending}
