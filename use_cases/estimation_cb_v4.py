"""CB Parts V4: physical runs -> workshop groups -> existing parts/BOM builders.

Source ownership is still a model interpretation. Geometry and material claims
remain auditable assumptions; arithmetic consistency is not visual acceptance.
"""
from copy import deepcopy
import math

from use_cases.estimation_cb_bays import _fields, _ids, _list, compose_cb_bay_parts
from use_cases.estimation_cb_parts import positive
from use_cases.estimation_cb_spans import _text, _unit
from use_cases.estimation_assembly_bom import build_assembly_bom, _allowed_refs


def _id(value):
    _text(value, "ID", 80)
    if "." in value:
        raise ValueError("IDs cannot contain dots")
    return value


def _share(total, weights):
    weights = [positive(w, "weight") for w in weights]
    denominator = sum(weights)
    if not weights or not math.isfinite(denominator):
        raise ValueError("finite nonempty weight sum required")
    values = [total * w / denominator for w in weights]
    values[-1] = total - sum(values[:-1])
    if min(values) < 1:
        raise ValueError("estimated interval must be at least 1 mm")
    return values


def compose_cb_v4(raw, *, scope, input_row, dimension_graph, allowed_material_families):
    _fields(raw, "summary materials dimensions runs blocks explicit_assemblies uncertainties", "CB Parts V4")
    _text(raw["summary"], "summary", 1200)
    for field, limit in (("materials", 40), ("dimensions", 300), ("runs", 100),
                         ("blocks", 300), ("explicit_assemblies", 100), ("uncertainties", 100)):
        _list(raw[field], field, 0, limit)
    for note in raw["uncertainties"]:
        _text(note, "uncertainty", 1200)
    # Include the same shared source context consumed by the visual interpreter.
    row = deepcopy(input_row)
    payload = row["input_payload"]
    for kind in ("artifacts", "ocr_blocks", "ocr_literal_items"):
        payload["evidence"].setdefault(kind, []).extend(payload.get("document_context", {}).get(kind, []))
    refs = _allowed_refs(payload)
    known_views = {v["view_id"] for v in scope["front"]["island_types"]}
    material_map = {}
    for m in raw["materials"]:
        _fields(m, "id name family stock_thickness_mm layers finish edge_treatment basis evidence_refs reason", "V4 material")
        mid = _id(m["id"])
        if mid in material_map or m["family"] not in allowed_material_families:
            raise ValueError("duplicate material or unsupported family")
        for k in ("name", "reason"):
            _text(m[k], k, 1200)
        for k in ("finish", "edge_treatment"):
            if not isinstance(m[k], str) or len(m[k]) > 300:
                raise ValueError("bounded finish/edge intent required")
        stock = positive(m["stock_thickness_mm"], "stock thickness")
        layers = positive(m["layers"], "layers", integer=True)
        if stock * layers > 500 or layers > 10:
            raise ValueError("material thickness exceeds coarse bound")
        _list(m["evidence_refs"], "material evidence")
        if any(not isinstance(r, str) or r not in refs for r in m["evidence_refs"]):
            raise ValueError("foreign material evidence")
        if m["basis"] not in {"source_evidence", "construction_assumption"}:
            raise ValueError("invalid material basis")
        if bool(m["evidence_refs"]) != (m["basis"] == "source_evidence"):
            raise ValueError("material source/assumption evidence mismatch")
        material_map[mid] = {"source_name": m["name"], "family": m["family"],
            # References establish traceability, not the truth of a model claim.
            "basis": "construction_assumption", "evidence_refs": [],
            "specification": {"thickness_mm": stock * layers, "stock_thickness_mm": stock,
                "layers": layers, "finish": m["finish"], "edge_treatment": m["edge_treatment"]}}
    measurements, dimensions = {}, {}
    for d in raw["dimensions"]:
        _fields(d, "id value unit basis view_id label reason", "V4 dimension")
        did = _id(d["id"])
        if did in dimensions:
            raise ValueError("duplicate dimension")
        mm = positive(d["value"], "dimension") * _unit(d["unit"])
        if mm > 30000:
            raise ValueError("dimension exceeds furniture bound")
        if d["basis"] not in {"drawing_reading", "assumption"}:
            raise ValueError("invalid dimension basis")
        if d["view_id"] is not None and d["view_id"] not in known_views:
            raise ValueError("unknown dimension view")
        if not isinstance(d["label"], str) or len(d["label"]) > 100:
            raise ValueError("bounded dimension label required")
        if d["basis"] == "drawing_reading" and (not d["label"].strip() or d["view_id"] is None):
            raise ValueError("drawing reading requires view and printed label")
        _text(d["reason"], "dimension reason", 1200)
        dimensions[did] = {**d, "value_mm": mm, "ownership_verified": False}
        measurements[did] = mm
    def measure(ref):
        if not isinstance(ref, str) or ref not in measurements:
            raise ValueError("unknown measurement reference")
        return measurements[ref]
    front_types = {}
    for group in scope["front"]["front_groups"]:
        for f in group["fronts"]:
            if f["id"] in front_types:
                raise ValueError("duplicate upstream front")
            front_types[f["id"]] = group["type"]
    runs, bays, covered = {}, {}, []
    for run in raw["runs"]:
        _fields(run, "id name view_id width_ids height_id depth_id bays", "V4 run")
        rid = _id(run["id"])
        if rid in runs or rid in dimensions or rid in bays or run["view_id"] not in known_views:
            raise ValueError("duplicate run identity or unknown view")
        _text(run["name"], "run name")
        _list(run["width_ids"], "run width dimensions", 1, 30)
        if any(not isinstance(k, str) or k not in dimensions for k in run["width_ids"]):
            raise ValueError("run width must reference independent dimensions")
        if len(set(run["width_ids"])) != len(run["width_ids"]):
            raise ValueError("duplicate width dimension would double count")
        if any(run[k] not in dimensions for k in ("height_id", "depth_id")):
            raise ValueError("run height/depth require dimension IDs")
        width = sum(measure(k) for k in run["width_ids"])
        height, depth = measure(run["height_id"]), measure(run["depth_id"])
        if width > 30000:
            raise ValueError("run width exceeds furniture bound")
        _list(run["bays"], "run bays", 1, 100)
        widths = _share(width, [b.get("width_weight") for b in run["bays"]])
        for bay, bw in zip(run["bays"], widths):
            _fields(bay, "id width_weight shelves opening_weight fronts", "V4 bay")
            qid = _id(bay["id"])
            if qid in bays or qid in dimensions or qid == rid or qid in runs:
                raise ValueError("duplicate bay identity")
            if type(bay["shelves"]) is not int or not 0 <= bay["shelves"] <= 100:
                raise ValueError("bounded shelf count required")
            opening = bay["opening_weight"]
            if type(opening) not in (int, float) or not math.isfinite(opening) or opening < 0:
                raise ValueError("nonnegative finite opening weight required")
            _list(bay["fronts"], "bay fronts", 0, 100)
            for f in bay["fronts"]:
                _fields(f, "id height_weight", "V4 front")
                if not isinstance(f["id"], str) or f["id"] not in front_types:
                    raise ValueError("unknown front")
            weights = [f["height_weight"] for f in bay["fronts"]] + ([opening] if opening else [])
            heights = _share(height, weights)
            resolved_fronts = []
            for f, fh in zip(bay["fronts"], heights):
                resolved_fronts.append({"id": f["id"], "height": fh,
                    "body_height": min(fh * .75, 250) if front_types[f["id"]] == "drawer" else None})
                covered.append(f["id"])
            bays[qid] = {"run_id": rid, "width": bw, "fronts": resolved_fronts,
                "shelves": bay["shelves"], "opening_height_mm": heights[-1] if opening else 0}
            measurements[qid + ".width"] = bw
        runs[rid] = {"width_mm": width, "height_mm": height, "depth_mm": depth,
            "bay_ids": [b["id"] for b in run["bays"]], "width_ids": list(run["width_ids"])}
        measurements.update({rid + "." + k: v for k, v in (("width", width), ("height", height), ("depth", depth))})
    _ids(covered, list(front_types))
    compiled_blocks, plan_blocks, block_defs, allocated = [], [], {}, []
    for block in raw["blocks"]:
        _fields(block, "id name run_id bay_ids body_material_id front_material_id drawer_material_id reason", "V4 block")
        bid = _id(block["id"])
        if bid in block_defs or block["run_id"] not in runs:
            raise ValueError("duplicate block or unknown run")
        _text(block["name"], "block name"); _text(block["reason"], "block reason", 1200)
        for k in ("body_material_id", "front_material_id", "drawer_material_id"):
            if not isinstance(block[k], str) or block[k] not in material_map:
                raise ValueError("unknown block material")
        _list(block["bay_ids"], "block bays", 1, 100)
        run = runs[block["run_id"]]
        if any(not isinstance(q, str) or q not in run["bay_ids"] for q in block["bay_ids"]):
            raise ValueError("block must use bays of one run")
        indices = [run["bay_ids"].index(q) for q in block["bay_ids"]]
        if indices != list(range(indices[0], indices[0] + len(indices))):
            raise ValueError("block bays must be consecutive and ordered")
        allocated.extend(block["bay_ids"])
        block_defs[bid] = block
        selected = [{"id": q, **{k: deepcopy(bays[q][k]) for k in ("width", "fronts", "shelves")}} for q in block["bay_ids"]]
        compiled_blocks.append({"id": bid, "kind": "carcass", "unit": "mm", "height": run["height_mm"],
            "depth": run["depth_mm"], "thickness_mm": 17, "assumptions": block["reason"], "bays": selected})
        plan_blocks.append({"id": bid, "front_ids": [f["id"] for b in selected for f in b["fronts"]]})
    _ids(allocated, list(bays))  # exact once, independent of old Planner groups
    local_scope = {**scope, "planner": {"blocks": plan_blocks, "shared_parts": []}}
    carcasses = compose_cb_bay_parts({"blocks": compiled_blocks}, scope=local_scope) if compiled_blocks else {"blocks": []}
    page_refs = [a["storage_ref"] for a in payload["evidence"]["artifacts"] if a.get("artifact_kind") == "page"]
    assemblies, lineage = [], {}
    def component(aid, cid, name, role, quantity, length, width, mid, reason, dependencies):
        _id(cid); _text(name, "part name"); _text(reason, "part reason", 1200)
        if mid not in material_map or role not in {"panel", "worktop", "support", "side", "partition", "horizontal", "back", "shelf", "facade", "drawer_side", "drawer_end", "drawer_bottom"}:
            raise ValueError("invalid part material/role")
        quantity = positive(quantity, "part quantity", integer=True)
        if quantity > 10000 or max(length, width) > 30000:
            raise ValueError("part exceeds coarse bounds")
        lineage[aid + ":" + cid] = {"name": name, "palette_material_id": mid,
            "dimension_dependencies": dependencies, "thickness_mm": material_map[mid]["specification"]["thickness_mm"]}
        return {"component_id": cid, "component_role": role, "quantity": quantity,
            "length_value": length, "width_value": width, "dimension_unit": "mm",
            "dimension_unit_basis": "explicit_source", "geometry_basis": "assumption",
            "geometry_evidence_refs": [], "assumption_reason": reason, "material": material_map[mid]}
    for b in carcasses["blocks"]:
        definition = block_defs[b["id"]]
        rows = []
        for index, part in enumerate(b["parts"], 1):
            name = part["name"]
            role = {"Carcass side wall": "side", "Carcass top": "horizontal", "Carcass bottom": "horizontal",
                "Back panel": "back", "Shared mounting partition": "partition", "Shelf": "shelf",
                "Hinged door": "facade", "Lift-up front": "facade", "Drawer front": "facade",
                "Drawer body side": "drawer_side", "Drawer body end panel": "drawer_end", "Drawer bottom": "drawer_bottom"}[name]
            material_key = "drawer_material_id" if name.startswith("Drawer body") or name == "Drawer bottom" else (
                "front_material_id" if name in {"Hinged door", "Lift-up front", "Drawer front"} else "body_material_id")
            rows.append(component(b["id"], f"P{index:03d}", name, role, part["quantity"], *part["size_mm"][:2],
                definition[material_key], definition["reason"], {"run_id": definition["run_id"], "bay_ids": definition["bay_ids"]}))
        assemblies.append({"assembly_id": b["id"], "evidence_refs": page_refs, "components": rows})
    seen = set(block_defs)
    for assembly in raw["explicit_assemblies"]:
        _fields(assembly, "id name parts", "explicit assembly")
        aid = _id(assembly["id"])
        if aid in seen:
            raise ValueError("duplicate assembly")
        seen.add(aid); _text(assembly["name"], "assembly name")
        _list(assembly["parts"], "explicit parts", 1, 100)
        rows = []
        for p in assembly["parts"]:
            _fields(p, "id name role quantity length_ref width_ref material_id reason", "explicit part")
            if p["role"] not in {"panel", "worktop", "support"}:
                raise ValueError("invalid explicit part role")
            rows.append(component(aid, p["id"], p["name"], p["role"], p["quantity"],
                measure(p["length_ref"]), measure(p["width_ref"]), p["material_id"], p["reason"],
                {"length_ref": p["length_ref"], "width_ref": p["width_ref"]}))
        assemblies.append({"assembly_id": aid, "evidence_refs": page_refs, "components": rows})
    bom = build_assembly_bom(input_row=row, dimension_graph=dimension_graph,
        extraction={"assemblies": assemblies, "omissions": []}, allowed_material_families=allowed_material_families)
    for p in bom["parts"]:
        p.update(lineage[p["part_id"]])
    used = {p["palette_material_id"] for p in bom["parts"]}
    if used != set(material_map):
        raise ValueError("palette must contain only used materials")
    totals = []
    for mid in sorted(used):
        parts = [p for p in bom["parts"] if p["palette_material_id"] == mid and p["component_role"] != "support"]
        area = sum(p["quantity"] * p["length_mm"] * p["width_mm"] / 1e6 for p in parts)
        totals.append({"palette_material_id": mid, "finished_area_m2": area,
            "stock_area_m2": area * material_map[mid]["specification"]["layers"], "basis": "net_rectangular_parts_no_waste_or_nesting"})
    bom.update(status="cb_parts_v4_requires_review", prompt_version="CB Parts V4", summary=raw["summary"],
        geometry_scheme={"dimensions": dimensions, "runs": runs, "bays": bays},
        resolved_blocks=carcasses["blocks"], material_interpretations=deepcopy(raw["materials"]),
        material_area_per_object=totals, uncertainties=list(raw["uncertainties"]),
        upstream_status=deepcopy(scope.get("upstream_status", {})),
        limitations=["Source dimension ownership and material interpretation remain unverified.",
            "Front IDs/types inherited from saved fallible Analyze reference.",
            "Full top/bottom/back, drawer body height policy and partitions are coarse construction assumptions.",
            "Finishes and edge treatments are retained intent; their separate purchasing demand is not compiled."])
    return bom
