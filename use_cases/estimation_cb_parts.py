"""CB Parts V1: bounded coarse parts, no model calls or catalog decisions."""
from __future__ import annotations

import ast
from copy import deepcopy
import math
import operator

from use_cases.estimation_2vn_resolver import resolve_2vn_geometry
from use_cases.estimation_assembly_bom import build_assembly_bom
from use_cases.estimation_structural_bom import _slide_depth_mm

VERSION = "CB Parts V1"
DEFAULT_MATERIAL = dict(id="M0", name="LDSP", family="ldsp", thickness_mm=17,
    stock_thickness_mm=17, layers=1, basis="construction_assumption",
    evidence_refs=[], reason="Owner-approved LDSP 17 mm fallback, absent contrary evidence.")
ROLES = {"side", "partition", "horizontal", "back", "facade", "drawer_box", "worktop", "panel", "support"}


def validate_cb_part_counts(response, *, scope):
    """V2 validates only shape/coverage, not visual or construction correctness.

    No dimensions, material defaults, 2VN, drawer expansion or repairs here.
    The model's exact part names and quantities remain visible to the reviewer.
    """
    if not isinstance(response, dict) or set(response) != {"blocks"}:
        raise ValueError("CB Parts V2 returns only blocks")
    blocks = response["blocks"]
    plan = scope["planner"]
    expected = {b["id"] for b in plan["blocks"] + plan["shared_parts"]}
    if not isinstance(blocks, list) or len(blocks) != len(expected):
        raise ValueError("CB Parts V2 requires every planned block once")
    seen = set()
    for block in blocks:
        if not isinstance(block, dict) or set(block) != {"id", "parts"}:
            raise ValueError("CB Parts V2 block requires only id and parts")
        bid = block["id"]
        if not isinstance(bid, str) or bid not in expected or bid in seen:
            raise ValueError("CB Parts V2 duplicate or foreign block")
        seen.add(bid)
        if not isinstance(block["parts"], list) or not 1 <= len(block["parts"]) <= 100:
            raise ValueError("CB Parts V2 bounded nonempty parts required")
        names = set()
        for part in block["parts"]:
            if not isinstance(part, dict) or set(part) != {"name", "quantity"}:
                raise ValueError("CB Parts V2 part requires only name and quantity")
            name = part["name"]
            if not isinstance(name, str) or not name.strip() or len(name) > 160 or name.strip().casefold() in names:
                raise ValueError("CB Parts V2 unique short part name required")
            names.add(name.strip().casefold())
            if type(part["quantity"]) is not int or part["quantity"] <= 0:
                raise ValueError("CB Parts V2 positive integer quantity required")
    return response


