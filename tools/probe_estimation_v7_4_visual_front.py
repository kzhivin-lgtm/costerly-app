"""Test visual Front classification on saved Islands without leader or swing evidence."""

import argparse
from base64 import b64encode
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.probe_estimation_v7_4_front_evidence import execute_request
from use_cases.estimation_detection_context_v7 import digest


ROLES = {"hinged_door", "lift_up", "drawer", "pull_out_shelf", "fixed_open_shelf",
         "mirror", "support_leg", "unresolved_front"}
VISUAL_INSTRUCTIONS = """Identify physical furniture fronts and tabletop support legs on the supplied
views of one object. Read all views together. Use the clean crops for visual
evidence and the matching cyan contour maps for geometry. Many contours are
fixed panels, infill, rims or details. A C ID alone does not identify a front.

Inspect each view for separate faces, including adjacent faces and stacked
faces. Use outlines, gaps, handles, drawing marks and construction context
to separate hinged leaves, lift-up leaves, drawers, pull-out shelves and
fixed open shelves. Require evidence of movement to call a shelf a pull-out.
Exclude fixed side panels from door counts. Use unresolved_front when a
distinct face is visible but its opening type cannot be established."""

SYSTEM = VISUAL_INSTRUCTIONS + """

Return one item per physical element. Use multiple appearances within an
item only when the same element is identifiable in more than one view.
Keep different faces separate, including across a turn in the assembly.
For each appearance, use the exact C ID if its outline matches that face.
Otherwise give a tight pixel box in the stated crop, or null if it cannot be
localized. Never substitute a nearby contour. C IDs are local to each view.
Do not return totals.

Return JSON only. Allowed roles: hinged_door, lift_up, drawer, pull_out_shelf,
fixed_open_shelf, mirror, support_leg, unresolved_front.
{"items":[{"role":"drawer","evidence":"short visible cue",
"appearances":[{"view_id":"view-xxx","candidate_id":"Cxx","bbox_px":null}]}]}
"""

PER_ISLAND_SYSTEM = VISUAL_INSTRUCTIONS + """

Record each visible face or support leg as one independent row in its own
view. Adjacent faces and stacked faces each have their own row. If the same
element appears in several views, give it a separate row in each view.
Keep each row scoped to one view_id and one visible face. Cross-view
correspondence and object totals are outside this task.

Use the exact C ID if its outline matches the face. Otherwise set
candidate_id to null and give a tight pixel box in the stated crop, or
bbox_px null if the face cannot be localized. C IDs are local to each view.

Return JSON only. Allowed roles: hinged_door, lift_up, drawer, pull_out_shelf,
fixed_open_shelf, mirror, support_leg, unresolved_front.
{"faces":[{"view_id":"view-xxx","candidate_id":"Cxx","bbox_px":null,
"role":"drawer","evidence":"short visible cue"}]}
"""


def image_block(data):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                       "data": b64encode(data).decode("ascii")}}


def contour_map(image, candidates):
    annotated = image.convert("RGB")
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default(size=14)
    labels = []
    visible = {}
    for face in sorted(candidates, key=lambda row: row["area"]):
        left, top, right, bottom = face["bbox"]
        width, height = right - left, bottom - top
        if width < 12 or height < 8 or face["area"] < .25 * width * height:
            continue
        ident = face["id"]
        text_width = round(draw.textlength(ident, font=font)) + 4
        for fraction in (.5, .25, .75):
            x = round(left + fraction * width - text_width / 2)
            y = round((top + bottom) / 2 - 8)
            box = (x, y, x + text_width, y + 16)
            if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1]
                   for b, _ in labels):
                continue
            labels.append((box, ident))
            visible[ident] = face["bbox"]
            points = [tuple(p) for p in face["polygon"]]
            draw.line(points + points[:1], fill="#85c8d8", width=1)
            break
    for box, ident in labels:
        draw.rectangle(box, fill="#e4f5f7", outline="#12778b")
        draw.text((box[0] + 2, box[1]), ident, font=font, fill="#083c47")
    buffer = BytesIO()
    annotated.save(buffer, format="PNG")
    return buffer.getvalue(), visible


