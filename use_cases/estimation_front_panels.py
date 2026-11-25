"""Front purpose and estimate-local stock choices for existing physical parts."""

FRONT_PART_ROLES = frozenset({
    "facade", "door_front", "drawer_front", "lift_up_front", "hinged_facade", "lift_up_facade",
})
FRONT_MATERIALS = {
    "ldsp": ("LDSP", "melamine_faced_particleboard", {}),
    "veneered_mdf": ("MDF Veneered", "mdf_hdf", {"board_type": "mdf", "surface": "veneer_two_sided"}),
    "mdf": ("MDF Raw", "mdf_hdf", {"board_type": "mdf", "surface": "raw"}),
    "plywood": ("Plywood", "plywood", {}),
    "veneered_mdf_oil": ("MDF Veneered", "mdf_hdf", {"board_type": "mdf", "surface": "veneer_two_sided"}),
    "plywood_oil": ("Plywood", "plywood", {}),
}
FRONT_LABELS = {
    "ldsp": "LDSP", "veneered_mdf": "MDF Veneered · Lacquer",
    "veneered_mdf_oil": "MDF Veneered · Oil", "mdf": "MDF Raw · Enamel/Lacquer",
    "plywood": "Plywood · Lacquer", "plywood_oil": "Plywood · Oil",
}


def front_material_base(choice):
    """Finish selection shares the same existing board identity and geometry."""
    return {"veneered_mdf_oil": "veneered_mdf", "plywood_oil": "plywood"}.get(choice, choice)


def front_material_finish(choice):
    if choice in {"veneered_mdf_oil", "plywood_oil"}:
        return "oil"
    return {"mdf": "enamel", "veneered_mdf": "lacquer", "plywood": "lacquer", "ldsp": None}.get(choice)


def front_plan_revision(plan):
    """Bind a server-side draft to the exact persisted plan it was based on."""
    import hashlib
    import json
    return hashlib.sha256(json.dumps(plan, sort_keys=True, default=str).encode()).hexdigest()


def front_material_groups(materials):
    """Identify fronts from saved part roles, including older demand records."""
    groups = []
    for material in materials:
        sources = [part for part in material.get("part_sources", ())
                   if part.get("role") in FRONT_PART_ROLES]
        if not sources or material.get("unit") or not material.get("family"):
            continue
        spec = material.get("specification", {})
        surface = str(spec.get("surface") or "").casefold()
        source_choice = None
        if material["family"] == "melamine_faced_particleboard":
            source_choice = "ldsp"
        elif material["family"] == "mdf_hdf" and "veneer" in surface:
            source_choice = "veneered_mdf"
        elif material["family"] == "mdf_hdf" and spec.get("board_type") != "hdf":
            source_choice = "mdf"
        elif material["family"] in {"plywood", "plywood_special"}:
            source_choice = "plywood"
        groups.append({
            "id": material["requirement_id"], "source_name": material["source_name"],
            "family": material["family"], "specification": dict(spec),
            "part_ids": [source["part_id"] for source in sources],
            "part_sources": sources,
            "mixed": len(sources) != len(material.get("part_sources", ())),
            "thickness_mm": spec.get("thickness_mm"),
            "source_choice": source_choice,
        })
    return groups


def validate_front_choices(groups, choices):
    known = {group["id"] for group in groups}
    if set(choices) - known or any(choice not in {"source", *FRONT_MATERIALS} for choice in choices.values()):
        raise ValueError("This front panel material is no longer available.")
    original = {group["id"]: group.get("source_choice") for group in groups}
    return {group_id: choice for group_id, choice in choices.items()
            if choice != "source" and choice != original[group_id]}


def front_choices_by_part(groups, choices):
    selected = validate_front_choices(groups, choices)
    return {part_id: selected[group["id"]]
            for group in groups if group["id"] in selected for part_id in group["part_ids"]}


def _source_reference_key(material):
    return tuple(sorted((source["part_id"], str(source.get("surface", {}).get("id", "")),
                         str(source.get("cutout", {}).get("id", "")))
                        for source in material.get("part_sources", ())))


