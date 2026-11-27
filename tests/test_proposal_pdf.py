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
    assert 'Preliminary production time estimate: approximately 15 working days' in text.replace('\n',' ')
    assert 'Installation time is not included' in text.replace('\n',' ')
    assert 'Production lead time' not in text and 'Payment terms:' not in text
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


def test_proposal_download_name_uses_project_partner_and_version_number():
    assert proposal_download_name(
        project_name="Restaurant / Deer",
        partner_name="Studio Tree",
        version_number=2,
        approved_at="2026-11-27T13:00:00Z",
    ) == "Restaurant - Deer_Studio Tree_V2.pdf"


@pytest.mark.parametrize('project,partner,expected',[
    (None,None,'V1.pdf'),
    ('unknown','none','V1.pdf'),
    ('ADA',None,'ADA_V1.pdf'),
    (None,'Studio','Studio_V1.pdf'),
])
def test_download_name_omits_absent_metadata(project,partner,expected):
    assert proposal_download_name(project_name=project,partner_name=partner,
                                  version_number=1,approved_at='2026-11-27T13:00:00Z') == expected


@pytest.mark.parametrize('project_present',[False,True])
@pytest.mark.parametrize('partner_present',[False,True])
@pytest.mark.parametrize('client_present',[False,True])
def test_pdf_omits_each_absent_metadata_field(project_present,partner_present,client_present):
    result=build_proposal_pdf(profile={},project_name='Named project' if project_present else 'unknown',
        partner_name='Named partner' if partner_present else None,
        client_name='Named client' if client_present else '',snapshot=_snapshot())
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        text='\n'.join(p.get_text() for p in pdf)
    assert ('Named project' in text) == project_present
    assert ('Partner: Named partner' in text) == partner_present
    assert ('Client: Named client' in text) == client_present
    assert 'Untitled project' not in text and 'Unknown Partner' not in text and 'unknown' not in text
    assert ('Partner:' in text) == partner_present
    assert ('Client:' in text) == client_present

@pytest.mark.parametrize('advance',[None,0,70,100])
def test_optional_payment_terms_preserve_financial_totals(advance):
    snapshot=_snapshot();snapshot['advance_payment_percent']=advance
    payload=build_proposal_pdf(profile={'company_name':'Workshop'},project_name='ADA',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=payload,filetype='pdf') as pdf:
        text='\n'.join(page.get_text() for page in pdf)
    assert 'Payment terms:' not in text
    if advance is None:assert 'Advance payment:' not in text
    else:assert f'Advance payment: {advance}%' in text
    assert snapshot['summary']['total']==3200.16

@pytest.mark.parametrize('advance',[-1,101,70.5,True])
def test_pdf_rejects_invalid_advance_payment(advance):
    snapshot=_snapshot();snapshot['advance_payment_percent']=advance
    with pytest.raises(ValueError):
        build_proposal_pdf(profile={},project_name='ADA',partner_name='',client_name='',snapshot=snapshot)


