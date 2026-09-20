from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from agents.schemas.price_source_schema import (
    PriceSourceSchemaError,
    validate_price_source_result,
)
from use_cases.price_sources import (
    PriceSourceError,
    _VisibleTextParser,
    _validate_public_url,
    apply_legacy_price_benchmark,
    extract_spreadsheet_text,
)


def _result(*, status: str = "ready", confidence: float = 96) -> dict:
    return {
        "supplier_name": "Supplier Ltd",
        "document_type": "price_list",
        "document_date": "2026-09-20",
        "currency": "ILS",
        "vat_mode": "excluded",
        "rows": [
            {
                "source_row_number": 1,
                "raw_description": "Birch plywood 10 mm 2440x1220",
                "raw_sku": "PLY-10",
                "raw_price": 90,
                "raw_currency": "ILS",
                "raw_unit": "sheet",
                "raw_package_quantity": 1,
                "raw_quantity": 1,
                "raw_line_total": 90,
                "raw_vat_mode": "excluded",
                "normalized_name": "Birch plywood 10 mm 2440x1220",
                "purchase_unit": "sheet",
                "calculation_unit": "m2",
                "conversion_factor": 2.9768,
                "normalized_price": 90 / 2.9768,
                "conversion_basis": "one 2.44 m x 1.22 m sheet contains 2.9768 m2",
                "status": status,
                "confidence": confidence,
                "reason_codes": [],
                "evidence_reference": "page 1 row 4",
            }
        ],
    }


def test_price_source_schema_accepts_evidenced_unit_conversion():
    result = _result()
    assert validate_price_source_result(result) is result


def test_ready_price_requires_currency_and_positive_normalized_price():
    missing_currency = _result()
    missing_currency["currency"] = ""
    missing_currency["rows"][0]["raw_currency"] = ""
    with pytest.raises(PriceSourceSchemaError, match="currency"):
        validate_price_source_result(missing_currency)

    zero_price = _result()
    zero_price["rows"][0]["normalized_price"] = 0
    with pytest.raises(PriceSourceSchemaError, match="normalized unit price"):
        validate_price_source_result(zero_price)


def test_ready_price_requires_supported_units_and_matching_arithmetic():
    unknown_unit = _result()
    unknown_unit["rows"][0]["calculation_unit"] = "unknown"
    with pytest.raises(PriceSourceSchemaError, match="canonical units"):
        validate_price_source_result(unknown_unit)

    wrong_arithmetic = _result()
    wrong_arithmetic["rows"][0]["normalized_price"] = 90
    with pytest.raises(PriceSourceSchemaError, match="conversion factor"):
        validate_price_source_result(wrong_arithmetic)


def test_prompt_preserves_item_vat_basis_and_excludes_document_totals():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()
    assert "subtotal, VAT or tax total, grand total, and amount due" in prompt
    assert "Never add\n  or remove VAT from a product price" in prompt


def test_prompt_preserves_raw_unit_and_normalizes_common_square_meter_aliases():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()
    assert "Preserve raw_unit exactly as written" in prompt
    for alias in ("sqm", "sq.m", "m2", "m^2", "m²", "מ״ר", 'מ"ר'):
        assert alias in prompt


def test_supplier_may_be_unknown_and_negative_credit_rows_must_be_excluded():
    unknown_supplier = _result()
    unknown_supplier["supplier_name"] = ""
    assert validate_price_source_result(unknown_supplier) is unknown_supplier

    credit = _result(status="excluded")
    credit["rows"][0]["raw_price"] = -100
    credit["rows"][0]["raw_line_total"] = -100
    assert validate_price_source_result(credit) is credit

    active_negative = _result()
    active_negative["rows"][0]["raw_price"] = -100
    with pytest.raises(PriceSourceSchemaError, match="must be excluded"):
        validate_price_source_result(active_negative)


def test_duplicate_source_row_numbers_are_rejected():
    result = _result()
    result["rows"].append(dict(result["rows"][0]))
    with pytest.raises(PriceSourceSchemaError, match="unique positive"):
        validate_price_source_result(result)


def test_legacy_price_is_only_an_exact_unit_aware_negative_signal():
    result = _result(confidence=96)
    apply_legacy_price_benchmark(
        result,
        [{"material_name": "Birch plywood 10 mm 2440x1220", "price": 10, "price_unit": "m2"}],
    )
    assert result["rows"][0]["confidence"] == 81
    assert "extreme_legacy_price_difference" in result["rows"][0]["reason_codes"]

    unrelated = _result(confidence=96)
    apply_legacy_price_benchmark(
        unrelated,
        [{"material_name": "Birch plywood 10 mm 2440x1220", "price": 10, "price_unit": "sheet"}],
    )
    assert unrelated["rows"][0]["confidence"] == 96


def test_csv_is_rendered_as_bounded_agent_evidence():
    text = extract_spreadsheet_text(
        "prices.csv",
        "sku,description,price\nA-1,Panel,90\n".encode(),
    )
    assert "sku | description | price" in text
    assert "A-1 | Panel | 90" in text


def test_xlsx_is_rendered_with_sheet_and_column_context():
    output = BytesIO()
    pd.DataFrame([{"SKU": "A-1", "Description": "Panel", "Price": 90}]).to_excel(
        output,
        index=False,
    )
    text = extract_spreadsheet_text("prices.xlsx", output.getvalue())
    assert "SHEET: Sheet1" in text
    assert "SKU,Description,Price" in text
    assert "A-1,Panel,90" in text


def test_visible_html_text_ignores_scripts_and_keeps_rows():
    parser = _VisibleTextParser()
    parser.feed(
        "<html><script>ignore()</script><table><tr><td>Panel</td>"
        "<td>90 ILS</td></tr></table></html>"
    )
    assert "ignore" not in parser.text()
    assert "Panel" in parser.text()
    assert "90 ILS" in parser.text()


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/prices",
        "http://localhost/prices",
        "file:///etc/passwd",
        "https://user:password@example.com/prices",
        "https://example.com:8443/prices",
    ],
)
def test_url_import_rejects_private_or_credentialed_targets(url):
    with pytest.raises(PriceSourceError):
        _validate_public_url(url)
