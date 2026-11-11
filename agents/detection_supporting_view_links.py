"""Find bounded first links for sparse, registered technical projections."""

from collections import Counter, defaultdict
from decimal import Decimal
from io import BytesIO

from PIL import Image

from agents.detection_dimension_chains import DimensionSpan, SpanReading, _bind_readings, _TICK_TOLERANCE
from agents.pdf_page_inspection import measure_rgb_visual_coverage
from agents.schemas.detection_registry_schema import (
    _V5_SHORT_FINGERPRINT_MAX_POSITIONS,
    is_detection_supporting_technical_role,
)


_NON_FABRICATION_ROLES = {"presentation_render", "floor_plan", "location_plan", "unknown"}
# The core can include small margins. Both ticks still have to span the object.
_CORE_MARGIN_RATIO = 0.1
# Require a clear contraction across the projection axis.
_MAX_SECONDARY_DEPTH_RATIO = 0.5


def _core_bounds(package, frame, width, height):
    box = package.get("core_bbox")
    if not box:
        return None
    limits = tuple(
        float(box[f"{corner}_{axis}"]) * scale / frame[i]
        for corner in ("top_left", "bottom_right")
        for i, (axis, scale) in enumerate((("x", width), ("y", height)))
    )
    if 0 <= limits[0] < limits[2] <= width and 0 <= limits[1] < limits[3] <= height:
        return limits
    return None


def _full_span(span, box):
    axis = span.axis
    margin = _CORE_MARGIN_RATIO * (box[axis + 2] - box[axis])
    return (
        abs(span.start[axis] - box[axis]) <= margin
        and abs(span.end[axis] - box[axis + 2]) <= margin
    )


def _registered(left, right, left_box, right_box):
    axis = left.axis
    perpendicular = 1 - axis
    separated = (left_box[perpendicular + 2] <= right_box[perpendicular]
                 or right_box[perpendicular + 2] <= left_box[perpendicular])
    return separated and max(
        abs(left.start[axis] - right.start[axis]),
        abs(left.end[axis] - right.end[axis]),
    ) <= _TICK_TOLERANCE


def _image_occupancy(image, box, width, height):
    pixels = tuple(round(v * scale) for v, scale in zip(
        box, (image.width / width, image.height / height) * 2, strict=True,
    ))
    if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
        return 0
    with image.crop(pixels) as crop:
        return measure_rgb_visual_coverage(crop)["occupied_area_ratio"]


