import { statePath, reportPath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, rmSync} from 'node:fs';
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
async function boot(value={},width=1280){
 settings(value);
 const page=await browser.newPage({viewport:{width,height:1000}});
 page.on('pageerror',error=>console.error('browser error',error.message));
 page.setDefaultTimeout(12000);
 await page.goto('http://127.0.0.1:8796/');
 const core=page.frameLocator('#costerly-app-frame');
 await page.locator('iframe.is-ready').waitFor();
 const frame=await (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 return {page,core,frame};
}
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
  const save=core.getByRole('button',{name:'Save changes',exact:true});
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
   await core.getByText('Could not save changes. Your edits are still here.',{exact:true}).waitFor();
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
