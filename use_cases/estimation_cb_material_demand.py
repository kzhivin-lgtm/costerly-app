"""Adapt preliminary CB Parts to the existing assembly BOM material contract."""

from math import isfinite

from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1
from use_cases.estimation_structural_bom import _CONSTRUCTION_MATERIAL_NAMES, _FAMILY_PREFERENCE
from use_cases.material_engine_adapter import build_material_plan, material_plan_input_fingerprint, material_plan_snapshot


_ROLES = {
    **dict.fromkeys(("carcass_side", "carcass_top", "carcass_bottom", "drawer_bay_divider"), "carcass_sheet"),
    **dict.fromkeys(("carcass_back", "drawer_box_bottom"), "backing_sheet"),
    **dict.fromkeys(("drawer_box_side", "drawer_box_end"), "internal_sheet"),
    **dict.fromkeys(("drawer_front", "door_front", "lift_up_front", "fixed_panel", "seat_cover", "frame_backing",
                    "frame_cap", "frame_side", "vertical_rib", "plinth_front", "plinth_return",
                    "plinth_visible_run"), "visible_sheet"),
    **dict.fromkeys(("tabletop", "shared_worktop"), "worktop_sheet"),
    "tabletop_underlayer": "internal_sheet",
    "support_leg": "leg", "drawer_slide": "drawer_slide", "hinge": "hinge", "gas_lift": "gas_lift",
}
_COUNT_ROLES = {"leg", "drawer_slide", "hinge", "gas_lift"}


def _positive(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def build_cb_material_demand(*, parts_report, input_row, allowed_material_families):
    """Build one object's demand. Geometry gaps remain outside the priced basket."""
    payload = input_row["input_payload"]
    obj = payload["object"]
    object_id = obj["object_id"]
    object_quantity = obj["quantity"]
    if parts_report["stage"] != "CB Parts" or not _positive(object_quantity) or int(object_quantity) != object_quantity:
        raise ValueError("CB Parts requires an immutable object input with a whole positive quantity")
    source = parts_report["objects"][object_id]
    scopes = [(row["block_id"], row) for row in source["blocks"]] + [
        (row["id"], row) for row in source["shared_parts"]
    ]
    if len(scopes) != len({key for key, _ in scopes}):
        raise ValueError("Block and shared part IDs must be unique within the object")
    materials, parts, review_items, assumptions = {}, [], [], []
    inventory_issues = source.get("inventory_review_items", ())
    duplicate_refs = {(issue["role"], issue["source_ref"]) for issue in inventory_issues
                      if issue["reason"] == "duplicate_part_evidence"}
    for scope_id, scope in scopes:
        assumptions.extend(f"{scope_id}: {note}" for note in scope.get("review", ()))
        if not scope["parts"]:
            review_items.append({"part_id": scope_id, "reason": "construction_unresolved"})
        multiplier = scope.get("quantity", 1)
        if not _positive(multiplier) or int(multiplier) != multiplier:
            raise ValueError(f"Invalid scope quantity for {scope_id}")
        for index, row in enumerate(scope["parts"], start=1):
            part_id = f"{scope_id}:{row['role']}:{index:03d}"
            if (row["role"], row.get("instance_ref")) in duplicate_refs:
                continue
            role = _ROLES.get(row["role"])
            measurements = row["dimensions"]
            is_count = role in _COUNT_ROLES
            required = () if is_count else ("length", "width", "thickness")
            missing = [field for field in required if not _positive(measurements.get(field, {}).get("mm"))]
            # The hardboard pricing key currently also matches insulation board.
            # Use an explicit HDF backing allowance in this preliminary route.
            preferences = ("mdf_hdf",) if role == "backing_sheet" else _FAMILY_PREFERENCE.get(role, ())
            family = next((f for f in preferences if f in allowed_material_families), None)
            if missing or not family:
                review_items.append({"part_id": part_id, "role": row["role"], "missing_dimensions": missing,
                                     "reason": "dimensions_unresolved" if missing and role else "unsupported_material_role"})
                continue
            count = row["quantity"]
            if count is None:
                review_items.append({"part_id": part_id, "role": row["role"], "reason": "quantity_unresolved"})
                continue
            if not _positive(count) or int(count) != count:
                raise ValueError(f"Invalid part quantity for {part_id}")
            quantity = int(count * multiplier * object_quantity)
            unit = row.get("unit", "piece") if is_count else None
            spec = {} if is_count else {"thickness_mm": measurements["thickness"]["mm"]}
            name = _CONSTRUCTION_MATERIAL_NAMES[family]
            if family == "mdf_hdf" and role in {"carcass_sheet", "backing_sheet", "internal_sheet"}:
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
            key = (role, family, unit, tuple(sorted(spec.items())))
            if key not in materials:
                materials[key] = {
                    "requirement_id": f"cb-material-{len(materials) + 1:03d}",
                    "source_name": name, "family": family, "material_role": role,
                    "specification": spec, "basis": "construction_assumption", "evidence_refs": [],
                    "quantity": 0 if is_count else None, "unit": unit, "part_sources": [],
                }
            material = materials[key]
            refs = list(dict.fromkeys(ref for value in measurements.values() for ref in value.get("refs", ())))
            if row.get("instance_ref"):
                refs.append(row["instance_ref"])
            material["part_sources"].append({"part_id": part_id, "quantity": quantity, "unit": unit,
                                             "measurements": measurements, "evidence_refs": refs})
            if is_count:
                material["quantity"] += quantity
            else:
                parts.append({
                    "part_id": part_id, "assembly_id": scope_id, "component_role": row["role"],
                    "material_requirement_id": material["requirement_id"], "quantity": quantity,
                    "length_mm": measurements["length"]["mm"], "width_mm": measurements["width"]["mm"],
                    "rotation_allowed": role not in {"visible_sheet", "worktop_sheet"},
                    "basis": "construction_assumption", "evidence_refs": refs,
                    "assumption_reason": "Preliminary part geometry and stock family require confirmation.",
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
    fingerprint = material_plan_input_fingerprint(
        facts_by_object=facts, material_default_variants=catalogs.get("material_default_variants") or (),
    )
    snapshot = material_plan_snapshot(build_material_plan(facts_by_object=facts, catalogs=catalogs),
                                      input_fingerprint=fingerprint)
    gaps = {oid: item["review_items"] for oid, item in facts.items() if item["review_items"]}
    if gaps:
        snapshot["status"] = "needs_review"
        snapshot["cb_parts_review_items"] = gaps
        snapshot["reason_codes"].append("cb_parts_review_required")
    return {"composition_version": "cb_parts_material_demand_v1", "facts_by_object": facts,
            "material_plan": snapshot}
