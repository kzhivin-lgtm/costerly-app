from __future__ import annotations

from concurrent.futures import Future
from io import BytesIO
from copy import deepcopy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import fitz
import pandas as pd
import pytest
from openpyxl import Workbook
from PIL import Image

from agents.schemas.price_source_schema import (
    apply_price_source_document_defaults,
    apply_price_source_hardware_defaults,
    apply_price_source_material_unit_defaults,
    PriceSourceSchemaError,
    guard_price_source_document_totals,
    guard_price_source_row_activation,
    normalize_price_source_row_identity_fields,
    normalize_price_source_units,
    normalize_price_source_optional_numbers,
    normalize_price_source_confidence_scale,
    reconcile_price_source_arithmetic,
    validate_price_source_result,
)
from agents.price_source_agent import (
    PRICE_SOURCE_MAX_OUTPUT_TOKENS,
    _apply_material_taxonomy_to_rows,
    _line_arithmetic_conflicts,
    _mark_unverified_source_table_rows_for_review,
    _mark_unrepaired_fractional_hardware_for_review,
    _merge_arithmetic_recheck,
)
from use_cases.price_sources import (
    discard_price_source_non_candidates,
    discard_price_source_consumables,
    prepare_price_source_operation_rows,
    PriceSourceError,
    PRICE_CATALOG_DEPARTMENTS,
    _VisibleTextParser,
    _find_previous_source_revision,
    _unchanged_duplicate_summary,
    _validate_department,
    _validate_public_url,
    apply_legacy_price_benchmark,
    purge_price_source,
    accepted_price_source_uploads,
    canonical_price_source_category,
    combine_price_source_files,
    create_price_source_download_url,
    extract_spreadsheet_text,
    fetch_public_page,
    guard_price_source_department,
    list_material_jobs,
    list_price_catalog,
    list_unresolved_price_source_rows,
    prepare_internal_estimate_row_defaults,
    price_source_material_types,
    price_source_vat_rate,
    price_source_family_identity,
    price_source_semantic_fingerprint,
    supplier_service_pricing_basis,
    match_existing_supplier,
    normalize_price_source_sheet_rows,
    supplier_merge_key,
    supplier_merge_max_distance,
    price_source_template_fingerprint,
    price_offer_matches_row,
    material_offer_matches_extracted_row,
    material_offer_matches_same_supplier_description,
    material_offer_matches_same_supplier_material,
    material_offer_proves_unknown_family,
    material_catalog_key,
    material_persisted_normalized_name,
    material_structural_key,
    price_rows_match_same_supplier_material,
    company_identity_blacklist,
    issuer_identity_from_source_text,
    repair_supplier_from_issuer_evidence,
    supplier_is_company_identity,
    supplier_operation_offer_matches_row,
    supplier_operation_offer_catalog_key,
    price_offer_lane_key,
    price_source_supplier_name,
    price_source_extraction_diagnostics,
    remove_price_source_row,
    render_price_source_pdf_preview,
    render_price_source_preview,
    save_price_source_row,
    validate_price_source_upload_selection,
)
from use_cases.price_source_taxonomy import (
    apply_material_taxonomy,
    apply_operation_taxonomy,
    job_operation_for_text,
    material_rule_for_text,
)


def test_price_source_extraction_diagnostics_records_zero_row_evidence():
    diagnostics = price_source_extraction_diagnostics(
        {"document_type": "tax_invoice", "source_origin": "supplier", "rows": []},
        text_layer_strategy="image_ocr",
        text_layer_characters=563,
        ocr_pages=1,
    )

    assert diagnostics == {
        "text_layer_strategy": "image_ocr",
        "text_layer_characters": 563,
        "ocr_pages": 1,
        "agent_row_count": 0,
        "agent_ready_row_count": 0,
        "agent_unresolved_row_count": 0,
        "agent_excluded_row_count": 0,
        "document_type": "tax_invoice",
        "source_origin": "supplier",
    }


def test_price_source_download_url_is_direct_owned_and_attachment_scoped(monkeypatch):
    calls = []

    class Bucket:
        def create_signed_url(self, path, expires_in, options):
            calls.append((path, expires_in, options))
            return {"signedURL": "https://storage.example/signed-source"}

    class Storage:
        def from_(self, bucket):
            assert bucket == "company-price-sources"
            return Bucket()

    client = SimpleNamespace(storage=Storage())
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: client)
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    url = create_price_source_download_url(
        SimpleNamespace(company_id="company-1", user_id="user-1"),
        "storage://company-price-sources/company-1/source/invoice.pdf",
        file_name="invoice.pdf",
    )

    assert url == "https://storage.example/signed-source"
    assert calls == [
        (
            "company-1/source/invoice.pdf",
            3600,
            {"download": "invoice.pdf"},
        )
    ]


def test_purge_price_source_uses_owned_transactional_rpc_and_deletes_storage(monkeypatch):
    calls = []

    class Rpc:
        def execute(self):
            return SimpleNamespace(
                data={
                    "deleted_material_offers": 47,
                    "deleted_rows": 12,
                    "deleted_materials": 39,
                }
            )

    class Bucket:
        def remove(self, paths):
            calls.append(("storage.remove", paths))

    class Storage:
        @staticmethod
        def from_(bucket):
            assert bucket == "company-price-sources"
            return Bucket()

    class Client:
        storage = Storage()

        def table(self, name):
            if name == "company_price_source_pages":
                return _CatalogQuery([])
            assert name == "company_price_sources"
            return _CatalogQuery(
                [{
                    "source_id": "source-1",
                    "company_id": "company-1",
                    "status": "ready",
                    "storage_path": "storage://company-price-sources/company-1/source-1.pdf",
                }]
            )

        def rpc(self, name, values):
            calls.append((name, values))
            return Rpc()

    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", Client)
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    result = purge_price_source(
        SimpleNamespace(company_id="company-1", user_id="user-1"),
        "source-1",
    )

    assert result == {
        "deleted_material_offers": 47,
        "deleted_operation_offers": 0,
        "deleted_service_offers": 0,
        "deleted_rows": 12,
        "deleted_materials": 39,
        "deleted_supplier_aliases": 0,
        "storage_deleted": True,
    }
    assert calls == [
        (
            "purge_company_price_source",
            {"p_company_id": "company-1", "p_source_id": "source-1"},
        ),
        ("storage.remove", ["company-1/source-1.pdf"]),
    ]


def test_source_library_uses_modal_confirmed_optimistic_source_removal():
    from screens.company_profile import _render_price_lists, _render_price_lists_projections
    from ui.js_guards import install_price_source_remove_guard

    source = inspect.getsource(_render_price_lists)
    projections = inspect.getsource(_render_price_lists_projections)
    guard = inspect.getsource(install_price_source_remove_guard)

    assert "install_price_source_remove_guard" in source
    assert "_render_price_lists_projections" in source
    assert "_price_source_purging_ids" in projections
    assert "delete_price_source_" in projections
    assert "on_click=_start_price_source_purge_action" in projections
    assert "price-source-remove-modal" in guard
    assert "This permanently deletes the source" in guard
    assert "costerly-price-source-pending-delete" in guard
    assert 'st-key-price_source_row_' in guard
    assert 'key=f"price_source_row_{source_id}"' in projections


def test_price_source_pdf_preview_renders_only_first_page():
    document = fitz.open()
    first = document.new_page(width=400, height=600)
    first.draw_rect(fitz.Rect(40, 40, 360, 180), fill=(0.5, 0.28, 0.78))
    document.new_page(width=400, height=600)
    source = document.tobytes()
    document.close()

    preview = render_price_source_pdf_preview(source)

    assert preview is not None
    with Image.open(BytesIO(preview)) as image:
        assert image.format == "PNG"
        assert image.width <= 240
        assert image.height <= 140


def test_price_source_pdf_preview_falls_back_for_invalid_pdf():
    assert render_price_source_pdf_preview(b"not a pdf") is None


def test_price_source_image_preview_renders_a_bounded_png():
    source = BytesIO()
    Image.new("RGB", (900, 600), "#7F4BD1").save(source, format="JPEG")

    preview = render_price_source_preview("page.jpg", source.getvalue())

    assert preview is not None
    with Image.open(BytesIO(preview)) as image:
        assert image.format == "PNG"
        assert image.width <= 240
        assert image.height <= 140


def test_price_source_xlsx_preview_renders_a_table_png():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Material", "Price", "Unit"])
    sheet.append(["Plywood", 75, "sheet"])
    source = BytesIO()
    workbook.save(source)
    workbook.close()

    preview = render_price_source_preview("prices.xlsx", source.getvalue())

    assert preview is not None
    with Image.open(BytesIO(preview)) as image:
        assert image.format == "PNG"
        assert image.size == (240, 140)


def test_price_source_csv_preview_renders_a_table_png():
    preview = render_price_source_preview(
        "prices.csv",
        b"Material,Price,Unit\nPlywood,75,sheet\n",
    )

    assert preview is not None
    with Image.open(BytesIO(preview)) as image:
        assert image.format == "PNG"


