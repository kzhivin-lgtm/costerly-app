"""Compile reviewed display and counter construction into Estimation 9 Parts."""

from collections import defaultdict
from decimal import Decimal, ROUND_CEILING
from difflib import SequenceMatcher
import re

from use_cases.estimation_cb_geometry_parts import VISIBLE_GRAIN_ROLES, derived, dimension, geometry_dimension, part, stock
from use_cases.estimation_cb_parts_coverage import planner_owners
from use_cases.estimation_structural_bom import _hinges_per_facade, _slide_depth_mm
from use_cases.price_source_taxonomy import material_rule_for_text


def _assumed(value, refs=()):
    return dimension(value, "construction_assumption", refs)


def _subtract(value, thickness, count):
    return derived("construction_assumption", [value, thickness], lambda d, t: d - count * t,
                   reason="Panels fitted between adjacent members.")


def _sized(role, qty, material, length, width, thickness, **evidence):
    return {**part(role, qty, material=material, length=length, width=width, thickness=thickness), **evidence}


def _note_dim(spec, name):
    record = spec.get(name, {})
    return dimension(record.get("mm"), record.get("basis", "construction_assumption"), record.get("refs", ()))


def _envelope(readings, axis):
    return geometry_dimension(readings.get(axis, {"value_mm": None, "method": "unresolved"}))


def _source_lighting_length(element, rows, measurements):
    """Size the fronts within the scope that owns the drawing's lighting note."""
    source_refs = list(dict.fromkeys(f"{ref['view_id']}:{ref['annotation_id']}" for ref in element["source_refs"]))
    shelves = [row for row in rows if row["role"] == "pull_out_shelf"]
    mirrors = [row for row in rows if row["role"] == "mirror_glass"]
    if shelves and not mirrors and all(row.get("quantity") for row in shelves):
        segments = [(row["dimensions"]["length"], row["quantity"]) for row in shelves]
        reason = "One lighting run across the front edge of each pull-out shelf in the lit scope."
    elif mirrors and not shelves and all(row.get("quantity") for row in mirrors):
        upright = measurements.get("installed_height", {})
        if len(mirrors) == 1 and upright.get("from") == "top of mirror mounting panel" and upright.get("value_mm"):
            segments = [(geometry_dimension(upright), 1)]
            reason = "Estimated straight lighting span along the full-height mirror upright."
        else:
            segments = [(row["dimensions"][axis], 2 * row["quantity"]) for row in mirrors
                        for axis in ("length", "width")]
            reason = "Full perimeter of each mirror in the lit scope."
    else:
        return None
    sizes, counts = zip(*segments)
    length = derived("construction_assumption", sizes, lambda *mm: sum(n * size for n, size in zip(counts, mm)),
                     reason=reason)
    length["refs"] = list(dict.fromkeys([*source_refs, *length["refs"],
                                         *(row["instance_ref"] for row in shelves + mirrors if row.get("instance_ref"))]))
    if length["mm"] is not None:
        length["segments"] = [{"length_mm": size["mm"], "quantity": count} for size, count in segments]
    return length


def _box(width, height, depth, thickness, material, back_t, partitions):
    inner_w = _subtract(width, thickness, 2)
    inner_h = _subtract(height, thickness, 2)
    rows = [
        _sized("carcass_side", 2, material, height, depth, thickness),
        _sized("carcass_top", 1, material, inner_w, depth, thickness),
        _sized("carcass_bottom", 1, material, inner_w, depth, thickness),
        _sized("carcass_back", 1, material, inner_w, inner_h, back_t),
    ]
    if partitions:
        rows.append(_sized("drawer_bay_divider", partitions, material, inner_h, depth, thickness))
    return rows


def glass_box_parts(width, depth, height, thickness, *, scope_id, ref):
    """Five panes, with the base below the sides and ends between long walls."""
    inside = _subtract(depth, thickness, 2)
    wall = _subtract(height, thickness, 1)
    material = "tempered glass"
    refs = {"inventory_item_id": scope_id, "instance_ref": ref}
    return [
        _sized("glass_box_bottom", 1, material, width, depth, thickness, **refs),
        _sized("glass_box_long_wall", 2, material, width, wall, thickness, **refs),
        _sized("glass_box_end_wall", 2, material, inside, wall, thickness, **refs),
    ]


DISPLAY_GLASS_NOTE = re.compile(r"\b(?:витрина\s*[/,]?\s*стекло|display\s*[/,]?\s*glass)\b", re.IGNORECASE)


