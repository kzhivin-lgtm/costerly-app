import pymupdf
import pytest

from use_cases.proposal_pdf import (
    _contact_lines,
    build_proposal_pdf,
    proposal_download_name,
    proposal_signed_url,
)


def _snapshot():
    return {
        "rows": [
            {
                "name": "Display shelf",
                "quantity": 2,
                "self_cost_unit": 800,
                "sale_price_unit": 1200,
                "sale_price_total": 2400,
            }
        ],
        "project_costs": [
            {"object_key": "delivery", "name": "Delivery", "sale_price_unit": 72},
            {"object_key": "installation", "name": "Installation", "sale_price_unit": 240},
        ],
        "summary": {
            "project_price": 2712,
            "vat": 488.16,
            "total": 3200.16,
            "vat_percent": 18,
        },
    }


def test_proposal_omits_empty_contacts_and_self_cost():
    assert _contact_lines({"public_email": "office@example.com"}) == ["office@example.com"]

    payload = build_proposal_pdf(
        profile={"company_name": "Workshop"},
        project_name="Restaurant Deer",
        partner_name="Studio Tree",
        client_name="Restaurant Group",
        snapshot=_snapshot(),
    )

    assert payload.startswith(b"%PDF")
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Display shelf" in text
    assert "Delivery" in text
    assert "Installation" in text
    assert "Project Total" in text
    assert "800" not in text


def test_proposal_production_time_uses_saved_working_days_without_changing_totals():
    snapshot=_snapshot()
    snapshot['production_time_working_days']=15
    payload=build_proposal_pdf(profile={'company_name':'Workshop'},project_name='A3',
                               partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=payload,filetype='pdf') as document:
        text='\n'.join(page.get_text() for page in document)
    assert 'Production time: 15 working days after payment' in text
    assert 'delivery and installation excluded' in text.lower()
    assert 'Production time: 15 working days after payment.' not in text
    assert snapshot['summary']['total']==3200.16


def test_proposal_supports_non_latin_project_names():
    payload = build_proposal_pdf(
        profile={"company_name": "Мастерская"},
        project_name="Ресторан Олень",
        partner_name="Бюро Ёлочка",
        client_name="Ресторанная группа",
        snapshot=_snapshot(),
    )
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Ресторан Олень" in text
    assert "Бюро Ёлочка" in text


def test_signed_proposal_url_accepts_supabase_response_spelling():
    class Bucket:
        def create_signed_url(self, path, expires_in, options=None):
            assert path == "company/project/version.pdf"
            assert expires_in == 3600
            assert options is None
            return {"signedURL": "https://signed.example/proposal.pdf"}

    class Storage:
        def from_(self, bucket):
            assert bucket == "project-proposals"
            return Bucket()

    class Client:
        storage = Storage()

    assert proposal_signed_url(Client(), "company/project/version.pdf") == (
        "https://signed.example/proposal.pdf"
    )


def test_proposal_download_name_uses_project_partner_and_approval_date():
    assert proposal_download_name(
        project_name="Restaurant / Deer",
        partner_name="Studio Tree",
        approved_at="2026-10-03T13:39:35+03:00",
    ) == "Restaurant - Deer_Studio Tree_2026-10-03.pdf"

@pytest.mark.parametrize('advance',[None,0,70,100])
def test_optional_payment_terms_preserve_financial_totals(advance):
    snapshot=_snapshot();snapshot['advance_payment_percent']=advance
    payload=build_proposal_pdf(profile={'company_name':'Workshop'},project_name='ADA',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=payload,filetype='pdf') as pdf:
        text='\n'.join(page.get_text() for page in pdf)
    if advance is None:assert 'Payment terms:' not in text
    else:assert f'Payment terms: {advance}% advance payment, {100-advance}% on completion' in text
    assert snapshot['summary']['total']==3200.16

@pytest.mark.parametrize('advance',[-1,101,70.5,True])
def test_pdf_rejects_invalid_advance_payment(advance):
    snapshot=_snapshot();snapshot['advance_payment_percent']=advance
    with pytest.raises(ValueError):
        build_proposal_pdf(profile={},project_name='ADA',partner_name='',client_name='',snapshot=snapshot)


