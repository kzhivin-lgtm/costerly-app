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
  await core.getByRole('button',{name:/^continue to objects estimation$/i}).click();
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
  await core.getByRole('link',{name:'Back to Objects',exact:true}).click();
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
 await core.getByRole('button',{name:/^continue to objects estimation$/i}).click();
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
  await core.getByRole('button',{name:/^continue to objects estimation$/i}).click();
  report['objectsFooter'+width]=await checkClosingGap(frame,'.st-key-objects_actions');
  // The Objects suite covers the real quantity RPC. This case begins with its
  // persisted quantity, then exercises the production detail editor end to end.
  writeFileSync(statePath('object-quantities.json'),JSON.stringify({'estimate-ui-saved:object-001':3}));
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-overhead-ready="true"]').waitFor();
  const net=core.locator('.object-detail-final [data-final="excl_vat"]');
  assert.equal(await net.innerText(),'₪1\u202f000');
  await page.waitForURL('**/o/**');
  const originalUrl=page.url();
  await core.locator('.object-detail-materials-band > summary').click();
  const picker=core.getByRole('combobox',{name:'Front panels',exact:true});
  await picker.selectOption('mdf');
  const save=core.locator('.object-detail-material-save');
  await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
  const preview=await net.innerText();
  settings({front_panels:true,labor_ready:true,front_save_failure:true});
  await save.click();await core.getByRole('button',{name:'Retry save',exact:true}).waitFor();
  assert.equal(page.url(),originalUrl);assert.equal(await picker.inputValue(),'mdf');
  assert.equal(await net.innerText(),preview);
  assert.equal(await save.getAttribute('data-save-error'),'');
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),false);
  assert.ok(await core.locator('.object-detail-material-edit-status').evaluate(n=>n.getBoundingClientRect().height<=1 && getComputedStyle(n).clipPath==='inset(50%)'));
  assert.equal(existsSync(statePath('front-choice')),false);
  settings({front_panels:true,labor_ready:true});
  const started=Date.now();await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  assert.equal(page.url(),originalUrl);assert.equal(await core.locator('.object-detail-title--name').count(),1);
  assert.equal(await net.innerText(),preview);assert.equal(readFileSync(statePath('front-choice'),'utf8'),'mdf');
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),true);
  await core.locator('.object-detail-materials-band > summary').click();
  await save.scrollIntoViewIfNeeded();
  const gap=await frame.evaluate(()=>{
   const actions=document.querySelector('.object-detail-footer-actions').getBoundingClientRect();
   return innerHeight-46-actions.bottom;
  });
  assert.ok(Math.abs(gap-26)<2,JSON.stringify({width,gap}));
  await page.screenshot({path:reportPath('detail-save-'+width+'.png'),fullPage:true});
  report['detailSave'+width]={seconds:(Date.now()-started)/1000,footerGap:gap,quantity:3,net:preview};
  await core.locator('.object-detail-materials-band > summary').click();
  await picker.selectOption('plywood');
  await frame.waitForFunction(()=>!document.querySelector('.object-detail-material-save')?.disabled);
  assert.equal(await save.evaluate(n=>n.classList.contains('object-detail-material-save--saved')),false);
  await core.getByRole('link',{name:'Back to Objects',exact:true}).click();
  await core.getByRole('button',{name:'Stay',exact:true}).click();
  assert.equal(await picker.inputValue(),'plywood');
  await core.getByRole('link',{name:'Back to Objects',exact:true}).click();
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
  await core.getByRole('button',{name:/^continue to objects estimation$/i}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-cost-band="labor"] > summary').click();
  const hours=core.getByRole('textbox',{name:'Assembly hours',exact:true});
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
  const sheetHours=core.getByRole('textbox',{name:'Sheet Processing hours',exact:true});
  await sheetHours.fill('100.0');await sheetHours.press('Enter');
  assert.equal(await core.locator('[data-cost-band="sheet-processing"] > summary [data-labor-column="total"]').innerText(),'₪6\u202f250');
  assert.equal(await core.locator('[data-cost-band="labor"] > summary [data-labor-column="total"] .object-detail-cost-value').innerText(),'₪8\u202f781');
  assert.equal(await overhead.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪1\u202f405',
   JSON.stringify(await overhead.evaluate(node=>({host:{...node.dataset},rows:[...node.querySelectorAll('[data-line-id]')].map(row=>({...row.dataset})),context:window.__costerlyObjectDetailDraft?.context}))));
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  assert.equal(JSON.parse(readFileSync(statePath('labor-hours.json'),'utf8')).find(row=>row.raw_agent_json.block==='assembly').raw_agent_json.hours_per_item,'40.5');
  await hours.fill('1.25');await hours.press('Tab');
  assert.equal(await hours.getAttribute('aria-invalid'),'true');
  await hours.fill('0');await hours.press('Tab');
  assert.equal(await total.innerText(),'₪0');
  assert.equal(await core.locator('[data-cost-band="labor"] > summary [data-labor-column="total"] .object-detail-cost-value').innerText(),'₪6\u202f250');
  assert.equal(await overhead.locator('[data-metric="cost"] .object-detail-section-value').innerText(),'₪1\u202f000');
  assert.equal(await core.locator('.object-detail-final [data-final="excl_vat"]').innerText(),'₪8\u202f250');
  await save.click();await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
  await core.getByRole('link',{name:'Back to Objects',exact:true}).click();
  await core.getByText('₪8\u202f250',{exact:true}).first().waitFor();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('[data-cost-band="labor"] > summary').click();
  await hours.waitFor();assert.equal(await hours.innerText(),'0.0');
  assert.equal(await sheetHours.innerText(),'100.0');
  const body=await core.locator('body').innerText();
  assert.ok(!/Some work needs review|outside this estimate/.test(body));
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  await page.screenshot({path:reportPath(`labor-edit-${width}.png`),fullPage:true});
  report[width]={savedHours:await hours.innerText(),total:await total.innerText()};
  await page.close();
 }
 console.log(JSON.stringify({freshFrames:report.fresh.length,...report[1280],mobile:report[390]}));
 writeFileSync(reportPath('calculation.json'),JSON.stringify(report,null,2));
}finally{
 rmSync(config,{force:true});
 await browser.close();await new Promise(resolve=>server.close(resolve));
}
