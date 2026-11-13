"""Read visible Front components and review each original PDF sheet for Estimation 9."""

from concurrent.futures import ThreadPoolExecutor
from math import isfinite

import pymupdf

from use_cases.estimation_v9_inventory import COMPONENT_ROLES, page_box
from use_cases.estimation_door_hardware import DOOR_OPENING_ROLES

FRONT_ROLES = (COMPONENT_ROLES - {"hinged_door", "lift_up", "drawer", "support_leg", "pull_out_shelf"}
               | DOOR_OPENING_ROLES | {"material_callout"})
SCOPES = {"standalone", "block_member", "unclear"}
SCHEMA = """Return JSON only:
{"findings":[{"role":"one supplied role","scope":"standalone | block_member | unclear",
"bbox":[left,top,right,bottom],"evidence":"short observed reason","source_text":null,"callout_bbox":null}]}
Scale the image width and height separately to 1000. Each coordinate must be
between 0 and 1000. Use bbox null when a target cannot be localized.
Boxes must surround the physical target, not the text of a callout.
For lighting with a legible printed callout, copy its text verbatim into
source_text, including the number as printed. Keep distinct targets separate.
Use callout_bbox for the text position in the same coordinate frame.
Use source_text null when the callout is absent, illegible or cannot be tied to the target.
Use standalone only when the drawing shows a distinct element outside
an assembly or one continuous feature shared by assemblies. A mirror or
light within the physical Block is a block member. If scope is uncertain, use
unclear. Report only visible or expressly called-out
physical features; do not infer quantities or construction.
Use an empty findings list when there is no supported physical feature."""

FRONT = """Look at this Island for visible mirrors, lighting, plinths, worktops,
glazing, shelves, closures and other physical items in the supplied roles.
Use glass_box for a distinct glass display or storage box. Use glazed_zone
for glass panels or an annotated glazed area with open construction.
Keep mirrors and lighting attached to the physical assembly. Group plinth
segments under one object-level kit. Distinguish separate worktops only
when the drawing shows a real break in the run.
Read printed callouts where they are legible and follow their leaders.
Use material_callout for a printed material or finish specification whose
leader points to a specific panel or part. Transcribe the complete note,
including any second line, finish, and thickness, without supplying a
missing value. Include the indexed annotation_id where available. Keep
general material schedules separate; they are not part-specific callouts.
For a fully visible individual hinged door, use door_without_handle if the
opening edge is clear and there is no external or integrated pull. Use
door_with_pull if a handle, finger pull, recessed grip, or pull profile is
visible. Draw the box around the whole leaf. Skip unreadable or occluded
leaves. Keep one finding per leaf and skip drawers and lift-up flaps.
An apparent feature can be part of a block. Retain the evidence without
inventing hidden components. Ignore geometry clipped from adjacent Islands."""
INVENTORY = """Independently read this full original sheet for physical elements
in the supplied roles. Inspect all views, cross-sections and notes, including
details outside major views. Pay attention to small parts and named features
such as shelves, mirrors, glass boxes, glazing, lighting, bases and closures.
Use glass_box for a distinct glass display or storage box. Keep distinct
physical targets separate. Exclude dimensions, borders and construction lines.
A box must mark one appearance within one drawing view. When the same
physical feature repeats across projections, use the clearest single appearance.
A note with no locatable target should be reported with bbox null and scope unclear."""


