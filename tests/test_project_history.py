from copy import deepcopy
from urllib.parse import parse_qs,urlsplit

from screens.projects import _projects_table
from use_cases.projects import load_projects_workspace


def sample():
    return {
        'organizations':[{'company_id':'c','organization_id':'partner','name':'Studio','is_partner':True}],
        'projects':[{'company_id':'c','project_id':'p','name':'Current project','partner_organization_id':'partner'}],
        'files':[{'company_id':'c','project_id':'p','file_id':'file-a','file_name':'Drawing.pdf','content_sha256':'a'*64},
                 {'company_id':'c','project_id':'p','file_id':'file-b','file_name':'Drawing.pdf','content_sha256':'b'*64}],
        'clients':[],
        'versions':[
            {'company_id':'c','project_id':'p','source_file_id':'file-a' if n<3 else 'file-b',
             'estimate_id':'estimate-a' if n<3 else 'estimate-b','version_id':f'v{n}','version_number':n,
             'approved_at':'2026-11-27T10:00:00Z','summary':{'total':n*100},
             'proposal_pdf_path':f'c/p/v{n}.pdf','proposal_pdf_url':f'https://example.invalid/v{n}.pdf',
             'project_metadata':{'project_name':'Frozen project','design_partner':'Saved partner'},
             'objects':[{'name':'Chair','quantity':n,'sale_price_unit':100,'sale_price_total':n*100}]}
            for n in [1,2,3]],
    }


def test_history_keeps_source_and_estimate_ids_distinct_even_with_identical_names():
    data=sample();html=_projects_table(data)
    assert html.count('class="projects-file"')==2
    assert html.count('class="projects-calculation"')==2
    assert html.count('class="projects-version"')==3
    assert html.count('class="projects-objects"')==3
    assert 'data-source-file-id="file-a"' in html and 'data-source-file-id="file-b"' in html
    assert 'V1' in html and 'V2' in html and 'V3' in html
    assert html.count('Drawing.pdf')==2


def test_optional_partner_and_legacy_unknown_source_do_not_hide_projects_or_invent_groups():
    data=sample();data['organizations']=[];data['projects'][0]['partner_organization_id']=None
    data['projects'][0]['name']=None;data['files']=[]
    for version in data['versions']:version['source_file_id']=None
    html=_projects_table(data)
    assert 'projects-project-row' in html and 'V1' in html
    assert 'Unknown' not in html and 'Untitled' not in html
    assert 'projects-empty' not in html


def test_history_escapes_names_and_rejects_active_url_schemes():
    data=sample();data['versions'][0]['objects'][0]['name']='<img src=x onerror=alert(1)>'
    data['versions'][0]['proposal_pdf_url']='javascript:alert(1)'
    html=_projects_table(data)
    assert '<img' not in html and '&lt;img' in html and 'javascript:' not in html


def test_workspace_reads_every_page_and_batch_signs_all_versions_with_frozen_names(monkeypatch):
    data=sample();tables={'organizations':data['organizations'],'projects':data['projects'],
                         'project_files':data['files'],'project_versions':data['versions']}
    tables['project_versions'].append({**deepcopy(data['versions'][0]),'version_id':'bad','proposal_pdf_path':'foreign/p/bad.pdf'})
    reads=[];signs=[]
    class Query:
        def __init__(self,name):self.name=name;self.start=0;self.filters={}
        def select(self,columns,**kwargs):
            assert 'snapshot,' not in columns and columns!='*'
            return self
        def eq(self,key,value):self.filters[key]=value;return self
        def order(self,*a):return self
        def range(self,start,end):self.start=start;return self
        def execute(self):
            assert self.filters=={'company_id':'c'}
            reads.append((self.name,self.start))
            class Response:pass
            r=Response();r.count=len(tables[self.name]);r.data=deepcopy(tables[self.name][self.start:self.start+2]);return r
    class Storage:
        def from_(self,bucket):assert bucket=='project-proposals';return self
        def create_signed_urls(self,paths,expiry):
            signs.append(paths);assert expiry==3600
            return [{'path':path,'signedURL':'https://example.invalid/'+path+'?token=test'} for path in paths]
    class Client:
        storage=Storage()
        def table(self,name):return Query(name)
    monkeypatch.setattr('use_cases.projects.get_supabase_client',Client)
    result=load_projects_workspace('c')
    assert len(result['versions'])==4 and len(result['files'])==2
    assert ('project_versions',2) in reads
    assert len(signs)==1 and len(signs[0])==3
    for version in result['versions']:
        if version['version_id']=='bad':assert version['proposal_pdf_url'] is None;continue
        query=parse_qs(urlsplit(version['proposal_pdf_url']).query)
        assert query['download']==[f"Frozen project_Saved partner_V{version['version_number']}.pdf"]
        assert '2026-' not in query['download'][0]