def test_price_source_preview_falls_back_for_invalid_image():
    assert render_price_source_preview("page.png", b"not an image") is None


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

    def in_(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _CatalogClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _CatalogQuery(self.tables[name])


class _MutableQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.payload = None
        self.operation = "select"
        self.row_limit = None

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.filters.append(("eq", key, value))
        return self

    def neq(self, key, value):
        self.filters.append(("neq", key, value))
        return self

    def in_(self, key, values):
        self.filters.append(("in", key, set(values)))
        return self

    def limit(self, value):
        self.row_limit = value
        return self

    def order(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = deepcopy(payload)
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = deepcopy(payload)
        return self

    def _matches(self, row):
        for operation, key, value in self.filters:
            if operation == "eq" and row.get(key) != value:
                return False
            if operation == "neq" and row.get(key) == value:
                return False
            if operation == "in" and row.get(key) not in value:
                return False
        return True

    def execute(self):
        rows = self.client.tables[self.table_name]
        if self.operation == "insert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            id_fields = {
                "company_material_items": "company_material_id",
                "company_material_offers": "offer_id",
                "company_price_source_rows": "row_id",
            }
            id_field = id_fields.get(self.table_name)
            inserted_rows = []
            for payload in payloads:
                inserted = deepcopy(payload)
                if id_field and id_field not in inserted:
                    inserted[id_field] = f"generated-{len(rows) + 1}"
                inserted.setdefault(
                    "status",
                    "active" if self.table_name == "company_material_offers" else "private",
                )
                rows.append(inserted)
                inserted_rows.append(deepcopy(inserted))
            return SimpleNamespace(data=inserted_rows)
        matches = [row for row in rows if self._matches(row)]
        if self.row_limit is not None:
            matches = matches[: self.row_limit]
        if self.operation == "update":
            for row in matches:
                row.update(deepcopy(self.payload))
        return SimpleNamespace(data=deepcopy(matches))


class _MutableClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _MutableQuery(self, name)


def _result(*, status: str = "ready", confidence: float = 96) -> dict:
    return {
        "supplier_name": "Supplier Ltd",
        "supplier_hp": "",
        "source_origin": "supplier",
        "document_type": "price_list",
        "document_number": "PL-204",
        "document_date": "2026-09-20",
        "price_context": "public_list",
        "currency": "ILS",
        "vat_mode": "excluded",
        "document_subtotal": 90,
        "document_vat_amount": 16.2,
        "document_total": 106.2,
        "rows": [
            {
                "source_row_number": 1,
                "item_kind": "material",
                "material_type": "Wood Sheets",
                "material_family": "birch plywood",
                "identity_attributes": {
                    "thickness_mm": 10,
                    "width_mm": 1220,
                    "length_mm": 2440,
                    "diameter_mm": 0,
                    "primary_attribute": "10 mm",
                    "brand": "",
                    "brand_basis": "unknown",
                    "species": "birch",
                    "substrate": "plywood",
                    "surface": "",
                    "coating": "",
                    "colour": "",
                    "grade": "",
                    "construction": "",
                    "finish": "",
                },
                "raw_description": "Birch plywood 10 mm 2440x1220",
                "raw_sku": "PLY-10",
                "raw_price": 90,
                "raw_currency": "ILS",
                "raw_unit": "sheet",
                "raw_package_quantity": 1,
                "raw_quantity": 1,
                "raw_line_total": 90,
                "raw_discount_percent": 0,
                "raw_discount_amount": 0,
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


def test_operation_service_remains_ready_for_the_supplier_work_catalog():
    result = _result()
    row = result["rows"][0]
    row["item_kind"] = "operation_service"
    row["material_family"] = "cutting service"

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "ready"
    assert validate_price_source_result(guarded) is guarded


def test_document_vat_and_currency_defaults_apply_without_manual_source_gate():
    result = _result()
    result.update({
        "currency": "",
        "vat_mode": "unknown",
        "document_type": "tax_invoice",
        "document_subtotal": 100,
        "document_vat_amount": 18,
        "document_total": 118,
    })
    result["rows"][0]["raw_currency"] = ""
    result["rows"][0]["raw_vat_mode"] = "unknown"

    prepared = apply_price_source_document_defaults(result, source_kind="file")

    assert prepared["currency"] == "ILS"
    assert prepared["vat_mode"] == "excluded"
    assert prepared["rows"][0]["raw_currency"] == "ILS"
    assert prepared["rows"][0]["raw_vat_mode"] == "excluded"


def test_consumables_are_discarded_and_supplier_services_map_before_persistence():
    consumable = _result()["rows"][0]
    consumable["raw_description"] = "Wood screws 4x40"
    service = _result()["rows"][0]
    service.update({
        "source_row_number": 2,
        "item_kind": "operation_service",
        "raw_description": "פס חיתוך + קנט",
        "normalized_name": "Cut and edge banding",
        "material_family": "supplier processing",
    })
    result = _result()
    result["rows"] = [consumable, service]

    assert discard_price_source_consumables(result) == 1
    assert prepare_price_source_operation_rows(result) == {2: "supplier_cut_and_edge_banding"}
    assert supplier_service_pricing_basis("") == "supplier_defined"
    assert supplier_service_pricing_basis("m") == "linear_meter"
    assert supplier_service_pricing_basis("m2") == "square_meter"
    assert supplier_service_pricing_basis(
        "piece", operation_code="supplier_cut_and_edge_banding"
    ) == "supplier_defined"


def test_glass_cutter_is_a_tool_consumable_not_a_glass_material():
    result = _result()
    cutter = result["rows"][0]
    cutter.update({
        "material_type": "Glass",
        "material_family": "glass",
        "raw_description": "סכין חותך זכוכית נפט",
        "normalized_name": "Glass cutter knife",
    })

    assert discard_price_source_consumables(result) == 1
    assert result["rows"] == []


def test_hardware_with_integral_screws_is_not_discarded_as_a_consumable():
    result = _result()
    hardware = result["rows"][0]
    hardware.update({
        "material_type": "Metal Supplies",
        "material_family": "furniture leg",
        "raw_description": "Adjustable plinth leg 80 mm with mounting screws",
        "normalized_name": "Adjustable plinth leg 80 mm",
        "raw_unit": "unknown",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "normalized_price": 0,
    })

    prepared = apply_price_source_hardware_defaults(result)

    assert prepared["rows"][0]["material_type"] == "Hardware"
    assert prepared["rows"][0]["purchase_unit"] == "piece"
    assert prepared["rows"][0]["calculation_unit"] == "piece"
    assert discard_price_source_consumables(prepared) == 0


def test_bulk_low_value_screw_pack_is_discarded_even_if_model_calls_it_hardware():
    result = _result()
    screws = result["rows"][0]
    screws.update({
        "material_type": "Hardware",
        "material_family": "screw",
        "raw_description": "בורג סיבית FGV 4x40 (1000)",
        "normalized_name": "Screw FGV 4x40 1000 pack",
        "raw_price": 61.8,
        "raw_unit": "pack",
        "raw_package_quantity": 1000,
    })

    assert discard_price_source_consumables(result) == 1
    assert result["rows"] == []


def test_bulk_low_value_pack_supports_consumables_filter_without_hiding_fittings():
    result = _result()
    pack = result["rows"][0]
    pack.update({
        "material_type": "Hardware",
        "material_family": "fastening kit",
        "raw_description": "Fastening kit 100 pack",
        "normalized_name": "Fastening kit 100 pack",
        "raw_price": 100,
        "raw_unit": "pack",
        "raw_package_quantity": 100,
    })

    assert discard_price_source_consumables(result) == 1


def test_drawer_runner_defaults_to_a_set_when_the_source_omits_the_unit():
    result = _result()
    runner = result["rows"][0]
    runner.update({
        "material_type": "Other",
        "material_family": "drawer runner",
        "raw_description": "Undermount drawer runner 600 mm",
        "normalized_name": "Undermount drawer runner 600 mm",
        "raw_unit": "",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "normalized_price": 0,
    })

    prepared = apply_price_source_hardware_defaults(result)

    assert prepared["rows"][0]["material_type"] == "Hardware"
    assert prepared["rows"][0]["purchase_unit"] == "set"
    assert prepared["rows"][0]["calculation_unit"] == "set"
    assert prepared["rows"][0]["normalized_price"] == 90


def test_drawer_runner_is_a_set_even_when_invoice_uses_piece_as_count_unit():
    result = _result()
    runner = result["rows"][0]
    runner.update({
        "material_type": "Hardware",
        "material_family": "drawer runner",
        "raw_description": "Drawer runner 600 mm",
        "normalized_name": "Drawer runner 600 mm",
        "raw_unit": "piece",
        "purchase_unit": "piece",
        "calculation_unit": "piece",
    })

    prepared = apply_price_source_hardware_defaults(result)

    assert prepared["rows"][0]["raw_unit"] == "piece"
    assert prepared["rows"][0]["purchase_unit"] == "set"
    assert prepared["rows"][0]["calculation_unit"] == "set"


def test_ordinary_material_defaults_to_piece_when_an_invoice_omits_the_unit():
    result = _result()
    row = result["rows"][0]
    row.update({
        "material_type": "Solid Wood",
        "raw_unit": "unknown",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "normalized_price": 0,
        "status": "unresolved",
        "reason_codes": ["missing_unit"],
    })

    prepared = apply_price_source_material_unit_defaults(result)

    assert row["status"] == "ready"
    assert row["raw_unit"] == row["purchase_unit"] == row["calculation_unit"] == "piece"
    assert row["conversion_factor"] == 1
    assert row["normalized_price"] == row["raw_price"]


def test_proven_sheet_defaults_before_review_and_retains_3100_span():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "טווין 17 ממ 3100 טפ",
        "normalized_name": "Twin 17 mm",
        "material_type": "Other",
        "material_family": "other",
        "raw_unit": "unknown",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "normalized_price": 0,
        "status": "unresolved",
        "reason_codes": ["missing_unit", "missing_dimensions"],
        "identity_attributes": {"thickness_mm": 17},
    })

    _apply_material_taxonomy_to_rows(result)
    apply_price_source_material_unit_defaults(result)
    guarded = guard_price_source_row_activation(result)

    assert row["status"] == "ready"
    assert row["material_type"] == "Wood Sheets"
    assert row["raw_unit"] == row["purchase_unit"] == row["calculation_unit"] == "sheet"
    assert row["identity_attributes"]["length_mm"] == 3100
    assert "missing_unit" not in row["reason_codes"]
    assert "missing_dimensions" not in row["reason_codes"]
    assert guarded is result
    assert validate_price_source_result(result) is result


def test_sheet_identity_never_invents_a_second_side_from_star_notation():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "טווין 17 ממ 3100 טפ 2*",
        "normalized_name": "Plywood twin 17 mm",
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_unit": "board",
        "purchase_unit": "board",
        "calculation_unit": "board",
        "identity_attributes": {
            "thickness_mm": 17,
            "width_mm": 3100,
            "length_mm": 2400,
        },
    })

    normalize_price_source_sheet_rows(result)

    assert row["raw_unit"] == row["purchase_unit"] == row["calculation_unit"] == "sheet"
    assert row["identity_attributes"]["width_mm"] == 0
    assert row["identity_attributes"]["length_mm"] == 3100


def test_rows_without_a_name_or_positive_price_are_not_persisted_for_review():
    nameless = _result()["rows"][0]
    nameless["raw_description"] = ""
    nameless["normalized_name"] = ""
    zero_price = _result()["rows"][0]
    zero_price["source_row_number"] = 2
    zero_price["raw_price"] = 0
    result = _result()
    result["rows"] = [nameless, zero_price]

    assert discard_price_source_non_candidates(result) == 2
    assert result["rows"] == []


def test_supplier_merge_ignores_legal_forms_and_uses_unique_length_scaled_match():
    candidates = [
        {"supplier_id": "a", "supplier_name": "ООО Ёлочка", "normalized_name": "ооо елочка"},
        {"supplier_id": "b", "supplier_name": "Другой поставщик", "normalized_name": "другой поставщик"},
    ]

    assert supplier_merge_key("Ёлочка בע\"מ") == supplier_merge_key("ООО Ёлочка")
    assert supplier_merge_max_distance(5) == 1
    assert supplier_merge_max_distance(9) == 5
    assert match_existing_supplier("Елочкa", candidates)["supplier_id"] == "a"


def test_supplier_merge_rejects_an_ambiguous_fuzzy_match():
    candidates = [
        {"supplier_id": "a", "supplier_name": "Wood Center", "normalized_name": "wood center"},
        {"supplier_id": "b", "supplier_name": "Wood Senter", "normalized_name": "wood senter"},
    ]

    assert match_existing_supplier("Wood Zenter", candidates) is None


def test_supplier_merge_uses_the_first_saved_supplier_for_a_timestamped_tie():
    candidates = [
        {
            "supplier_id": "first",
            "supplier_name": "Wood Center",
            "normalized_name": "wood center",
            "created_at": "2026-10-05T09:57:00+00:00",
        },
        {
            "supplier_id": "later",
            "supplier_name": "Wood Senter",
            "normalized_name": "wood senter",
            "created_at": "2026-10-05T12:01:00+00:00",
        },
    ]

    assert match_existing_supplier("Wood Zenter", candidates)["supplier_id"] == "first"


def test_supplier_merge_keeps_first_saved_canonical_when_later_ocr_is_closer():
    candidates = [
        {"supplier_id": "first", "supplier_name": "Wood Center Ltd", "created_at": "2026-10-05T09:57:00+00:00"},
        {"supplier_id": "later", "supplier_name": "Wood Zenter", "created_at": "2026-10-05T12:01:00+00:00"},
    ]

    assert match_existing_supplier("Wood Zenter", candidates)["supplier_id"] == "first"


def test_supplier_merge_uses_hp_before_unreliable_ocr_name():
    candidates = [
        {"supplier_id": "first", "supplier_name": "Wood Center", "supplier_hp": "HP-120", "created_at": "2026-10-05T09:57:00+00:00"},
        {"supplier_id": "other", "supplier_name": "Other supplier", "supplier_hp": "HP-222", "created_at": "2026-10-05T10:00:00+00:00"},
    ]

    assert match_existing_supplier("Unreadable OCR issuer", candidates, supplier_hp="hp 120")["supplier_id"] == "first"


def test_company_identity_is_an_exact_supplier_blacklist():
    identity = company_identity_blacklist({
        "company_name": "Wooden Heart",
        "legal_name": "Wooden Heart Ltd",
        "legal_name_hebrew": "וודן הארט בעמ",
        "company_registration_number": "514-539-998",
    })

    assert identity["hp"] == "514539998"
    assert supplier_is_company_identity(
        "Wooden Heart Ltd", "", company_identity=identity,
    )
    assert supplier_is_company_identity(
        "Unrelated OCR", "514539998", company_identity=identity,
    )
    assert not supplier_is_company_identity(
        "Wooden Hearts Supply", "", company_identity=identity,
    )


def test_issuer_identity_reads_all_israeli_business_number_labels_before_buyer():
    text = (
        'א.ש. פירוזל בע"מ\nע.מ. 513453233\n'
        'לכבוד: לב קגלס\nח.פ. 337791438'
    )

    assert issuer_identity_from_source_text(text) == {
        "supplier_name": "א.ש. פירוזל",
        "supplier_hp": "513453233",
    }
    assert issuer_identity_from_source_text("ע.פ. 123456789\nלכבוד: buyer")["supplier_hp"] == "123456789"
    assert issuer_identity_from_source_text("H.P. 987654321\nלכבוד: buyer")["supplier_hp"] == "987654321"
    assert issuer_identity_from_source_text('לבידי בוקטוס בע"מ\nפ.ח 514539998')["supplier_hp"] == "514539998"
    assert issuer_identity_from_source_text('לבידי בוקטוס בע"מ\n514539998 פ.ח')["supplier_hp"] == "514539998"
    assert issuer_identity_from_source_text("מ.ע. 123456789\nלכבוד: buyer")["supplier_hp"] == "123456789"


def test_issuer_header_repairs_a_buyer_selected_as_supplier():
    result = _result()
    result.update({"supplier_name": "לב קגלס", "supplier_hp": "337791438"})
    company_identity = company_identity_blacklist({
        "company_name": "לב קגלס",
        "company_registration_number": "337791438",
    })

    assert repair_supplier_from_issuer_evidence(
        result,
        issuer_identity={"supplier_name": "א.ש. פירוזל", "supplier_hp": "513453233"},
        company_identity=company_identity,
    )
    assert result["supplier_name"] == "א.ש. פירוזל"
    assert result["supplier_hp"] == "513453233"


def test_supplier_hp_defaults_to_exactly_nine_digits_or_empty():
    result = _result()
    result["supplier_hp"] = "514-539-998"

    assert apply_price_source_document_defaults(result, source_kind="file")["supplier_hp"] == "514539998"

    result["supplier_hp"] = "customer 337791438 / seller unknown"
    assert apply_price_source_document_defaults(result, source_kind="file")["supplier_hp"] == ""


def test_material_structural_key_ignores_sheet_wording_but_keeps_perforation():
    base = _result()["rows"][0]
    base.update({
        "material_family": "twin plywood",
        "normalized_name": "Twin plywood 17 mm",
        "identity_attributes": {**base["identity_attributes"], "thickness_mm": 17, "length_mm": 3100},
    })
    variant = deepcopy(base)
    variant["normalized_name"] = "Plywood twin 17 mm sheet"
    perforated = deepcopy(base)
    perforated["identity_attributes"]["construction"] = "perforated"

    assert material_structural_key(base) == material_structural_key(variant)
    assert material_structural_key(base) != material_structural_key(perforated)


def test_same_supplier_material_merge_keeps_proved_wood_species_separate():
    first = _result()["rows"][0]
    first.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_price": 110,
        "identity_attributes": {
            **first["identity_attributes"], "thickness_mm": 17, "species": "okoume",
        },
    })
    other_species = deepcopy(first)
    other_species["identity_attributes"]["species"] = "birch"

    assert not price_rows_match_same_supplier_material(first, other_species)


def test_same_supplier_material_merge_keeps_two_proved_brands_separate_but_tolerates_absence():
    first = _result()["rows"][0]
    first.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_price": 110,
        "identity_attributes": {
            **first["identity_attributes"], "thickness_mm": 17, "brand": "EGGER",
        },
    })
    other_brand = deepcopy(first)
    other_brand["identity_attributes"]["brand"] = "Kronospan"
    no_brand = deepcopy(first)
    no_brand["identity_attributes"]["brand"] = ""

    assert not price_rows_match_same_supplier_material(first, other_brand)
    assert price_rows_match_same_supplier_material(first, no_brand)


def test_same_supplier_material_merge_allows_decor_and_sku_variants():
    first = _result()["rows"][0]
    first.update({
        "material_type": "Wood Sheets",
        "material_family": "twin plywood",
        "raw_sku": "WHITE-17",
        "raw_price": 110,
        "identity_attributes": {**first["identity_attributes"], "thickness_mm": 17, "width_mm": 3100},
    })
    second = deepcopy(first)
    second.update({"raw_sku": "BLACK-17", "normalized_name": "Plywood twin 17 mm black"})

    assert price_rows_match_same_supplier_material(first, second)


def test_same_supplier_material_merge_collapses_perforation_only_at_equal_price():
    base = _result()["rows"][0]
    base.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_sku": "",
        "raw_price": 110,
        "identity_attributes": {**base["identity_attributes"], "thickness_mm": 17, "width_mm": 3100},
    })
    perforated = deepcopy(base)
    perforated["identity_attributes"]["construction"] = "perforated"
    other_price = deepcopy(base)
    other_price["raw_price"] = 111
    other_thickness = deepcopy(base)
    other_thickness["identity_attributes"]["thickness_mm"] = 18

    assert price_rows_match_same_supplier_material(base, perforated)
    assert not price_rows_match_same_supplier_material(base, other_price)
    assert not price_rows_match_same_supplier_material(base, other_thickness)


