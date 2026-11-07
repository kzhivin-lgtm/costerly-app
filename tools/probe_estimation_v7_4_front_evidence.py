"""Replay one view with model-read labels and deterministic contour ownership."""

import argparse
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
import json
from math import dist
import os
from pathlib import Path
import time
import tomllib

from use_cases.estimation_detection_context_v7 import digest


LEADER_ROLES = {
    "drawer", "pull_out_shelf", "fixed_open_shelf", "mirror", "glazed_zone",
    "lighting", "cover", "other", "unresolved",
}
TIP_BOUND_ROLES = {"drawer", "pull_out_shelf", "fixed_open_shelf"}
SWING_ROLES = {"hinged_door", "cut_or_fixed", "unresolved"}
SOURCE_NAMES = {"lev1": "Lev_1.pdf", "lev2": "Lev 2.pdf", "adda": "Adda.pdf"}
SYSTEM = """Read the clean drawing and interpret its evidence. The second image has neutral
C contour IDs and A annotation leader IDs. Return one reading for every supplied
leader group. Classify the meaning of the printed label at its origin, rather
than the shape of nearby panels. Keep pull-out shelves, drawers and fixed open
shelves distinct. Record the exact label when readable, otherwise null.

Review every supplied side-stroke pair separately on its own contour. A pair
meeting near the midpoint of one side can identify one hinged leaf. Neighboring
marks may look like an X. A corner-to-corner X within one outline can describe a
cut or continuation. Check which case the drawing supports.

The caller will attach leader readings to native tip intersections, so do not
expand a reading to any other contour. Return direct mirror labels only when
the word is printed inside the identified contour. Record a zone or a callout
at its original scope. Return no quantities.

Return JSON only, with one entry per A ID and one per supplied side-stroke C ID.
Allowed leader roles: drawer, pull_out_shelf, fixed_open_shelf, mirror,
glazed_zone, lighting, cover, other, unresolved.
Allowed stroke roles: hinged_door, cut_or_fixed, unresolved.
{"leader_readings":[{"id":"Axx","role":"drawer","source_text":"as printed"}],
"stroke_readings":[{"id":"Cxx","role":"hinged_door"}],
"direct_labels":[{"id":"Cxx","role":"mirror","source_text":"as printed"}]}"""


def _index(rows, expected, allowed_roles):
    result = {}
    for row in rows:
        ident = row["id"]
        if ident in result or ident not in expected or row["role"] not in allowed_roles:
            raise ValueError(f"invalid or repeated evidence reading: {ident}")
        result[ident] = row
    return result


def bind_front_roles(readings, *, leaders, contours, stroke_ids):
    """Only attach geometric intersections for explicit readings; expose conflicts."""
    source_reads = _index(readings["leader_readings"], leaders, LEADER_ROLES)
    swing_reads = _index(readings["stroke_readings"], stroke_ids, SWING_ROLES)
    direct_reads = _index(readings["direct_labels"], contours, {"mirror"})
    candidates = {}
    issues = []

    def attach(ident, role, evidence):
        candidates.setdefault(ident, {}).setdefault(role, []).append(evidence)

    for ident in sorted(set(leaders) - source_reads.keys()):
        issues.append({"source_id": ident, "reason": "missing leader reading"})
    for ident in sorted(set(stroke_ids) - swing_reads.keys()):
        issues.append({"source_id": ident, "reason": "missing stroke reading"})
    for ident, row in source_reads.items():
        if row["role"] not in TIP_BOUND_ROLES or not row["source_text"]:
            continue
        for tip in leaders[ident]["tips"]:
            hits = set(tip["contours"]) & contours.keys()
            if len(hits) == 1:
                attach(next(iter(hits)), row["role"], ident)
            else:
                issues.append({"source_id": ident, "tip_px": tip["xy_px"],
                               "reason": "no unique target contour"})
    for ident, row in swing_reads.items():
        if row["role"] == "hinged_door":
            attach(ident, row["role"], ident)
        elif row["role"] == "cut_or_fixed" and ident in candidates:
            attach(ident, row["role"], ident)
    for ident, row in direct_reads.items():
        if row["source_text"]:
            attach(ident, row["role"], ident)

    items = []
    counts = {}
    for ident, roles in sorted(candidates.items()):
        if len(roles) != 1:
            issues.append({"candidate_id": ident, "roles": sorted(roles),
                           "reason": "conflicting evidence"})
            continue
        (role, source_ids), = roles.items()
        items.append({"candidate_id": ident, "role": role, "bbox_px": contours[ident],
                      "source_ids": sorted(set(source_ids))})
        counts[role] = counts.get(role, 0) + 1
    return {"counts": counts, "items": items, "issues": issues}


