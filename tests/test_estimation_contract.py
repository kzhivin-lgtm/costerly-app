from agents.schemas.estimation_schema import (
    EstimationSchemaError,
    validate_estimation_result,
)
from use_cases.estimation import build_estimate_lines_from_agent_result


def _valid_payload():
    return {
        "estimate_id": "run_001_estimate_001",
        "run_id": "run_001",
        "company_id": "001",
        "object_id": "object_001",
        "object_name": "Curtain rod system",
        "object_quantity": 1,
        "status": "estimated",
        "file_evidence_summary": "Object is visible on pages 1 and 3.",
        "materials": [
            {
                "group_name": "Sheet materials",
                "item_name": "Steel tubing, diameter 20mm",
                "catalog_match_query": "steel tube 20mm",
                "unit": "m",
                "quantity": 8,
                "quantity_basis": "Two curved tubes estimated from drawing dimensions.",
                "evidence_pages": "1, 3",
                "confidence": 76,
                "notes": "Exact steel grade not specified.",
            }
        ],
        "labor": [
            {
                "group_name": "Metalworks",
                "work_name": "Tube cutting and bending",
                "role": "metal worker",
                "hours": 6,
                "hours_basis": "Custom curved tube fabrication and bracket prep.",
                "evidence_pages": "1, 3",
                "confidence": 72,
                "notes": "Excludes final installation.",
            }
        ],
        "estimation_notes": [],
        "missing_information": [],
        "confidence": 82,
    }


def test_valid_estimation_contract_builds_db_lines():
    payload = validate_estimation_result(_valid_payload())
    lines = build_estimate_lines_from_agent_result(payload)

    assert len(lines) == 2
    assert lines[0]["section"] == "material"
    assert lines[0]["needs_price"] is True
    assert "unit_cost" not in lines[0]
    assert lines[1]["section"] == "labor"
    assert lines[1]["hours"] == 6
    assert "rate" not in lines[1]


def test_estimation_contract_rejects_agent_prices():
    payload = _valid_payload()
    payload["materials"][0]["unit_cost"] = 180

    try:
        validate_estimation_result(payload)
    except EstimationSchemaError as exc:
        assert "extra keys" in str(exc)
    else:
        raise AssertionError("unit_cost must be rejected")
