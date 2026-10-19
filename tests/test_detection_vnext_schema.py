import pytest

from agents.anthropic_adapter import (
    DETECTION_VISUAL_REGISTRY_JSON_SCHEMA,
    discard_degenerate_evidence_regions,
)
from agents.schemas.detection_registry_schema import (
    DETECTION_REGISTRY_JSON_SCHEMA,
    DetectionRegistrySchemaError,
    validate_detection_pairwise_merge_proofs,
    validate_detection_registry,
)
from agents.schemas.detection_schema import validate_detection_result
from agents.schemas.detection_visual_map_schema import (
    DetectionVisualMapSchemaError,
    normalize_detection_visual_map_group_ids,
    validate_detection_visual_map,
)


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
            "review_required": False, "evidence_pages": "1", "approved": False, "created_at": "unknown",
            "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "regions": [{"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40}],
                "presentation_preview_bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            }],
        }],
    })

    assert result["detected_objects"][0]["evidence_page_refs"][0]["regions"]


def test_degenerate_evidence_regions_are_dropped_but_the_page_is_preserved():
    result = {
        "detected_objects": [{
            "evidence_page_refs": [{
                "page_number": 3,
                "source_label": "Detail",
                "regions": [
                    {"top_left_x": 20, "top_left_y": 10, "bottom_right_x": 20, "bottom_right_y": 50},
                ],
                "presentation_preview_bbox": {"top_left_x": 5, "top_left_y": 5, "bottom_right_x": 5, "bottom_right_y": 30},
            }],
        }],
    }

    normalized = discard_degenerate_evidence_regions(result)
    ref = normalized["detected_objects"][0]["evidence_page_refs"][0]

    assert ref["page_number"] == 3
    assert ref["regions"] == []
    assert "presentation_preview_bbox" not in ref


def test_visual_map_and_registry_keep_representation_identity_separate():
    visual_map = validate_detection_visual_map({
        "visual_groups": [
            {"group_id": "view-001", "page_number": 1, "location_hint": "lower left", "visual_description": "long storage console perspective", "representation_kind": "perspective"},
            {"group_id": "view-002", "page_number": 1, "location_hint": "lower right", "visual_description": "long storage console alternate perspective", "representation_kind": "perspective"},
        ],
    })
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "one long storage console shown twice",
            "boundary_basis": "matching full-page structure and panel sequence",
        }],
    }

    assert validate_detection_registry(
        registry,
        visual_group_ids={group["group_id"] for group in visual_map["visual_groups"]},
    ) == registry


def test_pairwise_merge_proofs_require_two_independent_signals_and_a_minimal_tree():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1, 2],
            "estimation_evidence_pages": [1, 2],
            "visual_group_ids": ["view-001", "view-002", "view-003"],
            "visual_identity": "one sliding-door system in three views",
            "boundary_basis": "matching track, bay topology and door sequence",
        }],
    }
    proofs = [
        {
            "object_id": "object-001", "from_group_id": "view-001",
            "to_group_id": "view-002",
            "relationship": "same_object_view",
            "evidence_facts": [
                {"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "The same three leaves recur."},
                {"evidence_type": "unique_geometry", "evidence_pages": [1], "observation": "The offset handle sequence recurs."},
            ],
            "commercial_inseparability": "Both views show the same single track assembly.",
        },
        {
            "object_id": "object-001", "from_group_id": "view-002",
            "to_group_id": "view-003",
            "relationship": "same_object_view",
            "evidence_facts": [
                {"evidence_type": "dimension_transform", "evidence_pages": [1, 2], "observation": "The elevation width matches the plan after the view-axis change."},
                {"evidence_type": "matching_topology", "evidence_pages": [1, 2], "observation": "The bay and leaf order matches in both views."},
            ],
            "commercial_inseparability": "The leaves use one common track and frame.",
        },
    ]

    assert validate_detection_pairwise_merge_proofs(
        proofs, registry=registry, page_count=2
    ) == proofs


def test_pairwise_merge_proof_rejects_a_lone_direct_structure_claim():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "claimed integrated furniture", "boundary_basis": "one system",
        }],
    }
    proofs = [{
        "object_id": "object-001", "from_group_id": "view-001",
        "to_group_id": "view-002", "relationship": "same_object_view",
        "evidence_facts": [{"evidence_type": "direct_shared_structure", "evidence_pages": [1], "observation": "An L-shaped junction is drawn."}],
        "commercial_inseparability": "The furniture appears connected.",
    }]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="needs two independent evidence facts",
    ):
        validate_detection_pairwise_merge_proofs(proofs, registry=registry, page_count=1)


