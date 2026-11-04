"""Compact visual intent -> existing V6 construction contract, without a model call."""
from copy import deepcopy
import math
from typing import Any, Mapping, Sequence

from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_dimension_scale import build_dimension_scale_gate

SEMANTIC_PLAN_VERSION = "estimation_semantic_plan_v6_1"
KINDS = {"drawer_cabinet": ("drawer_bank", "drawer"), "cabinet": ("box_carcass", "fixed"),
         "screen": ("vertical_panel", "fixed"), "panel": ("vertical_panel", "fixed"),
         "shelves": ("shelf_stack", "fixed"), "worktop": ("countertop", "fixed"),
         "supports": ("support", "none"), "doors": ("facade_set", "hinged")}
MATERIALS = {
    "veneered_mdf": ("mdf_hdf", {"board_type": "mdf", "surface": "veneer_two_sided"}),
    "painted_mdf": ("mdf_hdf", {"board_type": "mdf", "surface": "raw"}),
    "raw_mdf": ("mdf_hdf", {"board_type": "mdf", "surface": "raw"}),
    "ldsp": ("melamine_faced_particleboard", {}), "plywood": ("plywood", {}),
    "solid_wood": ("timber_solid_wood_panel", {}), "purchased_leg": ("hardware_leg_caster", {}),
    "metal_tube": ("round_tube", {})}
SHEETS = {"veneered_mdf", "painted_mdf", "raw_mdf", "ldsp", "plywood", "solid_wood"}


def _positive(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"semantic {field} must be positive") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"semantic {field} must be positive")
    return number


def _count(value: Any, field: str) -> int:
    number = _positive(value, field)
    if number != int(number):
        raise ValueError(f"semantic {field} must be an integer")
    return int(number)


def _thicknesses(zones, row):
    graph = build_dimension_graph(input_row=row)
    convention = (build_dimension_scale_gate(dimension_graph=graph).get("decision") or {}).get("required_unit")
    numbers = {ref: n for n in graph.get("dimension_numbers") or [] for ref in n.get("evidence_refs") or []}
    by_id, resolved, visiting = {z["id"]: z for z in zones}, {}, set()
    def resolve(zid):
        if zid in resolved:
            return resolved[zid]
        if zid in visiting or zid not in by_id:
            raise ValueError("semantic thickness relationship is cyclic or unknown")
        visiting.add(zid)
        raw = by_id[zid].get("thickness") or {}
        if raw.get("same_as"):
            value, _, _, _ = resolve(raw["same_as"])
            result = (value, "assumption", [], raw.get("reason") or "Visually corresponding exposed member thickness assumed equal.")
        elif raw.get("ref"):
            number = numbers.get(raw["ref"])
            unit = (number or {}).get("printed_unit") or convention
            if not number or unit not in {"mm", "cm", "m"}:
                raise ValueError("semantic thickness reference has no unit-resolved numeric witness")
            result = (_positive(number["numeric_value"], "thickness") * {"mm": 1, "cm": 10, "m": 1000}[unit],
                      "source", [raw["ref"]], "Indicated member thickness converted using printed units or the recorded document-scale assumption.")
        else:
            result = (_positive(raw.get("mm", 20), "thickness"), "assumption", [],
                      raw.get("reason") or "Unspecified panel thickness: 20-mm estimating default.")
        visiting.remove(zid)
        resolved[zid] = result
        return result
    for z in zones:
        resolve(z["id"])
    return resolved


