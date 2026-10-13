from use_cases.estimation import _material_norms_from_plan


def test_object_norms_are_derived_from_sheet_allocations_not_purchase_count():
    norms = _material_norms_from_plan({
        "lines": [{
            "purchase_kind": "sheet",
            # Two purchased sheets are deliberately irrelevant to Object Detail.
            "purchase_quantity": 2,
            "allocations": [{
                "object_id": "cabinet", "material_requirement_id": "mdf",
                "length_mm": 1200, "width_mm": 600, "quantity": 2,
            }],
        }],
    })

    assert norms == {("cabinet", "mdf"): ("m²", 1.44)}


def test_object_norms_are_derived_from_linear_stock_allocations():
    norms = _material_norms_from_plan({
        "lines": [{
            "purchase_kind": "linear_stock",
            "allocations": [{
                "object_id": "shelf", "material_requirement_id": "tube",
                "length_mm": 2500, "quantity": 2,
            }],
        }],
    })

    assert norms == {("shelf", "tube"): ("m", 5.0)}
