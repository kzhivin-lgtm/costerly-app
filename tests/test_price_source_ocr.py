from io import BytesIO

import fitz
from PIL import Image

from use_cases.price_source_ocr import (
    PriceSourceTextLayer,
    ocr_issuer_evidence_text,
    ocr_package_text,
    prepare_price_source_text_layer,
    render_price_source_table_evidence,
)
from use_cases.price_sources import (
    CombinedPriceSource,
    issuer_identity_from_source_text,
    route_price_source_pdf_bundle,
)


def _ocr_package(markdown: str) -> dict:
    return {
        "contract_version": "ocr_v2",
        "model": "mistral-ocr-latest",
        "processing_seconds": 0.4,
        "pages": [{"page_number": 1, "markdown": markdown}],
    }


def _image_bytes(fmt: str = "JPEG") -> bytes:
    output = BytesIO()
    Image.new("RGB", (64, 48), "white").save(output, format=fmt)
    return output.getvalue()


def test_structured_table_bypasses_ocr():
    result = prepare_price_source_text_layer(
        file_name="prices.csv",
        file_bytes=b"name,price\nplywood,100\n",
        structured_text="name | price\nplywood | 100",
        image_ocr=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected OCR")),
        pdf_ocr=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected OCR")),
    )

    assert result.strategy == "structured_table"
    assert result.text == "name | price\nplywood | 100"
    assert result.ocr_package is None


def test_digital_pdf_keeps_embedded_text_and_always_ocrs_issuer_header():
    document = fitz.open()
    page = document.new_page()
    for line in range(12):
        page.insert_text((72, 72 + line * 18), f"Digital supplier invoice line {line} with price evidence")
    pdf_bytes = document.tobytes()
    document.close()

    package = {
        "pages": [
            {
                "page_number": 1,
                "markdown": "# Invoice\nלכבוד: Buyer",
                "blocks": [
                    {"type": "header", "content": 'לבידי בוקטוס בע"מ\nח.פ. 514539998'},
                ],
            }
        ],
    }
    calls = []
    result = prepare_price_source_text_layer(
        file_name="invoice.pdf",
        file_bytes=pdf_bytes,
        image_ocr=lambda **kwargs: calls.append(kwargs) or package,
        pdf_ocr=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected full-PDF OCR")),
    )

    assert result.strategy == "pdf_embedded_text_with_header_ocr"
    assert "Digital supplier invoice" in result.text
    assert calls[0]["file_name"] == "invoice-issuer-header.png"
    assert calls[0]["profile"] == "evidence"
    assert calls[0]["file_bytes"].startswith(b"\x89PNG")
    assert result.ocr_package["pages"] == package["pages"]
    assert result.ocr_package["source_file_name"] == "invoice.pdf"
    assert result.ocr_package["source_region"] == "first_page_issuer_header"
    assert issuer_identity_from_source_text(result.issuer_evidence_text) == {
        "supplier_name": "לבידי בוקטוס",
        "supplier_hp": "514539998",
    }


def test_scanned_pdf_uses_ocr_when_no_text_layer():
    document = fitz.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=_image_bytes())
    pdf_bytes = document.tobytes()
    document.close()
    called = []

    result = prepare_price_source_text_layer(
        file_name="scan.pdf",
        file_bytes=pdf_bytes,
        pdf_ocr=lambda **kwargs: called.append(kwargs) or _ocr_package("Invoice row"),
    )

    assert result.strategy == "pdf_ocr"
    assert result.text == "PAGE 1:\nInvoice row"
    assert called[0]["file_name"] == "scan.pdf"


def _bundle_pdf(*pages: str) -> bytes:
    document = fitz.open()
    for page_text in pages:
        page = document.new_page()
        for line_number, line in enumerate(page_text.splitlines(), start=1):
            page.insert_text((72, 72 + line_number * 18), line)
    result = document.tobytes()
    document.close()
    return result


