"""Run production UI/handlers against synthetic local data, never production services."""
from pathlib import Path
from types import SimpleNamespace
from base64 import b64encode
import json
from copy import deepcopy
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
import traceback

_fixture_report_failure = objects.report_runtime_failure
def _report_fixture_failure(stage, error, **scope):
 traceback.print_exception(type(error), error, error.__traceback__)
 _fixture_report_failure(stage, error, **scope)
objects.report_runtime_failure = _report_fixture_failure

import os
STATE = Path(os.environ['COSTERLY_UI_STATE_DIR'])
STATE.mkdir(parents=True, exist_ok=True)
sample = json.loads((Path(__file__).parent / 'fixtures/saved_estimate.json').read_text())
sample['run_id'] = sample['routes'][0]['run_id']
estimate_id = sample['routes'][0]['estimate_id']
for fixture_object in sample['parts']['objects'].values():
 fixture_object['preparation_evidence'] = {'status':'ready', 'interfaces':[]}
parts = json.dumps(sample['parts'])
lines = sample['lines']
run_id = sample['run_id']
company_id = 'fixture-lev1-company'
preview_ref = f'storage://rfq-estimation-evidence/{company_id}/{run_id}/object-001/crop.webp'
preview_url = 'data:image/svg+xml;base64,' + b64encode(
 (Path(__file__).parent / 'fixtures/presentation_crop.svg').read_bytes()).decode()
sample['review_objects'][0]['evidence_page_refs'] = [{
 'page_number': 1, 'preview_ref': preview_ref,
 'presentation_preview_bbox': {'top_left_x': 10, 'top_left_y': 10, 'bottom_right_x': 170, 'bottom_right_y': 110},
}]
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
 if scenario().get('fresh_progress') and (STATE / 'fresh-active').exists() and not (STATE / 'fresh-done').exists():
  record('ERROR active progress waited for object reads')
  raise AssertionError('Pending progress must not wait for unrelated result reads')
 if ((STATE / 'fresh-active').exists() and not (STATE / 'fresh-done').exists()
     and not (STATE / 'fresh-allocated').exists()):
  return pd.DataFrame([{**row, 'status':'running', 'self_cost_ex_vat':None,
   'progress_percent':15 if scenario().get('fresh_progress') else 35, 'progress_label':'Estimating'} for row in sample['objects']])
 if st.session_state.get('screen')=='file_review':
  lag_file=(STATE / 'slow-objects-read')
  if lag_file.exists():
   sleep(float(lag_file.read_text().removesuffix('s')))
 if st.session_state.get('screen')=='objects':
  sleep(float(scenario().get('objects_refresh_delay',0)))
 record('objects '+estimate_id)
 totals=json.loads(totals_path.read_text()) if totals_path.exists() else {}
 approvals=json.loads((STATE / 'object-approvals.json').read_text()) if (STATE / 'object-approvals.json').exists() else {}
 quantities_path=STATE/'object-quantities.json'
 quantities=json.loads(quantities_path.read_text()) if quantities_path.exists() else {}
 names_path=STATE/'object-names.json'
 names=json.loads(names_path.read_text()) if names_path.exists() else {}
 return pd.DataFrame([{**row,**({'object_name':names[row['object_id']]} if row['object_id'] in names else {}),**totals.get(row['object_id'],{}),**({'quantity':quantities[estimate_id+':'+row['object_id']]} if estimate_id+':'+row['object_id'] in quantities else {}),**({'approved':approvals[row['object_id']]} if row['object_id'] in approvals else {})} for row in sample['objects'] if row['estimate_id']==estimate_id])
def read_plans(_client, estimate_id):
 rows=[row for row in sample['plans'] if row['estimate_id']==estimate_id]
 if scenario().get('labor_ready'):
  source={key:sample['parts'].get(key) for key in ('run_id','estimate_id','input_ids','source_audit_sha256','overlay_revision')}
  rows=[{**row,'plan_payload':{**row['plan_payload'],'parts_check_source':source}} for row in rows]
 if scenario().get('front_panels'):
  choice=(STATE/'front-choice').read_text() if (STATE/'front-choice').exists() else 'ldsp'
  rows=[{**row,'plan_payload':front_plan(row['plan_payload'],choice)} for row in rows]
 return pd.DataFrame(rows)