def test_branded_document_uses_native_text_requisites_frozen_version_and_date():
    snapshot=_snapshot()
    snapshot['document']={'issued_at':'2026-11-27T09:00:00Z'}
    snapshot['version_number']=3
    profile={'company_name':'DO NOT DUPLICATE HEADER','legal_name':'Workshop Ltd',
             'company_registration_number':'123456789','bank_name':'Saved bank',
             'account_number':'12345','facebook_url':'https://example.test/not-in-proposal'}
    snapshot['rows'][0]['materials']='plywood 18 mm fronts · LED · mirror'
    result=build_proposal_pdf(profile=profile,project_name='ADA',partner_name='Studio',client_name='Customer',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        assert len(pdf)==1
        text='\n'.join(p.get_text() for p in pdf)
        assert 'V3' in text and '27 November 2026' in text
        for expected in ['V3','123456789','Saved bank','12345','estimated with','plywood 18 mm fronts','Partner: Studio','Client: Customer','₪2 400']:
            assert expected in text
        assert 'DO NOT DUPLICATE HEADER' not in text
        assert 'Workshop Ltd' not in text
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


def test_owner_footer_revision_aligns_both_languages_and_omits_legal_name():
    snapshot=_snapshot();snapshot['production_time_working_days']=15;snapshot['advance_payment_percent']=70
    result=build_proposal_pdf(profile={'legal_name':'Do not print legal name','legal_name_hebrew':'לא להציג',
        'company_registration_number':'123456789','bank_name':'Saved bank'},
        project_name='ADA',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        page=pdf[0]
        spans=[span for block in page.get_text('dict')['blocks'] if block['type']==0
               for line in block['lines'] for span in line['spans']]
        text=page.get_text()
        assert 'Do not print legal name' not in text and 'לא להציג' not in text
        start=next(span['origin'][1] for span in spans if span['text'].startswith('Preliminary production time estimate:'))
        terms=[span for span in spans if span['origin'][1]>=start-.2 and abs(span['size']-8)<.1]
        assert terms
        grouped={}
        for span in terms:grouped.setdefault(round(span['origin'][1],1),[]).append(span)
        assert all(abs(max(span['bbox'][2] for span in line)-544)<2 for line in grouped.values())
        hebrew=[span for span in terms if any('א'<=char<='ת' for char in span['text'])]
        english=[span for span in terms if not any('א'<=char<='ת' for char in span['text'])]
        assert hebrew and english
        heading=[span for span in spans if 'הצעת' in span['text']]
        assert not heading
        english_bottom=max(span['bbox'][3] for span in english)
        assert min(span['bbox'][1] for span in hebrew)>english_bottom
        assert 'הובלה' in text and 'התקנה' in text
        assert 'Production lead time' not in text and 'Payment terms:' not in text
        lines=[item[1].y for path in page.get_drawings() for item in path['items']
               if item[0]=='l' and abs(item[1].x-51)<.01 and abs(item[2].x-544)<.01]
        footer=max(lines)
        registration=next(span for span in spans if span['text'].startswith('Company No.'))
        assert 0<registration['bbox'][1]-footer<11
        credit=next(span for span in spans if span['text']=='estimated with')
        assert abs(credit['bbox'][2]-544)<1.5
        assert credit['bbox'][3]<footer+18


@pytest.mark.parametrize('width,height',[(600,600),(1800,600),(3000,600),(600,1500)])
def test_profile_normalized_logos_use_one_pdf_height_without_contact_overlap(width,height):
    from use_cases.company_logo import normalize_company_logo
    from use_cases.proposal_document import logo_image
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="#8049c6"/></svg>'.encode()
    normalized=normalize_company_logo(svg)
    _,size=logo_image(normalized.png_bytes)
    result=build_proposal_pdf(profile={'public_email':'contact@fixture.invalid'},project_name='A3',
        partner_name='',client_name='',snapshot=_snapshot(),logo_bytes=normalized.png_bytes)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        page=pdf[0];rect=page.get_image_rects(page.get_images()[0][0])[0]
        assert abs(rect.height-71)<.01 and abs(rect.y0-48)<.01 and abs(rect.x0-51)<.01
        assert abs(rect.width/rect.height-size[0]/size[1])<.001
        contacts=page.search_for('contact@fixture.invalid')
        assert contacts and all((rect & box).is_empty for box in contacts)


def test_bilingual_terms_share_the_same_line_pitch():
    snapshot=_snapshot();snapshot['production_time_working_days']=14;snapshot['advance_payment_percent']=70
    result=build_proposal_pdf(profile={},project_name='ADA',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        spans=[span for block in pdf[0].get_text('dict')['blocks'] for line in block.get('lines',[]) for span in line['spans']]
        start=next(span['origin'][1] for span in spans if span['text'].startswith('Preliminary production time estimate:'))
        rows=sorted({round(span['origin'][1],2) for span in spans if span['origin'][1]>=start-.2 and abs(span['size']-8)<.1})
        text=pdf[0].get_text().replace('\n',' ')
    assert len(rows)==6
    pitches=[rows[i+1]-rows[i] for i in range(len(rows)-1)]
    assert max(pitches)-min(pitches)<.2,pitches
    assert all(abs(pitch-18)<.2 for pitch in pitches),pitches
    assert 'site. Installation time is not included' in text
    assert 'Installation time is not included.' not in text
    assert 'זמן ההתקנה אינו כלול.' not in text


@pytest.mark.parametrize('advance',[None,0,70,100])
def test_owner_terms_keep_three_explicit_rows_in_each_language(advance):
    snapshot=_snapshot();snapshot['production_time_working_days']=365;snapshot['advance_payment_percent']=advance
    result=build_proposal_pdf(profile={},project_name='',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:
        spans=[s for block in pdf[-1].get_text('dict')['blocks'] for line in block.get('lines',[]) for s in line['spans']]
        start=next(s['origin'][1] for s in spans if s['text']=='Preliminary production time estimate:')
        rows={}
        for span in spans:
            if span['origin'][1]>=start-.2 and abs(span['size']-8)<.1:
                rows.setdefault(round(span['origin'][1],1),[]).append(span)
        lines=list(rows.values())
        assert len(lines)==6
        assert ''.join(s['text'] for s in lines[0])=='Preliminary production time estimate:'
        assert 'approximately 365 working days' in ''.join(s['text'] for s in lines[1])
        assert ''.join(s['text'] for s in lines[2])=='until the items are ready for delivery to site. Installation time is not included'
        assert all(abs(max(s['bbox'][2] for s in row)-544)<2 for row in lines)
        for row in lines[3:]:assert any(any('א'<=c<='ת' for c in s['text']) for s in row)



@pytest.mark.parametrize('change',['price','partner','client','days','profile','source'])
def test_reopening_changed_inputs_cannot_restore_an_old_proposal_url(change):
    from copy import deepcopy
    from use_cases.proposal_pdf import load_estimate_proposal_url
    original=_snapshot()
    original.update(project_name='ADA',design_partner='Studio',client='Client',proposal_source={'settings':{'advance':70}})
    original['document']={'project':{'project_name':'ADA','design_partner':'Studio','client':'Client'},'profile':{'public_email':'old@example.test'}}
    current=deepcopy(original)
    if change=='price':current['rows'][0]['sale_price_unit']=999
    if change=='partner':current['design_partner']='New studio'
    if change=='client':current['client']='New client'
    if change=='days':current['production_time_working_days']=999
    if change=='source':current['proposal_source']['settings']['advance']=50
    class Query:
        def table(self,name):self.name=name;return self
        def select(self,*a):return self
        def eq(self,*a):return self
        def order(self,*a,**kw):return self
        def limit(self,*a):return self
        def execute(self):
            class Response:pass
            r=Response()
            r.data=([{'snapshot':original,'version_number':1,'proposal_pdf_path':'old.pdf'}]
                    if self.name=='project_versions' else [{'public_email':'new@example.test' if change=='profile' else 'old@example.test'}])
            return r
        @property
        def storage(self):raise AssertionError('A stale PDF must never be signed')
    assert load_estimate_proposal_url(client=Query(),company_id='c',estimate_id='e',current_data=current) is None


def test_unchanged_legacy_proposal_reopens_with_frozen_name_and_version():
    from copy import deepcopy
    from use_cases.proposal_pdf import load_estimate_proposal_url
    frozen=_snapshot();frozen['document']={'project':{'project_name':'Original','design_partner':'Studio'},'profile':{}}
    current=deepcopy(frozen);current.update(project_name='Original',design_partner='Studio',proposal_source={'new_receipt':True})
    current['rows'][0]['proposal_input_basis']='not captured by legacy snapshot'
    calls=[]
    class Query:
        def table(self,name):self.name=name;return self
        def select(self,*a):return self
        def eq(self,*a):calls.append(('eq',*a));return self
        def order(self,*a,**kw):calls.append(('order',a,kw));return self
        def limit(self,*a):return self
        def execute(self):
            class Response:pass
            r=Response();r.data=[{'snapshot':frozen,'version_number':2,'proposal_pdf_path':'original-v2.pdf'}] if self.name=='project_versions' else [{}]
            assert self.name!='rfq_runs','Use frozen metadata for an issued filename'
            return r
        @property
        def storage(self):return self
        def from_(self,bucket):assert bucket=='project-proposals';return self
        def create_signed_url(self,path,expiry,options):
            calls.append(('signed',path,options))
            return {'signedURL':'signed-v2.pdf'}
    assert load_estimate_proposal_url(client=Query(),company_id='c',estimate_id='e',current_data=current)=='signed-v2.pdf'
    assert ('eq','company_id','c') in calls and ('eq','estimate_id','e') in calls
    assert ('order',('version_number',),{'desc':True}) in calls
    assert ('signed','original-v2.pdf',{'download':'Original_Studio_V2.pdf'}) in calls


@pytest.mark.parametrize('company',['c','foreign'])
def test_proposal_source_reuses_private_content_identity_and_checks_company(company):
    from use_cases.proposal_pdf import capture_proposal_source
    meta={'storage_ref':f'storage://rfq-estimation-originals/{company}/'+('a'*64)+'.pdf',
          'content_sha256':'a'*64,'size_bytes':100,'mime_type':'application/pdf'}
    calls=[]
    class Query:
        def table(self,name):assert name=='agent_usage_events';return self
        def select(self,*a):return self
        def eq(self,*a):calls.append(a);return self
        def in_(self,*a):return self
        def order(self,*a,**k):return self
        def execute(self):
            class Response:data=[{'raw_usage':{'estimation_original':meta}}]
            return Response()
    if company=='foreign':
        with pytest.raises(ValueError,match='does not belong'):
            capture_proposal_source(client=Query(),company_id='c',run_id='r',file_name='same-name.pdf')
    else:
        source=capture_proposal_source(client=Query(),company_id='c',run_id='r',file_name='same-name.pdf')
        assert source=={**meta,'file_name':'same-name.pdf'}
        assert ('company_id','c') in calls and ('run_id','r') in calls


def test_missing_legacy_source_stays_unknown_without_blocking_generation():
    from use_cases.proposal_pdf import capture_proposal_source
    class Query:
        def table(self,*a):return self
        def select(self,*a):return self
        def eq(self,*a):return self
        def in_(self,*a):return self
        def order(self,*a,**k):return self
        def execute(self):
            class Response:data=[{'raw_usage':'invalid legacy JSON'},{'raw_usage':{}}]
            return Response()
    assert capture_proposal_source(client=Query(),company_id='c',run_id='r',file_name='old.pdf') is None


def test_new_proposal_download_reads_small_basis_without_full_calculation():
    from use_cases.proposal_pdf import load_estimate_proposal_url
    from use_cases.proposal_basis import pricing_signature
    current=_snapshot();current['proposal_source']={'settings':{'vat_percent':18}}
    selections=[]
    class Query:
        def table(self,name):self.name=name;return self
        def select(self,columns):
            selections.append(columns)
            assert columns!='snapshot','Do not download the complete issued calculation for a link'
            return self
        def eq(self,*a):return self
        def order(self,*a,**k):return self
        def limit(self,*a):return self
        def execute(self):
            class Response:pass
            r=Response();r.data=([{'version_id':'v2','version_number':2,'proposal_pdf_path':'v2.pdf',
                                  'proposal_basis_sha256':pricing_signature(current),'project':{},'profile':{}}]
                                 if self.name=='project_versions' else [{}])
            return r
        @property
        def storage(self):return self
        def from_(self,*a):return self
        def create_signed_url(self,*a,**k):return {'signedURL':'download-v2'}
    assert load_estimate_proposal_url(client=Query(),company_id='c',estimate_id='e',current_data=current)=='download-v2'
    assert len(selections)==2


def test_frozen_pdf_date_uses_the_saved_local_timezone_at_midnight():
    snapshot=_snapshot();snapshot['version_number']=2
    snapshot['document']={'issued_at':'2026-11-27T22:30:00Z','timezone':'Asia/Jerusalem'}
    result=build_proposal_pdf(profile={},project_name='A3',partner_name='',client_name='',snapshot=snapshot)
    with pymupdf.open(stream=result,filetype='pdf') as pdf:text=pdf[0].get_text()
    assert '28 November 2026' in text and 'V2' in text
