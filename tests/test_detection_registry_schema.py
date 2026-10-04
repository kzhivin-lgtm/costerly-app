import pytest

from agents.schemas.detection_registry_schema import (
    DetectionRegistrySchemaError,
    validate_detection_registry,
)


def _registry(commercial_class: str) -> dict:
    return {
        "objects": [{
            "object_id": "object-001",
            "transport_label": "Object 1",
            "commercial_class": commercial_class,
            "quantity": 1,
            "quantity_explicit": False,
            "identity_pages": [1],
            "dossier_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_identity": "one continuous opening with a shared track",
            "boundary_basis": "one independently installed door system",
        }],
    }


def test_registry_preserves_door_system_classification_before_detection():
    registry = validate_detection_registry(_registry("door_system"))

    assert registry["objects"][0]["commercial_class"] == "door_system"


def test_registry_rejects_an_unknown_commercial_class():
    with pytest.raises(DetectionRegistrySchemaError, match="fields do not match contract|commercial class"):
        validate_detection_registry(_registry("door_leaf"))
