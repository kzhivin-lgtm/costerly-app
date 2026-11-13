"""Adapt preliminary CB Parts to the existing assembly BOM material contract."""

from math import ceil, isfinite
import re

from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1
from use_cases.estimation_structural_bom import _CONSTRUCTION_MATERIAL_NAMES, _FAMILY_PREFERENCE
from use_cases.material_engine_adapter import build_material_plan, material_plan_input_fingerprint, material_plan_snapshot
from use_cases.material_identity_resolution import normalize_material_phrase
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
_LDSP_FAMILY = "melamine_faced_particleboard"
_LDSP_DEFAULT_THICKNESS_MM = 17
_STANDARD_LED_STRIP = "LED strip standard output"
_LED_FAMILY = "hardware_electrical_component"
_ROLE_FAMILY_PREFERENCE = {
    **_FAMILY_PREFERENCE,
    "carcass_sheet": _FAMILY_PREFERENCE["internal_sheet"],
    "backing_sheet": ("mdf_hdf",),
    "visible_sheet": _FAMILY_PREFERENCE["internal_sheet"],
    "mirror": ("mirror",),
}
_MATERIAL_NAMES = {**_CONSTRUCTION_MATERIAL_NAMES, "mirror": "Mirror"}
_WORKTOP_DEFAULT_FAMILY = "engineered_quartz_mineral_hybrid"
_STONE_CUTOUT_FAMILIES = {"natural_stone_slab", _WORKTOP_DEFAULT_FAMILY, "sintered_ultra_compact_surface",
                          "porcelain_ceramic_slab", "solid_surface", "terrazzo_engineered_agglomerate"}
_CYRILLIC_OCR_GLYPHS = str.maketrans("авекмнорстухф", "abekmhopcyyxf")


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


def _stock_alias_family(note, family_alias_context):
    text = normalize_material_phrase(note)
    matches = set()
    for family, context in family_alias_context.items():
        for alias in context.get("family_aliases", ()):
            phrase = normalize_material_phrase(alias)
            if phrase and re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text):
                matches.add(family)
                break
    return next(iter(matches)) if len(matches) == 1 else None


def _ocr_stock_alias_family(note, family_alias_context):
    # A role-labelled thickness note can contain Latin OCR for a Cyrillic
    # material token. Compare its leading token only against shared aliases.
    token = normalize_material_phrase(note).split()[0:1]
    if not token or not re.fullmatch(r"[a-z]{6,}", token[0]):
        return None
    observed = token[0].replace("ph", "f").replace("n", "h")
    matches = set()
    for family, context in family_alias_context.items():
        for alias in context.get("family_aliases", ()):
            phrase = normalize_material_phrase(alias)
            if not re.fullmatch(r"[а-яё]{6,}", phrase):
                continue
            expected = phrase.translate(_CYRILLIC_OCR_GLYPHS)
            if (len(observed) == len(expected) and observed[:3] == expected[:3]
                    and sum(a != b for a, b in zip(observed, expected)) <= 1):
                matches.add(family)
    return next(iter(matches)) if len(matches) == 1 else None


def _source_material(measurements, family_alias_context, material_note=None):
    source = material_note or measurements.get("thickness", {})
    if source.get("basis") != "ocr_material_note":
        return None, {}, (), ()
    notes = source.get("source_text") or ()
    if isinstance(notes, str):
        notes = (notes,)
    if not notes:
        return None, {}, (), ()
    materials = set()
    for note in notes:
        words = note.casefold().split(maxsplit=1)
        token = words[0].strip(".,:;()") if words else ""
        family = {"мдф": "mdf", "хдф": "hdf"}.get(token)
        if not family and (rule := material_rule_for_text(note)):
            family = rule.family
        taxonomy = catalog_taxonomy_for_family(family)
        if not taxonomy:
            alias_family = (_stock_alias_family(note, family_alias_context)
                            or _ocr_stock_alias_family(note, family_alias_context))
            if alias_family:
                materials.add((alias_family, None))
                continue
            return None, {}, notes, ()
        code = taxonomy["family_code"]
        board_type = family if code == "mdf_hdf" and family in {"mdf", "hdf"} else None
        materials.add((code, board_type))
    refs = tuple(source.get("refs", ()))
    if len(materials) == 1 and refs:
        family, board_type = materials.pop()
        return family, {"board_type": board_type} if board_type else {}, notes, refs
    return None, {}, notes, ()


