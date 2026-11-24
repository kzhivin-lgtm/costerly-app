// Production handlers plus the exact shipped V1.2.23 wrapper (582343a).
import {statePath,reportPath,chromeOptions} from './support.mjs';
import {readFileSync,writeFileSync} from 'node:fs';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const current=readFileSync('cloudflare/index.html','utf8');
const historical=readFileSync('tests/ui/fixtures/preprotocol_wrapper.html','utf8');
assert.equal(createHash('sha256').update(historical).digest('hex'),'01e0f3a1c9415ac899943b5d3277d9b47efef91d8e96bbcc6e649da114c8c519');
const expected=current.match(/const BUILD_VERSION = "([^"]+)"/)[1];
let mode='',loads=0;const records=[];
const server=createServer(async(req,res)=>{
 if(req.url.startsWith('/api/')){
  let body='';for await(const chunk of req)body+=chunk;
  if(body){const parsed=JSON.parse(body);records.push(...(Array.isArray(parsed)?parsed:parsed.events));}
  return res.writeHead(202).end();
 }
 if(new URL(req.url,'http://localhost').pathname!=='/')return res.writeHead(204).end();
 loads++;
 let html=mode==='v1223'&&loads===1?historical:current;
 if(mode==='no_ack'&&loads===1)html=html.replace('event.data.workflowNavigationProtocol === 1','false');
 if(mode==='wrong_protocol'&&loads===1)html=html.replace('protocol: 1, traceId,','protocol: 2, traceId,');
 html=html.replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}).end(html);
});
await new Promise(resolve=>server.listen(8797,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions),report=[];
let page;
async function boot(next,route=''){
 mode=next;loads=0;records.length=0;
 writeFileSync(statePath('scenario.json'),'{}');
 page=await browser.newPage({viewport:{width:1280,height:900}});page.setDefaultTimeout(12000);
 await page.goto('http://127.0.0.1:8797/'+route);
 await page.locator('iframe.is-ready').waitFor();
 const core=page.frameLocator('#costerly-app-frame');
 const frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 await frame.waitForFunction(()=>window.__costerlyWorkflowTransition);
 assert.equal(await frame.evaluate(()=>__costerlyWorkflowTransition.enabled()),false);
 return {core,frame};
}
async function recovery(core,control){
 const marker=await core.locator('[data-costerly-render-id]').getAttribute('data-costerly-render-id');
 await control.click();
 await core.getByRole('dialog',{name:'App update required'}).waitFor();
 assert.equal(await core.locator('[data-costerly-render-id]').getAttribute('data-costerly-render-id'),marker,
              'Unconfirmed navigation must not reach the native callback');
 const covered=await core.locator('#costerly-workflow-recovery').evaluate(node=>
  [[10,10],[innerWidth/2,innerHeight/2],[innerWidth-10,innerHeight-10]].every(([x,y])=>node.contains(document.elementFromPoint(x,y))));
 assert(covered,'Recovery must cover the full screen');
 const typography=await core.locator('#costerly-workflow-recovery > .costerly-workflow-status').evaluate(n=>{
  const ref=document.createElement('span');ref.className='costerly-workflow-status';document.body.append(ref);
  const a=getComputedStyle(n),b=getComputedStyle(ref);
  const same=['fontFamily','fontSize','fontWeight','letterSpacing','lineHeight','color'].every(k=>a[k]===b[k]);
  ref.remove();return same;
 });
 assert.equal(typography,true,'Update recovery uses the shared loading typography');
}
try{
 for(const fixture of ['v1223','no_ack','wrong_protocol']){
  const {core,frame}=await boot(fixture);
  await recovery(core,core.getByRole('button',{name:'Profile',exact:true}));
  await core.getByRole('button',{name:'Keep working',exact:true}).click();
  await recovery(core,core.getByRole('button',{name:'Last Estimate',exact:true}));
  await core.getByRole('button',{name:'Keep working',exact:true}).click();
  await recovery(core,core.getByRole('button',{name:'All Projects',exact:true}));
  await frame.evaluate(()=>sessionStorage.setItem('costerly.supabase.session.v1',JSON.stringify({access_token:'synthetic-retained'})));
  await Promise.all([
   page.waitForEvent('framenavigated',{predicate:f=>f===page.mainFrame()}),
   core.getByRole('link',{name:'Update app',exact:true}).click(),
  ]);
  await page.locator('iframe.is-ready').waitFor();
  const next=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  await next.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  assert.equal(loads,2,'Exactly one user-requested outer reload');
  assert.equal(await next.evaluate(()=>JSON.parse(sessionStorage.getItem('costerly.supabase.session.v1')).access_token),'synthetic-retained');
  assert.equal(await page.locator('meta[name="costerly-wrapper-version"]').getAttribute('content'),expected);
  const loggedEnd=page.waitForResponse(response=>response.url().includes('/api/runtime-events')&&
   [].concat(response.request().postDataJSON()).some(e=>e.event_name==='browser.workflow_protection'&&e.metadata.phase==='cover_end'));
  await core.getByRole('button',{name:'Profile',exact:true}).click();
  await next.waitForFunction(()=>!__costerlyWorkflowTransition.busy()&&document.querySelector('[data-costerly-screen="account"]'));
  await loggedEnd;
  const phases=records.filter(x=>x.event_name==='browser.workflow_protection').map(x=>x.metadata.phase);
  assert(phases.includes('compatible')&&phases.includes('cover_start')&&phases.includes('cover_end'),JSON.stringify(phases));
  assert(records.some(x=>x.event_name==='browser.transition_ready'&&x.metadata.covered===true));
  report.push({fixture,blocked:true,outerReloads:loads-1,sessionRetained:true,normalCoverLogged:true});
  await page.close();
 }
 let {core,frame}=await boot('v1223','?screen=objects&route_token=estimate1234');
 await recovery(core,core.getByRole('link',{name:/^(Review|Done)$/i}));
 await core.getByRole('button',{name:'Keep working',exact:true}).click();
 await recovery(core,core.getByRole('button',{name:/^Back to file review$/i}));
 report.push({fixture:'saved-object-links',documentNavigationAndFooterBlocked:true});
 await page.close();
 ({core,frame}=await boot('no_ack','?screen=account'));
 const tabs=core.locator('.st-key-company_profile_tab [role="tab"]');
 const selected=await core.locator('.st-key-company_profile_tab [role="tab"][aria-selected="true"]').innerText();
 await recovery(core,tabs.nth(1));
 assert.equal(await core.locator('.st-key-company_profile_tab [role="tab"][aria-selected="true"]').innerText(),selected);
 await core.getByRole('button',{name:'Keep working',exact:true}).click();
 await tabs.first().focus();
 await tabs.first().press('ArrowRight');
 await core.getByRole('dialog',{name:'App update required'}).waitFor();
 assert.equal(await core.locator('.st-key-company_profile_tab [role="tab"][aria-selected="true"]').innerText(),selected);
 await core.getByRole('button',{name:'Keep working',exact:true}).click();
 // Existing edits remain live when the owner declines an explicit reload.
 const field=core.locator('.company-metrics-monthly-input').first();
 await field.fill('999');
 await recovery(core,core.getByRole('button',{name:'All Projects',exact:true}));
 page.once('dialog',dialog=>dialog.dismiss());
 await core.getByRole('link',{name:'Update app',exact:true}).click();
 assert.equal(loads,1);
 await core.getByRole('button',{name:'Keep working',exact:true}).click();
 assert.match(await field.innerText(),/999/);
 report.push({fixture:'profile-tab-and-draft',nativeSelectionBlocked:true,cancelledReloadRetainedDraft:true});
 await page.close();
 ({core,frame}=await boot('no_ack'));
 await recovery(core,core.getByRole('button',{name:'Profile',exact:true}));
 const retained=await frame.evaluate(()=>{
  const previous=window.__costerlyWorkflowTransition;
  const node=document.querySelector('#costerly-workflow-recovery');
  const receipt={screen:'upload',traceId:previous.traceId,runId:document.querySelector('[data-costerly-render-id]').dataset.costerlyRenderId};
  const selected=workflowTransitionController(window,previous.traceId,'next-controller-revision',receipt);
  return previous===selected&&window.__costerlyWorkflowTransition===previous&&node.isConnected&&previous.busy();
 });
 assert(retained,'A controller upgrade must not remove an unresolved recovery screen');
 report.push({fixture:'controller-upgrade',recoveryRetained:true});
 await page.close();
 ({core,frame}=await boot('no_ack'));
 await recovery(core,core.getByRole('button',{name:'Profile',exact:true}));
 await frame.evaluate(()=>{const marker=document.createElement('div');marker.className='objects-progress-status';document.body.append(marker);});
 await core.getByRole('link',{name:'Update app',exact:true}).click();
 await core.getByText('Finish the current upload or calculation before updating.').waitFor();
 assert.equal(loads,1);
 await frame.evaluate(()=>document.querySelector('.objects-progress-status').remove());
 await frame.evaluate(()=>{const dt=new DataTransfer();dt.items.add(new File(['fixture'],'test.pdf'));document.querySelector('input[type="file"]').files=dt.files;});
 await core.getByRole('link',{name:'Update app',exact:true}).click();
 assert.equal(loads,1);
 await frame.evaluate(()=>{document.querySelector('input[type="file"]').files=new DataTransfer().files;const saving=document.createElement('button');saving.textContent='SAVING...';document.body.append(saving);});
 await core.getByRole('link',{name:'Update app',exact:true}).click();
 await core.getByText('Finish the current save before updating.').waitFor();
 assert.equal(loads,1);
 report.push({fixture:'active-work',calculationSelectedUploadAndSaveRetained:true});
 writeFileSync(reportPath('compatibility-recovery.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
}catch(error){
 console.error({mode,loads,events:records.filter(x=>x.event_name.startsWith('browser.transition')||x.event_name==='browser.workflow_protection').map(x=>({event:x.event_name,metadata:x.metadata})),state:(await page?.frameLocator('#costerly-app-frame').locator('body').innerText().catch(()=>'(no frame)')).slice(-600)});
 await page?.screenshot({path:reportPath('compatibility-recovery-failure.png')}).catch(()=>{});
 throw error;
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