def _shelves_under_glass_tips(source, shelves):
    """Require a distinct nearby pull-out shelf below each display glass arrow."""
    matches = []
    for tip in source["tips"]:
        x, y = tip["xy_px"]
        candidates = []
        for shelf in shelves:
            left, top, right, bottom = shelf["bbox_px"]
            if left <= x <= right and y < (top + bottom) / 2 and top - y <= 2 * (bottom - top):
                candidates.append((abs(top - y), shelf["candidate_id"]))
        candidates.sort()
        if not candidates or (len(candidates) > 1 and candidates[0][0] == candidates[1][0]):
            return []
        matches.append(candidates[0][1])
    return matches if len(set(matches)) == len(matches) else []


def add_source_display_glass_parts(parts, inventory, analyze):
    """Apply the five-pane recipe when a display note binds one-to-one to shelves."""
    for oid, obj in inventory["objects"].items():
        blocks = {block["id"]: block for block in analyze["objects"][oid]["planner"]["blocks"]}
        scopes = {scope["block_id"]: scope for scope in parts["objects"][oid]["blocks"]}
        faces = analyze["objects"][oid]["front"]["faces"]
        for item in obj["items"]:
            if item["kind"] != "block" or item["id"] not in scopes:
                continue
            if any(child["role"] == "glass_box" for child in item["children"]):
                continue
            zones = [zone for zone in item["children"] if zone["role"] == "glazed_zone"]
            if len(zones) != 1:
                continue
            zone, = zones
            if zone.get("quantity") is not None or len(zone["source_refs"]) != 1:
                continue
            source, = zone["source_refs"]
            if not source.get("tips") or not DISPLAY_GLASS_NOTE.search(source.get("source_text") or ""):
                continue
            shelves = [face for face in faces if face["role"] == "pull_out_shelf"
                       and face["view_id"] == source["view_id"] and face.get("bbox_px")
                       and face.get("candidate_id") in blocks[item["id"]].get("members", ())]
            if len(shelves) != len(source["tips"]):
                continue
            if not (matches := _shelves_under_glass_tips(source, shelves)):
                continue
            zone.update(quantity=len(matches), unit="glass_box",
                        quantity_basis="one distinct pull-out shelf below each display glass arrow")
            note_ref = f"{source['view_id']}:{source['annotation_id']}"
            thickness = dimension(4, "owner_construction_rule", [note_ref])
            scope = scopes[item["id"]]
            if not scope["parts"]:
                scope["construction_pending"] = True
            shelves_by_ref = {row["instance_ref"]: row for row in scope["parts"]
                              if row["role"] == "pull_out_shelf" and row.get("instance_ref")}
            for cid in matches:
                ref = f"{source['view_id']}:{cid}"
                pending_size = dimension(None, "unresolved", [note_ref, ref])
                shelf = shelves_by_ref.get(ref, {}).get("dimensions", {})
                width, depth = (derived("construction_assumption", [shelf.get(axis, pending_size)],
                                        lambda mm: mm, reason="Estimate the glass base on its supporting shelf.")
                                for axis in ("length", "width"))
                scope["parts"].extend(glass_box_parts(
                    width, depth, scope.get("glass_box_height", pending_size), thickness, scope_id=zone["id"], ref=ref))


def power_supply_watts(length_mm, watts_per_m):
    if length_mm <= 0 or watts_per_m <= 0:
        raise ValueError("Lighting length and power must be positive")
    length = Decimal(str(length_mm)) / 1000
    load = length * Decimal(str(watts_per_m)) * Decimal("1.2")
    step = int((load / 10).to_integral_value(rounding=ROUND_CEILING)) * 10
    return max(40 if length <= 5 else 50, step)


