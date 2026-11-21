import { statePath, reportPath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {chromium} from 'playwright';
const config=statePath('scenario.json'),prices=statePath('objects-prices.json');
for(const file of ['object-approvals.json','objects-prices.json','generated-proposal.json','generation-failure'])rmSync(statePath(file),{force:true});
writeFileSync(config,JSON.stringify({objects_v2:true}));

const server=createServer(async(req,res)=>{
 if(req.url.startsWith('/rest/v1/')){
  const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,apikey,content-type,prefer','Access-Control-Allow-Methods':'POST,OPTIONS'};
  if(req.method==='OPTIONS')return res.writeHead(204,headers).end();
  let body='';for await(const chunk of req)body+=chunk;
  const row=JSON.parse(body),saved=existsSync(prices)?JSON.parse(readFileSync(prices)):[];
  const filtered=saved.filter(old=>old.object_key!==row.object_key);filtered.push(row);writeFileSync(prices,JSON.stringify(filtered));
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
 const set=()=>core.getByRole('button',{name:'Set prices',exact:true});
 const generate=()=>core.getByRole('button',{name:'GENERATE PROPOSAL',exact:true});
 assert(await set().isDisabled());assert(await generate().isDisabled());
 assert.equal(await core.getByRole('button',{name:'Parts Check',exact:true}).count(),0);
 report.geometry=await frame.evaluate(()=>{
  const box=node=>{const b=node.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height};};
  const controls=document.querySelector('[class*="st-key-costerly_header_controls"]');
  const metrics=document.querySelector('.objects-cycle-metrics');
  const title=document.querySelector('h1.workflow-title');
  const buttons=[...document.querySelectorAll('.st-key-objects_actions button')];
  return{title:box(title),controls:box(controls),metrics:box(metrics),buttons:buttons.map(box),projectInput:box(document.querySelector('.objects-pricing-project-cost-cell .objects-pricing-price-input')),qty:box(document.querySelector('.objects-pricing-quantity-input')),
   stages:box(document.querySelector('.objects-workflow-stages')),tableHead:box(document.querySelector('.objects-pricing-header')),
   summary:box(document.querySelector('.objects-pricing-summary')),summaryTitle:box(document.querySelector('.objects-pricing-summary-title')),
   summaryValues:[...document.querySelectorAll('[data-summary-field]')].map(box),stageColors:[...document.querySelectorAll('.objects-workflow-stages strong')].map(node=>getComputedStyle(node).color)};
 });
 await page.screenshot({path:reportPath('objects-v2-initial.png'),fullPage:true});
 assert(report.geometry.controls.y>report.geometry.title.y);
 assert(Math.abs(report.geometry.metrics.x-report.geometry.controls.x-report.geometry.controls.width-24)<2,JSON.stringify(report.geometry));
 assert(Math.abs(report.geometry.metrics.y+report.geometry.metrics.height/2-report.geometry.controls.y-report.geometry.controls.height/2)<2,JSON.stringify(report.geometry));
 assert.equal(report.geometry.buttons.length,3);assert(Math.max(...report.geometry.buttons.map(b=>b.width))-Math.min(...report.geometry.buttons.map(b=>b.width))<2);
 assert.equal(report.geometry.projectInput.width,162);assert(Math.abs(report.geometry.projectInput.x-report.geometry.qty.x)<4);
 const geometry=report.geometry;
 assert.equal(geometry.stages.y-geometry.controls.y-geometry.controls.height,50);
 assert.equal(geometry.tableHead.y-geometry.stages.y-geometry.stages.height,50);
 const topSpace=geometry.summaryTitle.y-geometry.summary.y;
 const bottomSpace=geometry.buttons[0].y-Math.max(...geometry.summaryValues.map(box=>box.y+box.height));
 assert(Math.abs(topSpace-bottomSpace)<=4,JSON.stringify({topSpace,bottomSpace}));
 assert(geometry.stageColors.every(color=>color===geometry.stageColors[0]),JSON.stringify(geometry.stageColors));
 assert(!/subtotal/i.test(await core.locator('body').innerText()));
 assert(!(await core.locator('[title]').evaluateAll(nodes=>nodes.map(node=>node.title).join(' '))).match(/subtotal/i));
 await page.screenshot({path:reportPath('objects-v2-initial.png'),fullPage:true});
 await move(core.getByRole('link',{name:/^review$/i}),'object_detail');
 await core.locator('.object-detail-title').first().waitFor();
 await move(core.locator('.object-detail-footer-button--primary'),'objects');
 await core.locator('.objects-pricing-table').waitFor();await set().waitFor();assert(await set().isEnabled());
 await frame.waitForFunction(()=>window.__costerlyObjectsActionsCleanup&&window.__costerlyObjectsPriceInputGuardCleanup);
 const input=core.locator('.objects-pricing-row[data-object-key="object-001"] .objects-pricing-price-input');
 async function editPrice(value){
  await input.fill(String(value));await input.press('Tab');
  const deadline=Date.now()+5000;
  while(!existsSync(prices)||JSON.parse(readFileSync(prices)).find(row=>row.object_key==='object-001')?.value!==value){
   if(Date.now()>deadline)throw new Error('Original price persistence did not complete');
   await new Promise(resolve=>setTimeout(resolve,20));
  }
 }
 await editPrice(1750);await set().click();
 await frame.waitForFunction(()=>{const button=document.querySelector('[class*="st-key-objects_generate_proposal_"] button');return button&&!button.disabled;});
 assert.equal(await core.locator('.objects-workflow-stages [data-stage="2"]').getAttribute('data-state'),'complete');
 await editPrice(1850);assert(await generate().isDisabled());
 await set().click();
 await frame.waitForFunction(()=>{const button=document.querySelector('[class*="st-key-objects_generate_proposal_"] button');return button&&!button.disabled;});
 writeFileSync(statePath('generation-failure'),'fail');await generate().click();await core.getByText('Controlled proposal failure',{exact:true}).waitFor();assert(await generate().isEnabled());
 rmSync(statePath('generation-failure'));await generate().click();
 await frame.waitForFunction(()=>document.querySelector('.objects-workflow-stages [data-stage="3"]')?.dataset.state==='complete');
 assert(await generate().isDisabled());
 const proposal=JSON.parse(readFileSync(statePath('generated-proposal.json')));assert.equal(proposal.rows[0].sale_price_unit,1850);
 assert.equal((readFileSync(statePath('browser-journal'),'utf8').match(/proposal generated/g)||[]).length,1);
 assert.deepEqual(errors,[]);report.errors=errors;
 await page.screenshot({path:reportPath('objects-v2-generated.png'),fullPage:true});
 writeFileSync(reportPath('objects-v2.json'),JSON.stringify(report,null,2));
 console.log('Objects V2.1 passed: 50px stage gaps, readable stages, balanced totals/footer, retired copy, original approval/persistence/proposal flow and input allocation axis.');
}catch(error){
 for(const page of browser.contexts().flatMap(context=>context.pages())){
  await page.screenshot({path:reportPath('objects-v2-latest-failure.png'),fullPage:true});
  const handle=await page.locator('#costerly-app-frame').elementHandle();const frame=handle&&await handle.contentFrame();
  if(frame)writeFileSync(reportPath('objects-v2-latest-failure.json'),JSON.stringify(await frame.evaluate(()=>({text:document.body.innerText,receipt:document.getElementById('objects-actions-error')?.outerHTML,pending:[...(window.__costerlyObjectsPricingWrites?.latest||new Map())].map(([key,entry])=>({key,ok:entry.ok})),buttons:[...document.querySelectorAll('.st-key-objects_actions button')].map(button=>({text:button.innerText,disabled:button.disabled,busy:button.getAttribute('aria-busy'),phase:button.dataset.objectsPhase}))})),null,2));
 }
 throw error;
}finally{await browser.close();server.close();}
