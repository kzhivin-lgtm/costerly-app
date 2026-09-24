from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
from PIL import Image

from agents.schemas.price_source_schema import (
    PriceSourceSchemaError,
    guard_price_source_row_activation,
    normalize_price_source_confidence_scale,
    reconcile_price_source_arithmetic,
    validate_price_source_result,
)
from agents.price_source_agent import PRICE_SOURCE_MAX_OUTPUT_TOKENS
from use_cases.price_sources import (
    PriceSourceError,
    PRICE_CATALOG_DEPARTMENTS,
    _VisibleTextParser,
    _validate_category,
    _validate_public_url,
    apply_legacy_price_benchmark,
    combine_price_source_files,
    extract_spreadsheet_text,
    fetch_public_page,
    list_price_catalog,
)


class _UploadedPhoto:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


class _CatalogQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def neq(self, *_args):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _CatalogClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _CatalogQuery(self.tables[name])


def _result(*, status: str = "ready", confidence: float = 96) -> dict:
    return {
        "category": "Sheet Materials",
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


def test_fractional_confidence_scale_is_normalized_before_activation():
    result = _result(confidence=0.95)

    normalized = normalize_price_source_confidence_scale(result)

    assert normalized["rows"][0]["confidence"] == 95
    assert validate_price_source_result(normalized) is normalized


def test_mixed_confidence_scales_are_rejected():
    result = _result(confidence=0.95)
    result["rows"].append({**result["rows"][0], "source_row_number": 2, "confidence": 92})

    with pytest.raises(PriceSourceSchemaError, match="mixed scales"):
        normalize_price_source_confidence_scale(result)


def test_ambiguous_package_to_unit_conversion_cannot_activate():
    result = _result(confidence=95)
    row = result["rows"][0]
    row["raw_package_quantity"] = 25
    row["purchase_unit"] = "ml"
    row["calculation_unit"] = "ml"
    row["conversion_factor"] = 1
    row["normalized_price"] = row["raw_price"]

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "package_conversion_unresolved" in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


def test_price_source_schema_requires_a_supported_inferred_category():
    result = _result()
    result["category"] = "Unknown category"
    with pytest.raises(PriceSourceSchemaError, match="material category"):
        validate_price_source_result(result)


def test_category_can_be_left_for_automatic_detection():
    assert _validate_category("") == ""


def test_price_source_output_budget_supports_large_supplier_pages():
    assert PRICE_SOURCE_MAX_OUTPUT_TOKENS >= 32_768


def test_price_catalog_uses_three_stable_user_facing_departments():
    assert PRICE_CATALOG_DEPARTMENTS["Sheet Materials"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Metal"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Finishes and Coatings"] == "Finishing"


def test_several_ordered_photos_become_one_pdf_source():
    photos = []
    for index, color in enumerate(((255, 255, 255), (220, 220, 220)), start=1):
        output = BytesIO()
        Image.new("RGB", (16, 16), color).save(output, format="PNG")
        photos.append(_UploadedPhoto(f"page-{index}.png", output.getvalue()))

    combined = combine_price_source_files(photos)

    assert combined.name == "photo-document-2-pages.pdf"
    assert combined.getvalue().startswith(b"%PDF")


def test_multiple_upload_rejects_mixed_document_types():
    with pytest.raises(PriceSourceError, match="one PDF or spreadsheet"):
        combine_price_source_files(
            [
                _UploadedPhoto("invoice.pdf", b"%PDF"),
                _UploadedPhoto("page.png", b"png"),
            ]
        )


def test_active_offer_is_enriched_as_material_first_catalog_row(monkeypatch):
    tables = {
        "company_material_offers": [
            {
                "offer_id": "offer-1",
                "company_material_id": "material-1",
                "supplier_id": "supplier-1",
                "source_id": "source-1",
                "source_row_id": "row-1",
                "normalized_price": 90,
                "normalized_unit": "m2",
                "currency": "ILS",
                "valid_from": "2026-09-24",
            }
        ],
        "company_material_items": [
            {
                "company_material_id": "material-1",
                "category": "Sheet Materials",
                "canonical_name": "Birch plywood 10 mm",
                "preferred_unit": "m2",
            }
        ],
        "company_suppliers": [
            {"supplier_id": "supplier-1", "supplier_name": "Supplier Ltd"}
        ],
        "company_price_source_rows": [
            {"row_id": "row-1", "raw_description": "Plywood birch 10mm"}
        ],
        "company_price_sources": [
            {
                "source_id": "source-1",
                "source_name": "invoice.pdf",
                "source_kind": "file",
                "source_url": None,
                "processed_at": "2026-09-24T10:00:00Z",
            }
        ],
    }
    monkeypatch.setattr(
        "use_cases.price_sources.get_supabase_client",
        lambda: _CatalogClient(tables),
    )
    monkeypatch.setattr(
        "use_cases.price_sources.assert_company_owner",
        lambda *_args: None,
    )

    rows = list_price_catalog(SimpleNamespace(company_id="company-1", user_id="user-1"))

    assert rows[0]["department"] == "Wood"
    assert rows[0]["canonical_name"] == "Birch plywood 10 mm"
    assert rows[0]["original_name"] == "Plywood birch 10mm"
    assert rows[0]["supplier_name"] == "Supplier Ltd"
    assert rows[0]["updated_at"] == "2026-09-24"


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


def test_ready_price_arithmetic_is_reconciled_deterministically():
    result = _result()
    result["rows"][0]["normalized_price"] = 90
    reconciled = reconcile_price_source_arithmetic(result)
    assert reconciled["rows"][0]["normalized_price"] == pytest.approx(90 / 2.9768)
    assert "normalized_price_recalculated" in reconciled["rows"][0]["reason_codes"]
    assert validate_price_source_result(reconciled) is reconciled


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


def test_script_only_supplier_page_returns_actionable_error(monkeypatch):
    class Response:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class Client:
        @staticmethod
        def get(_url, *, follow_redirects=False):
            assert follow_redirects is False
            return Response()

    monkeypatch.setattr(
        "use_cases.price_sources._validate_public_url",
        lambda value: value,
    )
    with pytest.raises(PriceSourceError, match="does not expose readable text"):
        fetch_public_page("https://example.com/prices", client=Client())


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