def test_multi_invoice_pdf_router_splits_only_proven_distinct_issuer_invoice_pairs(monkeypatch):
    import use_cases.price_sources as price_sources

    pdf_bytes = _bundle_pdf(
        "Alpha Ltd\nH.P. 514539998\nTax Invoice No: AL-100",
        "Beta Ltd\nH.P. 513452333\nTax Invoice No: BE-200",
    )
    monkeypatch.setattr(
        price_sources,
        "prepare_price_source_text_layer",
        lambda **_kwargs: PriceSourceTextLayer(text="unused", strategy="pdf_embedded_text_with_header_ocr"),
    )

    routed = route_price_source_pdf_bundle(
        CombinedPriceSource(name="scanned-bundle.pdf", data=pdf_bytes)
    )

    assert [item.uploaded_file.name for item in routed] == [
        "scanned-bundle-page-001.pdf",
        "scanned-bundle-page-002.pdf",
    ]
    assert [item.bundle_page_number for item in routed] == [1, 2]
    assert all(item.bundle_page_count == 2 for item in routed)


def test_multi_page_single_invoice_pdf_router_preserves_the_existing_fast_path(monkeypatch):
    import use_cases.price_sources as price_sources

    pdf_bytes = _bundle_pdf(
        "Alpha Ltd\nH.P. 514539998\nTax Invoice No: AL-100",
        "Alpha Ltd\nH.P. 514539998\nTax Invoice No: AL-100",
    )
    text_layer = PriceSourceTextLayer(text="full document", strategy="pdf_embedded_text_with_header_ocr")
    monkeypatch.setattr(price_sources, "prepare_price_source_text_layer", lambda **_kwargs: text_layer)

    routed = route_price_source_pdf_bundle(
        CombinedPriceSource(name="one-invoice.pdf", data=pdf_bytes)
    )

    assert len(routed) == 1
    assert routed[0].uploaded_file.name == "one-invoice.pdf"
    assert routed[0].text_layer is text_layer


def test_scanned_multi_invoice_pdf_router_reuses_its_per_page_ocr_evidence(monkeypatch):
    import use_cases.price_sources as price_sources

    pdf_bytes = _bundle_pdf("scanned page", "another scanned page")
    text_layer = PriceSourceTextLayer(
        text="full scan",
        strategy="pdf_ocr",
        ocr_package={
            "processing_seconds": 2.0,
            "pages": [
                {
                    "page_number": 1,
                    "markdown": "Tax Invoice No: AL-100",
                    "blocks": [{"type": "header", "content": "Alpha Ltd\nH.P. 514539998"}],
                },
                {
                    "page_number": 2,
                    "markdown": "Tax Invoice No: BE-200",
                    "blocks": [{"type": "header", "content": "Beta Ltd\nH.P. 513452333"}],
                },
            ],
        },
    )
    monkeypatch.setattr(price_sources, "prepare_price_source_text_layer", lambda **_kwargs: text_layer)

    routed = route_price_source_pdf_bundle(
        CombinedPriceSource(name="scan-bundle.pdf", data=pdf_bytes)
    )

    assert len(routed) == 2
    assert [item.text_layer.ocr_package["processing_seconds"] for item in routed] == [1.0, 1.0]
    assert all(len(item.text_layer.ocr_package["pages"]) == 1 for item in routed)


def test_jpeg_uses_ocr_before_price_extraction():
    called = []

    result = prepare_price_source_text_layer(
        file_name="invoice.jpg",
        file_bytes=_image_bytes(),
        image_ocr=lambda **kwargs: called.append(kwargs) or _ocr_package("Photo invoice"),
    )

    assert result.strategy == "image_ocr"
    assert result.text == "PAGE 1:\nPhoto invoice"
    assert called[0]["file_name"] == "invoice.jpg"
    assert result.ocr_package["source_file_name"] == "invoice.jpg"


