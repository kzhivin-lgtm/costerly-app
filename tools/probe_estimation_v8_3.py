"""Experimental Analyze pipeline over source-only Detection and native Islands."""

import argparse
from base64 import b64decode
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
from math import hypot, isfinite
import json
from pathlib import Path

import pymupdf

from PIL import Image, ImageDraw, ImageFont

from tools.estimation_v83_locator import native_locator, raster_locator
from tools.estimation_native_islands import extract_islands
from tools.estimation_native_opening_marks import mark_on_face, thin_strokes
from tools.probe_estimation_v7_4_front_evidence import (
    SYSTEM as TYPED_FRONT,
    bind_front_roles,
    execute_request,
    render_caption_image,
    render_stroke_image,
)
from tools.probe_estimation_v7_4_visual_front import bind_island_faces, image_block, prepare
from tools.probe_estimation_v8_native_blocks import (
    ELEVATION_PROJECTIONS, assemble_native_front_blocks, isolated_callout_outline,
)

AXONOMETRIC = "Axonometric view"
PROJECTIONS = ELEVATION_PROJECTIONS | {
    AXONOMETRIC, "Top view", "Section", "Detail", "Render", "Room plan", "Other"
}
ISLAND_MAP = """Classify every supplied drawing crop by projection. Axonometric
shows multiple axes in a pictorial view. A top view shows the object from above.
A front elevation displays the operating faces of a cabinet wing. A rear or
side view may display the exterior, or another working elevation of the same
object. Section requires evidence of a cut. Use one supplied exact projection
per Island. Based on all Islands of an object, name the object in up to three
words, describe its arrangement briefly, and list a few construction or finish
characteristics. Keep visible evidence separate from uncertainty. Use
Detection's normalized values only if clearly relevant to the named feature.
Express any physical measurement in millimetres. Keep operating-front counts
for the Front stage and assembly dimensions for Geometry. Separate visible
material cues from unconfirmed substrate or finish.
Return JSON only:
{"islands":{"view_id":"projection"},"understanding":{"object_id":{"name":"...",
"description":"...","characteristics":["..."]}}}"""
MAX_FINISH_SURFACES = 24
VISIBLE_FINISH = """
For each object, return finish_surfaces with one row per distinguishable visible panel surface.
Use {"role":"...", "view_id":"...", "bbox_crop_1000":[left,top,right,bottom],
"finish":"wood_grain", "finish_group":"...", "evidence":"short visible cue"}.
Use 0–1000 coordinates relative to the clean crop. Locate the visible surface itself.
Finish is wood_grain, plain, unclear or solid_wood. Use unclear when the finish is unreadable.
Base the finish on the surface's visible grain, colour and drawing notes.
Treat a clear wood-grain pattern on a sheet or panel as veneer and choose veneered MDF
as the estimating substrate when the drawing does not specify a different material.
Do not infer solid wood from grain, colour or a species name. Choose "solid_wood" only
if a drawing note explicitly specifies solid wood for that role. For "solid_wood" also
return "source_ref" from material_notes and a verbatim "source_quote" naming the role
and solid material. If a note specifies another material, omit that role here.
Use the clearest coloured or axonometric view for finish, and the drawing annotations
and measured elevations for geometry. Extend a finish to another visible panel when
the rendering shows that it shares the same identified decor. Plain colour or hatch
in isolation does not establish veneer. Report different surfaces separately even when
they share a role. Use the same finish group only for corroborated matching decor.
Allowed roles: seat_cover (seat or base cover), drawer_front, door_front, lift_up_front,
fixed_panel, frame_cap, frame_side, frame_backing, vertical_rib, tabletop,
tabletop_underlayer (visible lower plate), carcass_side (visible exterior sides).
If one crop shows the same finish on several roles, report each role separately and give
them the same short finish_group. Use different groups for visibly different finishes.
Check the seat or top cover, operating fronts, outer sides and decorative frame separately
against the visible finish characteristics. In characteristics,
state the visible evidence and whether the material is an assumption or explicitly
specified. Parts Geometry uses one stock thickness for compatible panels where the
drawing leaves it open, while preserving explicit dimensions.
Return at most {limit} surfaces per object. Prefer the clearest view when a surface repeats.
Prioritize distinct finishes and visible surfaces where the material would otherwise be unclear.
""".replace("{limit}", str(MAX_FINISH_SURFACES))
WORKTOP_CUTOUTS = """
In each object's Understanding, also return worktop_cutouts (empty if none).
Record one row per visible appliance opening in a worktop. Use a single
clearest Island per object so alternate views cannot count the same opening
twice. An opening has an enclosed boundary on the worktop surface. Exclude
seams, door edges, colour changes and uncut markings. For each opening use
{\"view_id\":\"...\",\"bbox_px\":[left,top,right,bottom],\"fixture\":\"unknown\",
\"surface\":\"main_worktop\"}, with tight pixel bounds on the clean crop.
Fixture is sink, cooktop or unknown. Use sink or cooktop only when the
drawing identifies it. Surface is main_worktop, contrasting_end or unknown.
Do not infer dimensions or request any area deduction.
"""
REVIEW = """Review only the listed exact native contours. For each, decide
whether it is an operating front, fixed side, open shelf, frame, or space.
Compare plan, clean elevations and axonometric. A tall profile on an elevation
that faces a different wing can be the side of a cabinet with its actual
fronts on the other elevation. Identify the visual sign that supports movement.
On an elevated row, a short wide closed panel can lift up, but a tall front
cannot be identified as lift-up from its location. A stack of horizontal
moving panels can be drawers. Distinguish an open shelf interior from a closed
front and distinguish a vertical door from a side or an end filler. Use
unresolved_front when evidence conflicts. Return exactly one decision per
supplied ID and no other contours. Use at most five words of visual evidence
per decision. Identify a worktop separately when visible."""
REVIEW_ROLES = ("hinged_door", "lift_up", "drawer", "mirror", "fixed_surface",
                "fixed_open_shelf", "unresolved_front")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def payload(value):
    return {"type": "text", "text": json.dumps(value, ensure_ascii=False, separators=(",", ":"))}


def provider_request(system, content, *, model="claude-sonnet-4-6", max_tokens=4000):
    return {"model": model, "max_tokens": max_tokens, "thinking": {"type": "disabled"},
            "output_config": {"effort": "medium"}, "system": system,
            "messages": [{"role": "user", "content": content}]}