def source_request(request, system, content, *, roles, max_tokens, view_ids=None):
    """Use the project's Anthropic structured response format."""
    finding = {
        "role": {"type": "string", "enum": sorted(roles)},
        "scope": {"type": "string", "enum": sorted(SCOPES)},
        "bbox": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}]},
        "callout_bbox": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}]},
        "evidence": {"type": "string"},
        "source_text": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    }
    fields = {}
    if view_ids:
        view_id = {"type": "string", "enum": sorted(view_ids)}
        finding["view_id"] = view_id
        finding["annotation_id"] = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        fields["reviewed_view_ids"] = {"type": "array", "items": view_id}
    fields["findings"] = {"type": "array", "items": {
        "type": "object", "properties": finding, "required": list(finding), "additionalProperties": False,
    }}
    schema = {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}
    params = request(system, content, max_tokens=max_tokens)
    params["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    return params


def _normalized_box(box, view):
    if (isinstance(box, list) and len(box) == 4
            and all(type(n) in (int, float) and isfinite(n) and 0 <= n <= 1000 for n in box)
            and box[0] < box[2] and box[1] < box[3]):
        return page_box(box, view, size=(1000, 1000)) if view else [n / 1000 for n in box]
    return None


def bind_findings(raw, *, page, roles, stage, view=None):
    if not isinstance(raw, dict) or not isinstance(raw.get("findings"), list):
        raise ValueError("Expected a source findings list")
    findings = []
    for row in raw["findings"]:
        if (not isinstance(row, dict) or row.get("role") not in roles or row.get("scope") not in SCOPES
                or not isinstance(row.get("evidence"), str) or not row["evidence"].strip()):
            raise ValueError("Invalid source finding")
        box = row.get("bbox")
        box_normalized = _normalized_box(box, view)
        source = {"page": page, "evidence": row["evidence"].strip()}
        if "source_text" in row:
            literal = row["source_text"]
            if literal is not None and not isinstance(literal, str):
                raise ValueError("Invalid source callout transcription")
            source["source_text"] = literal.strip() or None if literal is not None else None
        if box is not None and box_normalized is None:
            source["localization_issue"] = "invalid_source_target_coordinates"
        if "callout_bbox" in row:
            source["callout_bbox_normalized"] = _normalized_box(row["callout_bbox"], view)
        source["bbox_normalized"] = box_normalized
        if view:
            source["view_id"] = view["view_id"]
        findings.append({"stage": stage, "role": row["role"], "scope": row["scope"], "source": source})
    return findings


def read_front_components(invoke, views, images, request, payload, *, captions=None, image_block=None):
    """Read the original Island crops, independently of physical ownership."""
    # One request for the Islands keeps the additional Front pass bounded.
    content = [payload({"allowed_roles": sorted(FRONT_ROLES), "islands": [
        {"view_id": view["view_id"], "object_id": view["object_id"], "page": view["page"]}
        for view in views.values()
    ]})]
    for vid in views:
        content.extend(images[vid][:2])
        if vid in (captions or {}):
            content.extend([{"type": "text", "text": f"{vid}: indexed closeups of printed callouts."},
                            image_block(captions[vid][0])])
    system = FRONT + "\n" + SCHEMA + """
For this request, include a view_id on every finding and use its own image
coordinates. Review every supplied Island and return reviewed_view_ids
listing every view examined, including empty views. On an indexed closeup,
copy the printed caption into source_text and its exact A ID into annotation_id
when you recognize a supplied role. This applies in particular to every LED
callout, including multiple callouts of the same temperature. Use null for
annotation_id unless you can read the matching indexed caption."""

    def bind(raw):
        if not isinstance(raw, dict) or not isinstance(raw.get("reviewed_view_ids"), list):
            raise ValueError("Front component response must record its reviewed Islands")
        reviewed = raw["reviewed_view_ids"]
        if set(reviewed) != views.keys() or len(reviewed) != len(views):
            raise ValueError("Front component response did not cover every Island")
        grouped = {vid: [] for vid in views}
        if not isinstance(raw.get("findings"), list):
            raise ValueError("Front component response must include findings")
        for row in raw["findings"]:
            if not isinstance(row, dict) or row.get("view_id") not in grouped:
                raise ValueError("Front component response contains an unknown Island")
            grouped[row["view_id"]].append(row)
        findings = []
        for vid, rows in grouped.items():
            bound = bind_findings({"findings": rows}, page=views[vid]["page"], roles=FRONT_ROLES,
                                  stage="front", view=views[vid])
            if vid in (captions or {}):
                _, leaders = captions[vid]
                for row, finding in zip(rows, bound, strict=True):
                    ident = row.get("annotation_id")
                    if (finding["role"] in ({"lighting", "material_callout"} | DOOR_OPENING_ROLES)
                            and isinstance(ident, str) and ident in leaders
                            and finding["source"].get("source_text")):
                        finding["source"].update(annotation_id=ident, tips=leaders[ident]["tips"])
            findings.extend(bound)
        return findings

    if not views:
        return []
    params = source_request(request, system, content, roles=FRONT_ROLES, max_tokens=7500, view_ids=views)
    return invoke("v9-front-components", params, bind)


def review_original_sheets(document, invoke, request, payload, image_block):
    """Run an independent pass on full pages. A failed page stays explicitly open."""
    def review(number, content):
        def bind(raw):
            return bind_findings(raw, page=number, roles=COMPONENT_ROLES, stage="inventory_check")

        try:
            params = source_request(request, INVENTORY + "\n" + SCHEMA, content,
                                    roles=COMPONENT_ROLES, max_tokens=3500)
            findings = invoke(f"v9-inventory-page-{number:03d}", params, bind)
        except (RuntimeError, ValueError) as exc:
            return {"page": number, "status": "review_failed", "error": str(exc), "findings": []}
        return {"page": number, "status": "reviewed", "findings": findings}

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = []
        for number, page in enumerate(document, 1):
            scale = min(3, 2200 / max(page.rect.width, page.rect.height))
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            content = [payload({"page": number, "allowed_roles": sorted(COMPONENT_ROLES)}),
                       image_block(pixmap.tobytes("png"))]
            futures.append(pool.submit(review, number, content))
        return [future.result() for future in futures]
