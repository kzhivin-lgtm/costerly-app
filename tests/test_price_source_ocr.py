from io import BytesIO

import fitz
from PIL import Image

from use_cases.price_source_ocr import (
    ocr_issuer_evidence_text,
    ocr_package_text,
    prepare_price_source_text_layer,
)
from use_cases.price_sources import issuer_identity_from_source_text


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