def provider(output, source_hash, *, resume=False):
    def invoke(stage, request, validate):
        path = output / f"{stage}.json"
        if not (resume and path.exists()):
            execute_request(request, path, bind=validate, source_hash=source_hash)
        else:
            saved = read_json(path)
            if saved["provider_request"] != request or saved["source_request_sha256"] != source_hash:
                raise ValueError(f"{stage}: cannot resume a different request")
        result = read_json(path)
        if resume and "model_readings" in result and result.get("stop_reason") == "end_turn":
            return validate(result["model_readings"])
        if "bound_fronts" not in result:
            raise RuntimeError(f"{stage}: {result.get('error', 'missing provider result')}")
        return result["bound_fronts"]
    return invoke


def island_content(request, views):
    content = request["messages"][0]["content"]
    result = {}
    for vid in views:
        index = next(i for i, block in enumerate(content)
                     if block.get("text", "").startswith(f"{vid}: clean crop"))
        mapped = content[index + 2:index + 4]
        result[vid] = content[index:index + 2]
        if mapped and mapped[0].get("text", "").startswith(f"{vid}: same crop"):
            result[vid].extend(mapped)
    return result


def classify_islands(invoke, views, images, detection, *, include_worktop_cutouts=False, inputs=()):
    by_object = {}
    for vid, view in views.items():
        by_object.setdefault(view["object_id"], []).append(vid)
    context = {"objects": by_object, "projections": sorted(PROJECTIONS),
               "detection": detection}
    notes = {}
    if include_worktop_cutouts:
        from use_cases.estimation_cb_geometry_parts import (
            SOLID_WOOD, VENEERED_MDF, VISIBLE_GRAIN_ROLES, is_explicit_solid_wood_note,
        )
        from use_cases.price_source_taxonomy import material_rule_for_text

        for row in inputs:
            data = row["input_payload"]
            oid = data["object"]["object_id"]
            if oid not in by_object:
                continue
            evidence = data["evidence"]
            for block in (*evidence.get("ocr_blocks", ()), *evidence.get("ocr_literal_items", ())):
                if not block.get("block_ref"):
                    continue
                lines = []
                for line in block["text"].splitlines():
                    if is_explicit_solid_wood_note(line) or (
                            (rule := material_rule_for_text(line)) and rule.family in {
                                "mdf", "hdf", "plywood", "particleboard", "laminated panel", "veneer",
                            }):
                        lines.append(line.strip())
                if lines:
                    notes.setdefault(oid, {})[block["block_ref"]] = lines
        context["material_notes"] = notes
    content = [payload(context)]
    for vid in images:
        content.extend(images[vid][:2])

    def bind(raw):
        if (raw["islands"].keys() != views.keys() or
                not set(raw["islands"].values()) <= PROJECTIONS or
                raw["understanding"].keys() != by_object.keys()):
            raise ValueError("Island Map must classify each input Island and object")
        if include_worktop_cutouts:
            for oid, understanding in raw["understanding"].items():
                if "finish_surfaces" in understanding:
                    supplied = understanding["finish_surfaces"]
                    understanding["finish_surfaces"] = bind_finish_surfaces(
                        supplied, {vid: views[vid] for vid in by_object[oid]},
                        VISIBLE_GRAIN_ROLES, notes.get(oid, {}),
                        is_explicit_solid_wood_note,
                    )
                    understanding["finish_surface_audit"] = {
                        "supplied": len(supplied), "accepted": len(understanding["finish_surfaces"]),
                        "limit": MAX_FINISH_SURFACES,
                    }
                if "wood_grain" not in understanding:
                    continue
                cues = understanding["wood_grain"]
                accepted = []
                for cue in cues if isinstance(cues, list) else ():
                    if (not isinstance(cue, dict) or not isinstance(cue.get("role"), str)
                            or cue["role"] not in VISIBLE_GRAIN_ROLES or cue.get("view_id") not in by_object[oid]
                            or not isinstance(cue.get("finish_group", ""), str)
                            or cue.get("material", VENEERED_MDF) not in (VENEERED_MDF, SOLID_WOOD)):
                        continue
                    bound = {key: cue[key] for key in ("role", "view_id", "finish_group", "material") if key in cue}
                    if cue.get("material") == SOLID_WOOD:
                        ref, quote = cue.get("source_ref"), cue.get("source_quote")
                        if (not isinstance(ref, str) or not isinstance(quote, str) or not is_explicit_solid_wood_note(quote)
                                or quote.strip() not in notes.get(oid, {}).get(ref, ())):
                            continue
                        bound["solid_wood_note"] = {"ref": ref, "text": quote.strip()}
                    accepted.append(bound)
                understanding["wood_grain"] = accepted
        return raw

    system = ISLAND_MAP + WORKTOP_CUTOUTS + VISIBLE_FINISH if include_worktop_cutouts else ISLAND_MAP
    max_tokens = min(3000 + 2000 * len(by_object), 12000) if include_worktop_cutouts else 3000
    return invoke("island-map", provider_request(system, content, max_tokens=max_tokens), bind)


def bind_finish_surfaces(rows, views, roles, notes, solid_wood_note):
    if not isinstance(rows, list) or len(rows) > MAX_FINISH_SURFACES:
        raise ValueError(f"Understanding must return at most {MAX_FINISH_SURFACES} finish surfaces per object")
    accepted = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        view_id, role, finish, box = (row.get(field) for field in ("view_id", "role", "finish", "bbox_crop_1000"))
        if (not isinstance(view_id, str) or view_id not in views or not isinstance(role, str) or role not in roles
                or finish not in ("wood_grain", "plain", "unclear", "solid_wood")
                or not isinstance(box, list) or len(box) != 4
                or not all(type(v) in (int, float) and isfinite(v) and 0 <= v <= 1000 for v in box)
                or box[0] >= box[2] or box[1] >= box[3]):
            continue
        group, evidence = row.get("finish_group", ""), row.get("evidence")
        if not isinstance(group, str) or not isinstance(evidence, str) or not evidence.strip():
            continue
        bound = {"view_id": view_id, "role": role, "finish": finish, "bbox_crop_1000": box,
                 "evidence": evidence, "finish_group": group}
        view = views[view_id]
        if view.get("width") and view.get("height"):
            candidates = [candidate["id"] for candidate in view.get("candidates", ())
                          if _finish_surface_matches(box, candidate["bbox"], view["width"], view["height"])]
            if len(candidates) == 1:
                bound["contour_ref"] = f"{view_id}:{candidates[0]}"
        if finish == "solid_wood":
            ref, quote = row.get("source_ref"), row.get("source_quote")
            if (not isinstance(ref, str) or not isinstance(quote, str) or not solid_wood_note(quote)
                    or quote.strip() not in notes.get(ref, ())):
                continue
            bound["solid_wood_note"] = {"ref": ref, "text": quote.strip()}
        accepted.append(bound)
    return accepted


