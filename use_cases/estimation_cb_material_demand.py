"""Adapt preliminary CB Parts to the existing assembly BOM material contract."""

from math import isfinite

from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1
from use_cases.estimation_structural_bom import _CONSTRUCTION_MATERIAL_NAMES, _FAMILY_PREFERENCE
from use_cases.material_engine_adapter import build_material_plan, material_plan_input_fingerprint, material_plan_snapshot
from use_cases.price_source_taxonomy import catalog_taxonomy_for_family, material_rule_for_text


_ROLES = {
    **dict.fromkeys(("carcass_side", "carcass_top", "carcass_bottom", "drawer_bay_divider"), "carcass_sheet"),
    **dict.fromkeys(("carcass_back", "drawer_box_bottom"), "backing_sheet"),
    **dict.fromkeys(("drawer_box_side", "drawer_box_end", "fixed_open_shelf", "pull_out_shelf",
                    "mirror_mounting_panel"), "internal_sheet"),
    **dict.fromkeys(("drawer_front", "door_front", "lift_up_front", "fixed_panel", "seat_cover", "frame_backing",
                    "frame_cap", "frame_side", "vertical_rib", "plinth_front", "plinth_return",
                    "plinth_visible_run", "closure_exterior_skin"), "visible_sheet"),
    **dict.fromkeys(("tabletop", "shared_worktop"), "worktop_sheet"),
    "tabletop_underlayer": "internal_sheet",
    "support_leg": "leg", "drawer_slide": "drawer_slide", "hinge": "hinge", "gas_lift": "gas_lift",
    "mirror_glass": "mirror",
}
_COUNT_ROLES = {"leg", "drawer_slide", "hinge", "gas_lift"}
_ROLE_FAMILY_PREFERENCE = {
    **_FAMILY_PREFERENCE,
    "carcass_sheet": _FAMILY_PREFERENCE["internal_sheet"],
    "backing_sheet": ("mdf_hdf",),
    "mirror": ("mirror",),
}
_MATERIAL_NAMES = {**_CONSTRUCTION_MATERIAL_NAMES, "mirror": "Mirror"}
_SHEET_DIMENSIONS = ("length", "width", "thickness")
_SPECIAL_DIMENSIONS = {"led_strip_run": ("length",), "led_power_supply": ()}
_MATERIAL_HOLDS = {
    "shared_worktop": "worktop_cut_geometry_unresolved",
    **dict.fromkeys(("glass_box_bottom", "glass_box_long_wall", "glass_box_end_wall"),
                    "glass_treatment_resolution_required"),
    **dict.fromkeys(("led_strip_run", "led_power_supply"), "lighting_material_resolution_required"),
}
_WORKTOP_DEFAULT_FAMILY = "engineered_quartz_mineral_hybrid"


