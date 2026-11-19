"""Production auth/ready code, rotating one-use synthetic tokens, no external IO."""
from pathlib import Path
from types import SimpleNamespace
import base64,json,os,socket,time
import streamlit as st
from supabase_auth.errors import AuthApiError
from state import company_auth as auth, session_resume
from observability.runtime import new_runtime_trace, LABOR_BUILD_VERSION
from app import _signal_ready
from styles.auth import apply_auth_css

_connect=socket.socket.connect
socket.socket.connect=lambda sock,address: _connect(sock,address) if not isinstance(address,tuple) or address[0] in {'127.0.0.1','::1','localhost'} else (_ for _ in ()).throw(AssertionError('nonlocal auth fixture IO'))
STATE=Path(os.environ['COSTERLY_UI_STATE_DIR']);STATE.mkdir(exist_ok=True,parents=True)
config_path=STATE/'auth-scenario.json';db_path=STATE/'auth-provider.json'
def settings():return json.loads(config_path.read_text()) if config_path.exists() else {}
def provider():return json.loads(db_path.read_text()) if db_path.exists() else {'generation':0,'refreshes':0}
def save(value):db_path.write_text(json.dumps(value))
def now():return time.time()+float(settings().get('offset',0))
class Clock:
 def time(self):return now()
 def __getattr__(self,name):return getattr(time,name)
auth.time=Clock()
session_resume.get_optional_secret=lambda name,default=None:{'COSTERLY_FAST_RESUME_ENABLED':'true','COSTERLY_SESSION_SEAL_KEY':base64.urlsafe_b64encode(b'0'*32).decode()}.get(name,default)
def mint(n):
 payload=base64.urlsafe_b64encode(json.dumps({'sub':'fixture-user','email':'fixture@example.invalid','exp':int(now())+3600,'generation':n}).encode()).decode().rstrip('=')
 return SimpleNamespace(access_token='eyJhbGciOiJub25lIn0.'+payload+'.synthetic',refresh_token=f'synthetic-refresh-{n}',expires_at=int(now())+3600)
class Provider:
 def sign_in_with_password(self,credentials):
  data=provider();data['generation']+=1;data['signins']=data.get('signins',0)+1;save(data)
  config=settings()
  if config.get('build_after_signin'):
   config['build']=config['build_after_signin'];config_path.write_text(json.dumps(config))
  return SimpleNamespace(session=mint(data['generation']))
 def refresh_session(self,token):
  data=provider()
  if settings().get('revoked') or token!=f"synthetic-refresh-{data['generation']}":
   raise AuthApiError('Synthetic expired/reused token',400,'refresh_token_already_used')
  data['generation']+=1;data['refreshes']+=1;save(data)
  return SimpleNamespace(session=mint(data['generation']))
auth._auth_client=lambda:SimpleNamespace(auth=Provider())
auth.legal_consent_enabled=lambda:False
def access(token,**_):
 return auth.CompanyAccess('fixture-user','fixture@example.invalid','fixture-company','owner',token)
auth._company_access_via_rls=access
st.set_page_config(page_title='Auth resume fixture',layout='wide')
auth.recover_sign_in_submit_after_reconnect()
st.session_state._runtime_run_sequence=int(st.session_state.get('_runtime_run_sequence',0))+1
trace=new_runtime_trace(started_at=time.perf_counter(),session_state=st.session_state,requested_trace_id=st.query_params.get('obs_trace'),screen='upload',build_version=settings().get('build',LABOR_BUILD_VERSION))
if not auth.sync_browser_auth_session(trace_id=trace.trace_id,run_id=trace.run_id,run_sequence=st.session_state._runtime_run_sequence):st.stop()
current=auth.current_company_access(trace=trace)
if current is None:
 apply_auth_css()
 auth.render_login_or_signup(None)
 _signal_ready(trace,'login')
else:
 with st.container(key='costerly_header_controls'):st.button('Fixture rerun')
 st.markdown('<div class="upload-screen__hero">Authenticated Upload</div>',unsafe_allow_html=True)
 st.file_uploader('File',key='fixture_upload')
 st.markdown('<div data-auth-user="fixture-user">Signed in</div>',unsafe_allow_html=True)
 st.caption('restore: '+str(st.session_state.get('_browser_auth_sync_outcome')))
 _signal_ready(trace,'upload',company_id='fixture-company')