def _part_material_identity(hint, known_family, catalog_names):
    """Use the common taxonomy and catalog names when the role has no stock default."""
    tokens = set(normalize_material_phrase(hint).split())
    if not tokens:
        return known_family, None
    rule = material_rule_for_text(hint)
    taxonomy = catalog_taxonomy_for_family(rule.family) if rule else None
    family = known_family or (taxonomy or {}).get("family_code")
    families = {code for code, name in catalog_names if tokens <= name}
    if not family and len(families) == 1:
        family = next(iter(families))
    return family, hint


def _estimated_part_dimensions(row, owner_parts, object_parts, envelope):
    """Use a corroborated same-role dimension, then the block span for a linear run."""
    result = dict(row["dimensions"])
    for axis in ("length", "width"):
        if axis not in result or _positive(result[axis].get("mm")):
            continue
        for peers in (owner_parts, object_parts):
            values = [other["dimensions"].get(axis, {}) for other in peers if other["role"] == row["role"]]
            values = [value for value in values if _positive(value.get("mm"))]
            if values and len({value["mm"] for value in values}) == 1:
                result[axis] = {**values[0], "basis": "construction_assumption",
                                "reason": "Estimated from a matching part in the same object."}
                break
        if axis == "length" and "width" not in result and not _positive(result[axis].get("mm")):
            span = envelope.get("width", {})
            if _positive(span.get("mm")):
                result[axis] = {**span, "basis": "construction_assumption",
                                "reason": "Estimated one linear run along its owning block."}
    return result


def _physical_unit(row, role, measurements):
    unit = str(row.get("unit") or "").strip().lower()
    if unit == "ea":
        unit = "piece"
    if role in _COUNT_ROLES or unit in {"ea", "piece", "pair", "set"}:
        return unit or "piece"
    if _positive(measurements.get("length", {}).get("mm")) and "width" not in measurements:
        return "m"
    return None


def _worktop_requirements(row, part_source, object_quantity, families, materials, review_items, family_alias_context):
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
    stock_family, stock_spec, stock_notes, stock_refs = _source_material(row["dimensions"], family_alias_context)
    refs = list(dict.fromkeys([*part_source["evidence_refs"], *outline["source_refs"],
                               *outline.get("seam_source_refs", ()), *([finish_view] if finish_view else [])]))
    part_id = part_source["part_id"]
    for surface in surfaces:
        main = surface["material_role"] == "main_worktop"
        explicit = main and stock_family in families
        default_family = _WORKTOP_DEFAULT_FAMILY if main else _LDSP_FAMILY
        default = outline.get("kitchen_worktop") and default_family in families and (not main or not stock_notes)
        family = stock_family if explicit else default_family if default else None
        surface_thickness = _LDSP_DEFAULT_THICKNESS_MM if default and not main else thickness
        if explicit:
            source_name = " / ".join(stock_notes)
        elif default:
            source_name = "Artificial stone" if main else _MATERIAL_NAMES[_LDSP_FAMILY]
        else:
            source_name = "Main worktop material" if main else "Contrasting finish on beveled end"
        evidence = list(dict.fromkeys([*refs, *stock_refs])) if explicit else refs
        quantity = round(surface["area_m2"] * multiplier, 6)
        key = (part_id, surface["id"])
        materials[key] = {
            "requirement_id": f"cb-material-{len(materials) + 1:03d}",
            "source_name": source_name,
            "family": family, "material_role": "worktop_sheet",
            "specification": {"thickness_mm": surface_thickness, **(stock_spec if explicit else {})},
            "basis": "ocr_material_note" if explicit else "construction_assumption" if default else "material_unresolved",
            "evidence_refs": evidence, "quantity": quantity, "unit": "m2",
            "area_basis": outline["area_basis"],
            "part_sources": [{**part_source, "surface": surface, "evidence_refs": evidence}],
        }
        if not family:
            review_items.append({"part_id": part_id, "surface_id": surface["id"],
                                 "reason": "worktop_material_family_unresolved",
                                 "area_m2": quantity})
    return True