def test_branded_document_uses_native_text_requisites_and_frozen_date():
    snapshot=_snapshot()
    snapshot['document']={'issued_at':'2026-11-27T09:00:00Z'}
    profile={'company_name':'DO NOT DUPLICATE HEADER','legal_name':'Workshop Ltd',
             'company_registration_number':'123456789','bank_name':'Saved bank',
             'account_number':'12345','facebook_url':'https://example.test/not-in-proposal'}
    snapshot['rows'][0]['materials']='plywood 18 mm fronts · LED · mirror'
    result=build_proposal_pdf(profile=profile,project_name='ADA',partner_name='Studio',client_name='Customer',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        assert len(pdf)==1
        text='\n'.join(p.get_text() for p in pdf)
        for expected in ['27 November 2026','Workshop Ltd','123456789','Saved bank','12345','estimated with','plywood 18 mm fronts','Partner: Studio','Client: Customer','₪2 400']:
            assert expected in text
        assert 'DO NOT DUPLICATE HEADER' not in text
        assert 'facebook' not in text.lower()
        assert '\x00' not in text
        assert not pdf[0].get_images()
        pix=pdf[0].get_pixmap()
        assert pix.pixel(10,10)==(255,255,255)
        assert len(pdf[0].get_fonts())>1


def test_many_rows_and_long_mixed_names_preserve_every_object():
    snapshot=_snapshot()
    snapshot['rows']=[{**snapshot['rows'][0],'name':f'Object {i:02d} '+('cabinet with long description '*4)} for i in range(25)]
    result=build_proposal_pdf(profile={'legal_name_hebrew':'חברה בע״מ'},project_name='Проект шкаф',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        assert len(pdf)>1
        text='\n'.join(p.get_text() for p in pdf)
        for i in range(25):assert f'Object {i:02d}' in text
        assert 'Проект шкаф' in text
        assert text.count('Project Total')==1
        for page in pdf:
            for block in page.get_text('dict')['blocks']:
                if block['type']==0:
                    assert block['bbox'][3]<=842


def test_summary_on_its_own_page_does_not_repeat_an_empty_object_table():
    snapshot=_snapshot()
    snapshot['rows']=[{**snapshot['rows'][0],'name':f'Cabinet {i}'} for i in range(4)]
    result=build_proposal_pdf(profile={},project_name='ADA',partner_name='Studio',client_name='Customer',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        assert len(pdf)>1
        last=pdf[-1].get_text()
        assert 'Project Total' in last
        assert 'QTY' not in last


def test_shared_webp_preview_is_embedded_without_rasterizing_the_page():
    from PIL import Image
    from io import BytesIO
    buffer=BytesIO();Image.new('RGB',(80,60),'white').save(buffer,format='WEBP')
    snapshot=_snapshot();snapshot['rows'][0]['object_key']='object-1'
    result=build_proposal_pdf(profile={},project_name='ADA',partner_name='',client_name='',snapshot=snapshot,
                              preview_bytes={'object-1':buffer.getvalue()})
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        assert pdf[0].get_images()
        assert 'Display shelf' in pdf[0].get_text()
        for image in pdf[0].get_images():
            assert all(rect.get_area()<pdf[0].rect.get_area()*.1 for rect in pdf[0].get_image_rects(image[0]))


def test_pdf_logo_preserves_complete_wordmark_without_the_profile_preview_card():
    from pathlib import Path
    from PIL import Image
    from io import BytesIO
    from use_cases.company_logo import normalize_company_logo
    from use_cases.proposal_document import logo_image
    normalized=normalize_company_logo(Path('assets/brand/costelry_logo_full_cropped.svg').read_bytes())
    payload,size=logo_image(normalized.png_bytes)
    assert size[0]/size[1]>4
    result=build_proposal_pdf(profile={'company_name':'Duplicate name'},project_name='ADA',partner_name='',client_name='',snapshot=_snapshot(),logo_bytes=normalized.png_bytes)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        rect=pdf[0].get_image_rects(pdf[0].get_images()[0][0])[0]
        assert abs(rect.x0-51)<.01
        assert 'Duplicate name' not in pdf[0].get_text()
