import pytest

from use_cases.estimation_v2_bom import EstimationV2BomError, derive_supported_bom


def _facts(width=450):
    ref = "storage://rfq-estimation-evidence/company/run/object/preview.webp"
    return {
        "status": "review_required",
        "template": {"code": "open_shelving_unit"},
        "dimensions_mm": {"width": width, "depth": 510, "height": 2695},
        "features": {"shelf_count": 5, "back_panel": True},
        "materials": [
            {"requirement_id": "m1", "source_name": "MDF 20 mm", "family": "mdf",
             "specification": {"thickness_mm": 20}, "quantity": 1.053, "unit": "m2", "evidence_refs": [ref]},
            {"requirement_id": "m2", "source_name": "metal profile 20x20", "family": "carbon_steel",
             "specification": {"profile_section": "20x20"}, "quantity": None, "unit": "m", "evidence_refs": [ref]},
            {"requirement_id": "m3", "source_name": "perforated metal sheet", "family": "carbon_steel",
             "specification": {}, "quantity": None, "unit": "m2", "evidence_refs": [ref]},
        ],
        "purchased_components": [],
        "review_items": [],
        "primary_preview_ref": ref,
    }


def test_open_shelving_bom_derives_five_priced_requirements_and_visible_assumptions():
    result = derive_supported_bom(_facts())

    assert result is not None
    facts = result["facts"]
    assert facts["status"] == "ready"
    assert len(facts["materials"]) == 5
    assert all(row["quantity"] > 0 for row in facts["materials"])
    assert facts["materials"][1]["quantity"] == pytest.approx(1.211, abs=0.0001)
    assert facts["materials"][2]["quantity"] == pytest.approx(1.334, abs=0.0001)
    assert facts["review_items"][0]["severity"] == "warning"
    assert "square_tube_wall_1_5_mm" in result["assumptions"]
    assert result["calculations"]["bom-profile"]["kg_per_m"] == pytest.approx(0.87135, abs=0.0001)


def test_open_shelving_rejects_contaminated_full_page_width():
    try:
        derive_supported_bom(_facts(width=4130))
    except EstimationV2BomError as exc:
        assert "outside the supported envelope" in str(exc)
    else:
        raise AssertionError("full-page neighboring-object dimensions must not produce a draft")


def test_open_shelving_accepts_sonnet_russian_profile_and_20x20mm_transport():
    facts = _facts()
    facts["materials"][1]["source_name"] = "металлический профиль квадратного сечения 20×20мм"
    facts["materials"][1]["specification"]["profile_section"] = "20×20мм"

    result = derive_supported_bom(facts)

    assert result is not None
    assert result["facts"]["materials"][0]["family"] == "carbon_steel"