def front_plan(plan, choice):
 plan=deepcopy(plan)
 if scenario().get('labor_ready'):
  plan['parts_check_source']={key:sample['parts'].get(key) for key in ('run_id','estimate_id','input_ids','source_audit_sha256','overlay_revision')}
 plan['front_panel_groups']={'object-001':[{'id':'fixture-front','source_name':'LDSP 17 mm',
  'source_choice':'ldsp','thickness_mm':17,'part_ids':['B01:door_front:001']} ]}
 plan['front_panel_choices']={'object-001':{'fixture-front':choice}}
 if scenario().get('coating'):
  plan['front_panel_groups']['object-001'][0].update(family='melamine_faced_particleboard',specification={},
   part_sources=[{'part_id':'B01:door_front:001','role':'door_front','quantity':2,'source_quantity':2,
    'scope_quantity':1,'measurements':{axis:{'mm':value} for axis,value in [('length',1000),('width',500),('thickness',20)]}}])
 base_choice={'veneered_mdf_oil':'veneered_mdf','plywood_oil':'plywood'}.get(choice,choice)
 labels={'ldsp':'LDSP','mdf':'MDF','veneered_mdf':'Veneered MDF','plywood':'Plywood'}
 for line in plan['lines']:
  if line.get('purchase_kind')=='sheet':
   line['display_name']=labels[base_choice]+' 17 mm'
   line['selection_key']='front-fixture-'+base_choice
   if choice!='ldsp':
    line['price_per_purchase_unit']+=100
    delta=100*line['purchase_quantity']
    line['total_cost']+=delta
    owners={(row['object_id'],row['material_requirement_id']) for row in line['allocations']}
    allocated=[row for row in plan['object_material_costs'] if (row['object_id'],row['material_requirement_id']) in owners]
    prior=sum(row['cost_ex_vat'] for row in allocated)
    for row in allocated:row['cost_ex_vat']+=delta*row['cost_ex_vat']/prior
    for value in (line.get('object_purchases') or {}).values():value['total']+=100*value['quantity']
   break
 return plan
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
file_review.evidence_signed_url = lambda **kw: preview_url if kw['storage_ref'] == preview_ref else None
file_review._record_first_file_review_render = lambda *_: None
if not hasattr(file_review,'_fixture_original_sync_naming'):
 file_review._fixture_original_sync_naming=file_review._sync_durable_naming_once
 file_review._fixture_original_sync_identity=file_review._sync_durable_document_identity_once
_real_sync_naming=file_review._fixture_original_sync_naming
_real_sync_identity=file_review._fixture_original_sync_identity
file_review._sync_durable_naming_once = lambda *_: None
file_review._sync_durable_document_identity_once = lambda *_: None
def fixture_project_metadata():
 path=STATE/'project-metadata.json'
 return json.loads(path.read_text()) if scenario().get('project_name_edit') and path.exists() else {'project_name':scenario().get('project_name','unknown')}
def save_project_metadata(**kwargs):
 values={**fixture_project_metadata(),**kwargs['values']}
 (STATE/'project-metadata.json').write_text(json.dumps(values))
 return values
file_review.save_file_review_run_metadata=save_project_metadata
def review_objects():
 result=list(map(_normalize_object,sample['review_objects']))
 names=json.loads((STATE/'object-names.json').read_text()) if (STATE/'object-names.json').exists() else {}
 for item in result:
  if item['object_id'] in names:item['name']=names[item['object_id']]
 return result
def save_review_name(**kwargs):
 assert kwargs['run_id']==run_id
 values={item['object_id']:item['name'] for item in review_objects()}
 current=values[kwargs['object_id']]
 if kwargs.get('expected_name')!=current:
  from use_cases.rfq_processing import FileReviewNameConflict
  raise FileReviewNameConflict(current)
 values[kwargs['object_id']]=kwargs['object_name'].strip()
 (STATE/'object-names.json').write_text(json.dumps(values))
 return values[kwargs['object_id']]
file_review.save_file_review_object_name=save_review_name
file_review.load_file_review_data = lambda _: {
 'run':{'file_name':'ui-fixture.pdf','pages_detected':1,**fixture_project_metadata()},
 'objects':review_objects(),
 'timings':{}, 'source':None,
}
file_review.load_file_review_naming_publication=lambda _run,**_kwargs:{
 'status':'succeeded','names':{item['object_id']:item['name'] for item in review_objects()}}
