// Real wrapper/controller/auth component, with synthetic screen markup only.
import { reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
const source=readFileSync('cloudflare/index.html','utf8');
const initialBuild=source.match(/const BUILD_VERSION = "([^"]+)"/)[1];
const controller=readFileSync('ui/workflow_transition.js','utf8');
const auth=readFileSync('ui/browser_session_component/index.html','utf8');
const legacy=readFileSync(fixturePath('legacy_wrapper.html'),'utf8');
let serverBuild=initialBuild, scenario='matching', screen='upload', deliveries=0;
const coreServer=createServer((req,res)=>{
 if(req.url==='/auth')return res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(auth);
 const legacyCore=scenario==='old_core_wait'||(scenario==='old_core'&&deliveries===1);
 const trace=new URL(req.url,'http://127.0.0.1:8796').searchParams.get('obs_trace');
 const markup=`<!doctype html><body><div id="content"></div><iframe id="auth" src="/auth" hidden></iframe><script>
 ${controller}
 let sequence=0; window.acceptedUploads=0;window.coreLegacy=${JSON.stringify(legacyCore)};
 addEventListener('change',e=>{if(e.target.type==='file')acceptedUploads++});
 window.restoredSession=undefined;
 addEventListener('message',e=>{
  if(e.source===document.querySelector('#auth').contentWindow&&e.data.type==='streamlit:setComponentValue')
   window.restoredSession=JSON.parse(e.data.value).session;
 });
 const authArgs=args=>document.querySelector('#auth').contentWindow.postMessage({type:'streamlit:render',args},location.origin);
 window.storeAuth=session=>authArgs({action:'store',session});
 document.querySelector('#auth').onload=()=>authArgs({action:'read',requestId:'restore'});
 window.render=(screen,build=${JSON.stringify(serverBuild)})=>{
  const id='ready-'+(++sequence);
  const keep=document.querySelector('[data-costerly-screen]')?.dataset.costerlyScreen===screen;
  if(!keep)document.querySelector('#content').innerHTML='<div class="stApp"><div class="st-key-costerly_header_controls"><button>New Estimate</button></div>'+
    '<div data-costerly-render-id="'+id+'" data-costerly-screen="'+screen+'"></div>'+
    (screen==='upload'?'<div class="upload-screen__hero">Upload</div><div data-testid="stFileUploader"><input type="file"><div data-testid="stFileUploaderDropzone">Drop file</div></div>':
     screen==='object_detail'?'<div class="object-detail-title">Object</div><div class="object-detail-final"></div><div class="object-detail-footer-actions"></div><input id="draft" value="saved">':'<div id="processing">Calculating</div>')+'</div>';
  document.querySelector('[data-costerly-render-id]').dataset.costerlyRenderId=id;
  const receipt={type:'costerly:app-ready',traceId:${JSON.stringify(trace)},runId:id,screen,
   metrics:{server_build_version:window.coreLegacy?'previous-core':build},route:{},workflowNavigationProtocol:1};
  if(!window.coreLegacy)receipt.versionRefreshSafe=screen==='upload';
  const workflow=window.__costerlyWorkflowTransition||workflowTransitionController(window,receipt.traceId,'test-source',receipt);
  if(!workflow.ready(receipt))top.postMessage(receipt,'*');
 };
 render(${JSON.stringify(screen)});
 </script>`;
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(markup);
});
const wrapperServer=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 if(new URL(req.url,'http://localhost').pathname!=='/')return res.writeHead(204).end();
 deliveries++;
 const outdated=scenario==='forever'||(['stale','legacy'].includes(scenario)&&deliveries===1);
 let html=scenario==='legacy'&&outdated?legacy:source;
 html=html.replace(/const BUILD_VERSION = "[^"]+"/,`const BUILD_VERSION = "${outdated?'previous-wrapper':serverBuild}"`)
  .replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8796/?embed=true"');
 if(scenario==='no_ack')html=html.replace('event.data.workflowNavigationProtocol === 1','false');
 html=html.replace('<script>', '<script>window.fixtureWrapperBuild='+JSON.stringify(outdated?'previous-wrapper':serverBuild)+';</script><script>');
 res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'}).end(html);
});
await Promise.all([new Promise(r=>coreServer.listen(8796,'127.0.0.1',r)),new Promise(r=>wrapperServer.listen(8797,'127.0.0.1',r))]);
const browser=await chromium.launch(chromeOptions), results=[];let lastPage=null;
const core=page=>page.frameLocator('#costerly-app-frame');
async function coreFrame(page){return (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();}
async function matched(page){
 await page.waitForFunction(build=>window.fixtureWrapperBuild===build,serverBuild);
 await page.waitForFunction(()=>document.querySelector('#costerly-app-frame')?.classList.contains('is-ready'));
 await (await coreFrame(page)).waitForFunction(()=>window.__costerlyWorkflowTransition?.versionMatched());
}
async function boot(mode='matching',initialScreen='upload'){
 scenario=mode;screen=initialScreen;deliveries=0;serverBuild=initialBuild;
 const page=await browser.newPage();lastPage=page;page.setDefaultTimeout(10000);
 page.on('pageerror',e=>{throw e;});
 await page.goto('http://127.0.0.1:8797/');
 await core(page).locator('[data-costerly-render-id]').waitFor({state:'attached'});
 return page;
}
try{
 let page=await boot();await matched(page);
 assert.equal(deliveries,1);
 let frame=await coreFrame(page);
 await frame.waitForFunction(()=>window.restoredSession!==undefined);
 const tokens={access_token:'synthetic-access',refresh_token:'synthetic-refresh',expires_at:4102444800};
 await frame.evaluate(tokens=>storeAuth(tokens),tokens);
 await frame.waitForFunction(()=>sessionStorage.getItem('costerly.supabase.session.v1'));
 scenario='stale';deliveries=0;
 await page.goto('http://127.0.0.1:8797/');
 await matched(page);frame=await coreFrame(page);
 await frame.waitForFunction(()=>window.restoredSession?.access_token==='synthetic-access');
 assert.deepEqual(await frame.evaluate(()=>restoredSession),tokens);
 assert.equal(deliveries,2);
 console.log('Passed scenario',results.length+1);results.push('Mismatched wrapper reloaded once; production auth component restored both synthetic tokens from existing tab storage');
 await page.close();
 page=await boot('legacy');
 await page.waitForFunction(()=>document.querySelector('#costerly-app-frame')?.classList.contains('is-ready'));
 // The old wrapper replies without a build, then its existing reload command migrates it.
 await core(page).locator('[data-costerly-render-id]').waitFor({state:'attached'});
 await matched(page);assert.equal(deliveries,2);
 console.log('Passed scenario',results.length+1);results.push('Unmodified legacy wrapper migrated using its supported correlated reload');await page.close();
 page=await boot('old_core');await matched(page);assert.equal(deliveries,2);
 console.log('Passed scenario',results.length+1);results.push('New wrapper safely migrated a Core without the refresh protocol');await page.close();
 page=await boot('old_core_wait');
 await page.getByRole('button',{name:'Reload page',exact:true}).waitFor();
 assert.match(await page.locator('#app-loading-mask').innerText(),/The app update is not ready yet/);
 assert.equal(deliveries,2);frame=await coreFrame(page);
 await frame.evaluate(()=>render('login'));
 await page.locator('#app-loading-mask.is-hidden').waitFor({state:'attached'});
 assert.equal(await page.locator('#costerly-app-frame').getAttribute('inert'),null);
 await frame.evaluate(()=>{window.coreLegacy=false;render('upload');});
 await matched(page);
 assert.equal(await page.locator('#costerly-app-frame').getAttribute('inert'),null);
 assert.equal(await page.locator('#app-loading-mask').evaluate(node=>getComputedStyle(node).pointerEvents),'none');
 assert.equal(deliveries,2);
 console.log('Passed scenario',results.length+1);results.push('Auth expiry released the legacy update cover; later matching Core restored Upload without another reload');await page.close();
 for(const state of ['processing','object_detail']){
  page=await boot('stale',state);frame=await coreFrame(page);
  await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  if(state==='object_detail')await core(page).locator('#draft').fill('unsaved 42');
  await frame.evaluate(()=>render(document.querySelector('[data-costerly-screen]').dataset.costerlyScreen));
  assert.equal(deliveries,1);
  if(state==='object_detail'){
   assert.equal(await core(page).locator('#draft').inputValue(),'unsaved 42');
  }
  screen='upload';await frame.evaluate(()=>render('upload'));
  await matched(page);assert.equal(deliveries,2);
  console.log('Passed scenario',results.length+1);results.push(`Mismatch deferred in ${state}, then one reload on empty Upload`);await page.close();
 }
 page=await boot();await matched(page);frame=await coreFrame(page);
 const chooser=page.waitForEvent('filechooser');await core(page).locator('input[type=file]').click();
 const selected=await chooser;
 serverBuild='synthetic-next-core';
 await frame.evaluate(build=>render('upload',build),serverBuild);
 await frame.waitForFunction(()=>!window.__costerlyWorkflowTransition.versionMatched());
 assert.equal(deliveries,1);
 await selected.setFiles({name:'test.pdf',mimeType:'application/pdf',buffer:Buffer.from('synthetic upload')});
 await frame.waitForFunction(()=>acceptedUploads===1);assert.equal(deliveries,1);
 assert.equal(await core(page).locator('input[type=file]').evaluate(input=>{
  const event=new MouseEvent('click',{bubbles:true,cancelable:true});input.dispatchEvent(event);return event.defaultPrevented;
 }),true);
 await frame.evaluate(build=>render('processing',build),serverBuild);assert.equal(deliveries,1);
 screen='upload';await frame.evaluate(build=>render('upload',build),serverBuild);
 await matched(page);assert.equal(deliveries,2);
 console.log('Passed scenario',results.length+1);results.push('Open file picker and accepted file transfer survived a server-build change');await page.close();
 for(const mode of ['forever','no_ack']){
  page=await boot(mode);
  if(mode==='no_ack'){
   assert.equal(await core(page).locator('input[type=file]').evaluate(input=>{
    const event=new MouseEvent('click',{bubbles:true,cancelable:true});input.dispatchEvent(event);return event.defaultPrevented;
   }),true);
   await core(page).getByText('Checking app version…',{exact:true}).waitFor();
  }
  await core(page).getByText('The app update is not ready yet. Reload to retry.',{exact:true}).waitFor();
  const count=deliveries;assert.equal(count,mode==='forever'?2:1);
  if(mode==='forever'){
   const active=await coreFrame(page);await active.evaluate(()=>render('login'));
   await core(page).locator('#costerly-workflow-transition').waitFor({state:'hidden'});
   await core(page).locator('[data-costerly-screen="login"]').waitFor({state:'attached'});
   await active.evaluate(()=>render('upload'));
   await core(page).getByRole('button',{name:'Reload page',exact:true}).waitFor();
  }
  assert.equal(await core(page).locator('input[type=file]').evaluate(input=>{
   const event=new Event('drop',{bubbles:true,cancelable:true});input.dispatchEvent(event);return event.defaultPrevented;
  }),true);
  assert.equal(await (await coreFrame(page)).evaluate(()=>acceptedUploads),0);
  await new Promise(r=>setTimeout(r,250));assert.equal(deliveries,count);
  await page.screenshot({path:reportPath('version-refresh-'+mode+'.png')});
  scenario='matching';const navigation=page.waitForEvent('framenavigated',{predicate:f=>f===page.mainFrame()});
  await core(page).getByRole('button',{name:'Reload page',exact:true}).click();await navigation;
  await matched(page);assert.equal(deliveries,count+1);
  console.log('Passed scenario',results.length+1);results.push(`${mode}: blocked new upload, no reload loop, manual retry recovered`);await page.close();
 }
 page=await boot();await matched(page);frame=await coreFrame(page);
 await frame.evaluate(()=>{
  const original=Storage.prototype.setItem;
  Storage.prototype.setItem=function(key,value){if(key==='costerly.version-refresh.v1')throw Error('storage blocked');return original.call(this,key,value);};
 });
 serverBuild='synthetic-storage-case';await frame.evaluate(build=>render('upload',build),serverBuild);
 await core(page).getByRole('button',{name:'Reload page',exact:true}).waitFor();assert.equal(deliveries,1);
 console.log('Passed scenario',results.length+1);results.push('Unavailable reload-guard storage failed safely with manual recovery');await page.close();
 writeFileSync(reportPath('version-refresh.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}catch(error){
 if(lastPage&&!lastPage.isClosed()){await lastPage.screenshot({path:reportPath('version-refresh-failure.png')});console.error({scenario,deliveries,body:await lastPage.locator('body').innerText()});}
 throw error;
}finally{await browser.close();await Promise.all([new Promise(r=>coreServer.close(r)),new Promise(r=>wrapperServer.close(r))]);}