def prepare(archive, document, *, per_island=False):
    audit = (archive / "estimation-offline-all-islands-evidence.json").read_bytes()
    views = json.loads(audit)["documents"][document]
    frames, content = {}, []
    for view in sorted(views, key=lambda row: row["number"]):
        ident, width, height = view["view_id"], view["width"], view["height"]
        clean = (archive / "full" / f"{document}-{view['number']:02d}.png").read_bytes()
        with Image.open(BytesIO(clean)) as image:
            if image.size != (width, height):
                raise ValueError(f"unexpected crop size for {ident}")
            overlay, visible = contour_map(image, view["candidates"])
        frames[ident] = {"size": (width, height), "contours": visible}
        content.extend([
            {"type": "text", "text": f"{ident}: clean crop, width {width}, height {height} pixels."},
            image_block(clean),
        ])
        if visible:
            content.extend([{"type": "text", "text": f"{ident}: same crop with neutral contour IDs."},
                            image_block(overlay)])
    request = {"model": "claude-haiku-5-5", "max_tokens": 14000, "thinking": {"type": "disabled"},
               "output_config": {"effort": "medium"},
               "system": PER_ISLAND_SYSTEM if per_island else SYSTEM,
               "messages": [{"role": "user", "content": content}]}
    return request, frames, sha256(audit).hexdigest()


def bind_visual_roles(readings, frames):
    items, issues, used = [], [], set()
    ambiguous_counts = False
    for index, item in enumerate(readings["items"], start=1):
        if item["role"] not in ROLES or not item["appearances"]:
            raise ValueError("invalid visual role or empty appearances")
        appearances = []
        views = set()
        for appearance in item["appearances"]:
            view_id, ident = appearance["view_id"], appearance["candidate_id"]
            if view_id in views:
                ambiguous_counts = True
                issues.append({"item": index, "view_id": view_id, "candidate_id": ident,
                               "reason": "multiple faces from one view grouped into one item"})
            views.add(view_id)
            frame = frames[view_id]
            box = appearance["bbox_px"]
            if ident is not None:
                box = frame["contours"].get(ident)
                if box is None or (view_id, ident) in used:
                    ambiguous_counts = True
                    issues.append({"view_id": view_id, "candidate_id": ident,
                                   "reason": "unknown or repeated candidate"})
                    continue
                used.add((view_id, ident))
            elif box is not None:
                width, height = frame["size"]
                if not (len(box) == 4 and 0 <= box[0] < box[2] <= width
                        and 0 <= box[1] < box[3] <= height):
                    issues.append({"view_id": view_id, "reason": "invalid crop box", "bbox_px": box})
                    box = None
            appearances.append({"view_id": view_id, "candidate_id": ident, "bbox_px": box})
        if appearances:
            items.append({"role": item["role"], "evidence": item["evidence"], "appearances": appearances})
    counts = None if ambiguous_counts else dict(Counter(item["role"] for item in items))
    return {"items": items, "counts": counts, "issues": issues}


def bind_island_faces(readings, frames):
    fields = {"view_id", "candidate_id", "bbox_px", "role", "evidence"}
    if set(readings) != {"faces"} or any(set(row) != fields for row in readings["faces"]):
        raise ValueError("expected independent Island face records")
    items = [
        {"role": row["role"], "evidence": row["evidence"],
         "appearances": [{key: row[key] for key in ("view_id", "candidate_id", "bbox_px")}]}
        for row in readings["faces"]
    ]
    bound = bind_visual_roles({"items": items}, frames)
    return {"faces": [
        {"role": item["role"], "evidence": item["evidence"], **item["appearances"][0]}
        for item in bound["items"]
    ], "issues": bound["issues"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--document", choices=("lev1", "lev2"), required=True)
    parser.add_argument("--per-island", action="store_true", help="Use the V7.5 face-per-Island probe")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    request, frames, source_hash = prepare(args.archive, args.document, per_island=args.per_island)
    if args.execute:
        if args.output is None or args.output.exists():
            parser.error("--execute requires a new --output path")
        bind = bind_island_faces if args.per_island else bind_visual_roles
        execute_request(request, args.output, bind=lambda rows: bind(rows, frames),
                        source_hash=source_hash)
    else:
        print(json.dumps({"provider_calls": 0, "request_sha256": digest(request),
                          "views": {key: len(frame["contours"]) for key, frame in frames.items()}}))


if __name__ == "__main__":
    main()