file_review.load_file_review_document_identity_publication=lambda _run,**_kwargs:{
 'status':'succeeded','metadata':fixture_project_metadata()}
file_review._source_bytes_for_objects_plan = no_estimation
estimation.get_supabase_client = Client
estimation._assert_screen_estimate_access = lambda *a, **kw: None
estimation.fetch_rfq_object_estimates = read_objects
def read_price_overrides(*_):
 filename=STATE / 'objects-prices.json'
 return pd.DataFrame(json.loads(filename.read_text()) if filename.exists() else [])
estimation.fetch_rfq_estimate_pricing_overrides = read_price_overrides
estimation.fetch_rfq_run = lambda *_: pd.DataFrame([fixture_project_metadata()])
estimation.fetch_rfq_estimate_material_plan = read_plans
objects.get_supabase_client = Client
objects._data_with_object_routes = lambda data, **_: data
objects.submit_prepared_estimation_job = no_estimation
_original_detail_prefetch = objects._prefetch_completed_object_details
def prefetch_details(*args, **kwargs):
 return _original_detail_prefetch(*args, **kwargs)
objects._prefetch_completed_object_details = prefetch_details
_original_object_navigation_loader = objects._load_prepared_object_navigation
def prepared_object_navigation(**kwargs):
 record('prepare Object '+kwargs['object_id'])
 from time import monotonic
 deadline=monotonic()+20
 while (STATE/'hold-object-preparation').exists():
  if monotonic()>deadline:raise TimeoutError('Test did not release Object preparation')
  sleep(.02)
 return _original_object_navigation_loader(**kwargs)
objects._load_prepared_object_navigation=prepared_object_navigation
estimation.fetch_rfq_object_quantity = lambda client, *, estimate_id, object_id: float(
 read_objects(client, estimate_id).set_index('object_id').loc[object_id, 'quantity'])
objects.load_parts_check = lambda **_: {'status':'ready'}
objects.load_estimation_cycle_cost = lambda **_: None
ocr_adapter.warm_mistral_http_client_async = lambda: None
upload.warm_mistral_http_client_async = lambda: None
hours_path=STATE / 'labor-hours.json'
totals_path=STATE / 'full-cost-totals.json'
derived_path=STATE / 'full-cost-lines.json'
def read_lines(_client, **kwargs):
 extra=json.loads(hours_path.read_text()) if hours_path.exists() else []
 extra+=(json.loads(derived_path.read_text()) if derived_path.exists() else [])
 return pd.DataFrame([row for row in lines+extra
  if row['estimate_id']==kwargs['estimate_id'] and row['object_id']==kwargs['object_id']])
estimation.fetch_rfq_estimate_lines_for_object = read_lines
def save_hours(_client, *, lines):
 if not lines:return
 if all(row['source']=='object_costs_v3_1' for row in lines):
  assert all(row['company_id']==company_id for row in lines)
  saved={row['line_id']:row for row in json.loads(derived_path.read_text())} if derived_path.exists() else {}
  saved.update({row['line_id']:row for row in lines});derived_path.write_text(json.dumps(list(saved.values())))
  return
 assert all(row['source']=='labor_hours_override' and row['company_id']==company_id for row in lines)
 if scenario().get('hours_write_failure'):raise RuntimeError('controlled hours write failure')
 saved={row['line_id']:row for row in json.loads(hours_path.read_text())} if hours_path.exists() else {}
 saved.update({row['line_id']:row for row in lines})
 hours_path.write_text(json.dumps(list(saved.values())))
estimation.upsert_rfq_estimate_lines=save_hours
estimation.fetch_rfq_estimate_lines=lambda client,estimate:pd.concat([read_lines(client,estimate_id=estimate,object_id=row['object_id']) for row in sample['objects'] if row['estimate_id']==estimate],ignore_index=True)
def save_totals(_client, *, estimate_id, object_id, **values):
 assert estimate_id==sample['routes'][0]['estimate_id']
 data=json.loads(totals_path.read_text()) if totals_path.exists() else {}
 data[object_id]={**data.get(object_id,{}),**{k:v for k,v in values.items() if v is not None}}
 totals_path.write_text(json.dumps(data))
