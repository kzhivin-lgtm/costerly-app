import { statePath, reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {chromium} from 'playwright';
const config=statePath('scenario.json'),prices=statePath('objects-prices.json');
let priceDelay=0,priceFailure=false;
for(const file of ['object-approvals.json','objects-prices.json','object-quantities.json','generated-proposal.json','generation-failure','browser-journal'])rmSync(statePath(file),{force:true});
writeFileSync(config,JSON.stringify({objects_v2:true}));

const server=createServer(async(req,res)=>{
 if(req.url.startsWith('/rest/v1/')){
  const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,apikey,content-type,prefer','Access-Control-Allow-Methods':'POST,OPTIONS'};
  if(req.method==='OPTIONS')return res.writeHead(204,headers).end();
  let body='';for await(const chunk of req)body+=chunk;
  const row=JSON.parse(body);
  if(req.url.includes('/rpc/save_rfq_object_quantity')){
   const file=statePath('object-quantities.json'),values=existsSync(file)?JSON.parse(readFileSync(file)):{};
   values[row.p_estimate_id+':'+row.p_object_id]=row.p_quantity;
   const approvalsFile=statePath('object-approvals.json'),approvals=existsSync(approvalsFile)?JSON.parse(readFileSync(approvalsFile)):{};
   approvals[row.p_object_id]=false;writeFileSync(approvalsFile,JSON.stringify(approvals));
   writeFileSync(file,JSON.stringify(values));return res.writeHead(200,{...headers,'Content-Type':'application/json'}).end(JSON.stringify({quantity:row.p_quantity}));
  }
  await new Promise(resolve=>setTimeout(resolve,row.value===333?300:priceDelay));
  if(priceFailure)return res.writeHead(503,headers).end();
  const latest=existsSync(prices)?JSON.parse(readFileSync(prices)):[];
  const filtered=latest.filter(old=>old.object_key!==row.object_key);filtered.push(row);writeFileSync(prices,JSON.stringify(filtered));
  return res.writeHead(204,headers).end();
 }
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 const html=readFileSync('cloudflare/index.html','utf8').replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(html);
});
await new Promise(resolve=>server.listen(8798,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions),report={};
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(15000);
 await page.addInitScript(()=>{if(window!==top)return;window.objectsReady=[];addEventListener('message',event=>{if(event.data?.type==='costerly:app-ready')objectsReady.push({screen:event.data.screen,id:event.data.transitionId});});});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:8798/');await page.locator('iframe.is-ready').waitFor();
 const core=page.frameLocator('#costerly-app-frame');const frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 async function move(control,screen){
  const before=await page.evaluate(()=>objectsReady.length);
  const previous=await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
  await control.click();
  await core.locator(`[data-costerly-screen="${screen}"]:not([data-costerly-render-id="${previous}"])`).waitFor({state:'attached'});
  await page.waitForFunction(({before,screen})=>objectsReady.slice(before).some(event=>event.id&&event.screen===screen),{before,screen});
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 }
 await move(core.getByRole('button',{name:'Last Estimate',exact:true}),'file_review');
 await move(core.getByRole('button',{name:/^continue to objects estimation$/i}),'objects');
 await core.locator('.objects-pricing-table').waitFor();
 await page.locator('iframe.is-ready').waitFor();
 const set=()=>core.getByRole('button',{name:'Set Prices',exact:true});
 const generate=()=>core.getByRole('button',{name:'GENERATE PROPOSAL',exact:true});
 assert(await set().isDisabled());assert(await generate().isDisabled());
 assert.equal(await core.getByRole('button',{name:'Parts Check',exact:true}).count(),0);
 await frame.evaluate(()=>document.fonts.ready);
 report.geometry=await frame.evaluate(()=>{
  const box=node=>{const b=node.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height};};
  const controls=document.querySelector('[class*="st-key-costerly_header_controls"]');
  const metrics=document.querySelector('.objects-cycle-metrics');
  const title=document.querySelector('h1.workflow-title');
  const buttons=[...document.querySelectorAll('.st-key-objects_actions button')];
  return{title:box(title),controls:box(controls),metrics:box(metrics),dashboard:box(document.querySelector('.objects-technical-metrics')),buttons:buttons.map(box),projectInput:box(document.querySelector('.objects-pricing-project-cost-cell .objects-pricing-price-input')),qty:box(document.querySelector('.objects-pricing-quantity-input')),
   stages:box(document.querySelector('.objects-workflow-stages')),tableHead:box(document.querySelector('.objects-pricing-header')),
   summary:box(document.querySelector('.objects-pricing-summary')),summaryTitle:box(document.querySelector('.objects-pricing-summary-title')),
   summaryValues:[...document.querySelectorAll('[data-summary-field]')].map(box),stageColors:[...document.querySelectorAll('.objects-workflow-stages strong')].map(node=>getComputedStyle(node).color)};
 });
 await page.screenshot({path:reportPath('objects-v2-initial.png'),fullPage:true});
 assert(report.geometry.controls.y>report.geometry.title.y);
 const center=b=>b.y+b.height/2,right=b=>b.x+b.width;
 assert(Math.abs(center(report.geometry.controls)-center(report.geometry.title)-4)<.1,JSON.stringify(report.geometry));
 assert(Math.abs(right(report.geometry.controls)-right(report.geometry.title))<.1);
 assert.equal(report.geometry.dashboard.y-report.geometry.controls.y-report.geometry.controls.height,8);
 assert(Math.abs(right(report.geometry.dashboard)-right(report.geometry.controls))<.1);
 assert.equal(report.geometry.buttons.length,3);assert(Math.max(...report.geometry.buttons.map(b=>b.width))-Math.min(...report.geometry.buttons.map(b=>b.width))<2);
 assert.equal(report.geometry.projectInput.width,122);assert(Math.abs(report.geometry.projectInput.x-report.geometry.qty.x)<4);
 const geometry=report.geometry;
 assert.equal(geometry.stages.y-geometry.title.y,118);
 assert.equal(geometry.tableHead.y-geometry.stages.y-geometry.stages.height,50);
 const topSpace=geometry.summaryTitle.y-geometry.summary.y;
 const bottomSpace=geometry.buttons[0].y-Math.max(...geometry.summaryValues.map(box=>box.y+box.height));
 assert(Math.abs(topSpace-bottomSpace)<=4,JSON.stringify({topSpace,bottomSpace}));
 assert(geometry.stageColors.every(color=>color===geometry.stageColors[0]),JSON.stringify(geometry.stageColors));
 assert(!/subtotal/i.test(await core.locator('body').innerText()));
 assert(!(await core.locator('[title]').evaluateAll(nodes=>nodes.map(node=>node.title).join(' '))).match(/subtotal/i));
 assert.deepEqual(await core.locator('.objects-workflow-stages strong').allTextContents(),['Review Objects','Set Prices','Generate Proposal']);
 assert.equal(await core.locator('.objects-workflow-stages [data-stage="2"] small, .objects-workflow-stages [data-stage="3"] small').count(),0);
 assert(await core.getByRole('button',{name:'Project Summary',exact:true}).isDisabled());
 assert(await core.getByRole('button',{name:'Download Proposal',exact:true}).isDisabled());
 assert.equal(await core.locator('.objects-document-icon--excel').innerText(),'X');
 const iconState=()=>frame.evaluate(()=>[...document.querySelectorAll('.objects-document-button')].map(n=>{
  const icon=n.querySelector('.objects-document-icon'),r=icon.getBoundingClientRect();
  return{x:r.x,color:getComputedStyle(icon).color};
 }));
 const initialIcons=await iconState();
 assert.equal(initialIcons[0].x,initialIcons[1].x,'Document frames share the left edge');
 assert.equal(initialIcons[0].color,initialIcons[1].color,'Unavailable document icons are equally grey');
 report.documentIcons={initial:initialIcons};
 const baseline=JSON.parse(readFileSync(fixturePath('objects_v22_geometry.json'),'utf8'));
 // Approved V2.4 lifts the body26px; keep every other coordinate/dimension strict.
 // Only the intrinsically sized VAT
 // text box uses frozen V2.2 typography rendered with this platform's fonts,
 // rather than treating macOS glyph widths as a Linux layout requirement.
 const intrinsicWidths=await frame.evaluate(references=>Object.fromEntries(Object.entries(references).map(([selector,reference])=>{
  const host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;top:0;visibility:hidden;';
  const shadow=host.attachShadow({mode:'closed'});shadow.innerHTML=reference.html;document.body.append(host);
  try{return[selector,shadow.firstElementChild.getBoundingClientRect().width];}finally{host.remove();}
 })),baseline.intrinsic_width_references);
 report.intrinsicWidths=intrinsicWidths;
 report.protectedGeometry={};report.serviceHitAreas=[];
 for(const width of [1440,2536]){
  await page.setViewportSize({width,height:1244});
  const actual=await frame.evaluate(selectors=>{
   const box=n=>{const b=n.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height};};
   const preserved=Object.fromEntries(selectors.map(s=>[s,box(document.querySelector(s))]));
   const list=document.querySelector('.objects-workflow-stages'),steps=[...list.children];
   const lines=steps.slice(0,2).map(n=>parseFloat(getComputedStyle(n,'::after').width));
   const end=document.querySelector('[data-stage="3"] .objects-stage-group').getBoundingClientRect().right;
   const action=document.querySelector('.objects-pricing-action-cell').getBoundingClientRect().right;
   const docs=box(document.querySelector('.objects-pricing-downloads'));
   const heading=box(document.querySelector('.objects-pricing-summary-title'));
   const documents=[...document.querySelectorAll('.objects-document-button')].map(box);
   const back=box(document.querySelector('.st-key-objects_actions button'));
   return{preserved,lines,end,action,docs,heading,documents,back};
  },Object.keys(baseline.viewports[width]));
  for(const [selector,expected] of Object.entries(baseline.viewports[width]))for(const [axis,recorded] of Object.entries(expected)){
   const value=axis==='width'&&selector in intrinsicWidths?intrinsicWidths[selector]:recorded+(axis==='y'&&selector!=='h1.workflow-title'?-26:0);
   assert(Math.abs(actual.preserved[selector][axis]-value)<.1,JSON.stringify({width,selector,axis,expected:value,actual:actual.preserved[selector][axis]}));
  }
  assert(Math.abs(actual.lines[0]-actual.lines[1])<1);
  assert(Math.abs(actual.end-actual.action)<1);
  assert(Math.abs(actual.docs.y-actual.heading.y)<.1);
  for(const b of actual.documents)assert(Math.abs(b.width-actual.back.width/2)<.1);
  assert.equal(actual.documents[0].x,actual.documents[1].x);
  assert.equal(actual.documents[1].y-actual.documents[0].y-actual.documents[0].height,8);
  report.protectedGeometry[width]=actual;
  for(const key of ['delivery','installation']){
   const field=core.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input');
   const b=await field.boundingBox();assert.equal(b.width,122);
   await field.click();assert(await field.evaluate(n=>document.activeElement===n));
   for(const distance of [1,4,8])for(const [side,x,y] of [['left',b.x-distance,b.y+b.height/2],['right',b.x+b.width+distance,b.y+b.height/2],['above',b.x+b.width/2,b.y-distance],['below',b.x+b.width/2,b.y+b.height+distance]]){
    await frame.evaluate(()=>document.activeElement?.blur());await page.mouse.click(x,y);
    assert(!(await field.evaluate(n=>document.activeElement===n)),key+' activated by '+side+' click');
    report.serviceHitAreas.push({width,key,side,distance,focused:false});
   }
  }
  await page.screenshot({path:reportPath('objects-v24-'+width+'.png'),fullPage:true});
 }
 await page.setViewportSize({width:1440,height:1000});
 const beforeJournal=readFileSync(statePath('browser-journal'),'utf8');
 const toggle=core.getByRole('button',{name:'Collapse technical metrics',exact:true});
 const dashboard=await core.locator('.objects-technical-metrics').boundingBox();
 const toggleBox=await toggle.boundingBox();
 assert(Math.abs(toggleBox.x+toggleBox.width-dashboard.x-dashboard.width)<1,'Metrics arrow is fixed at the right edge');
 const metricText=await core.locator('.objects-cycle-metrics').innerText();
 assert.match(metricText,/R1\s/);assert(!metricText.includes('Saved bench'));
 const metricsMarkup=await core.locator('.objects-cycle-metrics').innerHTML();
 report.metricsCounts=[];
 for(const count of [10,40]){
  await core.locator('.objects-cycle-metrics').evaluate((n,count)=>{n.innerHTML='<span>Total lap <strong>123.4s</strong></span><span>TC <strong>1.23</strong></span>'+Array.from({length:count},(_,i)=>'<span>R'+(i+1)+' <strong>123.4s</strong></span>').join('');},count);
  const sizing=await frame.evaluate(()=>{
   const m=document.querySelector('.objects-cycle-metrics'),b=document.querySelector('.objects-metrics-toggle').getBoundingClientRect(),d=document.querySelector('.objects-technical-metrics').getBoundingClientRect();
   return{viewport:innerWidth,x:d.x,right:d.right,width:d.width,arrowRight:b.right,client:m.clientWidth,scroll:m.scrollWidth};
  });
  assert(sizing.x>=0&&sizing.right<=sizing.viewport,'Many metrics stay inside the viewport');
  assert(Math.abs(sizing.arrowRight-sizing.right)<1);
  report.metricsCounts.push({count,...sizing});
 }
 await core.locator('.objects-cycle-metrics').evaluate((n,markup)=>n.innerHTML=markup,metricsMarkup);
 const arrowBefore=await toggle.boundingBox();await toggle.click();
 assert(!(await core.locator('.objects-cycle-metrics').isVisible()));
 await frame.evaluate(()=>{const n=document.querySelector('.objects-technical-metrics'),copy=n.cloneNode(true),button=copy.querySelector('button');button.setAttribute('aria-expanded','true');button.setAttribute('aria-label','Collapse technical metrics');n.replaceWith(copy);});
 await core.getByRole('button',{name:'Expand technical metrics',exact:true}).waitFor();
 assert(!(await core.locator('.objects-cycle-metrics').isVisible()));
 const arrowAfter=await core.getByRole('button',{name:'Expand technical metrics',exact:true}).boundingBox();
 assert.equal(arrowBefore.x,arrowAfter.x);assert.equal(arrowBefore.y,arrowAfter.y);
 assert.equal(readFileSync(statePath('browser-journal'),'utf8'),beforeJournal,'Dashboard toggle must not rerun/read/write');
 assert(!existsSync(prices),'Focus-only interactions must not write prices');
 await page.screenshot({path:reportPath('objects-v2-initial.png'),fullPage:true});
 await move(core.getByRole('link',{name:/^review$/i}),'object_detail');
 await core.locator('.object-detail-title').first().waitFor();
 await move(core.locator('.object-detail-footer-button--primary'),'objects');
 await core.locator('.objects-pricing-table').waitFor();await set().waitFor();assert(await set().isEnabled());
 await frame.waitForFunction(()=>window.__costerlyObjectsActionsCleanup&&window.__costerlyObjectsPriceInputGuardCleanup);
 await core.getByRole('button',{name:'Expand technical metrics',exact:true}).waitFor();
 assert(!(await core.locator('.objects-cycle-metrics').isVisible()),'Collapsed metrics survive navigation/full render');
 const input=core.locator('.objects-pricing-row[data-object-key="object-001"] .objects-pricing-price-input');
 async function editPrice(value){
  await input.fill(String(value));await input.press('Tab');
  const deadline=Date.now()+5000;
  while(!existsSync(prices)||JSON.parse(readFileSync(prices)).find(row=>row.object_key==='object-001')?.value!==value){
   if(Date.now()>deadline)throw new Error('Original price persistence did not complete');
   await new Promise(resolve=>setTimeout(resolve,20));
  }
 }
 for(const [key,value] of [['delivery',123],['installation',321]]){
  const field=core.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input');
  await field.click();
  assert(await field.evaluate(n=>document.activeElement===n),'Service editing starts with an inside-field click');
  await field.fill(String(value));await field.press('Tab');
  const deadline=Date.now()+5000;
  while(!existsSync(prices)||JSON.parse(readFileSync(prices)).find(row=>row.object_key===key)?.value!==value){
   if(Date.now()>deadline)throw new Error('Original service-price persistence did not complete: '+key);
   await new Promise(resolve=>setTimeout(resolve,20));
  }
 }
 const unconfirmedColor=await set().evaluate(n=>getComputedStyle(n).backgroundColor);
 await editPrice(1750);
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Objects',exact:true}),'objects');
 for(const [key,value] of [['delivery',123],['installation',321],['object-001',1750]]){
  const field=core.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input');
  assert.equal((await field.innerText()).replace(/[^0-9]/g,''),String(value),key+' blur save survives Review/Back without Set Prices');
 }
 const service=key=>core.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input');
 async function waitPrice(key,value){
  const deadline=Date.now()+5000;
  while(!existsSync(prices)||JSON.parse(readFileSync(prices)).find(row=>row.object_key===key)?.value!==value){
   if(Date.now()>deadline){
    report.persistenceFailure=await frame.evaluate(()=>({
     inputs:[...document.querySelectorAll('.objects-pricing-price-input')].map(n=>n.outerHTML),
     writes:[...(window.__costerlyObjectsPriceWrites||new Map())].map(([key,x])=>({key,value:x.value,done:x.done,failed:x.failed}))
    }));
    writeFileSync(reportPath('persistence-failure.json'),JSON.stringify(report.persistenceFailure,null,2));
    throw new Error('Blur price not persisted: '+key);
   }
   await new Promise(resolve=>setTimeout(resolve,20));
  }
 }
 priceDelay=500;
 await service('delivery').fill('222');
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Objects',exact:true}),'objects');
 await waitPrice('delivery',222);
 assert.equal((await service('delivery').innerText()).replace(/[^0-9]/g,''),'222');
 priceDelay=0;priceFailure=true;
 await service('installation').fill('444');await service('installation').press('Tab');
 await frame.waitForFunction(()=>document.querySelector('[data-object-key="installation"] .objects-pricing-price-input')?.getAttribute('aria-invalid')==='true');
 assert.equal((await service('installation').innerText()).replace(/[^0-9]/g,''),'444');
 assert.equal(JSON.parse(readFileSync(prices)).find(row=>row.object_key==='installation').value,321);
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Objects',exact:true}),'objects');
 assert.equal((await service('installation').innerText()).replace(/[^0-9]/g,''),'444');
 priceFailure=false;
 await service('installation').click();await service('installation').press('Tab');await waitPrice('installation',444);
 await service('delivery').fill('333');await service('delivery').press('Tab');
 await service('delivery').fill('555');await service('delivery').press('Tab');await waitPrice('delivery',555);
 await service('delivery').fill('123');await service('delivery').press('Tab');await waitPrice('delivery',123);
 await service('installation').fill('321');await service('installation').press('Tab');await waitPrice('installation',321);
 priceDelay=300;
 await input.fill('1750');await set().click();
 await frame.waitForFunction(()=>document.querySelector('.objects-workflow-stages [data-stage="2"]')?.dataset.state==='complete');
 await waitPrice('object-001',1750);priceDelay=0;
 const quantity=core.locator('.objects-pricing-row[data-object-key="object-001"] [data-object-quantity-input]');
 await quantity.fill('2');await quantity.press('Tab');
 await core.locator('.objects-quantity-saving-overlay.is-visible').waitFor({state:'hidden'});
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Objects',exact:true}),'objects');
 assert.equal(await quantity.innerText(),'2','Quantity blur save survives Review/Back');
 await quantity.fill('1');await quantity.press('Tab');
 await core.locator('.objects-quantity-saving-overlay.is-visible').waitFor({state:'hidden'});
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.locator('.object-detail-footer-button--primary'),'objects');
 const reopened=await browser.newPage({viewport:{width:390,height:1000}});
 await reopened.goto('http://127.0.0.1:8798/');await reopened.locator('iframe.is-ready').waitFor();
 const reopenedCore=reopened.frameLocator('#costerly-app-frame');
 await reopenedCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await reopenedCore.getByRole('button',{name:/^continue to objects estimation$/i}).click();
 await reopenedCore.locator('.objects-pricing-table').waitFor();
 for(const [key,value] of [['delivery',123],['installation',321],['object-001',1750]]){
  assert.equal((await reopenedCore.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input').innerText()).replace(/[^0-9]/g,''),String(value),'New browser context reads saved '+key);
 }
 await reopened.close();
 report.blurPersistence={roundTripWithoutSetPrices:true,slowWrite:true,failedWriteRetained:true,retry:true,
  latestEditWins:true,quantityRoundTrip:true,newBrowserContext:true,confirmationWaitsForWrite:true};
 await editPrice(1750);await set().click();
 await frame.waitForFunction(()=>{const button=document.querySelector('[class*="st-key-objects_generate_proposal_"] button');return button&&!button.disabled;});
 assert.equal(await core.locator('.objects-workflow-stages [data-stage="2"]').getAttribute('data-state'),'complete');
 await page.mouse.move(0,0);
 await frame.waitForFunction(()=>{
  const set=document.querySelector('.st-key-objects_set_prices button'),done=document.querySelector('.objects-pricing-review-button--done');
  return set&&done&&getComputedStyle(set).backgroundColor===getComputedStyle(done).backgroundColor;
 });
 const confirmedColor=await set().evaluate(n=>getComputedStyle(n).backgroundColor);
 assert.equal(confirmedColor,await core.locator('.objects-pricing-review-button--done').evaluate(n=>getComputedStyle(n).backgroundColor),'Confirmed Set Prices reuses Done green');
 const checks=await core.locator('.objects-workflow-stages [data-state="complete"] .objects-stage-marker').evaluateAll(ns=>ns.map(n=>{
  const c=getComputedStyle(n,'::before');return{width:c.width,height:c.height,right:c.borderRightWidth,bottom:c.borderBottomWidth};
 }));
 assert.equal(checks.length,2);assert(checks.every(c=>parseFloat(c.width)>0&&parseFloat(c.height)>0&&c.right==='2px'&&c.bottom==='2px'));
 await core.locator('.objects-workflow-stages').screenshot({path:reportPath('objects-v26-checkmarks.png')});
 await editPrice(1850);assert(await generate().isDisabled());
 // The original base stylesheet animates background for140ms. Persistence
 // and disabled state can complete before the first painted animation frame.
 // Require the full original color back, retaining the original assertion.
 await frame.waitForFunction(expected=>{
  const button=document.querySelector('.st-key-objects_set_prices button');
  return button&&getComputedStyle(button).backgroundColor===expected;
 },unconfirmedColor,{timeout:1000});
 assert.notEqual(await set().evaluate(n=>getComputedStyle(n).backgroundColor),confirmedColor,'Editing revokes the confirmed green');
 await set().click();
 await frame.waitForFunction(()=>{const button=document.querySelector('[class*="st-key-objects_generate_proposal_"] button');return button&&!button.disabled;});
 writeFileSync(statePath('generation-failure'),'fail');await generate().click();await core.getByText('Controlled proposal failure',{exact:true}).waitFor();assert(await generate().isEnabled());
 rmSync(statePath('generation-failure'));await generate().click();
 await frame.waitForFunction(()=>document.querySelector('.objects-workflow-stages [data-stage="3"]')?.dataset.state==='complete');
 assert(await generate().isDisabled());
 const proposal=JSON.parse(readFileSync(statePath('generated-proposal.json')));assert.equal(proposal.rows[0].sale_price_unit,1850);
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,1);
 const download=core.getByRole('link',{name:'Download Proposal',exact:true});await download.waitFor();
 const availableIcons=await iconState();report.documentIcons.available=availableIcons;
 assert.equal(availableIcons[0].x,availableIcons[1].x);
 assert.equal(availableIcons[0].color,initialIcons[0].color,'Project Summary remains disabled and grey');
 assert.equal(availableIcons[1].color,'rgb(180, 59, 70)','Available PDF is red');
 const summaryButton=core.getByRole('button',{name:'Project Summary',exact:true});
 const futureExcelColor=await summaryButton.evaluate(n=>{
  n.disabled=false;
  try{return getComputedStyle(n.querySelector('.objects-document-icon--excel')).color;}
  finally{n.disabled=true;}
 });
 assert.equal(futureExcelColor,'rgb(40, 121, 76)','Available Excel appearance is green; no export is enabled');
 assert.equal(await download.getAttribute('href'),proposal.proposal_pdf_url||'data:application/pdf;base64,JVBERi0xLjQ=');
 assert.deepEqual(errors,[]);report.errors=errors;
 await page.screenshot({path:reportPath('objects-v2-generated.png'),fullPage:true});
 writeFileSync(config,JSON.stringify({objects_v2:true,admin:false}));
 const member=await browser.newPage({viewport:{width:1440,height:1000}}),memberCore=member.frameLocator('#costerly-app-frame');
 await member.goto('http://127.0.0.1:8798/');await member.locator('iframe.is-ready').waitFor();
 await memberCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await memberCore.getByRole('button',{name:/continue to objects estimation/i}).waitFor();await memberCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 await memberCore.getByRole('button',{name:/continue to objects estimation/i}).click();await memberCore.locator('.objects-pricing-table').waitFor();await memberCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await memberCore.locator('.objects-cycle-metrics,.objects-metrics-toggle').count(),0,'Technical metrics reuse existing platform-admin visibility');
 await member.close();report.nonAdminMetricsHidden=true;
 writeFileSync(reportPath('objects-v2.json'),JSON.stringify(report,null,2));
 console.log('Objects V2.4 passed: approved26px body lift, original geometry/field boundaries, top-right menu+metrics with4px offset, stacked half-width documents, local metrics toggle and original pricing/approval/proposal flow.');
}catch(error){
 for(const page of browser.contexts().flatMap(context=>context.pages())){
  await page.screenshot({path:reportPath('objects-v2-latest-failure.png'),fullPage:true});
  const handle=await page.locator('#costerly-app-frame').elementHandle();const frame=handle&&await handle.contentFrame();
  if(frame)writeFileSync(reportPath('objects-v2-latest-failure.json'),JSON.stringify(await frame.evaluate(()=>({text:document.body.innerText,receipt:document.getElementById('objects-actions-error')?.outerHTML,pending:[...(window.__costerlyObjectsPricingWrites?.latest||new Map())].map(([key,entry])=>({key,ok:entry.ok})),serviceInputs:[...document.querySelectorAll('.objects-pricing-project-cost-cell .objects-pricing-price-input')].map(n=>({key:n.closest('.objects-pricing-row')?.dataset.objectKey,text:n.textContent,active:document.activeElement===n,dirty:n.dataset.editDirty})),buttons:[...document.querySelectorAll('.st-key-objects_actions button')].map(button=>({text:button.innerText,disabled:button.disabled,busy:button.getAttribute('aria-busy'),phase:button.dataset.objectsPhase}))})),null,2));
 }
 throw error;
}finally{await browser.close();server.close();}