def test_same_supplier_material_merge_uses_sku_over_price_and_spurious_dimensions():
    """A repeated supplier SKU survives price volatility and bad OCR geometry."""
    first = _result()["rows"][0]
    first.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_sku": "27",
        "raw_price": 110,
        "identity_attributes": {
            **first["identity_attributes"],
            "thickness_mm": 17,
            "width_mm": 3100,
            "length_mm": 3100,
            "construction": "twin",
        },
    })
    repeated = deepcopy(first)
    repeated.update({"raw_price": 117})
    repeated["identity_attributes"].update({"width_mm": 3100, "length_mm": 2000})

    assert price_rows_match_same_supplier_material(first, repeated)

    perforated = deepcopy(repeated)
    perforated["identity_attributes"]["construction"] = "perforated twin"
    assert not price_rows_match_same_supplier_material(first, perforated)


def test_hardware_merge_ignores_quantity_and_requires_same_sku_and_name_overlap():
    base = _result()["rows"][0]
    base.update(
        {
            "material_type": "Hardware",
            "material_family": "hinge",
            "normalized_name": "Blum hinge 110 soft close",
            "raw_sku": "71B358E",
            "raw_price": 14.08,
            "raw_quantity": 10,
        }
    )
    same_item = deepcopy(base)
    same_item.update({"normalized_name": "Soft close Blum hinge 110", "raw_quantity": 1000})
    other_sku = deepcopy(base)
    other_sku["raw_sku"] = "17JH710"
    unrelated_name = deepcopy(base)
    unrelated_name["normalized_name"] = "Movento rail double 750"

    assert price_rows_match_same_supplier_material(base, same_item)
    assert not price_rows_match_same_supplier_material(base, other_sku)
    assert not price_rows_match_same_supplier_material(base, unrelated_name)


def test_hardware_catalog_key_keeps_different_sku_rows_separate():
    base = _result()["rows"][0]
    base.update(
        {
            "material_type": "Hardware",
            "material_family": "rail",
            "normalized_name": "Movento rail double 750",
            "raw_sku": "T766H750",
            "raw_price": 217.6,
        }
    )
    other_sku = deepcopy(base)
    other_sku["raw_sku"] = "B766H750"

    assert material_catalog_key(base) != material_catalog_key(other_sku)


def test_hardware_persisted_key_keeps_different_skus_separate_for_database_uniqueness():
    base = _result()["rows"][0]
    base.update(
        {
            "material_type": "Hardware",
            "material_family": "drawer slide",
            "normalized_name": "Drawer slide 750 mm double",
            "raw_sku": "T766H750",
        }
    )
    other_sku = deepcopy(base)
    other_sku["raw_sku"] = "B766H750"

    assert material_persisted_normalized_name(base) != material_persisted_normalized_name(other_sku)
    assert "sku:t766h750" in material_persisted_normalized_name(base)


def test_non_hardware_persisted_key_remains_its_structural_identity():
    row = _result()["rows"][0]

    assert json.loads(material_persisted_normalized_name(row)) == list(material_structural_key(row))


def test_hardware_same_sku_keeps_identity_when_supplier_price_changes():
    row = _result()["rows"][0]
    row.update(
        {
            "material_type": "Hardware",
            "normalized_name": "Blum hinge 110 soft close",
            "raw_sku": "71B358E",
            "raw_price": 15.4,
            "raw_unit": "piece",
            "purchase_unit": "piece",
            "calculation_unit": "piece",
            "raw_currency": "ILS",
            "raw_vat_mode": "excluded",
        }
    )
    offer = {
        "supplier_sku": "71B358E",
        "source_price": 14.08,
        "source_unit": "piece",
        "purchase_unit": "piece",
        "calculation_unit": "piece",
        "currency": "ILS",
        "vat_included": False,
    }
    material = {
        "category": "Hardware",
        "canonical_name": "Blum hinge 110 soft close",
        "specifications": {"source_sku": "71B358E"},
    }

    assert material_offer_matches_extracted_row(
        offer, material, row, default_currency="ILS"
    )


def test_same_supplier_offer_merge_allows_sku_variants_but_needs_same_thickness():
    row = _result()["rows"][0]
    row.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_sku": "B-17",
        "raw_price": 110,
        "raw_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "normalized_price": 110,
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 17},
    })
    offer = {
        "source_price": 110,
        "source_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "normalized_price": 110,
        "currency": "ILS",
        "vat_included": False,
    }
    material = {
        "category": "Wood Sheets",
        "specifications": {"material_family": "twin plywood", "thickness_mm": 17},
    }

    assert material_offer_matches_same_supplier_material(offer, material, row, default_currency="ILS")
    material["specifications"]["thickness_mm"] = 18
    assert not material_offer_matches_same_supplier_material(offer, material, row, default_currency="ILS")


def test_same_supplier_offer_merge_reuses_canonical_material_for_conflicting_dimensions():
    row = _result()["rows"][0]
    row.update({
        "material_type": "Wood Sheets",
        "material_family": "plywood",
        "raw_sku": "27",
        "raw_price": 110,
        "raw_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "raw_currency": "ILS",
        "raw_vat_mode": "excluded",
        "identity_attributes": {
            **row["identity_attributes"],
            "thickness_mm": 17,
            "width_mm": 3100,
            "length_mm": 2000,
            "construction": "twin",
        },
    })
    offer = {
        "supplier_sku": "27",
        "source_price": 110,
        "source_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "currency": "ILS",
        "vat_included": False,
    }
    material = {
        "category": "Wood Sheets",
        "specifications": {
            "material_family": "plywood",
            "source_sku": "27",
            "thickness_mm": 17,
            "width_mm": 3100,
            "length_mm": 3100,
            "construction": "twin",
        },
    }

    assert material_offer_matches_same_supplier_material(offer, material, row, default_currency="ILS")


def test_existing_supplier_offer_can_prove_an_unknown_brand_family():
    row = _result()["rows"][0]
    row.update({
        "material_family": "",
        "raw_sku": "4",
        "raw_price": 65,
        "raw_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "normalized_price": 65,
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 5, "width_mm": 3100, "length_mm": 0},
    })
    offer = {"source_price": 65, "source_unit": "sheet", "currency": "ILS", "vat_included": False}
    material = {
        "canonical_name": "Okume plywood 5 mm",
        "specifications": {"material_family": "plywood", "thickness_mm": 5, "width_mm": 3100},
    }

    assert material_offer_proves_unknown_family(offer, material, row, default_currency="ILS") == "plywood"


def test_same_supplier_source_wording_merges_despite_changed_family_label():
    row = _result()["rows"][0]
    row.update({
        "material_family": "plywood",
        "raw_description": "טווין 17 ממ 3100 טפ *2",
        "raw_price": 110,
        "raw_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "normalized_price": 110,
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 17, "width_mm": 3100, "length_mm": 0},
    })
    offer = {"source_price": 110, "source_unit": "sheet", "currency": "ILS", "vat_included": False}
    material = {
        "canonical_name": "Twin 17 mm",
        "specifications": {
            "source_description_key": "טווין 17 ממ 3100 טפ 2",
            "material_family": "laminated particleboard",
            "thickness_mm": 17,
            "width_mm": 3100,
        },
    }

    assert material_offer_matches_same_supplier_description(
        offer, material, row, default_currency="ILS"
    )


def test_sheet_normalization_canonicalizes_explicit_surface_descriptors():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "Twin plywood 17 mm מבוקע high gloss",
        "normalized_name": "Twin plywood 17mm cut to size sheet",
        "material_type": "Wood Sheets",
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 17},
    })

    normalize_price_source_sheet_rows(result)

    assert row["identity_attributes"]["construction"] == "perforated twin"
    assert row["identity_attributes"]["finish"] == "glossy"
    assert row["normalized_name"] == "Plywood 17 mm, perforated twin, glossy"


def test_sheet_normalization_replaces_wrong_glass_label_when_okoume_proves_plywood():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "לוח אוקומה 5 ממ 3100",
        "normalized_name": "Glass 5mm 3100 sheet",
        "material_type": "Glass",
        "material_family": "glass",
        "raw_unit": "piece",
        "purchase_unit": "piece",
        "calculation_unit": "piece",
        "conversion_factor": 1,
        "normalized_price": row["raw_price"],
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 5, "width_mm": 3100},
    })

    normalize_price_source_sheet_rows(result)

    assert row["material_type"] == "Wood Sheets"
    assert row["material_family"] == "plywood"
    assert row["identity_attributes"]["species"] == "okoume"
    assert row["purchase_unit"] == row["calculation_unit"] == "sheet"


def test_sheet_taxonomy_removes_hallucinated_glass_and_resolves_known_okoume():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "אוקמה 5 ממ 3100 טפ 1*",
        "normalized_name": "Glass Aukma 5 mm 3100 1-Pack",
        "material_type": "Other",
        "material_family": "other",
        "status": "unresolved",
        "reason_codes": ["unknown_product_term"],
        "raw_unit": "piece",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "normalized_price": row["raw_price"],
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 5},
    })

    normalize_price_source_sheet_rows(result)

    assert row["status"] == "ready"
    assert row["normalized_name"] == "Plywood 5 mm, Okoume"
    assert "Glass" not in row["normalized_name"]
    assert "unknown_product_term" not in row["reason_codes"]


def test_sheet_taxonomy_replaces_model_acrylic_label_when_okoume_proves_plywood():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "אוקמה 5 ממ 3100 טפ 1*",
        "normalized_name": "Acrylic 5 mm",
        "material_type": "Other",
        "material_family": "other",
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 5},
    })

    normalize_price_source_sheet_rows(result)

    assert row["material_type"] == "Wood Sheets"
    assert row["material_family"] == "plywood"
    assert row["normalized_name"] == "Plywood 5 mm, Okoume"


def test_sheet_taxonomy_accepts_compact_hebrew_mdf_abbreviation():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "מדפ 19 יצוק לבן חלק ירוק",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
        "status": "unresolved",
        "reason_codes": ["unknown_product_term"],
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 19},
    })

    normalize_price_source_sheet_rows(result)

    assert row["status"] == "ready"
    assert row["material_type"] == "Wood Sheets"
    assert row["material_family"] == "mdf"
    assert row["normalized_name"] == "MDF 19 mm, white"


@pytest.mark.parametrize("alias", ("MDF", "m.d.f", "m d f", "מדי אף", "אמ די אף", "מדפ", "מ.ד.פ", "מ ד פ"))
def test_mdf_taxonomy_covers_safe_english_hebrew_and_ocr_variants(alias):
    rule = material_rule_for_text(f"לוח {alias} 19 ממ".casefold())

    assert rule is not None
    assert rule.category == "Wood Sheets"
    assert rule.family == "mdf"


def test_hebrew_item_abbreviation_normalizes_before_sheet_rules():
    result = _result()
    row = result["rows"][0]
    row.update({"raw_unit": "יח", "purchase_unit": "sheet", "calculation_unit": "sheet"})

    normalize_price_source_units(result)
    normalize_price_source_sheet_rows(result)

    assert row["raw_unit"] == "sheet"


def test_sheet_normalization_classifies_proved_hebrew_trade_families_without_supplier_logic():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "טווין 17 ממ 3100 טפ 2*",
        "normalized_name": "Unclassified sheet material",
        "material_type": "Other",
        "material_family": "other",
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 17},
    })

    normalize_price_source_sheet_rows(result)

    assert row["material_type"] == "Wood Sheets"
    assert row["material_family"] == "plywood"
    assert row["identity_attributes"]["construction"] == "twin"
    assert row["normalized_name"] == "Plywood 17 mm, twin"
    assert "taxonomy_wood_sheets" in row["reason_codes"]


def test_sheet_normalization_keeps_okume_perforated_separate_from_the_plain_family():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "אוקמה 5 ממ מבוקע 1*",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
        "identity_attributes": {**row["identity_attributes"], "thickness_mm": 5},
    })

    normalize_price_source_sheet_rows(result)

    assert row["material_type"] == "Wood Sheets"
    assert row["material_family"] == "plywood"
    assert row["normalized_name"] == "Plywood 5 mm, Okoume, perforated"
    assert row["identity_attributes"]["construction"] == "perforated"


def test_sheet_normalization_keeps_proved_glass_category():
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": "Glass sheet 5 mm 3100",
        "normalized_name": "Glass 5 mm 3100 sheet",
        "material_type": "Glass",
        "material_family": "glass",
    })

    normalize_price_source_sheet_rows(result)

    assert row["material_type"] == "Glass"
    assert row["normalized_name"] == "Glass 5 mm 3100 sheet"


@pytest.mark.parametrize(
    ("description", "category", "family"),
    [
        ("לוח MDF ירוק 17 ממ", "Wood Sheets", "mdf"),
        ("oak planed timber 40 mm", "Solid Wood", "solid timber"),
        ("ציר מטבח", "Hardware", "hinge"),
        ("aluminium profile 30x30", "Metal Profiles", "metal profile"),
        ("פח נירוסטה 2 ממ", "Metal Sheets", "metal sheet"),
        ("powder coating black", "Paints & Coatings", "powder coating"),
        ("לכה מט", "Paints & Coatings", "lacquer"),
    ],
)
def test_bilingual_taxonomy_covers_all_material_departments(description, category, family):
    result = _result()
    row = result["rows"][0]
    row.update({
        "raw_description": description,
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
    })

    assert apply_material_taxonomy(row) is True
    assert row["material_type"] == category
    assert row["material_family"] == family


def test_taxonomy_preserves_a_category_scoped_brand_and_sheet_primary_attribute():
    row = _result()["rows"][0]
    row.update({
        "raw_description": "EGGER plywood 17 mm 3100",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
    })

    assert apply_material_taxonomy(row) is True
    assert row["material_type"] == "Wood Sheets"
    assert row["identity_attributes"]["brand"] == "EGGER"
    assert row["identity_attributes"]["primary_attribute"] == "17 mm"
    assert row["normalized_name"].startswith("Plywood 17 mm EGGER")


