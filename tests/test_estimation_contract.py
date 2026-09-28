from agents.schemas.estimation_schema import (
    EstimationSchemaError,
    validate_estimation_result,
)
from agents.anthropic_adapter import strip_schema_for_claude
from agents.schemas.estimation_schema import ESTIMATION_RESULT_JSON_SCHEMA
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
        "manufacturing": [
            {
                "process": "sheet_laser",
                "material_family": "carbon_steel",
                "measurements": [3, 4, 1, 12, 18, None, 8, None, None],
                "flags": [
                    "no", "no", "unknown", "no", "unknown",
                    "unknown", "unknown", "unknown", "unknown", "unknown",
                    "no", "no", "yes", "yes", "yes",
                ],
                "evidence_pages": "1, 3",
                "confidence": 74,
                "notes": "Laser profile required.",
            }
        ],
        "estimation_notes": [],
        "missing_information": [],
        "confidence": 82,
    }


def test_valid_estimation_contract_builds_db_lines():
    payload = validate_estimation_result(_valid_payload())
    assert payload["manufacturing"][0]["path_length_m"] == 12
    assert payload["manufacturing"][0]["precision_or_repeatability_required"] == "yes"
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


def test_estimation_schema_strips_provider_unsupported_fixed_array_lengths():
    schema = strip_schema_for_claude(ESTIMATION_RESULT_JSON_SCHEMA)
    manufacturing = schema["properties"]["manufacturing"]["items"]["properties"]
    assert "minItems" not in manufacturing["measurements"]
    assert "maxItems" not in manufacturing["measurements"]
    assert "minItems" not in manufacturing["flags"]
    assert "maxItems" not in manufacturing["flags"]


def test_manufacturing_process_is_normalized_from_canonical_material_family():
    payload = _valid_payload()
    payload["manufacturing"][0]["process"] = "sheet_laser"
    payload["manufacturing"][0]["material_family"] = "green_mdf"

    validated = validate_estimation_result(payload)

    assert validated["manufacturing"][0]["process"] == "cnc_router"
