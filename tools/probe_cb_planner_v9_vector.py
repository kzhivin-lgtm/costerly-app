"""Replay Planner V9 with selectable native PDF contours for block locators."""

import argparse
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from agents.estimation_understanding_agent import planner_front_ids, validate_assembly_plan
from tools.probe_estimation_v7_4_front_evidence import execute_request
from tools.probe_estimation_v7_4_visual_front import image_block
from tools.render_estimation_front_overlay import COLORS, box_to_pixels, decode_evidence_images, draw_annotations
from use_cases.estimation_detection_context_v7 import digest


POLICY = Path(__file__).resolve().parents[1] / "agents/prompts/cb_planner_v9.md"
OLD_REGION = '"bbox_1000": [0, 0, 1000, 1000]}'
NEW_REGION = ('"bbox_1000": [0, 0, 1000, 1000], '
              '"geometry_scope": "complete | partial | unavailable", "contour_ids": []}')
VECTOR_POLICY = """
SOURCE GEOMETRY FOR BLOCK REGIONS
Each map is an independent crop of the same Island with neutral native PDF
contour IDs. A map can include fixtures, dimension outlines, neighboring
surfaces and open space. Select only contours with physical ownership in
this block or shared element. Identify the assembly boundaries across the
drawings before selecting its visible contour or visible constituent
contours. Choose the view that provides reliable source geometry. Prefer
plan contours for the worktop when the plan shows its extent and turns.
Use geometry_scope complete only if the selected source contours cover
the block's visible extent in the chosen view. Use partial for a visible
subset, or unavailable with an empty contour_ids list when no contour
supports the locator. Contour IDs are local to region.view_id. Keep
bbox_1000 in the original labelled detail image's coordinate frame.
"""


def source_map(image, candidates):
    """Place neutral labels inside their native contours, including concave faces."""
    mapped = image.convert("RGB")
    draw = ImageDraw.Draw(mapped)
    font = ImageFont.load_default(size=14)
    used = []
    indexed = {}
    for face in sorted(candidates, key=lambda row: row["area"]):
        left, top, right, bottom = (round(v) for v in face["bbox"])
        width, height = right - left, bottom - top
        if width < 12 or height < 8:
            continue
        ident = face["id"]
        points = [tuple(p) for p in face["polygon"]]
        mask = Image.new("1", (width + 1, height + 1))
        ImageDraw.Draw(mask).polygon([(x - left, y - top) for x, y in points], fill=1)
        label_width = round(draw.textlength(ident, font=font)) + 4
        fractions = (.5, .25, .75, .1, .9)
        for x_fraction, y_fraction in ((x, y) for y in fractions for x in fractions):
            x, y = round(width * x_fraction), round(height * y_fraction)
            if not mask.getpixel((x, y)):
                continue
            label_x = left + x - label_width // 2
            label_y = top + y - 8
            box = (label_x, label_y, label_x + label_width, label_y + 16)
            if (box[0] < 0 or box[1] < 0 or box[2] >= image.width or box[3] >= image.height
                    or any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1]
                           for b, _ in used)):
                continue
            used.append((box, ident))
            indexed[ident] = face["polygon"]
            draw.line(points + points[:1], fill="#188394", width=2)
            break
    for box, ident in used:
        draw.rectangle(box, fill="#e4f5f7", outline="#12778b")
        draw.text((box[0] + 2, box[1]), ident, font=font, fill="#083c47")
    data = BytesIO()
    mapped.save(data, format="PNG")
    return data.getvalue(), indexed


def prepare_request(witness, archive, *, document):
    original = witness["provider_request"]
    if digest(original) != witness["request_sha256"] or original["system"] != POLICY.read_text().strip():
        raise ValueError("expected an exact saved Planner V9 request")
    if original["system"].count(OLD_REGION) != 2:
        raise ValueError("unexpected Planner region template")
    system = original["system"].replace(OLD_REGION, NEW_REGION)
    system = system.replace("Return English JSON only", VECTOR_POLICY + "\nReturn English JSON only", 1)
    audit = (archive / "estimation-offline-all-islands-evidence.json").read_bytes()
    views = {v["view_id"]: v for v in json.loads(audit)["documents"][document]}
    _, details = decode_evidence_images(original)
    message, = original["messages"]
    content = list(message["content"])
    geometry = {}
    for ident, (_, meta) in details.items():
        view = views[ident.removeprefix("p1-")]
        detail = meta["detail_of_existing_view"]
        if (view["object_id"] != detail["object_id"]
                or any(abs(a - b) >= .0003 for a, b in zip(
                    view["bbox_normalized"], detail["bbox_normalized"], strict=True))):
            raise ValueError(f"unexpected source Island geometry: {ident}")
        path = archive / "full" / f"{document}-{view['number']:02d}.png"
        with Image.open(path) as image:
            if image.size != (view["width"], view["height"]):
                raise ValueError(f"unexpected native crop size: {ident}")
            pixels, contours = source_map(image, view["candidates"])
        geometry[ident] = {"source_crop": str(path), "contours": contours}
        if contours:
            content.extend([
                {"type": "text", "text": f"Native contour map for {ident}. C IDs belong only to this Island."},
                image_block(pixels),
            ])
    request = {**original, "system": system, "messages": [{**message, "content": content}]}
    return request, geometry, sha256(audit).hexdigest()