def compile_semantic_plan(raw: Mapping[str, Any], *, inputs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Transport-only revision; palette/scope/composer/Engine contracts stay intact."""
    if raw.get("contract_version") != SEMANTIC_PLAN_VERSION:
        raise ValueError("Analyze requires the compact semantic plan contract")
    raw = deepcopy(dict(raw))
    # Known view ids are locators on existing source pages, not new evidence.
    # Resolve only ids present in the immutable graph, never invented labels.
    view_refs, owned_view_refs, ambiguous_views = {}, {}, set()
    for row in inputs:
        owned = owned_view_refs.setdefault(str(row["input_id"]), {})
        payload = row["input_payload"]
        pages = {a.get("page_number"): a["storage_ref"] for a in (payload.get("evidence") or {}).get("artifacts") or []
                 if a.get("artifact_kind") == "page" and a.get("storage_ref")}
        for view in build_dimension_graph(input_row=row).get("views") or []:
            if view["page_number"] in pages:
                ref = pages[view["page_number"]]
                owned[view["view_id"]] = ref
                if view["view_id"] in view_refs and view_refs[view["view_id"]] != ref:
                    ambiguous_views.add(view["view_id"])
                view_refs[view["view_id"]] = ref
    for obj in raw.get("objects") or []:
        owned = owned_view_refs.get(str(obj.get("input_id")), {})
        for zone in obj.get("zones") or []:
            zone["evidence_refs"] = list(dict.fromkeys(owned.get(ref, ref) for ref in zone.get("evidence_refs") or []))
    for material in raw.get("materials") or []:
        for link in material.get("evidence_chain") or []:
            if link.get("ref") in ambiguous_views:
                raise ValueError("shared material evidence requires a source ref, not an ambiguous object-local view id")
            if link.get("ref") in view_refs:
                view_id = link["ref"]
                link["ref"] = view_refs[view_id]
                link["observation"] = f"{view_id}: {link.get('observation') or ''}"
    owners = {str(row["input_id"]): row for row in inputs}
    objects = raw.get("objects")
    if not isinstance(objects, list) or {str(o.get("input_id")) for o in objects} != set(owners) or len(objects) != len(owners):
        raise ValueError("semantic plan must cover every requested input exactly once")
    intents = {}
    for m in raw.get("materials") or []:
        mid = str(m.get("id") or "")
        if not mid or mid in intents or mid.startswith("__"):
            raise ValueError("semantic material ids must be unique and non-reserved")
        if m.get("kind") not in {*MATERIALS, "other"}:
            raise ValueError("semantic material kind is unsupported")
        intents[mid] = m
    prepared, targets = [], {}
    for obj in objects:
        row = owners[obj["input_id"]]
        if obj.get("object_id") != row["input_payload"]["object"]["object_id"]:
            raise ValueError("semantic plan changed object identity")
        zones = obj.get("zones") or []
        if not zones or len({z.get("id") for z in zones}) != len(zones) or any(not z.get("id") for z in zones):
            raise ValueError("semantic zones need unique ids")
        thickness = _thicknesses(zones, row)
        for z in zones:
            if z.get("kind") not in KINDS or z.get("material_id") not in intents:
                raise ValueError("semantic zone has unknown kind or material")
            if intents[z["material_id"]]["kind"] in SHEETS:
                targets.setdefault(z["material_id"], []).append(thickness[z["id"]])
        prepared.append((obj, zones, thickness))
    palette, stock = {}, {}
    for mid, intent in intents.items():
        kind = intent["kind"]
        family, defaults = MATERIALS.get(kind, (intent.get("family"), {}))
        specification = {**defaults, **deepcopy(intent.get("specification") or {})}
        assumptions = dict(intent.get("attribute_assumptions") or {})
        if kind in SHEETS:
            explicit = intent.get("stock_thickness_mm") or specification.get("thickness_mm")
            if explicit:
                stock[mid] = _positive(explicit, "stock thickness")
            else:
                decisions = targets.get(mid) or [(20, "assumption", [], "")]
                source_values = [t[0] for t in decisions if t[1] == "source"]
                values = source_values or [t[0] for t in decisions]
                candidates = [v for v in (30, 25, 22, 20, 19, 18, 16, 15, 12, 9, 6)
                              if all(abs(t / v - round(t / v)) < 1e-6 and 1 <= round(t / v) <= 8 for t in values)]
                stock[mid] = (candidates[0] if candidates else min(values)) if kind != "solid_wood" else min(values)
                assumptions["thickness_mm"] = f"Purchased {stock[mid]:g}-mm stock is an estimating construction assumption, not a catalog offer."
            specification["thickness_mm"] = stock[mid]
        palette[mid] = {"material_id": mid, "source_name": intent.get("name") or kind, "family": family,
            "specification": specification, "basis": intent.get("basis") or "construction_default",
            "reason": intent.get("reason") or "Professional material assumption.",
            "evidence_chain": deepcopy(intent.get("evidence_chain") or []), "attribute_assumptions": assumptions}
    scopes = []
    for obj, zones, thickness in prepared:
        compiled = []
        for z in zones:
            kind, mid = z["kind"], z["material_id"]
            role, operability = KINDS[kind]
            finished, basis, refs, why = thickness[z["id"]]
            intent = intents[mid]
            layers = finished / stock[mid] if mid in stock else 1
            if mid in stock and (abs(layers - round(layers)) > 1e-6 or not 1 <= layers <= 8):
                if basis == "source":
                    raise ValueError("semantic finished thickness cannot be built from selected stock")
                layers = min(8, max(1, round(layers)))
                original = finished
                finished = layers * stock[mid]
                why += f" Assumed {original:g}-mm thickness aligned to {finished:g} mm using shared project stock; source dimensions unchanged."
            assigned = "leg" if kind == "supports" else "worktop_sheet" if kind == "worktop" else "visible_sheet"
            main = {"role": assigned, "material_id": mid, "finished_thickness_mm": finished if mid in stock else 0,
                    "layer_count": int(round(layers)), "thickness_basis": basis, "thickness_evidence_refs": refs, "reason": why}
            if intent["kind"] == "veneered_mdf":
                eid = f"__edge_{mid}_{finished:g}"
                palette[eid] = {"material_id": eid, "source_name": "Matching veneer edge", "family": "edge_banding",
                    "specification": {"width_mm": finished, "surface": "wood_veneer"}, "basis": "construction_default",
                    "reason": "Full exposed perimeter edge allowance covering finished thickness; factory face veneer already included."}
                main["edge_material_id"] = eid
            assignments = [main]
            if kind in {"drawer_cabinet", "cabinet", "shelves"}:
                assignments.append({**main, "role": "carcass_sheet"})
                hidden = z.get("hidden_material_id") or mid
                if hidden not in stock:
                    raise ValueError("semantic hidden material requires sheet stock")
                for hr in ("internal_sheet", "backing_sheet"):
                    assignments.append({"role": hr, "material_id": hidden, "layer_count": 1,
                        "finished_thickness_mm": stock[hidden], "thickness_basis": "assumption",
                        "alternative_material_ids": z.get("hidden_alternatives") or [],
                        "reason": "Unshown internals use one layer of assigned project stock; no new sheet family by default."})
            if intent["kind"] == "painted_mdf":
                fid = f"__finish_{mid}"
                palette[fid] = {"material_id": fid, "source_name": "Paint finish", "family": "paint_lacquer_stain",
                    "specification": {k: v for k, v in palette[mid]["specification"].items() if k in {"colour", "finish_type"}},
                    "basis": palette[mid]["basis"], "evidence_chain": palette[mid]["evidence_chain"],
                    "reason": "Separate paint material for raw MDF, scoped to assigned exposed faces."}
                assignments.append({"role": "finish", "material_id": fid, "applies_to_roles": [assigned]})
            fronts, counts = [], {}
            if kind in {"drawer_cabinet", "doors"}:
                n = _count(z.get("front_count"), "front count")
                layout = z.get("front_arrangement")
                if layout not in {"side_by_side", "stacked"}:
                    raise ValueError("semantic fronts require explicit arrangement")
                fronts = [{"front_kind": "drawer_front" if kind == "drawer_cabinet" else "hinged_facade", "quantity": n, "arrangement": layout}]
                counts["drawers" if kind == "drawer_cabinet" else "facades"] = n
            if z.get("shelf_count"):
                counts["shelves"] = _count(z["shelf_count"], "shelf count")
            groups = [{"group_id": m["id"], "component_role": m.get("role") or "panel", "quantity": _count(m.get("count"), "member count"),
                       "material_role": assigned, "reason": m.get("observation") or "Observed fixed member group."} for m in z.get("members") or []]
            if groups and kind not in {"screen", "panel"}:
                raise ValueError("semantic member groups belong to a fixed screen or panel")
            compiled.append({"scope_id": z["id"], "assembly_role": role, "semantic_role": z.get("description") or kind,
                "quantity": _count(z.get("quantity", 1), "zone quantity"), "operability": operability, "counts": counts,
                "front_groups": fronts, "material_assignments": assignments, "panel_groups": groups, "evidence_refs": z.get("evidence_refs") or [],
                "geometry_links": [], "construction": "linear_stock" if intent["kind"] == "metal_tube" else "purchased" if kind == "supports" else "conventional"})
        scopes.append({"input_id": obj["input_id"], "object_id": obj["object_id"], "object_summary": obj.get("summary") or "",
                       "zones": compiled, "assumptions": obj.get("assumptions") or []})
    return {"material_palette": list(palette.values()), "object_scopes": scopes}