def positive(value, field, *, integer=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0 or (integer and int(value) != value):
        raise ValueError(f"{field} must be finite and positive" + (" integer" if integer else ""))
    return int(value) if integer else float(value)


def compose_cb_sized_parts(response, *, scope):
    """V3 unit/default arithmetic only; never repair model geometry or counts."""
    if not isinstance(response, dict) or set(response) != {"blocks"}:
        raise ValueError("CB Parts V3 returns only blocks")
    expected = {b["id"] for b in scope["planner"]["blocks"] + scope["planner"]["shared_parts"]}
    blocks = response["blocks"]
    if not isinstance(blocks, list) or len(blocks) != len(expected):
        raise ValueError("CB Parts V3 requires every planned block once")
    seen = set()
    result = []
    for block in blocks:
        if not isinstance(block, dict) or set(block) != {"id", "unit", "size", "assumptions", "parts"}:
            raise ValueError("invalid CB Parts V3 block fields")
        bid = block["id"]
        if not isinstance(bid, str) or bid not in expected or bid in seen:
            raise ValueError("duplicate or foreign block")
        seen.add(bid)
        if not isinstance(block["unit"], str) or block["unit"] not in {"mm", "cm", "m"}:
            raise ValueError("explicit block unit required")
        factor = {"mm": 1, "cm": 10, "m": 1000}[block["unit"]]
        if not isinstance(block["size"], list) or len(block["size"]) != 3:
            raise ValueError("three block dimensions required")
        axes = [positive(v, "block size") * factor for v in block["size"]]
        if max(axes) > 30000:
            raise ValueError("block exceeds coarse furniture size bound")
        if not isinstance(block["assumptions"], str) or len(block["assumptions"]) > 1200:
            raise ValueError("bounded assumptions required")
        if not isinstance(block["parts"], list) or not 1 <= len(block["parts"]) <= 100:
            raise ValueError("bounded nonempty parts required")
        rows, keys = [], set()
        for part in block["parts"]:
            if not isinstance(part, dict) or set(part) != {"name", "quantity", "role", "size", "thickness_mm", "approximate"}:
                raise ValueError("invalid sized part fields")
            if not isinstance(part["name"], str) or not part["name"].strip() or len(part["name"]) > 160:
                raise ValueError("short part name required")
            if type(part["quantity"]) is not int or not 1 <= part["quantity"] <= 10000:
                raise ValueError("positive bounded integer quantity required")
            if part["role"] not in ("panel", "worktop", "support") or type(part["approximate"]) is not bool:
                raise ValueError("valid role and approximation flag required")
            if not isinstance(part["size"], list) or len(part["size"]) != 2:
                raise ValueError("two part face dimensions required")
            face = []
            derived = False
            for value in part["size"]:
                if value == "drawer_depth":
                    if part["role"] != "panel" or "drawer" not in part["name"].casefold():
                        raise ValueError("drawer_depth requires a drawer panel")
                    face.append(_slide_depth_mm(axes[2]))
                    derived = True
                else:
                    face.append(round(positive(value, "part size") * factor, 3))
            if max(face) > max(axes) * 1.2:
                raise ValueError("part face exceeds block envelope")
            default = part["thickness_mm"] is None
            thickness = (30 if part["role"] == "worktop" else 17) if default else positive(part["thickness_mm"], "thickness")
            if thickness > 500:
                raise ValueError("thickness exceeds coarse part bound")
            key = (part["name"].strip().casefold(), *face, thickness)
            if key in keys:
                raise ValueError("identical parts must be grouped")
            keys.add(key)
            rows.append({"name": part["name"], "quantity": part["quantity"], "role": part["role"],
                "size_mm": [*face, thickness], "approximate": part["approximate"] or default or derived,
                "thickness_basis": "default" if default else "model_returned_unverified",
                "drawer_depth_derived": derived})
        result.append({"id": bid, "size_mm": axes, "assumptions": block["assumptions"], "parts": rows})
    return {"blocks": result}


def face_size(expression, axes):
    """Small arithmetic grammar, never eval; return value and axis dependencies."""
    if not isinstance(expression, str) or not 0 < len(expression) <= 120:
        raise ValueError("bounded size expression required")
    try:
        tree = ast.parse(expression, mode="eval")
        if len(list(ast.walk(tree))) > 40:
            raise ValueError("size expression too complex")
        names = set()
        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return node.value
            if isinstance(node, ast.Name) and node.id in axes:
                names.add(node.id)
                return axes[node.id]
            if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div):
                return {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}[type(node.op)](visit(node.left), visit(node.right))
            raise ValueError("unsupported size expression")
        value = positive(visit(tree.body), "part face")
        return round(value, 3), names
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError("invalid size expression") from exc


