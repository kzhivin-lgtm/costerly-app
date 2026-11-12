"""Source-linked assembly outlines kept separate from material ownership."""

from collections import defaultdict
from copy import deepcopy


def complete_native_assemblies(plan, view, *, additions, plinth_ids, front_ids):
    """Extend fixed assemblies with exclusive source contours from one view."""
    result = deepcopy(plan)
    vid = view["view_id"]
    native = {row["id"]: row["polygon"] for row in view["candidates"]}
    blocks = {row["id"]: row for row in result["blocks"]}
    if additions.keys() != blocks.keys():
        raise ValueError("Block Locator must preserve all block IDs")
    claimed = defaultdict(set)
    for bid, block in blocks.items():
        for ident in block["appearances"][vid] + block.get("supporting_contours", []):
            claimed[ident].add(bid)
    reserved = {ident for row in result["object_parts"] if row["role"] == "plinth"
                and row.get("source_view_id") == vid for ident in row["contour_ids"]}
    if not (set(plinth_ids) | reserved | {ident for ids in additions.values() for ident in ids}) <= native.keys():
        raise ValueError("unknown native source contour")
    issues = []
    for ident in plinth_ids:
        if ident in front_ids:
            issues.append({"contour_id": ident, "reason": "plinth proposal conflicts with an operating or mirrored face"})
        else:
            reserved.add(ident)
    for ident in reserved:
        claimed.pop(ident, None)
    for ident, owners in claimed.items():
        if len(owners) != 1:
            raise ValueError(f"existing native contour has multiple owners: {ident}")
    pending = defaultdict(set)
    for bid, items in additions.items():
        for ident in items:
            if ident in reserved or (ident in claimed and bid not in claimed[ident]):
                issues.append({"contour_id": ident, "block_id": bid, "reason": "contour already has a different owner"})
            else:
                pending[ident].add(bid)
    for ident, owners in pending.items():
        if len(owners) == 1:
            claimed[ident].update(owners)
        else:
            issues.append({"contour_id": ident, "block_ids": sorted(owners), "reason": "competing block claims"})
    for bid, block in blocks.items():
        contour_ids = sorted(ident for ident, owners in claimed.items() if bid in owners)
        block["appearances"][vid] = contour_ids
        if "members" in block:
            block["members"] = contour_ids
        block.setdefault("structural_contours", {})[vid] = [ident for ident in contour_ids if ident not in front_ids]
        if "supporting_contours" in block:
            block["supporting_contours"] = [ident for ident in block["supporting_contours"] if ident not in reserved]
        block.setdefault("envelopes", {})[vid] = {"basis": "native_assembly_members", "contour_ids": contour_ids,
                                                   "polygons_px": [native[ident] for ident in contour_ids]}
    if reserved:
        plinth = next((part for part in result["object_parts"] if part["role"] == "plinth"), None)
        if plinth is None:
            plinth = {"id": "plinth-kit", "role": "plinth", "quantity": 1, "unit": "set"}
            result["object_parts"].append(plinth)
        plinth.update(source_view_id=vid, contour_ids=sorted(reserved))
    result["locator_issues"] = issues
    return result


def link_supported_worktop(plan):
    """Record one projected owner for the top while keeping its part identity."""
    supports = {row["id"] for row in plan["blocks"] if row["basis"] == "independently_supported_extension"}
    for part in plan["object_parts"]:
        if part["role"] != "worktop":
            continue
        linked = supports.intersection(part.get("attached_block_ids", []))
        if len(linked) == 1:
            part["envelope_block_id"] = next(iter(linked))
    return plan


def bind_raster_supported_envelope(plan, reading, packet):
    """Use source region pixels for a mounted top and its visible vertical legs."""
    selected = reading["supported_assembly"]
    bid = selected["id"]
    part, = [row for row in plan["object_parts"] if row.get("envelope_block_id") == bid]
    regions = {row["id"]: row for row in packet["regions"]}
    top = regions[selected["top_region_id"]]
    top_ids, leg_ids = [top["id"]], []
    for ident in selected["leg_region_ids"]:
        left, upper, right, lower = regions[ident]["bbox"]
        if lower - upper >= 2 * (right - left):
            leg_ids.append(ident)
        elif min(right, top["bbox"][2]) - max(left, top["bbox"][0]) >= .7 * (right - left) and (
                lower > top["bbox"][3] and lower - top["bbox"][3] <= .12 * (top["bbox"][3] - top["bbox"][1])):
            top_ids.append(ident)
    if not leg_ids:
        raise ValueError("no vertical support bound to the projected assembly")
    return {"block_id": bid, "part_id": part["id"], "basis": "visible raster regions",
            "view_id": reading["view_id"], "top_region_ids": list(dict.fromkeys(top_ids)),
            "support_region_ids": list(dict.fromkeys(leg_ids)), "frame_size_px": packet["size"]}
