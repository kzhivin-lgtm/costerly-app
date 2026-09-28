import pytest

from agents.schemas.material_identity_agent_schema import (
    validate_material_identity_decisions,
)


REQUESTS = [
    {
        "source_row_id": "row-1",
        "candidates": [{"material_id": "material-1"}],
    }
]


def _result(**changes):
    row = {
        "source_row_id": "row-1",
        "decision": "link_existing",
        "selected_material_id": "material-1",
        "confidence": 94,
        "reason": "Same family and specifications",
    }
    row.update(changes)
    return {"decisions": [row]}


def test_identity_agent_can_only_select_a_supplied_candidate():
    with pytest.raises(ValueError, match="supplied candidates"):
        validate_material_identity_decisions(
            REQUESTS, _result(selected_material_id="material-outside-shortlist")
        )


def test_non_link_decision_cannot_select_a_material():
    with pytest.raises(ValueError, match="only link_existing"):
        validate_material_identity_decisions(
            REQUESTS, _result(decision="new_variant")
        )


def test_identity_agent_must_decide_every_requested_row_once():
    with pytest.raises(ValueError, match="must decide every"):
        validate_material_identity_decisions(REQUESTS, {"decisions": []})


def test_valid_bounded_link_is_accepted():
    decisions = validate_material_identity_decisions(REQUESTS, _result())

    assert decisions[0]["selected_material_id"] == "material-1"