def compose_cb_parts(*, response, input_row, dimension_graph, scope, allowed_material_families):
    """Preserve raw response separately; expose provenance/2VN and input defects."""
    raw = deepcopy(response)
    if not isinstance(raw, dict) or set(raw) != {"document_unit", "materials", "view_interpretations", "dimension_bindings", "blocks", "conflicts", "omissions"}:
        raise ValueError("invalid CB Parts fields")
    for key in ("materials", "view_interpretations", "dimension_bindings", "blocks", "conflicts", "omissions"):
        if not isinstance(raw[key], list) or len(raw[key]) > 300:
            raise ValueError(f"bounded {key} list required")
    payload = input_row["input_payload"]
    refs = {x.get("storage_ref") or x.get("block_ref") for container in ("evidence", "document_context")
        for kind in ("artifacts", "ocr_blocks", "ocr_literal_items")
        for x in payload.get(container, {}).get(kind, [])}
    refs.discard(None)
    def citations(values):
        if not isinstance(values, list) or any(not isinstance(x, str) or x not in refs for x in values):
            raise ValueError("foreign evidence reference")
        return values
    def text(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 1200:
            raise ValueError("short explanatory text required")
    for key in ("conflicts", "omissions"):
        for value in raw[key]:
            text(value)
    unit = raw["document_unit"]
    if not isinstance(unit, dict) or unit.get("unit") not in {"mm", "cm", "m"} or unit.get("basis") not in {"explicit_source", "document_convention_assumption"}:
        raise ValueError("invalid document unit")
    citations(unit.get("evidence_refs"))
    if unit["basis"] == "document_convention_assumption":
        text(unit.get("assumption_reason"))
    materials = {"M0": deepcopy(DEFAULT_MATERIAL)}
    for material in raw["materials"]:
        if not isinstance(material, dict) or not isinstance(material.get("id"), str) or not material["id"] or material["id"] in materials:
            raise ValueError("duplicate/invalid material ID")
        text(material.get("name")); text(material.get("reason"))
        citations(material.get("evidence_refs"))
        if material.get("family") not in allowed_material_families or material.get("basis") not in {"source_evidence", "construction_assumption"}:
            raise ValueError("invalid material family/basis")
        if material["basis"] == "source_evidence" and not material["evidence_refs"]:
            raise ValueError("source material requires evidence")
        if material["basis"] == "construction_assumption" and material["evidence_refs"]:
            raise ValueError("assumed material cannot claim source proof")
        thickness = positive(material.get("thickness_mm"), "thickness")
        stock = positive(material.get("stock_thickness_mm"), "stock thickness")
        layers = positive(material.get("layers"), "layers", integer=True)
        if abs(stock * layers - thickness) > .001:
            raise ValueError("stock layers do not match finished thickness")
        materials[material["id"]] = material
    plan = scope["planner"]
    expected = {b["id"]: b for b in plan["blocks"] + plan["shared_parts"]}
    blocks = raw["blocks"]
    if any(not isinstance(b, dict) or not isinstance(b.get("id"), str) for b in blocks):
        raise ValueError("invalid parts block")
    if len(blocks) != len(expected) or {b["id"] for b in blocks} != set(expected):
        raise ValueError("missing/duplicate/foreign parts block")
    drawers = {f["id"] for g in scope["front"]["front_groups"] if g.get("type") == "drawer"
        for f in g["fronts"]}
    assemblies = []
    for block in blocks:
        dims = block.get("dimensions")
        if not isinstance(dims, dict) or set(dims) != {"width", "height", "depth"}:
            raise ValueError("block requires width/height/depth")
        for axis, value in dims.items():
            if not isinstance(value, dict):
                raise ValueError("dimension object required")
            positive(value.get("value"), axis); citations(value.get("evidence_refs"))
            if value.get("basis") not in {"source", "derived", "assumption"}:
                raise ValueError("invalid dimension basis")
            if value["basis"] == "assumption" and value["evidence_refs"]:
                raise ValueError("assumed dimension cannot claim source proof")
            if value["basis"] in {"source", "derived"} and not value["evidence_refs"]:
                raise ValueError("source/derived dimension requires evidence")
            if value["basis"] != "source":
                text(value.get("assumption_reason"))
            value.update(unit="mm", unit_basis="explicit_source")
        assemblies.append({"assembly_id": block["id"], "dimensions": dims})
    resolved, audit = resolve_2vn_geometry(dimension_graph=dimension_graph, extraction={
        "document_unit": unit, "assemblies": assemblies,
        "view_interpretations": raw["view_interpretations"], "dimension_bindings": raw["dimension_bindings"],
        "composition_scope": {"construction_version": "cb_parts_v1"}})
    components = []
    group_log = []
    for block, normalized in zip(blocks, resolved["assemblies"]):
        bid = block["id"]
        dims = normalized["dimensions"]
        if set(dims) != {"width", "height", "depth"}:
            raise ValueError(f"{bid}: rejected 2VN dimension; no silent numeric fallback")
        axes = {a: d["value"] * {"mm": 1, "cm": 10, "m": 1000}[d["unit"]] for a, d in dims.items()}
        parts = block.get("parts")
        if not isinstance(parts, list) or not parts or len(parts) > 100:
            raise ValueError("bounded nonempty parts required")
        facades, boxes, rows = set(), set(), []
        front_ids = set(expected[bid].get("front_ids", []))
        for index, part in enumerate(parts, 1):
            if not isinstance(part, dict) or part.get("role") not in ROLES or part.get("material_id") not in materials:
                raise ValueError("invalid part role/material")
            role = part["role"]; quantity = positive(part.get("quantity"), "quantity", integer=True)
            text(part.get("note"))
            ids = part.get("front_ids")
            if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids)):
                raise ValueError("unique front references required")
            if role in {"facade", "drawer_box"}:
                seen = facades if role == "facade" else boxes
                allowed = front_ids if role == "facade" else front_ids & drawers
                if len(ids) != quantity or not set(ids) <= allowed or seen.intersection(ids):
                    raise ValueError("invalid/duplicate facade or drawer assignment")
                seen.update(ids)
            elif ids:
                raise ValueError("only facades/drawer boxes reference fronts")
            if not isinstance(part.get("size"), list) or len(part["size"]) != 2:
                raise ValueError("part requires two face sizes")
            length, deps_l = face_size(part["size"][0], axes)
            width, deps_w = face_size(part["size"][1], axes)
            material = materials[part["material_id"]]
            expanded = [(role, quantity, length, width)]
            if role == "drawer_box":
                depth = _slide_depth_mm(axes["depth"])
                if depth >= axes["depth"]:
                    raise ValueError("drawer cannot fit within cabinet depth")
                expanded = [("drawer_bottom", quantity, length, depth),
                    ("drawer_side", quantity * 2, depth, width), ("drawer_end", quantity * 2, length, width)]
                deps_w.add("depth")
            for subrole, count, l, w in expanded:
                # Topology/face expressions remain estimating assumptions even if
                # every envelope dimension passed 2VN. Do not upgrade panel proof.
                rows.append({"component_id": f"G{index:02d}-{subrole}", "component_role": subrole,
                    "quantity": count, "length_value": l, "width_value": w, "dimension_unit": "mm",
                    "dimension_unit_basis": "explicit_source", "geometry_basis": "assumption",
                    "geometry_evidence_refs": [], "assumption_reason": part["note"],
                    "material": {"source_name": material["name"], "family": material["family"],
                        "basis": material["basis"], "evidence_refs": material["evidence_refs"],
                        "specification": {k: material[k] for k in ("thickness_mm", "stock_thickness_mm", "layers")}}})
            group_log.append({"block_id": bid, **part, "axis_dependencies": sorted(deps_l | deps_w),
                "resolved_axis_bases": {a: dims[a]["basis"] for a in sorted(deps_l | deps_w)}})
        if facades != front_ids or boxes != front_ids & drawers:
            raise ValueError(f"{bid}: missing facades or drawer bodies")
        page_refs = [a["storage_ref"] for a in payload["evidence"]["artifacts"] if a.get("artifact_kind") == "page"]
        components.append({"assembly_id": bid, "evidence_refs": page_refs, "components": rows})
    # Existing material-facts shape and unit conversion, not a competing BOM.
    merged_row = deepcopy(input_row)
    for kind in ("artifacts", "ocr_blocks", "ocr_literal_items"):
        merged_row["input_payload"]["evidence"].setdefault(kind, []).extend(payload.get("document_context", {}).get(kind, []))
    bom = build_assembly_bom(input_row=merged_row, dimension_graph=dimension_graph,
        extraction={"assemblies": components, "omissions": raw["omissions"]}, allowed_material_families=allowed_material_families)
    totals = {m["requirement_id"]: 0.0 for m in bom["materials"]}
    for part in bom["parts"]:
        if part["component_role"] != "support":
            totals[part["material_requirement_id"]] += part["quantity"] * part["length_mm"] * part["width_mm"] / 1e6
    bom.update(status="cb_parts_requires_review", prompt_version=VERSION, two_vn=audit,
        resolved_blocks=resolved["assemblies"], part_groups=group_log, conflicts=raw["conflicts"],
        material_interpretations=list(materials.values()),
        upstream_status=deepcopy(scope.get("upstream_status", {})),
        material_area_per_object=[{"material_id": m["requirement_id"], "finished_area_m2": round(totals[m["requirement_id"]], 4),
            "stock_area_m2": round(totals[m["requirement_id"]] * m["specification"]["layers"], 4)}
            for m in bom["materials"] if m["requirement_id"] in {p["material_requirement_id"] for p in bom["parts"] if p["component_role"] != "support"}])
    return bom
