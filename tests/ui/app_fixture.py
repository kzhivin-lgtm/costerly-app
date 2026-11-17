"""Run production UI/handlers against synthetic local data, never production services."""
from pathlib import Path
from types import SimpleNamespace
import json
import pandas as pd
import streamlit as st
import socket
_original_socket_connect = socket.socket.connect

def _local_connect(sock, address):
    if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1', 'localhost'}:
        raise AssertionError('UI fixture attempted a nonlocal connection')
    return _original_socket_connect(sock, address)

socket.socket.connect = _local_connect
import app
from screens import company_profile
_original_profile_reads={name:getattr(company_profile,name) for name in [
 'load_company_metrics','load_company_profile','load_company_members',
 'load_company_employees','_start_post_overhead_warmup']}
from agents import ocr_adapter
from screens import file_review, objects, upload, object_detail, estimation_labor_v1 as labor
from concurrent.futures import Future
from time import sleep
from state import company_auth
from use_cases import estimation
from use_cases.rfq_processing import _normalize_object

import os
STATE = Path(os.environ['COSTERLY_UI_STATE_DIR'])
STATE.mkdir(parents=True, exist_ok=True)
sample = json.loads((Path(__file__).parent / 'fixtures/saved_estimate.json').read_text())
sample['run_id'] = sample['routes'][0]['run_id']
estimate_id = sample['routes'][0]['estimate_id']
parts = json.dumps(sample['parts'])
lines = sample['lines']
run_id = sample['run_id']
company_id = 'fixture-lev1-company'
status_path = (STATE / 'auth-expired')
journal = (STATE / 'browser-journal')
def record(payload):
 with journal.open('a') as stream: stream.write(payload + chr(10))
def no_estimation(**kwargs):
 record('ERROR tried to estimate')
 raise AssertionError('Parts Check must not be launched during restore')
class Client:
 def table(self, name): self.name=name; self.filters={}; return self
 def select(self, _): return self
 def eq(self, key, value): self.filters[key]=value; return self
 def order(self, *_args, **_kwargs): return self
 def limit(self, _): return self
 def execute(self):
  assert self.filters.get('company_id')==company_id
  if self.name=='agent_usage_events':
   return SimpleNamespace(data=[{'run_id':run_id}])
  assert self.name=='rfq_estimates' and self.filters['run_id']==run_id
  record('lookup saved estimate')
  return SimpleNamespace(data=sample['routes'])
def read_objects(_client, estimate_id):
 if st.session_state.get('screen')=='file_review':
  lag_file=(STATE / 'slow-objects-read')
  if lag_file.exists():
   sleep(float(lag_file.read_text().removesuffix('s')))
 record('objects '+estimate_id)
 return pd.DataFrame([row for row in sample['objects'] if row['estimate_id']==estimate_id])
def read_plans(_client, estimate_id):
 return pd.DataFrame([row for row in sample['plans'] if row['estimate_id']==estimate_id])
def company_access(**kwargs):
 record('auth checked '+('expired' if status_path.exists() else 'valid'))
 return None if status_path.exists() else company_auth.CompanyAccess('fixture-user','fixture@example.invalid',company_id,'owner','fixture-token')

app.configure_runtime_sink = lambda *x: None
app.company_auth_enabled = lambda: True
app.current_company_access = company_access
app.sync_browser_auth_session = lambda **_: True
app.invitation_from_url = lambda: None
app.legal_consent_enabled = lambda: False
app.get_supabase_client = Client
app.get_company_id = lambda: company_id
app._header_client = lambda _: Client()
app.take_prefetched_header_access = lambda **_: None
app.load_platform_access = lambda *_: None
app.record_authenticated_session_in_background = lambda *a, **kw: None
app.assert_run_owned = lambda _client, run_id, company_id: None
app.assert_estimate_owned = lambda _client, estimate_id, company_id: None
app._workflow_route_token = lambda **kw: {'run':'fileReview1234','estimate':'estimate1234','object':'objectDetail1234'}[kw['scope']]
app.resolve_workflow_route_token = lambda *a, **kw: {
 'run_id':run_id,
 'estimate_id':estimate_id if kw['expected_scope'] in {'estimate','object'} else None,
 'object_id':'object-001' if kw['expected_scope']=='object' else None,
}
file_review.get_supabase_client = Client
file_review.get_company_id = lambda: company_id
file_review._record_first_file_review_render = lambda *_: None
file_review._sync_durable_naming_once = lambda *_: None
file_review._sync_durable_document_identity_once = lambda *_: None
file_review.load_file_review_data = lambda _: {
 'run':{'file_name':'ui-fixture.pdf','pages_detected':1},
 'objects':list(map(_normalize_object,sample['review_objects'])),
 'timings':{}, 'source':None,
}
file_review._source_bytes_for_objects_plan = no_estimation
estimation.get_supabase_client = Client
estimation._assert_screen_estimate_access = lambda *a, **kw: None
estimation.fetch_rfq_object_estimates = read_objects
estimation.fetch_rfq_estimate_pricing_overrides = lambda *_: pd.DataFrame()
estimation.fetch_rfq_estimate_material_plan = read_plans
objects.get_supabase_client = Client
objects._data_with_object_routes = lambda data, **_: data
objects.submit_prepared_estimation_job = no_estimation
objects._prefetch_completed_object_details = lambda *a, **kw: None
objects.load_parts_check = lambda **_: {'status':'ready'}
objects.load_estimation_cycle_cost = lambda **_: None
ocr_adapter.warm_mistral_http_client_async = lambda: None
upload.warm_mistral_http_client_async = lambda: None
estimation.fetch_rfq_estimate_lines_for_object = lambda _client, **kwargs: pd.DataFrame([
 row for row in lines if row['estimate_id']==kwargs['estimate_id'] and row['object_id']==kwargs['object_id']
])
estimation.fetch_company_overhead_settings = lambda *args: pd.DataFrame([])
estimation._with_saved_led_catalog_specs = lambda _client, plan: plan
estimation._with_saved_element_ownership = lambda _client, checked, *a, **kw: checked
estimation._estimation_preview_url = lambda *a, **kw: None
object_detail._overlay_links = lambda *a, **kw: None
labor.get_supabase_client = Client
labor.load_parts_check = lambda **_: {'status':'ready', 'payload':parts}
labor.fetch_rfq_estimate_material_plan = read_plans
labor.load_sheet_processing_machinery = lambda *_: {}