@pytest.mark.parametrize(
    ("description", "category", "brand"),
    [
        ("לביד אגר 17 ממ", "Wood Sheets", "EGGER"),
        ("לוח MDF קרונוספן 18 ממ", "Wood Sheets", "Kronospan"),
        ("ציר טיטוס 110 מעלות", "Hardware", "Titus"),
        ("מסילת מגירה אקורייד 550 ממ", "Hardware", "Accuride"),
        ("פרופיל קליל 40x40", "Metal Profiles", "Klil"),
        ("זכוכית פילקינגטון 6 ממ", "Glass", "Pilkington"),
        ("לכה טמבור מט", "Paints & Coatings", "Tambour"),
    ],
)
def test_taxonomy_normalizes_hebrew_brand_aliases_to_one_english_canonical_name(
    description, category, brand,
):
    row = _result()["rows"][0]
    row.update({
        "raw_description": description,
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
    })

    assert apply_material_taxonomy(row) is True
    assert row["material_type"] == category
    assert row["identity_attributes"]["brand"] == brand
    assert row["identity_attributes"]["brand_basis"] == "catalog"


def test_taxonomy_preserves_an_unknown_proper_name_as_brand_candidate():
    row = _result()["rows"][0]
    row.update({
        "raw_description": "Plywood 17 mm Mario Box double sided",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
        "identity_attributes": {
            **row["identity_attributes"], "brand": "", "brand_basis": "unknown",
        },
    })

    assert apply_material_taxonomy(row) is True
    assert row["identity_attributes"]["brand"] == "Mario Box"
    assert row["identity_attributes"]["brand_basis"] == "candidate"


def test_taxonomy_keeps_aisi_as_grade_and_profile_section_as_primary_attribute():
    row = _result()["rows"][0]
    row.update({
        "raw_description": "stainless steel profile AISI 304 40x40 mm",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
    })

    assert apply_material_taxonomy(row) is True
    assert row["material_type"] == "Metal Profiles"
    assert row["identity_attributes"]["grade"] == "AISI 304"
    assert row["identity_attributes"]["primary_attribute"] == "40×40 mm"


def test_brand_never_classifies_a_material_without_generic_evidence():
    assert material_rule_for_text("EGGER U999") is None


def test_glass_door_closure_is_hardware_not_glass_and_keeps_compact_brand_candidate():
    row = _result()["rows"][0]
    row.update({
        "raw_description": "Glass door closure white 550 mm Pure high internal front Mario Box",
        "normalized_name": "Unclassified material",
        "material_type": "Other",
        "material_family": "other",
        "identity_attributes": {
            **row["identity_attributes"], "primary_attribute": "", "brand": "",
        },
    })

    assert apply_material_taxonomy(row) is True
    assert row["material_type"] == "Hardware"
    assert row["material_family"] == "door closure"
    assert row["identity_attributes"]["primary_attribute"] == "550 mm"
    assert row["identity_attributes"]["brand"] == "Mario Box"
    assert row["normalized_name"] == "Door Closure 550 mm Mario Box, white"


@pytest.mark.parametrize(
    ("description", "operation_code"),
    [
        ("חיתוך + קנטים", "supplier_cut_and_edge_banding"),
        ("פס חיתוך + קנט", "supplier_cut_and_edge_banding"),
        ("חיתוך וקנת", "supplier_cut_and_edge_banding"),
        ("edge banding", "edge_banding"),
        ("CNC drilling", "cnc_vertical_drilling"),
        ("הרכבת גוף", "carcass_assembly"),
        ("עבודת חיתוך לייזר", "sheet_laser_cutting"),
        ("powder coating service", "powder_coating_application"),
    ],
)
def test_bilingual_material_jobs_dictionary_resolves_existing_operations(description, operation_code):
    assert job_operation_for_text(description.casefold()) == operation_code


def test_explicit_cut_and_edge_work_overrides_an_incorrect_material_classification():
    result = _result()
    row = result["rows"][0]
    row.update({
        "item_kind": "material",
        "material_type": "Wood Supplies",
        "material_family": "edge banding",
        "raw_description": "פס חיתוך + קנט 29.00",
        "normalized_name": "Edge Banding Cutting Strip",
    })

    normalize_price_source_sheet_rows(result)

    assert row["item_kind"] == "operation_service"
    assert row["normalized_name"] == "Cutting and edge banding"
    assert prepare_price_source_operation_rows(result) == {1: "supplier_cut_and_edge_banding"}


def test_bare_edge_band_product_is_not_promoted_to_a_material_job():
    row = _result()["rows"][0]
    row.update({
        "item_kind": "material",
        "raw_description": "PVC edge band white 22 mm",
        "normalized_name": "PVC edge band white",
    })

    assert apply_operation_taxonomy(row) is None
    assert row["item_kind"] == "material"


def test_identity_attributes_require_the_fixed_contract():
    result = _result()
    del result["rows"][0]["identity_attributes"]["thickness_mm"]

    with pytest.raises(PriceSourceSchemaError, match="identity attributes"):
        validate_price_source_result(result)


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


def test_meaningful_negative_invoice_discount_is_normalized_to_a_magnitude():
    result = _result()
    result["rows"][0]["raw_discount_percent"] = "-10%"
    result["rows"][0]["raw_discount_amount"] = -7.5

    normalized = normalize_price_source_optional_numbers(result)

    assert normalized["rows"][0]["raw_discount_percent"] == 10
    assert normalized["rows"][0]["raw_discount_amount"] == 7.5
    assert validate_price_source_result(normalized) is normalized


def test_invoice_footer_rounding_discount_is_not_persisted_on_a_material_row():
    result = _result()
    result["rows"][0]["raw_discount_percent"] = "-0.02%"
    result["rows"][0]["raw_discount_amount"] = "-0.38"

    normalized = normalize_price_source_optional_numbers(result)

    assert normalized["rows"][0]["raw_discount_percent"] == 0
    assert normalized["rows"][0]["raw_discount_amount"] == 0


def test_negative_return_line_is_excluded_without_rejecting_the_invoice():
    result = _result()
    row = result["rows"][0]
    row["raw_quantity"] = -3
    row["raw_line_total"] = -360

    normalized = normalize_price_source_optional_numbers(result)

    assert row["status"] == "excluded"
    assert row["raw_quantity"] == 3
    assert "return_or_credit_line" in row["reason_codes"]
    assert validate_price_source_result(normalized) is normalized


def test_numeric_invoice_item_codes_are_preserved_as_sku_not_row_numbers():
    result = _result()
    first = result["rows"][0]
    first["source_row_number"] = 27
    first["raw_sku"] = ""
    second = deepcopy(first)
    second["source_row_number"] = 41
    second["raw_sku"] = ""
    result["rows"].append(second)

    normalized = normalize_price_source_row_identity_fields(result)

    assert [row["source_row_number"] for row in normalized["rows"]] == [1, 2]
    assert [row["raw_sku"] for row in normalized["rows"]] == ["27", "41"]


def test_line_quantity_does_not_block_a_proven_sheet_price():
    result = _result(confidence=95)
    row = result["rows"][0]
    row["raw_package_quantity"] = 25
    row["purchase_unit"] = "sheet"
    row["calculation_unit"] = "sheet"
    row["conversion_factor"] = 1
    row["normalized_price"] = row["raw_price"]

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "ready"
    assert "package_conversion_unresolved" not in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


def test_supplier_operation_offer_comparison_ignores_raw_service_spelling():
    row = _result(confidence=95)["rows"][0]
    row.update({"raw_price": 17.5, "raw_unit": "piece", "raw_currency": "ILS"})
    offer = {
        "source_price": 17.5,
        "pricing_basis": "supplier_defined",
        "source_unit_label": "piece",
        "currency": "ILS",
        "vat_included": False,
    }

    assert supplier_operation_offer_matches_row(
        offer, row, pricing_basis="supplier_defined", default_currency="ILS"
    )


def test_supplier_defined_operation_matches_when_invoice_omits_a_piece_unit():
    row = _result(confidence=95)["rows"][0]
    row.update({"raw_price": 17.5, "raw_unit": "", "raw_currency": "ILS"})
    offer = {
        "source_price": 17.5,
        "pricing_basis": "supplier_defined",
        "source_unit_label": "piece",
        "currency": "ILS",
        "vat_included": False,
    }

    assert supplier_operation_offer_matches_row(
        offer, row, pricing_basis="supplier_defined", default_currency="ILS"
    )


def test_supplier_defined_job_catalog_identity_ignores_piece_vs_missing_unit():
    common = {
        "operation_id": "operation-1",
        "supplier_id": "supplier-1",
        "pricing_basis": "supplier_defined",
        "source_price": 17.5,
        "currency": "ILS",
        "vat_included": False,
    }

    assert supplier_operation_offer_catalog_key(
        {**common, "source_unit_label": "piece"}
    ) == supplier_operation_offer_catalog_key({**common, "source_unit_label": None})


def test_material_offer_comparison_reuses_sheet_despite_line_quantity_words():
    row = _result(confidence=95)["rows"][0]
    row.update(
        {
            "normalized_name": "Plywood Twin 17mm Split ×2",
            "material_family": "Plywood",
            "raw_price": 110,
            "raw_unit": "sheet",
            "raw_currency": "ILS",
            "identity_attributes": {
                **row["identity_attributes"],
                "thickness_mm": 17,
                "width_mm": 0,
                "length_mm": 0,
            },
        }
    )
    offer = {"source_price": 110, "source_unit": "sheet", "currency": "ILS", "vat_included": False}
    material = {"canonical_name": "Plywood Twin 17 mm × 3100 mm"}

    assert material_offer_matches_extracted_row(
        offer, material, row, default_currency="ILS"
    )


def test_unknown_vat_basis_cannot_activate():
    result = _result(confidence=95)
    result["rows"][0]["raw_vat_mode"] = "unknown"

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "vat_basis_unknown" in guarded["rows"][0]["reason_codes"]


def test_unknown_canonical_unit_is_sent_to_review_not_allowed_to_fail_the_source():
    result = _result(confidence=95)
    result["rows"][0]["purchase_unit"] = "unknown"
    result["rows"][0]["calculation_unit"] = "unknown"
    result["rows"][0]["conversion_factor"] = 0
    result["rows"][0]["normalized_price"] = 0

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "missing_unit" in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


def test_known_material_job_with_unknown_unit_uses_its_canonical_supplier_basis():
    result = _result(confidence=95)
    row = result["rows"][0]
    row.update({
        "item_kind": "operation_service",
        "raw_description": "פס חיתוך + קנט",
        "normalized_name": "Cut and edge banding",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "normalized_price": 0,
    })

    guarded = guard_price_source_row_activation(result)
    assert prepare_price_source_operation_rows(guarded) == {1: "supplier_cut_and_edge_banding"}

    assert guarded["rows"][0]["status"] == "ready"
    assert "missing_unit" not in guarded["rows"][0]["reason_codes"]
    assert "operation_type_unresolved" not in guarded["rows"][0]["reason_codes"]


def test_confidence_and_other_material_type_do_not_block_a_usable_price():
    result = _result(confidence=42)
    result["rows"][0]["material_type"] = "Other"

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "ready"
    assert "material_type_unresolved" not in guarded["rows"][0]["reason_codes"]


def test_price_source_schema_requires_a_supported_row_material_type():
    result = _result()
    result["rows"][0]["material_type"] = "Unknown category"
    with pytest.raises(PriceSourceSchemaError, match="row material type"):
        validate_price_source_result(result)


def test_mixed_material_types_are_preserved_per_row():
    result = _result()
    result["rows"].append(
        {
            **result["rows"][0],
            "source_row_number": 2,
            "material_type": "Metal Profiles",
            "raw_description": "Steel angle 30x30",
            "normalized_name": "Steel angle 30x30",
        }
    )

    assert validate_price_source_result(result) is result
    assert price_source_material_types(result) == ["Metal Profiles", "Wood Sheets"]


def test_source_department_does_not_change_row_review_status():
    result = _result()
    result["rows"][0]["material_type"] = "Metal Sheets"

    guarded = guard_price_source_department(result, "Wood")

    assert guarded["rows"][0]["status"] == "ready"
    assert "selected_department_mismatch" not in guarded["rows"][0]["reason_codes"]


def test_explicit_document_totals_are_reconciled_deterministically():
    valid = _result()
    assert guard_price_source_document_totals(valid)["rows"][0]["confidence"] == 96

    mismatch = _result()
    mismatch["document_total"] = 125
    guarded = guard_price_source_document_totals(mismatch)
    assert guarded["rows"][0]["confidence"] == 76
    assert "document_total_mismatch" in guarded["rows"][0]["reason_codes"]


def test_semantic_fingerprint_detects_same_document_across_file_variants():
    original = _result()
    rescan = _result()
    rescan["rows"][0]["evidence_reference"] = "photo 2 row 8"
    rescan["document_total"] = 106.19
    assert price_source_semantic_fingerprint(original) == price_source_semantic_fingerprint(rescan)

    different_document = _result()
    different_document["document_number"] = "PL-205"
    assert price_source_semantic_fingerprint(original) != price_source_semantic_fingerprint(
        different_document
    )


def _template_workbook_bytes(*, price: float, material: str = "Plywood") -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Estimate"
    sheet.merge_cells("A1:D1")
    sheet["A1"] = "Workshop material estimate"
    sheet["A1"].font = sheet["A1"].font.copy(bold=True)
    for column, heading in enumerate(("Material", "Unit", "Quantity", "Price"), 1):
        cell = sheet.cell(row=3, column=column, value=heading)
        cell.font = cell.font.copy(bold=True)
    sheet.append([material, "sheet", 2, price])
    sheet["D5"] = "=C4*D4"
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_template_fingerprint_ignores_spreadsheet_values():
    original = _template_workbook_bytes(price=75, material="Plywood")
    changed = _template_workbook_bytes(price=82, material="OSB")

    assert price_source_template_fingerprint("estimate.xlsx", original) == (
        price_source_template_fingerprint("renamed-estimate.xlsx", changed)
    )