def find_supporting_view_links(
    *, visual_groups, view_packages, object_view_ids, fingerprints, page_dimensions, page_images,
    read_spans, dimension_edges, dimension_chain_matches,
):
    """Return measured first-link candidates before compilation changes membership."""
    roles = {
        row["group_id"]: str(row["representation_kind"]).strip().lower().replace("-", "_").replace(" ", "_")
        for row in visual_groups
        if row["group_id"] in object_view_ids
    }
    eligible = {view for view, role in roles.items() if role not in _NON_FABRICATION_ROLES}
    by_view = {row["group_id"]: row["occurrences"] for row in fingerprints}
    packages_by_page = defaultdict(dict)
    for package in view_packages:
        if package["visual_group_id"] in eligible:
            packages_by_page[package["page_number"]][package["visual_group_id"]] = package
    edges_by_page = defaultdict(list)
    for edge in dimension_edges:
        if edge["same_page"] and {edge["group_id_a"], edge["group_id_b"]} <= eligible:
            edges_by_page[edge["page_a"]].append(edge)

    links = {}
    for page, edges in edges_by_page.items():
        frame = page_dimensions.get(page)
        if not frame or not 1 <= page <= len(page_images):
            continue
        geometry = read_spans(page)
        if not geometry or not geometry.spans:
            continue
        packages = packages_by_page[page]
        bounds = {view: box for view, package in packages.items() if (
            box := _core_bounds(package, frame, geometry.width, geometry.height)
        )}
        readings = {
            view: [r for r in _bind_readings(by_view.get(view, []), packages[view]["bbox"], frame, geometry)
                   if _full_span(r.span, box)]
            for view, box in bounds.items()
        }
        values_to_views = defaultdict(set)
        dimension_sources = {}
        position_counts = {}
        for view in packages:
            rows = by_view.get(view, [])
            dimension_sources[view] = {source for row in rows for source in row["source_fact_ids"]}
            position_counts[view] = len({row.get("ambiguity_key") or row["occurrence_id"] for row in rows})
            for row in rows:
                values_to_views[Decimal(row["value_mm"])].add(view)
        for edge in edges:
            pair = (edge["group_id_a"], edge["group_id_b"])
            for chain in dimension_chain_matches.get(pair, ()):
                first, last = chain.chain[0].span, chain.chain[-1].span
                whole = DimensionSpan(first.axis, first.start, last.end)
                total = chain.printed_total.value_mm
                box = bounds.get(chain.chain_view)
                if box and _full_span(whole, box):
                    sources = frozenset().union(*(part.source_fact_ids for part in chain.chain))
                    readings[chain.chain_view].append(SpanReading(whole, total, sources))
                    values_to_views[total].add(chain.chain_view)

        pending = []
        for edge in edges:
            pair = (edge["group_id_a"], edge["group_id_b"])
            for support, primary in (pair, pair[::-1]):
                if (is_detection_supporting_technical_role(roles[primary])
                        or not 0 < position_counts[support] <= _V5_SHORT_FINGERPRINT_MAX_POSITIONS
                        or position_counts[support] >= position_counts[primary]
                        or set(packages[support]["source_fact_ids"]) - dimension_sources[support]):
                    continue
                for left in readings.get(support, []):
                    axis = left.span.axis
                    cross_axis = 1 - axis
                    support_box = bounds[support]
                    primary_box = bounds.get(primary)
                    if not primary_box:
                        continue
                    depth = support_box[cross_axis + 2] - support_box[cross_axis]
                    primary_depth = primary_box[cross_axis + 2] - primary_box[cross_axis]
                    if (depth > primary_depth * _MAX_SECONDARY_DEPTH_RATIO
                            or values_to_views[left.value_mm] - set(pair)
                            or any(r.span.axis == axis and r.value_mm != left.value_mm
                                   for r in readings[support] + readings[primary])):
                        continue
                    match = next((right for right in readings[primary]
                                  if right.span.axis == axis and right.value_mm == left.value_mm
                                  and not left.source_fact_ids & right.source_fact_ids
                                  and _registered(left.span, right.span, support_box, primary_box)), None)
                    if match:
                        pending.append((pair, support, primary, left, match))
                        break
        if not pending:
            continue

        try:
            with Image.open(BytesIO(page_images[page - 1])) as source:
                image = source.convert("RGB")
                image.thumbnail((1536, 1536))
                occupancy = {
                    view: _image_occupancy(image, bounds[view], geometry.width, geometry.height)
                    for view in {v for pair, *_ in pending for v in pair}
                }
        except (OSError, ValueError):
            continue
        for pair, support, primary, left, right in pending:
            if not 0 < occupancy[support] < occupancy[primary]:
                continue
            links[pair] = {
                "supporting_view": support,
                "primary_view": primary,
                "axis": "xy"[left.span.axis],
                "extent_mm": str(left.value_mm),
                "source_fact_ids": sorted(left.source_fact_ids | right.source_fact_ids),
                "ink_coverage": {view: occupancy[view] for view in pair},
                "sheet_area_ratio": {
                    view: round((bounds[view][2] - bounds[view][0]) * (bounds[view][3] - bounds[view][1])
                                / (geometry.width * geometry.height), 6)
                    for view in pair
                },
                "dimension_positions": {view: position_counts[view] for view in pair},
            }

    endpoints = Counter(view for pair in links for view in pair)
    return {pair: witness for pair, witness in links.items() if all(endpoints[v] == 1 for v in pair)}