def save_materials(**kwargs):
 assert kwargs['estimate_id']==estimate_id and kwargs['object_id']=='object-001'
 assert len(kwargs['edits'])==1
 record('save material '+kwargs['estimate_id'])
 st.session_state.fixture_material_edit=kwargs['edits'][0]
 result=Future()
 result.set_result(None)
 return result

def saved_receipt(**kwargs):
 data=estimation.load_object_detail_data(**kwargs)
 edit=st.session_state.fixture_material_edit
 for row in data['sections'][0]['rows']:
  if row.get(edit['field']+'_line_id')==edit['lineId']:
   row[edit['field']+'_value']=float(edit['value'])
 return data

object_detail.save_object_detail_material_edits=save_materials
object_detail.load_object_detail_material_receipt=saved_receipt
if st.query_params.get('screen') == 'object_detail' or st.session_state.get('screen') == 'object_detail':
 record('read Object Detail '+str(st.session_state.get('current_estimate_id')))

from screens import company_profile, projects, platform_admin
from use_cases.platform_admin import PlatformAccess
config_path=(STATE / 'scenario.json')
def scenario():
 return json.loads(config_path.read_text()) if config_path.exists() else {}
def guarded_load(screen, data):
 settings=scenario()
 record('load '+screen)
 sleep(float(settings.get('delay',{}).get(screen,0)))
 if settings.get('fail')==screen:
  raise RuntimeError('Controlled read failure')
 return data
def platform_access(*_args):
 return PlatformAccess('fixture-user','platform_admin') if scenario().get('admin',True) else None
app.load_platform_access=platform_access
def require_platform(*_args):
 access=platform_access()
 if access is None: raise PermissionError('Platform Admin access is required.')
 return access
platform_admin.get_supabase_client=Client
platform_admin.require_platform_access=require_platform
platform_admin.record_dashboard_view=lambda *_args,**_kwargs:None
platform_admin.load_company_dashboard=lambda *_args,**_kwargs: guarded_load('admin',[
 {'company_id':company_id,'company_name':'Lev1 workshop','users_count':1}
])
platform_admin.load_manufacturing_parameter_library=lambda *_args,**_kwargs: guarded_load('admin',[])
projects.load_projects_workspace=lambda *_args: guarded_load('projects',
 {'organizations':[],'projects':[],'clients':[],'versions':[]} if scenario().get('empty_projects') else
 {'organizations':[{'organization_id':'partner-1','name':'Lev1 Partner'}],
  'projects':[{'project_id':'project-1','partner_organization_id':'partner-1','name':'Lev1 booth'}],
  'clients':[],'versions':[]})
company_profile.load_company_metrics=lambda *_args: guarded_load('account',({'vat_percent':18},{}))
company_profile._start_post_overhead_warmup=lambda *_args,**_kwargs:None
company_profile.list_company_machinery=lambda *_args:[]
company_profile.list_company_suppliers=lambda *_args:[]
company_profile.list_supplier_services=lambda *_args:[]
company_profile.load_company_profile=lambda *_args: guarded_load('account',{'company_name':'Lev1 workshop'})
company_profile.load_company_logo_bytes=lambda *_args,**_kwargs:None
company_profile.load_company_employees=lambda *_args:[]
company_profile.load_company_members=lambda *_args:[]
original_company_access=company_access
def company_access(**kwargs):
 access=original_company_access(**kwargs)
 if access is None: return None
 return company_auth.CompanyAccess(access.user_id,access.email,access.company_id,scenario().get('role','owner'),access.access_token)
app.current_company_access=company_access
original_sign_out=company_auth.sign_out
def sign_out_fixture():
 original_sign_out()
 status_path.write_text('expired')
