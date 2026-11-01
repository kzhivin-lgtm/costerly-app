from copy import deepcopy
from io import BytesIO
import re
from unittest.mock import patch

import pytest

from agents.detection_v82 import (
    DetectionV82ContractError,
    apply_detection_v82_conflict_decisions,
    audit_detection_v82_candidate_coverage,
    build_detection_v82_candidate_regions,
    compile_detection_v82_components,
    normalize_detection_v82_discovery,
    normalize_detection_v82_membership_links,
    run_detection_v82_pipeline,
    select_detection_v82_conflict_targets,
)
from agents.detection_v82_adapter import run_detection_v82_with_request
from agents.detection_agent import _select_detection_pipeline_version


def _bbox(left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    return {
        "top_left_x": left,
        "top_left_y": top,
        "bottom_right_x": right,
        "bottom_right_y": bottom,
    }


def _facts() -> list[dict]:
    return [
        {"fact_id": "SF-1", "page_number": 1, "source": "native_pdf_text", "text": "600", "bbox": _bbox(1300, 1000, 1310, 1010)},
        {"fact_id": "SF-2", "page_number": 1, "source": "native_pdf_text", "text": "800", "bbox": _bbox(1450, 1000, 1460, 1010)},
    ]


def _ocr() -> dict:
    return {"pages": [{
        "page_number": 1,
        "dimensions": {"width": 2000, "height": 2000},
        "blocks": [{"type": "image", **_bbox(100, 100, 900, 900)}],
    }]}


def _view(group_id: str, *, kind: str = "technical_elevation", bbox: dict | None = None) -> dict:
    bbox = bbox or _bbox(100, 100, 600, 600)
    return {
        "group_id": group_id,
        "page_number": 1,
        "bbox": bbox,
        "core_bbox": _bbox(bbox["top_left_x"] + 20, bbox["top_left_y"] + 20, bbox["bottom_right_x"] - 20, bbox["bottom_right_y"] - 20),
        "representation_kind": kind,
        "visual_description": "distinctive triangular fabricated shelving configuration",
        "reason": "visible technical construction",
        "evidence_class": "object_evidence",
    }


def _proof(kind: str) -> dict:
    return {"kind": kind, "observation": "distinctive triangular shelving configuration visible in both views"}


def test_v82_candidate_union_keeps_mypdf_compact_and_never_page_inflates():
    candidates = build_detection_v82_candidate_regions(_ocr(), _facts())

    assert len(candidates) == 2
    mypdf = next(candidate for candidate in candidates if candidate["sources"] == ["mypdf_dimensions"])
    assert mypdf["technical_signal"] is True
    assert mypdf["bbox"] == _bbox(1204, 904, 1556, 1106)
    assert (mypdf["bbox"]["bottom_right_x"] - mypdf["bbox"]["top_left_x"]) < 500
    assert "evidence_class" not in mypdf


def test_v82_candidate_identity_is_unaffected_by_unrelated_candidate():
    first = build_detection_v82_candidate_regions(_ocr(), _facts())
    changed = _ocr()
    changed["pages"][0]["blocks"].append({"type": "image", **_bbox(1000, 100, 1200, 300)})
    second = build_detection_v82_candidate_regions(changed, _facts())

    assert {row["candidate_region_id"] for row in first} <= {row["candidate_region_id"] for row in second}


def test_v82_floor_plan_is_terminal_before_membership_and_resolver():
    objects, exclusions = normalize_detection_v82_discovery([{
        "page_number": 1,
        "bbox": _bbox(0, 0, 1000, 1000),
        "core_bbox": _bbox(0, 0, 1000, 1000),
        "representation_kind": "floor_plan",
        "decision": "object_evidence",
        "exclusion_kind": "other",
        "visual_description": "whole-level room circulation plan",
        "reason": "full page architectural plan",
    }], page_dimensions={1: (1000, 1000)})
    candidate = {"candidate_region_id": "C", "page_number": 1, "bbox": _bbox(0, 0, 1000, 1000), "technical_signal": True, "dimension_fact_count": 2, "source_fact_ids": []}
    coverage = audit_detection_v82_candidate_coverage(candidates=[candidate], object_evidence=objects, exclusions=exclusions)

    assert objects == []
    assert exclusions[0]["exclusion_kind"] == "floor_plan"
    assert coverage[0]["status"] == "covered_by_terminal_exclusion"
    assert select_detection_v82_conflict_targets(candidates=[candidate], coverage_audit=coverage) == []


def test_v82_conflict_selection_is_one_per_page_before_second_target():
    candidates = [
        {"candidate_region_id": "p5-a", "page_number": 5, "bbox": _bbox(0, 0, 100, 100), "technical_signal": True, "dimension_fact_count": 5, "source_fact_ids": []},
        {"candidate_region_id": "p5-b", "page_number": 5, "bbox": _bbox(200, 0, 300, 100), "technical_signal": True, "dimension_fact_count": 4, "source_fact_ids": []},
        {"candidate_region_id": "p10", "page_number": 10, "bbox": _bbox(0, 0, 100, 100), "technical_signal": True, "dimension_fact_count": 3, "source_fact_ids": []},
    ]
    audit = [{"candidate_region_id": row["candidate_region_id"], "status": "unexplained"} for row in candidates]

    targets = select_detection_v82_conflict_targets(candidates=candidates, coverage_audit=audit)

    assert [target["candidate_region_id"] for target in targets] == ["p5-a", "p10"]


def test_v82_resolver_admission_is_ordinary_object_evidence_not_a_special_membership_type():
    target = {"target_id": "R", "candidate_region_id": "C", "page_number": 10, "bbox": _bbox(100, 100, 500, 500), "source_fact_ids": []}
    admitted, audit = apply_detection_v82_conflict_decisions(
        object_evidence=[], targets=[target], page_dimensions={10: (1000, 1000)},
        decisions=[{
            "target_id": "R", "decision": "object_evidence", "bbox": _bbox(120, 120, 480, 480), "core_bbox": _bbox(140, 140, 460, 460),
            "representation_kind": "technical_elevation", "visual_description": "separate cabinet elevation", "reason": "separate dimensioned fabricated view",
        }],
    )

    assert admitted[0]["evidence_class"] == "object_evidence"
    assert audit[0]["admitted_group_id"] == admitted[0]["group_id"]
    assert "conflict" not in admitted[0]


def test_v82_membership_has_one_real_contract_for_technical_and_render_links():
    technical_a, technical_b, render = _view("A"), _view("B", bbox=_bbox(700, 100, 1200, 600)), _view("R", kind="presentation_render", bbox=_bbox(1300, 100, 1800, 600))
    links, rejected = normalize_detection_v82_membership_links([
        {"group_id_a": "A", "group_id_b": "B", "proofs": [_proof("matching_topology"), _proof("dimension_equality")]},
        {"group_id_a": "R", "group_id_b": "A", "proofs": [_proof("unique_geometry")]},
    ], object_evidence=[technical_a, technical_b, render])

    assert not rejected
    assert len(links) == 2
    components, excluded = compile_detection_v82_components(object_evidence=[technical_a, technical_b, render], membership_links=links)
    assert components == [["A", "B", "R"]]
    assert excluded == []


def test_v82_rejects_invalid_membership_instead_of_silently_publishing_singletons():
    views = [_view("A"), _view("B", bbox=_bbox(700, 100, 1200, 600))]
    with pytest.raises(DetectionV82ContractError, match="none satisfied"):
        run_detection_v82_pipeline(
            ocr_package=_ocr(), source_facts=_facts(), page_dimensions={1: (2000, 2000)},
            discover=lambda _candidates: [{
                "page_number": 1, "bbox": view["bbox"], "core_bbox": view["core_bbox"], "representation_kind": view["representation_kind"], "decision": "object_evidence", "exclusion_kind": "other", "visual_description": view["visual_description"], "reason": view["reason"],
            } for view in views],
            resolve_conflict=lambda target: {"target_id": target["target_id"], "decision": "exclude", "reason": "not needed"},
            review_membership=lambda _views: [{"group_id_a": "unknown", "group_id_b": "B", "proofs": [_proof("matching_topology"), _proof("dimension_equality")] }],
        )


def test_v82_components_are_invariant_to_membership_order():
    views = [_view("A"), _view("B", bbox=_bbox(700, 100, 1200, 600)), _view("C", bbox=_bbox(1300, 100, 1800, 600))]
    links = [
        {"group_id_a": "A", "group_id_b": "B", "proofs": [_proof("matching_topology"), _proof("dimension_equality")]},
        {"group_id_a": "B", "group_id_b": "C", "proofs": [_proof("matching_topology"), _proof("direct_shared_structure")]},
    ]
    first, _ = normalize_detection_v82_membership_links(links, object_evidence=views)
    second, _ = normalize_detection_v82_membership_links(list(reversed(deepcopy(links))), object_evidence=views)

    assert compile_detection_v82_components(object_evidence=views, membership_links=first) == compile_detection_v82_components(object_evidence=views, membership_links=second)


def test_v82_adapter_membership_uses_literal_view_ids_not_undeclared_registry_source_ids():
    from PIL import Image

    image = Image.new("RGB", (2000, 2000), "white")
    encoded = BytesIO()
    image.save(encoded, format="JPEG")

    def request(stage, _prompt, _schema, content, _max_tokens):
        if stage == "discovery":
            return {"islands": [
                {"page_number": 1, "bbox": _bbox(100, 100, 600, 600), "core_bbox": _bbox(120, 120, 580, 580), "representation_kind": "technical_elevation", "decision": "object_evidence", "exclusion_kind": "other", "visual_description": "triangular shelving elevation", "reason": "dimensioned technical view"},
                {"page_number": 1, "bbox": _bbox(700, 100, 1200, 600), "core_bbox": _bbox(720, 120, 1180, 580), "representation_kind": "technical_detail", "decision": "object_evidence", "exclusion_kind": "other", "visual_description": "triangular shelving detail", "reason": "matching technical detail"},
            ]}, {"input_tokens": 1, "output_tokens": 1}
        if stage == "membership":
            text = str(content[-1]["text"])
            assert "registry_view:" not in text
            ids = re.findall(r"^(V82-I-[^|]+)\|P", text, flags=re.MULTILINE)
            assert len(ids) == 2
            return {"links": [{"group_id_a": ids[0], "group_id_b": ids[1], "proofs": [_proof("matching_topology"), _proof("dimension_equality")]}]}, {"input_tokens": 1, "output_tokens": 1}
        raise AssertionError(stage)

    _visual_map, registry, audit = run_detection_v82_with_request(
        file_name="fixture.pdf", company_id="test", file_bytes=b"pdf", page_images=[encoded.getvalue()], ocr_package=_ocr(), request_json=request,
    )

    assert len(registry["objects"]) == 1
    assert len(audit["pipeline"]["membership"]["accepted_links"]) == 1


def test_v82_membership_global_board_is_stable_and_precedes_individual_crops():
    from PIL import Image
    from agents.detection_v82_adapter import (
        _build_membership_board,
        _build_membership_crops,
        _membership_content,
    )

    image = Image.new("RGB", (2000, 2000), "white")
    encoded = BytesIO()
    image.save(encoded, format="JPEG")
    page_images = [encoded.getvalue(), encoded.getvalue()]
    frames = {
        1: {"fusion_dimensions": {"width": 2000, "height": 2000}, "review_dimensions": {"width": 2000, "height": 2000}},
        2: {"fusion_dimensions": {"width": 2000, "height": 2000}, "review_dimensions": {"width": 2000, "height": 2000}},
    }
    first = _view("B", bbox=_bbox(100, 100, 600, 600))
    second = {**_view("A", bbox=_bbox(700, 100, 1200, 600)), "page_number": 2}

    crops, _audit = _build_membership_crops(page_images=page_images, views=[second, first], frames=frames)
    board = _build_membership_board(crops=crops, views=[second, first])
    content = _membership_content(context="FIXED OBJECT EVIDENCE VIEWS", crops=crops, board=board)

    assert [tile["group_id"] for tile in board["audit"]["tiles"]] == ["B", "A"]
    assert board["audit"]["tiles"][1]["page_number"] == 2
    assert content[0]["type"] == "text"
    assert "GLOBAL COMPARISON BOARD" in content[0]["text"]
    assert content[1]["type"] == "image"


def test_v82_is_explicitly_versioned_and_is_the_default():
    assert _select_detection_pipeline_version() == "v82"
    assert _select_detection_pipeline_version("v82") == "v82"


def _registry_result() -> tuple[dict, dict, dict]:
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False,
            "identity_pages": [1], "estimation_evidence_pages": [1],
            "visual_group_ids": [], "visual_identity": "one object",
            "boundary_basis": "fixture",
        }],
    }
    return {"visual_groups": []}, registry, {"raw_usage": {}}