estimation.update_rfq_object_estimate_totals=save_totals
estimation.fetch_company_overhead_settings = lambda *args: pd.DataFrame([])
estimation._with_saved_led_catalog_specs = lambda _client, plan: plan
estimation._with_saved_element_ownership = lambda _client, checked, *a, **kw: checked
def read_presentation(_client, **scope):
 assert scope == {'company_id': company_id, 'run_id': run_id, 'object_id': 'object-001'}
 record('preview read object-001')
 return sample['review_objects'][0]
estimation.fetch_rfq_detected_object_presentation = read_presentation
estimation._estimation_preview_url = lambda _client, ref, **kw: preview_url if ref == preview_ref else None
object_detail._overlay_links = lambda *a, **kw: None
labor.get_supabase_client = Client
labor.load_parts_check = lambda **_: {'status':'ready', 'payload':parts}
labor.fetch_rfq_estimate_material_plan = read_plans
labor.load_sheet_processing_machinery = lambda *_: {'availability':{'finish_wet_spray_booth':'in_house'}} if scenario().get('coating') else {}
_original_labor_loader = getattr(labor,'_ui_fixture_original_labor_loader',labor.load_object_labor)
labor._ui_fixture_original_labor_loader = _original_labor_loader
def fixture_labor_loader(*args, **kwargs):
 if scenario().get('labor_unknown'):return {'status':'preparing'}
 state=_original_labor_loader(*args, **kwargs)
 if scenario().get('special_assembly'):
  from use_cases.additional_assembly import calculate_additional_assembly
  from use_cases.block_assembly import calculate_block_assembly
  evidence={'objects':{'fixture':{'blocks':[{'id':'B01'}],'parts':[
   {'role':'fixed_panel','quantity':3,'block_id':'B01'},
   {'role':'hinge','quantity':4,'block_id':'B01'},
   {'role':'door_front','quantity':2,'block_id':'B01'},
   {'role':'push_latch','quantity':2,'block_id':'B01'},
   {'role':'glass_box_lid','quantity':8,'instance_ref':'glass boxes'},
   {'role':'mirror_glass','quantity':2,'instance_ref':'mirrors'},
   {'role':'led_strip_run','quantity':4,'instance_ref':'LED zones'}]}}}
  state={**state,'assembly':calculate_block_assembly(evidence,object_id='fixture'),
         'additional_assembly':calculate_additional_assembly(evidence,object_id='fixture')}
 if scenario().get('edge_applicable') and state.get('status')=='ready':
  # This interaction fixture includes an applicable edge operation at a zero
  # configured norm. Its financial baseline remains unchanged; inapplicable
  # edges are checked separately in coatingChecks and the unit source cases.
  state=deepcopy(state);state['result']['edge_banding']['metres']=10
 return state
labor.load_object_labor = fixture_labor_loader
estimation.load_object_labor = fixture_labor_loader

def read_overhead(_client, scoped_company, *, delay=True, parallel_reads=False):
 assert scoped_company == company_id
 if delay:sleep(scenario().get('overhead_delay', 0))
 if scenario().get('overhead_read_failure'):raise RuntimeError('controlled overhead read failure')
 record('overhead read '+company_id)
 return {'status':'ready','settings':{'production_workers':12,'workdays_per_month':21,
  'hours_per_day':8,'vat_percent':18}, 'monthly':{'rent_facilities_cost':20160}}
labor._load_overhead_context=read_overhead
def full_cost_context(client,obj,plan,settings=None,**kwargs):
 inputs=read_overhead(client,obj['company_id'],delay=False)
 return {**inputs,'plan':plan,'parts':{'status':'ready','payload':parts},
  'machinery':{'availability':{'finish_wet_spray_booth':'in_house'}} if scenario().get('coating') else {},**kwargs}
estimation._full_cost_context=full_cost_context

