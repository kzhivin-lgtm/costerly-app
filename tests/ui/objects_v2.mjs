import { statePath, reportPath, fixturePath, chromeOptions, checkClosingGap } from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {chromium} from 'playwright';
const config=statePath('scenario.json'),prices=statePath('objects-prices.json');
let priceDelay=0,priceFailure=false,quantityDelay=0,quantityFailure=false;
for(const file of ['object-approvals.json','object-names.json','objects-prices.json','object-quantities.json','generated-proposal.json','generated-proposal-history.json','generation-failure','proposal-delay','browser-journal'])rmSync(statePath(file),{force:true});
writeFileSync(config,JSON.stringify({objects_v2:true,detail_prefetch:true}));
writeFileSync(statePath('hold-object-preparation'),'hold');

const server=createServer(async(req,res)=>{
 if(/^\/generated-proposal(?:-v\d+)?\.pdf$/.test(req.url)){
  const version=Number(req.url.match(/-v(\d+)/)?.[1]||1);
  return res.writeHead(200,{'Content-Type':'application/pdf','Content-Disposition':`attachment; filename="Proposal_V${version}.pdf"`}).end(`%PDF-1.4\nfixture proposal V${version}\n`);
 }
 if(req.url.startsWith('/rest/v1/')){
  const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,apikey,content-type,prefer','Access-Control-Allow-Methods':'POST,OPTIONS'};
  if(req.method==='OPTIONS')return res.writeHead(204,headers).end();
  let body='';for await(const chunk of req)body+=chunk;
  const row=JSON.parse(body);
  if(req.url.includes('/rpc/save_rfq_object_quantity')){
   await new Promise(resolve=>setTimeout(resolve,row.p_quantity===4?300:quantityDelay));
   if(quantityFailure)return res.writeHead(503,headers).end();
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
 await page.addInitScript(()=>{if(window!==top)return;window.objectsReady=[];addEventListener('message',event=>{if(event.data?.type==='costerly:app-ready')objectsReady.push({screen:event.data.screen,id:event.data.transitionId,at:Date.now()});});});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:8798/');await page.locator('iframe.is-ready').waitFor();
 const core=page.frameLocator('#costerly-app-frame');const frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 report.transitions=[];
 await frame.evaluate(()=>document.addEventListener('click',()=>{window.lastNavigationClickAt=Date.now();},true));
 async function move(control,screen){
  const before=await page.evaluate(()=>objectsReady.length);
  const previous=await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
  await control.click();
  await core.locator(`[data-costerly-screen="${screen}"]:not([data-costerly-render-id="${previous}"])`).waitFor({state:'attached'});
  await page.waitForFunction(({before,screen})=>objectsReady.slice(before).some(event=>event.id&&event.screen===screen),{before,screen});
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  const clickAt=await frame.evaluate(()=>window.lastNavigationClickAt);
  const ready=await page.evaluate(()=>objectsReady.at(-1));
  report.transitions.push({target:screen,clickToReadyMs:ready.at-clickAt});
 }
 await move(core.getByRole('button',{name:'Last Estimate',exact:true}),'file_review');
 await move(core.getByRole('button',{name:/^continue to project$/i}),'objects');
 await core.locator('.objects-pricing-table').waitFor();
 await page.locator('iframe.is-ready').waitFor();
 assert.equal(await core.getByRole('link',{name:/^(Done|Review)$/i}).count(),0,'Review is not available before Object preparation');
 rmSync(statePath('hold-object-preparation'));
 await core.getByRole('link',{name:/^(Done|Review)$/i}).waitFor();
 report.preparedBeforeReview=true;
 const set=()=>core.getByRole('button',{name:'Set Prices',exact:true});
 const generate=()=>core.getByRole('button',{name:'GENERATE PROPOSAL',exact:true});
 assert(await set().isDisabled());assert(await generate().isDisabled());
 assert.equal(await core.getByRole('button',{name:'Parts Check',exact:true}).count(),0);
 await frame.evaluate(()=>document.fonts.ready);
 assert.equal(await core.locator('h1 .workflow-title-text').innerText(),'Project');
 const logoAxis=await frame.evaluate(async()=>{
  const img=document.querySelector('.objects-estimation-header .workflow-title-mark img');await img.decode();
  const r=img.getBoundingClientRect(),canvas=document.createElement('canvas');
  canvas.width=Math.ceil(r.width*4);canvas.height=Math.ceil(r.height*4);
  const context=canvas.getContext('2d');context.drawImage(img,0,0,canvas.width,canvas.height);
  const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;let first=canvas.width;
  for(let y=0;y<canvas.height;y++)for(let x=0;x<first;x++)if(pixels[(y*canvas.width+x)*4+3]>20)first=x;
  return {artwork:r.x+first/4,body:document.querySelector('.objects-pricing-header').getBoundingClientRect().x};
 });
 assert(Math.abs(logoAxis.artwork-logoAxis.body)<=1,JSON.stringify(logoAxis));report.logoAxis=logoAxis;
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
 assert(bottomSpace>=topSpace-4,JSON.stringify({topSpace,bottomSpace}));
 report.footer=await checkClosingGap(frame,'.st-key-objects_actions');
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
  const shadow=host.attachShadow({mode:'closed'});shadow.innerHTML=reference.html.replace('font-size:18px;line-height:1.2;font-weight:700','font-size:30px;line-height:1.2;font-weight:400');document.body.append(host);
  try{return[selector,shadow.firstElementChild.getBoundingClientRect().width];}finally{host.remove();}
 })),baseline.intrinsic_width_references);
 report.intrinsicWidths=intrinsicWidths;
 report.protectedGeometry={};report.serviceHitAreas=[];
 for(const width of [1440,2536]){
  await page.setViewportSize({width,height:1244});
  const actual=await frame.evaluate(selectors=>{
   const box=n=>{const b=n.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height};};
   const preserved=Object.fromEntries(selectors.map(s=>[s,box(document.querySelector(s==='.objects-pricing-row--project-cost'?'.objects-pricing-row[data-object-key="delivery"]':s))]));
   const list=document.querySelector('.objects-workflow-stages'),steps=[...list.children];
   const lines=steps.slice(0,2).map(n=>parseFloat(getComputedStyle(n,'::after').width));
   const end=document.querySelector('[data-stage="3"] .objects-stage-group').getBoundingClientRect().right;
   const action=document.querySelector('.objects-pricing-action-cell').getBoundingClientRect().right;
   const docs=box(document.querySelector('.objects-pricing-downloads'));
   const heading=box(document.querySelector('.objects-pricing-summary-title'));
   const documents=[...document.querySelectorAll('.objects-document-button')].map(box);
   const back=box(document.querySelector('.st-key-objects_actions button'));
   return{preserved,lines,end,action,docs,heading,documents,back,productionHeight:box(document.querySelector('[data-commercial-term]')).height};
  },Object.keys(baseline.viewports[width]));
  for(const [selector,expected] of Object.entries(baseline.viewports[width]))for(const [axis,recorded] of Object.entries(expected)){
   if(selector==='.st-key-objects_actions'&&axis==='y')continue; //9.45 pins the terminal gap, all other axes remain strict.
   // Owner-approved2.18 adds one service row and raises only Price/VAT values to30px
   const shifted=selector==='.objects-pricing-row--project-cost'||selector.startsWith('.objects-pricing-summary')||selector==='.st-key-objects_actions';
   const larger=selector==='.objects-pricing-summary-price'||selector==='.objects-pricing-summary-vat';
   //2.19 reserves the same two-line helper region in every row, keeping all
   // existing field axes and typography. Only row heights/later y positions move.
   const rowHeight=133, rowGrowth=rowHeight-baseline.viewports[width]['.objects-pricing-row--project-cost'].height;
   const wholeRow=selector==='.objects-pricing-row--project-cost'||selector==='.objects-pricing-row:not(.objects-pricing-row--project-cost)';
   const laterGrowth=selector==='.objects-pricing-row--project-cost'?rowGrowth:selector.startsWith('.objects-pricing-summary')||selector==='.st-key-objects_actions'?3*rowGrowth:0;
   const value=axis==='width'&&selector in intrinsicWidths?intrinsicWidths[selector]:recorded+(axis==='y'&&selector!=='h1.workflow-title'?-26:0)+(axis==='y'&&shifted?actual.productionHeight:0)+(axis==='y'?laterGrowth:0)+(axis==='height'&&larger?14.40625:0)+(axis==='height'&&wholeRow?rowGrowth:0);
   assert(Math.abs(actual.preserved[selector][axis]-value)<.1,JSON.stringify({width,selector,axis,expected:value,actual:actual.preserved[selector][axis]}));
  }
  assert.equal(actual.productionHeight,133);
  assert.equal(await core.locator('.objects-pricing-row').evaluateAll(nodes=>new Set(nodes.map(n=>n.getBoundingClientRect().height)).size),1,'Object and service divider intervals match');
  await checkClosingGap(frame,'.st-key-objects_actions');
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
 for(const field of [core.locator('.objects-pricing-sale-cell .objects-pricing-price-input').first(),core.locator('[data-object-key="delivery"] .objects-pricing-price-input')]){
  for(const x of [8,50,100]){
   await field.click({position:{x,y:20}});
   assert(await field.evaluate(input=>{const s=getSelection(),r=s.getRangeAt(0).cloneRange();r.selectNodeContents(input);r.setEnd(s.anchorNode,s.anchorOffset);return r.toString().length===input.textContent.length;}),'Pointer entry always positions the shared end caret');
  }
  await field.press('Tab');
 }
 const production=core.getByRole('textbox',{name:'Estimated production time',exact:true});
 await production.click();await production.pressSequentially('1');
 assert(await production.evaluate(input=>{const r=document.createRange();r.selectNodeContents(input);const t=r.getBoundingClientRect(),b=input.getBoundingClientRect();return Math.abs(t.x+t.width/2-b.x-b.width/2)<1;}),'Active day text stays centered');
 const financialBefore=await core.locator('[data-summary-field]').allTextContents();
 const productionSaved=page.waitForResponse(response=>response.url().includes('/rfq_estimate_pricing_overrides')&&response.request().method()==='POST'&&response.request().postDataJSON()?.field==='production_time_working_days');
 await production.fill('15');await production.press('Tab');assert.equal((await productionSaved).status(),204);
 assert.equal(JSON.parse(readFileSync(prices)).find(row=>row.object_key==='__project__').value,15);
 assert.deepEqual(await core.locator('[data-summary-field]').allTextContents(),financialBefore,'Production days never enter financial totals');
 assert.equal(await production.innerText(),'15');
 await production.evaluate(input=>{const data=new DataTransfer();data.setData('text/plain','12.5');input.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:data}));});
 assert.equal(await production.innerText(),'15','Fractional day paste is rejected without silently concatenating digits');
 const totalStyles=await core.locator('[data-summary-field]').evaluateAll(nodes=>nodes.map(n=>({field:n.dataset.summaryField,font:getComputedStyle(n).fontFamily,size:getComputedStyle(n).fontSize,weight:getComputedStyle(n).fontWeight,color:getComputedStyle(n).color})));
 assert(totalStyles.every(s=>s.font===totalStyles[2].font&&s.size==='30px'));
 assert(totalStyles.slice(0,2).every(s=>s.weight==='400'&&s.color==='rgb(23, 19, 28)'));assert.equal(totalStyles[2].weight,'700');
 report.productionTime={saved:15,totalsUnchanged:true,styles:totalStyles};

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
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
 assert.equal(await core.getByRole('textbox',{name:'Estimated production time',exact:true}).innerText(),'15');
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
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
 await waitPrice('delivery',222);
 assert.equal((await service('delivery').innerText()).replace(/[^0-9]/g,''),'222');
 priceDelay=0;priceFailure=true;
 await service('installation').fill('444');await service('installation').press('Tab');
 await frame.waitForFunction(()=>document.querySelector('[data-object-key="installation"] .objects-pricing-price-input')?.getAttribute('aria-invalid')==='true');
 assert.equal((await service('installation').innerText()).replace(/[^0-9]/g,''),'444');
 assert.equal(JSON.parse(readFileSync(prices)).find(row=>row.object_key==='installation').value,321);
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
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
 assert.equal(await core.locator('.object-detail-quantity-input').innerText(),'2','Object Detail must show the saved quantity, including a warm cached card');
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
 assert.equal(await quantity.innerText(),'2','Quantity blur save survives Review/Back');
 quantityDelay=500;
 await quantity.fill('3');await quantity.press('Tab');
 await core.getByRole('link',{name:/^(Done|Review)$/i}).press('Enter');
 await core.locator('.object-detail-quantity-input').waitFor();
 assert.equal(await core.locator('.object-detail-quantity-input').innerText(),'3','Keyboard Review waits for its pending quantity write');
 quantityDelay=0;
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
 await quantity.fill('4');await quantity.press('Tab');
 await quantity.fill('5');await quantity.press('Tab');
 await core.locator('.objects-quantity-saving-overlay.is-visible').waitFor({state:'hidden'});
 assert.equal(JSON.parse(readFileSync(statePath('object-quantities.json')))['estimate-ui-saved:object-001'],5,'A delayed older quantity cannot overwrite the latest edit');
 quantityFailure=true;
 const nextFieldSelection=await frame.evaluate(async()=>{
  const price=document.querySelector('.objects-pricing-price-input');
  const quantity=document.querySelector('[data-object-quantity-input]');
  price.focus();quantity.focus();
  const selection=getSelection(),range=document.createRange();
  range.selectNodeContents(quantity);selection.removeAllRanges();selection.addRange(range);
  await new Promise(resolve=>setTimeout(resolve,10));
  return {value:quantity.textContent,selected:selection.toString(),active:document.activeElement===quantity};
 });
 assert.equal(nextFieldSelection.selected,nextFieldSelection.value,'Previous price blur must preserve selection in the next active quantity field');
 assert(nextFieldSelection.active,'Previous price blur must preserve the next active field');
 await quantity.fill('6');await quantity.press('Tab');
 await frame.waitForFunction(()=>document.querySelector('[data-object-quantity-input]')?.getAttribute('aria-invalid')==='true');
 assert.equal(await quantity.innerText(),'6','Failed quantity save retains the requested value');
 assert.equal(JSON.parse(readFileSync(statePath('object-quantities.json')))['estimate-ui-saved:object-001'],5);
 await core.getByRole('link',{name:/^(Done|Review)$/i}).press('Enter');
 assert.equal(await core.locator('.object-detail-quantity-input').count(),0,'Review must not proceed after a rejected quantity write');
 quantityFailure=false;
 await quantity.press('Tab');
 await core.locator('.objects-quantity-saving-overlay.is-visible').waitFor({state:'hidden'});
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 assert.equal(await core.locator('.object-detail-quantity-input').innerText(),'6','Retry publishes the accepted canonical quantity');
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 assert.equal((await core.locator('.objects-pricing-self-cost-cell').first().innerText()).replace(/[^0-9]/g,''),'1000','Commercial copies do not divide configured unit cost');
 await quantity.fill('1');await quantity.press('Tab');
 await core.locator('.objects-quantity-saving-overlay.is-visible').waitFor({state:'hidden'});
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 assert.equal(await core.locator('.object-detail-quantity-input').innerText(),'1','The card also reflects quantity reduced back to one');
 await move(core.locator('.object-detail-footer-button--primary'),'objects');
 const reopened=await browser.newPage({viewport:{width:390,height:1000}});
 await reopened.goto('http://127.0.0.1:8798/');await reopened.locator('iframe.is-ready').waitFor();
 const reopenedCore=reopened.frameLocator('#costerly-app-frame');
 await reopenedCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await reopenedCore.getByRole('button',{name:/^continue to project$/i}).click();
 await reopenedCore.locator('.objects-pricing-table').waitFor();
 for(const [key,value] of [['delivery',123],['installation',321],['object-001',1750]]){
  assert.equal((await reopenedCore.locator('.objects-pricing-row[data-object-key="'+key+'"] .objects-pricing-price-input').innerText()).replace(/[^0-9]/g,''),String(value),'New browser context reads saved '+key);
 }
 await reopened.close();
 report.blurPersistence={roundTripWithoutSetPrices:true,slowWrite:true,failedWriteRetained:true,retry:true,
  latestEditWins:true,quantityRoundTrip:true,detailQuantity:true,pendingQuantityReview:true,
  latestQuantityWins:true,quantityFailureRetry:true,realDetailPrefetch:true,newBrowserContext:true,confirmationWaitsForWrite:true};
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
 rmSync(statePath('generation-failure'));
 writeFileSync(statePath('proposal-delay'),'0.8');
 const firstDownloadPromise=page.waitForEvent('download',{timeout:10000});
 await generate().click();
 await core.getByRole('button',{name:'GENERATING…',exact:true}).waitFor({timeout:500});
 assert(await core.getByRole('button',{name:'GENERATING…',exact:true}).isDisabled());
 const firstDownload=await firstDownloadPromise;
 rmSync(statePath('proposal-delay'));
 assert.equal(await firstDownload.failure(),null);
 report.firstProposalDownload={name:firstDownload.suggestedFilename()};
 await frame.waitForFunction(()=>document.querySelector('.objects-workflow-stages [data-stage="3"]')?.dataset.state==='complete');
 // The stage table is emitted before native footer actions. Assert the
 // completed native render, not the outgoing button between Streamlit deltas.
 const completedDownload=core.locator('.st-key-final_approval_approved').getByRole('link',{name:'Download Proposal',exact:true});
 await completedDownload.waitFor({timeout:1000});
 assert.equal(await generate().count(),0,'Successful Generate becomes Download');
 await frame.waitForFunction(expected=>getComputedStyle(document.querySelector('.st-key-objects_set_prices button')).backgroundColor===expected,unconfirmedColor,{timeout:1000});
 assert.equal(await set().evaluate(n=>getComputedStyle(n).backgroundColor),unconfirmedColor,'After success Set Prices returns to its ordinary appearance');
 await page.mouse.move(0,0);
 await frame.waitForFunction(()=>getComputedStyle(document.querySelector('.st-key-final_approval_approved a')).color==='rgb(47, 141, 72)',{},{timeout:1000});
 assert.equal(await completedDownload.evaluate(n=>getComputedStyle(n).color),'rgb(47, 141, 72)','Completed Download uses accepted green');
 const proposal=JSON.parse(readFileSync(statePath('generated-proposal.json')));assert.equal(proposal.rows[0].sale_price_unit,1850);assert.equal(proposal.production_time_working_days,15);
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,1);
 const download=core.locator('.objects-pricing-downloads').getByRole('link',{name:'Download Proposal',exact:true});await download.waitFor();
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
 assert.equal(await download.getAttribute('href'),'http://127.0.0.1:8798/generated-proposal.pdf');
 assert.equal(await completedDownload.getAttribute('href'),await download.getAttribute('href'));
 const greenDownloadPromise=page.waitForEvent('download',{timeout:10000});await completedDownload.click();
 const greenDownload=await greenDownloadPromise;assert.equal(await greenDownload.failure(),null);
 assert.equal(readFileSync(await firstDownload.path(),'utf8'),readFileSync(await greenDownload.path(),'utf8'));
 const repeatDownloadPromise=page.waitForEvent('download',{timeout:10000});
 await download.click();
 const repeatedDownload=await repeatDownloadPromise;
 assert.equal(await repeatedDownload.failure(),null);
 assert.equal(readFileSync(await firstDownload.path(),'utf8'),readFileSync(await repeatedDownload.path(),'utf8'));
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,1,'Repeat download does not regenerate');
 assert.equal(firstDownload.suggestedFilename(),'Proposal_V1.pdf');
 const issuedV1=readFileSync(statePath('generated-proposal.json'),'utf8');
 await editPrice(1900);
 const revokedDownload=core.locator('.st-key-final_approval_approved a');
 assert.equal(await revokedDownload.getAttribute('href'),null,'An input edit immediately revokes the issued action');
 assert.equal(await revokedDownload.getAttribute('aria-disabled'),'true');
 assert.equal(await revokedDownload.innerText(),'GENERATE PROPOSAL');
 assert.equal(await core.locator('.objects-pricing-downloads a').getAttribute('href'),null,'The secondary old PDF is also inactive');
 await set().click();await generate().waitFor();assert(await generate().isEnabled());
 const version2Promise=page.waitForEvent('download',{timeout:10000});await generate().click();
 const version2=await version2Promise;assert.equal(version2.suggestedFilename(),'Proposal_V2.pdf');
 await completedDownload.waitFor();
 assert.equal(JSON.parse(readFileSync(statePath('generated-proposal.json'))).version_number,2);
 assert.equal(JSON.parse(issuedV1).rows[0].sale_price_unit,1850,'Issued V1 snapshot is preserved');
 const days=core.locator('[data-commercial-term="production_time_working_days"] .objects-pricing-price-input');
 await days.fill('16');await days.press('Tab');
 assert.equal(await revokedDownload.getAttribute('href'),null,'Production time is also a proposal input');
 await set().click();await generate().waitFor();assert(await generate().isEnabled());
 const version3Promise=page.waitForEvent('download',{timeout:10000});await generate().click();
 const version3=await version3Promise;assert.equal(version3.suggestedFilename(),'Proposal_V3.pdf');
 await completedDownload.waitFor();
 assert.equal(JSON.parse(readFileSync(statePath('generated-proposal.json'))).production_time_working_days,16);
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,3);
 const currentV3=await completedDownload.getAttribute('href');
 await move(core.getByRole('link',{name:/^(Done|Review)$/i}),'object_detail');
 await move(core.getByRole('link',{name:'Back to Project',exact:true}),'objects');
 await completedDownload.waitFor();
 assert.equal(await completedDownload.getAttribute('href'),currentV3,'Viewing a card without edits keeps the issued version');
 await days.fill('17');await days.fill('16');await days.press('Tab');
 assert.equal(await revokedDownload.getAttribute('href'),null,'Reverting an edit still requires explicit confirmation');
 await set().click();await generate().waitFor();assert(await generate().isEnabled());
 const version4Promise=page.waitForEvent('download',{timeout:10000});await generate().click();
 const version4=await version4Promise;assert.equal(version4.suggestedFilename(),'Proposal_V4.pdf');
 await completedDownload.waitFor();
 assert.equal(JSON.parse(readFileSync(statePath('generated-proposal.json'))).version_number,4);
 report.revisions={versions:[1,2,3,4],priceEditRevoked:true,productionTimeEditRevoked:true,oldSnapshotPreserved:true,revertedEditReconfirmed:true,unchangedViewKeepsVersion:true};
 assert.deepEqual(errors,[]);report.errors=errors;
 await page.screenshot({path:reportPath('objects-v2-generated.png'),fullPage:true});
 writeFileSync(config,JSON.stringify({objects_v2:true,admin:false,project_name:'A3'}));
 const member=await browser.newPage({viewport:{width:1440,height:1000}}),memberCore=member.frameLocator('#costerly-app-frame');
 await member.goto('http://127.0.0.1:8798/');await member.locator('iframe.is-ready').waitFor();
 await memberCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await memberCore.getByRole('button',{name:/continue to project/i}).waitFor();await memberCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 await memberCore.getByRole('button',{name:/continue to project/i}).click();await memberCore.locator('.objects-pricing-table').waitFor();await memberCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await memberCore.locator('.objects-cycle-metrics,.objects-metrics-toggle').count(),0,'Technical metrics reuse existing platform-admin visibility');
 assert.equal((await memberCore.locator('h1 .workflow-title-text').textContent()).replace(/\s+/g,' '),'Project A3');
 assert.equal(await memberCore.getByRole('textbox',{name:'Estimated production time',exact:true}).innerText(),'16','Reopening reads the newly saved production time');
 await member.setViewportSize({width:390,height:1000});
 assert(await memberCore.getByRole('textbox',{name:'Estimated production time',exact:true}).isVisible());
 await member.close();report.nonAdminMetricsHidden=true;
 const longName='A very long custom furniture project name for a complete residential interior and multiple display cabinets';
 writeFileSync(config,JSON.stringify({objects_v2:true,admin:false,project_name:longName}));
 const longPage=await browser.newPage({viewport:{width:1280,height:1000}}),longCore=longPage.frameLocator('#costerly-app-frame');
 await longPage.goto('http://127.0.0.1:8798/');await longPage.locator('iframe.is-ready').waitFor();
 await longCore.getByRole('button',{name:'Last Estimate',exact:true}).click();await longCore.getByRole('button',{name:/continue to project/i}).click();
 await longCore.locator('.objects-pricing-table').waitFor();
 await longCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await longCore.locator('.project-title-name').innerText(),longName);
 const longFrame=await(await longPage.locator('#costerly-app-frame').elementHandle()).contentFrame();
 const {nameBox,labelBox,markBox}=await longFrame.evaluate(async()=>{
  await document.fonts.ready;await new Promise(requestAnimationFrame);
  const box=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
  return{nameBox:box('.project-title-name'),labelBox:box('.project-title-label'),markBox:box('.workflow-title-mark')};
 });
 assert(nameBox.y>=labelBox.y+labelBox.height-1,'Long names start below Project');
 assert(markBox.y+markBox.height/2>=labelBox.y&&markBox.y+markBox.height/2<=labelBox.y+labelBox.height,
        'The mark stays on the Project line: '+JSON.stringify({markBox,labelBox,nameBox}));
 report.longTitle={markBox,labelBox,nameBox};
 await longPage.screenshot({path:reportPath('project-long-title.png'),fullPage:true});await longPage.close();
 writeFileSync(config,JSON.stringify({objects_v2:true,project_name:longName}));
 const adminTitlePage=await browser.newPage({viewport:{width:1280,height:1000}}),adminTitleCore=adminTitlePage.frameLocator('#costerly-app-frame');
 await adminTitlePage.goto('http://127.0.0.1:8798/');await adminTitlePage.locator('iframe.is-ready').waitFor();
 await adminTitleCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await adminTitleCore.getByRole('button',{name:/continue to project/i}).click();
 await adminTitleCore.locator('.objects-pricing-table').waitFor();
 await adminTitleCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const adminTitleFrame=await(await adminTitlePage.locator('#costerly-app-frame').elementHandle()).contentFrame();
 report.adminTitleClearance=[];
 for(const width of [1280,901,390,1440]){
  await adminTitlePage.setViewportSize({width,height:1000});
  const clearance=await adminTitleFrame.evaluate(async()=>{
   await document.fonts.ready;await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);
   const name=document.querySelector('.project-title-name'),range=document.createRange();range.selectNodeContents(name);
   const box=r=>({x:r.x,y:r.y,width:r.width,height:r.height});
   return {lines:[...range.getClientRects()].map(box),toolbar:box(document.querySelector('.st-key-objects_header_toolbar').getBoundingClientRect()),text:name.textContent};
  });
  assert.equal(clearance.text,longName);
  assert(clearance.lines.every(line=>line.x+line.width<=clearance.toolbar.x-8 || line.x>=clearance.toolbar.x+clearance.toolbar.width+8 || line.y+line.height<=clearance.toolbar.y-1 || line.y>=clearance.toolbar.y+clearance.toolbar.height+1),
         'Project text must wrap clear of the menu and technical dashboard: '+JSON.stringify({width,...clearance}));
  report.adminTitleClearance.push({width,...clearance});
  if(width===1280){
   await adminTitleCore.getByRole('button',{name:'Collapse technical metrics',exact:true}).click();
   assert.equal(await adminTitleCore.locator('.objects-metrics-toggle').getAttribute('aria-expanded'),'false');
   await adminTitleCore.getByRole('button',{name:'Expand technical metrics',exact:true}).click();
  }
 }
 await adminTitlePage.screenshot({path:reportPath('project-admin-long-title.png'),fullPage:true});await adminTitlePage.close();
 writeFileSync(config,JSON.stringify({objects_v2:true,project_name:'Before edit',project_name_edit:true}));
 const editPage=await browser.newPage({viewport:{width:1280,height:1000}}),editCore=editPage.frameLocator('#costerly-app-frame');
 await editPage.goto('http://127.0.0.1:8798/');await editPage.locator('iframe.is-ready').waitFor();
 await editCore.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await editCore.getByRole('button',{name:/continue to project/i}).click();await editCore.locator('.objects-pricing-table').waitFor();
 await editCore.getByRole('button',{name:'Back to File Review',exact:true}).click();
 await editCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const projectName=editCore.getByRole('textbox',{name:'Project name',exact:true});
 await projectName.fill('ADA renamed');await projectName.press('Tab');
 for(let attempt=0;attempt<30&&!existsSync(statePath('project-metadata.json'));attempt++)await new Promise(resolve=>setTimeout(resolve,100));
 assert.equal(JSON.parse(readFileSync(statePath('project-metadata.json'))).project_name,'ADA renamed','File Review acknowledged the rename before Continue');
 await editCore.getByRole('button',{name:/continue to project/i}).click();
 await editCore.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal((await editCore.locator('h1 .workflow-title-text').innerText()).replace(/\s+/g,' '),'Project ADA renamed','Renaming a completed project appears on the first ready Project render');
 assert.equal(JSON.parse(readFileSync(statePath('project-metadata.json'))).project_name,'ADA renamed');
 report.projectRename={saved:true,completedEstimate:true,immediateReadyTitle:true};
 await editPage.setViewportSize({width:3840,height:3000});
 const tallProject=await editCore.locator('.st-key-objects_actions').evaluate(node=>({top:node.getBoundingClientRect().top,summary:document.querySelector('.objects-pricing-summary').getBoundingClientRect().bottom}));
 assert(tallProject.top-tallProject.summary<120,'Zoomed-out Project must not stretch the gap: '+JSON.stringify(tallProject));
 report.tallProject=tallProject;await editPage.close();
 writeFileSync(config,JSON.stringify({objects_v2:true,project_history:true}));
 await page.setViewportSize({width:1440,height:1000});
 await core.getByRole('button',{name:'All Projects',exact:true}).click();
 await core.locator('.projects-table-card').waitFor();await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const authCount=()=>((readFileSync(statePath('browser-journal'),'utf8').match(/auth checked/g)||[]).length);
 const runsBefore=authCount();
 await core.locator('.projects-partner > summary').click();
 const historyProject=core.locator('[data-project-id="history-project"]');
 await historyProject.locator(':scope > summary').click();
 assert.equal(await historyProject.locator('.projects-file').count(),2,'Different contents with the same filename stay distinct');
 const sourceA=historyProject.locator('[data-source-file-id="source-a"]');
 await sourceA.locator(':scope > summary').click();await sourceA.locator('.projects-calculation > summary').click();
 assert.equal(await sourceA.locator('.projects-version').count(),2,'One calculation retains all issued versions');
 const oldVersion=sourceA.locator('[data-version-number="1"]');await oldVersion.locator(':scope > summary').click();
 assert.equal(await oldVersion.locator('tbody tr').count(),1);
 const historyDownloadPromise=page.waitForEvent('download',{timeout:10000});await oldVersion.getByRole('link',{name:'PDF',exact:true}).click();
 const historyDownload=await historyDownloadPromise;assert.equal(historyDownload.suggestedFilename(),'Proposal_V1.pdf');
 assert.equal(readFileSync(await historyDownload.path(),'utf8'),readFileSync(await firstDownload.path(),'utf8'),'Historical PDF remains the issued bytes');
 const generatedProject=core.locator('[data-project-id="generated-project"]');
 await generatedProject.locator(':scope > summary').click();
 await generatedProject.locator('.projects-file > summary').click();await generatedProject.locator('.projects-calculation > summary').click();
 assert.equal(await generatedProject.locator('.projects-version').count(),4,'Every generated proposal is visible in All Projects');
 const issuedFirst=generatedProject.locator('[data-version-number="1"]');await issuedFirst.locator(':scope > summary').click();
 assert((await issuedFirst.locator('tbody').innerText()).includes('1 850'),'Old inputs are retained after newer prices');
 assert.equal(authCount(),runsBefore,'Native history expansion/download requires no Python rerun');
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,4,'History browsing never creates a version');
 const noPartner=core.locator('.projects-table-card > .projects-projects-body [data-project-id="partnerless"]');
 await noPartner.locator(':scope > summary').click();
 assert.equal(await noPartner.locator('.projects-calculation').count(),1,'Partnerless legacy history remains available');
 assert(!(await core.locator('.projects-table-card').innerText()).includes('Unknown Partner'));
 await page.screenshot({path:reportPath('all-projects-version-history.png'),fullPage:true});
 await page.setViewportSize({width:390,height:1000});assert(await oldVersion.getByRole('link',{name:'PDF',exact:true}).isVisible());
 report.allProjects={twoSameNameSources:true,allVersionsVisible:true,oldInputsRetained:true,downloadUnchanged:true,noRerun:true,partnerless:true,mobile:true};
 await page.setViewportSize({width:1440,height:1000});
 await core.getByRole('button',{name:'New Estimate',exact:true}).click();
 await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 await core.getByRole('button',{name:/continue to project/i}).click();
 await completedDownload.waitFor();await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 await core.getByRole('button',{name:'Back to File Review',exact:true}).click();
 await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const objectName=core.getByRole('textbox',{name:'Object name',exact:true});
 await objectName.fill('Renamed reception');await objectName.press('Tab');
 await frame.waitForFunction(()=>document.querySelector('[aria-label="Object name"]')?.value==='Renamed reception');
 for(let attempt=0;attempt<50&&!existsSync(statePath('object-names.json'));attempt++)await new Promise(resolve=>setTimeout(resolve,100));
 assert.equal(JSON.parse(readFileSync(statePath('object-names.json')))['object-001'],'Renamed reception');
 await core.getByRole('button',{name:/continue to project/i}).click();
 await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await core.locator('.objects-pricing-name').first().innerText(),'Renamed reception');
 assert(await generate().isDisabled(),'A name change also requires Set Prices');
 await set().click();
 await frame.waitForFunction(()=>document.querySelector('.objects-workflow-stages [data-stage="3"]')?.dataset.state==='current');
 assert(await generate().isEnabled());
 const renamedDownloadPromise=page.waitForEvent('download',{timeout:10000});await generate().click();
 const renamedDownload=await renamedDownloadPromise;assert.equal(renamedDownload.suggestedFilename(),'Proposal_V5.pdf');
 const savedHistory=JSON.parse(readFileSync(statePath('generated-proposal-history.json')));
 assert.equal(savedHistory.at(-1).rows[0].name,'Renamed reception');
 assert.equal(savedHistory[0].rows[0].name,'Saved bench','Renaming never rewrites an issued snapshot');
 report.objectRename={persisted:true,reconfirmed:true,version:5,oldNameRetained:true};
 writeFileSync(reportPath('objects-v2.json'),JSON.stringify(report,null,2));
 console.log('Objects V2.4 passed: approved26px body lift, original geometry/field boundaries, top-right menu+metrics with4px offset, stacked half-width documents, local metrics toggle and original pricing/approval/proposal flow.');
}catch(error){
 console.error('Original Objects V2 failure:',error);
 for(const page of browser.contexts().flatMap(context=>context.pages())){
  try{
  try{await page.screenshot({path:reportPath('objects-v2-latest-failure.png'),fullPage:true});}
  catch(captureError){console.error('Failure screenshot unavailable:',captureError.message);}
  const handle=await page.locator('#costerly-app-frame').elementHandle();const frame=handle&&await handle.contentFrame();
  if(frame)writeFileSync(reportPath('objects-v2-latest-failure.json'),JSON.stringify(await frame.evaluate(()=>({text:document.body.innerText,confirmationId:document.querySelector('.objects-workflow-stages')?.dataset.confirmationId,dirtyDrafts:[...(window.__costerlyProposalDrafts||new Map())],issuedAction:{hasHref:!!document.querySelector('.st-key-final_approval_approved a')?.getAttribute('href'),disabled:document.querySelector('.st-key-final_approval_approved a')?.getAttribute('aria-disabled')},receipt:document.getElementById('objects-actions-error')?.outerHTML,pending:[...(window.__costerlyObjectsPricingWrites?.latest||new Map())].map(([key,entry])=>({key,ok:entry.ok})),serviceInputs:[...document.querySelectorAll('.objects-pricing-project-cost-cell .objects-pricing-price-input')].map(n=>({key:n.closest('.objects-pricing-row')?.dataset.objectKey,text:n.textContent,active:document.activeElement===n,dirty:n.dataset.editDirty})),buttons:[...document.querySelectorAll('.st-key-objects_actions button')].map(button=>({text:button.innerText,disabled:button.disabled,busy:button.getAttribute('aria-busy'),phase:button.dataset.objectsPhase}))})),null,2));
  }catch(captureError){console.error('Failure DOM unavailable:',captureError.message);}
 }
 throw error;
}finally{await browser.close();server.close();}
