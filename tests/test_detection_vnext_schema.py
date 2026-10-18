import pytest

from agents.anthropic_adapter import discard_degenerate_evidence_regions
from agents.schemas.detection_registry_schema import (
    DETECTION_REPRESENTATION_PACKAGE_JSON_SCHEMA,
    DETECTION_REGISTRY_JSON_SCHEMA,
    DetectionRegistrySchemaError,
    validate_detection_pairwise_merge_proofs,
    validate_detection_representation_packages,
    validate_detection_registry,
)
from agents.schemas.detection_schema import validate_detection_result
from agents.schemas.detection_visual_map_schema import (
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
            "evidence_types": ["matching_topology", "unique_geometry"],
            "evidence_pages": [1],
            "observed_fact": "The same three leaves and offset handle sequence recur.",
            "commercial_inseparability": "Both views show the same single track assembly.",
        },
        {
            "object_id": "object-001", "from_group_id": "view-002",
            "to_group_id": "view-003",
            "evidence_types": ["dimension_transform", "matching_topology"],
            "evidence_pages": [1, 2],
            "observed_fact": "The elevation width matches the plan after the view-axis change.",
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
        "to_group_id": "view-002", "evidence_types": ["direct_shared_structure"],
        "evidence_pages": [1], "observed_fact": "An L-shaped junction is drawn.",
        "commercial_inseparability": "The furniture appears connected.",
    }]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="needs two independent evidence types",
    ):
        validate_detection_pairwise_merge_proofs(proofs, registry=registry, page_count=1)


def test_representation_package_connects_one_complete_view_with_its_details():
    visual_groups = [
        {
            "group_id": "view-001", "page_number": 11,
            "location_hint": "centre", "visual_description": "complete frontal shelving elevation N76B",
            "representation_kind": "elevation", "commercial_role": "assembly_view",
        },
        {
            "group_id": "view-002", "page_number": 11,
            "location_hint": "upper", "visual_description": "N76B plan and profile detail",
            "representation_kind": "plan_detail", "commercial_role": "component_detail",
        },
    ]
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "N76B",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [11],
            "estimation_evidence_pages": [11], "visual_group_ids": ["view-001"],
            "visual_identity": "N76B shelving unit", "boundary_basis": "complete coded frontal elevation",
        }],
    }
    packages = [{
        "package_id": "package-001", "object_id": "object-001",
        "assembly_view_group_ids": ["view-001"],
        "supporting_component_detail_group_ids": ["view-002"],
        "package_basis": "The N76B code, full elevation and supporting plan describe one shelving unit.",
    }]

    assert validate_detection_representation_packages(
        packages, visual_groups=visual_groups, registry=registry,
    ) == packages


def test_representation_package_keeps_a_complete_grid_elevation_as_an_assembly_view():
    visual_groups = [
        {
            "group_id": "view-001", "page_number": 11,
            "location_hint": "upper", "visual_description": "N76B plan view",
            "representation_kind": "plan", "commercial_role": "assembly_view",
        },
        {
            "group_id": "view-002", "page_number": 11,
            "location_hint": "lower", "visual_description": "N76B complete frontal grid elevation",
            "representation_kind": "elevation", "commercial_role": "assembly_view",
        },
        {
            "group_id": "view-003", "page_number": 11,
            "location_hint": "right", "visual_description": "N76B section detail",
            "representation_kind": "section", "commercial_role": "component_detail",
        },
    ]
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "N76B",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [11],
            "estimation_evidence_pages": [11],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "N76B shelving unit", "boundary_basis": "coded plan and full elevation",
        }],
    }
    packages = [{
        "package_id": "package-001", "object_id": "object-001",
        "assembly_view_group_ids": ["view-001", "view-002"],
        "supporting_component_detail_group_ids": ["view-003"],
        "package_basis": "The coded plan and complete grid elevation describe the same N76B unit.",
    }]

    assert validate_detection_representation_packages(
        packages, visual_groups=visual_groups, registry=registry,
    ) == packages


def test_representation_package_schema_leaves_bookkeeping_ids_to_the_runtime():
    package_schema = DETECTION_REPRESENTATION_PACKAGE_JSON_SCHEMA["items"]

    assert package_schema["required"] == [
        "object_id",
        "assembly_view_group_ids",
        "supporting_component_detail_group_ids",
        "package_basis",
    ]
    assert "package_id" not in package_schema["properties"]
    assert package_schema["properties"]["object_id"]["minLength"] == 1


def test_representation_packages_require_every_assembly_view_once():
    visual_groups = [
        {
            "group_id": "view-001", "page_number": 1, "location_hint": "left",
            "visual_description": "cabinet elevation", "representation_kind": "elevation",
            "commercial_role": "assembly_view",
        },
        {
            "group_id": "view-002", "page_number": 1, "location_hint": "right",
            "visual_description": "console elevation", "representation_kind": "elevation",
            "commercial_role": "assembly_view",
        },
    ]
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
            "visual_identity": "cabinet", "boundary_basis": "complete cabinet",
        }],
    }
    packages = [{
        "package_id": "package-001", "object_id": "object-001",
        "assembly_view_group_ids": ["view-001"],
        "supporting_component_detail_group_ids": [], "package_basis": "cabinet view",
    }]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="account for every assembly view exactly once",
    ):
        validate_detection_representation_packages(
            packages, visual_groups=visual_groups, registry=registry,
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


def test_registry_rejects_shared_visual_group_ownership_but_keeps_owners_for_audit():
    registry = {
        "objects": [
            {"object_id": "object-001", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "first", "boundary_basis": "first"},
            {"object_id": "object-002", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "second", "boundary_basis": "second"},
        ],
    }

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="must have one commercial-object owner",
    ) as raised:
        validate_detection_registry(registry, visual_group_ids={"view-001"})

    assert raised.value.details == {
        "duplicate_visual_group_owners": {
            "view-001": ["object-001", "object-002"],
        },
    }


def test_registry_allows_unassigned_navigation_only_visual_groups():
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
    ) == registry


def test_integrated_visual_map_requires_a_commercial_role_for_each_group():
    visual_map = {
        "visual_groups": [
            {
                "group_id": "view-001", "page_number": 1,
                "location_hint": "left", "visual_description": "cabinet",
                "representation_kind": "elevation", "commercial_role": "assembly_view",
            },
            {
                "group_id": "view-002", "page_number": 1,
                "location_hint": "title block", "visual_description": "sheet metadata",
                "representation_kind": "title_block", "commercial_role": "document_context",
            },
        ],
    }

    assert validate_detection_visual_map(
        visual_map,
        require_commercial_roles=True,
    ) == visual_map


def test_registry_rejects_component_detail_as_commercial_boundary_support():
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
        match="must be complete assembly views",
    ) as raised:
        validate_detection_registry(
            registry,
            visual_group_ids={"view-001"},
            visual_group_roles={"view-001": "component_detail"},
        )

    assert raised.value.details == {"non_assembly_visual_group_ids": ["view-001"]}
