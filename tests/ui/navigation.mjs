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
let deliveredOld=false;
const server=createServer((req,res)=>{
 const path=new URL(req.url,'http://127.0.0.1:8797');
 if(path.pathname.startsWith('/api/')) return res.writeHead(202).end();
 const serveOld=path.searchParams.has('old')&&!deliveredOld;
 if(serveOld)deliveredOld=true;
 const html=(serveOld?old:current).replace('<script>', '<script>window.wrapperFixtureVersion='+JSON.stringify(serveOld?'old':'current')+';</script><script>');
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
  {name:'restored_document',width:1280,height:900,restoreDocument:true,lag:true},
 ]){
  const scenarioSettings={objects_v2:!!cfg.restoreDocument,objects_refresh_delay:cfg.restoreDocument?0.8:0,delay:cfg.lag?{projects:1.25,account:1.25}:{}};
  writeFileSync(config,JSON.stringify(scenarioSettings));
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
                              transition:ev.data.transition,sentAt:ev.data.sentAt,receivedAt:Date.now()});
    }
   });
  });
  await page.goto('http://127.0.0.1:8797/'+(cfg.oldWrapper?'?old':''));
  if(cfg.oldWrapper)await page.waitForFunction(()=>window.wrapperFixtureVersion==='current');
  await page.locator('iframe.is-ready').waitFor();
  let frame=await (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  const core=page.frameLocator('#costerly-app-frame');
  await core.getByRole('button',{name:'Last Estimate',exact:true}).waitFor();
  await page.locator('iframe.is-ready').waitFor();
  if(!cfg.old) await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  if(cfg.restoreDocument){
   const originalTrace=await frame.evaluate(()=>window.__costerlyWorkflowTransition.traceId);
   // Two real document navigations: the second has no trace in either URL or
   // referrer. They must retain the verified parent context, not silently
   // disable the shield for all subsequent page transitions.
   for(let round=1;round<=2;round++){
    await Promise.all([
     frame.waitForURL(url=>url.searchParams.get('restored_document')===String(round),{waitUntil:'domcontentloaded'}),
     frame.evaluate(round=>{const url=new URL(location.href);url.searchParams.delete('obs_trace');url.searchParams.set('restored_document',String(round));const link=document.createElement('a');link.href=url.toString();document.body.append(link);link.click();},round),
    ]);
    await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
    assert.equal(await frame.evaluate(()=>window.__costerlyWorkflowTransition.traceId),originalTrace);
   }
  }
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
     const bounds=cover?.getBoundingClientRect();
     const regional=bounds&&bounds.width>0&&bounds.height>0&&cover.contains(document.elementFromPoint(bounds.x+bounds.width/2,bounds.y+Math.min(30,bounds.height/2)));
     frames.push({at:Date.now(),ms:Math.round(performance.now()-start),cover:Boolean(covered),regionalCover:Boolean(regional),screens});
     requestAnimationFrame(sample);
    }
    sample();
   });
   const profileTab=label.startsWith('Profile tab ');
   if(profileTab)await frame.evaluate(()=>window.__profileHeader=document.querySelector('.company-profile-heading'));
   const clickStarted=Date.now();
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
    assert(Number.isFinite(completions[0].sentAt),'Missing actual Core-ready timestamp');
    const untilReady=samples.filter(row=>row.at>=covered[0].receivedAt&&row.at<completions[0].sentAt);
    assert(untilReady.length>0,'Continuous-cover check must sample the pending interval');
    counts.uncoveredBeforeReady=untilReady.filter(row=>!row[profileTab?'regionalCover':'cover']).length;
    assert.equal(counts.uncoveredBeforeReady,0,JSON.stringify({transition:label,events,gaps:untilReady.filter(row=>!row[profileTab?'regionalCover':'cover']).slice(0,6)}));
    assert.equal(counts.uncoveredMixed,0,JSON.stringify(samples));
    if(profileTab){
     assert.equal(counts.coveredFrames,0);
     assert.ok(await frame.evaluate(()=>window.__profileHeader===document.querySelector('.company-profile-heading')));
    }else assert.ok(counts.coveredFrames>0,JSON.stringify(samples));
    assert.ok(!(await frame.evaluate(()=>document.querySelector('.stMain').scrollTop)));
   } else assert.equal(covered.length,0);
   if(label.includes('New Estimate'))counts.clickToReadyMs=Date.now()-clickStarted;
   actions.push(counts);
   console.log(cfg.name, label, JSON.stringify(counts));
  }


  await move('Open Profile before restart',button('Profile'),'account');
  await move('Clear workflow URL with New Estimate',button('New Estimate'),'upload');
  assert.ok(!new URL(frame.url()).searchParams.has('obs_trace'));
  const browserTrace=await frame.evaluate(()=>window.__costerlyWorkflowTransition.traceId);
  writeFileSync(config,JSON.stringify({...scenarioSettings,restart_once:true}));
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
  const materials=core.locator('.object-detail-materials-band');
  const labor=core.locator('[data-cost-band="labor"]');
  const sheet=labor.locator('[data-cost-band="sheet-processing"]');
  const assembly=labor.locator('[data-cost-band="assembly"]');
  await labor.waitFor();
  assert.equal(await core.locator('[data-cost-band="labor"]').count(),1);
  assert.equal(await sheet.count(),1);
  assert.equal(await assembly.count(),1);
  assert.equal(await sheet.locator('.object-detail-elements').count(),1);
  assert.equal(await assembly.locator('.object-detail-elements').count(),0);
  const overhead=core.locator('.object-detail-overhead-band');
  await overhead.waitFor();
  for(const band of [materials,labor,overhead]){
   assert.equal(await band.evaluate(node=>node.open),false,'Object Details starts compact');
   assert.equal(await band.locator(':scope > summary .object-detail-cost-value').isVisible(),true);
  }
  const bandAxes=await frame.evaluate(()=>[...document.querySelectorAll('.object-detail-band-summary .object-detail-cost-value')].map(n=>{const b=n.getBoundingClientRect();return b.x+b.width/2;}));
  assert.equal(bandAxes.length,3);assert.ok(bandAxes.every(x=>Math.abs(x-bandAxes[0])<1),JSON.stringify(bandAxes));
  assert.equal(await materials.locator('details').count(),0,'Material rows do not disclose another level');
  const previewSize=await core.locator('.object-detail-preview-placeholder').boundingBox();
  assert.equal(previewSize.width,240);assert.equal(previewSize.height,164);
  const detailCopy=await core.locator('body').innerText();
  assert.ok(!/AI confidence|Subtotal based|some costs are still awaiting/i.test(detailCopy));
  if(cfg.width>760){
   const axis=await core.locator('.object-detail-final').evaluate(node=>{
    const cy=n=>{const b=n.getBoundingClientRect();return b.y+b.height/2;};
    return {title:cy(node.querySelector('.object-detail-final-title')),values:[...node.querySelectorAll('[data-final]')].map(cy)};
   });
   assert.ok(axis.values.every(y=>Math.abs(y-axis.title)<1),JSON.stringify(axis));
  }
  await page.screenshot({path:reportPath('object-details-compact-'+cfg.name+'.png'),fullPage:true});
  await materials.locator(':scope > summary').click();
  await labor.locator(':scope > summary').click();
  const production=labor.locator('[data-cost-band="part-production"]');
  const assemblyStage=labor.locator('[data-cost-band="assembly-stage"]');
  for(const parent of [production,assemblyStage]){
   assert.equal(await parent.evaluate(node=>node.open),false);
   await parent.locator(':scope > summary').click();
  }
  assert.equal(await materials.locator('.object-detail-cost-body > .object-detail-table-head-row > div').first().innerText(),'');
  assert.equal(await labor.locator('.object-detail-cost-column-headings > div').first().innerText(),'');
  for(const row of [sheet,assembly]){
   assert.equal(await row.evaluate(node=>node.classList.contains('object-detail-table')),false);
   assert.ok((await row.locator(':scope > summary').evaluate(node=>node.getBoundingClientRect().height))<=48);
   assert.equal(await row.locator(':scope > summary [data-labor-column="hours"]').isVisible(),true);
  }
  // Native scroll-into-view can pan a narrow independent table when opening
  // the new parent rows. Compare the protected axes at equal scroll positions.
  const tableScroll=await frame.evaluate(()=>{
   const tables=[document.querySelector('.object-detail-materials-band'),document.querySelector('[data-cost-band="labor"]')];
   const before=tables.map(n=>n.scrollLeft);for(const n of tables)n.scrollLeft=0;
   return {before,after:tables.map(n=>n.scrollLeft)};
  });
  assert.deepEqual(tableScroll.after,[0,0]);
  console.log(cfg.name,'axis scroll precondition',JSON.stringify(tableScroll));
  const alignment=await frame.evaluate(()=>{
   const cells=document.querySelector('.object-detail-materials-band .object-detail-cost-body > .object-detail-table-head-row').children;
   const center=node=>{const r=node.getBoundingClientRect();return r.x+r.width/2;};
   const head=document.querySelector('[data-cost-band="labor"] .object-detail-cost-column-headings');
   const reference=document.createElement('span');
   reference.style.backgroundColor='rgba(42, 31, 44, 0.045)';
   head.appendChild(reference);
   const originalColor=getComputedStyle(reference).backgroundColor;
   reference.remove();
   return {
    hours:Math.abs(center(cells[1])-center(head.querySelector('[data-labor-column="hours"]'))),
    pay:center(head.querySelector('[data-labor-column="pay"] > span')),
    taxes:center(head.querySelector('[data-labor-column="taxes"] > span')),
    start:center(head.querySelector('[data-labor-column="hours"]')),
    end:center(head.querySelector('[data-labor-column="total"]')),
    total:Math.abs(center(cells[5])-center(head.querySelector('[data-labor-column="total"]'))),
    header:getComputedStyle(head).backgroundColor,
    originalColor,
    cell:getComputedStyle(head.children[0]).backgroundColor,
   };
  });
  assert.ok(alignment.hours<1 && alignment.total<1 && alignment.taxes>alignment.pay,JSON.stringify(alignment));
  const step=(alignment.end-alignment.start)/3;
  assert.ok(Math.abs(alignment.pay-alignment.start-step)<1 && Math.abs(alignment.taxes-alignment.pay-step)<1,JSON.stringify(alignment));
  assert.equal(alignment.header,alignment.originalColor);
  assert.equal(alignment.cell,'rgba(0, 0, 0, 0)');
  assert.equal(await labor.locator('.object-detail-cost-column-headings .object-detail-cost-label').last().innerText(),'TOTAL');
  assert.equal(await labor.locator('.object-detail-labor-body > .object-detail-cnc-caption:not(.object-detail-labor-review)').count(),0);
  const cardRender=await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
  for(const band of [materials,labor,production,assemblyStage,sheet,assembly]){
   const summary=band.locator(':scope > summary');
   await summary.focus();
   const initial=await band.evaluate(node=>node.open);
   await summary.press('Enter');
   assert.equal(await band.evaluate(node=>node.open),!initial);
   await summary.press('Space');
   assert.equal(await band.evaluate(node=>node.open),initial);
  }
  await overhead.locator(':scope > summary').click();
  const group=overhead.locator('.object-detail-group').first();
  assert.ok(await overhead.locator('.object-detail-group').count()>0);
  assert.equal(await group.evaluate(n=>n.open),false);
  const closedColor=await group.locator(':scope > summary').evaluate(n=>getComputedStyle(n).backgroundColor);
  await group.locator(':scope > summary').click();
  assert.equal(await group.locator('.object-detail-table-row').first().isVisible(),true);
  assert.notEqual(await group.locator(':scope > summary').evaluate(n=>getComputedStyle(n).backgroundColor),closedColor);
  await overhead.locator(':scope > summary').click();
  await sheet.locator(':scope > summary .object-detail-cost-title').click();
  await sheet.locator('.object-detail-elements > summary').click();
  await assembly.locator(':scope > summary .object-detail-cost-title').click();
  assert.match(await assembly.innerText(),/Taxes & social/i);
  await page.screenshot({path:reportPath('object-cost-hierarchy-'+cfg.name+'.png'),fullPage:true});
  await materials.locator(':scope > summary').click();
  await labor.locator(':scope > summary').click();
  for(const band of [materials,labor]){
   assert.equal(await band.evaluate(node=>node.open),false);
   assert.equal(await band.locator(':scope > summary .object-detail-cost-value').last().isVisible(),true);
  }
  assert.equal(await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id'),cardRender);
  await move('Card to New Estimate',button('New Estimate'),'upload');
  if(cfg.restoreDocument){
   const screen=()=>core.locator('[data-costerly-screen]').last().getAttribute('data-costerly-screen');
   async function enter(target){
    if(await screen()===target)return;
    if(target==='upload')return move('Matrix restore Upload',button('New Estimate'),'upload');
    if(target==='projects')return move('Matrix restore Projects',button('Projects'),'projects');
    if(target==='account')return move('Matrix restore Profile',button('Profile'),'account');
    if(target==='file_review'){await enter('upload');return move('Matrix restore File Review',button('Last Estimate'),'file_review');}
    if(target==='objects'){await enter('file_review');return move('Matrix restore Objects',cont(),'objects');}
    await enter('objects');return move('Matrix restore Object Detail',openObject(),'object_detail');
   }
   const sources=['upload','file_review','objects','object_detail','projects','account'];
   for(const source of sources)for(const [target,label] of [['upload','New Estimate'],['projects','Projects'],['account','Profile']]){
    if(source===target)continue;
    await enter(source);await move(`Header ${source} to ${target}`,button(label),target);
   }
   for(const source of ['upload','projects','account']){
    await enter(source);await move(`Last Estimate from ${source}`,button('Last Estimate'),'file_review');
   }
   await enter('object_detail');await move('Scrolled Approve to Objects',core.locator('.object-detail-footer-button--primary'),'objects');
   await enter('object_detail');await move('Scrolled Back to Objects',core.locator('.object-detail-footer-button--secondary').filter({hasText:'Back to Objects'}),'objects');
   await move('Objects Back to File Review',button('Back to File Review'),'file_review');
   await move('File Review Back to Upload',button(/^back to upload$/i),'upload');
   for(const source of sources){
    await enter(source);await move(`Sign out from ${source}`,core.locator('.st-key-company_sign_out button'),'login');
    rmSync(expiry,{force:true});await page.reload();await page.locator('iframe.is-ready').waitFor();
    frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
    await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
   }
  }
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  report[cfg.name]=actions;
  await page.close();
 }
 const calls=readFileSync(journal,'utf8');
 assert.ok(calls.includes('objects '+expected));
 assert.ok(!calls.includes('ERROR'));
 writeFileSync(reportPath('navigation.json'),JSON.stringify(report,null,2));
 console.log('Saved-estimate reuse, continuous shielding and zero Parts Check launches across fresh, legacy, mobile and restored-document routes.');
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
