from io import BytesIO

import fitz
from PIL import Image

from use_cases.price_source_ocr import prepare_price_source_text_layer


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


def test_digital_pdf_uses_embedded_text_without_ocr():
    document = fitz.open()
    page = document.new_page()
    for line in range(12):
        page.insert_text((72, 72 + line * 18), f"Digital supplier invoice line {line} with price evidence")
    pdf_bytes = document.tobytes()
    document.close()

    result = prepare_price_source_text_layer(
        file_name="invoice.pdf",
        file_bytes=pdf_bytes,
        pdf_ocr=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected OCR")),
    )

    assert result.strategy == "pdf_embedded_text"
    assert "Digital supplier invoice" in result.text


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
