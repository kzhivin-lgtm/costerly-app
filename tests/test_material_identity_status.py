from use_cases.material_identity_status import material_identity_status


def test_drawer_slide_without_nominal_length_is_yellow_not_review_or_red():
    status = material_identity_status({
        "specifications": {
            "material_family": "drawer slide",
            "brand": "Blum",
            "product_system": "Movento",
        },
    })

    assert status.tone == "yellow"
    assert status.missing == ("nominal length",)
    assert status.known_path == ("drawer slide", "brand: Blum", "system: Movento")


def test_complete_endpoint_without_israel_link_is_blue():
    status = material_identity_status({
        "specifications": {"material_family": "drawer slide", "depth_mm": 600},
    })

    assert status.tone == "blue"
    assert status.label == "Israel reference link missing"


def test_complete_endpoint_with_israel_link_is_green():
    status = material_identity_status({
        "reference_material_id": "reference-slide-600",
        "specifications": {"material_family": "drawer slide", "depth_mm": 600},
    })

    assert status.tone == "green"
    assert status.missing == ()


def test_missing_family_is_red():
    status = material_identity_status({"specifications": {"brand": "Blum"}})

    assert status.tone == "red"
    assert status.missing == ("material family",)