def _finish_surface_matches(box, candidate, width, height):
    x0, y0, x1, y1 = box
    l, t, r, b = (1000 * value / axis for value, axis in zip(candidate, (width, height, width, height), strict=True))
    intersection = max(0, min(r, x1) - max(l, x0)) * max(0, min(b, y1) - max(t, y0))
    union = (r - l) * (b - t) + (x1 - x0) * (y1 - y0) - intersection
    return union > 0 and intersection / union >= .65


def write_finish_overlays(understanding, images, output):
    by_view = {}
    for obj in understanding.values():
        for surface in obj.get("finish_surfaces", ()):
            by_view.setdefault(surface["view_id"], []).append(surface)
    if not by_view:
        return
    folder = output / "finish-overlays"
    folder.mkdir(exist_ok=True)
    colours = {"wood_grain": "#8051b1", "plain": "#167083", "unclear": "#ae5d16", "solid_wood": "#65792d"}
    legend = {}
    for view_id, surfaces in by_view.items():
        crop = Image.open(BytesIO(b64decode(images[view_id][1]["source"]["data"]))).convert("RGB")
        draw = ImageDraw.Draw(crop)
        for index, surface in enumerate(surfaces, 1):
            coords = tuple(round(value * (crop.width if axis % 2 == 0 else crop.height) / 1000)
                           for axis, value in enumerate(surface["bbox_crop_1000"]))
            colour = colours[surface["finish"]]
            draw.rectangle(coords, outline=colour, width=max(2, crop.width // 350))
            draw.text((coords[0] + 3, coords[1] + 3), str(index), fill="white", stroke_width=2, stroke_fill=colour)
        crop.save(folder / f"{view_id}.png")
        legend[view_id] = [{"label": index, **surface} for index, surface in enumerate(surfaces, 1)]
    (folder / "legend.json").write_text(json.dumps(legend, ensure_ascii=False, indent=2) + "\n")


def bind_source_front(raw, frames):
    """Normalize an explicit origin-and-size pixel box without changing native bindings."""
    records = []
    for row in raw["faces"]:
        box = row.get("bbox_px")
        if isinstance(box, dict):
            if set(box) == {"x", "y", "w", "h"} and all(type(v) in (int, float) for v in box.values()):
                x, y, width, height = (box[key] for key in ("x", "y", "w", "h"))
                box = [x, y, x + width, y + height]
            else:
                box = None
        records.append({**row, "bbox_px": box})
    return bind_island_faces({**raw, "faces": records}, frames)


def run_initial(geometry, key, source, output, *, resume=False, request_provider=None, component_pdf=None):
    audit_path = geometry / "estimation-offline-all-islands-evidence.json"
    views = {row["view_id"]: row for row in read_json(audit_path)["documents"][key]}
    request, frames, source_hash = prepare(geometry, key, source_review=True)
    images = island_content(request, views)
    invoke = request_provider or provider(output, source_hash, resume=resume)
    with ThreadPoolExecutor(max_workers=3) as pool:
        map_call = pool.submit(classify_islands, invoke, views, images, source["detection_context"],
                               include_worktop_cutouts=component_pdf is not None, inputs=source.get("inputs", ()))
        if any(not any(view["arrows"] and oblique_evidence(view)
                       for view in views.values() if view["object_id"] == oid)
               for oid in {view["object_id"] for view in views.values()}):
            front_call = pool.submit(invoke, "front", request, lambda raw: bind_source_front(raw, frames))
        else:
            front_call = None
        component_call = None
        if component_pdf is not None:
            from tools.estimation_v9_source_review import read_front_components

            captions = {}
            with pymupdf.open(component_pdf) as pdf:
                for vid, view in views.items():
                    leaders = {ident: leader for ident, leader in leader_packet(view).items()
                               if len(leader["tips"]) >= 2 or any(
                                   all(abs(a - b) > 3 for a, b in zip(leader["root_px"], tip["xy_px"]))
                                   for tip in leader["tips"])}
                    if leaders and (caption := render_caption_image(pdf[view["page"] - 1], view, leaders)):
                        captions[vid] = caption, leaders
            component_call = pool.submit(read_front_components, invoke, views, images, provider_request, payload,
                                         captions=captions, image_block=image_block)
        island_map = map_call.result()
        front = front_call.result()["faces"] if front_call else []
        observations, review = None, None
        if component_call:
            try:
                observations = component_call.result()
                review = {"status": "reviewed", "finding_count": len(observations)}
            except (RuntimeError, ValueError) as exc:
                observations = []
                review = {"status": "review_failed", "error": str(exc)}
    return views, frames, images, invoke, island_map, front, source_hash, observations, review


EXPLICIT_FRONT = """Read the actual printed callouts and their leaders on this
furniture drawing. List only physically indicated drawers, pull-out shelves
and mirrors. Follow each relevant callout to all its own arrow tips. The
supplied leader candidates are neutral and may include unrelated labels.
Identify which contour actually belongs to the named item. A mirror may also
be identified from a direct printed label inside the face. Exclude any item
if you cannot connect it to its specific printed label. Use the clean image
and its matching C IDs. Return independent exact contour IDs and no count.
Return JSON only:
{"faces":[{"view_id":"the supplied view ID","candidate_id":"Cxx","bbox_px":null,
"role":"drawer | pull_out_shelf | mirror","evidence":"printed label and arrow or direct label"}]}"""


def structural_front(views, projections, front, detection, *, frame_pairs, supported_tops=None):
    """Keep repeated frame cells and a supported extension's side profile out of Front."""
    from tools.probe_cb_block_boundaries import (
        box_area, drawer_frame, encloses, supported_extensions,
    )
    from tools.probe_estimation_v8_grounded_front import linked_support_faces

    fixed = {(appearance["view_id"], cid) for pair in frame_pairs for appearance in pair
             for cid in (*appearance["opening_contours"], appearance["frame"])}

    banks = {vid: frame for vid, view in views.items() if (frame := drawer_frame(view, front))}
    drawer_objects = {views[vid]["object_id"] for vid in banks}
    for obj in detection["objects"]:
        own = {vid: view for vid, view in views.items() if view["object_id"] == obj["object_id"]}
        extensions = (supported_tops or {}).get(obj["object_id"])
        legs = linked_support_faces(own, projections, obj["accepted_observations"],
                                    extensions=extensions, frame_pairs=frame_pairs)
        if not legs:
            continue
        leg_view = legs[0]["view_id"]
        opposite = {b["view_id"] if a["view_id"] == leg_view else a["view_id"]
                    for a, b in frame_pairs if leg_view in (a["view_id"], b["view_id"])}
        if not (opposite & banks.keys()):
            continue
        under = min(row["bbox_px"][1] for row in legs)
        floor = max(row["bbox_px"][3] for row in legs)
        leg_ids = {row["candidate_id"] for row in legs}
        for candidate in own[leg_view]["candidates"]:
            x0, y0, x1, y1 = candidate["bbox"]
            if (candidate["id"] not in leg_ids and y0 >= under - .1 * (floor - under)
                    and y1 <= floor + 2 and y1 - y0 >= .5 * (floor - under)
                    and any(min(abs(x0 - row["bbox_px"][2]), abs(x1 - row["bbox_px"][0])) <= 2
                            for row in legs)):
                fixed.add((leg_view, candidate["id"]))

    fronts_by_view = {}
    operating = {"hinged_door", "drawer", "lift_up", "pull_out_shelf"}
    for vid, view in views.items():
        if projections[vid] not in ELEVATION_PROJECTIONS:
            continue
        operating_ids = {row["candidate_id"] for row in front if row["view_id"] == vid and row["role"] in operating}
        fronts = [row for row in view["candidates"] if row["id"] in operating_ids and (vid, row["id"]) not in fixed]
        fronts_by_view[vid] = fronts
        fixed.update((vid, row["id"]) for row in view["candidates"]
                     if row["area"] <= .55 * box_area(row["bbox"]) and
                     sum(encloses(row["bbox"], candidate["bbox"]) for candidate in fronts) >= 2)
    native_front_objects = {views[vid]["object_id"] for vid, rows in fronts_by_view.items() if len(rows) >= 2}
    for vid, view in views.items():
        if projections[vid] != "Side view" or view["object_id"] not in drawer_objects:
            continue
        for ext in supported_extensions(view):
            side = next(row for row in view["candidates"] if row["id"] == ext["attached_side"])["bbox"]
            fixed.update((vid, row["id"]) for row in view["candidates"]
                         if abs(row["bbox"][2] - side[2]) <= 2 and abs(row["bbox"][1] - side[3]) <= 2
                         and row["bbox"][0] >= side[0] - 2)
    retained, audit = [], []
    for row in front:
        key = (row["view_id"], row["candidate_id"])
        if key in fixed and row["role"] != "support_leg":
            audit.append({**row, "reason": "native matched frame bay or side projection of the drawer assembly"})
        elif (projections[row["view_id"]] == AXONOMETRIC
              and views[row["view_id"]]["object_id"] in native_front_objects):
            audit.append({**row, "reason": "pictorial appearance only; use native operating faces on linked elevations"})
        else:
            retained.append(row)
    return retained, audit


def frame_opening_evidence(pdf, views, projections, component_observations):
    from tools.probe_cb_block_boundaries import framed_panel_appearances
    from use_cases.estimation_v9_inventory import _overlap, page_box

    protected = set()
    for vid, view in views.items():
        if (projections[vid] not in ELEVATION_PROJECTIONS | {"Detail"}
                or not framed_panel_appearances(view)):
            continue
        _, strokes = thin_strokes(pdf[view["page"] - 1], view)
        protected.update((vid, row["id"]) for row in view["candidates"] if mark_on_face(row, strokes))
        protected.update((vid, cid) for mark in view.get("x_marks", ()) for cid in mark["leaf_candidates"])
        for finding in component_observations or ():
            source = finding["source"]
            if source["view_id"] != vid or not source.get("bbox_normalized"):
                continue
            if finding["role"] in {"door_with_pull", "door_without_handle"}:
                matches = [row["id"] for row in view["candidates"] if _overlap(
                    source["bbox_normalized"], page_box(row["bbox"], view, size=(view["width"], view["height"]))) >= .65]
                if len(matches) == 1 and (finding["role"] == "door_with_pull" or any(
                        set(tip["contours"]) == set(matches) for tip in source.get("tips", ()))):
                    protected.add((vid, matches[0]))
    return protected


def corroborate_supported_tops(pdf, views, projections, front, detection):
    from tools.estimation_block_geometry import source_printed_spans
    from tools.probe_cb_block_boundaries import drawer_frame, supported_extensions, supported_top_witnesses

    result = {}
    for obj in detection["objects"]:
        oid = obj["object_id"]
        own = {vid: view for vid, view in views.items() if view["object_id"] == oid}
        local = {vid: projections[vid] for vid in own}
        direct = supported_top_witnesses(own, local, front, obj["accepted_observations"], {})
        if direct:
            if len(direct) == 1:
                result[oid] = direct
            continue
        if (not any(local[vid] == "Side view" and supported_extensions(view) for vid, view in own.items())
                or not any(local[vid] in ELEVATION_PROJECTIONS and drawer_frame(view, front)
                           for vid, view in own.items())
                or not any(kind == "Top view" for kind in local.values())):
            continue
        measurable = {vid: view for vid, view in own.items()
                      if local[vid] in ELEVATION_PROJECTIONS | {"Top view"}}
        printed = source_printed_spans(pdf, measurable, obj)
        matches = supported_top_witnesses(own, local, front, obj["accepted_observations"], printed)
        if matches:
            result[oid] = matches
    return result


def stack_and_profiles(views, projections, detection, front):
    """Anchor competing orthographic profiles to a plan-matched column."""
    from tools.probe_cb_block_boundaries import (
        ORTHOGRAPHIC_PLAN_LINK_TYPES, axis_overlap, front_positions, plan_span_matches, rectangular,
    )

    protected, corrections = set(), []
    rows = {(row["view_id"], row["candidate_id"]): row for row in front}
    for obj in detection["objects"]:
        for relation in obj["accepted_observations"]:
            if relation["evidence_type"] not in ORTHOGRAPHIC_PLAN_LINK_TYPES:
                continue
            first, second = relation["group_id_a"], relation["group_id_b"]
            for plan, elevation in ((first, second), (second, first)):
                if projections.get(plan) != "Top view" or projections.get(elevation) not in ELEVATION_PROJECTIONS:
                    continue
                if not views[plan]["candidates"]:
                    continue
                source = views[elevation]["candidates"]
                panel_rows = [row for row in source if rectangular(row) and
                              .20 <= (row["bbox"][3] - row["bbox"][1]) / (row["bbox"][2] - row["bbox"][0]) <= 2.6]
                for position in front_positions(panel_rows):
                    x0, y0, x1, y1 = position["bbox"]
                    members = [r["id"] for r in position["faces"]]
                    if (len(members) < 3 or y1 - y0 < 2.5 * (x1 - x0)
                            or not plan_span_matches(position["bbox"], views[elevation], views[plan])
                            or sum(rows.get((elevation, ident), {}).get("role") == "drawer" for ident in members) < 2):
                        continue
                    protected.update((elevation, ident) for ident in members)
                    for panel in position["faces"]:
                        ident = panel["id"]
                        role = rows.get((elevation, ident), {}).get("role")
                        left, top, right, bottom = panel["bbox"]
                        if role == "unresolved_front" and bottom - top >= .95 * (right - left):
                            corrections.append({
                                "view_id": elevation, "candidate_id": ident, "role": "hinged_door",
                                "evidence": "operating panel in a plan-matched column; hinged is inferred from its "
                                            "closed tall face and alignment with adjacent cabinet fronts",
                                "role_basis": "inferred hinge type; no opening hardware mark",
                            })
                    for vid, view in views.items():
                        if (view["object_id"] != obj["object_id"] or vid == elevation
                                or projections[vid] not in ELEVATION_PROJECTIONS):
                            continue
                        profiles = sorted((r for r in view["candidates"]
                                           if r["bbox"][3] - r["bbox"][1] >= .85 * (y1 - y0) * view["height"] / views[elevation]["height"]
                                           and r["bbox"][3] - r["bbox"][1] >= 4 * (r["bbox"][2] - r["bbox"][0])),
                                          key=lambda r: r["bbox"][0])
                        for a, b in zip(profiles, profiles[1:]):
                            ab, bb = a["bbox"], b["bbox"]
                            if abs(ab[2] - bb[0]) > 3 or axis_overlap(ab, bb, 1) < .97:
                                continue
                            wide, narrow = sorted((a, b), key=lambda r: r["bbox"][0] - r["bbox"][2])
                            if wide["bbox"][2] - wide["bbox"][0] < 1.5 * (narrow["bbox"][2] - narrow["bbox"][0]):
                                continue
                            corrections.extend([
                                {"view_id": vid, "candidate_id": wide["id"], "role": "fixed_surface",
                                 "evidence": "wide matching-height secondary profile of a plan-linked primary stack"},
                                {"view_id": vid, "candidate_id": narrow["id"], "role": "unresolved_front",
                                 "evidence": "narrow adjacent profile with no separate opening evidence"},
                            ])
    return protected, corrections


def review_elevations(invoke, views, frames, images, projections, front, protected, corrections, *, audit):
    candidates, content = [], []
    covered = {(row["view_id"], row["candidate_id"]) for row in corrections} | protected
    for vid in views:
        if projections[vid] in ELEVATION_PROJECTIONS:
            faces = [row for row in front if row["view_id"] == vid and row["candidate_id"]
                     and row["role"] in {"hinged_door", "unresolved_front", "lift_up"}
                     and (vid, row["candidate_id"]) not in covered]
            for face in faces:
                candidates.append({key: face[key] for key in ("view_id", "candidate_id", "bbox_px")})
    if not candidates:
        return corrections, []
    keys = {(face["view_id"], face["candidate_id"]) for face in candidates}
    by_id = {f"{vid}:{cid}": (vid, cid) for vid, cid in sorted(keys)}
    candidate_views = {vid for vid, _ in keys}
    object_ids = {views[vid]["object_id"] for vid in candidate_views}
    for vid, view in views.items():
        if view["object_id"] in object_ids:
            content.extend(images[vid] if vid in candidate_views else images[vid][:2])
    content.append(payload({"review_candidates": [
        {"id": f'{face["view_id"]}:{face["candidate_id"]}', "bbox_px": face["bbox_px"]}
        for face in candidates
    ]}))

    decision = {"id": {"type": "string", "enum": list(by_id)},
                "role": {"type": "string", "enum": list(REVIEW_ROLES)},
                "evidence": {"type": "string"}}
    fields = {"review": {"type": "array", "items": {
        "type": "object", "properties": decision, "required": list(decision), "additionalProperties": False}},
        "worktop_view_id": {"anyOf": [{"type": "string", "enum": sorted(
            vid for vid, view in views.items() if view["object_id"] in object_ids)}, {"type": "null"}]}}
    params = provider_request(REVIEW, content, max_tokens=min(8000, max(600, 36 * len(by_id) + 100)))
    params["output_config"]["format"] = {"type": "json_schema", "schema": {
        "type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}}

    def bind(raw):
        if not isinstance(raw.get("review"), list):
            raise ValueError("Front role review must return a list")
        rows = [row for row in raw["review"] if isinstance(row, dict) and isinstance(row.get("id"), str)]
        counts = Counter(row["id"] for row in rows)
        accepted = []
        for row in rows:
            ident = row["id"]
            if (ident in by_id and counts[ident] == 1 and row.get("role") in REVIEW_ROLES
                    and isinstance(row.get("evidence"), str) and row["evidence"].strip()):
                view_id, candidate_id = by_id[ident]
                accepted.append({"view_id": view_id, "candidate_id": candidate_id,
                                 "role": row["role"], "evidence": row["evidence"]})
        vid = raw.get("worktop_view_id")
        return accepted, vid if isinstance(vid, str) and vid in frames and views[vid]["object_id"] in object_ids else None

    try:
        reviewed, vid = invoke("front-role-review", params, bind)
    except (RuntimeError, ValueError):
        reviewed, vid = [], None
    confirmed = {(row["view_id"], row["candidate_id"]) for row in reviewed}
    audit.extend({"view_id": view_id, "candidate_id": candidate_id, "reason": "front_role_review_pending"}
                 for view_id, candidate_id in sorted(keys - confirmed))
    features = ([{"role": "worktop", "id": "worktop", "view_id": vid,
                  "quantity": 1, "status": "recognized, full outline unresolved"}] if vid else [])
    return reviewed + corrections, features


def leader_packet(view):
    return {f"A{i:02}": {"root_px": list(map(round, row["root"])), "tips": [
        {"xy_px": list(map(round, tip["xy"])), "contours": tip["hits"]} for tip in row["tips"]
    ]} for i, row in enumerate(view["arrows"], 1)}


def typed_map(view, clean, leaders):
    with Image.open(BytesIO(clean)) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=15)
    used = set()
    for face in sorted(view["candidates"], key=lambda row: row["area"]):
        left, top, right, bottom = face["bbox"]
        x, y = round((left + right) / 2), round((top + bottom) / 2)
        if right - left < 13 or bottom - top < 10 or (x // 14, y // 13) in used:
            continue
        used.add((x // 14, y // 13))
        polygon = [tuple(point) for point in face["polygon"]]
        draw.line(polygon + polygon[:1], fill="#7ab5c4", width=1)
        draw.text((x, y), face["id"], anchor="mm", font=font, fill="#163847",
                  stroke_width=2, stroke_fill="white")
    for ident, group in leaders.items():
        root = tuple(group["root_px"])
        for tip in group["tips"]:
            end = tuple(tip["xy_px"])
            draw.line((root, end), fill="#9084be", width=1)
            draw.ellipse((end[0] - 2, end[1] - 2, end[0] + 2, end[1] + 2), outline="#7349a1")
        draw.text(root, ident, font=font, fill="#48267a", stroke_width=2, stroke_fill="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return image_block(buffer.getvalue())


def read_marked(invoke, view, page, images, marks):
    from use_cases.estimation_cb_parts_coverage import retained_component_callouts

    vid = view["view_id"]
    leaders = leader_packet(view)
    strokes = {row["candidate_id"]: {"side": row["apex_side_on_view"], "rays_px": row["rays_px"]}
               for row in marks}
    clean = images[vid][1]
    mapped = typed_map(view, b64decode(clean["source"]["data"]), leaders)
    contours = {row["id"]: row["bbox"] for row in view["candidates"]}
    context = {"view_id": vid, "leader_groups": leaders, "side_stroke_pairs": strokes}
    content = [{"type": "text", "text": "Clean source view."}, clean,
               {"type": "text", "text": "Same view with geometry IDs."}, mapped, payload(context)]
    if captions := render_caption_image(page, view, leaders):
        content.extend([
            {"type": "text", "text": "Indexed source-caption crops. Read the printed label beside each A ID here."},
            image_block(captions),
        ])
    content.extend([
        {"type": "text", "text": "Use these isolated native contours and stroke pairs for stroke_readings. Each tile is one C contour."},
        image_block(render_stroke_image(view, strokes)),
    ])

    def bind(raw):
        if {r["id"] for r in raw["leader_readings"]} != leaders.keys():
            raise ValueError("marked Front missed a leader reading")
        bound = bind_front_roles(raw, leaders=leaders, contours=contours, stroke_ids=strokes)
        return {"readings": raw, "items": bound["items"], "issues": bound["issues"],
                "marks": marks, "leaders": leaders}

    result = invoke(f"marked-{vid}", provider_request(TYPED_FRONT, content, model="claude-haiku-5-5",
                                                     max_tokens=2500), bind)
    features = retained_component_callouts(vid, result["readings"], leaders)
    for annotation in result["readings"]["leader_readings"]:
        if annotation["role"] != "cover" or not annotation["source_text"]:
            continue
        aid = annotation["id"]
        tips = leaders[aid]["tips"]
        if len(tips) == 1 and (outline := isolated_callout_outline(page, view, tips[0]["xy_px"])):
            features.append({**outline, "id": f"closure-{aid}", "annotation": aid,
                             "view_id": vid, "role": "window_closure"})
    return result, features


def read_labelled(invoke, view, frame, images):
    vid = view["view_id"]
    content = images[vid] + [payload({"view_id": vid, "neutral_leader_candidates": view["arrows"]})]
    return invoke(f"labelled-{vid}", provider_request(EXPLICIT_FRONT, content, max_tokens=2500),
                  lambda raw: bind_island_faces(raw, {vid: frame}))["faces"]


def oblique_evidence(view):
    total, oblique = 0, 0
    for face in view["candidates"]:
        polygon = face["polygon"]
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            length = hypot(dx, dy)
            if length <= 30:
                continue
            total += length
            if dx >= 15 and .025 <= dy / dx <= 2:
                oblique += length
    return total > 0 and oblique >= .28 * total


def source_routes(pdf, views, projections):
    by_object = {}
    for vid, view in views.items():
        by_object.setdefault(view["object_id"], []).append(view)
    routes = {}
    for oid, islands in by_object.items():
        options = []
        for view in islands:
            vid = view["view_id"]
            if not view["arrows"] or not (projections[vid] == AXONOMETRIC or oblique_evidence(view)):
                continue
            _, strokes = thin_strokes(pdf[view["page"] - 1], view)
            marks = [mark for candidate in view["candidates"] if (mark := mark_on_face(candidate, strokes))]
            unique_leaders = sum(any(len(tip["hits"]) == 1 for tip in group["tips"]) for group in view["arrows"])
            if marks or unique_leaders >= 2:
                options.append((len(marks), unique_leaders, vid, marks))
        if options:
            _, _, vid, marks = max(options)
            routes[oid] = (vid, marks)
    return routes


def find_front_and_blocks(pdf, views, frames, images, invoke, island_map, front, detection,
                          *, component_observations=None):
    from tools.probe_cb_block_boundaries import matched_frame_pairs

    projections = island_map["islands"]
    routes = source_routes(pdf, views, projections)
    for vid, _ in routes.values():
        if oblique_evidence(views[vid]):
            projections[vid] = AXONOMETRIC
    frame_pairs = matched_frame_pairs(views, projections,
                                      frame_opening_evidence(pdf, views, projections, component_observations))
    supported_tops = corroborate_supported_tops(pdf, views, projections, front, detection)
    front, audit = structural_front(views, projections, front, detection, frame_pairs=frame_pairs,
                                   supported_tops=supported_tops)
    protected, corrections = stack_and_profiles(views, projections, detection, front)
    present = {(row["view_id"], row["candidate_id"]) for row in front}
    for row in corrections:
        key = row["view_id"], row["candidate_id"]
        if row["role"] == "unresolved_front" and key not in present:
            view = views[row["view_id"]]
            contour = next(candidate for candidate in view["candidates"] if candidate["id"] == row["candidate_id"])
            front.append({**row, "bbox_px": contour["bbox"]})
            present.add(key)
    marked, labelled = {}, {}
    features, review = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        reviews = pool.submit(review_elevations, invoke, views, frames, images, projections, front,
                              protected, corrections, audit=audit)
        calls = {}
        for vid, marks in routes.values():
            view = views[vid]
            if marks:
                # PyMuPDF page extraction is kept on the caller thread.
                marked[vid], additions = read_marked(invoke, view, pdf[view["page"] - 1], images, marks)
                features.extend(additions)
            else:
                calls[vid] = pool.submit(read_labelled, invoke, view, frames[vid], images)
        for vid, future in calls.items():
            rows = future.result()
            if any(row["role"] in {"drawer", "pull_out_shelf"} for row in rows):
                labelled[vid] = rows
        review, additions = reviews.result()
        features.extend(additions)
    objects = assemble_native_front_blocks(
        views=views, projections=projections, detection=detection, faces=front, review=review,
        marked_sources=marked, labelled_sources=labelled, object_features=features,
        component_observations=component_observations, frame_pairs=frame_pairs, supported_tops=supported_tops,
    )
    for oid, obj in objects.items():
        front_result = obj["front"]
        if component_observations is not None:
            front_result["typed_leaders"] = {vid: source["readings"]["leader_readings"]
                                              for vid, source in marked.items() if views[vid]["object_id"] == oid}
        front_result["audit"].extend(row for row in audit if views[row["view_id"]]["object_id"] == oid)
        inference = {(row["view_id"], row["candidate_id"]): row["role_basis"]
                     for row in corrections if row.get("role_basis")}
        for face in front_result["faces"]:
            key = face["view_id"], face["candidate_id"]
            if key in inference:
                face["role_basis"] = inference[key]
        counts = Counter(row["role"] for row in front_result["faces"])
        supports = Counter(row["view_id"] for row in front_result["faces"] if row["role"] == "support_leg")
        if supports:
            counts["support_leg"] = max(supports.values())
        front_result["instance_counts"] = dict(counts)
        front_result["support_appearance_counts_by_view"] = dict(supports)
        if not obj["planner"]["blocks"]:
            obj["planner"]["coverage_status"] = "unresolved_no_source_grounded_blocks"
    return objects


def main(*, version="8.3"):
    v9 = version == "9"
    parser = argparse.ArgumentParser(description=f"Experimental Estimation {version}")
    parser.add_argument("--geometry", type=Path, help="Reuse a verified source-only native geometry packet")
    parser.add_argument("--key", required=True, help="Document key in the source geometry packet")
    parser.add_argument("--source", type=Path, required=True, help="Saved Detection input context")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--block-geometry", action="store_true",
                        help="Resolve orthographic dimensions after Analyze locks Blocks")
    parser.add_argument(*(["--parts", "--cb-parts"] if v9 else ["--cb-parts"]), dest="cb_parts", action="store_true",
                        help="Compile a preliminary cut list from Block Geometry and native evidence")
    if v9:
        parser.add_argument("--parts-profile", type=Path, help="Reviewed construction and source references")
        parser.add_argument("--saved-dimension-inventory", type=Path,
                            help="Replay local OCR from a saved Block Geometry report for the same source")
    parser.add_argument("--material-context", type=Path,
                        help="Calculate the CB Parts using a saved tenant catalog context")
    parser.add_argument("--dimension-reader", type=Path, help="Local OCR executable for missing dimension evidence")
    parser.add_argument("--dimension-unit", choices=("mm", "cm"), help="Assumed unit for local dimension OCR")
    args = parser.parse_args()
    if args.cb_parts and not args.block_geometry:
        parser.error("--cb-parts requires --block-geometry")
    if v9 and args.parts_profile and not args.cb_parts:
        parser.error("--parts-profile requires --parts")
    saved_dimensions = args.saved_dimension_inventory if v9 else None
    if saved_dimensions and (args.dimension_reader or not args.block_geometry):
        parser.error("--saved-dimension-inventory requires --block-geometry and replaces the local OCR call")
    if args.material_context and not args.cb_parts:
        parser.error("--material-context requires --cb-parts")
    if bool(args.dimension_reader) != bool(args.dimension_unit) or (args.dimension_reader and not args.block_geometry):
        parser.error("Local dimension OCR requires --block-geometry, --dimension-reader and --dimension-unit")
    source = read_json(args.source)
    if args.material_context and not source.get("inputs"):
        parser.error("Material calculation requires saved immutable object inputs")
    result = run_pipeline(args, source, version=version)
    for oid, obj in result["objects"].items():
        print(oid, obj["front"]["instance_counts"], len(obj["planner"]["blocks"]))


def _write_inventory_check(output, inventory, page_reviews):
    (output / "inventory-check.json").write_text(
        json.dumps({"stage": "Inventory Check", "source_audit_sha256": inventory["source_audit_sha256"],
                    "status": inventory["source_coverage"], "sheets": page_reviews,
                    "objects": {oid: [row for row in obj["source_review_findings"]
                                      if row["kind"] == "inventory_check"]
                                for oid, obj in inventory["objects"].items()},
                    "unassigned_findings": [row for row in inventory["unassigned_source_findings"]
                                            if row["stage"] == "inventory_check"]},
                   ensure_ascii=False, indent=2) + "\n")


def run_pipeline(args, source, *, version, request_provider=None):
    v9 = version == "9"
    saved_dimensions = args.saved_dimension_inventory if v9 else None
    if v9:
        from tools.estimation_v9_source_review import review_original_sheets
        from use_cases.estimation_shelf_recovery import recover_fixed_shelves
        from use_cases.estimation_v9_inventory import (
            add_inventory_geometry, apply_source_findings, bind_native_components, check_inventory, check_parts,
            include_standalone_parts_scopes, refresh_source_coverage,
        )

    args.output.mkdir(parents=True, exist_ok=args.resume)
    detection = source.get("detection_context", source)
    geometry = args.geometry or args.output / "geometry"
    if args.geometry is None and not (args.resume and geometry.is_dir()):
        extract_islands(args.pdf, detection, geometry, args.key)
    packet = read_json(geometry / "estimation-offline-all-islands-evidence.json")
    if packet["source_sha256"][args.key] != sha256(args.pdf.read_bytes()).hexdigest():
        raise ValueError("Geometry packet belongs to a different PDF")
    views, frames, images, invoke, island_map, front, source_hash, component_observations, front_review = run_initial(
        geometry, args.key, {"detection_context": detection, "inputs": source.get("inputs", ())},
        args.output, resume=args.resume,
        request_provider=request_provider, component_pdf=args.pdf if v9 else None)
    with pymupdf.open(args.pdf) as pdf:
        page_count = len(pdf)
        objects = find_front_and_blocks(pdf, views, frames, images, invoke, island_map, front, detection,
                                       component_observations=component_observations)
    native_locator(objects, views, images, frames, invoke, provider_request, payload)
    raster_locator(objects, views, island_map["islands"], images, invoke, provider_request, payload)
    result = {**island_map, "version": version, "objects": objects, "source_audit_sha256": source_hash}
    if v9:
        write_finish_overlays(result["understanding"], images, args.output)
    from use_cases.estimation_object_inventory import build_object_inventory, reconcile_object_inventory

    inventory = build_object_inventory(result, views.values(), page_count=page_count)
    if v9:
        bind_native_components(inventory, result)
        inventory["front_component_review"] = front_review
        front_findings = [finding for obj in objects.values() for finding in obj["front"]["components"]]
        apply_source_findings(inventory, views.values(), front_findings)
        (args.output / "object-inventory-draft.json").write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
        with pymupdf.open(args.pdf) as pdf:
            page_reviews = review_original_sheets(pdf, invoke, provider_request, payload, image_block)
        inventory = check_inventory(inventory, views.values(), page_reviews)
        _write_inventory_check(args.output, inventory, page_reviews)
    (args.output / "object-inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    (args.output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.block_geometry:
        from tools.estimation_block_geometry import AUDIT_FILE, run_block_geometry

        measurements = run_block_geometry(
            args.pdf, geometry / AUDIT_FILE, detection, result, args.key,
            dimension_reader=args.dimension_reader, dimension_unit=args.dimension_unit,
            saved_dimension_inventory=read_json(saved_dimensions) if saved_dimensions else None,
        )
        if v9:
            from tools.estimation_worktop_geometry import bind_worktop_cutouts, worktop_geometry

            for oid, measurements_for_object in measurements["objects"].items():
                owners = result["objects"][oid]["planner"].get("object_parts", ())
                if sum(owner["role"] == "worktop" and not owner.get("envelope_block_id") for owner in owners) != 1:
                    continue
                object_views = {vid: view for vid, view in views.items() if view["object_id"] == oid}
                understanding = result["understanding"].get(oid, {})
                footprint = worktop_geometry(
                    measurements_for_object["blocks"], object_views, measurements_for_object["printed_dimensions"],
                    understanding, result["islands"],
                )
                if footprint:
                    measurements_for_object["worktop_outline"] = footprint
                cutouts = bind_worktop_cutouts(understanding.get("worktop_cutouts"), object_views, result["islands"])
                if cutouts:
                    measurements_for_object["worktop_cutouts"] = cutouts
            if not args.parts_profile:
                from use_cases.estimation_lighting_ownership import resolve_lighting_ownership

                resolve_lighting_ownership(inventory, result, measurements, views)
                refresh_source_coverage(inventory)
                (args.output / "object-inventory.json").write_text(
                    json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
                _write_inventory_check(args.output, inventory, page_reviews)
            add_inventory_geometry(measurements, inventory)
        (args.output / "block-geometry.json").write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + "\n")
        if args.cb_parts:
            from tools.estimation_geometry_parts import run_geometry_parts
            from use_cases.estimation_cb_geometry_parts import apply_sheet_layups
            from use_cases.estimation_cb_parts_coverage import audit_cb_parts_coverage

            stock_notes = None
            if v9 and not args.parts_profile:
                from use_cases.estimation_display_parts import _stock_notes

                stock_notes = _stock_notes(source.get("inputs", ()), {obj["object_id"]: obj for obj in detection["objects"]})
                stock_notes = {oid: {role: note for role, note in notes.items() if note["mm"] is not None}
                               for oid, notes in stock_notes.items()}
            parts = run_geometry_parts(geometry / AUDIT_FILE, result, measurements, args.key, stock_notes=stock_notes)
            if v9:
                include_standalone_parts_scopes(parts, inventory)
                if args.parts_profile:
                    from use_cases.estimation_display_parts import apply_reviewed_display_parts

                    apply_reviewed_display_parts(parts, inventory, result, measurements, read_json(args.parts_profile))
                else:
                    from use_cases.estimation_display_parts import add_source_casework_parts, add_source_display_glass_parts
                    from use_cases.estimation_door_hardware import add_push_latches

                    with pymupdf.open(args.pdf) as pdf:
                        add_source_casework_parts(parts, inventory, result, measurements,
                                                  input_rows=source.get("inputs", ()), detection=detection,
                                                  views=views, pdf=pdf)
                    add_source_display_glass_parts(parts, inventory, result)
                    add_push_latches(parts, result, views, source.get("inputs", ()))
                    apply_sheet_layups(parts)
            parts_filename = "parts.json" if v9 else "cb-parts.json"
            inventory_with_parts = reconcile_object_inventory(inventory, parts)
            if v9:
                coverage = check_parts(result, inventory_with_parts, parts)
                if not args.parts_profile and (repairs := recover_fixed_shelves(
                        coverage, inventory, parts, result, views,
                        lambda vid: b64decode(images[vid][1]["source"]["data"]))):
                    inventory_with_parts = reconcile_object_inventory(inventory, parts)
                    coverage = check_parts(result, inventory_with_parts, parts)
                    coverage["automatic_repairs"] = repairs
                    (args.output / "object-inventory.json").write_text(
                        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
                for oid, obj in parts["objects"].items():
                    obj["inventory_review_items"] = coverage["objects"][oid]["inventory_issues"]
                    if coverage["source_coverage"] != "reviewed":
                        obj["inventory_review_items"] = [*obj["inventory_review_items"],
                            {"reason": coverage["source_coverage"]}]
            else:
                coverage = audit_cb_parts_coverage(result, parts)
            (args.output / "object-inventory-parts.json").write_text(
                json.dumps(inventory_with_parts, ensure_ascii=False, indent=2) + "\n")
            check_filename = "parts-check.json" if v9 else "cb-parts-coverage.json"
            (args.output / parts_filename).write_text(json.dumps(parts, ensure_ascii=False, indent=2) + "\n")
            (args.output / check_filename).write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
            if args.material_context:
                from use_cases.estimation_cb_material_demand import calculate_cb_materials

                materials = calculate_cb_materials(parts_report=coverage if v9 else parts, input_rows=source["inputs"],
                                                   catalog_context=read_json(args.material_context))
                (args.output / "cb-materials.json").write_text(json.dumps(materials, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    main()