def _front_parts(rows, faces, spec, *, width, height, depth, panel_t, face_t,
                 box_material, face_material, divisions, glass, glass_t, source_only=False, face_sizes=None):
    bay_width = _assumed(None)
    if divisions:
        inner_width = _subtract(width, panel_t, divisions + 1)
        bay_width = derived("construction_assumption", [inner_width],
                            lambda w: w / divisions - 26,
                            reason="Equal bays with provisional slide clearance.")
    slide = derived("construction_assumption", [depth], _slide_depth_mm,
                    reason="Owner slide rule based on cabinet depth.")
    role_counts = defaultdict(int)
    for face in faces:
        role_counts[face["role"]] += 1
    for face in faces:
        role = face["role"]
        ref = f"{face['view_id']}:{face['candidate_id']}"
        measured = (face_sizes or {}).get(ref)
        if role == "drawer":
            face_h = _note_dim(spec, "drawer_face_height")
            box_width = bay_width
            face_w = derived("construction_assumption", [width], lambda w: w / role_counts[role] - 2,
                             reason="Equal drawer front widths with a provisional reveal.")
            if source_only and divisions != role_counts[role]:
                face_w = _assumed(None, width["refs"])
            if measured:
                face_w, face_h = measured[:2]
                if len(measured) == 3:
                    box_width = measured[2]
            rows.append(_sized("drawer_front", 1, face_material, face_w, face_h, face_t, instance_ref=ref))
            wall = derived("construction_assumption", [face_h], lambda h: h - 40,
                           reason="Provisional drawer-box height below front height.")
            rows.extend([
                _sized("drawer_box_side", 2, box_material, slide, wall, panel_t, instance_ref=ref),
                _sized("drawer_box_end", 2, box_material, _subtract(box_width, panel_t, 2), wall,
                       panel_t, instance_ref=ref),
                _sized("drawer_box_bottom", 1, box_material, box_width, slide, stock(6), instance_ref=ref),
                {**part("drawer_slide", 2, material="concealed soft-close drawer slide", length=slide),
                 "unit": "piece", "instance_ref": ref},
            ])
        elif role == "hinged_door":
            face_h = _note_dim(spec, "door_face_height")
            face_w = derived("construction_assumption", [width], lambda w: w / role_counts[role] - 2,
                             reason="Equal hinged door widths within the observed band.")
            if measured:
                face_w, face_h = measured
            hinge_height = face_h["mm"] if source_only else face_h["mm"] or height["mm"] or 1000
            rows.extend([
                _sized("door_front", 1, face_material, face_w, face_h, face_t, instance_ref=ref),
                {**part("hinge", _hinges_per_facade(hinge_height) if hinge_height else None,
                        material="hinge" if source_only else "Blum unsprung hinge"), "unit": "piece", "instance_ref": ref},
            ])
            if not source_only:
                rows.append({**part("push_latch", material="push latch"), "unit": "piece", "instance_ref": ref})
        elif role == "pull_out_shelf":
            rows.extend([
                _sized("pull_out_shelf", 1, box_material, bay_width, slide, panel_t, instance_ref=ref),
                {**part("pull_out_shelf_slide", 2, material="pull-out shelf slide", length=slide),
                 "unit": "piece", "instance_ref": ref},
            ])
            if glass:
                rows.extend(glass_box_parts(bay_width, slide, _note_dim(spec, "glass_box_height"), glass_t,
                                            scope_id=glass["id"], ref=ref))
        elif role == "fixed_open_shelf":
            rows.append(_sized("fixed_open_shelf", 1, box_material, width, depth, panel_t, instance_ref=ref))


SOURCE_CASEWORK = {"source_labelled_drawer_bank", "drawer_and_pull_out_bay",
                   "return_door_band", "assumed_lower_frame_split", "mirror_upright"}
OCR_LOOKALIKES = str.maketrans({
    "а": "a", "в": "b", "д": "d", "е": "e", "и": "u", "й": "u", "к": "k", "л": "l",
    "м": "m", "н": "h", "о": "o", "п": "n", "р": "p", "с": "c", "т": "y", "у": "y",
    "ф": "f", "ч": "c", "ы": "b",
})
STOCK_LABELS = {"carcass": ("корпусный", "carcass"), "facade": ("фасадный", "facade", "front"),
                "backing": ("задний", "backing")}
MM_STOCK = re.compile(r"(?<![\d.,×xх])(\d{1,2}(?:[.,]\d)?)\s*(?:mm|мм)\b", re.IGNORECASE)


def _stock_notes(input_rows, source_objects):
    """Read explicit role-labelled sheet thickness from the locked OCR blocks."""
    evidence = defaultdict(lambda: defaultdict(list))
    for row in input_rows:
        payload = row["input_payload"]
        oid = payload["object"]["object_id"]
        if oid not in source_objects or row["input_id"] != source_objects[oid]["input_id"]:
            continue
        for block in payload["evidence"].get("ocr_blocks", ()):
            if not block.get("block_ref"):
                continue
            for line in block["text"].splitlines():
                label, colon, spec = line.partition(":")
                words = re.findall(r"[^\W\d_]+", label.casefold())
                values = MM_STOCK.findall(spec)
                if not colon or len(words) != 2 or len(values) > 1 or re.search(r"\d\s*[–×xх-]\s*\d", spec):
                    continue
                if words[1] != "material" and SequenceMatcher(
                        None, words[1].translate(OCR_LOOKALIKES), "материал".translate(OCR_LOOKALIKES)).ratio() < .72:
                    continue
                first = words[0].translate(OCR_LOOKALIKES)
                roles = [role for role, labels in STOCK_LABELS.items() if any(
                    first == name or (len(first) >= 6 and SequenceMatcher(
                        None, first, name.translate(OCR_LOOKALIKES)).ratio() >= .78) for name in labels)]
                value = float(values[0].replace(",", ".")) if values else None
                if len(roles) == 1 and (value > 0 if value is not None else material_rule_for_text(spec)):
                    evidence[oid][roles[0]].append((value, block["block_ref"], spec.strip()))
    notes = defaultdict(dict)
    for oid, roles in evidence.items():
        for role, rows in roles.items():
            if len({value for value, _, _ in rows}) == 1:
                value, _, _ = rows[0]
                notes[oid][role] = {"mm": value, "basis": "ocr_material_note",
                                    "refs": list(dict.fromkeys(ref for _, ref, _ in rows)),
                                    "source_text": list(dict.fromkeys(spec for _, _, spec in rows))}
    return notes


