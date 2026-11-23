"""Retain existing construction/native-edge evidence for dispatch trial fit."""

from itertools import combinations


def attach_preparation_evidence(report, analyze, native_views):
    """Add Labor evidence without altering source Parts, envelopes or recognition."""
    from tools.probe_cb_adda_ownership import contact

    if report["source_audit_sha256"] != analyze["source_audit_sha256"]:
        raise ValueError("Preparation evidence must match the locked source")
    views = {view["view_id"]: {c["id"]: c for c in view["candidates"]} for view in native_views}
    for oid, source in report["objects"].items():
        plan = analyze["objects"][oid]["planner"]
        blocks = plan["blocks"]
        interfaces = {}

        def add(a, b, ref):
            if a == b:
                return
            key = tuple(sorted((a, b)))
            row = interfaces.setdefault(key, {"unit_ids": list(key), "quantity": 1, "source_refs": []})
            if ref not in row["source_refs"]:
                row["source_refs"].append(ref)

        def appearances(block):
            value = block.get("appearances", {})
            if isinstance(value, dict):
                return {vid: set(ids) for vid, ids in value.items()}
            result = {}
            for appearance in value:
                ids = {*appearance.get("contour_ids", ()), *appearance.get("drawer_faces", ())}
                ids.update(cid for group in block.get("positions", ()) for cid in group)
                result.setdefault(appearance["view_id"], set()).update(ids)
            return result

        by_id = {b["id"]: appearances(b) for b in blocks}
        for block in blocks:
            attachment = block.get("attachment") or {}
            if attachment.get("block_id") in by_id:
                add(block["id"], attachment["block_id"], {"basis": "saved_structural_attachment", **attachment})
        known_units = {b["id"] for b in source.get("blocks", ())} | {
            p.get("owner_id") for p in source.get("parts", ()) if not p.get("block_id")}
        for part in plan.get("object_parts", ()):
            owner = part.get("envelope_block_id") or part["id"]
            for attached in part.get("attached_block_ids", ()):
                if owner in known_units and attached in by_id:
                    add(owner, attached, {"basis": "saved_component_attachment", "component_id": part["id"]})
        for a, b in combinations(blocks, 2):
            for vid in sorted(by_id[a["id"]].keys() & by_id[b["id"]].keys()):
                contours = views.get(vid, {})
                left, right = by_id[a["id"]][vid], by_id[b["id"]][vid]
                strongest = None
                for i in sorted(left - right):
                    for j in sorted(right - left):
                        if i not in contours or j not in contours:
                            continue
                        length = contact(contours[i], contours[j])
                        if length >= 4 and (strongest is None or length > strongest[0]):
                            strongest = length, i, j
                if strongest:
                    length, i, j = strongest
                    add(a["id"], b["id"], {"basis": "native_shared_boundary", "view_id": vid,
                                             "contour_ids": [i, j], "contact_length_px": round(length, 3)})
        missing = [bid for bid, appearances in by_id.items() if not any(
            ids & views.get(vid, {}).keys() for vid, ids in appearances.items())
            and not any(bid in key for key in interfaces)]
        source["preparation_evidence"] = {
            "version": "native_block_interfaces_v1", "status": "partial" if missing else "ready",
            "source_audit_sha256": report["source_audit_sha256"],
            "unrepresented_block_ids": missing,
            "interfaces": [interfaces[key] for key in sorted(interfaces)],
        }
    return report
