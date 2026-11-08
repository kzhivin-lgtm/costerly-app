"""Replay Planner V9 with selectable native PDF contours for block locators."""

import argparse
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from math import ceil, floor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from agents.estimation_understanding_agent import planner_front_ids, validate_assembly_plan
from tools.probe_estimation_v7_4_front_evidence import execute_request
from tools.probe_estimation_v7_4_visual_front import image_block
from tools.render_estimation_front_overlay import decode_evidence_images
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
LOCATOR_POLICY = """Locate the visible geometry of a saved assembly plan. The supplied
Blocks, shared elements, Front assignments and membership are fixed. Return
exactly one locator for each saved ID. Use the clean crops and native PDF
contour maps together. Select a view that actually shows the element. For a
worktop, prefer the plan when it shows the true extent. Exclude neighboring
units, unrelated marks and spaces. C IDs belong to one view only.

Use complete when the selected contours cover the visible element in that
view. Use partial for a visible subset. Use unavailable with no contour IDs
when the visible element cannot be reliably located. Return JSON only:
{"locators":[{"id":"B01","view_id":"source view ID",
"geometry_scope":"complete | partial | unavailable","contour_ids":[]}]}
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


def prepare_request(witness, archive, *, document, locked_plan=False):
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
    if locked_plan:
        plan = witness["model_readings"]
        saved = {key: [{k: v for k, v in row.items() if k != "region"} for row in plan[key]]
                 for key in ("blocks", "shared_parts")}
        content.append({"type": "text", "text": json.dumps({"locked_plan": saved}, ensure_ascii=False)})
        system = LOCATOR_POLICY
    request = {**original, "system": system, "messages": [{**message, "content": content}]}
    return request, geometry, sha256(audit).hexdigest()


def bind_regions(regions, geometry):
    bindings = {}
    issues = []
    owners = {}
    for region in regions:
        ident, view = region["id"], region["view_id"]
        scope, ids = region["geometry_scope"], region["contour_ids"]
        available = geometry.get(view, {}).get("contours", {})
        if (view not in geometry or scope not in ("complete", "partial", "unavailable")
                or not isinstance(ids, list)
                or any(not isinstance(ident, str) or ident not in available for ident in ids)
                or len(set(ids)) != len(ids) or bool(ids) != (scope != "unavailable")):
            issues.append({"id": ident, "reason": "invalid or unavailable source contour selection"})
            continue
        if ids:
            bindings[ident] = {"view_id": view, "scope": scope, "contour_ids": ids,
                               "polygons": [available[contour] for contour in ids]}
            for contour in ids:
                key = (view, contour)
                if key in owners:
                    issues.append({"id": ident, "other_id": owners[key], "contour_id": contour,
                                   "reason": "source contour assigned to multiple regions"})
                else:
                    owners[key] = ident
    return {"bindings": bindings, "geometry_issues": issues}


def structure_error(plan, geometry, front_ids):
    try:
        validate_assembly_plan(plan, set(geometry), front_ids)
    except ValueError as exc:
        return str(exc)
    return None


def bind_plan(plan, *, geometry, front_ids):
    original = deepcopy(plan)
    regions = []
    for row in original["blocks"] + original["shared_parts"]:
        region = row["region"]
        regions.append({"id": row["id"], "view_id": region["view_id"],
                        "geometry_scope": region.pop("geometry_scope", None),
                        "contour_ids": region.pop("contour_ids", None)})
    return {**bind_regions(regions, geometry),
            "planner_structure_error": structure_error(original, geometry, front_ids)}


def bind_locked_locators(readings, *, plan, geometry, front_ids):
    expected = [row["id"] for row in plan["blocks"] + plan["shared_parts"]]
    fields = {"id", "view_id", "geometry_scope", "contour_ids"}
    if set(readings) != {"locators"} or not isinstance(readings["locators"], list):
        raise ValueError("expected only geometry locators for the locked plan")
    locators = readings["locators"]
    if any(not isinstance(row, dict) or set(row) != fields
           or not isinstance(row["id"], str) or not isinstance(row["view_id"], str) for row in locators):
        raise ValueError("invalid locked locator fields")
    if sorted(row["id"] for row in locators) != sorted(expected):
        raise ValueError("locators must cover exactly the saved assembly IDs once")
    return {**bind_regions(locators, geometry),
            "planner_structure_error": structure_error(plan, geometry, front_ids)}


def block_outline(polygons):
    # Padding keeps a connected background even when a polygon meets the crop edge.
    xs, ys = zip(*(point for polygon in polygons for point in polygon))
    padding = 6
    left, top = floor(min(xs)) - padding, floor(min(ys)) - padding
    width = ceil(max(xs)) - left + padding + 1
    height = ceil(max(ys)) - top + padding + 1
    mask = Image.new("L", (width, height))
    draw = ImageDraw.Draw(mask)
    for polygon in polygons:
        draw.polygon([(x - left, y - top) for x, y in polygon], fill=255)
    # Close narrow drafting seams up to four crop pixels. Larger gaps stay open.
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    ImageDraw.floodfill(mask, (0, 0), 128)
    exterior = mask.point([255 if value == 128 else 0 for value in range(256)])
    outline = ImageChops.subtract(exterior.filter(ImageFilter.MaxFilter(9)), exterior)
    return outline, (left, top)


def render_overlay(plan, binding_result, geometry, output, *, review_note=None):
    bindings = binding_result["bindings"]
    blocks = {row["id"]: row for row in plan["blocks"]}
    palette = ("#2257a6", "#8c2da7", "#c3411c", "#007c6a", "#a35b00",
               "#007ca0", "#563c95", "#2e782a", "#b62469")
    block_colors = {ident: palette[index % len(palette)] for index, ident in enumerate(blocks)}
    views = sorted({binding["view_id"] if (binding := bindings.get(ident)) else row["region"]["view_id"]
                    for ident, row in blocks.items()} & geometry.keys())
    conflicts = {ident for issue in binding_result["geometry_issues"] if "other_id" in issue
                 for ident in (issue["id"], issue["other_id"]) if ident in blocks}
    missing = sorted(blocks.keys() - bindings.keys())
    notes = [review_note] if review_note else []
    if conflicts:
        notes.append("Conflicting contour ownership (*): " + ", ".join(sorted(conflicts)))
    if missing:
        notes.append("No source outline: " + ", ".join(missing))
    tile_width, tile_height, gap = 800, 650, 16
    columns = min(2, max(1, len(views)))
    tile_rows = (len(views) + columns - 1) // columns
    header = 66 + 22 * len(notes)
    sheet = Image.new("RGB", (columns * (tile_width + gap) + gap,
                              header + tile_rows * (tile_height + 42)), "#eef4f8")
    draw = ImageDraw.Draw(sheet)
    ink = "#183048"
    title = ImageFont.load_default(size=24)
    label = ImageFont.load_default(size=16)
    draw.text((gap, 9), "Planner V9 | Block outlines", font=title, fill=ink)
    draw.text((gap, 42), "One color per Block ID. Exterior of saved source geometry only.", font=label, fill=ink)
    for index, note in enumerate(notes):
        draw.text((gap, 64 + index * 22), note, font=label, fill="#a12d46")
    for index, view_id in enumerate(views):
        top = header + index // columns * (tile_height + 42)
        left = gap + index % columns * (tile_width + gap)
        with Image.open(geometry[view_id]["source_crop"]) as crop:
            native = crop.convert("RGB")
        native_draw = ImageDraw.Draw(native)
        captions = []
        for ident in blocks:
            binding = bindings.get(ident)
            if not binding or binding["view_id"] != view_id:
                continue
            outline, position = block_outline(binding["polygons"])
            color = block_colors[ident]
            native.paste(color, position, outline)
            x, y = min((point for polygon in binding["polygons"] for point in polygon),
                       key=lambda point: (point[1], point[0]))
            caption = ident + ("*" if ident in conflicts else "")
            if binding["scope"] == "partial":
                caption += " partial"
            x = max(2, min(x + 5, native.width - native_draw.textlength(caption, font=label) - 3))
            y = max(2, min(y + 5, native.height - 22))
            captions.append(((x, y), caption, color))
        for position, caption, color in captions:
            native_draw.text(position, caption, fill=color, font=label, stroke_width=2, stroke_fill="white")
        draw.text((left, top), view_id, font=label, fill=ink)
        native.thumbnail((tile_width, tile_height), Image.Resampling.LANCZOS)
        sheet.paste(native, (left + (tile_width - native.width) // 2, top + 28))
    sheet.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--document", choices=("lev2", "adda"), required=True)
    parser.add_argument("--locked-plan", action="store_true", help="Localize existing Blocks without regrouping")
    parser.add_argument("--output", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--execute", action="store_true")
    action.add_argument("--render", type=Path, help="Render a saved vector Planner witness")
    args = parser.parse_args()
    source = args.baseline.read_bytes()
    witness = json.loads(source)
    request, geometry, audit_hash = prepare_request(
        witness, args.archive, document=args.document, locked_plan=args.locked_plan)
    context = json.loads(witness["provider_request"]["messages"][0]["content"][-1]["text"])
    ids = planner_front_ids(context["fallible_front_reference"], set(geometry))
    if args.locked_plan:
        plan = witness["model_readings"]

        def bind(readings):
            return bind_locked_locators(readings, plan=plan, geometry=geometry, front_ids=ids)
    else:
        def bind(readings):
            return bind_plan(readings, geometry=geometry, front_ids=ids)
    print(json.dumps({"request_sha256": digest(request), "geometry_sha256": audit_hash,
                      "contours_by_view": {key: len(value["contours"]) for key, value in geometry.items()}}),
          flush=True)
    if args.execute:
        if args.output is None or args.output.exists():
            parser.error("--execute requires a new --output path")
        execute_request(request, args.output, bind=bind, source_hash=sha256(source).hexdigest())
    elif args.render is not None:
        if args.output is None or args.output.exists():
            parser.error("--render requires a new --output path")
        saved = json.loads(args.render.read_bytes())
        if saved["provider_request"] != request or saved["request_sha256"] != digest(request):
            raise ValueError("overlay witness does not use this exact request")
        readings = saved["model_readings"]
        plan = witness["model_readings"] if args.locked_plan else readings
        bound = bind(readings)
        render_overlay(plan, bound, geometry, args.output)


if __name__ == "__main__":
    main()