def test_v82_uses_v82_only_for_the_ordinary_router_category():
    ordinary_route = {
        "category": "ordinary_object_set", "decision": "ordinary_haiku",
        "reasons": ["no_special_category_evidenced"], "registry_model": "test-model",
        "evidence_model": "test-model", "signals": {},
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default=None: default),
        patch("agents.detection_agent.classify_detection_document", return_value=ordinary_route),
        patch("agents.detection_agent.assess_detection_source_capability", return_value={"route_eligible": False, "page_count": 1}),
        patch("agents.detection_agent.run_anthropic_detection_v82", return_value=_registry_result()) as v82,
        patch("agents.detection_agent.run_anthropic_detection_visual_registry_agent", side_effect=AssertionError("legacy route must not run")),
    ):
        from agents.detection_agent import run_detection_agent
        run_detection_agent(file_name="ordinary.pdf", company_id="test", file_bytes=b"pdf", page_images=[b"page"], ocr_package={}, pipeline_version="v82")

    v82.assert_called_once()


def test_v82_preserves_page23_source_degraded_route():
    page23_route = {
        "category": "page23_native_graphic_pack", "decision": "page23_native_graphic_pack",
        "reasons": ["all_pages_lack_usable_coordinate_evidence"], "registry_model": "test-model",
        "evidence_model": "test-model", "signals": {},
    }
    source_visual = {"route": "v5_32", "registry": _registry_result()[1]}
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default=None: default),
        patch("agents.detection_agent.classify_detection_document", return_value=page23_route),
        patch("agents.detection_agent.assess_detection_source_capability", return_value={"route_eligible": True, "page_count": 1}),
        patch("agents.detection_agent.render_detection_pdf_pages", return_value=([b"page"], {})),
        patch("agents.detection_agent.run_anthropic_detection_v82", side_effect=AssertionError("V8.2 must not run for Page 23")),
        patch("agents.detection_agent.run_anthropic_detection_v5_source_degraded_pairwise_structural_admission_audit", return_value=(source_visual, {"raw_usage": {}})) as legacy,
    ):
        from agents.detection_agent import run_detection_agent
        run_detection_agent(file_name="page23.pdf", company_id="test", file_bytes=b"pdf", page_images=[b"page"], ocr_package={}, pipeline_version="v82")

    legacy.assert_called_once()


def test_v82_preserves_ada_route_before_registry():
    ada_route = {
        "category": "ada_sparse_multi_object", "decision": "ada_boundary_risk",
        "reasons": ["multiple_large_drawing_regions_on_single_page"], "registry_model": "boundary-model",
        "evidence_model": "base-model", "signals": {},
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default=None: default),
        patch("agents.detection_agent.classify_detection_document", return_value=ada_route),
        patch("agents.detection_agent.assess_detection_source_capability", return_value={"route_eligible": False, "page_count": 1}),
        patch("agents.detection_agent.run_anthropic_detection_v82", side_effect=AssertionError("V8.2 must not run for ADA")),
        patch("agents.detection_agent.run_anthropic_detection_v627_scope_scout", return_value=({"classification": "multi_object_risk"}, {"raw_usage": {}})),
        patch("agents.detection_agent.run_anthropic_detection_visual_registry_agent", return_value=_registry_result()) as legacy,
    ):
        from agents.detection_agent import run_detection_agent
        run_detection_agent(file_name="ada.pdf", company_id="test", file_bytes=b"pdf", page_images=[b"page"], ocr_package={}, pipeline_version="v82")

    legacy.assert_called_once()