def save_materials(**kwargs):
 assert kwargs['estimate_id']==estimate_id and kwargs['object_id']=='object-001'
 if kwargs['edits'] and all(edit['field']=='labor_hours' for edit in kwargs['edits']):
  return estimation.save_object_detail_material_edits(**kwargs)
 front_edits=[edit for edit in kwargs['edits'] if edit['field']=='front_material']
 assert len(kwargs['edits'])==1 or (scenario().get('coating') and len(front_edits)==1
  and all(edit['field'] in {'front_material','labor_hours'} for edit in kwargs['edits']))
 if front_edits:
  choice=front_edits[0]['value']
  preview=kwargs.get('preview',False)
  record('front preview' if preview else 'front save')
  sleep(float(scenario().get('front_delay',0.15)))
  result=Future()
  if not preview and scenario().get('front_save_failure'):
   result.set_exception(RuntimeError('Controlled persistence failure'))
   return result
  if scenario().get('front_failure'):
   result.set_exception(ValueError('Controlled front material failure.'))
   return result
  plan=front_plan(sample['plans'][0]['plan_payload'],choice)
  if not preview:
   if (STATE / 'object-approvals.json').exists():
    (STATE / 'object-approvals.json').write_text(json.dumps({'object-001':False}))
   (STATE/'front-choice').write_text(choice)
   if scenario().get('coating'):
    hours={edit['lineId']:estimation.validate_hours(edit['value']) for edit in kwargs['edits'] if edit['field']=='labor_hours'}
    if hours:save_hours(Client(),lines=estimation.override_lines(hours,estimate_id=estimate_id,
      object_id='object-001',company_id=company_id,quantity=1))
    estimation._recalculate_object_estimate_totals(Client(),estimate_id=estimate_id,object_id='object-001',
      object_row={**sample['objects'][0],'estimate_id':estimate_id},settings=read_overhead(Client(),company_id,delay=False)['settings'],
      lines_df=read_lines(Client(),estimate_id=estimate_id,object_id='object-001'),
      plan_snapshot=plan,cost_context=full_cost_context(Client(),{'company_id':company_id},plan,preserve_labor=True))
  result.set_result(plan)
  return result
 if kwargs['edits'][0]['field']=='labor_hours':
  return estimation.save_object_detail_material_edits(**kwargs)
 record('save material '+kwargs['estimate_id'])
 st.session_state.fixture_material_edit=kwargs['edits'][0]
 result=Future()
 result.set_result(None)
 return result

def saved_receipt(**kwargs):
 if scenario().get('labor_ready') and hours_path.exists():
  return estimation.load_object_detail_material_receipt(**kwargs)
 data=estimation.load_object_detail_data(**kwargs)
 edit=st.session_state.get('fixture_material_edit')
 if not edit:return data
 for row in data['sections'][0]['rows']:
  if row.get(edit['field']+'_line_id')==edit['lineId']:
   row[edit['field']+'_value']=float(edit['value'])
 return data

object_detail.save_object_detail_material_edits=save_materials
object_detail.load_object_detail_material_receipt=saved_receipt
def front_preview_receipt(**kwargs):
 data=estimation.front_material_preview_receipt(**kwargs)
 record('front receipt '+json.dumps(data['self_cost']))
 return data
object_detail.front_material_preview_receipt=front_preview_receipt
if st.query_params.get('screen') == 'object_detail' or st.session_state.get('screen') == 'object_detail':
 record('read Object Detail '+str(st.session_state.get('current_estimate_id')))

from screens import company_profile, projects, platform_admin
from use_cases.platform_admin import PlatformAccess
config_path=(STATE / 'scenario.json')
def scenario():
 return json.loads(config_path.read_text()) if config_path.exists() else {}
object_detail.get_supabase_client=Client
object_detail.fetch_rfq_object_detail_draft=lambda *a,**kw:[]
def approve_saved_object(**kwargs):
 assert kwargs['estimate_id']==estimate_id and kwargs['object_id']=='object-001'
 sleep(float(scenario().get('approval_delay',0)))
 record('approve object')
 (STATE / 'object-approvals.json').write_text(json.dumps({'object-001':True}))
 return {'costs_changed':False}
