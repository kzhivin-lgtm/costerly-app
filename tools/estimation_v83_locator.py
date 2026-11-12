"""Locate the existing Blocks on native and raster source views."""

from base64 import b64decode
from collections import defaultdict
from io import BytesIO

from PIL import Image

from tools.estimation_raster_regions import raster_regions
from tools.probe_cb_adda_ownership import hull
from tools.probe_estimation_v7_4_visual_front import image_block
from tools.probe_estimation_v8_native_blocks import close_display_envelopes, resolve_locator_contours
from use_cases.estimation_block_locator_v8 import bind_raster_supported_envelope, complete_native_assemblies


NATIVE_LOCATOR = """Return one compact JSON object only, no analysis or prose. Each primary
axonometric drawing represents its supplied object. Keep each block in its supplied
view and preserve each existing ID and grouping. The supplied contours identify
just some of the block's existing members. Identify additional visible exact
C contours that complete each assembly, including sides, backing, top, and
narrow fixed edges. A display assembly includes its whole cabinet from top to
bottom, including the panels above the pull-outs. A mirror block includes its
mounting panel. A drawer-bank block includes the open top shelf and cabinet end
faces. A thin toe kick below the body belongs to an object plinth kit, not to
any carcass. Don't include legend/annotation space, or a contour spanning
multiple different assemblies. Use only C IDs printed on the corresponding
image. Never invent IDs or move a group to another view.
Schema:
{"objects":{"supplied object ID":{"add":{"supplied block ID":["Cxx"]},"plinth":["Cxx"],"unresolved":[]}}}
Include each supplied block key exactly once, using empty arrays when needed.
Unresolved entries should name short specific visible regions and block ID.
"""
RASTER_LOCATOR = """Locate the independent supported tabletop and its visible
legs in each axonometric crop. The supplied assembly ID is fixed. Identify
the R region that best represents the tabletop surface. For every visible
leg select its own R region, one seed per physical piece. Compare the views
to distinguish legs from cabinet sides. An R region can cover just the
visible interior of a piece. Leave hidden legs out. Exclude cabinet,
plinth, and background. Do not trace any freehand coordinates.
Return JSON only:
{"views":[{"view_id":"source view ID","supported_assembly":{"id":"supplied block ID",
"top_region_id":"Rxx","leg_region_ids":["Rxx"]}}]}"""


