import pytest

from agents.estimation_object_to_estimate_agent import _validate_batch_response


def _batch():
    return {"batch_id": "geometry-1", "pages": [{"page_number": 1}, {"page_number": 2}]}


def test_geometry_response_must_cover_every_requested_page_once():
    result = _validate_batch_response(
        response={
            "batch_id": "geometry-1", "pages": [{"page_number": 2}, {"page_number": 1}],
            "object_kind": "wardrobe", "dimensions": [], "counts": [], "material_roles": [],
        },
        batch=_batch(),
    )

    assert result["object_kind"] == "wardrobe"


def test_geometry_response_rejects_a_missing_page():
    with pytest.raises(ValueError, match="page coverage"):
        _validate_batch_response(
            response={"batch_id": "geometry-1", "pages": [{"page_number": 1}]}, batch=_batch(),
        )