company_auth.sign_out=sign_out_fixture

def projection_jobs(*_args,**kwargs):
 return {name:complete_projection() for name in kwargs['loaders']}
def complete_projection():
 result=Future()
 result.set_result([])
 return result
company_profile.submit_price_lists_projection_jobs=projection_jobs
company_profile.list_price_catalog=lambda *_args:[]
company_profile.list_unresolved_price_source_rows=lambda *_args:[]
company_profile.list_price_sources=lambda *_args:[]
company_profile.list_material_jobs=lambda *_args:[]
company_auth.create_company_join_url=lambda *_args,**_kwargs:'https://fixture.invalid/join'

from use_cases import machinery as machinery_use_case
from uuid import uuid4
db_path=(STATE / 'profile-db.json')
if not db_path.exists():
 db_path.write_text(json.dumps({
  'companies':[{'company_id':company_id,'company_name':'Lev1 workshop','public_email':'office@fixture.invalid','public_phone':'+972501234567','bank_name':'Fixture Bank','bank_number':'10','branch_number':'20','account_number':'30'}],
  'overhead_settings':[{'company_id':company_id,'vat_percent':18}],
  'overhead_monthly':[{'company_id':company_id}],
  'company_members':[{'company_id':company_id,'user_id':'fixture-user','role':'owner'},{'company_id':company_id,'user_id':'fixture-member','role':'member'}],
  'company_employees':[],'company_machinery':[],'company_suppliers':[],'company_supplier_services':[]
 }))
def read_db():
 return json.loads(db_path.read_text())
def write_db(data):
 temporary=db_path.with_suffix('.tmp')
 temporary.write_text(json.dumps(data))
 temporary.replace(db_path)
class ProfileQuery:
 def __init__(self,name):
  self.name=name;self.filters={};self.operation='select';self.payload=None
 def select(self,*_args,**_kwargs):return self
 def eq(self,key,value):self.filters[key]=value;return self
 def is_(self,key,value):self.filters[key]=None if value=='null' else value;return self
 def limit(self,*_args):return self
 def order(self,*_args,**_kwargs):return self
 def update(self,payload):self.operation='update';self.payload=payload;return self
 def insert(self,payload):self.operation='insert';self.payload=payload;return self
 def upsert(self,payload,**_kwargs):self.operation='upsert';self.payload=payload;return self
 def execute(self):
  delay=float(scenario().get('read_delay',0.08)) if self.operation=='select' else 0
  if delay:sleep(delay)
  if self.operation!='select' and scenario().get('fail_write')==self.name:
   raise RuntimeError('Injected Profile write failure')
  if self.operation=='select' and (scenario().get('fail_read')==self.name or (scenario().get('fail')=='account' and self.name.startswith('overhead_'))):
   raise RuntimeError('Injected Profile read failure')
  data=read_db()
  rows=data[self.name]
  selected=[row for row in rows if all(row.get(key)==value for key,value in self.filters.items())]
  if self.operation=='update':
   for row in selected:row.update(self.payload)
  elif self.operation in {'insert','upsert'}:
   payload=dict(self.payload)
   if self.name=='company_machinery':
    selected=[row for row in rows if row.get('company_id')==payload.get('company_id') and row.get('machine_code')==payload.get('machine_code')]
    payload.setdefault('company_machine_id',str(uuid4()))
   else:selected=[]
   if selected:selected[0].update(payload)
   else:
    if self.name=='company_employees':payload.setdefault('employee_id',str(uuid4()))
    rows.append(payload);selected=[payload]
  if self.operation!='select':
   write_db(data);record('write '+self.name)
  else:record('read '+self.name)
  return SimpleNamespace(data=selected)
class ProfileRpc:
 def __init__(self,name,params):self.name=name;self.params=params
 def execute(self):
  assert self.name=='remove_company_member_access'
  data=read_db()
  data['company_members']=[row for row in data['company_members'] if row['user_id']!=self.params['p_member_id']]
  write_db(data);record('write company_members')
  return SimpleNamespace(data=[])
class ProfileClient:
 def rpc(self,name,params):return ProfileRpc(name,params)
 @property
 def auth(self):
  return SimpleNamespace(admin=SimpleNamespace(get_user_by_id=lambda uid:SimpleNamespace(user=SimpleNamespace(email=uid+'@fixture.invalid'))))
 def table(self,name):
  if name in read_db():return ProfileQuery(name)
  return Client().table(name)
for name,original in _original_profile_reads.items():setattr(company_profile,name,original)
company_profile.get_supabase_client=ProfileClient
company_profile.list_company_machinery=machinery_use_case.list_company_machinery
company_profile.list_company_suppliers=machinery_use_case.list_company_suppliers
company_profile.list_supplier_services=machinery_use_case.list_supplier_services
machinery_use_case.get_supabase_client=ProfileClient
company_auth.current_company_access=company_access
company_auth._server_client=lambda:ProfileClient()

restart=scenario()
if restart.pop('restart_once',False):
 config_path.write_text(json.dumps(restart))
 st.session_state._app_boot_id='previous-worker'
app.main()