def ground_native_shell_proposal(plan, view, proposal):
    """Anchor proposed fixed shells to their actual visible planes before resolving seams."""
    from tools.probe_cb_adda_ownership import contact
    from tools.probe_cb_block_boundaries import axis_overlap

    native = {row["id"]: row for row in view["candidates"]}
    vid = view["view_id"]
    blocks = {row["id"]: row for row in plan["blocks"]}
    base = {bid: set(block["appearances"][vid] + block.get("supporting_contours", []))
            for bid, block in blocks.items()}
    plinth = set(resolve_locator_contours(plan, view, proposal)["plinth_ids"])
    fixed = set().union(*base.values(), plinth)
    proposed = {bid: set(ids) - fixed for bid, ids in proposal["add"].items()}

    def size(cid):
        left, top, right, bottom = native[cid]["bbox"]
        return right - left, bottom - top

    def shared(cid, ids):
        return max((contact(native[cid], native[other]) for other in ids), default=0)

    bays = {bid for bid, block in blocks.items() if block["basis"] == "drawer_and_pull_out_bay"}
    for bid, block in blocks.items():
        if block["basis"] == "assumed_lower_frame_split":
            upper_edge = min(native[cid]["bbox"][1] for cid in base[bid])
            proposed[bid] = {cid for cid in proposed[bid]
                             if native[cid]["bbox"][1] + .4 * size(cid)[1] >= upper_edge - 3}
        elif block["basis"] == "mirror_upright":
            proposed[bid] = {cid for cid in proposed[bid] if shared(cid, base[bid]) >= .30 * max(size(cid))}

    seed_span = {bid: (min(native[cid]["bbox"][0] for cid in base[bid] | proposed[bid]),
                       max(native[cid]["bbox"][2] for cid in base[bid] | proposed[bid])) for bid in bays}

    # Adjacent carcass panels grow from positive contact, including panels omitted by the model.
    # Keep each step exclusive and stop at a competing assembly seam.
    while bays:
        occupied = fixed | set().union(*proposed.values())
        additions = []
        for cid, contour in native.items():
            if cid in occupied:
                continue
            width, height = size(cid)
            scores = sorted((shared(cid, base[bid] | proposed[bid]), bid) for bid in blocks)
            best, bid = scores[-1]
            second = scores[-2][0] if len(scores) > 1 else 0
            if bid not in bays or best < max(12, .35 * min(width, height)) or best < 1.5 * second:
                continue
            shell = [native[r]["bbox"] for r in base[bid] | proposed[bid]]
            left = min(box[0] for box in shell)
            right = max(box[2] for box in shell)
            bottom = max(box[3] for box in shell)
            x0, y0, x1, y1 = contour["bbox"]
            # Grow within the projected face band or into a narrow return side.
            if y1 > bottom + .04 * height or min(right, x1) - max(left, x0) < -.04 * (right - left):
                continue
            if (x1 < left or x0 > right) and width > .22 * (right - left):
                continue
            seed_left, seed_right = seed_span[bid]
            # A narrow seam can terminate the shell. It cannot extend the
            # admitted front plane into the next vertical strip.
            center = (x0 + x1) / 2
            if height > 5 * width and width < .05 * (seed_right - seed_left):
                mirror_edge = any(block["basis"] == "mirror_upright" and shared(cid, base[other]) >= .8 * height
                                  for other, block in blocks.items())
                if mirror_edge or not seed_left - 2 <= center <= seed_right + 2:
                    continue
            additions.append((bid, cid))
        if not additions:
            break
        for bid, cid in additions:
            proposed[bid].add(cid)

    # An end face below an upper assembly can continue the lower row with a
    # small setback. Confirm both the lower seam and independent plinth contact.
    for cid in native.keys() - fixed:
        box = native[cid]["bbox"]
        width, height = size(cid)
        if not plinth or width < 10 or height < 15 or shared(cid, plinth) < .5 * width:
            continue
        matches = []
        for bid, block in blocks.items():
            if block["basis"] != "return_door_band":
                continue
            for member in (ident for slot in block["positions"] for ident in slot):
                other = native[member]["bbox"]
                gap = max(box[0] - other[2], other[0] - box[2])
                if (-3 <= gap <= .15 * min(width, size(member)[0])
                        and axis_overlap(box, other, 1) >= .82 and .5 <= height / size(member)[1] <= 1.4):
                    matches.append(bid)
        if len(set(matches)) == 1:
            for ids in proposed.values():
                ids.discard(cid)
            proposed[matches[0]].add(cid)

    return {**proposal, "add": {bid: sorted(ids) for bid, ids in proposed.items()}}


def native_locator(objects, views, images, frames, invoke, request, payload):
    prior, content = {}, []
    for oid, item in objects.items():
        plan = item["planner"]
        blocks = plan["blocks"]
        if not blocks or not all(isinstance(b["appearances"], dict) for b in blocks):
            continue
        vids = {vid for block in blocks for vid in block["appearances"]}
        if len(vids) != 1:
            continue
        vid, = vids
        content.append({"type": "text", "text": f"The next two images represent {oid}, primary axonometric {vid}. "
                        "A cropped sliver of another object in the margin is outside its scope."})
        content.extend(images[vid])
        prior[oid] = {"view_id": vid, "blocks": {
            block["id"]: {"role": block["basis"], "members": block["appearances"][vid],
                          "backing": block.get("supporting_contours", [])} for block in blocks
        }, "plinth": [part.get("contour_ids", []) for part in plan["object_parts"] if part["role"] == "plinth"]}
    if not prior:
        return
    content.append(payload(prior))

    def bind(raw):
        if raw["objects"].keys() != prior.keys():
            raise ValueError("Block Locator changed the object IDs")
        for oid, value in raw["objects"].items():
            allowed = frames[prior[oid]["view_id"]]["contours"]
            if value["add"].keys() != prior[oid]["blocks"].keys():
                raise ValueError("Block Locator changed the existing block IDs")
            for ids in [*value["add"].values(), value["plinth"]]:
                if not set(ids) <= allowed.keys() or len(set(ids)) != len(ids):
                    raise ValueError("Block Locator used an invalid or repeated contour")
        return raw["objects"]

    result = invoke("native-locator", request(NATIVE_LOCATOR, content, max_tokens=3500), bind)
    for oid, reading in result.items():
        item = objects[oid]
        vid = prior[oid]["view_id"]
        plan = item["planner"]
        proposal = ground_native_shell_proposal(plan, views[vid], reading)
        resolved = resolve_locator_contours(plan, views[vid], proposal)
        front_ids = {row["candidate_id"] for row in item["front"]["faces"] if row["view_id"] == vid}
        plan = complete_native_assemblies(plan, views[vid], front_ids=front_ids, **resolved)
        item["planner"] = close_display_envelopes(plan, vid)
        plan["reported_unresolved_edges"] = reading["unresolved"]


