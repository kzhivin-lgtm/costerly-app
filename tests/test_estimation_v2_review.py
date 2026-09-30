from ui import object_detail_view, objects_pricing
from use_cases.estimation import _estimation_preview_url, _material_rows_from_v2_facts


def test_pending_object_without_v2_facts_stays_disabled():
    markup = objects_pricing._review_action_html(
        {"object_key": "object-1", "status": "pending"},
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert ">Pending<" in markup
    assert "aria-disabled" in markup


def test_object_detail_uses_v2_materials_without_inventing_costs():
    rows = _material_rows_from_v2_facts({
        "materials": [{
            "requirement_id": "mat-1",
            "source_name": "MDF panel 20 mm",
            "family": "mdf",
            "unit": "m2",
            "quantity": None,
        }]
    })

    assert rows == [{
        "group": "Detected materials",
        "line_id": "mat-1",
        "item": "MDF panel 20 mm",
        "unit": "m2",
        "unit_cost": None,
        "qty": None,
        "cost": None,
    }]


class _Bucket:
    def create_signed_url(self, path, expires_in):
        assert path == "company-1/run-1/object-1/preview.webp"
        assert expires_in == 3600
        return {"signedURL": "https://signed.example/preview.webp"}


class _Storage:
    def from_(self, bucket):
        assert bucket == "rfq-estimation-evidence"
        return _Bucket()


class _Client:
    storage = _Storage()


def test_object_detail_preview_requires_owned_private_path():
    assert _estimation_preview_url(
        _Client(),
        "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp",
        company_id="company-1",
    ) == "https://signed.example/preview.webp"
    assert _estimation_preview_url(
        _Client(),
        "storage://rfq-estimation-evidence/company-2/run-1/object-1/preview.webp",
        company_id="company-1",
    ) is None


def test_object_detail_hero_renders_source_preview():
    markup = object_detail_view.hero_html({
        "name": "Shelving unit",
        "quantity": 1,
        "confidence": 0.95,
        "preview_label": "Object preview",
        "preview_url": "https://signed.example/preview.webp",
    })

    assert 'class="object-detail-preview-image"' in markup
    assert 'src="https://signed.example/preview.webp"' in markup