def test_template_fingerprint_changes_with_spreadsheet_structure():
    original = _template_workbook_bytes(price=75)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Different template"
    sheet.append(["SKU", "Description", "Net", "VAT", "Gross"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()

    assert price_source_template_fingerprint("estimate.xlsx", original) != (
        price_source_template_fingerprint("estimate.xlsx", output.getvalue())
    )


def test_template_identity_links_renamed_workbook_revisions():
    result = _result()
    template = price_source_template_fingerprint(
        "estimate.xlsx", _template_workbook_bytes(price=75)
    )

    first = price_source_family_identity(
        result,
        source_name="estimate-january.xlsx",
        source_kind="file",
        template_sha256=template,
    )
    changed_classification = deepcopy(result)
    changed_classification["document_type"] = "internal_estimate"
    second = price_source_family_identity(
        changed_classification,
        source_name="estimate-february.xlsx",
        source_kind="file",
        template_sha256=template,
    )

    assert first == second


def test_source_family_identity_stays_stable_across_changed_file_revisions():
    original = _result()
    changed = _result()
    changed["rows"][0]["raw_price"] = 95
    changed["rows"][0]["normalized_price"] = 95 / 2.9768

    original_family = price_source_family_identity(
        original,
        source_name="supplier-prices.xlsx",
        source_kind="file",
    )
    changed_family = price_source_family_identity(
        changed,
        source_name="supplier-prices.xlsx",
        source_kind="file",
    )

    assert original_family == changed_family
    assert original_family[1].startswith("PSF-")


def test_source_family_identity_ignores_url_query_refresh_tokens():
    result = _result()

    first = price_source_family_identity(
        result,
        source_name="https://supplier.example/prices?cache=one",
        source_kind="url",
    )
    second = price_source_family_identity(
        result,
        source_name="https://supplier.example/prices?cache=two",
        source_kind="url",
    )

    assert first == second


def test_source_family_revision_links_to_latest_revision():
    client = _CatalogClient(
        {
            "company_price_sources": [
                {
                    "source_id": "source-2",
                    "processing_summary": {
                        "source_family_sha256": "family-1",
                        "source_revision": 2,
                    },
                },
                {
                    "source_id": "source-1",
                    "processing_summary": {
                        "source_family_sha256": "family-1",
                        "source_revision": 1,
                    },
                },
            ]
        }
    )

    previous, revision = _find_previous_source_revision(
        client,
        "company-1",
        family_sha256="family-1",
        semantic_sha256="semantic-1",
    )

    assert previous["source_id"] == "source-2"
    assert revision == 3


def test_exact_duplicate_summary_keeps_source_family_metadata():
    summary = _unchanged_duplicate_summary(
        {
            "processing_summary": {
                "total": 10,
                "ready": 8,
                "unresolved": 2,
                "source_family_sha256": "family-1",
                "source_family_code": "PSF-123456789ABC",
                "source_revision": 3,
                "previous_source_id": "source-2",
            }
        }
    )

    assert summary["unchanged"] == 8
    assert summary["source_family_code"] == "PSF-123456789ABC"
    assert summary["source_revision"] == 3


def test_price_offer_diff_ignores_representation_but_detects_price_affecting_changes():
    row = _result()["rows"][0]
    offer = {
        "source_price": "90.0000",
        "source_unit": "sheets",
        "purchase_unit": "sheet",
        "calculation_unit": "m2",
        "conversion_factor": "2.97680000",
        "normalized_price": f'{row["normalized_price"]:.4f}',
        "currency": "ils",
        "vat_included": False,
    }

    assert price_offer_matches_row(offer, row, default_currency="ILS") is True

    changed_price = {**row, "raw_price": 91, "normalized_price": 91 / 2.9768}
    assert price_offer_matches_row(offer, changed_price, default_currency="ILS") is False

    changed_vat = {**row, "raw_vat_mode": "included"}
    assert price_offer_matches_row(offer, changed_vat, default_currency="ILS") is False


def test_price_offer_lanes_isolate_internal_families_and_supplier_offers():
    internal_first = price_offer_lane_key(
        supplier_id=None,
        source_summary={
            "source_origin": "company_internal",
            "source_family_sha256": "internal-family-1",
        },
        source_id="internal-source-1",
    )
    internal_revision = price_offer_lane_key(
        supplier_id=None,
        source_summary={
            "source_origin": "company_internal",
            "source_family_sha256": "internal-family-1",
        },
        source_id="internal-source-2",
    )
    other_internal = price_offer_lane_key(
        supplier_id=None,
        source_summary={
            "source_origin": "company_internal",
            "source_family_sha256": "internal-family-2",
        },
        source_id="internal-source-3",
    )
    supplier = price_offer_lane_key(
        supplier_id="supplier-1",
        source_summary={"source_family_sha256": "supplier-family"},
        source_id="supplier-source-1",
    )
    unknown_supplier = price_offer_lane_key(
        supplier_id=None,
        source_summary={"source_family_sha256": "supplier-family"},
        source_id="unknown-source-1",
    )

    assert internal_first == internal_revision == "internal:internal-family-1"
    assert other_internal == "internal:internal-family-2"
    assert supplier == "supplier:supplier-1"
    assert unknown_supplier == "supplier-unknown:supplier-family"
    assert len({internal_first, other_internal, supplier, unknown_supplier}) == 4


def test_internal_source_never_creates_a_supplier_from_model_output():
    internal = _result()
    internal["source_origin"] = "company_internal"
    internal["supplier_name"] = "Workshop owner"

    assert price_source_supplier_name(internal) == ""
    assert price_source_supplier_name(_result()) == "Supplier Ltd"


def test_department_can_be_left_for_automatic_detection():
    assert _validate_department("") == ""


def test_price_source_output_budget_supports_large_supplier_pages():
    assert PRICE_SOURCE_MAX_OUTPUT_TOKENS >= 32_768


def test_price_catalog_uses_three_stable_user_facing_departments():
    assert PRICE_CATALOG_DEPARTMENTS["Wood Sheets"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Wood Supplies"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Hardware"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Other"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Sheets"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Profiles"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Supplies"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Paints & Coatings"] == "Finishing"
    assert PRICE_CATALOG_DEPARTMENTS["Coating Supplies"] == "Finishing"


def test_legacy_material_types_are_canonicalized_without_splitting_filters():
    assert canonical_price_source_category("Sheet Materials") == "Wood Sheets"
    assert canonical_price_source_category("Hardware") == "Hardware"
    assert canonical_price_source_category("Metal") == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Metal"] == "Metal"


def test_four_ordered_photos_become_one_pdf_source():
    photos = []
    colors = (
        (255, 255, 255),
        (235, 235, 235),
        (220, 220, 220),
        (205, 205, 205),
    )
    for index, color in enumerate(colors, start=1):
        output = BytesIO()
        Image.new("RGB", (16, 16), color).save(output, format="PNG")
        photos.append(_UploadedPhoto(f"page-{index}.png", output.getvalue()))

    combined = combine_price_source_files(photos)

    assert combined.name == "photo-document-4-pages.pdf"
    assert combined.getvalue().startswith(b"%PDF")
    with fitz.open(stream=combined.getvalue(), filetype="pdf") as document:
        assert document.page_count == 4


def test_price_source_uploader_accepts_multiple_files_before_backend_validation():
    from screens.company_profile import _render_price_source_add

    source = inspect.getsource(_render_price_source_add)
    uploader_call = source.split("st.file_uploader(", 1)[1].split(
        ")\n", 1
    )[0]
    assert "accept_multiple_files=True" in uploader_call
    assert "type=" not in uploader_call
    assert 'label_visibility="collapsed"' in uploader_call


def test_price_source_dropzone_only_hides_native_prompt_while_empty():
    from styles.company_profile import apply_company_profile_css

    source = inspect.getsource(apply_company_profile_css)
    price_source_dropzone_rules = source.split(
        '.st-key-price_source_add_body [data-testid="stFileUploader"] section {', 1
    )[1].split(
        '.st-key-price_source_add_body [data-testid="stFileUploader"] section:hover',
        1,
    )[0]

    assert 'section:not(:has([data-testid="stFileChips"])) > *:not(input)' in (
        price_source_dropzone_rules
    )
    assert 'section:has([data-testid="stFileChips"]) > div' in (
        price_source_dropzone_rules
    )
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in source
    assert "grid-auto-rows: 74px" in source
    assert "height: 156px !important" in source
    assert "max-height: 156px !important" in source
    assert "overflow-y: auto !important" in source
    assert 'button[aria-label="Add files"]' in source
    assert "display: none !important" in source
    assert "section.costerly-upload-dragover" in source
    assert "border-color: var(--input-focus-border) !important" in source
    assert "box-shadow: 0 0 0 3px var(--input-focus-ring) !important" in source
    assert "section small" not in price_source_dropzone_rules
    assert "section button" not in price_source_dropzone_rules
    assert '[data-testid="stFileChip"] small' not in source
    assert "display: none !important" in source
    delete_rule = source.split('[data-testid="stFileChipDeleteBtn"] {', 1)[1].split(
        "}", 1
    )[0]
    assert "display: flex !important" in delete_rule
    assert "z-index: 4 !important" in delete_rule
    assert "pointer-events: auto !important" in delete_rule
    assert "costerly-single-document-selection" in source
    assert "grid-template-columns: minmax(0, 280px) !important" in source
    assert "grid-auto-rows: 132px !important" in source
    assert "width: 55px !important" in source
    assert '[data-testid="stFileUploader"].costerly-selection-warning::after' in source
    assert "content: attr(data-costerly-selection-warning)" in source
    assert "background: #FFF7D6" in source
    assert "font-size: 13px" in source


def test_price_source_fragment_does_not_dim_stale_content():
    source = Path("styles/company_profile.py").read_text()

    assert (
        '.st-key-price_source_add_card [data-testid="stElementContainer"]'
        '[data-stale="true"]'
    ) in source
    assert (
        '.st-key-price_catalog_shell [data-testid="stElementContainer"]'
        '[data-stale="true"]'
    ) in source
    assert "opacity: 1 !important" in source
    assert "transition: none !important" in source


def test_price_catalog_geometry_patch_stays_scoped_to_agreed_controls():
    screen_source = Path("screens/company_profile.py").read_text()
    style_source = Path("styles/company_profile.py").read_text()

    assert "price-catalog-title price-catalog-title-main" in screen_source
    assert 'key=f"save_price_row_{source_id}_{row_id}"' in screen_source
    assert 'key=f"cancel_price_row_{source_id}_{row_id}"' in screen_source
    assert 'st.container(key="price_review_pagination")' in screen_source
    assert "height: 45px !important;" in style_source
    assert "background: var(--button-secondary-bg-hover) !important;" in style_source
    assert "border-radius: 18px 18px 0 0;" in style_source
    assert ".st-key-price_review_pagination" in style_source
    assert "padding: 0 0 var(--space-3) var(--space-4);" in style_source
    assert ".st-key-price_review_header .price-source-row-label" in style_source
    assert "transform: translateY(9px);" in style_source


def test_price_source_processing_uses_callback_without_manual_rerun():
    from screens.company_profile import _render_price_lists, _render_price_source_add

    add_source = inspect.getsource(_render_price_source_add)
    lists_source = inspect.getsource(_render_price_lists)

    assert "on_click=_queue_price_source_processing" in add_source
    assert "install_price_source_processing_guard()" in add_source
    assert "st.rerun" not in add_source
    assert lists_source.startswith("@st.fragment")
    assert "_process_pending_price_source(access, trace=trace)" in lists_source


def test_reloaded_price_list_session_reattaches_to_active_extraction(monkeypatch):
    from screens import company_profile

    class SessionState(dict):
        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            self[name] = value

    future = Future()
    state = SessionState(_price_source_processing_cycle=2)
    monkeypatch.setattr(company_profile.st, "session_state", state)
    monkeypatch.setattr(
        company_profile,
        "active_price_source_job",
        lambda _company_id: SimpleNamespace(
            future=future,
            started_at=123.0,
            started_at_epoch_ms=456000,
        ),
    )

    company_profile._restore_active_price_source_processing(
        SimpleNamespace(company_id="company-1")
    )

    assert state["_price_source_processing"] is True
    assert state["_price_source_pending"]["future"] is future
    assert state["_price_source_pending"]["processing_cycle"] == 3
    assert state["_price_source_pending"]["user_cycle_started_at_epoch_ms"] == 456000


def test_price_source_processing_guard_restores_client_mutations_after_completion():
    from ui.js_guards import install_price_source_processing_guard

    source = inspect.getsource(install_price_source_processing_guard)

    assert "resetCompletedState" in source
    assert 'card.classList.remove("costerly-price-source-processing")' in source
    assert "button.disabled = true" not in source
    assert "button.disabled = false" not in source
    assert 'label.textContent = "Extract prices"' in source
    assert '".price-source-processing-marker"' in source
    assert ".price-source-processing-complete-marker" in source
    assert "card.dataset.costerlyProcessingCycle" in source
    assert "completeMarker.dataset.processingCycle" in source
    assert "completedCycle === startedCycle" in source
    assert "new MutationObserver(resetCompletedState)" in source
    assert "preventPrematureProfileNavigation" in source
    assert "releaseDeferredProfileNavigation" in source
    assert "__costerlyDeferredPriceSourceTab" in source
    assert "tab.click()" in source
    assert ".price-source-start-rejected-marker" in source
    assert "Server markers" in source
    assert "__costerlyPriceSourceStartPending" in source
    assert "3000" in source
    assert "__costerlyPriceSourceStartWatchdog" not in source
    assert "Extraction did not reach the server. Try again." not in source
    assert 'label.textContent = "Starting extraction"' in source
    assert 'showLiveProgress(card, Date.now(), "Starting extraction")' in source
    assert 'if (!card.querySelector(".price-source-live-progress"))' in source
    assert "trigger itself indefinitely and freeze the browser" in source
    assert "observer.disconnect()" in source
    assert "never the native disabled property" in source
    assert "parentWindow.setTimeout(() =>" in source
    assert 'showLiveProgress(card, Date.now(), "Starting extraction")' in source
    assert "function showLiveProgress(card, startedAtMs)" in source
    assert "function removeLiveProgress(card)" in source
    assert "clearTerminalResultForNewSelection" in source
    assert "__costerlyClearPriceSourceTerminalResult" in source
    assert 'parentDoc.querySelectorAll(".price-source-cycle-result")' in source
    assert 'card.querySelectorAll(".price-source-cycle-result")' not in source
    assert "!completeMarker && processingMarker" in source
    assert "event.stopImmediatePropagation()" in source
    assert 'card.classList.contains("costerly-price-source-processing")' in source


def test_price_source_save_guard_shows_saving_state_immediately():
    from ui.js_guards import install_price_source_save_guard

    source = inspect.getsource(install_price_source_save_guard)

    assert "costerly-price-source-saving" in source
    assert 'label.textContent = "Saving"' in source


def test_price_source_add_renders_an_explicit_server_completion_marker():
    from screens.company_profile import _render_price_source_add

    source = inspect.getsource(_render_price_source_add)

    assert "price-source-processing-complete-marker" in source
    assert 'data-processing-cycle="{processing_cycle}"' in source


def test_price_source_uploader_installs_dragover_guard():
    from screens.company_profile import _render_price_source_add
    from ui.js_guards import install_upload_dragover_guard

    source = inspect.getsource(_render_price_source_add)
    guard_source = inspect.getsource(install_upload_dragover_guard)

    assert "install_upload_dragover_guard(" in source
    assert "file_previews=file_previews" in source
    assert "install_price_source_file_selection_guard" not in source
    assert "install_price_source_file_selection_guard(" in guard_source
    assert "file_previews=file_previews" in guard_source
    assert guard_source.count("components.html(") == 1
    assert "render_price_source_preview" in source
    assert "costerly-upload-invalid-dragover" in guard_source
    assert "costerly-single-document-selection" in guard_source
    assert "event.stopImmediatePropagation()" in guard_source
    assert "if (!event.relatedTarget)" in guard_source


def test_mixed_selection_keeps_only_the_first_file():
    first = _UploadedPhoto("invoice.pdf", b"%PDF")
    selected = accepted_price_source_uploads(
        [first, _UploadedPhoto("page.png", b"png")]
    )

    assert selected == [first]
    combined = combine_price_source_files(selected)
    assert combined.name == first.name
    assert combined.getvalue() == first.getvalue()


def test_photo_led_mixed_selection_keeps_all_photo_pages_only():
    first = _UploadedPhoto("page-1.jpg", b"first")
    second = _UploadedPhoto("page-2.png", b"second")

    assert accepted_price_source_uploads(
        [first, _UploadedPhoto("prices.xlsx", b"sheet"), second]
    ) == [first, second]


def test_multiple_spreadsheets_keep_only_the_first_file():
    first = _UploadedPhoto("prices-a.xlsx", b"first")

    assert accepted_price_source_uploads(
        [first, _UploadedPhoto("prices-b.xlsx", b"second")]
    ) == [first]


def test_multiple_photos_are_valid_as_one_document_before_processing_is_queued():
    validate_price_source_upload_selection(
        [
            _UploadedPhoto("page-1.jpg", b"first"),
            _UploadedPhoto("page-2.png", b"second"),
        ]
    )


def test_multiple_tiff_and_heic_photos_are_valid_as_one_document_before_processing_is_queued():
    validate_price_source_upload_selection(
        [
            _UploadedPhoto("page-1.tiff", b"first"),
            _UploadedPhoto("page-2.heic", b"second"),
        ]
    )


def test_multiple_spreadsheets_queue_only_the_first_file(monkeypatch):
    from screens import company_profile

    class SessionState(dict):
        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            self[name] = value

    state = SessionState(
        price_upload=[
            _UploadedPhoto("prices-a.xlsx", b"first"),
            _UploadedPhoto("prices-b.xlsx", b"second"),
        ],
        price_url="",
    )
    monkeypatch.setattr(company_profile.st, "session_state", state)
    submitted = []
    monkeypatch.setattr(
        company_profile,
        "submit_price_source_job",
        lambda **kwargs: submitted.append(kwargs) or Future(),
    )

    company_profile._queue_price_source_processing(
        SimpleNamespace(company_id="company-1"), "price_upload", "price_url"
    )

    assert state["_price_source_processing"] is True
    assert submitted[0]["uploaded_file"].name == "prices-a.xlsx"
    assert isinstance(state["_price_source_pending"]["future"], Future)
    assert "_price_source_error" not in state


def test_source_removal_hides_immediately_and_finishes_in_background(monkeypatch):
    from screens import company_profile

    class SessionState(dict):
        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            self[name] = value

    state = SessionState()
    future = Future()
    monkeypatch.setattr(company_profile.st, "session_state", state)
    monkeypatch.setattr(
        company_profile,
        "submit_price_source_purge_job",
        lambda **_kwargs: future,
    )
    cleared = []
    monkeypatch.setattr(
        company_profile,
        "_clear_price_lists_snapshot",
        lambda: cleared.append(True),
    )

    company_profile._start_price_source_purge_action(
        SimpleNamespace(company_id="company-1"), "source-1"
    )

    assert state["_price_source_purging_ids"] == {"source-1"}
    assert state["_price_source_purge_pending"]["source-1"] is future

    future.set_result({"deleted_rows": 5, "storage_deleted": True})

    assert company_profile._process_pending_price_source_purges() is True
    assert cleared == [True]
    assert "_price_source_purge_pending" not in state
    assert "_price_source_action_notice" not in state
    assert state["_price_source_library_open_once"] is True


def test_optimistic_source_purge_hides_all_source_owned_projections():
    from screens import company_profile

    records = [
        {"source_id": "source-remove", "value": "hidden"},
        {"source_id": "source-keep", "value": "visible"},
    ]

    assert company_profile._without_purging_price_source_records(
        records, {"source-remove"}
    ) == [{"source_id": "source-keep", "value": "visible"}]


def test_completed_source_purge_refreshes_stale_catalog_without_discarding_selection(monkeypatch):
    """A completed background purge must replace the old rendered snapshot.

    The refresh is intentionally deferred while the uploader contains a file
    or URL, because that selection belongs to the later Extract callback.
    """
    from screens import company_profile

    class SessionState(dict):
        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            self[name] = value

    state = SessionState(_price_source_uploader_version=2)
    monkeypatch.setattr(company_profile.st, "session_state", state)
    monkeypatch.setattr(
        company_profile,
        "accepted_price_source_uploads",
        lambda files: files,
    )

    assert company_profile._price_source_has_unsubmitted_selection() is False

    state["price_source_upload_2"] = [object()]
    assert company_profile._price_source_has_unsubmitted_selection() is True

    state["price_source_upload_2"] = []
    state["price_source_url_2"] = "https://supplier.example/prices"
    assert company_profile._price_source_has_unsubmitted_selection() is True


def test_price_source_file_selection_clears_the_supplier_url(monkeypatch):
    from screens import company_profile

    state = {
        "price_upload": [_UploadedPhoto("prices.xlsx", b"first")],
        "price_url": "https://supplier.example/prices",
    }
    monkeypatch.setattr(company_profile.st, "session_state", state)

    company_profile._clear_price_source_url_for_files("price_upload", "price_url")

    assert state["price_url"] == ""


def test_price_source_selection_invalidates_the_server_terminal_result(monkeypatch):
    from screens import company_profile

    state = {
        "price_upload": [_UploadedPhoto("prices.xlsx", b"first")],
        "price_url": "https://supplier.example/prices",
        "_price_source_selection_cycle": 4,
        "_price_source_notice": {"summary": {"total": 2}},
        "_price_source_error": "old error",
    }
    monkeypatch.setattr(company_profile.st, "session_state", state)

    company_profile._clear_price_source_url_for_files("price_upload", "price_url")

    assert state["price_url"] == ""
    assert state["_price_source_selection_cycle"] == 5
    assert "_price_source_notice" not in state
    assert "_price_source_error" not in state


def test_price_source_url_entry_replaces_existing_file_selection(monkeypatch):
    from screens import company_profile

    state = {
        "_price_source_uploader_version": 4,
        "price_source_url_4": "https://supplier.example/prices",
        "price_source_upload_4": [_UploadedPhoto("prices.xlsx", b"first")],
    }
    monkeypatch.setattr(company_profile.st, "session_state", state)

    company_profile._clear_price_source_files_for_url("price_source_url_4")

    assert state["_price_source_uploader_version"] == 5
    assert state["price_source_url_5"] == "https://supplier.example/prices"
    assert "price_source_upload_5" not in state


def test_price_source_file_guard_filters_before_streamlit_receives_selection():
    from ui.js_guards import install_price_source_file_selection_guard

    source = inspect.getsource(install_price_source_file_selection_guard)

    assert "files.every(isPhoto)" in source
    assert "files.filter(isPhoto)" in source
    assert "return files.slice(0, 1)" in source
    assert "new DataTransfer()" in source
    assert 'parentDoc.addEventListener("change", handleChange, true)' in source
    assert 'parentDoc.addEventListener("drop", handleDrop, true)' in source
    assert 'parentDoc.addEventListener("click", handleClick, true)' in source
    assert "event.stopImmediatePropagation()" in source
    assert 'new DragEvent("drop"' in source
    assert "__costerlyAcceptedPriceSourceDrop" in source
    assert "Upload one PDF, XLSX or CSV at a time · JPG/PNG can be combined" in source
    assert "costerly-selection-warning" in source
    assert "renderedFiles(uploader)" in source
    assert 'stFileChipName' in source
    assert "nativeFiles.length ? nativeFiles : renderedFiles(uploader)" in source
    assert "costerly-photo-selection" in source
    assert "costerly-single-document-selection" in source
    assert "transient empty DOM" in source
    assert "stFileChipDeleteBtn" in source
    assert "emptyWarningTimer" in source
    assert "}, 5000)" in source
    assert "FILE_PREVIEWS" in source
    assert "costerly-file-preview" in source
    assert "acceptedIncomingFiles" in source
    assert "existing.every(isPhoto)" in source
    assert "if (files.length && !accepted.length)" in source
    assert "clearTerminalResultOnSelection" in source


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
                "category": "Wood Sheets",
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


def test_active_supplier_operation_offer_is_enriched_as_material_job(monkeypatch):
    tables = {
        "company_supplier_operation_offers": [{
            "operation_offer_id": "job-1", "operation_id": "operation-1",
            "supplier_id": "supplier-1", "source_id": "source-1", "source_row_id": "row-1",
            "raw_service_name": "פס חיתוך + קנט", "source_price": 17.5,
            "pricing_basis": "supplier_defined", "source_unit_label": "piece",
            "currency": "ILS", "vat_included": False, "valid_from": "2026-10-05",
        }],
        "reference_operations": [{
            "operation_id": "operation-1", "operation_code": "supplier_cut_and_edge_banding",
            "department": "Wood", "operation_name": "Cutting and edge banding",
        }],
        "company_suppliers": [{"supplier_id": "supplier-1", "supplier_name": "Wood supplier"}],
        "company_price_sources": [{
            "source_id": "source-1", "source_name": "invoice.pdf", "source_kind": "file",
            "processing_summary": {"document_subtotal": 100, "document_vat_amount": 18},
        }],
    }
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: _CatalogClient(tables))
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    rows = list_material_jobs(SimpleNamespace(company_id="company-1", user_id="user-1"))

    assert rows[0]["operation_name"] == "Cutting and edge banding"
    assert rows[0]["supplier_name"] == "Wood supplier"
    assert rows[0]["pricing_basis"] == "supplier_defined"


def test_material_jobs_show_one_supplier_defined_offer_when_unit_was_omitted(monkeypatch):
    tables = {
        "company_supplier_operation_offers": [
            {
                "operation_offer_id": "job-old", "operation_id": "operation-1",
                "supplier_id": "supplier-1", "source_id": "source-old", "source_row_id": "row-old",
                "raw_service_name": "cut and edge", "source_price": 17.5,
                "pricing_basis": "supplier_defined", "source_unit_label": "piece",
                "currency": "ILS", "vat_included": False, "valid_from": "2026-10-04",
                "created_at": "2026-10-04T10:00:00Z",
            },
            {
                "operation_offer_id": "job-new", "operation_id": "operation-1",
                "supplier_id": "supplier-1", "source_id": "source-new", "source_row_id": "row-new",
                "raw_service_name": "פס חיתוך + קנט", "source_price": 17.5,
                "pricing_basis": "supplier_defined", "source_unit_label": None,
                "currency": "ILS", "vat_included": False, "valid_from": "2026-10-05",
                "created_at": "2026-10-05T10:00:00Z",
            },
        ],
        "reference_operations": [{
            "operation_id": "operation-1", "operation_code": "supplier_cut_and_edge_banding",
            "department": "Wood", "operation_name": "Cutting and edge banding",
        }],
        "company_suppliers": [{"supplier_id": "supplier-1", "supplier_name": "Wood supplier"}],
        "company_price_sources": [
            {"source_id": "source-old", "source_name": "old.pdf", "source_kind": "file", "source_url": None,
             "processed_at": "2026-10-04T10:00:00Z", "processing_summary": {}},
            {"source_id": "source-new", "source_name": "new.jpg", "source_kind": "file", "source_url": None,
             "processed_at": "2026-10-05T10:00:00Z", "processing_summary": {}},
        ],
    }
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: _CatalogClient(tables))
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    rows = list_material_jobs(SimpleNamespace(company_id="company-1", user_id="user-1"))

    assert len(rows) == 1
    assert rows[0]["operation_offer_id"] == "job-new"


def test_unresolved_queue_excludes_rows_from_archived_sources(monkeypatch):
    tables = {
        "company_price_source_rows": [
            {
                "row_id": "row-visible",
                "source_id": "source-visible",
                "company_id": "company-1",
                "result_status": "unresolved",
            },
            {
                "row_id": "row-archived",
                "source_id": "source-archived",
                "company_id": "company-1",
                "result_status": "unresolved",
            },
        ],
        "company_price_sources": [
            {
                "source_id": "source-visible",
                "company_id": "company-1",
                "status": "partial",
                "source_name": "visible.xlsx",
            },
            {
                "source_id": "source-archived",
                "company_id": "company-1",
                "status": "archived",
                "source_name": "archived.xlsx",
            },
        ],
    }
    client = _MutableClient(tables)
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: client)
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    rows = list_unresolved_price_source_rows(
        SimpleNamespace(company_id="company-1", user_id="user-1")
    )

    assert [row["row_id"] for row in rows] == ["row-visible"]
    assert rows[0]["source"]["source_name"] == "visible.xlsx"