object_detail.approve_object_estimate=approve_saved_object
if scenario().get('objects_v2'):
 objects._objects_price_input_config=lambda:('http://127.0.0.1:'+('8796' if scenario().get('fresh_progress') else '8798'),'fixture-anon','fixture-token')
 def generate_proposal(**kwargs):
  assert kwargs['company_id']==company_id and kwargs['estimate_id']==estimate_id and kwargs['run_id']==run_id
  current=estimation.load_objects_estimation_data(estimate_id)
  previous=json.loads((STATE / 'generated-proposal.json').read_text()) if (STATE / 'generated-proposal.json').exists() else {}
  request=(kwargs.get('confirmed_data') or {}).get('proposal_request_id')
  version=int(previous.get('version_number',0))+(previous.get('proposal_request_id')!=request or not previous)
  if (STATE / 'generation-failure').exists():raise RuntimeError('Controlled proposal failure')
  if (STATE / 'proposal-delay').exists():sleep(float((STATE / 'proposal-delay').read_text()))
  if not previous or version!=previous.get('version_number'):record('proposal generated')
  current.update(version_number=version,proposal_request_id=request)
  if not previous or version!=previous.get('version_number'):
   history_path=STATE/'generated-proposal-history.json'
   history=json.loads(history_path.read_text()) if history_path.exists() else []
   history.append(deepcopy(current));history_path.write_text(json.dumps(history,default=str))
  (STATE / 'generated-proposal.json').write_text(json.dumps(current,default=str))
  url='http://127.0.0.1:8798/'+('generated-proposal.pdf' if version==1 else f'generated-proposal-v{version}.pdf')
  return {'project_id':'project-one','version_id':f'version-{version}','version_number':version,'proposal_pdf_url':url}
 objects.final_approval=generate_proposal
 def saved_proposal_url(**kwargs):
  if not (STATE / 'generated-proposal.json').exists():return None
  saved=json.loads((STATE / 'generated-proposal.json').read_text())
  if objects.pricing_signature(saved)!=objects.pricing_signature(kwargs.get('current_data') or saved):return None
  version=saved['version_number']
  return 'http://127.0.0.1:8798/'+('generated-proposal.pdf' if version==1 else f'generated-proposal-v{version}.pdf')
 objects.load_estimate_proposal_url=saved_proposal_url
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
def history_workspace():
 versions=[]
 for n in [1,2,3]:
  versions.append({'version_id':f'history-{n}','project_id':'history-project',
   'source_file_id':'source-a' if n<3 else 'source-b','estimate_id':'calc-a' if n<3 else 'calc-b',
   'version_number':n,'approved_at':'2026-11-27T10:00:00Z','summary':{'total':n*100},
   'project_metadata':{'project_name':'Furniture'},'objects':[{'name':'Chair','quantity':n,'sale_price_unit':100,'sale_price_total':n*100}],
   'proposal_pdf_url':'http://127.0.0.1:8798/'+('generated-proposal.pdf' if n==1 else f'generated-proposal-v{n}.pdf')})
 history_path=STATE/'generated-proposal-history.json'
 for saved in json.loads(history_path.read_text()) if history_path.exists() else []:
  n=saved['version_number']
  versions.append({'version_id':f'generated-{n}','project_id':'generated-project','source_file_id':'generated-source',
   'estimate_id':estimate_id,'version_number':n,'approved_at':'2026-11-27T12:00:00Z','summary':saved['summary'],
   'project_metadata':{'project_name':saved.get('project_name')},'objects':saved['rows'],
   'proposal_pdf_url':'http://127.0.0.1:8798/'+('generated-proposal.pdf' if n==1 else f'generated-proposal-v{n}.pdf')})
 versions.append({'version_id':'legacy','project_id':'partnerless','source_file_id':None,'estimate_id':'legacy-calc','version_number':1,
  'approved_at':'2026-11-26T12:00:00Z','summary':{'total':100},'objects':[{'name':'Legacy object','quantity':1}], 'proposal_pdf_url':None})
 return {'organizations':[{'organization_id':'partner-1','name':'Lev1 Partner'}], 'clients':[],
  'projects':[{'project_id':'history-project','partner_organization_id':'partner-1','name':'Version workspace'},
              {'project_id':'generated-project','partner_organization_id':'partner-1','name':'Generated project'},
              {'project_id':'partnerless','partner_organization_id':None,'name':None}],
  'files':[{'file_id':'source-a','project_id':'history-project','file_name':'Drawing.pdf'},
           {'file_id':'source-b','project_id':'history-project','file_name':'Drawing.pdf'},
           {'file_id':'generated-source','project_id':'generated-project','file_name':'Current drawing.pdf'}], 'versions':versions}