def rect(box):
    left, top, right, bottom = box
    return [(left, top), (right, top), (right, bottom), (left, bottom)]


def supported_elevations(plan, part, views):
    block, = [block for block in plan["blocks"] if block["id"] == part["envelope_block_id"]]
    grouped = defaultdict(list)
    for appearance in block["appearances"]:
        grouped[appearance["view_id"]].append(appearance["bbox"])
    for vid, legs in grouped.items():
        tops = [row["bbox"] for row in part["appearances"] if row["view_id"] == vid]
        if not tops and len(legs) > 1:
            left, right = min(box[0] for box in legs), max(box[2] for box in legs)
            underside = min(box[1] for box in legs)
            tops = [row["bbox"] for row in views[vid]["candidates"] if row["bbox"][0] <= left
                    and row["bbox"][2] >= right and abs(row["bbox"][3] - underside) <= 2
                    and row["bbox"][2] - row["bbox"][0] > 8 * (row["bbox"][3] - row["bbox"][1])]
        if len(tops) == 1:
            block.setdefault("envelopes", {})[vid] = {
                "basis": "orthographic support and attached top", "part_id": part["id"],
                "polygons_px": [rect(box) for box in tops + legs],
            }


def raster_locator(objects, views, projections, images, invoke, request, payload):
    for oid, item in objects.items():
        plan = item["planner"]
        tops = [row for row in plan["object_parts"] if row.get("envelope_block_id")]
        for part in tops:
            supported_elevations(plan, part, views)
        raster_views = {vid: view for vid, view in views.items() if view["object_id"] == oid
                        and projections[vid] == "Axonometric view" and not view["candidates"]}
        if len(tops) != 1 or not raster_views:
            continue
        part, = tops
        frames, content = {}, []
        for vid, view in sorted(raster_views.items()):
            raw = b64decode(images[vid][1]["source"]["data"])
            with Image.open(BytesIO(raw)) as source:
                clean, mapped, packet = raster_regions(source)
            if not packet["regions"]:
                continue
            frames[vid] = packet
            buffer = BytesIO()
            clean.save(buffer, format="PNG")
            content.extend([{"type": "text", "text": f"{vid} clean axonometric drawing {clean.width}x{clean.height} px."},
                            image_block(buffer.getvalue())])
            buffer = BytesIO()
            mapped.save(buffer, format="PNG")
            content.extend([{"type": "text", "text": f"{vid} same crop with neutral raster region IDs."},
                            image_block(buffer.getvalue())])
        if not frames:
            continue
        content.append(payload({
            "supported_assembly_id": part["envelope_block_id"],
            "candidate_bbox_px": {vid: {r["id"]: r["bbox"] for r in packet["regions"]} for vid, packet in frames.items()},
        }))

        def bind(raw):
            by_view = {row["view_id"]: row for row in raw["views"]}
            if by_view.keys() != frames.keys() or len(by_view) != len(raw["views"]):
                raise ValueError("Raster Locator requires one result per source view")
            for vid, row in by_view.items():
                packet = frames[vid]
                ext = row["supported_assembly"]
                ids = {r["id"] for r in packet["regions"]}
                if ext["id"] != part["envelope_block_id"] or not {ext["top_region_id"], *ext["leg_region_ids"]} <= ids:
                    raise ValueError("Raster Locator did not bind the assembly to valid regions")
            return by_view

        raw = invoke(f"raster-locator-{oid}", request(RASTER_LOCATOR, content, max_tokens=1200), bind)
        block, = [b for b in plan["blocks"] if b["id"] == part["envelope_block_id"]]
        for vid, row in raw.items():
            packet, view = frames[vid], raster_views[vid]
            binding = bind_raster_supported_envelope(plan, row, packet)
            regions = {r["id"]: r for r in packet["regions"]}
            width, height = packet["size"]
            polygons = []
            for ident in binding["top_region_ids"] + binding["support_region_ids"]:
                points = [(i % width, i // width) for i in regions[ident]["pixels"]]
                polygons.append([(x * view["width"] / width, y * view["height"] / height)
                                 for x, y in hull(points)])
            block.setdefault("envelopes", {})[vid] = {**binding, "polygons_px": polygons}