def test_review_activate_and_remove_row_are_auditable(monkeypatch):
    tables = {
        "company_price_sources": [
            {
                "source_id": "source-1",
                "company_id": "company-1",
                "supplier_id": "supplier-1",
                "category": "Other",
                "currency": None,
                "document_date": "2026-09-24",
                "status": "partial",
                "processing_summary": {"ready": 0, "unresolved": 1, "excluded": 0},
            }
        ],
        "company_price_source_rows": [
            {
                "row_id": "row-1",
                "source_id": "source-1",
                "company_id": "company-1",
                "raw_description": "Birch plywood 10mm",
                "raw_sku": "PLY-10",
                "confidence": 42,
                "result_status": "unresolved",
                "raw_vat_included": None,
                "reason_codes": ["vat_basis_unknown", "below_auto_activation_threshold"],
                "evidence": {"material_type": "Other"},
            }
        ],
        "company_material_items": [],
        "company_material_offers": [],
    }
    client = _MutableClient(tables)
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: client)
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)
    access = SimpleNamespace(company_id="company-1", user_id="user-1")

    saved = save_price_source_row(
        access,
        "source-1",
        "row-1",
        {
            "normalized_name": "Plywood Birch 10 mm",
            "material_type": "Wood Sheets",
            "raw_price": 100,
            "raw_currency": "ILS",
            "raw_unit": "sheet",
            "purchase_unit": "sheet",
            "calculation_unit": "m2",
            "conversion_factor": 2.5,
            "vat_mode": "excluded",
        },
    )

    assert saved["result_status"] == "new"
    assert saved["normalized_price"] == 40
    assert saved["reason_codes"] == ["reviewed_by_user"]
    assert tables["company_material_offers"][0]["status"] == "active"
    assert tables["company_price_sources"][0]["status"] == "ready"
    assert tables["company_price_sources"][0]["currency"] == "ILS"

    remove_price_source_row(access, "source-1", "row-1")

    assert tables["company_price_source_rows"][0]["result_status"] == "excluded"
    assert tables["company_material_offers"][0]["status"] == "archived"
    assert "removed_by_user" in tables["company_price_source_rows"][0]["reason_codes"]