def test_pairwise_merge_proof_accepts_two_distinct_dimension_facts():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1, 2],
            "estimation_evidence_pages": [1, 2],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "one cabinet in elevation and section",
            "boundary_basis": "two transformed dimensions agree",
        }],
    }
    proofs = [{
        "object_id": "object-001", "from_group_id": "view-001",
        "to_group_id": "view-002", "relationship": "same_object_view",
        "evidence_facts": [
            {"evidence_type": "dimension_transform", "evidence_pages": [1, 2], "observation": "The 1180 mm elevation width matches the horizontal section dimension."},
            {"evidence_type": "dimension_transform", "evidence_pages": [1, 2], "observation": "The 2450 mm elevation height matches the vertical section dimension."},
        ],
        "commercial_inseparability": "The two views specify one cabinet envelope.",
    }]

    assert validate_detection_pairwise_merge_proofs(
        proofs, registry=registry, page_count=2
    ) == proofs


def test_pairwise_merge_proof_rejects_a_repeated_typed_fact():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "one cabinet in two views",
            "boundary_basis": "claimed matching width",
        }],
    }
    fact = {
        "evidence_type": "dimension_transform", "evidence_pages": [1],
        "observation": "The 1180 mm elevation width matches the section width.",
    }
    proofs = [{
        "object_id": "object-001", "from_group_id": "view-001",
        "to_group_id": "view-002", "relationship": "same_object_view",
        "evidence_facts": [fact, fact],
        "commercial_inseparability": "The two views specify one cabinet envelope.",
    }]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="evidence facts are invalid",
    ):
        validate_detection_pairwise_merge_proofs(proofs, registry=registry, page_count=1)


def test_pairwise_object_detail_proof_accepts_explicit_document_relation():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "N76B",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [11],
            "estimation_evidence_pages": [11],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "slatted partition and its section",
            "boundary_basis": "both views carry the N76B drawing code",
        }],
    }
    proofs = [{
        "object_id": "object-001", "from_group_id": "view-001",
        "to_group_id": "view-002", "relationship": "object_detail",
        "evidence_facts": [{"evidence_type": "explicit_document_relation", "evidence_pages": [11], "observation": "The N76B code applies to the elevation and section."}],
        "commercial_inseparability": "The section specifies construction of the same N76B partition.",
    }]

    assert validate_detection_pairwise_merge_proofs(
        proofs, registry=registry, page_count=11
    ) == proofs


def test_pairwise_merge_proof_rejects_singleton_placeholder():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "N76",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
            "visual_identity": "one cabinet elevation",
            "boundary_basis": "one complete dimensioned cabinet",
        }],
    }
    placeholder = [{
        "object_id": "object-001", "from_group_id": "view-001",
        "to_group_id": "view-001", "relationship": "same_object_view",
        "evidence_facts": [{"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "Single view"}],
        "commercial_inseparability": "N/A",
    }]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="pairwise merge proof groups are invalid",
    ):
        validate_detection_pairwise_merge_proofs(
            placeholder, registry=registry, page_count=1
        )


def test_registry_schema_requires_at_least_one_visual_group_per_object():
    visual_group_ids = (
        DETECTION_REGISTRY_JSON_SCHEMA["properties"]["objects"]
        ["items"]["properties"]["visual_group_ids"]
    )

    assert visual_group_ids["minItems"] == 1


def test_visual_map_normalizes_provider_group_ids_before_strict_validation():
    visual_map = {
        "visual_groups": [
            {"group_id": "group_a", "page_number": 1, "location_hint": "left", "visual_description": "console view", "representation_kind": "perspective"},
            {"group_id": "group_b", "page_number": 1, "location_hint": "right", "visual_description": "console view", "representation_kind": "elevation"},
        ],
    }

    normalized = validate_detection_visual_map(
        normalize_detection_visual_map_group_ids(visual_map)
    )

    assert [group["group_id"] for group in normalized["visual_groups"]] == [
        "view-001", "view-002",
    ]


def test_registry_allows_shared_object_evidence_when_it_supports_both_objects():
    registry = {
        "objects": [
            {"object_id": "object-001", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "first", "boundary_basis": "first"},
            {"object_id": "object-002", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "second", "boundary_basis": "second"},
        ],
    }

    assert validate_detection_registry(
        registry,
        visual_group_ids={"view-001"},
        object_evidence_group_ids={"view-001"},
    ) == registry


def test_registry_allows_unassigned_document_context_groups():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001"], "visual_identity": "cabinet",
            "boundary_basis": "one complete product",
        }],
    }

    assert validate_detection_registry(
        registry,
        visual_group_ids={"view-001", "view-002"},
        object_evidence_group_ids={"view-001"},
    ) == registry


