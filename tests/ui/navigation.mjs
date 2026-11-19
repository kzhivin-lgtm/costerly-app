import { statePath, reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
const lag=statePath('slow-objects-read');
const journal=statePath('browser-journal');
const config=statePath('scenario.json');
const expiry=statePath('auth-expired');
const old=readFileSync(fixturePath('legacy_wrapper.html'),'utf8');
const current=readFileSync('cloudflare/index.html','utf8');
const wrapper=html=>html.replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
const server=createServer((req,res)=>{
 const path=new URL(req.url,'http://127.0.0.1:8797');
 if(path.pathname.startsWith('/api/')) return res.writeHead(202).end();
 const html=path.searchParams.has('old')?old:current;
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(wrapper(html));
});
await new Promise(resolve=>server.listen(8797,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions);
const report={};
const expected='estimate-ui-saved';
rmSync(journal,{force:true});
try {
 for(const cfg of [
  {name:'current_wrapper',width:1280,height:900},
  {name:'open_old_wrapper',width:1280,height:900,oldWrapper:true},
  {name:'mobile',width:390,height:844},
 ]){
  writeFileSync(config,JSON.stringify({delay:cfg.lag?{projects:1.25,account:1.25,admin:1.25}:{}}));
  rmSync(expiry,{force:true});
  const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height}});
  page.setDefaultTimeout(9500);
  const errors=[];
  page.on('pageerror',err=>errors.push(err.message));
  await page.addInitScript(()=>{
   if(window!==top)return;
   window.navMessages=[];
   addEventListener('message',ev=>{
    if(['costerly:app-ready','costerly:transition-click','costerly:transition-failed',
        'costerly:transition-styled'].includes(ev.data?.type)) {
     window.navMessages.push({type:ev.data.type,screen:ev.data.screen,id:ev.data.transitionId,
                              runId:ev.data.runId,covered:ev.data.workflowNavigation,
                              transition:ev.data.transition});
    }
   });
  });
  await page.goto('http://127.0.0.1:8797/'+(cfg.oldWrapper?'?old':''));
  const frame=await (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  const core=page.frameLocator('#costerly-app-frame');
  await core.getByRole('button',{name:'Last Estimate',exact:true}).waitFor();
  await page.locator('iframe.is-ready').waitFor();
  if(!cfg.old) await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  const actions=[];
  const button=name=>core.getByRole('button',{name,exact:true});
  const link=name=>core.getByRole('link',{name,exact:true});
  const openObject=()=>core.getByRole('link',{name:/^(Done|Review)$/i});
  async function move(label, loc, screen){
   const messagesAt=await page.evaluate(()=>navMessages.length);
   const oldId=await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
   await frame.evaluate(()=>{
    const guard='#costerly-workflow-transition';
    const roots={upload:'.upload-screen__hero',file_review:'.file-review-detected-title',
                 objects:'.objects-pricing-table',object_detail:'.object-detail-title',
                 projects:'.projects-title',account:'.company-profile-heading',admin:'.platform-admin-heading'};
    const visible=node=>node.getClientRects().length>0 && getComputedStyle(node).visibility==='visible';
    let stop=false;
    const frames=[];
    window.__stopMeasurement=()=>{stop=true;return frames;};
    const start=performance.now();
    function sample(){
     if(stop)return;
     const screens=Object.keys(roots).filter(name=>
       [...document.querySelectorAll(roots[name])].some(visible));
     const cover=document.querySelector(guard);
     const covered=cover && [[10,10],[innerWidth/2,innerHeight/2],[innerWidth-10,innerHeight-10]].every(
       ([x,y])=>cover.contains(document.elementFromPoint(x,y)));
     frames.push({ms:Math.round(performance.now()-start),cover:Boolean(covered),screens});
     requestAnimationFrame(sample);
    }
    sample();
   });
   const profileTab=label.startsWith('Profile tab ');
   if(profileTab)await frame.evaluate(()=>window.__profileHeader=document.querySelector('.company-profile-heading'));
   await loc.click();
   const ready=core.locator('[data-costerly-screen="'+screen+'"]:not([data-costerly-render-id="'+oldId+'"])');
   await ready.waitFor({state:'attached'});
   if(!cfg.old) await page.waitForFunction(({messagesAt,screen})=>
     navMessages.slice(messagesAt).some(x=>x.type==='costerly:app-ready'&&x.id&&x.screen===screen),
     {messagesAt,screen});
   await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
   const samples=await frame.evaluate(()=>window.__stopMeasurement());
   const {events,covered} = await page.evaluate(messagesAt=>{
    const events=navMessages.slice(messagesAt);
    return {events,covered:events.filter(x=>x.type==='costerly:transition-click'&&x.covered)};
   },messagesAt);
   const counts={
    transition:label, visibleMs:samples.at(-1)?.ms, frames:samples.length, coveredFrames:samples.filter(x=>x.cover).length,
    uncoveredMixed:samples.filter(x=>!x.cover&&x.screens.length>1).length,
   };
   if(!cfg.old){
    assert.equal(covered.length,1,JSON.stringify(events));
    const completions=events.filter(x=>x.type==='costerly:app-ready'&&x.id===covered[0].id);
    // postReady may announce unrelated navigation readiness. A covered
    // transition alone must provide exactly one completion under its ID.
    assert.equal(completions.length,1);
    assert.equal(counts.uncoveredMixed,0,JSON.stringify(samples));
    if(profileTab){
     assert.equal(counts.coveredFrames,0);
     assert.ok(await frame.evaluate(()=>window.__profileHeader===document.querySelector('.company-profile-heading')));
    }else assert.ok(counts.coveredFrames>0,JSON.stringify(samples));
    assert.ok(!(await frame.evaluate(()=>document.querySelector('.stMain').scrollTop)));
   } else assert.equal(covered.length,0);
   actions.push(counts);
   console.log(cfg.name, label, JSON.stringify(counts));
  }


  await move('Open Profile before restart',button('Profile'),'account');
  await move('Clear workflow URL with New Estimate',button('New Estimate'),'upload');
  assert.ok(!new URL(frame.url()).searchParams.has('obs_trace'));
  const browserTrace=await frame.evaluate(()=>window.__costerlyWorkflowTransition.traceId);
  writeFileSync(config,JSON.stringify({restart_once:true}));
  await move('Open Projects after server restart',button('Projects'),'projects');
  assert.equal(await frame.evaluate(()=>window.__costerlyWorkflowTransition.traceId),browserTrace);
  await move('Open prepared Profile',button('Profile'),'account');
  for(const name of ['Machinery','Pricing Cost','Labor Costs','Contacts','Bank Details','Users','Overhead Expenses','Price Lists']){
   await move('Profile tab '+name,core.getByRole('tab',{name,exact:true}),'account');
  }
  await move('Profile to Admin',button('Admin'),'admin');
  await move('Admin to Projects',button('Projects'),'projects');
  await move('Projects to Last Estimate',button('Last Estimate'),'file_review');
  const savedCrop=await core.locator('.file-review-preview-box img').getAttribute('src');
  assert.ok(savedCrop?.startsWith('data:image/svg+xml;base64,'));
  const cont=()=>core.getByRole('button',{name:/^continue to objects estimation$/i});
  await move('Continue saved estimate',cont(),'objects');
  await move('Review saved card',openObject(),'object_detail');
  assert.equal(await core.locator('.object-detail-preview-image').getAttribute('src'),savedCrop);
  assert.ok(await core.locator('.object-detail-preview-image').evaluate(img=>img.complete&&img.naturalWidth>0));
  assert.match(await core.locator('.object-detail-final').innerText(),/₪1[\s,]?000/);
  await move('Card to New Estimate',button('New Estimate'),'upload');
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  report[cfg.name]=actions;
  await page.close();
 }
 const calls=readFileSync(journal,'utf8');
 assert.ok(calls.includes('objects '+expected));
 assert.ok(!calls.includes('ERROR'));
 writeFileSync(reportPath('navigation.json'),JSON.stringify(report,null,2));
 console.log('Same saved estimate and zero Parts Check launches in all three browser routes.');
} catch(error) {
 for (const context of browser.contexts()) for (const page of context.pages()) {
  await page.screenshot({path:reportPath('navigation-failure.png')}).catch(()=>{});
 }
 for(const context of browser.contexts()) for(const page of context.pages()){
  console.log('messages',JSON.stringify(await page.evaluate(()=>navMessages.slice(-9)).catch(()=>[])));
  for(const frame of page.frames()) if(frame.url().startsWith('http://127.0.0.1')) {
   console.log(frame.url(), (await frame.locator('body').innerText().catch(()=>'' )).slice(0,900));
   console.log('DOM',await frame.evaluate(()=>JSON.stringify({
    markers:[...document.querySelectorAll('[data-costerly-render-id]')].map(x=>x.outerHTML),
    stale:[...document.querySelectorAll('[data-stale="true"]')].map(x=>[x.getAttribute('data-testid'),x.getAttribute('class'),x.innerText.slice(0,30)]).slice(0,15),
    predicates:['.file-review-detected-title','.file-review-summary-card-marker','.st-key-costerly_header_controls button'].map(s=>[s,!!document.querySelector(s)]),
    button:[...document.querySelectorAll('button')].filter(x=>x.innerText.toLowerCase().includes('continue to')).map(x=>[x.innerText,x.disabled]),
    frames:[...document.querySelectorAll('iframe')].map(x=>[x.title,x.src.slice(0,120)]).slice(0,20)
   })).catch(()=>'')); 
  }
 }
 throw error;
} finally {
 rmSync(lag,{force:true});
 rmSync(config,{force:true});
 rmSync(expiry,{force:true});
 await browser.close();
 await new Promise(resolve=>server.close(resolve));
}
