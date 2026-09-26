from __future__ import annotations

from io import BytesIO
from copy import deepcopy
import inspect
from pathlib import Path
from types import SimpleNamespace
import fitz
import pandas as pd
import pytest
from PIL import Image

from agents.schemas.price_source_schema import (
    PriceSourceSchemaError,
    guard_price_source_document_totals,
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
    _find_previous_source_revision,
    _unchanged_duplicate_summary,
    _validate_department,
    _validate_public_url,
    apply_legacy_price_benchmark,
    accepted_price_source_uploads,
    canonical_price_source_category,
    combine_price_source_files,
    create_price_source_download_url,
    extract_spreadsheet_text,
    fetch_public_page,
    guard_price_source_department,
    list_price_catalog,
    list_unresolved_price_source_rows,
    price_source_material_types,
    price_source_family_identity,
    price_source_semantic_fingerprint,
    price_offer_matches_row,
    remove_price_source_row,
    save_price_source_row,
    validate_price_source_upload_selection,
)


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

    def order(self, *_args, **_kwargs):
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
        return True

    def execute(self):
        rows = self.client.tables[self.table_name]
        if self.operation == "insert":
            inserted = deepcopy(self.payload)
            id_fields = {
                "company_material_items": "company_material_id",
                "company_material_offers": "offer_id",
            }
            id_field = id_fields.get(self.table_name)
            if id_field and id_field not in inserted:
                inserted[id_field] = f"generated-{len(rows) + 1}"
            inserted.setdefault("status", "active" if self.table_name == "company_material_offers" else "private")
            rows.append(inserted)
            return SimpleNamespace(data=[deepcopy(inserted)])
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
                "material_type": "Wood Sheets",
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


def test_unknown_vat_basis_cannot_activate():
    result = _result(confidence=95)
    result["rows"][0]["raw_vat_mode"] = "unknown"

    guarded = guard_price_source_row_activation(result)

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "vat_basis_unknown" in guarded["rows"][0]["reason_codes"]


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


def test_selected_department_mismatch_becomes_unresolved():
    result = _result()
    result["rows"][0]["material_type"] = "Metal Sheets"

    guarded = guard_price_source_department(result, "Wood")

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "selected_department_mismatch" in guarded["rows"][0]["reason_codes"]


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


def test_department_can_be_left_for_automatic_detection():
    assert _validate_department("") == ""


def test_price_source_output_budget_supports_large_supplier_pages():
    assert PRICE_SOURCE_MAX_OUTPUT_TOKENS >= 32_768


def test_price_catalog_uses_three_stable_user_facing_departments():
    assert PRICE_CATALOG_DEPARTMENTS["Wood Sheets"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Wood Supplies"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Other"] == "Wood"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Sheets"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Profiles"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Metal Supplies"] == "Metal"
    assert PRICE_CATALOG_DEPARTMENTS["Paints & Coatings"] == "Finishing"
    assert PRICE_CATALOG_DEPARTMENTS["Coating Supplies"] == "Finishing"


def test_legacy_material_types_are_canonicalized_without_splitting_filters():
    assert canonical_price_source_category("Sheet Materials") == "Wood Sheets"
    assert canonical_price_source_category("Hardware") == "Wood Supplies"
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


def test_price_source_processing_guard_restores_client_mutations_after_completion():
    from ui.js_guards import install_price_source_processing_guard

    source = inspect.getsource(install_price_source_processing_guard)

    assert "resetCompletedState" in source
    assert 'card.classList.remove("costerly-price-source-processing")' in source
    assert "button.disabled = false" in source
    assert 'label.textContent = "Extract prices"' in source
    assert '".price-source-processing-marker"' in source
    assert ".price-source-processing-complete-marker" in source
    assert "card.dataset.costerlyProcessingCycle" in source
    assert "completeMarker.dataset.processingCycle" in source
    assert "completedCycle === startedCycle" in source
    assert "new MutationObserver(resetCompletedState)" in source
    assert "observer.disconnect()" in source


def test_price_source_add_renders_an_explicit_server_completion_marker():
    from screens.company_profile import _render_price_source_add

    source = inspect.getsource(_render_price_source_add)

    assert "price-source-processing-complete-marker" in source
    assert 'data-processing-cycle="{processing_cycle}"' in source


def test_price_source_uploader_installs_dragover_guard():
    from screens.company_profile import _render_price_source_add

    source = inspect.getsource(_render_price_source_add)

    assert "install_upload_dragover_guard()" in source
    assert "install_price_source_file_selection_guard()" in source


def test_mixed_selection_keeps_only_the_first_file():
    first = _UploadedPhoto("invoice.pdf", b"%PDF")
    selected = accepted_price_source_uploads(
        [first, _UploadedPhoto("page.png", b"png")]
    )

    assert selected == [first]
    assert combine_price_source_files(selected) is first


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

    company_profile._queue_price_source_processing("price_upload", "price_url")

    assert state["_price_source_processing"] is True
    assert [item.name for item in state["_price_source_pending"]["uploaded_files"]] == [
        "prices-a.xlsx"
    ]
    assert "_price_source_error" not in state


def test_price_source_file_guard_filters_before_streamlit_receives_selection():
    from ui.js_guards import install_price_source_file_selection_guard

    source = inspect.getsource(install_price_source_file_selection_guard)

    assert "files.every(isPhoto)" in source
    assert "files.filter(isPhoto)" in source
    assert "return files.slice(0, 1)" in source
    assert "new DataTransfer()" in source
    assert 'parentDoc.addEventListener("change", handleChange, true)' in source
    assert 'parentDoc.addEventListener("drop", handleDrop, true)' in source
    assert "event.stopImmediatePropagation()" in source
    assert 'new DragEvent("drop"' in source
    assert "__costerlyAcceptedPriceSourceDrop" in source
    assert "Upload one PDF, XLSX or CSV at a time · JPG/PNG can be combined" in source
    assert "costerly-price-source-selection-note" in source
    assert "costerly-photo-selection" in source
    assert "costerly-single-document-selection" in source


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


def test_prompt_requires_consistent_standalone_normalized_names():
    prompt = Path("agents/prompts/price_source_agent_prompt.md").read_text()

    assert "product family, material or subtype, dimensions or" in prompt
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

    assert guarded["rows"][0]["status"] == "unresolved"
    assert "internal_price_lane_pending" in guarded["rows"][0]["reason_codes"]
    assert validate_price_source_result(guarded) is guarded


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