def test_registry_requires_every_object_evidence_group_to_be_accounted_for():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
            "visual_identity": "cabinet", "boundary_basis": "one complete product",
        }],
    }

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="must account for every object-evidence group",
    ) as raised:
        validate_detection_registry(
            registry,
            visual_group_ids={"view-001", "view-002"},
            object_evidence_group_ids={"view-001", "view-002"},
        )

    assert raised.value.details == {
        "unassigned_object_evidence_group_ids": ["view-002"],
    }


def test_integrated_visual_map_requires_an_evidence_class_for_each_group():
    visual_map = {
        "visual_groups": [
            {
                "group_id": "view-001", "page_number": 1,
                "location_hint": "left", "visual_description": "cabinet",
                "representation_kind": "elevation",
                "evidence_class": "object_evidence",
            },
            {
                "group_id": "view-002", "page_number": 1,
                "location_hint": "title block", "visual_description": "sheet metadata",
                "representation_kind": "title_block",
                "evidence_class": "document_context",
            },
        ],
    }

    assert validate_detection_visual_map(
        visual_map,
        require_evidence_class=True,
    ) == visual_map


def test_integrated_registry_structured_output_requires_group_owners_only():
    group_schema = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"][
        "visual_groups"
    ]["items"]

    assert "owner_object_ids" in group_schema["required"]
    assert "evidence_class" not in group_schema["properties"]
    assert "depiction_scope" not in group_schema["required"]
    assert "scope_basis" not in group_schema["required"]
    assert "commercial_role" not in group_schema["properties"]
    assert "role_basis" not in group_schema["properties"]


def test_visual_map_rejects_unknown_evidence_class():
    visual_map = {
        "visual_groups": [{
            "group_id": "view-001", "page_number": 1,
            "location_hint": "center", "visual_description": "cabinet elevation",
            "representation_kind": "elevation", "evidence_class": "unknown",
        }],
    }

    with pytest.raises(DetectionVisualMapSchemaError, match="visual group is invalid"):
        validate_detection_visual_map(visual_map, require_evidence_class=True)


def test_object_evidence_class_keeps_details_linkable_to_an_object():
    visual_map = {
        "visual_groups": [
            {
                "group_id": "view-001", "page_number": 1,
                "location_hint": "front", "visual_description": "cabinet elevation",
                "representation_kind": "elevation", "evidence_class": "object_evidence",
            },
            {
                "group_id": "view-002", "page_number": 1,
                "location_hint": "cut", "visual_description": "panel section",
                "representation_kind": "section", "evidence_class": "object_evidence",
            },
        ],
    }

    assert validate_detection_visual_map(
        visual_map, require_evidence_class=True
    ) == visual_map


def test_registry_rejects_document_context_as_object_boundary_support():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
            "visual_identity": "cabinet", "boundary_basis": "one cabinet",
        }],
    }

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="must be object evidence",
    ) as raised:
        validate_detection_registry(
            registry,
            visual_group_ids={"view-001"},
            object_evidence_group_ids=set(),
        )

    assert raised.value.details == {"non_object_evidence_group_ids": ["view-001"]}