def _positive(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def _source_scopes(stage, source):
    if stage == "CB Parts":
        return [(scope.get("block_id") or scope["id"], scope)
                for scope in [*source["blocks"], *source["shared_parts"]]]
    by_owner = {}
    for row in source["parts"]:
        by_owner.setdefault(row["owner_id"], {"parts": []})["parts"].append(row)
    return list(by_owner.items())


def _source_material(measurements):
    thickness = measurements.get("thickness", {})
    if thickness.get("basis") != "ocr_material_note":
        return None, {}, (), ()
    notes = thickness.get("source_text") or ()
    if isinstance(notes, str):
        notes = (notes,)
    if not notes:
        return None, {}, (), ()
    materials = set()
    for note in notes:
        # Drawing OCR also supplies Russian material terms. Match the literal
        # term, and leave a corrupted or ambiguous label for review.
        words = note.casefold().split(maxsplit=1)
        token = words[0].strip(".,:;()") if words else ""
        family = {"фанера": "plywood", "мдф": "mdf", "хдф": "hdf"}.get(token)
        if not family and (rule := material_rule_for_text(note)):
            family = rule.family
        taxonomy = catalog_taxonomy_for_family(family)
        if not taxonomy:
            return None, {}, notes, ()
        code = taxonomy["family_code"]
        board_type = family if code == "mdf_hdf" and family in {"mdf", "hdf"} else None
        materials.add((code, board_type))
    refs = tuple(thickness.get("refs", ()))
    if len(materials) == 1 and refs:
        family, board_type = materials.pop()
        return family, {"board_type": board_type} if board_type else {}, notes, refs
    return None, {}, notes, ()


def _worktop_requirements(row, part_source, object_quantity, families, materials, review_items):
    outline = row.get("worktop_outline") or {}
    surfaces = outline.get("surfaces") or ()
    thickness = row["dimensions"].get("thickness", {}).get("mm")
    count = row["quantity"]
    if (outline.get("area_basis") != "gross_plan_outline" or not surfaces
            or not _positive(thickness) or not _positive(count) or int(count) != count
            or not all(_positive(surface.get("area_m2")) for surface in surfaces)):
        return False
    multiplier = count * part_source["scope_quantity"] * object_quantity
    finish_view = outline.get("finish_evidence", {}).get("view_id")
    stock_family, stock_spec, stock_notes, stock_refs = _source_material(row["dimensions"])
    refs = list(dict.fromkeys([*part_source["evidence_refs"], *outline["source_refs"],
                               *outline.get("seam_source_refs", ()), *([finish_view] if finish_view else [])]))
    part_id = part_source["part_id"]
    for surface in surfaces:
        main = surface["material_role"] == "main_worktop"
        explicit = main and stock_family in families
        default = main and not stock_notes and outline.get("kitchen_worktop") and _WORKTOP_DEFAULT_FAMILY in families
        family = stock_family if explicit else _WORKTOP_DEFAULT_FAMILY if default else None
        evidence = list(dict.fromkeys([*refs, *stock_refs])) if explicit else refs
        quantity = round(surface["area_m2"] * multiplier, 6)
        key = (part_id, surface["id"])
        materials[key] = {
            "requirement_id": f"cb-material-{len(materials) + 1:03d}",
            "source_name": " / ".join(stock_notes) if explicit else "Artificial stone" if default else (
                "Main worktop material" if main else "Contrasting finish on beveled end"),
            "family": family, "material_role": "worktop_sheet",
            "specification": {"thickness_mm": thickness, **(stock_spec if explicit else {})},
            "basis": "ocr_material_note" if explicit else "construction_assumption" if default else "material_unresolved",
            "evidence_refs": evidence, "quantity": quantity, "unit": "m2",
            "area_basis": outline["area_basis"],
            "part_sources": [{**part_source, "surface": surface, "evidence_refs": evidence}],
        }
        if not family:
            review_items.append({"part_id": part_id, "surface_id": surface["id"],
                                 "reason": "worktop_material_family_unresolved",
                                 "area_m2": quantity})
    if outline["cutout_status"] == "unresolved":
        review_items.append({"part_id": part_id, "reason": "worktop_cutouts_unresolved"})
    return True


def build_cb_material_demand(*, parts_report, input_row, allowed_material_families):
    """Convert each checked part to demand or retain its data for review."""
    payload = input_row["input_payload"]
    obj = payload["object"]
    object_id = obj["object_id"]
    object_quantity = obj["quantity"]
    stage = parts_report["stage"]
    if stage not in {"CB Parts", "Parts Check"} or not _positive(object_quantity) or int(object_quantity) != object_quantity:
        raise ValueError("Parts demand requires an immutable object input with a whole positive quantity")
    if parts_report.get("run_id", payload["run_id"]) != payload["run_id"]:
        raise ValueError("Parts Check must belong to the same run as the immutable object input")
    source = parts_report["objects"][object_id]
    scopes = _source_scopes(stage, source)
    if len(scopes) != len({key for key, _ in scopes}):
        raise ValueError("Block and shared part IDs must be unique within the object")
    materials, parts, review_items, assumptions = {}, [], [], []
    inventory_issues = list(source.get("inventory_issues", source.get("inventory_review_items", ())))
    coverage = parts_report.get("source_coverage")
    if coverage and coverage != "reviewed":
        inventory_issues.append({"reason": coverage})
    inventory_issues.extend({"reason": "unassigned_source_finding", "finding": finding}
                            for finding in parts_report.get("unassigned_source_findings", ()))
    duplicate_refs = {(issue["role"], issue["source_ref"]) for issue in inventory_issues
                      if issue["reason"] == "duplicate_part_evidence"}
    source_part_count = 0
    for scope_id, scope in scopes:
        assumptions.extend(f"{scope_id}: {note}" for note in scope.get("review", ()))
        if not scope["parts"]:
            review_items.append({"part_id": scope_id, "reason": "construction_unresolved"})
        for index, row in enumerate(scope["parts"], start=1):
            source_part_count += 1
            part_id = f"{scope_id}:{row['role']}:{index:03d}"
            multiplier = row.get("scope_quantity", scope.get("quantity", 1))
            if not _positive(multiplier) or int(multiplier) != multiplier:
                raise ValueError(f"Invalid scope quantity for {scope_id}")
            role = _ROLES.get(row["role"])
            measurements = row["dimensions"]
            refs = list(dict.fromkeys(ref for value in measurements.values() for ref in value.get("refs", ())))
            refs = list(dict.fromkeys([*refs, *row.get("count_refs", ()),
                                       *([row["instance_ref"]] if row.get("instance_ref") else [])]))
            part_source = {**row, "part_id": part_id, "scope_id": scope_id,
                           "scope_quantity": multiplier, "evidence_refs": refs}
            duplicate = (row["role"], row.get("instance_ref")) in duplicate_refs
            if row["role"] == "shared_worktop" and not duplicate and _worktop_requirements(
                    row, part_source, object_quantity, allowed_material_families, materials, review_items):
                continue
            is_count = role in _COUNT_ROLES
            required = () if is_count else _SPECIAL_DIMENSIONS.get(row["role"], _SHEET_DIMENSIONS)
            missing = [field for field in required if not _positive(measurements.get(field, {}).get("mm"))]
            source_family, material_spec, notes, material_refs = _source_material(measurements)
            preferences = (source_family,) if source_family else _ROLE_FAMILY_PREFERENCE.get(role, ())
            family = next((f for f in preferences if f in allowed_material_families), None)
            count = row["quantity"]
            reason = _MATERIAL_HOLDS.get(row["role"])
            if duplicate:
                reason = "duplicate_part_evidence"
            elif reason is None:
                if not role:
                    reason = "unsupported_material_role"
                elif missing:
                    reason = "dimensions_unresolved"
                elif count is None:
                    reason = "quantity_unresolved"
                elif notes and not source_family:
                    reason = "material_note_unresolved"
                elif not family:
                    reason = "material_family_unavailable"
            if reason:
                review_items.append({"part_id": part_id, "role": row["role"], "missing_dimensions": missing,
                                     "reason": reason, "part_source": part_source})
                continue
            if not _positive(count) or int(count) != count:
                raise ValueError(f"Invalid part quantity for {part_id}")
            quantity = int(count * multiplier * object_quantity)
            unit = (row.get("unit") or "piece") if is_count else None
            spec = {} if is_count else {**material_spec, "thickness_mm": measurements["thickness"]["mm"]}
            basis = "source_evidence" if material_refs else "construction_assumption"
            name = notes[0] if material_refs else _MATERIAL_NAMES[family]
            if family == "mdf_hdf" and not material_refs and role in {"carcass_sheet", "backing_sheet", "internal_sheet"}:
                spec.update(board_type="hdf" if role == "backing_sheet" else "mdf", surface="raw")
                if role == "backing_sheet":
                    name = "HDF"
            if role == "drawer_slide":
                if unit == "set":
                    quantity *= 2
                elif unit != "piece" or int(count * multiplier) % 2:
                    raise ValueError("Drawer slide pieces must form complete sets")
                unit = "piece"
                length = measurements.get("length", {})
                if _positive(length.get("mm")):
                    spec["depth_mm"] = length["mm"]
            key = (role, family, name, basis, unit, tuple(sorted(spec.items())))
            if key not in materials:
                materials[key] = {
                    "requirement_id": f"cb-material-{len(materials) + 1:03d}",
                    "source_name": name, "family": family, "material_role": role,
                    "specification": spec, "basis": basis, "evidence_refs": [],
                    "quantity": 0 if is_count else None, "unit": unit, "part_sources": [],
                }
            material = materials[key]
            material["evidence_refs"] = list(dict.fromkeys([*material["evidence_refs"], *material_refs]))
            material["part_sources"].append({**part_source, "quantity": quantity, "unit": unit,
                                             "source_quantity": count, "source_unit": row.get("unit"),
                                             "measurements": measurements})
            if is_count:
                material["quantity"] += quantity
            else:
                parts.append({
                    "part_id": part_id, "assembly_id": scope_id, "component_role": row["role"],
                    "material_requirement_id": material["requirement_id"], "quantity": quantity,
                    "length_mm": measurements["length"]["mm"], "width_mm": measurements["width"]["mm"],
                    "rotation_allowed": role not in {"visible_sheet", "worktop_sheet"},
                    "basis": "construction_assumption", "evidence_refs": refs,
                    "assumption_reason": "Cut geometry comes from the preliminary Parts estimate.",
                })
    review_items.extend({"part_id": row["instance_ref"], "role": row["role"], "reason": "ownership_unresolved"}
                        for row in source.get("unassigned_fronts", ()))
    for index, issue in enumerate(inventory_issues, 1):
        part_id = issue.get("item_id") or issue.get("source_ref") or f"inventory-review-{index}"
        review_items.append({**issue, "part_id": part_id})
    return {
        "contract_version": ASSEMBLY_BOM_V1, "composition_version": "cb_parts_material_demand_v1",
        "input_id": input_row["input_id"], "object_input_revision": input_row.get("object_input_revision", 1),
        "company_id": payload["company_id"], "run_id": payload["run_id"],
        "object_id": object_id, "object_name": obj.get("object_name") or object_id, "quantity": object_quantity,
        "status": "review_required" if review_items else "ready", "materials": list(materials.values()),
        "source_part_count": source_part_count,
        "parts": parts, "review_items": review_items, "assumptions": list(dict.fromkeys(assumptions)),
        "primary_preview_ref": next((a["storage_ref"] for a in payload.get("evidence", {}).get("artifacts", [])
                                     if a.get("storage_ref")), ""),
    }


def calculate_cb_materials(*, parts_report, input_rows, catalog_context):
    """Calculate one document through the existing estimate-wide Material Plan."""
    facts = {}
    run_ids = set()
    allowed = set(catalog_context["families"])
    for row in input_rows:
        item = build_cb_material_demand(parts_report=parts_report, input_row=row, allowed_material_families=allowed)
        if item["company_id"] != catalog_context["company_id"] or item["object_id"] in facts:
            raise ValueError("Parts costing requires matching catalog tenant and unique object inputs")
        facts[item["object_id"]] = item
        run_ids.add(item["run_id"])
    if len(run_ids) != 1 or facts.keys() != parts_report["objects"].keys():
        raise ValueError("Parts costing requires every immutable input from the same run")
    catalogs = catalog_context["catalogs"]
    priced_facts = {oid: {**item, "materials": [material for material in item["materials"] if material["family"]]}
                    for oid, item in facts.items()}
    fingerprint = material_plan_input_fingerprint(
        facts_by_object=priced_facts, material_default_variants=catalogs.get("material_default_variants") or (),
    )
    snapshot = material_plan_snapshot(build_material_plan(facts_by_object=priced_facts, catalogs=catalogs),
                                      input_fingerprint=fingerprint)
    gaps = {oid: item["review_items"] for oid, item in facts.items() if item["review_items"]}
    if gaps:
        snapshot["status"] = "needs_review"
        snapshot["cb_parts_review_items"] = gaps
        snapshot["reason_codes"].append("cb_parts_review_required")
    return {"composition_version": "cb_parts_material_demand_v1", "facts_by_object": facts,
            "material_plan": snapshot}