def audited_view(checkpoint, packet, *, document, view_id):
    audit_path = checkpoint / "evidence" / "estimation-offline-all-islands-evidence.json"
    audit_bytes = audit_path.read_bytes()
    if sha256(audit_bytes).hexdigest() != packet["source_audit_sha256"]:
        raise ValueError("caption source does not match the saved geometry")
    audit = json.loads(audit_bytes)
    view, = [view for view in audit["documents"][document] if view["view_id"] == view_id]
    source = checkpoint / "sources" / SOURCE_NAMES[document]
    if sha256(source.read_bytes()).hexdigest() != audit["source_sha256"][document]:
        raise ValueError("unexpected geometry source PDF")
    return source, view


def caption_image(checkpoint, packet, *, document, view_id):
    import pymupdf
    from PIL import Image, ImageDraw, ImageFont

    source, view = audited_view(checkpoint, packet, document=document, view_id=view_id)
    with pymupdf.open(source) as pdf:
        page = pdf[view["page"] - 1]
        x0, y0, x1, y1 = view["bbox_normalized"]
        w, h = page.rect.width, page.rect.height
        clip = pymupdf.Rect(x0 * w, y0 * h, x1 * w, y1 * h)
        zoom = 1100 / clip.width
        low = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        high = page.get_pixmap(matrix=pymupdf.Matrix(zoom * 3, zoom * 3), clip=clip)
        source_image = Image.frombytes("RGB", (high.width, high.height), high.samples)

        def project(point):
            p = point * page.rotation_matrix
            return p.x * zoom - low.x, p.y * zoom - low.y

        underlines = []
        for path in page.get_drawings():
            if path["type"] != "s" or not path["width"] < .4:
                continue
            for kind, *points in path["items"]:
                if kind != "l":
                    continue
                a, b = map(project, points)
                if abs(a[1] - b[1]) < .75 and dist(a, b) > 18:
                    underlines.append((a, b))

    crops = []
    for ident, leader in packet["leaders"].items():
        root = leader["root_px"]
        options = [(a, b) for a, b in underlines if min(dist(a, root), dist(b, root)) <= 2]
        if not options:
            continue
        a, b = max(options, key=lambda line: dist(*line))
        box = (min(a[0], b[0]) - 7, root[1] - 23, max(a[0], b[0]) + 7, root[1] + 26)
        crop = source_image.crop((
            max(0, round((box[0] + low.x) * 3 - high.x)),
            max(0, round((box[1] + low.y) * 3 - high.y)),
            min(high.width, round((box[2] + low.x) * 3 - high.x)),
            min(high.height, round((box[3] + low.y) * 3 - high.y)),
        ))
        crop.thumbnail((1000, 107), Image.Resampling.LANCZOS)
        crops.append((ident, crop))

    if not crops:
        return None
    sheet = Image.new("RGB", (1080, 114 * len(crops) + 8), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    for index, (ident, crop) in enumerate(crops):
        y = index * 114 + 4
        draw.text((9, y + 24), ident, font=font, fill="#163347")
        sheet.paste(crop, (67, y))
    buffer = BytesIO()
    sheet.save(buffer, format="PNG")
    return buffer.getvalue()


def stroke_image(checkpoint, packet, strokes, *, document, view_id):
    from PIL import Image, ImageDraw, ImageFont

    _, view = audited_view(checkpoint, packet, document=document, view_id=view_id)
    faces = {face["id"]: face for face in view["candidates"]}
    tile_width, tile_height = 238, 165
    columns = min(4, len(strokes))
    rows = (len(strokes) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    for index, (ident, stroke) in enumerate(strokes.items()):
        x = index % columns * tile_width
        y = index // columns * tile_height
        left, top, right, bottom = faces[ident]["bbox"]
        scale = min(184 / (right - left), 108 / (bottom - top))

        def point(pair):
            return x + 24 + (pair[0] - left) * scale, y + 36 + (pair[1] - top) * scale

        outline = [point(pair) for pair in faces[ident]["polygon"]]
        draw.text((x + 18, y + 8), ident, font=font, fill="#19394f")
        draw.line(outline + outline[:1], fill="#273f50", width=2)
        for ray in stroke["rays_px"]:
            draw.line([point(pair) for pair in ray], fill="#754597", width=3)
    buffer = BytesIO()
    sheet.save(buffer, format="PNG")
    return buffer.getvalue()


def prepare(source, packet, marks, *, document, view_id, checkpoint=None, stroke_details=False):
    request = source["provider_request"]
    if packet["source_audit_sha256"] != marks["audit_sha256"]:
        raise ValueError("stroke pairs and contours must use the same source audit")
    if source["request_sha256"] != digest(request):
        raise ValueError("saved request hash mismatch")
    original, = request["messages"]
    images = [block for block in original["content"] if block["type"] == "image"]
    if len(images) != 2:
        raise ValueError("expected a clean source crop and neutral geometry crop")
    context = json.loads(original["content"][-1]["text"])
    if context["view_id"] != view_id or context["leader_groups"] != packet["leaders"]:
        raise ValueError("neutral geometry does not belong to the saved source crop")
    views = [view for view in marks["documents"][document] if view["view_id"] == view_id]
    if len(views) != 1:
        raise ValueError("missing mark evidence for the requested view")
    strokes = {}
    for mark in views[0]["opening_marks"]:
        ident = mark["candidate_id"]
        if ident in packet["contours"]:
            strokes[ident] = {"side": mark["apex_side_on_view"], "rays_px": mark["rays_px"]}
    context["side_stroke_pairs"] = strokes
    content = [*original["content"][:-1], {"type": "text", "text": json.dumps(context, separators=(",", ":"))}]
    if checkpoint is not None and (captions := caption_image(checkpoint, packet, document=document, view_id=view_id)):
        content.extend([
            {"type": "text", "text": "Indexed source-caption crops. Read the printed label beside each A ID here."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": b64encode(captions).decode("ascii")}},
        ])
    if stroke_details and strokes:
        if checkpoint is None:
            raise ValueError("stroke details need the verified geometry checkpoint")
        image = stroke_image(checkpoint, packet, strokes, document=document, view_id=view_id)
        content.extend([
            {"type": "text", "text": "Use these isolated native contours and stroke pairs for stroke_readings. Each tile is one C contour."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": b64encode(image).decode("ascii")}},
        ])
    prepared = {**request, "system": SYSTEM, "messages": [{**original, "content": content}]}
    return prepared, strokes


def execute(request, output, *, packet, strokes, source_hash):
    from agents.estimation_understanding_agent import (
        _create_message_with_hard_timeout, _json_object, get_anthropic_client,
    )

    config = Path("/Users/qb/costerly-app/.streamlit/secrets.toml")
    for key, value in tomllib.loads(config.read_text()).items():
        if isinstance(value, (str, int, float)):
            os.environ.setdefault(key, str(value))
    client = get_anthropic_client().with_options(timeout=120, max_retries=0)
    witness = {"status": "provider_request_pending", "provider_calls": 1, "provider_request": request,
               "request_sha256": digest(request), "source_request_sha256": source_hash}
    with output.open("x", encoding="utf-8") as f:
        json.dump(witness, f, ensure_ascii=False, indent=2)
    started = time.monotonic()
    try:
        response = _create_message_with_hard_timeout(client, timeout_seconds=120, **request)
        raw = response.model_dump(mode="json")
        body = "\n".join(b["text"] for b in raw["content"] if b["type"] == "text")
        witness.update(provider_response=raw, raw_response_text=body, usage=raw["usage"],
                       stop_reason=raw["stop_reason"])
        if raw["stop_reason"] != "end_turn":
            raise ValueError("incomplete response")
        readings = _json_object(body)
        witness["model_readings"] = readings
        witness["bound_fronts"] = bind_front_roles(
            readings, leaders=packet["leaders"], contours=packet["contours"], stroke_ids=strokes)
        witness["status"] = "semantic_review_required"
    except Exception as exc:
        witness.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    witness["elapsed_seconds"] = round(time.monotonic() - started, 3)
    output.write_text(json.dumps(witness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: witness.get(key) for key in
                      ("status", "provider_calls", "elapsed_seconds", "usage", "error")}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-witness", type=Path, required=True)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--marks", type=Path, required=True)
    parser.add_argument("--document", required=True)
    parser.add_argument("--view-id", required=True)
    parser.add_argument("--checkpoint", type=Path, help="Use the verified PDF for local caption crops")
    parser.add_argument("--stroke-details", action="store_true", help="Show each native stroke pair on its own contour")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--execute", action="store_true", help="Send one request with no retries")
    args = parser.parse_args()
    source, packet, marks = (json.loads(path.read_bytes()) for path in
                             (args.source_witness, args.geometry, args.marks))
    request, strokes = prepare(source, packet, marks, document=args.document, view_id=args.view_id,
                               checkpoint=args.checkpoint, stroke_details=args.stroke_details)
    if args.execute:
        if args.output is None or args.output.exists():
            parser.error("--execute requires a new --output path")
        execute(request, args.output, packet=packet, strokes=strokes, source_hash=source["request_sha256"])
    else:
        print(json.dumps({"provider_calls": 0, "request_sha256": digest(request),
                          "leaders": len(packet["leaders"]), "stroke_pairs": len(strokes)}))


if __name__ == "__main__":
    main()