PLINTH_PARTS = {"plinth_visible_run", "plinth_front", "plinth_return", "plinth_kit"}


def _part_stock_callout(callouts, contour_refs):
    """Use a material note only when every arrow tip hits this part."""
    matches = defaultdict(list)
    for source in callouts:
        tips = source.get("tips") or ()
        text = source.get("source_text")
        if not text or not source.get("annotation_id") or not tips:
            continue
        vid = source["view_id"]
        hits = [{f"{vid}:{cid}" for cid in tip["contours"]} for tip in tips]
        if all(hit and hit <= contour_refs for hit in hits):
            matches[" ".join(text.casefold().split())].append(source)
    if len(matches) != 1:
        return None
    sources, = matches.values()
    text = sources[0]["source_text"]
    values = {float(v.replace(",", ".")) for v in MM_STOCK.findall(text)}
    if len(values) > 1:
        return None
    return {"mm": next(iter(values), None), "basis": "ocr_material_note",
            "refs": list(dict.fromkeys(ref for source in sources
                for ref in [f"{source['view_id']}:{source['annotation_id']}",
                            *(f"{source['view_id']}:{cid}" for tip in source["tips"] for cid in tip["contours"])])),
            "source_text": [text]}


def _finish_words(text):
    value = text.casefold().translate(OCR_LOOKALIKES)
    return {finish for finish, pattern in {
        "stain": r"\bstain|[tym][oо][hн][uiи]?po",
        "polyurethane": r"polyurethane|[np]o[li]uyp",
        "oil": r"\boil\b|mac[ln]o",
    }.items() if re.search(pattern, value)}


def _same_facade_stock(local, facade):
    if not facade:
        return False
    local_text, = local["source_text"]
    material = material_rule_for_text(local_text)
    finish = _finish_words(local_text)
    return bool(material and finish and all(
        (rule := material_rule_for_text(text)) and rule.family == material.family
        and finish == _finish_words(text) for text in facade["source_text"]
    ))


def _apply_stock(row, inherited, local, *, role):
    if local:
        row["material_note"] = local
        row["material_hint"] = local["source_text"][0]
        row["material_basis"] = "part_material_callout"
        if local["mm"] is not None:
            row["dimensions"]["thickness"] = local
        elif inherited and inherited["mm"] is not None:
            row["dimensions"]["thickness"] = {
                **inherited, "basis": "inherited_facade_stock",
                "refs": list(dict.fromkeys([*local["refs"], *inherited["refs"]])),
            }
    elif inherited:
        row["material_note"] = inherited
        if inherited["mm"] is not None:
            row["dimensions"]["thickness"] = inherited
        row["material_hint"] = inherited["source_text"][0]
        row["material_basis"] = f"inherited_{role}_stock"


def _standalone_source_parts(item, callouts, *, readings, views, printed, facade_thickness):
    from tools.estimation_casework_part_geometry import casework_closure_spans, casework_plinth_spans

    if item["role"] == "plinth" and item.get("quantity") == 1:
        if views and (runs := casework_plinth_spans(readings, views, printed)):
            return [{**part("plinth_visible_run", material="plinth stock", length=length,
                            width=height, thickness=stock(17)), "construction_basis": "visible runs only"}
                    for length, height in runs]
        refs = [f"{ref['view_id']}:{cid}" for ref in item["source_refs"] for cid in ref.get("contour_ids", ())]
        return [{**part("plinth_kit", material="plinth stock", length=_assumed(None, refs),
                       width=_assumed(None, refs), thickness=_assumed(None, refs)), "unit": "set"}]
    if item["role"] == "window_closure":
        refs = [f"{ref['view_id']}:{ref['annotation_id']}" for ref in item["source_refs"] if ref.get("annotation_id")]
        note = " ".join(callouts.get(ref, "") for ref in refs).casefold()
        if ("фасадн" in note or "facade material" in note) and ("гипсокартон" in note or "drywall" in note):
            item["quantity"] = 1
            unknown = _assumed(None, refs)
            length, height = (casework_closure_spans(item, readings, views, printed) if views else None) or (unknown, unknown)
            return [_sized("closure_exterior_skin", 1, "facade material", length, height, facade_thickness or unknown),
                    _sized("closure_interior_skin", 1, "painted drywall", length, height, unknown)]
    return []


