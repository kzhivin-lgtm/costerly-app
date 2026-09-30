import pytest

from use_cases.purchased_components import (
    EXTERNAL_PROCESS_POLICIES,
    classify_process_cost,
    price_scope_for_classification,
)


def test_all_supported_external_processes_become_purchased_components():
    assert len(EXTERNAL_PROCESS_POLICIES) == 18
    for process_code in EXTERNAL_PROCESS_POLICIES:
        classification = classify_process_cost(
            process_code=process_code,
            route="subcontractor",
        )
        assert classification == "purchased_fabricated_component"
        assert price_scope_for_classification(classification) == "fabricated_component"


def test_processes_with_company_machinery_remain_in_house_manufacturing():
    for process_code in (
        "cnc_router",
        "sheet_laser",
        "powder_coating",
        "spray_finishing",
        "press_brake_bending",
        "sheet_rolling",
        "tube_bending",
        "metal_machining",
        "sandblasting",
        "galvanizing",
    ):
        assert (
            classify_process_cost(process_code=process_code, route="in_house")
            == "in_house_manufacturing"
        )


def test_manual_route_is_company_labor_and_unknown_process_is_rejected():
    assert (
        classify_process_cost(process_code="cnc_router", route="manual")
        == "in_house_labor"
    )
    with pytest.raises(ValueError, match="Unsupported external process"):
        classify_process_cost(process_code="unknown", route="subcontractor")
