import pymupdf
import pytest

from agents.detection_dimension_chains import build_dimension_chain_matches, native_dimension_span_reader
from agents.detection_supporting_view_links import find_supporting_view_links
from agents.schemas.detection_registry_schema import (
    compile_detection_v5_dimension_graph,
    compile_detection_v5_merge_edges,
    derive_detection_proof_components,
)


def _drawing(*, shift=0, competing=False, independent_label=False, conflict=False,
             role="section", primary_role="elevation", chain=False):
    width, height = 420, 250
    packages, fingerprints, views = [], [], []

    def bbox(x0, y0, x1, y1):
        return dict(top_left_x=x0, top_left_y=y0, bottom_right_x=x1, bottom_right_y=y1)

    with pymupdf.open() as document:
        page = document.new_page(width=width, height=height)

        def dimension(start, end):
            page.draw_line(start, end, width=0.25)
            for x, y in (start, end):
                page.draw_line((x - 1.3, y - 1.3), (x + 1.3, y + 1.3), width=0.25)

        def add_view(view, kind, core, dimensions, *, label=False, detailed=False):
            x0, y0, x1, y1 = core
            page.draw_rect(core, width=0.8)
            if detailed:
                for x in range(x0 + 5, x1, 5):
                    page.draw_line((x, y0), (x, y1), width=0.7)
            occurrences = []
            for index, (value, start, end) in enumerate(dimensions):
                dimension(start, end)
                x, y = (a + b for a, b in zip(start, end, strict=True))
                x, y = x / 2, y / 2
                source = f"{view}-dimension-{index}"
                occurrences.append({
                    "value_mm": str(value),
                    "occurrence_id": source,
                    "source_fact_ids": [source],
                    "normalized_bbox": bbox(
                        (x - 4) / width, (y - 3) / height, (x + 4) / width, (y + 3) / height,
                    ),
                })
            views.append({"group_id": view, "page_number": 1, "representation_kind": kind})
            fingerprints.append({"group_id": view, "occurrences": occurrences})
            packages.append({
                "visual_group_id": view, "page_number": 1, "bbox": bbox(0, 0, width, height),
                "core_bbox": bbox(*core),
                "source_fact_ids": [row["occurrence_id"] for row in occurrences]
                + (["independent-piece-mark"] if label else []),
            })

        add_view("a", role, (35 + shift, 30, 155 + shift, 48),
                 [(1800, (35 + shift, 59), (155 + shift, 59))], label=independent_label)
        primary_dimensions = (
            [(600, (35, 171), (75, 171)), (1200, (75, 171), (155, 171))]
            if chain else [(1800, (35, 171), (155, 171))]
        )
        primary_dimensions.append((900, (170, 95), (170, 155)))
        if conflict:
            primary_dimensions.append((1700, (35, 181), (155, 181)))
        add_view("b", primary_role, (35, 95, 155, 155), primary_dimensions, detailed=True)
        if competing:
            add_view("c", "elevation", (245, 95, 365, 155),
                     [(1800, (245, 171), (365, 171))], detailed=True)
        pdf = document.tobytes()
        image = page.get_pixmap(dpi=144).tobytes("png")

    frame = {1: (width, height)}
    read_spans = native_dimension_span_reader(pdf)
    chains = build_dimension_chain_matches(
        fingerprints, packages, page_dimensions=frame, excluded_views=set(), read_spans=read_spans,
    )
    edges, _ = compile_detection_v5_dimension_graph(
        fingerprints, visual_groups=views, dimension_chain_matches=chains,
    )
    links = find_supporting_view_links(
        visual_groups=views, view_packages=packages, object_view_ids={v["group_id"] for v in views},
        fingerprints=fingerprints, page_dimensions=frame, page_images=[image],
        read_spans=read_spans, dimension_edges=edges, dimension_chain_matches=chains,
    )
    return views, edges, links


@pytest.mark.parametrize("chain", [False, True])
def test_registered_sparse_projection_gets_a_first_link_without_model_evidence(chain):
    views, edges, links = _drawing(chain=chain)
    baseline, _ = compile_detection_v5_merge_edges(edges, [], visual_groups=views)
    assert baseline[0]["relationship"] == "supporting_relation"
    result, audit = compile_detection_v5_merge_edges(
        edges, [], visual_groups=views, supporting_view_links=links,
    )
    assert result[0]["relationship"] == "same_object_view"
    assert result[0]["dimension_similarity_score"] == baseline[0]["dimension_similarity_score"]
    witness = audit["edges"][-1]["supporting_view_first_link"]
    assert witness["supporting_view"] == "a"
    assert witness["extent_mm"] == "1800"
    assert witness["ink_coverage"]["a"] < witness["ink_coverage"]["b"]


@pytest.mark.parametrize("drawing", [
    {"shift": 6}, {"competing": True}, {"independent_label": True},
    {"conflict": True}, {"role": "presentation_render"},
    {"role": "plan_detail", "primary_role": "technical_detail"},
])
def test_size_and_fingerprint_alone_do_not_prove_a_supporting_projection(drawing):
    assert _drawing(**drawing)[2] == {}


def test_first_link_respects_conflicts_and_does_not_start_batch_growth():
    views, edges, links = _drawing()
    blocked, _ = compile_detection_v5_merge_edges(
        edges, [], visual_groups=views, supporting_view_links=links,
        merge_blocked_pairs={("a", "b"): "conflicting_products"},
    )
    assert blocked[0]["relationship"] == "supporting_relation"

    views.append({"group_id": "c", "page_number": 1, "representation_kind": "elevation"})
    edges.append({**edges[0], "group_id_a": "b", "group_id_b": "c", "dimension_similarity_score": 65})
    result, _ = compile_detection_v5_merge_edges(edges, [], visual_groups=views, supporting_view_links=links)
    components = derive_detection_proof_components(result, visual_group_ids={"a", "b", "c"})
    assert sorted(components) == [["a", "b"], ["c"]]