def test_reviewed_internal_price_supersedes_only_its_recurring_internal_lane(monkeypatch):
    tables = {
        "company_price_sources": [
            {
                "source_id": "internal-current",
                "company_id": "company-1",
                "supplier_id": None,
                "currency": "ILS",
                "document_date": "2026-09-26",
                "status": "partial",
                "processing_summary": {
                    "source_origin": "company_internal",
                    "source_family_sha256": "workshop-template",
                },
            },
            {
                "source_id": "internal-previous",
                "company_id": "company-1",
                "supplier_id": None,
                "status": "ready",
                "processing_summary": {
                    "source_origin": "company_internal",
                    "source_family_sha256": "workshop-template",
                },
            },
            {
                "source_id": "supplier-source",
                "company_id": "company-1",
                "supplier_id": "supplier-1",
                "status": "ready",
                "processing_summary": {
                    "source_origin": "supplier",
                    "source_family_sha256": "supplier-family",
                },
            },
        ],
        "company_price_source_rows": [
            {
                "row_id": "row-current",
                "source_id": "internal-current",
                "company_id": "company-1",
                "raw_description": "Фанера 10 мм",
                "raw_sku": None,
                "confidence": 92,
                "result_status": "unresolved",
                "raw_vat_included": None,
                "reason_codes": ["internal_price_lane_pending", "vat_basis_unknown"],
                "evidence": {"material_type": "Wood Sheets"},
            }
        ],
        "company_material_items": [
            {
                "company_material_id": "material-1",
                "company_id": "company-1",
                "category": "Wood Sheets",
                "normalized_name": "birch plywood 10 mm",
                "canonical_name": "Birch plywood 10 mm",
                "status": "active",
            }
        ],
        "company_material_offers": [
            {
                "offer_id": "supplier-offer",
                "company_id": "company-1",
                "company_material_id": "material-1",
                "supplier_id": "supplier-1",
                "source_id": "supplier-source",
                "source_row_id": "supplier-row",
                "status": "active",
            },
            {
                "offer_id": "internal-old-offer",
                "company_id": "company-1",
                "company_material_id": "material-1",
                "supplier_id": None,
                "source_id": "internal-previous",
                "source_row_id": "internal-old-row",
                "status": "active",
            },
        ],
    }
    client = _MutableClient(tables)
    monkeypatch.setattr("use_cases.price_sources.get_supabase_client", lambda: client)
    monkeypatch.setattr("use_cases.price_sources.assert_company_owner", lambda *_args: None)

    saved = save_price_source_row(
        SimpleNamespace(company_id="company-1", user_id="user-1"),
        "internal-current",
        "row-current",
        {
            "normalized_name": "Birch plywood 10 mm",
            "material_type": "Wood Sheets",
            "raw_price": 80,
            "raw_currency": "ILS",
            "raw_unit": "sheet",
            "purchase_unit": "sheet",
            "calculation_unit": "sheet",
            "conversion_factor": 1,
            "vat_mode": "excluded",
        },
    )

    offers = {offer["offer_id"]: offer for offer in tables["company_material_offers"]}
    assert saved["result_status"] == "updated"
    assert offers["supplier-offer"]["status"] == "active"
    assert offers["internal-old-offer"]["status"] == "superseded"
    assert offers["generated-3"]["status"] == "active"
    assert offers["generated-3"]["supplier_id"] is None
    assert saved["reason_codes"] == ["reviewed_by_user"]

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


def test_line_total_never_derives_a_more_precise_unit_price():
    result = _result()
    row = result["rows"][0]
    row.update(
        raw_price=20,
        raw_quantity=20,
        raw_line_total=52.5,
        normalized_price=20 / 2.9768,
        reason_codes=["line_total_inconsistent", "unit_price_mismatch"],
    )

    reconciled = reconcile_price_source_arithmetic(result)

    assert row["status"] == "unresolved"
    assert row["raw_price"] == 20
    assert "line_total_inconsistent" in row["reason_codes"]
    assert "unit_price_derived_from_line_total" not in row["reason_codes"]
    assert reconciled is result


def test_ready_line_with_unproven_total_arithmetic_goes_to_review():
    result = _result()
    row = result["rows"][0]
    row.update(raw_price=5, raw_quantity=57.5, raw_line_total=137.5)

    reconciled = reconcile_price_source_arithmetic(result)

    assert row["status"] == "unresolved"
    assert "line_total_inconsistent" in row["reason_codes"]


def test_two_decimal_price_with_hidden_thousandth_is_not_sent_to_review():
    result = _result()
    row = result["rows"][0]
    row.update(
        raw_price=2.63,
        raw_quantity=30,
        raw_line_total=78.75,
        status="unresolved",
        reason_codes=["arithmetic_mismatch"],
    )

    _mark_unverified_source_table_rows_for_review(
        result,
        [{"source_row_number": row["source_row_number"]}],
    )

    assert row["status"] == "unresolved"
    assert "source_table_price_not_verified" not in row["reason_codes"]
    assert "source_table_price_rounding_tolerated" in row["reason_codes"]
    assert "arithmetic_mismatch" not in row["reason_codes"]


def test_large_arithmetic_difference_is_not_hidden_by_rounding_tolerance():
    result = _result()
    row = result["rows"][0]
    row.update(raw_price=2.63, raw_quantity=30, raw_line_total=77.5)

    _mark_unverified_source_table_rows_for_review(
        result,
        [{"source_row_number": row["source_row_number"]}],
    )

    assert row["status"] == "unresolved"
    assert "source_table_price_not_verified" in row["reason_codes"]


def test_fractional_hardware_piece_requires_a_second_read_or_review():
    result = _result()
    row = result["rows"][0]
    row.update(
        material_type="Hardware",
        raw_unit="piece",
        raw_price=5,
        raw_quantity=57.5,
        raw_line_total=287.5,
    )

    conflicts = _line_arithmetic_conflicts(result)
    _mark_unrepaired_fractional_hardware_for_review(result, conflicts)

    assert conflicts[0]["recheck_reason"] == "fractional_hardware_piece_quantity"
    assert row["status"] == "unresolved"
    assert "fractional_hardware_piece_quantity" in row["reason_codes"]


def test_arithmetic_recheck_repairs_only_a_consistent_second_reading():
    result = _result(status="unresolved")
    row = result["rows"][0]
    row.update(raw_price=20, raw_quantity=20, raw_line_total=52.5)

    conflicts = _line_arithmetic_conflicts(result)
    repaired = _merge_arithmetic_recheck(
        result,
        [{
            "source_row_number": 1,
            "raw_quantity": 20,
            "raw_price": 2.63,
            "raw_line_total": 52.6,
        }],
    )

    assert conflicts[0]["source_row_number"] == 1
    assert repaired == 1
    assert row["status"] == "ready"
    assert row["raw_price"] == pytest.approx(2.63)
    assert row["raw_line_total"] == pytest.approx(52.6)
    assert "unit_price_rechecked_from_source" in row["reason_codes"]


def test_arithmetic_recheck_preserves_printed_total_when_price_and_quantity_match():
    result = _result()
    row = result["rows"][0]
    row.update(raw_price=2.63, raw_quantity=20, raw_line_total=52.5)

    repaired = _merge_arithmetic_recheck(
        result,
        [{
            "source_row_number": 1,
            "raw_quantity": 20,
            "raw_price": 2.63,
            "raw_line_total": 52.6,
        }],
    )

    assert repaired == 1
    assert row["raw_price"] == pytest.approx(2.63)
    assert row["raw_line_total"] == pytest.approx(52.5)


def test_arithmetic_recheck_rejects_another_inconsistent_numeric_triple():
    result = _result(status="unresolved")
    row = result["rows"][0]
    row.update(raw_price=20, raw_quantity=20, raw_line_total=52.5)

    repaired = _merge_arithmetic_recheck(
        result,
        [{
            "source_row_number": 1,
            "raw_quantity": 20,
            "raw_price": 3,
            "raw_line_total": 52.5,
        }],
    )

    assert repaired == 0
    assert row["raw_price"] == 20
    assert row["status"] == "unresolved"


def test_prompt_preserves_item_vat_basis_and_excludes_document_totals():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()
    assert "subtotal, VAT or tax total, grand total, and amount due" in prompt
    assert "Never add\n  or remove VAT from a product price" in prompt


def test_prompt_requires_line_level_price_arithmetic_before_extraction():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()

    assert "quantity × unit price = line total" in prompt
    assert "line total ÷ quantity" in prompt
    assert "never infer their meaning from visual column position alone" in prompt


def test_prompt_requires_consistent_standalone_normalized_names():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()

    assert "entity, its primary attribute, brand, then" in prompt
    assert "same term and\n   capitalization" in prompt
    assert "when viewed outside the source document" in prompt


def test_prompt_accepts_documents_addressed_to_another_company():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()
    assert "may be a different\n   company from the current user" in prompt
    assert "must never\n   cause rejection, exclusion, or reduced confidence" in prompt


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


def test_internal_estimate_is_a_first_class_source_without_a_supplier():
    internal = _result()
    internal.update(
        {
            "supplier_name": "",
            "source_origin": "company_internal",
            "document_type": "internal_estimate",
            "price_context": "internal_cost_estimate",
        }
    )

    guarded = guard_price_source_row_activation(internal)

    assert guarded["rows"][0]["status"] == "ready"
    assert "internal_price_lane_pending" not in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


def test_internal_source_defaults_resolve_vat_currency_and_zero_quantity():
    row = {
        "raw_description": "Plywood 12 mm",
        "raw_price": 220,
        "raw_currency": None,
        "raw_unit": "sheet",
        "raw_vat_included": None,
        "normalized_name": "Plywood 12 mm",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": 1,
        "result_status": "unresolved",
        "reason_codes": [
            "unknown_currency",
            "unknown_vat",
            "zero_quantity",
            "below_auto_activation_threshold",
        ],
        "evidence": {"material_type": "Wood Sheets"},
    }

    prepared = prepare_internal_estimate_row_defaults(
        row,
        currency="ILS",
        vat_mode="excluded",
    )

    assert prepared["result_status"] == "ready"
    assert prepared["raw_currency"] == "ILS"
    assert prepared["raw_vat_included"] is False
    assert prepared["reason_codes"] == []
    assert prepared["normalized_price"] == 220


def test_internal_source_defaults_keep_missing_unit_in_review():
    row = {
        "raw_description": "Drawer handle",
        "raw_price": 60,
        "raw_currency": None,
        "raw_unit": None,
        "raw_vat_included": None,
        "normalized_name": "Drawer handle",
        "purchase_unit": "unknown",
        "calculation_unit": "unknown",
        "conversion_factor": 0,
        "result_status": "unresolved",
        "reason_codes": ["missing_unit", "unknown_vat", "zero_quantity"],
        "evidence": {"material_type": "Metal Supplies"},
    }

    prepared = prepare_internal_estimate_row_defaults(
        row,
        currency="ILS",
        vat_mode="included",
    )

    assert prepared["result_status"] == "unresolved"
    assert prepared["reason_codes"] == ["missing_unit"]


def test_internal_source_defaults_exclude_non_material_costs():
    row = {
        "raw_description": "Assembly labor",
        "raw_price": 350,
        "result_status": "unresolved",
        "reason_codes": ["unknown_vat"],
    }

    prepared = prepare_internal_estimate_row_defaults(
        row,
        currency="ILS",
        vat_mode="excluded",
    )

    assert prepared["result_status"] == "excluded"
    assert "internal_non_material_cost" in prepared["reason_codes"]


def test_customer_sale_price_is_deterministically_excluded_from_material_costs():
    customer_quote = _result()
    customer_quote.update(
        {
            "supplier_name": "",
            "source_origin": "company_internal",
            "document_type": "customer_quote",
            "price_context": "customer_sale",
        }
    )

    guarded = guard_price_source_row_activation(customer_quote)

    assert guarded["rows"][0]["status"] == "excluded"
    assert "customer_sale_not_material_cost" in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


def test_prompt_separates_internal_cost_from_customer_sale_price():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()

    assert "company's own estimating workbook" in prompt
    assert "Never create a supplier from the company name" in prompt
    assert "internal_cost_estimate" in prompt
    assert "customer_sale" in prompt
    assert "must never become\n  active material costs" in prompt


def test_prompt_keeps_internal_reference_price_when_quantity_is_zero():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()

    assert "does not invalidate a separate,\n  positive unit cost" in prompt
    assert "do not mark that price unresolved only because quantity is zero" in prompt
    assert "Exclude those non-material costs even when they contain a" in prompt


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