def classify_front_materials(base, effective, groups, choices):
    """Keep stable source requirement IDs while separating the front demands."""
    origins = {source["part_id"]: material["requirement_id"]
               for material in base["materials"] if material.get("unit") is None
               for source in material.get("part_sources", ())}
    mixed = {group["id"] for group in groups if group["mixed"]}
    front_ids = {part_id for group in groups for part_id in group["part_ids"]}
    original_ids = {(material.get("material_role"), material.get("unit"), _source_reference_key(material)):
                    material["requirement_id"] for material in base["materials"] if _source_reference_key(material)}
    materials, requirement_by_part = [], {}
    for material in effective["materials"]:
        if material.get("unit") is not None:
            material = dict(material)
            key = material.get("material_role"), material.get("unit"), _source_reference_key(material)
            material["requirement_id"] = original_ids.get(key, material["requirement_id"])
            materials.append(material)
            continue
        partitions = {}
        for source in material.get("part_sources", ()):
            part_id = source["part_id"]
            origin = origins.get(part_id, material["requirement_id"])
            is_front = part_id in front_ids
            requirement = (f"{origin}-{'front' if is_front else 'body'}" if origin in mixed else origin)
            partitions.setdefault(requirement, []).append(source)
            requirement_by_part[part_id] = requirement
        if not partitions:
            materials.append(material)
            continue
        for requirement, sources in partitions.items():
            row = {**material, "requirement_id": requirement, "part_sources": sources}
            if all(source["part_id"] in front_ids for source in sources):
                row["material_class"] = "front_panels"
            materials.append(row)
    for part in effective["parts"]:
        part["material_requirement_id"] = requirement_by_part.get(part["part_id"], part["material_requirement_id"])
        if part["part_id"] in front_ids:
            part["material_class"] = "front_panels"
    if len({material["requirement_id"] for material in materials}) != len(materials):
        raise ValueError("Material requirement identities must remain unique.")
    effective["materials"] = materials
    effective["front_panel_groups"] = [{**group, "choice": choices.get(group["id"], "source"),
        "requirement_ids": sorted({requirement_by_part[part_id] for part_id in group["part_ids"]})}
        for group in groups]
    return effective


def front_panel_controls(plan, lines, object_id):
    """Project the stored selector, or recover source groups from old line facts."""
    groups = (plan.get("front_panel_groups") or {}).get(object_id)
    if groups is None:
        materials = [row.get("raw_agent_json", {}).get("facts", {}) for row in lines
                     if row.get("section") == "material" and isinstance(row.get("raw_agent_json"), dict)]
        groups = front_material_groups(materials)
    choices = (plan.get("front_panel_choices") or {}).get(object_id, {})
    return [{**group, "choice": (choices.get(group["id"], "source") if choices.get(group["id"], "source") != "source"
                                else group.get("source_choice") or "source"),
             "options": [{"value": key, "label": label} for key, label in FRONT_LABELS.items()]}
            for group in groups]


def preserve_front_norms(facts, overrides):
    """Split a legacy mixed-row norm without moving its entire area to the body."""
    result = dict(overrides or {})
    for oid, fact in facts.items():
        material_by_id = {row["requirement_id"]: row for row in fact["materials"]}
        for group in fact.get("front_panel_groups", ()):
            original = (oid, group["id"])
            if not group["mixed"] or original not in result:
                continue
            override = result.pop(original)
            keys = [f"{group['id']}-body", f"{group['id']}-front"]
            weights = []
            for key in keys:
                sources = material_by_id[key]["part_sources"]
                weights.append(sum(
                    (source["measurements"]["length"]["mm"] or 0) * (source["measurements"]["width"]["mm"] or 0)
                    * source["quantity"] for source in sources
                ))
            if not sum(weights):
                raise ValueError("The front panel group has no measurable area.")
            for key, weight in zip(keys, weights, strict=True):
                result.setdefault((oid, key), {**override, "material_requirement_id": key,
                    "quantity_per_item": float(override["quantity_per_item"]) * weight / sum(weights)})
    return result