projects.load_projects_workspace=lambda *_args: guarded_load('projects',
 history_workspace() if scenario().get('project_history') else
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
company_profile.load_company_logo_bytes=lambda *_args,**_kwargs:(Path(__file__).resolve().parents[2] / 'cloudflare/assets/email/costerly-ai-logo.png').read_bytes() if scenario().get('profile_logo_present') else None
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
 settings=scenario()
 if not settings.get('prices_catalog_size') and not settings.get('prices_projection_delays'):
  return {name:complete_projection() for name in kwargs['loaders']}
 from use_cases.price_source_runtime import _PRICE_LISTS_READ_EXECUTOR
 def load(name):
  record('prices started '+name)
  sleep(float(settings.get('prices_projection_delays',{}).get(name,0)))
  record('prices finished '+name)
  if name!='catalog':return []
  size=int(settings.get('prices_catalog_size',120))
  return [{'source_id':'price-source','source_row_id':f'price-row-{i}',
   'department':'Metal' if i<10 else 'Wood','material_type':'Metal' if i<10 else 'Plywood',
   'supplier_name':'Fixture supplier','canonical_name':f'Fixture material {i}',
   'display_label':f'Fixture material {i}','normalized_price':100,'normalized_unit':'piece',
   'currency':'ILS','vat_included':False,'updated_at':'2026-11-23','source_kind':'link'} for i in range(size)]
 return {name:_PRICE_LISTS_READ_EXECUTOR.submit(load,name) for name in kwargs['loaders']}
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
 def in_(self,key,values):self.filters[key]=list(values);return self
 def limit(self,*_args):return self
 def order(self,*_args,**_kwargs):return self
 def update(self,payload):self.operation='update';self.payload=payload;return self
 def insert(self,payload):self.operation='insert';self.payload=payload;return self
 def upsert(self,payload,**_kwargs):self.operation='upsert';self.payload=payload;return self
 def execute(self):
  delay=float(scenario().get('read_delay',0.08)) if self.operation=='select' else float(scenario().get('write_delay',0))
  if delay:sleep(delay)
  if self.operation!='select' and scenario().get('fail_write')==self.name:
   raise RuntimeError('Injected Profile write failure')
  if self.operation=='select' and (scenario().get('fail_read')==self.name or (scenario().get('fail')=='account' and self.name.startswith('overhead_'))):
   raise RuntimeError('Injected Profile read failure')
  data=read_db()
  rows=data[self.name]
  selected=[row for row in rows if all(row.get(key) in value if isinstance(value,list) else row.get(key)==value for key,value in self.filters.items())]
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
  if self.operation=='select' and self.name=='companies' and scenario().get('profile_logo_present'):
   selected=[{**row,'logo_url':'storage://company-logos/'+company_id+'/fixture-logo.png'} for row in selected]
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
if scenario().get('fresh_calculation'):
 from use_cases import estimation_runtime as runtime
 from state.session import init_state
 init_state()
 if not st.session_state.get('fixture_fresh_started'):
  st.session_state.fixture_fresh_started=True
  st.session_state.screen='objects'
  st.session_state.current_run_id=run_id
  st.session_state.current_estimate_id=estimate_id
  st.session_state.prepared_estimate_access={'company_id':company_id,'run_id':run_id,'estimate_id':estimate_id}
  st.session_state.objects_estimation_seed_rows=[{'object_key':'object-001','name':'Saved bench',
   'quantity':1,'status':'pending','self_cost_unit':None,'progress_percent':3}]
  (STATE / 'fresh-active').touch()
  def create_shell(**kwargs):
   sleep(3.5)
   (STATE / 'fresh-shell-ready').touch()
   return {'estimate_id':estimate_id}
  def calculate(**kwargs):
   record('fresh worker started')
   if scenario().get('fresh_progress'):
    from use_cases.estimation_progress import begin_estimate_progress, set_estimate_stage, finish_estimate_progress
    token=begin_estimate_progress(estimate_id,['object-001'])
    for stage in ['geometry_ready','understanding_ready','locators_ready','inventory_ready',
                  'parts_ready','material_context_ready','material_plan_ready','materials_ready',
                  'parts_check_ready','allocations_published','plan_published']:
     if stage=='plan_published':(STATE / 'fresh-allocated').touch()
     set_estimate_stage(estimate_id,token,stage)
     for _ in range(300):
      if (STATE / ('fresh-stage-'+stage)).exists():break
      sleep(.1)
     else:raise AssertionError('Fixture stage was not released: '+stage)
    finish_estimate_progress(estimate_id,token)
   elif scenario().get('fresh_finish_away'):
    for _ in range(300):
     if (STATE / 'fresh-release').exists():break
     sleep(.1)
    else:raise AssertionError('Fixture calculation was not released')
   else:
    sleep(4)
   (STATE / 'fresh-done').touch()
   return {'estimate_id':estimate_id}
  runtime.save_file_review_run_metadata=lambda **_:None
  runtime.start_estimation_for_run=create_shell
  runtime._run_estimation_job=calculate
  st.session_state.estimation_batch_future=runtime.submit_prepared_estimation_job(
   estimate_id=estimate_id,run_id=run_id,company_id=company_id,file_name='fixture.pdf',file_bytes=b'pdf',
   object_edits={},metadata_values={},edits_changed=False,ignored_object_ids=set(),create_shell=True)
  # Match _start_prepared_estimation_launch's ownership receipt. This fixture
  # directly submits the real runtime worker instead of dispatching that UI plan.
  st.session_state.objects_estimation_future_id=estimate_id
 def assert_durable(*args, **kwargs):
  if not (STATE / 'fresh-shell-ready').exists():
   record('ERROR ownership read before shell')
   raise PermissionError('Estimate is not available to this company.')
 estimation._assert_screen_estimate_access=assert_durable
 st.button('Fixture rerender',key='fixture_calculation_rerender')
if scenario().get('material_row_geometry'):
 # Component geometry uses production CSS/renderer without invoking financial
 # persistence. The full saved-estimate interaction scenarios remain separate.
 from styles.object_detail import apply_object_detail_css
 from ui.object_detail_view import _table_html, MATERIAL_PURCHASE_COLUMNS
 apply_object_detail_css()
 audit=estimation.calculate_part_coating(front_plan(sample['plans'][0]['plan_payload'],'plywood'),object_id='object-001')
 rows=[{'item':'Consumables','locked':True,'policy_percent':5,'policy_basis':'materials','total':50},
       {'item':'Packaging','locked':True,'policy_percent':1,'policy_basis':'materials','total':10},
       estimation.coating_material_rows(audit)[-1],
       {'item':'Plywood','required_material_value':2,'required_material_unit':'m²',
        'required_material_line_id':'material:plywood','purchase_quantity_value':1,
        'purchase_quantity_line_id':'material:plywood','purchase_unit':'sheet','purchase_unit_cost':100,'total':100}]
 st.markdown(_table_html({'key':'material','columns':MATERIAL_PURCHASE_COLUMNS,'rows':rows}),unsafe_allow_html=True)
 st.stop()
if scenario().get('front_panels') and not derived_path.exists():
 # This scenario represents a completed estimate, including its saved Labor.
 # Seed that existing breakdown before opening the card, never on selection.
 obj={**sample['objects'][0], 'estimate_id':estimate_id}
 plan=front_plan(sample['plans'][0]['plan_payload'],'ldsp')
 estimation._full_cost_summary(Client(),estimate_id=estimate_id,obj=obj,
  lines=read_lines(Client(),estimate_id=estimate_id,object_id='object-001'),material_batch=0,
  context=full_cost_context(Client(),obj,plan))
if scenario().get('last_estimate_latency'):
 # Independent, fixed-latency reads. The old serial route exceeds the real
 # unchanged15s transition deadline; the Last-only joins must retain all data.
 file_review._sync_durable_naming_once=_real_sync_naming
 file_review._sync_durable_document_identity_once=_real_sync_identity
 def delayed_read(fn,seconds,label):
  def read(*args,**kwargs):
   record('restore-read-start '+label)
   sleep(seconds)
   value=fn(*args,**kwargs)
   record('restore-read-end '+label)
   return value
  return read
 file_review.load_file_review_data=delayed_read(file_review.load_file_review_data,2.4,'source')
 file_review.load_file_review_naming_publication=delayed_read(file_review.load_file_review_naming_publication,2,'naming')
 file_review.load_file_review_document_identity_publication=delayed_read(file_review.load_file_review_document_identity_publication,2,'identity')
 for name in ['fetch_rfq_object_estimates','fetch_rfq_estimate_pricing_overrides','fetch_rfq_estimate_material_plan']:
  setattr(estimation,name,delayed_read(getattr(estimation,name),3,name))
app.main()
if scenario().get('late_review_ack'):
 from streamlit.runtime.scriptrunner import get_script_run_ctx
 for widget_id in get_script_run_ctx().session_state._state._new_widget_state.widget_metadata:
  if widget_id.endswith(('-file_review_run_metadata.project_name', '-file_review_object_edits.object-001.name')):
   record('review-field-widget-id '+widget_id)