def _worktop_cutout_requirements(row, part_source, object_quantity, materials):
    count = row["quantity"]
    if not _positive(count) or int(count) != count:
        return
    part_id = part_source["part_id"]
    quantity = ceil(count * part_source["scope_quantity"] * object_quantity)
    surface_families = {item["part_sources"][0]["surface"]["material_role"]: item["family"]
                        for key, item in materials.items() if len(key) == 2 and key[0] == part_id}
    for cutout in row.get("worktop_cutouts", ()):
        key = part_id, cutout["id"], "operation_service"
        if key in materials:
            continue
        family = surface_families.get(cutout["surface"])
        if cutout["surface"] == "unknown" and len(surface_families) == 1:
            family = next(iter(surface_families.values()))
        refs = [cutout["view_id"], cutout["id"]]
        requirement_id = f"cb-material-{len(materials) + 1:03d}"
        materials[key] = {
            "requirement_id": requirement_id, "source_name": "Worktop cutout", "family": None,
            "material_role": "worktop_cutout", "item_kind": "operation_service",
            "operation_code": "stone_cutout" if family in _STONE_CUTOUT_FAMILIES else None,
            "specification": {"worktop_family": family},
            "basis": "source_evidence", "evidence_refs": refs, "quantity": quantity, "unit": "piece",
            "part_sources": [{**part_source, "cutout": cutout, "evidence_refs": refs}],
        }


