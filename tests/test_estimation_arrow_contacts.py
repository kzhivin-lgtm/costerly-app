import pytest

from tools.estimation_native_islands import bind_arrow_tip


def face(ident, box):
    x, y, u, v = box
    return {"id": ident, "polygon": [(x, y), (u, y), (u, v), (x, v)]}


@pytest.mark.parametrize("tip,root,expected", [
    ((5, 5), (5, 20), "panel"),
    ((5, 0), (5, -20), "panel"),
    ((10, 5), (20, 5), "panel"),
    ((5, 10), (5, 20), "panel"),
    ((0, 5), (-20, 5), "panel"),
    ((10.5, 5), (20, 5), "panel"),
    ((11, 5), (20, 5), None),
])
def test_interior_all_edges_and_small_native_contact_error(tip, root, expected):
    result = bind_arrow_tip(tip, root, [face("panel", (0, 0, 10, 10))])
    assert result["hits"] == ([expected] if expected else [])


@pytest.mark.parametrize("root,expected", [((5, 20), "lower"), ((5, -10), "upper")])
def test_shared_edge_belongs_to_panel_from_which_arrow_reaches_it(root, expected):
    result = bind_arrow_tip((5, 10), root, [face("upper", (0, 0, 10, 10)), face("lower", (0, 10, 10, 30))])
    assert result["hits"] == [expected]
    assert result["contact_hits"] == ["lower", "upper"]
    assert result["binding_basis"] == "boundary_incoming"


def test_tangent_shared_edge_keeps_both_candidates_without_inventing_owner():
    result = bind_arrow_tip((5, 10), (-10, 10), [face("upper", (0, 0, 10, 10)), face("lower", (0, 10, 10, 30))])
    assert result["hits"] == []
    assert result["contact_hits"] == ["lower", "upper"]
    assert result["binding_basis"] == "ambiguous_boundary"


def test_sloping_shared_edge_uses_polygon_and_not_bounding_rectangle():
    upper = {"id": "upper", "polygon": [(0, 0), (20, -2), (20, 8), (0, 10)]}
    lower = {"id": "lower", "polygon": [(0, 10), (20, 8), (20, 18), (0, 20)]}
    assert bind_arrow_tip((10, 9), (10, 17), [upper, lower])["hits"] == ["lower"]