def add_source_casework_parts(parts, inventory, analyze, geometry, *, input_rows=(), detection=None, views=None, pdf=None):
    """Build provisional Parts from locked topology and measured shell axes."""
    stock_notes = _stock_notes(input_rows, {row["object_id"]: row for row in (detection or {}).get("objects", ())})
    for oid, obj in inventory["objects"].items():
        planned = analyze["objects"][oid]
        readings = {row["block_id"]: row["measurements"] for row in geometry["objects"][oid]["blocks"]}
        printed = geometry["objects"][oid].get("printed_dimensions", {})
        blocks = {block["id"]: block for block in planned["planner"]["blocks"]}
        callouts = {row["id"]: row["source_text"] for row in planned["planner"].get("component_callouts", ())}
        output = parts["objects"][oid]
        scopes = {row.get("block_id") or row["id"]: row for row in [*output["blocks"], *output["shared_parts"]]}
        material_callouts = planned["front"].get("material_callouts", ())
        owners = planner_owners(planned["planner"])
        for item in obj["items"]:
            ident = item["id"]
            scope = scopes.get(ident)
            if scope is None:
                continue
            face_sizes = {}
            if item["kind"] == "block":
                block = blocks[ident]
                width, height, depth = (_envelope(readings[ident], axis) for axis in ("width", "height", "depth"))
                if not scope["parts"] and block["basis"] in SOURCE_CASEWORK:
                    faces = [face for face in planned["front"]["faces"] if face.get("candidate_id")
                             and face["candidate_id"] in block["appearances"].get(face["view_id"], ())]
                    roles = defaultdict(set)
                    for face in faces:
                        roles[face["role"]].add((face["view_id"], face["candidate_id"]))
                    faces = list({(face["view_id"], face["candidate_id"], face["role"]): face for face in faces}.values())
                    divisions = len(block.get("positions", ())) or len(roles["drawer"])
                    thickness = stock_notes[oid].get("carcass", _assumed(None))
                    face_thickness = stock_notes[oid].get("facade", _assumed(None))
                    if views:
                        from tools.estimation_casework_part_geometry import source_casework_part_geometry

                        face_sizes, glass_height = source_casework_part_geometry(
                            block, readings[ident], faces, views, geometry["objects"][oid]["printed_dimensions"],
                            glazed=any(child["role"] == "glazed_zone" for child in item["children"]),
                            panel_t=thickness, pdf=pdf)
                        if glass_height:
                            scope["glass_box_height"] = glass_height
                    if block["basis"] == "mirror_upright":
                        panel_depth = (depth if readings[ident].get("depth", {}).get("from") == "rear face of mounting panel"
                                       else _assumed(None))
                        scope["parts"] = [_sized("mirror_mounting_panel", 1, "panel stock", height, width, panel_depth)]
                    else:
                        scope["parts"] = _box(width, height, depth, thickness, "cabinet panel stock",
                                              stock_notes[oid].get("backing", stock(6)), max(0, divisions - 1))
                        _front_parts(scope["parts"], faces, {}, width=width, height=height, depth=depth,
                                     panel_t=thickness, face_t=face_thickness, box_material="cabinet panel stock",
                                     face_material="facade stock", divisions=divisions, glass=None,
                                     glass_t=None, source_only=True, face_sizes=face_sizes)
                    scope["review"] = ["Standard construction estimate. Confirm joinery, stock and unresolved sizes."]
                    for row in scope["parts"]:
                        if row["role"] not in {"drawer_slide", "pull_out_shelf_slide", "hinge"}:
                            row["construction_basis"] = "standard_construction_estimate"
                elements = item["children"]
                panels = [row for row in scope["parts"] if row["role"] == "mirror_mounting_panel"]
                if panels:
                    glass_refs = {f"{ref['view_id']}:{ref['candidate_id']}"
                                  for child in elements if child["role"] == "mirror"
                                  for ref in child["source_refs"] if ref.get("candidate_id")}
                    panel_refs = {f"{vid}:{cid}" for vid, ids in block.get("appearances", {}).items()
                                  for cid in ids if owners[f"{vid}:{cid}"] == {ident}} - glass_refs
                    local = _part_stock_callout(material_callouts, panel_refs) if len(panels) == 1 else None
                    facade = stock_notes[oid].get("facade")
                    inherited = stock_notes[oid].get("carcass")
                    if local:
                        inherited = facade if _same_facade_stock(local, facade) else None
                    for row in panels:
                        _apply_stock(row, inherited, local, role="carcass")
            else:
                width = height = _assumed(None)
                if not scope["parts"]:
                    scope["parts"] = _standalone_source_parts(
                        item, callouts, readings=readings, views=views, printed=printed,
                        facade_thickness=stock_notes[oid].get("facade"))
                elements = [item]
            for row in scope["parts"]:
                is_plinth = row["role"] in PLINTH_PARTS
                if not is_plinth and row["role"] not in VISIBLE_GRAIN_ROLES:
                    continue
                refs = {ref for axis in ("length", "width")
                        for ref in row["dimensions"].get(axis, {}).get("refs", ())}
                if not is_plinth and row.get("instance_ref"):
                    refs = {row["instance_ref"]}
                local = _part_stock_callout(material_callouts, refs)
                facade = stock_notes[oid].get("facade")
                if is_plinth:
                    _apply_stock(row, facade if not local or _same_facade_stock(local, facade) else None,
                                 local, role="facade")
                elif local or (row.get("visual_stock") and not row.get("material_note") and
                               row["role"] in {"drawer_front", "door_front", "lift_up_front"}):
                    exact = row["dimensions"].get("thickness", {}).get("basis") == "printed_dimension"
                    thickness = row["dimensions"].get("thickness")
                    _apply_stock(row, facade if not local else None, local, role="facade")
                    if exact and (not local or local["mm"] is None):
                        row["dimensions"]["thickness"] = thickness
            single_lighting_note = sum(element["role"] == "lighting" for element in elements) == 1
            for element in sorted(elements, key=lambda row: row["role"] == "lighting"):
                element_id = element["id"]
                if element["role"] == "mirror":
                    refs = [f"{ref['view_id']}:{ref['candidate_id']}" for ref in element["source_refs"]
                            if ref.get("candidate_id")]
                    ref = refs[0] if refs else element_id
                    face_width, face_height = face_sizes.get(ref, (_assumed(None, refs), _assumed(None, refs)))
                    scope["parts"].append(_sized("mirror_glass", element.get("quantity"), "mirror glass",
                        face_height, face_width,
                        _assumed(None, refs), instance_ref=ref, inventory_item_id=element_id))
                elif element["role"] == "lighting" and "kelvin_values" in element:
                    values = element["kelvin_values"]
                    refs = [f"{ref['view_id']}:{ref['annotation_id']}" for ref in element["source_refs"]]
                    length = (_source_lighting_length(element, scope["parts"], readings.get(ident, {}))
                              if single_lighting_note else None)
                    if (length is None and pdf is not None and views and item["kind"] == "block"
                            and analyze["islands"].get(readings[ident].get("depth", {}).get("view_id")) == "Top view"):
                        from tools.estimation_casework_part_geometry import casework_lighting_span

                        length = casework_lighting_span(element, readings[ident], views, printed, pdf)
                    scope["parts"].append({
                        **part("led_strip_run", 1 if length else element.get("quantity"), material="LED strip",
                               length=length or _assumed(None, dict.fromkeys(refs))),
                        "inventory_item_id": element_id, "instance_ref": element_id, "unit": "run",
                        "colour_temperature_k": values[0] if len(values) == 1 else None,
                        "colour_temperature_status": {0: "temperature_pending", 1: "source_reading"}.get(
                            len(values), "temperature_conflict"),
                        "colour_temperature_sources": element["source_refs"],
                    })


