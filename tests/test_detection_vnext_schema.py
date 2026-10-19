import pytest

from agents.anthropic_adapter import (
    DETECTION_VISUAL_REGISTRY_JSON_SCHEMA,
    discard_degenerate_evidence_regions,
)
from agents.schemas.detection_registry_schema import (
    DETECTION_REGISTRY_JSON_SCHEMA,
    DetectionRegistrySchemaError,
    derive_detection_proof_components,
    validate_detection_pairwise_merge_proofs,
    validate_detection_registry,
)
from agents.schemas.detection_schema import validate_detection_result
from agents.schemas.detection_visual_map_schema import (
    normalize_detection_visual_map_group_ids,
    validate_detection_visual_map,
)


def _fact(evidence_type, observation, pages=(1,)):
    return {
        "evidence_type": evidence_type,
        "evidence_pages": list(pages),
        "observation": observation,
    }


def _proof(left, right, facts):
    return {
        "from_group_id": left,
        "to_group_id": right,
        "relationship": "same_object_view",
        "evidence_facts": facts,
        "commercial_inseparability": "The cited construction evidence establishes one quote line.",
    }


def test_v4_schema_accepts_evidence_regions_and_ui_only_preview_bbox():
    result = validate_detection_result({
        "rfq_run": {
            "run_id": "run-1", "company_id": "company-1", "project_name": "Project",
            "file_name": "drawing.pdf", "source_type": "pdf", "design_partner": "unknown",
            "client": "unknown", "author": "unknown", "document_date": "unknown",
            "pages_detected": 1, "language": "en", "file_quality_level": 3,
            "file_quality_label": "detailed_drawings", "file_quality_confidence": 90,
            "file_quality_notes": "", "status": "intake_parsed", "created_at": "unknown",
        },
        "detected_objects": [{
            "run_id": "run-1", "company_id": "company-1", "object_id": "object-001",
            "object_name": "Object 1", "quantity": 1, "quantity_explicit": False,
            "review_required": False, "evidence_pages": "1", "approved": False,
            "created_at": "unknown", "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "regions": [{"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40}],
                "presentation_preview_bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            }],
        }],
    })

    assert result["detected_objects"][0]["evidence_page_refs"][0]["regions"]


def test_degenerate_evidence_regions_are_dropped_but_the_page_is_preserved():
    normalized = discard_degenerate_evidence_regions({
        "detected_objects": [{"evidence_page_refs": [{
            "page_number": 3,
            "regions": [{"top_left_x": 20, "top_left_y": 10, "bottom_right_x": 20, "bottom_right_y": 50}],
            "presentation_preview_bbox": {"top_left_x": 5, "top_left_y": 5, "bottom_right_x": 5, "bottom_right_y": 30},
        }]}],
    })

    reference = normalized["detected_objects"][0]["evidence_page_refs"][0]
    assert reference["page_number"] == 3
    assert reference["regions"] == []
    assert "presentation_preview_bbox" not in reference


def test_proof_graph_derives_one_component_from_two_evidence_backed_edges():
    groups = {"view-001", "view-002", "view-003"}
    proofs = [
        _proof("view-001", "view-002", [
            _fact("matching_topology", "The same three leaves recur."),
            _fact("unique_geometry", "The offset handle sequence recurs."),
        ]),
        _proof("view-002", "view-003", [
            _fact("dimension_transform", "The elevation width matches the plan after axis change.", (1, 2)),
            _fact("matching_topology", "The bay and leaf order matches.", (1, 2)),
        ]),
    ]

    assert validate_detection_pairwise_merge_proofs(
        proofs, visual_group_ids=groups, page_count=2
    ) == proofs
    assert derive_detection_proof_components(proofs, visual_group_ids=groups) == [
        ["view-001", "view-002", "view-003"],
    ]


def test_proof_graph_rejects_a_lone_direct_structure_claim():
    proof = _proof("view-001", "view-002", [
        _fact("direct_shared_structure", "An L-shaped junction is drawn."),
    ])

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="needs two independent evidence facts",
    ):
        validate_detection_pairwise_merge_proofs(
            [proof], visual_group_ids={"view-001", "view-002"}, page_count=1
        )