def test_script_only_wordpress_page_uses_same_host_json_alternate(monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {
            "content-type": "text/html",
            "link": '<https://example.com/wp-json/wp/v2/pages/269>; rel="alternate"; type="application/json"',
        }
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class JsonResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"content":{"rendered":"<table><tr><td>MDF 18 mm</td><td>210 ILS</td></tr></table>"}}'
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {
                "content": {
                    "rendered": "<table><tr><td>MDF 18 mm</td><td>210 ILS</td></tr></table>"
                }
            }

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            assert follow_redirects is False
            return JsonResponse() if "/wp-json/" in url else HtmlResponse()

    monkeypatch.setattr(
        "use_cases.price_sources._validate_public_url",
        lambda value: value,
    )

    resolved_url, source_bytes, text = fetch_public_page(
        "https://example.com/prices", client=Client()
    )

    assert resolved_url == "https://example.com/prices"
    assert source_bytes == JsonResponse.content
    assert "MDF 18 mm" in text


def test_wordpress_exact_json_endpoint_is_tried_before_slug_fallback(monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {
            "content-type": "text/html",
            "link": '<https://example.com/wp-json/wp/v2/pages/269>; rel="alternate"; type="application/json"',
        }
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class JsonResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"content":{"rendered":"<p>MDF 18 mm 210 ILS</p>"}}'
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"content": {"rendered": "<p>MDF 18 mm 210 ILS</p>"}}

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            assert follow_redirects is False
            if "?slug=" in url:
                raise AssertionError("slug fallback must not run before the exact endpoint")
            return JsonResponse() if "/wp-json/" in url else HtmlResponse()

    monkeypatch.setattr("use_cases.price_sources._validate_public_url", lambda value: value)

    _, _, text = fetch_public_page("https://example.com/prices", client=Client())

    assert "MDF 18 mm" in text


def test_wordpress_page_retries_accepted_response_before_rest_fallback(monkeypatch):
    class AcceptedResponse:
        status_code = 202
        headers = {"content-type": "text/html"}
        content = b"<html>pending</html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class ReadyResponse:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><p>MDF 18 mm 210 ILS</p></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    calls = {"page": 0}

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            assert follow_redirects is False
            calls["page"] += 1
            return AcceptedResponse() if calls["page"] == 1 else ReadyResponse()

    monkeypatch.setattr("use_cases.price_sources._validate_public_url", lambda value: value)
    monkeypatch.setattr("use_cases.price_sources.time.sleep", lambda _seconds: None)

    _, _, text = fetch_public_page("https://example.com/prices", client=Client())

    assert calls["page"] == 2
    assert "MDF 18 mm" in text


def test_script_only_wordpress_page_can_discover_json_by_slug(monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class JsonResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b"[]"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return [{"content": {"rendered": "<p>Birch plywood 18 mm 310 ILS</p>"}}]

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            assert follow_redirects is False
            if "/wp-json/wp/v2/pages?slug=materials-and-prices" in url:
                return JsonResponse()
            return HtmlResponse()

    monkeypatch.setattr(
        "use_cases.price_sources._validate_public_url",
        lambda value: value,
    )

    _, _, text = fetch_public_page(
        "https://example.com/materials-and-prices/", client=Client()
    )

    assert "Birch plywood 18 mm" in text


def test_script_only_wordpress_page_can_use_query_route_when_pretty_path_is_accepted(monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class AcceptedResponse:
        status_code = 202
        headers = {"content-type": "application/json"}
        content = b"{}"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class JsonResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"content":{"rendered":"<p>Birch plywood 18 mm 310 ILS</p>"}}'
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"content": {"rendered": "<p>Birch plywood 18 mm 310 ILS</p>"}}

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            assert follow_redirects is False
            if "rest_route=" in url:
                return JsonResponse()
            if "/wp-json/" in url:
                return AcceptedResponse()
            return HtmlResponse()

    monkeypatch.setattr("use_cases.price_sources._validate_public_url", lambda value: value)
    monkeypatch.setattr("use_cases.price_sources.time.sleep", lambda _seconds: None)

    _, _, text = fetch_public_page("https://example.com/materials-and-prices/", client=Client())

    assert "Birch plywood 18 mm" in text


def test_wordpress_json_alternate_retries_bounded_accepted_responses(monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><script>renderPrices()</script></html>"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class AcceptedResponse:
        status_code = 202
        headers = {"content-type": "application/json"}
        content = b"{}"
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

    class ReadyResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"content":{"rendered":"<p>MDF 18 mm 210 ILS</p>"}}'
        text = content.decode()

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"content": {"rendered": "<p>MDF 18 mm 210 ILS</p>"}}

    calls = {"alternate": 0}

    class Client:
        @staticmethod
        def get(url, *, follow_redirects=False):
            if "/wp-json/" not in url:
                return HtmlResponse()
            calls["alternate"] += 1
            return AcceptedResponse() if calls["alternate"] <= 3 else ReadyResponse()

    monkeypatch.setattr("use_cases.price_sources._validate_public_url", lambda value: value)
    monkeypatch.setattr("use_cases.price_sources.time.sleep", lambda _seconds: None)

    _, _, text = fetch_public_page("https://example.com/materials-and-prices/", client=Client())

    assert calls["alternate"] == 4
    assert "MDF 18 mm" in text


def test_price_source_processing_collects_completed_future_from_status_fragment():
    from screens.company_profile import (
        _process_pending_price_source,
        _render_price_source_processing_status,
    )

    source = inspect.getsource(_process_pending_price_source)
    status_source = inspect.getsource(_render_price_source_processing_status)

    assert "future.done()" in source
    assert "future.result()" in source
    assert "run_every=1.0" in status_source
    assert "st.rerun(scope=\"app\")" in status_source


def test_price_source_agent_disables_sdk_retries_for_background_cycles():
    source = Path("agents/price_source_agent.py").read_text()

    assert "with_options(timeout=45.0, max_retries=0)" in source
    assert "max_stream_seconds=60.0" in source


def test_price_source_arithmetic_recheck_uses_runtime_trace_metadata_contract():
    source = Path("agents/price_source_agent.py").read_text()

    assert 'metadata={"conflict_rows": len(recheck_candidates)}' in source
    assert 'status="error"' in source
    assert '"repaired_rows": repaired_count' in source
    assert "require_source_table_verification" in source
    assert "_source_table_recheck_rows(result)" in source


def test_price_source_summary_aggregates_primary_and_table_verifier_timing():
    source = Path("use_cases/price_sources.py").read_text()

    assert "total_agent_duration = sum(" in source
    assert '"agent_duration_seconds": total_agent_duration or None' in source
    assert "primary_usage = next(" in source


def test_known_supplier_vat_basis_resolves_a_partial_document_without_review_blocker():
    from use_cases.price_sources import apply_known_supplier_vat_basis

    result = {
        "document_type": "delivery_note",
        "vat_mode": "unknown",
        "rows": [{
            "raw_vat_mode": "unknown",
            "status": "unresolved",
            "reason_codes": ["vat_basis_unknown", "unknown_vat"],
        }],
    }

    assert apply_known_supplier_vat_basis(result, vat_mode="excluded") == "inferred_supplier_history"
    assert result["vat_mode"] == "excluded"
    assert result["rows"][0]["raw_vat_mode"] == "excluded"
    assert result["rows"][0]["status"] == "ready"
    assert "vat_basis_unknown" not in result["rows"][0]["reason_codes"]


def test_known_supplier_vat_basis_does_not_override_current_document_evidence():
    from use_cases.price_sources import apply_known_supplier_vat_basis

    result = {"vat_mode": "included", "rows": []}

    assert apply_known_supplier_vat_basis(result, vat_mode="excluded") == "explicit"
    assert result["vat_mode"] == "included"


def test_supplier_legal_identifier_marks_osek_murshe_as_vat_excluded():
    from use_cases.price_sources import supplier_legal_identifier_vat_basis

    assert supplier_legal_identifier_vat_basis(
        "א.ש. פירזול בע\"מ ע.מ. 513453233\nלכבוד: לב קגלס 337791438",
        supplier_hp="513453233",
    ) == "excluded"


def test_supplier_vat_default_activates_unknown_rows_without_supplier_history():
    from use_cases.price_sources import apply_supplier_vat_default

    result = {
        "source_origin": "supplier",
        "vat_mode": "unknown",
        "rows": [{
            "raw_vat_mode": "unknown",
            "status": "unresolved",
            "reason_codes": ["vat_basis_unknown"],
        }],
    }

    assert apply_supplier_vat_default(result) == "inferred_supplier_default"
    assert result["vat_mode"] == "excluded"
    assert result["rows"][0]["raw_vat_mode"] == "excluded"
    assert result["rows"][0]["status"] == "ready"
    assert result["rows"][0]["reason_codes"] == ["vat_inferred_supplier_default"]


def test_partial_invoice_uses_statutory_vat_rate_for_its_document_date():
    assert price_source_vat_rate(document_date="2024-12-31") == (0.17, "document_date")
    assert price_source_vat_rate(document_date="2025-01-01") == (0.18, "document_date")
    assert price_source_vat_rate(document_date="") == (0.18, "current_default")


def test_document_totals_override_statutory_vat_rate():
    assert price_source_vat_rate(
        document_date="2026-10-08",
        document_subtotal=100,
        document_vat_amount=17,
    ) == (0.17, "document_totals")


def test_canonical_supplier_resolution_releases_only_stale_supplier_review_rows():
    from use_cases.price_sources import resolve_rows_after_supplier_identity

    result = {
        "currency": "ILS",
        "rows": [
            {
                "item_kind": "material",
                "raw_price": 79,
                "normalized_price": 79,
                "raw_currency": "ILS",
                "raw_vat_mode": "excluded",
                "purchase_unit": "set",
                "calculation_unit": "set",
                "conversion_factor": 1,
                "normalized_name": "Drawer runner Blum",
                "status": "unresolved",
                "reason_codes": [
                    "missing_supplier_evidence", "unknown_vat_mode",
                    "taxonomy_hardware",
                    "vat_inferred_from_supplier_history",
                ],
            },
            {
                "item_kind": "material",
                "raw_price": 2.63,
                "normalized_price": 2.63,
                "raw_currency": "ILS",
                "raw_vat_mode": "excluded",
                "purchase_unit": "piece",
                "calculation_unit": "piece",
                "conversion_factor": 1,
                "normalized_name": "Mounting plate",
                "status": "unresolved",
                "reason_codes": ["supplier_unidentified", "source_table_price_not_verified"],
            },
            {
                "item_kind": "material",
                "raw_price": 2.63,
                "normalized_price": 2.63,
                "raw_currency": "ILS",
                "raw_vat_mode": "excluded",
                "purchase_unit": "piece",
                "calculation_unit": "piece",
                "conversion_factor": 1,
                "normalized_name": "Mounting plate Blum",
                "status": "unresolved",
                "reason_codes": [
                    "source_table_price_rounding_tolerated",
                    "vat_inferred_from_supplier_history",
                ],
            },
        ],
    }

    assert resolve_rows_after_supplier_identity(result) == 2
    assert result["rows"][0]["status"] == "ready"
    assert "missing_supplier_evidence" not in result["rows"][0]["reason_codes"]
    assert "unknown_vat_mode" not in result["rows"][0]["reason_codes"]
    assert result["rows"][1]["status"] == "unresolved"
    assert "supplier_unidentified" not in result["rows"][1]["reason_codes"]
    assert result["rows"][2]["status"] == "ready"


def test_invoice_source_identity_requires_supplier_and_invoice_number():
    from use_cases.price_sources import invoice_number_from_source_text, normalize_invoice_number

    assert normalize_invoice_number("Invoice 62-336") == "invoice62336"
    assert normalize_invoice_number("") == ""
    assert invoice_number_from_source_text("חשבונית מס: 62336") == "62336"
    assert invoice_number_from_source_text("Tax Invoice No. 62336") == "62336"


def test_price_source_arithmetic_recheck_prefers_original_visual_evidence():
    source = Path("agents/price_source_agent.py").read_text()
    processing_source = Path("use_cases/price_sources.py").read_text()

    assert "source_bytes: bytes | None" in source
    assert "source_evidence_bytes: bytes | None" in source
    assert "source_evidence_name: str | None" in source
    assert "The original visible table is authoritative" in source
    assert "build_uploaded_file_content_block(source_name, source_bytes)" in source
    assert "Never derive a price by dividing a total by quantity" in source
    assert "source_evidence_bytes=text_layer.arithmetic_evidence_bytes or source_bytes" in processing_source
    assert 'require_source_table_verification=text_layer.strategy == "image_ocr"' in processing_source


def test_price_source_runtime_marks_worker_boundaries(monkeypatch):
    from use_cases import price_source_runtime

    class Trace:
        def __init__(self):
            self.events = []

        def event(self, name, **kwargs):
            self.events.append((name, kwargs))

    trace = Trace()
    monkeypatch.setattr(price_source_runtime, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        price_source_runtime,
        "process_price_source",
        lambda _access, **_kwargs: "completed",
    )

    result = price_source_runtime._run_price_source_job(
        access=SimpleNamespace(company_id="diagnostic-company"),
        uploaded_file=SimpleNamespace(),
        source_url="",
        trace=trace,
        job_id="job-diagnostic",
    )

    assert result == "completed"
    assert [name for name, _kwargs in trace.events] == [
        "server.price_source_worker_started",
        "server.price_source_lock_acquired",
        "server.price_source_worker_finished",
    ]


def test_price_source_submission_queues_without_request_thread_network_io(monkeypatch):
    from use_cases import price_source_runtime

    class Executor:
        def __init__(self):
            self.kwargs = None

        def submit(self, _fn, **kwargs):
            self.kwargs = kwargs
            return Future()

    executor = Executor()
    monkeypatch.setattr(price_source_runtime, "_PRICE_SOURCE_EXECUTOR", executor)

    future = price_source_runtime.submit_price_source_job(
        access=SimpleNamespace(company_id="company-1", user_id="owner-1"),
        uploaded_file=SimpleNamespace(),
        source_url="",
    )

    assert isinstance(future, Future)
    assert executor.kwargs["owner_authorized"] is False


def test_price_source_failure_message_keeps_actionable_exception_detail_bounded():
    from screens.company_profile import _price_source_failure_message

    message = _price_source_failure_message(RuntimeError("upstream request failed"))

    assert message == "Price extraction failed (RuntimeError): upstream request failed"
    assert len(_price_source_failure_message(RuntimeError("x" * 400))) <= 330


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