def _lighting(circuits, mirrors, blocks, watts, object_id, temperature_readings):
    rows, lengths = [], []
    for circuit in circuits:
        ref = circuit["id"]
        readings = [reading for reading in temperature_readings
                    if reading["view_id"] in circuit["temperature_source_views"]
                    and ("temperature_source_annotation" not in circuit
                         or reading.get("annotation_id") == circuit["temperature_source_annotation"])]
        values = {value for reading in readings for value in reading["kelvin_values"]}
        kelvin = next(iter(values)) if len(values) == 1 else None
        status = {0: "temperature_pending", 1: "source_reading"}.get(len(values), "temperature_conflict")
        if circuit.get("mirror_id"):
            span = mirrors[circuit["mirror_id"]]["height"]
        else:
            span = _envelope(blocks[circuit["block_id"]], "width")
        length = derived("construction_assumption", [span], lambda n: n * circuit["passes"],
                         reason="Visible strip passes multiplied by their estimated span.")
        length["refs"] = list(dict.fromkeys([*length["refs"], *circuit["refs"]]))
        if length["mm"] is None:
            raise ValueError(f"Lighting circuit {ref} lacks a span for the reviewed estimate")
        capacity = power_supply_watts(length["mm"], watts)
        rows.extend([
            {**part("led_strip_run", material="LED strip", length=length), "unit": "run", "instance_ref": ref,
             "colour_temperature_k": kelvin, "colour_temperature_status": status,
             "colour_temperature_sources": readings, "watts_per_m": watts},
            {**part("led_power_supply", material="LED power supply"), "unit": "piece", "instance_ref": ref,
             "capacity_w": capacity, "headroom_percent": 20, "length_mm": length["mm"]},
        ])
        lengths.append({"object_id": object_id, "circuit_id": ref, "kelvin": kelvin,
                        "colour_temperature_status": status,
                        "watts_per_m": watts, "length_mm": length["mm"], "supply_w": capacity,
                        "segment_length_mm": span["mm"], "segments": circuit["passes"]})
    return rows, lengths