def test_image_ocr_prepares_upscaled_table_evidence_for_arithmetic_rereads():
    package = {
        "pages": [{
            "page_number": 1,
            "markdown": "# Invoice",
            "dimensions": {"width": 64, "height": 48},
            "blocks": [{
                "type": "table",
                "top_left_x": 10,
                "top_left_y": 10,
                "bottom_right_x": 54,
                "bottom_right_y": 34,
            }],
        }]
    }

    evidence = render_price_source_table_evidence(
        image_bytes=_image_bytes(), ocr_package=package,
    )

    assert evidence is not None
    with Image.open(BytesIO(evidence)) as image:
        assert image.format == "PNG"
        assert image.width > 100
        assert image.height > 80


def test_tiff_is_normalised_to_png_for_mistral_ocr():
    called = []

    result = prepare_price_source_text_layer(
        file_name="invoice.tiff",
        file_bytes=_image_bytes("TIFF"),
        image_ocr=lambda **kwargs: called.append(kwargs) or _ocr_package("TIFF invoice"),
    )

    assert result.strategy == "image_ocr"
    assert called[0]["file_name"] == "invoice.png"
    assert result.ocr_package["source_file_name"] == "invoice.tiff"


def test_ocr_text_layer_includes_mistral_table_content_not_only_its_link():
    text = ocr_package_text(
        {
            "pages": [
                {
                    "page_number": 1,
                    "markdown": "# Invoice\n[tbl-0.html](tbl-0.html)",
                    "tables": [
                        {
                            "id": "tbl-0.html",
                            "format": "html",
                            "content": "<table><tr><td>Plywood</td><td>100</td></tr></table>",
                        }
                    ],
                }
            ]
        }
    )

    assert "[tbl-0.html]" in text
    assert "Plywood" in text
    assert "100" in text


def test_ocr_issuer_evidence_keeps_header_and_footer_outside_markdown():
    package = {
        "pages": [
            {
                "page_number": 1,
                "markdown": "# Invoice\nלכבוד: Buyer",
                "blocks": [
                    {"type": "header", "content": 'א.ש. פירוזל בע"מ\nע.מ. 513453233'},
                    {"type": "footer", "content": "תודה שקניתם בא.ש. פירוזל"},
                ],
            }
        ]
    }

    evidence = ocr_issuer_evidence_text(package)

    assert "OCR HEADER" in evidence
    assert "א.ש. פירוזל" in evidence
    assert "513453233" in evidence
    assert "OCR FOOTER" in evidence
    assert "תודה שקניתם" in evidence
    assert issuer_identity_from_source_text(evidence) == {
        "supplier_name": "א.ש. פירוזל",
        "supplier_hp": "513453233",
    }


def test_ocr_issuer_evidence_uses_first_page_markdown_when_header_blocks_are_absent():
    evidence = ocr_issuer_evidence_text(
        {
            "pages": [
                {
                    "page_number": 1,
                    "markdown": 'לבידי בוקטוס בע"מ\nח.פ. 514539998\nלכבוד: Buyer\nע.מ. 337791438',
                }
            ]
        }
    )

    assert "OCR PAGE LEAD" in evidence
    assert issuer_identity_from_source_text(evidence) == {
        "supplier_name": "לבידי בוקטוס",
        "supplier_hp": "514539998",
    }


def test_ocr_image_layer_exposes_header_footer_as_local_issuer_evidence():
    package = {
        "pages": [
            {
                "page_number": 1,
                "markdown": "# Invoice\nלכבוד: Buyer",
                "blocks": [
                    {"type": "header", "content": 'א.ש. פירוזל בע"מ\nע.מ. 513453233'},
                ],
            }
        ]
    }

    result = prepare_price_source_text_layer(
        file_name="invoice.jpg",
        file_bytes=_image_bytes(),
        image_ocr=lambda **_kwargs: package,
    )

    assert "לכבוד" in result.text
    assert "513453233" not in result.text
    assert "513453233" in result.issuer_evidence_text