def test_proof_graph_accepts_two_distinct_dimension_facts():
    proof = _proof("view-001", "view-002", [
        _fact("dimension_transform", "The 1180 mm elevation width matches the section width.", (1, 2)),
        _fact("dimension_transform", "The 2450 mm elevation height matches the section height.", (1, 2)),
    ])

    assert validate_detection_pairwise_merge_proofs(
        [proof], visual_group_ids={"view-001", "view-002"}, page_count=2
    ) == [proof]


def test_proof_graph_rejects_repeated_facts_and_self_links():
    fact = _fact("dimension_transform", "The 1180 mm width matches.")
    repeated = _proof("view-001", "view-002", [fact, fact])
    self_link = _proof("view-001", "view-001", [
        _fact("explicit_document_relation", "N76B labels both depictions."),
    ])

    with pytest.raises(DetectionRegistrySchemaError, match="evidence facts are invalid"):
        validate_detection_pairwise_merge_proofs(
            [repeated], visual_group_ids={"view-001", "view-002"}, page_count=1
        )
    with pytest.raises(DetectionRegistrySchemaError, match="proof groups are invalid"):
        validate_detection_pairwise_merge_proofs(
            [self_link], visual_group_ids={"view-001"}, page_count=1
        )


def test_proof_graph_rejects_cycles_instead_of_deriving_ambiguous_membership():
    proofs = [
        _proof("view-001", "view-002", [_fact("explicit_document_relation", "N76B labels both views.")]),
        _proof("view-002", "view-003", [_fact("explicit_document_relation", "N76B labels both views.")]),
        _proof("view-003", "view-001", [_fact("explicit_document_relation", "N76B labels both views.")]),
    ]

    with pytest.raises(DetectionRegistrySchemaError, match="minimal proof tree"):
        validate_detection_pairwise_merge_proofs(
            proofs, visual_group_ids={"view-001", "view-002", "view-003"}, page_count=1
        )


def test_singleton_visual_group_becomes_a_singleton_component_without_placeholder():
    groups = {"view-001", "view-002"}

    assert validate_detection_pairwise_merge_proofs(
        [], visual_group_ids=groups, page_count=1
    ) == []
    assert derive_detection_proof_components([], visual_group_ids=groups) == [
        ["view-001"], ["view-002"],
    ]


def test_integrated_registry_schema_has_no_model_owner_or_object_id_fields():
    group_properties = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]["visual_groups"]["items"]["properties"]
    object_properties = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]["objects"]["items"]["properties"]
    coverage_properties = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]["page_coverage"]["items"]["properties"]

    assert "owner_object_ids" not in group_properties
    assert "object_id" not in object_properties
    assert "component_anchor_group_id" in object_properties
    assert "component_anchor_group_ids" in coverage_properties


def test_final_registry_requires_every_object_evidence_group_once():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "N76B", "quantity": 1,
        "quantity_explicit": False, "identity_pages": [11],
        "estimation_evidence_pages": [11], "visual_group_ids": ["view-001"],
        "visual_identity": "slatted partition", "boundary_basis": "dimensioned elevation",
    }]}

    assert validate_detection_registry(
        registry, visual_group_ids={"view-001"}, object_evidence_group_ids={"view-001"}
    ) == registry
    with pytest.raises(DetectionRegistrySchemaError, match="must account for every object-evidence group"):
        validate_detection_registry(
            registry, visual_group_ids={"view-001", "view-002"},
            object_evidence_group_ids={"view-001", "view-002"},
        )


def test_visual_map_normalizes_provider_group_ids_before_strict_validation():
    visual_map = validate_detection_visual_map(normalize_detection_visual_map_group_ids({
        "visual_groups": [
            {"group_id": "group_a", "page_number": 1, "location_hint": "left", "visual_description": "console view", "representation_kind": "perspective"},
            {"group_id": "group_b", "page_number": 1, "location_hint": "right", "visual_description": "console view", "representation_kind": "elevation"},
        ],
    }))

    assert [group["group_id"] for group in visual_map["visual_groups"]] == ["view-001", "view-002"]


def test_final_registry_schema_still_requires_nonempty_visual_packages():
    visual_group_ids = DETECTION_REGISTRY_JSON_SCHEMA["properties"]["objects"]["items"]["properties"]["visual_group_ids"]

    assert visual_group_ids["minItems"] == 1