def _coils(circuits):
    groups = defaultdict(list)
    for circuit in circuits:
        if circuit["kelvin"] is not None:
            groups[circuit["kelvin"], circuit["watts_per_m"]].append(circuit)
    output = []
    for (kelvin, watts), rows in sorted(groups.items()):
        segments = [row["segment_length_mm"] for row in rows for _ in range(row["segments"])]
        pieces = []
        for length in segments:
            full, remainder = divmod(length, 5000)
            pieces.extend([5000] * full)
            if remainder:
                pieces.append(remainder)
        reels = []
        for length in sorted(pieces, reverse=True):
            reel = next((i for i, remaining in enumerate(reels) if remaining >= length), None)
            if reel is None:
                reels.append(5000 - length)
            else:
                reels[reel] -= length
        output.append({"role": "led_strip_coil", "kelvin": kelvin, "watts_per_m": watts,
                       "coil_length_mm": 5000, "installed_length_mm": sum(segments), "quantity": len(reels),
                       "remaining_mm_by_coil": reels, "circuit_ids": [row["circuit_id"] for row in rows]})
    return output


def apply_reviewed_display_parts(parts, inventory, analyze, geometry, profile):
    """Add recipes only for the exact reviewed source packet and listed scopes."""
    if profile["source_audit_sha256"] != parts["source_audit_sha256"]:
        raise ValueError("Reviewed construction profile belongs to another source packet")
    if profile["objects"].keys() != parts["objects"].keys():
        raise ValueError("Reviewed construction profile must account for every object")
    material = profile["materials"]
    refs = material["refs"]
    panel_t = dimension(material["panel_mm"], "printed_note", refs)
    face_t = dimension(material["face_mm"], "printed_note", refs)
    glass_t = dimension(material["glass_mm"], "owner_construction_rule")
    box_material, face_material = material["panel"], material["face"]
    all_circuits = []
    for oid, reviewed in profile["objects"].items():
        obj = inventory["objects"][oid]
        result = parts["objects"][oid]
        planned = analyze["objects"][oid]
        measured = {row["block_id"]: row["measurements"] for row in geometry["objects"][oid]["blocks"]}
        items = {item["id"]: item for item in obj["items"]}
        by_block = {block["id"]: block for block in planned["planner"]["blocks"]}
        if reviewed["blocks"].keys() != by_block.keys():
            raise ValueError(f"Reviewed profile must cover every planned block for {oid}")
        for out in result["blocks"]:
            bid = out["block_id"]
            if out["parts"]:
                raise ValueError(f"Reviewed profile overlaps existing Parts for {bid}")
            spec = reviewed["blocks"][bid]
            block = by_block[bid]
            width, height, depth = (_envelope(measured[bid], key) for key in ("width", "height", "depth"))
            faces = [face for face in planned["front"]["faces"] if
                     face.get("candidate_id") in block.get("members", ()) and face["view_id"] in block["appearances"]]
            divisions = spec.get("divisions", 1)
            if spec["construction"] == "panel":
                panel_height = height if height["mm"] is not None else _note_dim(spec, "panel_height")
                rows = [_sized("mirror_mounting_panel", 1, face_material, panel_height, width, face_t)]
            else:
                rows = _box(width, height, depth, panel_t, box_material, stock(6), divisions - 1)
            glass = next((child for child in items[bid]["children"] if child["role"] == "glazed_zone"), None)
            _front_parts(rows, faces, spec, width=width, height=height, depth=depth, panel_t=panel_t,
                         face_t=face_t, box_material=box_material, face_material=face_material,
                         divisions=divisions, glass=glass, glass_t=glass_t)
            if glass:
                glass["quantity"] = sum(face["role"] == "pull_out_shelf" for face in faces)
                glass["unit"] = "glass_box"
                glass["quantity_basis"] = "one glass box per visible pull-out shelf, estimated from the drawing"
            if shelf_view := spec.get("open_shelf_view"):
                shelf_id = f"fixed-shelf:{bid}"
                shelf_sources = []
                for observation in obj["source_review_findings"]:
                    if observation["role"] == "fixed_open_shelf" and observation["source"]["view_id"] == shelf_view:
                        shelf_sources.append(observation["source"])
                        observation["candidate_owner_ids"] = [shelf_id]
                        observation["status"] = "assigned"
                        observation["disposition"] = "reviewed_source_profile"
                if not shelf_sources:
                    raise ValueError(f"Reviewed open shelf in {bid} lacks retained source evidence")
                items[bid]["children"].append({
                    "id": shelf_id, "kind": "element", "role": "fixed_open_shelf", "quantity": 1,
                    "source_refs": shelf_sources, "children": [],
                })
                rows.append(_sized("fixed_open_shelf", 1, box_material, width, depth, panel_t,
                                   inventory_item_id=shelf_id))
            if spec.get("fixed_front_blank"):
                rows.append(_sized("fixed_panel", 1, face_material, width, height, face_t))
            out["parts"] = rows
            out["review"] = ["Preliminary construction and fit clearances. Unbound dimensions stay open."]

        mirror_dimensions = {ident: {axis: _note_dim(spec, axis) for axis in ("width", "height")}
                             for ident, spec in reviewed["mirrors"].items()}
        scopes = {row["id"]: row for row in result["shared_parts"]}
        block_scopes = {row["block_id"]: row for row in result["blocks"]}
        mirror_owners = {child["id"]: item["id"] for item in obj["items"] if item["kind"] == "block"
                         for child in item["children"] if child["role"] == "mirror"}
        for ident, dims in mirror_dimensions.items():
            if owner := mirror_owners.get(ident):
                scope = block_scopes[owner]
            else:
                if items[ident]["role"] != "mirror":
                    raise ValueError(f"{ident} is not a mirror")
                scope = scopes[ident]
            scope["parts"].append(_sized("mirror_glass", 1, "mirror glass", dims["height"], dims["width"],
                                         _assumed(None), inventory_item_id=ident))
        lighting = items["lighting"]
        scopes["lighting"]["parts"], circuits = _lighting(
            reviewed["lighting_circuits"], mirror_dimensions, measured, profile["lighting_watts_per_m"], oid,
            scopes["lighting"]["colour_temperature_readings"])
        scopes["lighting"]["review"] = [
            "Run routing, voltage and provisional watts per metre require confirmation.",
            "Profiles, diffusers, connectors and wiring are not specified by the reviewed source.",
        ]
        lighting["quantity"] = len(circuits)
        lighting["unit"] = "estimated_circuit"
        all_circuits.extend(circuits)
        if closure := reviewed.get("closure"):
            scopes[closure]["parts"] = [
                _sized("closure_exterior_skin", 1, "facade material", _assumed(None), _assumed(None), face_t),
                _sized("closure_interior_skin", 1, "painted drywall", _assumed(None), _assumed(None), _assumed(None)),
            ]
            items[closure]["quantity"] = 1
            scopes[closure]["review"] = ["The annotation specifies both skins. Dimensions and mounting remain open."]
        plinth = scopes["plinth-kit"]
        plinth["parts"] = [_sized("plinth_visible_run", 1, face_material, _envelope(measured[bid], "width"),
                                 _note_dim(reviewed, "plinth_height"), face_t)
                           for bid in reviewed["plinth_blocks"]]
        plinth["review"] = ["One kit. Visible runs follow the reviewed lower bands; hidden returns remain open."]
    parts["lighting_purchase"] = {"circuits": all_circuits, "coils": _coils(all_circuits),
                                  "basis": "reviewed circuit and strip estimates",
                                  "watts_per_m_basis": profile["lighting_watts_basis"]}
