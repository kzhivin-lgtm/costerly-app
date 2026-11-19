// Real wrapper/controller/auth component, with synthetic screen markup only.
import { reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
const source=readFileSync('cloudflare/index.html','utf8');
const initialBuild=source.match(/const BUILD_VERSION = "([^"]+)"/)[1];
const controller=readFileSync('ui/workflow_transition.js','utf8');
const auth=readFileSync('ui/browser_session_component/index.html','utf8').replace('<script src="session_storage.js"></script>','<script>'+readFileSync('ui/browser_session_component/session_storage.js','utf8')+'</script>');
const legacy=readFileSync(fixturePath('legacy_wrapper.html'),'utf8');
let serverBuild=initialBuild, publishedBuild=initialBuild, scenario='matching', screen='upload', deliveries=0, versionReads=0;
const coreServer=createServer((req,res)=>{
 if(req.url==='/auth')return res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(auth);
 const legacyCore=scenario==='old_core_wait'||(scenario==='old_core'&&deliveries===1);
 const trace=new URL(req.url,'http://127.0.0.1:8796').searchParams.get('obs_trace');
 const markup=`<!doctype html><body><div id="content"></div><iframe id="auth" src="/auth" hidden></iframe><script>
 ${controller}
 let sequence=0; window.acceptedUploads=0;window.coreLegacy=${JSON.stringify(legacyCore)};
 addEventListener('change',e=>{if(e.target.type==='file'){acceptedUploads++;top.postMessage({type:'costerly:rfq-upload-selected',source:'input-change',cycleId:'fixture-cycle'},'*');}});
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
  if(!window.coreLegacy)receipt.versionRefreshSafe=['upload','login'].includes(screen);
  const workflow=window.__costerlyWorkflowTransition||workflowTransitionController(window,receipt.traceId,'test-source',receipt);
  if(!workflow.ready(receipt)){top.postMessage(receipt,'*');workflow.announceBuild(receipt);}
 };
 render(${JSON.stringify(screen)});
 </script>`;
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(markup);
});
const wrapperServer=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 if(new URL(req.url,'http://localhost').pathname==='/version.json'){versionReads++;return res.writeHead(scenario==='unavailable'?503:200,{'Content-Type':'application/json'}).end(JSON.stringify({build:publishedBuild}));}
 if(new URL(req.url,'http://localhost').pathname!=='/')return res.writeHead(204).end();
 deliveries++;
 const outdated=['forever','guard_failure'].includes(scenario)||(['stale','legacy'].includes(scenario)&&deliveries===1);
 let html=scenario==='legacy'&&outdated?legacy:source;
 html=html.replace(/const BUILD_VERSION = "[^"]+"/,`const BUILD_VERSION = "${outdated?initialBuild.replace(/-b([0-9]{14})-/,(_,v)=>'-b'+String(BigInt(v)-1n)+'-'):publishedBuild}"`)
  .replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8796/?embed=true"');
 if(scenario==='no_ack')html=html.replace('event.data.workflowNavigationProtocol === 1','false');
 html=html.replace('<script>', '<script>window.fixtureWrapperBuild='+JSON.stringify(outdated?initialBuild.replace(/-b([0-9]{14})-/,(_,v)=>'-b'+String(BigInt(v)-1n)+'-'):publishedBuild)+';</script><script>');
 res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'}).end(html);
});
await Promise.all([new Promise(r=>coreServer.listen(8796,'127.0.0.1',r)),new Promise(r=>wrapperServer.listen(8797,'127.0.0.1',r))]);
const browser=await chromium.launch(chromeOptions), results=[];let lastPage=null;
const core=page=>page.frameLocator('#costerly-app-frame');
async function coreFrame(page){return (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();}
async function ready(page){
 await page.locator('iframe.is-ready').waitFor();
 await core(page).locator('[data-costerly-render-id]').waitFor({state:'attached'});
}
async function matched(page){
 await page.waitForFunction(build=>window.fixtureWrapperBuild===build,publishedBuild);
 await ready(page);
}
const nextBuild=(n=1)=>initialBuild.replace(/-b([0-9]{14})-/,(_,stamp)=>'-b'+String(BigInt(stamp)+BigInt(n))+'-');
async function detect(page){
 await (await coreFrame(page)).evaluate(build=>render(document.querySelector('[data-costerly-screen]').dataset.costerlyScreen,build),serverBuild);
 await page.evaluate(()=>new Promise(requestAnimationFrame));
}
async function boot(mode='matching',initialScreen='upload'){
 scenario=mode;screen=initialScreen;deliveries=0;versionReads=0;serverBuild=publishedBuild=initialBuild;
 const page=await browser.newPage();lastPage=page;page.setDefaultTimeout(10000);
 page.on('pageerror',e=>{throw e;});
 if(mode==='guard_failure')await page.addInitScript(()=>{
  if(window!==top)return;
  const original=Storage.prototype.setItem;
  Storage.prototype.setItem=function(key,value){if(key==='costerly.deploy-refresh.v1')throw Error('storage blocked');return original.call(this,key,value);};
 });
 await page.goto('http://127.0.0.1:8797/');
 await core(page).locator('[data-costerly-render-id]').waitFor({state:'attached'});
 return page;
}
function passed(message){results.push(message);console.log('Passed scenario',results.length,message);}
try{
 let page=await boot();await matched(page);assert.equal(deliveries,1);
 let frame=await coreFrame(page);await frame.waitForFunction(()=>window.restoredSession!==undefined);
 const tokens={access_token:'synthetic-access',refresh_token:'synthetic-refresh',expires_at:4102444800};
 await frame.evaluate(tokens=>storeAuth(tokens),tokens);
 await frame.waitForFunction(()=>sessionStorage.getItem('costerly.supabase.session.v1'));
 scenario='stale';deliveries=0;
 await page.goto('http://127.0.0.1:8797/');await matched(page);frame=await coreFrame(page);
 await frame.waitForFunction(()=>window.restoredSession?.access_token==='synthetic-access');
 assert.deepEqual(await frame.evaluate(()=>restoredSession),tokens);assert.equal(deliveries,2);
 passed('One Core build event forced one reload; browser auth tokens retained');await page.close();
 for(const state of ['upload','login']){
  page=await boot('legacy',state);await matched(page);assert.equal(deliveries,2);
  passed('Already-open legacy wrapper migrated from '+state+' without an auth prerequisite');await page.close();
 }
 page=await boot('old_core_wait');await matched(page);assert.equal(deliveries,1);frame=await coreFrame(page);
 await frame.evaluate(()=>{window.coreLegacy=false;render('upload');});
 await ready(page);assert.equal(deliveries,1);
 passed('Current published wrapper does not reload or gate Upload on an older Core build');await page.close();
 for(const state of ['processing','object_detail']){
  page=await boot('matching',state);await matched(page);frame=await coreFrame(page);
  if(state==='object_detail')await core(page).locator('#draft').fill('unsaved 42');
  publishedBuild=serverBuild=nextBuild();await detect(page);
  assert.equal(deliveries,1);
  if(state==='object_detail')assert.equal(await core(page).locator('#draft').inputValue(),'unsaved 42');
  screen='upload';await frame.evaluate(build=>render('upload',build),serverBuild);await matched(page);
  assert.equal(deliveries,2);passed('Published update deferred in '+state+', then reloaded on empty Upload');await page.close();
 }
 page=await boot();await matched(page);frame=await coreFrame(page);
 const chooser=page.waitForEvent('filechooser');await core(page).locator('input[type=file]').click();const selected=await chooser;
 publishedBuild=serverBuild=nextBuild(2);await detect(page);assert.equal(deliveries,1);
 await selected.setFiles({name:'test.pdf',mimeType:'application/pdf',buffer:Buffer.from('synthetic upload')});
 await frame.waitForFunction(()=>acceptedUploads===1);assert.equal(deliveries,1);
 await frame.evaluate(build=>render('processing',build),serverBuild);await ready(page);assert.equal(deliveries,1);
 screen='upload';await frame.evaluate(build=>render('upload',build),serverBuild);await matched(page);assert.equal(deliveries,2);
 passed('File picker, accepted transfer and current calculation survived the pending update');await page.close();
 page=await boot('forever');await page.getByRole('button',{name:'Reload page',exact:true}).waitFor();
 assert.equal(deliveries,2);assert.notEqual(await page.locator('#costerly-app-frame').getAttribute('inert'),null);
 await detect(page);assert.equal(deliveries,2);assert.equal(versionReads,0);
 scenario='matching';const navigation=page.waitForEvent('framenavigated',{predicate:f=>f===page.mainFrame()});
 await page.getByRole('button',{name:'Reload page',exact:true}).click();await navigation;await matched(page);assert.equal(deliveries,3);
 passed('One automatic attempt, no reload loop, explicit retry recovered');await page.close();
 for(const mode of ['no_ack','unavailable']){
  page=await boot(mode);await matched(page);
  await core(page).locator('input[type=file]').setInputFiles({name:'test.pdf',mimeType:'application/pdf',buffer:Buffer.from('synthetic upload')});
  await (await coreFrame(page)).waitForFunction(()=>acceptedUploads===1);assert.equal(deliveries,1);
  passed(mode+': ordinary upload needs no version/auth precheck');await page.close();
 }
 page=await boot('guard_failure');await page.getByRole('button',{name:'Reload page',exact:true}).waitFor();assert.equal(deliveries,1);
 passed('Unavailable reload-guard storage offered manual retry without a loop');await page.close();
 assert.equal(versionReads,0,'No periodic or startup version-file request');
 writeFileSync(reportPath('version-refresh.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}catch(error){
 if(lastPage&&!lastPage.isClosed()){await lastPage.screenshot({path:reportPath('version-refresh-failure.png')}).catch(()=>{});console.error({scenario,deliveries,body:await lastPage.locator('body').innerText().catch(()=>'(navigating)')});}
 throw error;
}finally{await browser.close();await Promise.all([new Promise(r=>coreServer.close(r)),new Promise(r=>wrapperServer.close(r))]);}
