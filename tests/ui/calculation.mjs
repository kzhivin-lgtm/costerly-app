import { statePath, reportPath, chromeOptions, checkClosingGap } from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, rmSync, existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {chromium} from 'playwright';
const config=statePath('scenario.json'), journal=statePath('browser-journal');
const settings=value=>writeFileSync(config,JSON.stringify(value));
const server=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 const html=readFileSync('cloudflare/index.html','utf8').replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(html);
});
await new Promise(resolve=>server.listen(8796,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions), report={};
async function boot(value={},width=1280,height=1000){
 settings(value);
 const page=await browser.newPage({viewport:{width,height}});
 page.on('pageerror',error=>console.error('browser error',error.message));
 page.setDefaultTimeout(12000);
 await page.goto('http://127.0.0.1:8796/');
 const core=page.frameLocator('#costerly-app-frame');
 await page.locator('iframe.is-ready').waitFor();
 const frame=await (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 return {page,core,frame};
}

async function frontPanelChecks(){
 for(const width of [1280,390]){
  for(const name of ['front-choice','full-cost-totals.json','full-cost-lines.json'])rmSync(statePath(name),{force:true});
  const {page,core,frame}=await boot({front_panels:true,front_delay:0.6},width);
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  await core.getByRole('button',{name:/^continue to project$/i}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('.object-detail-materials-band > summary').click();
  const picker=core.getByRole('combobox',{name:'Front panels',exact:true});
  await picker.waitFor();
  const placement=await picker.evaluate(input=>{
   const label=input.closest('label'), text=label.querySelector('span');
   return {gap:input.getBoundingClientRect().left-text.getBoundingClientRect().right,
    arrow:getComputedStyle(input).backgroundPosition,appearance:getComputedStyle(input).appearance};
  });
  assert.ok(Math.abs(placement.gap-16)<1,JSON.stringify(placement));
  assert.equal(placement.appearance,'none');
  assert.ok(placement.arrow.includes('12px'),JSON.stringify(placement));
  assert.equal(await picker.inputValue(),'ldsp');
  assert.equal(await picker.locator('option').count(),4);
  assert.deepEqual(await picker.locator('option').allTextContents(),['LDSP','MDF Veneered','MDF Raw','Plywood']);
  const initialPrice=await core.locator('.object-detail-unit-price').first().innerText();
  const initialCost=await core.locator('.object-detail-final [data-final="excl_vat"]').innerText();
  assert.equal(initialCost,'₪1\u202f000','Each replacement scenario starts from its saved LDSP source');
  const originalDocument=await frame.evaluate(()=>{
   window.frontPanelDocumentWitness=crypto.randomUUID();return window.frontPanelDocumentWitness;
  });
  const save=core.locator('.object-detail-material-save');
  const immediate=await picker.evaluate(input=>{
   input.value='mdf';input.dispatchEvent(new Event('change',{bubbles:true}));
   const overlays=document.querySelectorAll('.object-detail-material-changing'),node=overlays[0];
   const label=node?.querySelector('.costerly-workflow-status'),style=label&&getComputedStyle(label);
   const reference=document.createElement('span');reference.className='costerly-workflow-status';document.body.append(reference);
   const shared=getComputedStyle(reference);
   const typography=Boolean(style)&&['fontFamily','fontSize','fontWeight','letterSpacing','lineHeight'].every(key=>style[key]===shared[key]);
   reference.remove();
   const rect=node?.getBoundingClientRect();
   return {count:overlays.length,text:node?.textContent,role:node?.getAttribute('role'),
    color:node&&getComputedStyle(node).backgroundColor,
    covers:rect?.left===0&&rect?.top===0&&rect?.width===innerWidth&&rect?.height===innerHeight,
    typography,background:style?.backgroundColor,shadow:style?.boxShadow,padding:style?.padding,border:style?.borderWidth};
  });
  assert.equal(immediate.count,1);assert.equal(immediate.text,'Changing material…');
  assert.equal(immediate.role,'status');assert.equal(immediate.covers,true);
  assert.equal(immediate.color,'rgb(241, 239, 239)','Opaque shared loading background prevents underlying table text from showing through');
  assert.equal(immediate.typography,true);assert.equal(immediate.background,'rgba(0, 0, 0, 0)');
  assert.equal(immediate.shadow,'none');assert.equal(immediate.padding,'0px');assert.equal(immediate.border,'0px');
  await core.getByRole('button',{name:'Calculating…',exact:true}).waitFor();
  await page.screenshot({path:reportPath('front-material-changing-'+width+'.png')});
  await core.getByRole('button',{name:'Save changes',exact:true}).waitFor();
  assert.equal(await core.locator('.object-detail-material-changing').count(),0);
  assert.equal(await picker.inputValue(),'mdf');
  assert.equal(await core.locator('.object-detail-material-name').first().innerText(),'MDF 17 mm');
  assert.notEqual(await core.locator('.object-detail-unit-price').first().innerText(),initialPrice);
  assert.notEqual(await core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),initialCost);
  assert.equal(await frame.evaluate(()=>window.frontPanelDocumentWitness),originalDocument);
  assert.ok(!existsSync(statePath('front-choice')));
  assert.equal(await save.isEnabled(),true);
  if(width===1280){
   settings({front_panels:true,front_failure:true});
   await picker.selectOption('veneered_mdf');
   await core.getByText('Controlled front material failure.',{exact:true}).waitFor();
   assert.equal(await core.locator('.object-detail-material-changing').count(),0);
   assert.equal(await picker.inputValue(),'veneered_mdf');
   settings({front_panels:true,front_delay:0.3});
   await picker.selectOption('ldsp');
   await picker.selectOption('mdf');
   assert.equal(await core.locator('.object-detail-material-changing').count(),1);
   await core.getByRole('button',{name:'Save changes',exact:true}).waitFor();
   await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
  }
  await save.click();
  if(width===1280){
   await core.getByRole('button',{name:'Saving…',exact:true}).waitFor();
   await picker.selectOption('plywood');
   assert.equal(await core.locator('.object-detail-material-changing').count(),1);
   await core.getByRole('button',{name:'Save changes',exact:true}).waitFor();
   await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
   assert.equal(readFileSync(statePath('front-choice'),'utf8'),'mdf');
   assert.equal(await picker.inputValue(),'plywood');
   await picker.selectOption('mdf');
  }
  await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  assert.equal(readFileSync(statePath('front-choice'),'utf8'),'mdf');
  await core.getByRole('link',{name:'Back to Project',exact:true}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('.object-detail-materials-band > summary').click();
  assert.equal(await core.getByRole('combobox',{name:'Front panels',exact:true}).inputValue(),'mdf');
  if(width===390){
   await core.getByRole('combobox',{name:'Front panels',exact:true}).selectOption('plywood');
   await core.getByRole('button',{name:'Calculating…',exact:true}).waitFor();
   await core.getByRole('link',{name:'APPROVE',exact:true}).click();
   await core.locator('.objects-pricing-table').waitFor();
   assert.equal(await core.locator('.object-detail-material-changing').count(),0);
   assert.equal(readFileSync(statePath('front-choice'),'utf8'),'plywood');
  }
  await page.close();
 }
 rmSync(statePath('object-approvals.json'),{force:true});
 rmSync(statePath('front-choice'),{force:true});
 const {page,core,frame}=await boot({front_panels:true,front_delay:1});
 await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await core.getByRole('button',{name:/^continue to project$/i}).click();
 await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
 await core.locator('.object-detail-materials-band > summary').click();
 await frame.evaluate(()=>{
  const original=window.setTimeout;
  window.frontMaterialOriginalTimeout=original;
  window.setTimeout=function(fn,ms,...args){return original.call(this,fn,ms===90000?200:ms,...args);};
 });
 const picker=core.getByRole('combobox',{name:'Front panels',exact:true});
 await picker.selectOption('mdf');
 await core.getByRole('button',{name:'Retry save',exact:true}).waitFor();
 assert.equal(await core.locator('.object-detail-material-changing').count(),0);
 assert.equal(await picker.inputValue(),'mdf');
 assert.equal(await core.getByRole('button',{name:'Retry save',exact:true}).isEnabled(),true);
 await frame.evaluate(()=>{window.setTimeout=window.frontMaterialOriginalTimeout;});
 settings({front_panels:true,front_delay:0.05});
 await picker.selectOption('plywood');
 await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
 assert.equal(await core.locator('.object-detail-material-changing').count(),0);
 assert.equal(await core.locator('.object-detail-material-name').first().innerText(),'Plywood 17 mm');
 await page.close();
 report.frontPanels={viewports:[1280,390],automaticPreview:true,explicitSave:true,
  immediateChangingCover:true,timeoutRetainsDraft:true};
}

async function detailSaveChecks(){
 for(const width of [1758,390]){
  for(const name of ['front-choice','object-quantities.json','full-cost-totals.json','full-cost-lines.json','labor-hours.json','object-approvals.json'])rmSync(statePath(name),{force:true});
  const {page,core,frame}=await boot({front_panels:true,labor_ready:true},width,933);
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  report['fileReviewFooter'+width]=await checkClosingGap(frame,'.st-key-file_review_actions');
  await core.getByRole('button',{name:/^continue to project$/i}).click();
  report['objectsFooter'+width]=await checkClosingGap(frame,'.st-key-objects_actions');
  // The Objects suite covers the real quantity RPC. This case begins with its
  // persisted quantity, then exercises the production detail editor end to end.
  writeFileSync(statePath('object-quantities.json'),JSON.stringify({'estimate-ui-saved:object-001':3}));
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-overhead-ready="true"]').waitFor();
  const net=core.locator('.object-detail-final [data-final="excl_vat"]');
  assert.equal(await net.innerText(),'₪1\u202f018');
  await page.waitForURL('**/o/**');
  const originalUrl=page.url();
  const bandSelectors=['.object-detail-materials-band','[data-cost-band="labor"]','.object-detail-overhead-band'];
  const collapseCases=[];
  for(let mask=0;mask<8;mask++) {
   for(let index=0;index<3;index++) {
    const band=core.locator(bandSelectors[index]);
    if(await band.evaluate(n=>n.open)!==Boolean(mask&(1<<index))) await band.locator(':scope > summary').click();
   }
   const state=await frame.evaluate(()=>({
    summaryGap:document.querySelector('.object-detail-page-end').getBoundingClientRect().top-document.querySelector('.object-detail-overhead-band').getBoundingClientRect().bottom,
    final:document.querySelector('[data-final="excl_vat"]').textContent,
   }));
   if(mask===0)assert.ok(state.summaryGap>=0&&state.summaryGap<=40,JSON.stringify({width,mask,...state}));
   assert.equal(state.final,'₪1\u202f018');collapseCases.push({mask,...state});
  }
  for(const selector of bandSelectors) {
   const band=core.locator(selector);if(await band.evaluate(n=>n.open))await band.locator(':scope > summary').click();
  }
  report['collapseStates'+width]=collapseCases;
  await core.locator('.object-detail-materials-band > summary').click();
  const picker=core.getByRole('combobox',{name:'Front panels',exact:true});
  await picker.selectOption('mdf');
  const save=core.locator('.object-detail-material-save');
  await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
  const preview=await net.innerText();
  async function startSaveAndCheckLock(){
   const state=await save.evaluate(button=>{
    button.click();
    const footer=document.querySelector('.object-detail-footer-actions');
    const links=[...footer.querySelectorAll('a')];
    for(const link of links)link.click(); // Exercise the delegated guard, not only CSS hit testing.
    return {busy:footer.getAttribute('aria-busy'),links:links.map(n=>({
     text:n.textContent,disabled:n.getAttribute('aria-disabled'),tab:n.getAttribute('tabindex'),
     background:getComputedStyle(n).backgroundColor,color:getComputedStyle(n).color}))};
   });
   assert.equal(state.busy,'true');assert.equal(state.links.length,2);
   assert.ok(state.links.every(n=>n.disabled==='true'&&n.tab==='-1'&&n.background==='rgb(247, 247, 247)'&&n.color==='rgb(159, 155, 156)'),JSON.stringify(state));
   await core.getByRole('button',{name:'Saving…',exact:true}).waitFor();
   const approve=core.locator('[data-object-detail-approve]');
   await approve.focus();await approve.press('Enter');
   await page.screenshot({path:reportPath('save-navigation-locked-'+width+'.png')});
   assert.equal(page.url(),originalUrl);
  }
  settings({front_panels:true,labor_ready:true,front_delay:0.7,front_save_failure:true});
  await startSaveAndCheckLock();await core.getByRole('button',{name:'Retry save',exact:true}).waitFor();
  assert.equal(await core.locator('[data-object-detail-approve]').getAttribute('aria-disabled'),null);
  assert.equal(await core.locator('[data-streamlit-bridge-key="object_detail_back_bridge"]').getAttribute('aria-disabled'),null);
  assert.equal(page.url(),originalUrl);assert.equal(await picker.inputValue(),'mdf');
  assert.equal(await net.innerText(),preview);
  assert.equal(await save.getAttribute('data-save-error'),'');
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),false);
  assert.ok(await core.locator('.object-detail-material-edit-status').evaluate(n=>n.getBoundingClientRect().height<=1 && getComputedStyle(n).clipPath==='inset(50%)'));
  assert.equal(existsSync(statePath('front-choice')),false);
  settings({front_panels:true,labor_ready:true,front_delay:0.7});
  const started=Date.now();await startSaveAndCheckLock();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  assert.equal(await core.locator('[data-object-detail-approve]').getAttribute('aria-disabled'),null);
  assert.equal(existsSync(statePath('object-approvals.json')),false,'Approve during explicit Save must not queue approval');
  assert.equal(page.url(),originalUrl);assert.equal(await core.locator('.object-detail-title--name').count(),1);
  assert.equal(await net.innerText(),preview,JSON.stringify(await frame.evaluate(()=>({inputs:[...document.querySelectorAll('[data-field="labor_hours"]')].map(n=>({key:n.dataset.lineId,original:n.dataset.originalValue,text:n.textContent})),pending:window.__costerlyObjectDetailDraft.pendingEdits(),root:document.querySelector('[data-cost-band="labor"]').dataset,overhead:document.querySelector('[data-overhead-summary]').dataset}))));assert.equal(readFileSync(statePath('front-choice'),'utf8'),'mdf');
  assert.equal(Number(await core.locator('[data-cost-band="labor"]').getAttribute('data-labor-cost-quantity')),1);
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),true);
  await core.locator('.object-detail-materials-band > summary').click();
  await save.scrollIntoViewIfNeeded();
  const gap=await frame.evaluate(()=>{
   const actions=document.querySelector('.object-detail-footer-actions').getBoundingClientRect();
   return innerHeight-46-actions.bottom;
  });
  const collapsed=await frame.evaluate(()=>{
   const overhead=document.querySelector('.object-detail-overhead-band').getBoundingClientRect();
   const end=document.querySelector('.object-detail-page-end').getBoundingClientRect();
   return {summaryGap:end.top-overhead.bottom,closed:[...document.querySelectorAll('.object-detail-materials-band,[data-cost-band="labor"],.object-detail-overhead-band')].every(n=>!n.open)};
  });
  assert.equal(collapsed.closed,true);assert.ok(collapsed.summaryGap>=0&&collapsed.summaryGap<=40,JSON.stringify({width,...collapsed}));
  assert.ok(gap>=24,JSON.stringify({width,gap})); // Fixed Privacy remains clear; collapsed summary is no longer bottom-pinned.
  await page.screenshot({path:reportPath('detail-save-'+width+'.png'),fullPage:true});
  report['detailSave'+width]={seconds:(Date.now()-started)/1000,footerGap:gap,quantity:3,net:preview};
  await core.locator('.object-detail-materials-band > summary').click();
  await save.scrollIntoViewIfNeeded();
  const expandedGap=await frame.evaluate(()=>innerHeight-46-document.querySelector('.object-detail-footer-actions').getBoundingClientRect().bottom);
  assert.ok(Math.abs(expandedGap-26)<2,JSON.stringify({width,expandedGap}));
  await picker.selectOption('plywood');
  await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),false);
  await core.getByRole('link',{name:'Back to Project',exact:true}).click();
  await core.getByRole('button',{name:'Stay',exact:true}).click();
  assert.equal(await picker.inputValue(),'plywood');
  await core.getByRole('link',{name:'Back to Project',exact:true}).click();
  await core.getByRole('button',{name:'Leave without saving',exact:true}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('.object-detail-materials-band > summary').click();
  assert.equal(await picker.inputValue(),'mdf');
  await core.getByRole('link',{name:'APPROVE',exact:true}).click();
  await core.locator('.objects-pricing-table').waitFor();
  assert.equal(JSON.parse(readFileSync(statePath('object-approvals.json')))['object-001'],true);
  await page.close();
 }
 for(const name of ['front-choice','object-quantities.json','full-cost-totals.json','full-cost-lines.json','labor-hours.json','object-approvals.json'])rmSync(statePath(name),{force:true});
}
await detailSaveChecks();
await frontPanelChecks();
try{
 for(const name of ['fresh-active','fresh-done','fresh-shell-ready','labor-hours.json','full-cost-totals.json','full-cost-lines.json','auth-expired'])rmSync(statePath(name),{force:true});
 const fresh=await boot({fresh_calculation:true,objects_refresh_delay:1.2});
 await fresh.core.locator('.objects-pricing-table').waitFor();
 await fresh.frame.evaluate(()=>{
  window.calculationFrames=[];window.calculationSample=true;
  const sample=()=>{
   if(!window.calculationSample)return;
   const opacity=selector=>{let node=document.querySelector(selector),value=1;if(!node)return null;for(;node;node=node.parentElement)value*=Number(getComputedStyle(node).opacity);return value;};
   calculationFrames.push({tables:document.querySelectorAll('.objects-pricing-table').length,
    headerOpacity:opacity('.st-key-costerly_screen_header'),
    metricsOpacity:opacity('.objects-cycle-metrics'),
    stagesOpacity:opacity('.objects-workflow-stages'),
    footerOpacity:opacity('.st-key-objects_actions button'),
    error:document.body.innerText.includes('Estimate is not available to this company.')});
   requestAnimationFrame(sample);
  };sample();
 });
 await fresh.core.getByRole('button',{name:'Fixture rerender',exact:true}).click();
 await fresh.frame.waitForFunction(()=>document.querySelector('.objects-pricing-table')?.innerText.includes('₪1\u202f000'),null,{timeout:16000});
 await fresh.core.getByRole('button',{name:'Fixture rerender',exact:true}).click();
 await fresh.core.getByRole('link',{name:/^(Done|Review)$/i}).waitFor();
 report.fresh=await fresh.frame.evaluate(()=>{window.calculationSample=false;return calculationFrames;});
 assert.ok(report.fresh.every(row=>row.tables<=1&&!row.error));
 assert.ok(report.fresh.every(row=>['headerOpacity','metricsOpacity','stagesOpacity','footerOpacity'].every(key=>row[key]===null||row[key]===1)),JSON.stringify(report.fresh.filter(row=>Object.keys(row).some(key=>key.endsWith('Opacity')&&row[key]!==null&&row[key]<1)).slice(0,4)));
 assert.equal((readFileSync(journal,'utf8').match(/fresh worker started/g)||[]).length,1);
 assert.ok(!readFileSync(journal,'utf8').includes('ERROR ownership read before shell'));
 assert.equal(await fresh.core.locator('[data-testid="stException"]').count(),0);
 await fresh.page.close();
 for(const width of [1280,390]){
  rmSync(statePath('labor-hours.json'),{force:true});
  const {page,core,frame}=await boot({labor_ready:true,overhead_delay:1.5},width);
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  await core.getByRole('button',{name:/^continue to project$/i}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-cost-band="labor"] > summary').click();
  const stages=core.locator('[data-cost-band="labor"] > .object-detail-labor-body > details');
  assert.deepEqual(await stages.evaluateAll(nodes=>nodes.map(n=>n.dataset.costBand)),['part-production','part-coating','assembly-stage','preparation-packing']);
  assert.equal(await core.locator('[data-cost-band="part-coating"] > summary [data-labor-column="total"]').innerText(),'₪0');
  const preparation=core.locator('[data-cost-band="preparation-packing"]');
  assert.equal(await preparation.locator(':scope > summary [data-labor-column="total"]').innerText(),'₪16');
  await preparation.locator(':scope > summary').click();
  const packing=core.locator('[data-cost-band="packing"]');
  assert.equal(await packing.locator(':scope > summary [data-labor-column="hours"]').innerText(),'0.3');
  assert.equal(await packing.locator('[contenteditable="true"]').count(),1);
  const packingOpen=await packing.evaluate(n=>n.open);
  await packing.getByRole('textbox',{name:'Packing hours',exact:true}).click();
  assert.equal(await packing.evaluate(n=>n.open),packingOpen);
  await packing.locator(':scope > summary .object-detail-cost-title').click();
  assert.match(await packing.innerText(),/B01 · M · 1 × 15 min/);
  for(const key of ['part-production','assembly-stage'])await core.locator(`[data-cost-band="${key}"] > summary`).click();
  const openCnc=async()=>{
   const sheet=core.locator('[data-cost-band="sheet-processing"]');
   if(!await sheet.evaluate(n=>n.open))await sheet.locator(':scope > summary .object-detail-cost-title').click();
   const cnc=sheet.locator('[data-labor-detail="cnc"]');
   if(!await cnc.evaluate(n=>n.open))await cnc.locator(':scope > summary').click();
  };
  await openCnc();
  const disclosures=core.locator('[data-cost-band="sheet-processing"] .object-detail-disclosure-summary');
  const elements=core.locator('[data-cost-band="sheet-processing"] .object-detail-elements');
  await elements.locator(':scope > summary').click();
  const group=elements.locator('.object-detail-element-group').first();
  if(await group.count()){
   await group.locator(':scope > summary').focus();await group.locator(':scope > summary').press('Enter');
   assert.equal(await group.evaluate(n=>n.open),true);
  }
  const disclosureGeometry=await disclosures.evaluateAll(nodes=>nodes.filter(n=>n.getClientRects().length).map(n=>{
   const title=n.querySelector('.object-detail-disclosure-title'),style=getComputedStyle(title),box=n.getBoundingClientRect();
   return {text:title.textContent,height:box.height,font:style.font,background:getComputedStyle(n).backgroundColor,
    marker:getComputedStyle(n).listStyleType,chevron:getComputedStyle(title,'::before').borderRightWidth};
  }));
  assert.equal(await core.locator('[data-labor-detail="cnc"] > summary .object-detail-cost-title').innerText(),'CNC');
  assert(disclosureGeometry.some(n=>n.text==='Elements'));
  const reference=await core.locator('.object-detail-overhead-band .object-detail-group-title').first().evaluate(n=>getComputedStyle(n).font);
  for(const row of disclosureGeometry){assert.equal(row.height,42,JSON.stringify(row));assert.equal(row.font,reference);assert.equal(row.marker,'none');assert.equal(row.chevron,'0px');}
  assert.equal(await core.locator('[data-labor-detail="cnc"] > summary .object-detail-cost-title').innerText(),'CNC');
  await elements.locator(':scope > summary').click();
  const assertCncRollup=async()=>{
   const sheet=core.locator('[data-cost-band="sheet-processing"]');
   const cnc=sheet.locator('[data-labor-detail="cnc"]');
   const values=node=>node.locator(':scope > summary .object-detail-cost-value').allTextContents();
   const before=await core.locator('[data-cost-band="labor"]').getAttribute('data-labor-total-hours');
   assert.equal(await cnc.locator(':scope > summary [contenteditable]').count(),0);
   assert(await sheet.evaluate(node=>node.querySelector(':scope > .object-detail-work-body').lastElementChild.matches('.object-detail-cnc-elements')));
   if(await cnc.evaluate(n=>n.open))await cnc.locator(':scope > summary .object-detail-cost-title').click();
   assert.deepEqual(await values(cnc),await values(sheet));
   for(const key of ['hours','pay','taxes','total'])assert(await cnc.locator(`:scope > summary [data-labor-column="${key}"] > span`).isVisible());
   assert.equal(await cnc.locator(':scope > summary .object-detail-cost-title').evaluate(n=>getComputedStyle(n,'::before').content),'"▸"');
   await cnc.locator(':scope > summary .object-detail-cost-title').click();
   for(const key of ['hours','pay','taxes','total'])assert.equal(await cnc.locator(`:scope > summary [data-labor-column="${key}"] > span`).isVisible(),false);
   const hierarchy=await core.locator('[data-cost-band="labor"]').evaluate(root=>{
    const start=node=>node.getBoundingClientRect().x+parseFloat(getComputedStyle(node).paddingLeft);
    return {work:['part-production','sheet-processing','cnc','cnc-operator'].map(key=>start(root.querySelector(`[data-cost-band="${key}"] > summary .object-detail-cost-title`))),
     reference:start(root.querySelector('.object-detail-cnc-elements .object-detail-elements > summary'))};
   });
   assert(hierarchy.work.every((x,i,a)=>i===0||x>a[i-1]),JSON.stringify(hierarchy));
   assert(Math.abs(hierarchy.reference-hierarchy.work[2])<1,JSON.stringify(hierarchy));
   assert.equal(await core.locator('[data-cost-band="labor"]').getAttribute('data-labor-total-hours'),before);
  };
  await assertCncRollup();
  assert.equal(await core.getByRole('textbox',{name:'Sheet Processing hours',exact:true}).count(),0);
  for(const title of ['Labor','Part Production','Assembly','Preparation and Packing'])
   assert.equal(await core.getByRole('textbox',{name:title+' hours',exact:true}).count(),0);
  const cncSheet=core.locator('[data-cost-band="sheet-processing"]');
  assert.ok(!/In-house|Subcontractor|Materials \+ labor/.test(await cncSheet.innerText()));
  assert.match(await core.locator('.object-detail-cost-column-headings').innerText(),/SOCIAL \+25%/);

  const hours=core.getByRole('textbox',{name:'Block Assembly hours',exact:true});
  await hours.waitFor();
  await frame.waitForFunction(()=>window.__costerlyObjectDetailDraft?.context?.objectId==='object-001');
  const assembly=core.locator('[data-cost-band="assembly"]');
  const inputOpen=await assembly.evaluate(node=>node.open);
  await hours.click();
  assert.equal(await assembly.evaluate(node=>node.open),inputOpen);
  const total=assembly.locator(':scope > summary [data-labor-column="total"]');
  const save=core.locator('.object-detail-material-save');
  await hours.fill('40.5');
  assert.equal(await hours.innerText(),'40.5');
  assert.equal((await frame.evaluate(()=>window.__costerlyObjectDetailDraft.pendingEdits()))[0].value,'40.5');
  await hours.press('Tab');
  const overhead=core.locator('[data-overhead-summary][data-overhead-ready="true"]');
  await overhead.waitFor();
  assert.equal(await overhead.locator('[contenteditable="true"]').count(),0);
  assert.equal(await hours.innerText(),'40.5');
  assert.equal(await assembly.evaluate(node=>node.open),inputOpen);
  assert.equal(await total.innerText(),'₪2\u202f531');
  assert.equal(await core.locator('[data-cost-band="assembly-stage"] > summary [data-labor-column="total"]').textContent(),'₪2\u202f531');
  assert.notEqual(await core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪1\u202f000');
  if(width===1280){
   settings({labor_ready:true,hours_write_failure:true});
   await save.click();
   await core.getByRole('button',{name:'Retry save',exact:true}).waitFor();
   assert.equal(await save.getAttribute('data-save-error'),'');
   assert.equal(await hours.innerText(),'40.5');
   settings({labor_ready:true});
  }
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  const sheetHours=core.getByRole('textbox',{name:'Operator hours',exact:true});
  await sheetHours.fill('100.0');await sheetHours.press('Enter');
  assert.equal(await core.locator('[data-cost-band="sheet-processing"] > summary [data-labor-column="total"]').textContent(),'₪6\u202f250');
  assert.equal(await core.locator('[data-cost-band="labor"] > summary [data-labor-column="total"] .object-detail-cost-value').innerText(),'₪8\u202f797');
  assert.equal(await preparation.locator(':scope > summary [data-labor-column="total"]').textContent(),'₪16');
  const laborRoot=core.locator('[data-cost-band="labor"]');
  const assertSharedHours=async(expected)=>{
   assert.equal(await laborRoot.locator(':scope > summary .object-detail-labor-hours-value').innerText(),expected.toFixed(1)+' h');
   assert.ok(Math.abs(Number(await laborRoot.getAttribute('data-labor-total-hours'))-expected)<1e-9);
   assert.ok(Math.abs(Number(await overhead.getAttribute('data-overhead-labor-hours'))-expected)<1e-9);
   await overhead.locator('details').first().evaluate(node=>{node.open=true;});
   await overhead.locator('.object-detail-group').first().evaluate(node=>{node.open=true;});
   const allocation=await overhead.locator('.object-detail-table-row[data-line-id]').first().locator(':scope > div').nth(2).innerText();
   assert.ok(allocation.includes(expected.toFixed(1).replace(/[.]0$/,'')+'h /'),JSON.stringify({expected,allocation}));
   const group=overhead.locator('.object-detail-group').first();
   await group.locator(':scope > summary').click();
   const monthly=await group.locator(':scope > summary [data-overhead-group-column="monthly"]').innerText();
   const monthlySum=await group.locator('.object-detail-table-row[data-line-id]').evaluateAll(rows=>rows.reduce((n,r)=>n+Number(r.dataset.overheadMonthly),0));
   assert.equal(Number(monthly.replace(/[^0-9.-]/g,'')),Math.round(monthlySum));
   assert.equal(await group.locator(':scope > summary [data-overhead-group-column="allocation"]').innerText(),allocation);
   for(const key of ['monthly','allocation','cost'])assert(await group.locator(`:scope > summary [data-overhead-group-column="${key}"]`).isVisible());
   await group.locator(':scope > summary').click();
   for(const key of ['monthly','allocation','cost'])assert.equal(await group.locator(`:scope > summary [data-overhead-group-column="${key}"]`).isVisible(),false);
  };
  await assertSharedHours(140.75);
  await laborRoot.locator(':scope > summary').click();
  assert.equal(await laborRoot.locator(':scope > summary .object-detail-labor-hours-value').isVisible(),true);
  await laborRoot.locator(':scope > summary').click();
  assert.equal(await overhead.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪1\u202f408',
   JSON.stringify(await overhead.evaluate(node=>({host:{...node.dataset},rows:[...node.querySelectorAll('[data-line-id]')].map(row=>({...row.dataset})),context:window.__costerlyObjectDetailDraft?.context}))));
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  assert.equal(JSON.parse(readFileSync(statePath('labor-hours.json'),'utf8')).find(row=>row.raw_agent_json.block==='assembly').raw_agent_json.hours_per_item,'40.5');
  await hours.fill('1.25');await hours.press('Tab');
  assert.equal(await hours.getAttribute('aria-invalid'),'true');
  await hours.fill('0');await hours.press('Tab');
  assert.equal(await total.innerText(),'₪0');
  assert.equal(await core.locator('[data-cost-band="labor"] > summary [data-labor-column="total"] .object-detail-cost-value').innerText(),'₪6\u202f266');
  assert.equal(await overhead.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪1\u202f003');
  assert.equal(await core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪8\u202f268');
  await assertSharedHours(100.25);
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  await core.getByRole('link',{name:'Back to Project',exact:true}).click();
  await core.getByText('₪8\u202f268',{exact:true}).first().waitFor();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-cost-band="labor"] > summary').click();
  for(const key of ['part-production','assembly-stage'])await core.locator(`[data-cost-band="${key}"] > summary`).click();
  await openCnc();
  await hours.waitFor();assert.equal(await hours.innerText(),'0.0');
  assert.equal(await sheetHours.innerText(),'100.0');
  await overhead.waitFor();
  await assertSharedHours(100.25);
  await core.locator('[data-cost-band="preparation-packing"] > summary').click();
  const extraHours={'File Preparation': '1.0','Edge Banding':'2.0','Part Coating':'1.2',
    'Additional Assembly':'0.4','Trial Installation':'0.5','Packing':'0.7'};
  for(const [title,value] of Object.entries(extraHours)){
   const input=core.getByRole('textbox',{name:title+' hours',exact:true});
   await input.fill(value);await input.press('Tab');
  }
  await assertSharedHours(105.8);
  await assertCncRollup();
  assert.equal(await core.locator('[data-cost-band="labor"] > summary [data-labor-column="total"] .object-detail-cost-value').innerText(),'₪6\u202f613');
  assert.equal(await overhead.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪1\u202f058');
  assert.equal(await core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪8\u202f671');
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  await assertSharedHours(105.8);
  await core.getByRole('link',{name:'Back to Project',exact:true}).click();
  await core.getByText('₪8\u202f671',{exact:true}).first().waitFor();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-cost-band="labor"] > summary').click();
  for(const key of ['part-production','assembly-stage','preparation-packing'])await core.locator(`[data-cost-band="${key}"] > summary`).click();
  await openCnc();
  for(const [title,value] of Object.entries(extraHours))
   assert.equal(await core.getByRole('textbox',{name:title+' hours',exact:true}).innerText(),value);
  await overhead.waitFor();await assertSharedHours(105.8);await assertCncRollup();
  await frame.evaluate(()=>{document.querySelector('[data-cost-band="labor"]').scrollLeft=0;});
  await frame.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const workGeometry=await frame.evaluate(()=>{
   const head=document.querySelector('.object-detail-cost-column-headings');
   const cx=n=>{const b=n.getBoundingClientRect();return b.x+b.width/2;};
   const axes=Object.fromEntries(['hours','pay','taxes','total'].map(c=>[c,cx(head.querySelector(`[data-labor-column="${c}"] > span`))]));
   return [...document.querySelectorAll('.object-detail-work-row > summary')].filter(n=>n.getClientRects().length).map(row=>{
    const b=row.getBoundingClientRect();
    return {key:row.parentElement.dataset.costBand,height:b.height,cells:[...row.querySelectorAll('[data-labor-column]')]
     .filter(n=>getComputedStyle(n.firstElementChild).visibility==='visible').map(n=>{
      const value=n.querySelector('[contenteditable],.object-detail-cost-value');const range=document.createRange();range.selectNodeContents(value);const t=range.getBoundingClientRect();
      return {column:n.dataset.laborColumn,x:Math.abs(cx(value)-axes[n.dataset.laborColumn]),y:Math.abs(t.y+t.height/2-(b.y+(b.height-1)/2))};
     })};
   });
  });
  assert.ok(workGeometry.length>=13,JSON.stringify(workGeometry));
  assert.ok(workGeometry.every(row=>Math.abs(row.height-workGeometry[0].height)<1 && row.cells.every(c=>c.x<1&&c.y<2)),JSON.stringify(workGeometry));
  console.log('editable work geometry',width,JSON.stringify(workGeometry));
  const body=await core.locator('body').innerText();
  assert.ok(!/Some work needs review|outside this estimate/.test(body));
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  await page.screenshot({path:reportPath(`labor-edit-${width}.png`),fullPage:true});
  report[width]={savedHours:await hours.innerText(),total:await total.innerText()};
  await page.close();
 }
 for(const name of ['labor-hours.json','full-cost-totals.json','full-cost-lines.json'])rmSync(statePath(name),{force:true});
 const unknown=await boot({labor_ready:true,labor_unknown:true},1280);
 await unknown.core.getByRole('button',{name:'Last Estimate',exact:true}).click();
 await unknown.core.getByRole('button',{name:/^continue to project$/i}).click();
 await unknown.core.getByRole('link',{name:/^(Done|Review)$/i}).click();
 await unknown.core.locator('[data-cost-band="labor"] > summary').click();
 await unknown.core.locator('[data-cost-band="preparation-packing"] > summary').click();
 const manual=unknown.core.getByRole('textbox',{name:'Trial Installation hours',exact:true});
 const unknownRoot=unknown.core.locator('[data-cost-band="labor"]');
 const unknownSave=unknown.core.locator('.object-detail-material-save');
 assert.equal(await manual.getAttribute('data-original-value'),null);
 await manual.click();await manual.press('Tab');
 assert.equal(await manual.getAttribute('aria-invalid'),null);
 assert.equal(await unknownRoot.locator(':scope > summary .object-detail-labor-hours-value').innerText(),'—');
 await manual.fill('0');await manual.press('Tab');
 assert.equal(await unknownRoot.locator(':scope > summary .object-detail-labor-hours-value').innerText(),'0.0 h');
 await manual.fill('');await manual.press('Tab');
 assert.equal(await unknownRoot.locator(':scope > summary .object-detail-labor-hours-value').innerText(),'—');
 assert.equal(await unknownSave.isDisabled(),true);
 await manual.fill('1.0');await manual.press('Tab');await unknownSave.click();
 await unknown.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 const recovered=unknown.core.locator('[data-overhead-summary][data-overhead-ready="true"]');await recovered.waitFor();
 assert.equal(await recovered.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪10');
 assert.equal(await unknown.core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪1\u202f073');
 assert.equal(await manual.innerText(),'1.0');
 assert.equal(await unknown.core.locator('[data-cost-band="assembly-stage"] > summary [data-labor-column="hours"]').textContent(),'—');
 await recovered.locator('.object-detail-overhead-band > summary').click();
 const readyGroup=recovered.locator('.object-detail-group').first();await readyGroup.locator(':scope > summary').click();
 await manual.fill('2.0');await manual.press('Tab');await unknownSave.click();
 await unknown.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 assert.equal(await readyGroup.evaluate(n=>n.open),true,'Healthy Overhead keeps native disclosure state on later saves');
 assert.equal(await recovered.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪20');
 assert.equal(await unknown.core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪1\u202f145');
 await unknown.page.close();
 console.log(JSON.stringify({freshFrames:report.fresh.length,...report[1280],mobile:report[390]}));
 writeFileSync(reportPath('calculation.json'),JSON.stringify(report,null,2));
}finally{
 rmSync(config,{force:true});
 await browser.close();await new Promise(resolve=>server.close(resolve));
}