def build_cb_material_demand(*, parts_report, input_row, allowed_material_families, catalog_names=(),
                             family_alias_context=None):
    """Emit a requirement for every identified part, retaining provisional evidence."""
    family_alias_context = family_alias_context or {}
    payload = input_row["input_payload"]
    obj = payload["object"]
    object_id = obj["object_id"]
    object_quantity = obj["quantity"]
    stage = parts_report["stage"]
    if stage not in {"CB Parts", "Parts Check"} or not _positive(object_quantity):
        raise ValueError("Parts demand requires an immutable object input with a positive quantity")
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
    object_parts = [row for _, scope in scopes for row in scope["parts"]]
    envelopes = {block.get("id", block.get("block_id")): block.get("envelope", {})
                 for block in source.get("blocks", ())}
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
            measurements = _estimated_part_dimensions(
                row, scope["parts"], object_parts, envelopes.get(row.get("block_id") or scope_id, {}),
            )
            refs = list(dict.fromkeys(ref for value in measurements.values() for ref in value.get("refs", ())))
            refs = list(dict.fromkeys([*refs, *row.get("count_refs", ()),
                                       *([row["instance_ref"]] if row.get("instance_ref") else [])]))
            part_source = {**row, "part_id": part_id, "scope_id": scope_id,
                           "scope_quantity": multiplier, "evidence_refs": refs}
            duplicate = (row["role"], row.get("instance_ref")) in duplicate_refs
            if duplicate:
                review_items.append({"part_id": part_id, "role": row["role"], "reason": "duplicate_part_evidence",
                                     "part_source": part_source})
                continue
            if row["role"] == "shared_worktop":
                area_resolved = _worktop_requirements(
                    row, part_source, object_quantity, allowed_material_families, materials, review_items,
                    family_alias_context)
                _worktop_cutout_requirements(row, part_source, object_quantity, materials)
                if area_resolved:
                    continue
            unit = _physical_unit(row, role, measurements)
            has_sheet_geometry = not unit and all(_positive(measurements.get(axis, {}).get("mm"))
                                                  for axis in ("length", "width"))
            source_family, material_spec, notes, material_refs = _source_material(
                measurements, family_alias_context, row.get("material_note"))
            if material_refs and row.get("material_note"):
                material_refs = tuple(dict.fromkeys([*material_refs, *measurements.get("thickness", {}).get("refs", ())]))
            preferences = (source_family,) if source_family else _ROLE_FAMILY_PREFERENCE.get(role, ())
            visual_stock = row.get("visual_stock", {})
            visible_veneer = (not notes and not unit and visual_stock.get("surface") == "wood_grain"
                              and "mdf_hdf" in allowed_material_families)
            if visible_veneer:
                preferences = ("mdf_hdf",)
            family = next((f for f in preferences if f in allowed_material_families), None)
            identity_hint = None
            if row["role"] == "led_strip_run" and _LED_FAMILY in allowed_material_families:
                family, identity_hint = _LED_FAMILY, _STANDARD_LED_STRIP
            elif not role and not source_family:
                family, identity_hint = _part_material_identity(row.get("material_hint") or row["role"],
                                                               family, catalog_names)
                if not family and (alias_family := _stock_alias_family(identity_hint, family_alias_context)):
                    family = alias_family
                    if family == "gypsum_board":
                        identity_hint = None
            thickness_mm = measurements.get("thickness", {}).get("mm")
            if role == "visible_sheet" and family == _LDSP_FAMILY and not notes and not _positive(thickness_mm):
                thickness_mm = _LDSP_DEFAULT_THICKNESS_MM
            count = row["quantity"]
            missing = [axis for axis, value in measurements.items() if not _positive(value.get("mm"))]
            fallback_reason = None
            if row["role"] == "shared_worktop":
                fallback_reason = "worktop_cut_geometry_unresolved"
            elif notes and not source_family:
                fallback_reason = "material_note_unresolved"
            elif not family:
                fallback_reason = "material_family_unavailable"
            elif not unit and not has_sheet_geometry:
                fallback_reason = "dimensions_unresolved"
            reason = fallback_reason or ("dimensions_unresolved" if missing else
                                         "quantity_unresolved" if count is None else None)
            if reason:
                review_items.append({"part_id": part_id, "role": row["role"], "missing_dimensions": missing,
                                     "reason": reason, "part_source": part_source})
            if count is None:
                count = 1
                assumptions.append(f"{part_id}: one unit estimated for the identified part.")
                if role == "drawer_slide" and unit == "piece":
                    unit = "set"
            if not _positive(count) or int(count) != count:
                raise ValueError(f"Invalid part quantity for {part_id}")
            quantity = ceil(count * multiplier * object_quantity)
            unit = unit or (None if has_sheet_geometry else "piece")
            spec = dict(material_spec)
            if _positive(thickness_mm) and not unit:
                spec["thickness_mm"] = thickness_mm
            basis = "source_evidence" if material_refs else "construction_assumption"
            name = notes[0] if notes else identity_hint or _MATERIAL_NAMES.get(family, row.get("material_hint") or row["role"])
            if family == "mdf_hdf" and not material_refs and role in {"carcass_sheet", "backing_sheet", "internal_sheet"}:
                spec.update(board_type="hdf" if role == "backing_sheet" else "mdf", surface="raw")
                if role == "backing_sheet":
                    name = "HDF"
            if visible_veneer:
                name = "Veneered MDF"
                spec.update(board_type="mdf", surface="veneer_two_sided")
            if role == "drawer_slide":
                if unit == "set":
                    quantity *= 2
                elif unit != "piece" or int(count * multiplier) % 2:
                    raise ValueError("Drawer slide pieces must form complete sets")
                else:
                    quantity = 2 * ceil(count * multiplier * object_quantity / 2)
                unit = "piece"
                length = measurements.get("length", {})
                if _positive(length.get("mm")):
                    spec["depth_mm"] = length["mm"]
            variant = row.get("colour_temperature_k") if unit == "m" else None
            demand_role = "visible_sheet" if visible_veneer else role
            key = (demand_role, family, name, basis, unit, tuple(sorted(spec.items())), fallback_reason, variant)
            if key not in materials:
                materials[key] = {
                    "requirement_id": f"cb-material-{len(materials) + 1:03d}",
                    "source_name": name, "family": family, "material_role": demand_role,
                    "specification": spec, "basis": basis, "evidence_refs": [],
                    "quantity": 0 if unit else None, "unit": unit, "part_sources": [],
                }
                if fallback_reason:
                    materials[key]["assumption_reason"] = fallback_reason
                if identity_hint:
                    materials[key]["identity_hint"] = identity_hint
                if variant:
                    materials[key]["purchase_variant"] = f"{variant}K"
            material = materials[key]
            material["evidence_refs"] = list(dict.fromkeys([
                *material["evidence_refs"], *material_refs, *(visual_stock.get("refs", ()) if visible_veneer else ()),
            ]))
            material["part_sources"].append({**part_source, "quantity": quantity, "unit": unit,
                                             "source_quantity": row["quantity"], "source_unit": row.get("unit"),
                                             "measurements": measurements})
            if unit:
                material["quantity"] += quantity * measurements["length"]["mm"] / 1000 if unit == "m" else quantity
            else:
                parts.append({
                    "part_id": part_id, "assembly_id": scope_id, "component_role": row["role"],
                    "material_requirement_id": material["requirement_id"], "quantity": quantity,
                    "length_mm": measurements["length"]["mm"], "width_mm": measurements["width"]["mm"],
                    "rotation_allowed": demand_role not in {"visible_sheet", "worktop_sheet"},
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


def build_cb_material_facts(*, parts_report, input_rows, catalog_context):
    """Bind the checked document to the same immutable inputs and catalog tenant."""
    facts = {}
    run_ids = set()
    allowed = set(catalog_context["families"])
    catalog_names = [(position.get("family_code"), set(normalize_material_phrase(position.get("canonical_name")).split()))
                     for position in catalog_context["catalogs"].get("reference_positions", ())
                     if position.get("family_code") in allowed]
    for row in input_rows:
        item = build_cb_material_demand(parts_report=parts_report, input_row=row, allowed_material_families=allowed,
                                       catalog_names=catalog_names,
                                       family_alias_context=catalog_context.get("family_alias_context"))
        if item["company_id"] != catalog_context["company_id"] or item["object_id"] in facts:
            raise ValueError("Parts costing requires matching catalog tenant and unique object inputs")
        facts[item["object_id"]] = item
        run_ids.add(item["run_id"])
    if len(run_ids) != 1 or facts.keys() != parts_report["objects"].keys():
        raise ValueError("Parts costing requires every immutable input from the same run")
    if "input_ids" in parts_report and sorted(parts_report["input_ids"]) != sorted(item["input_id"] for item in facts.values()):
        raise ValueError("Parts Check input revisions differ from the material demand inputs")
    return facts


def _checked_parts_for_estimate(rows, estimated, estimated_counts):
    owner_counts = {}
    parts = []
    for row in rows:
        owner = row["owner_id"]
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        part_id = f"{owner}:{row['role']}:{owner_counts[owner]:03d}"
        estimates = estimated.get(part_id, {})
        dimensions = {**row["dimensions"], **estimates}
        parts.append({"component_role": row["role"], "quantity": estimated_counts.get(part_id, row.get("quantity")),
                      **{f"{axis}_mm": dimensions.get(axis, {}).get("mm")
                         for axis in ("length", "width", "thickness")},
                      **({"quantity_basis": "construction_assumption"} if part_id in estimated_counts else {}),
                      **({"estimated_dimensions": estimates} if estimates else {})})
    return parts


def calculate_cb_materials(*, parts_report, input_rows, catalog_context,
                           material_norm_overrides=None, material_purchase_overrides=None):
    """Calculate one document through the existing estimate-wide Material Plan."""
    facts = build_cb_material_facts(parts_report=parts_report, input_rows=input_rows, catalog_context=catalog_context)
    catalogs = catalog_context["catalogs"]
    fingerprint = material_plan_input_fingerprint(
        facts_by_object=facts, material_default_variants=catalogs.get("material_default_variants") or (),
        material_norm_overrides=material_norm_overrides, material_purchase_overrides=material_purchase_overrides,
    )
    result = build_material_plan(
        facts_by_object=facts, catalogs=catalogs, material_norm_overrides=material_norm_overrides,
        material_purchase_overrides=material_purchase_overrides,
    )
    snapshot = material_plan_snapshot(result, input_fingerprint=fingerprint)
    allocations = {(row["object_id"], row["material_requirement_id"]) for row in snapshot["object_material_costs"]}
    unresolved = set(snapshot["unresolved_requirement_ids"])
    fallback_objects = {row["object_id"] for row in snapshot["assumption_fallbacks"] if row.get("assumption_price")}
    defaults = {(row["object_id"], row["material_requirement_id"]): row["applied_specifications"]
                for row in snapshot["applied_material_defaults"] if row.get("applied_specifications")}
    coverage = {}
    for oid, item in facts.items():
        missing = [material["requirement_id"] for material in item["materials"]
                   if (oid, material["requirement_id"]) not in allocations]
        issues = item["review_items"]
        checked_parts = parts_report["objects"][oid].get("parts", ()) if parts_report["stage"] == "Parts Check" else ()
        estimates = {}
        estimated_counts = {}
        for material in item["materials"]:
            stock_default = defaults.get((oid, material["requirement_id"]), {})
            for source in material["part_sources"]:
                dimensions = source.get("measurements", source["dimensions"])
                original = source["dimensions"]
                updated = {axis: value for axis, value in dimensions.items()
                           if _positive(value.get("mm")) and not _positive(original.get(axis, {}).get("mm"))}
                thickness = stock_default.get("thickness_mm", stock_default.get("thickness"))
                if _positive(thickness) and not _positive(original.get("thickness", {}).get("mm")):
                    updated["thickness"] = {"mm": thickness, "basis": "israel_reference_default",
                                             "reason": "Approved catalog default for the missing thickness."}
                if updated:
                    estimates[source["part_id"]] = updated
                if "source_quantity" in source and source["source_quantity"] is None:
                    estimated_counts[source["part_id"]] = 1
        coverage[oid] = {"source_part_count": item["source_part_count"], "issues": issues,
                         "unpriced_requirements": missing,
                         "has_estimated_costs": oid in fallback_objects or bool(estimates or estimated_counts),
                         "has_unresolved_demands": any(value.startswith(f"{oid}:") for value in unresolved),
                         "materials": [{key: material.get(key) for key in ("requirement_id", "source_name", "unit", "quantity")}
                                       for material in item["materials"]],
                         "parts": _checked_parts_for_estimate(checked_parts, estimates, estimated_counts),
                         "primary_preview_ref": item["primary_preview_ref"]}
    snapshot["parts_check"] = coverage
    snapshot["parts_check_source"] = {key: parts_report[key] for key in ("run_id", "estimate_id", "input_ids", "source_audit_sha256")
                                      if key in parts_report}
    if any(row["issues"] or row["unpriced_requirements"] or row["has_unresolved_demands"]
           or row["has_estimated_costs"] for row in coverage.values()):
        snapshot["status"] = "needs_review"
        snapshot["reason_codes"].append("cb_parts_review_required")
    return {"composition_version": "cb_parts_material_demand_v1", "facts_by_object": facts,
            "material_plan": snapshot}
