from copy import deepcopy

from agents.detection_v8 import (
    DETECTION_V8_DISCOVERY_SCHEMA,
    DETECTION_V8_MEMBERSHIP_SCHEMA,
    apply_detection_v8_conflict_decisions,
    audit_detection_v8_candidate_coverage,
    build_detection_v8_candidate_regions,
    compile_detection_v8_components,
    normalize_detection_v8_discovery,
    normalize_detection_v8_membership_links,
    run_detection_v8_pipeline,
    select_detection_v8_conflict_targets,
)
from agents.prompt_loader import (
    load_detection_v8_discovery_prompt,
    load_detection_v8_membership_prompt,
)


def _bbox(left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    return {
        "top_left_x": left,
        "top_left_y": top,
        "bottom_right_x": right,
        "bottom_right_y": bottom,
    }


def _ocr() -> dict:
    return {"pages": [{
        "page_number": 1,
        "dimensions": {"width": 2000, "height": 2000},
        "blocks": [{"type": "image", **_bbox(100, 100, 900, 900)}],
    }]}


def _dimension_facts() -> list[dict]:
    return [
        {
            "fact_id": "SF-1", "page_number": 1, "source": "native_pdf_text",
            "text": "600", "bbox": _bbox(1300, 1000, 1310, 1010),
        },
        {
            "fact_id": "SF-2", "page_number": 1, "source": "native_pdf_text",
            "text": "800", "bbox": _bbox(1450, 1000, 1460, 1010),
        },
    ]


def _view(group_id: str, *, kind: str = "technical_elevation") -> dict:
    return {
        "group_id": group_id,
        "page_number": 1,
        "bbox": _bbox(100, 100, 600, 600),
        "core_bbox": _bbox(120, 120, 580, 580),
        "representation_kind": kind,
        "visual_description": "distinct fabricated construction",
        "reason": "visible technical drawing",
        "evidence_class": "object_evidence",
    }


def _evidence(left: str, right: str, evidence_type: str) -> dict:
    return {
        "evidence_type": evidence_type,
        "observation": "distinctive triangular shelving configuration is visible in both views",
        "source_fact_ids": [f"registry_view:{left}", f"registry_view:{right}"],
    }


def test_v8_always_unions_mypdf_clusters_with_mistral_regions_without_object_proxy():
    candidates = build_detection_v8_candidate_regions(_ocr(), _dimension_facts())

    assert len(candidates) == 2
    assert candidates[0]["sources"] == ["mistral_graphic"]
    assert candidates[1]["sources"] == ["mypdf_dimensions"]
    assert candidates[1]["technical_signal"] is True
    assert "role" not in candidates[1]
    assert "evidence_class" not in candidates[1]


def test_v8_candidate_identity_does_not_change_when_an_unrelated_region_is_added():
    original = build_detection_v8_candidate_regions(_ocr(), _dimension_facts())
    changed_ocr = _ocr()
    changed_ocr["pages"][0]["blocks"].append({
        "type": "image", **_bbox(1000, 100, 1200, 300),
    })
    with_unrelated = build_detection_v8_candidate_regions(changed_ocr, _dimension_facts())

    original_ids = {row["candidate_region_id"] for row in original}
    changed_ids = {row["candidate_region_id"] for row in with_unrelated}
    assert original_ids <= changed_ids


def test_v8_excludes_dominant_floor_plan_during_discovery_and_never_routes_it_to_resolver():
    candidate = {
        "candidate_region_id": "candidate-plan", "page_number": 1,
        "bbox": _bbox(0, 0, 1000, 1000), "technical_signal": True,
    }
    objects, exclusions = normalize_detection_v8_discovery([{
        "page_number": 1,
        "bbox": _bbox(0, 0, 1000, 1000),
        "core_bbox": _bbox(0, 0, 1000, 1000),
        "representation_kind": "floor_plan",
        "decision": "object_evidence",
        "reason": "whole level architectural room and circulation plan",
    }], page_dimensions={1: (1000, 1000)})

    coverage = audit_detection_v8_candidate_coverage(
        candidates=[candidate], object_evidence=objects, exclusions=exclusions,
    )

    assert objects == []
    assert exclusions[0]["exclusion_kind"] == "floor_plan"
    assert coverage[0]["status"] == "covered_by_terminal_exclusion"
    assert select_detection_v8_conflict_targets(
        candidates=[candidate], coverage_audit=coverage,
    ) == []


def test_v8_conflict_resolver_is_only_selected_for_unexplained_technical_candidate():
    candidate = {
        "candidate_region_id": "candidate-p10", "page_number": 10,
        "bbox": _bbox(1200, 1200, 1800, 1800), "technical_signal": True,
        "source_fact_ids": ["SF-1", "SF-2"],
    }
    coverage = [{
        "candidate_region_id": "candidate-p10", "page_number": 10,
        "technical_signal": True, "status": "unexplained",
        "object_group_ids": [], "exclusion_group_ids": [],
    }]

    targets = select_detection_v8_conflict_targets(
        candidates=[candidate], coverage_audit=coverage,
    )
    admitted, audit = apply_detection_v8_conflict_decisions(
        object_evidence=[], targets=targets,
        decisions=[{
            "target_id": targets[0]["target_id"], "decision": "object_evidence",
            "bbox": _bbox(1220, 1220, 1780, 1780),
            "core_bbox": _bbox(1240, 1240, 1760, 1760),
            "representation_kind": "technical_elevation",
            "visual_description": "separate cabinet elevation",
            "reason": "separate fabricated cabinet elevation with dimensions",
        }],
        page_dimensions={10: (2000, 2000)},
    )

    assert len(targets) == 1
    assert admitted[0]["evidence_class"] == "object_evidence"
    assert audit[0]["admitted_group_id"] == admitted[0]["group_id"]


def test_v8_membership_has_one_link_contract_for_technical_views_and_renders():
    technical_a = _view("A")
    technical_b = _view("B")
    render = _view("R", kind="presentation_render")
    links, rejected = normalize_detection_v8_membership_links([
        {
            "group_id_a": "A", "group_id_b": "B",
            "evidence": [_evidence("A", "B", "matching_topology"), _evidence("A", "B", "dimension_equality")],
        },
        {
            "group_id_a": "R", "group_id_b": "A",
            "evidence": [_evidence("R", "A", "unique_geometry")],
        },
    ], object_evidence=[technical_a, technical_b, render])

    components, excluded = compile_detection_v8_components(
        object_evidence=[technical_a, technical_b, render], membership_links=links,
    )

    assert rejected == []
    assert components == [["A", "B", "R"]]
    assert excluded == []


def test_v8_rejects_weak_technical_link_and_excludes_unattached_render():
    technical = _view("T")
    render = _view("R", kind="presentation_render")
    links, rejected = normalize_detection_v8_membership_links([
        {
            "group_id_a": "T", "group_id_b": "R",
            "evidence": [_evidence("T", "R", "dimension_equality")],
        },
    ], object_evidence=[technical, render])

    components, excluded = compile_detection_v8_components(
        object_evidence=[technical, render], membership_links=links,
    )

    assert links == []
    assert rejected[0]["reason"] == "render_link_requires_one_technical_endpoint_and_visual_proof"
    assert components == [["T"]]
    assert excluded == ["R"]


def test_v8_membership_rejects_a_link_that_cites_an_unknown_source_fact():
    left, right = _view("A"), _view("B")
    links, rejected = normalize_detection_v8_membership_links([{
        "group_id_a": "A", "group_id_b": "B",
        "evidence": [
            _evidence("A", "B", "matching_topology"),
            {
                "evidence_type": "dimension_equality",
                "observation": "600 and 600 are printed beside both elevations",
                "source_fact_ids": ["registry_view:A", "registry_view:B", "SF-NOT-PRESENT"],
            },
        ],
    }], object_evidence=[left, right], known_source_fact_ids={"SF-REAL"})

    assert links == []
    assert rejected[0]["reason"] == "evidence_not_grounded"


def test_v8_end_to_end_has_no_special_conflict_membership_path():
    def discover(_candidates: list[dict]) -> list[dict]:
        return [{
            "page_number": 1,
            "bbox": _bbox(100, 100, 900, 900),
            "core_bbox": _bbox(120, 120, 880, 880),
            "representation_kind": "technical_elevation",
            "decision": "object_evidence",
            "reason": "main technical elevation",
        }]

    def resolve(target: dict) -> dict:
        return {
            "target_id": target["target_id"], "decision": "object_evidence",
            "bbox": _bbox(1300, 900, 1700, 1400),
            "core_bbox": _bbox(1320, 920, 1680, 1380),
            "representation_kind": "technical_elevation",
            "reason": "separate technical elevation with dimensions",
        }

    def review(views: list[dict]) -> list[dict]:
        assert {view["evidence_class"] for view in views} == {"object_evidence"}
        left, right = sorted(view["group_id"] for view in views)
        return [{
            "group_id_a": left, "group_id_b": right,
            "evidence": [_evidence(left, right, "matching_topology"), _evidence(left, right, "dimension_equality")],
        }]

    result = run_detection_v8_pipeline(
        ocr_package=_ocr(), source_facts=_dimension_facts(),
        page_dimensions={1: (2000, 2000)},
        discover=discover, resolve_conflict=resolve, review_membership=review,
    )

    assert result["conflict_resolver"]["attempted"] is True
    assert len(result["components"]) == 1
    assert len(result["components"][0]) == 2
    assert "conflict_pair_decisions" not in result["membership"]


def test_v8_components_are_invariant_to_membership_link_order():
    views = [_view("A"), _view("B"), _view("C")]
    links = [
        {"group_id_a": "A", "group_id_b": "B", "evidence": [_evidence("A", "B", "matching_topology"), _evidence("A", "B", "dimension_equality")]},
        {"group_id_a": "B", "group_id_b": "C", "evidence": [_evidence("B", "C", "unique_geometry"), _evidence("B", "C", "dimension_equality")]},
    ]
    first, _ = normalize_detection_v8_membership_links(links, object_evidence=views)
    second, _ = normalize_detection_v8_membership_links(list(reversed(deepcopy(links))), object_evidence=views)

    assert compile_detection_v8_components(object_evidence=views, membership_links=first) == compile_detection_v8_components(
        object_evidence=views, membership_links=second,
    )


def test_v8_has_two_ordinary_provider_contracts_without_render_or_conflict_side_arrays():
    discovery_prompt = load_detection_v8_discovery_prompt()
    membership_prompt = load_detection_v8_membership_prompt()

    assert "presentation_render_decisions" not in DETECTION_V8_MEMBERSHIP_SCHEMA["properties"]
    assert "conflict_pair_decisions" not in DETECTION_V8_MEMBERSHIP_SCHEMA["properties"]
    assert DETECTION_V8_DISCOVERY_SCHEMA["required"] == ["islands"]
    assert "Candidate Region is only a recall aid" in discovery_prompt
    assert "Absence of a\nlink means no merge" in membership_prompt
