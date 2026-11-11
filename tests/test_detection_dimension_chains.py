from decimal import Decimal

import pymupdf
import pytest

from agents.detection_dimension_chains import build_dimension_chain_matches, native_dimension_span_reader
from agents.schemas.detection_registry_schema import compile_detection_v5_dimension_graph, compile_detection_v5_merge_edges


def drawing_fixture(*, layout="continuous", wrong_axis=False, total_is_segment=False, competing=False, rotation=0):
    with pymupdf.open() as document:
        page = document.new_page(width=320, height=240)

        def line(first, last):
            page.draw_line(first, last, width=0.25)

        def tick(x, y):
            line((x - 1.3, y - 1.3), (x + 1.3, y + 1.3))

        if layout in {"continuous", "missing_tick"}:
            line((20, 80), (130, 80))
        else:
            line((20, 80), (42, 80))
            line((42, 90 if layout == "parallel" else 80), (130, 90 if layout == "parallel" else 80))
        tick(20, 80)
        if layout != "missing_tick":
            tick(42, 80)
        if layout == "parallel":
            tick(42, 90)
        tick(130, 90 if layout == "parallel" else 80)
        if wrong_axis:
            line((200, 75), (200, 185))
            tick(200, 75)
            tick(200, 185)
        else:
            line((175, 140), (285, 140))
            tick(175, 140)
            tick(285, 140)
            if total_is_segment:
                line((285, 140), (308, 140))
                tick(308, 140)
        if competing:
            line((175, 195), (285, 195))
            tick(175, 195)
            tick(285, 195)
        page.set_rotation(rotation)
        matrix = page.rotation_matrix
        width, height = int(page.rect.width), int(page.rect.height)
        pdf = document.tobytes()

    bbox = {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": width, "bottom_right_y": height}

    def occurrence(value, x, y, source_id):
        text = pymupdf.Rect(x - 4, y - 3, x + 4, y + 3) * matrix
        return {
            "value_mm": str(value),
            "occurrence_id": source_id,
            "source_fact_ids": [source_id],
            "normalized_bbox": {
                "top_left_x": text.x0 / width, "bottom_right_x": text.x1 / width,
                "top_left_y": text.y0 / height, "bottom_right_y": text.y1 / height,
            },
        }

    fingerprints = [
        {"group_id": "a", "occurrences": [
            occurrence(220, 31, 75, "s22"),
            occurrence(880, 86, 85 if layout == "parallel" else 75, "s88"),
        ]},
        {"group_id": "b", "occurrences": [
            occurrence(1100, 195 if wrong_axis else 230, 130 if wrong_axis else 135, "s110"),
        ]},
    ]
    if competing:
        fingerprints.append({"group_id": "c", "occurrences": [occurrence(1100, 230, 190, "s110-other")]})
    packages = [
        {"visual_group_id": row["group_id"], "page_number": 1, "bbox": bbox}
        for row in fingerprints
    ]
    matches = build_dimension_chain_matches(
        fingerprints, packages, page_dimensions={1: (width, height)},
        excluded_views=set(), read_spans=native_dimension_span_reader(pdf),
    )
    return fingerprints, packages, matches


@pytest.mark.parametrize(("layout", "rotation", "shared_tick"), [
    ("continuous", 0, (42, 80)),
    ("separate_segments", 0, (42, 80)),
    ("continuous", 90, (160, 42)),
])
def test_chain_of_native_spans_becomes_dimension_graph_evidence(layout, rotation, shared_tick):
    fingerprints, packages, matches = drawing_fixture(layout=layout, rotation=rotation)
    match, = matches["a", "b"]
    assert [part.value_mm for part in match.chain] == [Decimal(220), Decimal(880)]
    assert match.chain[0].span.end == match.chain[1].span.start == shared_tick
    views = [{"group_id": p["visual_group_id"], "page_number": 1} for p in packages]
    edges, audit = compile_detection_v5_dimension_graph(
        fingerprints, visual_groups=views, allowed_pairs=set(), dimension_chain_matches=matches,
    )
    assert edges[0]["relationship"] == "supporting_relation"
    assert edges[0]["dimension_similarity_score"] == 35
    merge_edges, _ = compile_detection_v5_merge_edges(edges, [], visual_groups=views)
    assert merge_edges[0]["relationship"] == "supporting_relation"
    fact, = edges[0]["evidence_facts"]
    assert fact["source_fact_ids"] == ["s110", "s22", "s88"]
    candidate, = audit["dimension_similarity_candidates"]
    assert candidate["dimension_chain_match"]["total_mm"] == "1100"
    assert candidate["features"] == []


@pytest.mark.parametrize("drawing", [
    {"layout": "missing_tick"},
    {"layout": "parallel"},
    {"wrong_axis": True},
    {"total_is_segment": True},
    {"competing": True},
])
def test_arithmetic_alone_cannot_create_dimension_chain_evidence(drawing):
    assert drawing_fixture(**drawing)[2] == {}


def test_chain_cannot_count_a_reading_already_used_by_fingerprint():
    fingerprints, packages, matches = drawing_fixture()
    fingerprints[1]["occurrences"].append({
        "value_mm": "220", "occurrence_id": "printed22", "source_fact_ids": ["printed22"],
    })
    views = [{"group_id": p["visual_group_id"], "page_number": 1} for p in packages]
    _, audit = compile_detection_v5_dimension_graph(
        fingerprints, visual_groups=views, allowed_pairs=set(), dimension_chain_matches=matches,
    )
    candidate, = audit["dimension_similarity_candidates"]
    assert "dimension_chain_match" not in candidate
    assert candidate["features"][0]["left_mm"] == "220"
