from __future__ import annotations

import base64
from io import BytesIO

import pymupdf
from PIL import Image, ImageDraw
import pytest

from use_cases.company_logo import (
    CompanyLogoError,
    load_company_logo_bytes,
    normalize_company_logo,
    persist_company_logo,
)


def _png(width: int = 800, height: int = 400) -> bytes:
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    ImageDraw.Draw(image).rectangle(
        (width // 8, height // 4, width * 7 // 8, height * 3 // 4),
        fill=(128, 73, 198, 255),
    )
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _pdf() -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=800, height=400)
    page.draw_rect(pymupdf.Rect(100, 100, 700, 300), color=(0.5, 0.28, 0.78), fill=(0.5, 0.28, 0.78))
    data = document.tobytes()
    document.close()
    return data


@pytest.mark.parametrize(
    ("source_format", "source"),
    [
        ("png", _png()),
        (
            "svg",
            b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">'
            b'<rect x="100" y="100" width="600" height="200" fill="#8049C6"/></svg>',
        ),
        ("pdf", _pdf()),
    ],
)
def test_company_logo_normalizes_supported_sources(source_format, source):
    result = normalize_company_logo(source)

    assert result.source_format == source_format
    assert len(result.png_bytes) <= 2 * 1024 * 1024
    with Image.open(BytesIO(result.png_bytes)) as image:
        assert image.format == "PNG"
        assert image.size == (1024, 1024)
        assert image.convert("RGBA").getpixel((512, 512))[:3] != (255, 255, 255)
        assert image.convert("RGBA").getpixel((512, 80))[:3] == (255, 255, 255)


@pytest.mark.parametrize(
    "source",
    [
        b"GIF89a-not-supported",
        b"\xff\xd8\xff\xe0-not-supported",
        b"PK\x03\x04-not-supported",
    ],
)
def test_company_logo_rejects_unsupported_file_types(source):
    with pytest.raises(CompanyLogoError, match="PNG, SVG, or PDF"):
        normalize_company_logo(source)


def test_company_logo_rejects_small_png_and_external_svg():
    with pytest.raises(CompanyLogoError, match="at least 512 px"):
        normalize_company_logo(_png(200, 100))

    with pytest.raises(CompanyLogoError, match="linked or unsupported resource"):
        normalize_company_logo(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">'
            b'<image href="https://example.com/logo.png"/></svg>'
        )


def test_company_logo_accepts_svg_with_embedded_raster_artwork():
    embedded_png = base64.b64encode(_png(800, 400))
    source = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">'
        b'<image width="800" height="400" href="data:image/png;base64,'
        + embedded_png
        + b'"/></svg>'
    )

    result = normalize_company_logo(source)

    assert result.source_format == "svg"
    with Image.open(BytesIO(result.png_bytes)) as image:
        assert image.size == (1024, 1024)


def test_company_logo_accepts_standard_svg_11_public_doctype():
    source = b'''<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800"
  viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="35" fill="#8049C6"/>
</svg>'''

    result = normalize_company_logo(source)

    assert result.source_format == "svg"
    assert result.source_width == 2048
    assert result.source_height == 2048


def test_company_logo_still_rejects_xml_entities():
    source = b'''<!DOCTYPE svg [<!ENTITY unsafe SYSTEM "file:///etc/passwd">]>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800">
  <text>&unsafe;</text>
</svg>'''

    with pytest.raises(CompanyLogoError, match="linked or unsupported resource"):
        normalize_company_logo(source)


class _Response:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, company_id: str, *, fail: bool = False):
        self.company_id = company_id
        self.fail = fail
        self.payload = None

    def update(self, payload):
        self.payload = payload
        return self

    def eq(self, field, value):
        assert field == "company_id"
        assert value == self.company_id
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("database unavailable")
        return _Response([{"company_id": self.company_id, **self.payload}])


class _Bucket:
    def __init__(self):
        self.uploaded = {}
        self.removed = []

    def upload(self, path, data, file_options=None):
        assert file_options == {
            "content-type": "image/png",
            "cache-control": "31536000",
            "upsert": "false",
        }
        self.uploaded[path] = data

    def remove(self, paths):
        self.removed.extend(paths)

    def download(self, path):
        return self.uploaded[path]


class _Storage:
    def __init__(self, bucket):
        self.bucket = bucket

    def from_(self, name):
        assert name == "company-logos"
        return self.bucket


class _Client:
    def __init__(self, company_id="company-a", *, fail_update=False):
        self.bucket = _Bucket()
        self.storage = _Storage(self.bucket)
        self.company_table = _Table(company_id, fail=fail_update)

    def table(self, name):
        assert name == "companies"
        return self.company_table


def test_company_logo_private_storage_replaces_previous_object():
    client = _Client()
    previous = "storage://company-logos/company-a/old.png"
    reference = persist_company_logo(
        client=client,
        company_id="company-a",
        png_bytes=b"normalized-png",
        previous_reference=previous,
    )

    assert reference.startswith("storage://company-logos/company-a/")
    assert reference.endswith(".png")
    assert client.company_table.payload == {"logo_url": reference}
    assert client.bucket.removed == ["company-a/old.png"]
    assert load_company_logo_bytes(
        client=client,
        company_id="company-a",
        reference=reference,
    ) == b"normalized-png"


def test_company_logo_rolls_back_new_object_when_database_update_fails():
    client = _Client(fail_update=True)

    with pytest.raises(RuntimeError, match="database unavailable"):
        persist_company_logo(
            client=client,
            company_id="company-a",
            png_bytes=b"normalized-png",
            previous_reference=None,
        )

    uploaded_path = next(iter(client.bucket.uploaded))
    assert client.bucket.removed == [uploaded_path]