def bind_plan(plan, *, geometry, front_ids):
    original = deepcopy(plan)
    bindings = {}
    issues = []
    owners = {}
    for row in original["blocks"] + original["shared_parts"]:
        region = row["region"]
        scope = region.pop("geometry_scope", None)
        ids = region.pop("contour_ids", None)
        available = geometry.get(region["view_id"], {}).get("contours", {})
        if (scope not in ("complete", "partial", "unavailable") or not isinstance(ids, list)
                or any(not isinstance(ident, str) or ident not in available for ident in ids)
                or len(set(ids)) != len(ids) or bool(ids) != (scope != "unavailable")):
            issues.append({"id": row["id"], "reason": "invalid or unavailable source contour selection"})
            continue
        if ids:
            bindings[row["id"]] = {"view_id": region["view_id"], "scope": scope, "contour_ids": ids,
                                    "polygons": [available[ident] for ident in ids]}
            for ident in ids:
                key = (region["view_id"], ident)
                if key in owners:
                    issues.append({"id": row["id"], "other_id": owners[key], "contour_id": ident,
                                   "reason": "source contour assigned to multiple regions"})
                else:
                    owners[key] = row["id"]
    error = None
    try:
        validate_assembly_plan(original, set(geometry), front_ids)
    except ValueError as exc:
        error = str(exc)
    return {"bindings": bindings, "geometry_issues": issues, "planner_structure_error": error}


def render_overlay(request, plan, binding_result, geometry, output):
    _, details = decode_evidence_images(request)
    bindings = binding_result["bindings"]
    rows = plan["blocks"] + plan["shared_parts"]
    views = sorted({row["region"]["view_id"] for row in rows} & details.keys())
    palette = list(COLORS)
    row_colors = {row["id"]: palette[index % len(palette)] for index, row in enumerate(rows)}
    tile_width, tile_height, gap, header = 670, 520, 16, 94
    sheet = Image.new("RGB", (2 * tile_width + 3 * gap, header + len(views) * (tile_height + 42)),
                      "#eef4f8")
    draw = ImageDraw.Draw(sheet)
    ink = "#183048"
    title = ImageFont.load_default(size=24)
    label = ImageFont.load_default(size=16)
    draw.text((gap, 9), "Planner V9 | Source contours and model locators", font=title, fill=ink)
    draw.text((gap, 46), "Left: native PDF contours selected by the model. Right: raw approximate boxes.",
              font=label, fill=ink)
    draw.text((gap, 68), "Partial means a visible subset. An exact source outline does not verify block membership.",
              font=label, fill=ink)
    for index, view_id in enumerate(views):
        top = header + index * (tile_height + 42)
        supplied, _ = details[view_id]
        with Image.open(geometry[view_id]["source_crop"]) as crop:
            native = crop.convert("RGB")
        native_draw = ImageDraw.Draw(native)
        approximate = []
        invalid_boxes = []
        for row in rows:
            region, ident = row["region"], row["id"]
            if region["view_id"] != view_id:
                continue
            box = region["bbox_1000"]
            if (isinstance(box, list) and len(box) == 4 and all(type(v) in (float, int) for v in box)
                    and 0 <= box[0] < box[2] <= 1000 and 0 <= box[1] < box[3] <= 1000):
                approximate.append({"id": ident, "type": row_colors[ident],
                                    "pixels": box_to_pixels(box, supplied.size)})
            else:
                invalid_boxes.append(ident)
            if ident in bindings:
                b = bindings[ident]
                color = COLORS[row_colors[ident]]
                for polygon in b["polygons"]:
                    points = [tuple(point) for point in polygon]
                    native_draw.line(points + points[:1], fill=color, width=4)
                x, y = b["polygons"][0][0]
                caption = ident + (" partial" if b["scope"] == "partial" else "")
                x = max(2, min(x + 3, native.width - native_draw.textlength(caption, font=label) - 3))
                y = max(2, min(y + 3, native.height - 22))
                native_draw.text((x, y), caption, fill=color, font=label, stroke_width=2, stroke_fill="white")
        overlay = draw_annotations(supplied, approximate)
        approx_caption = "Approximate"
        if invalid_boxes:
            approx_caption += " | invalid: " + ", ".join(invalid_boxes)
        for column, (caption, tile) in enumerate((("Native", native), (approx_caption, overlay))):
            left = gap + column * (tile_width + gap)
            draw.text((left, top), f"{view_id} | {caption}", font=label, fill=ink)
            tile.thumbnail((tile_width, tile_height), Image.Resampling.LANCZOS)
            sheet.paste(tile, (left + (tile_width - tile.width) // 2, top + 28))
    sheet.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--document", choices=("lev2", "adda"), required=True)
    parser.add_argument("--output", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--execute", action="store_true")
    action.add_argument("--render", type=Path, help="Render a saved vector Planner witness")
    args = parser.parse_args()
    source = args.baseline.read_bytes()
    witness = json.loads(source)
    request, geometry, audit_hash = prepare_request(witness, args.archive, document=args.document)
    context = json.loads(witness["provider_request"]["messages"][0]["content"][-1]["text"])
    ids = planner_front_ids(context["fallible_front_reference"], set(geometry))
    print(json.dumps({"request_sha256": digest(request), "geometry_sha256": audit_hash,
                      "contours_by_view": {key: len(value["contours"]) for key, value in geometry.items()}}),
          flush=True)
    if args.execute:
        if args.output is None or args.output.exists():
            parser.error("--execute requires a new --output path")
        execute_request(request, args.output, bind=lambda plan: bind_plan(plan, geometry=geometry, front_ids=ids),
                        source_hash=sha256(source).hexdigest())
    elif args.render is not None:
        if args.output is None or args.output.exists():
            parser.error("--render requires a new --output path")
        saved = json.loads(args.render.read_bytes())
        if saved["provider_request"] != request or saved["request_sha256"] != digest(request):
            raise ValueError("overlay witness does not use this exact request")
        plan = saved["model_readings"]
        bound = bind_plan(plan, geometry=geometry, front_ids=ids)
        render_overlay(request, plan, bound, geometry, args.output)


if __name__ == "__main__":
    main()
