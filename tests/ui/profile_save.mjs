import { statePath, reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,rmSync } from 'node:fs';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
import { profileReadyRegressions } from './profile_ready_regression.mjs';
const config=statePath('scenario.json'), expiry=statePath('auth-expired');
const settings=value=>writeFileSync(config,JSON.stringify(value));
const server=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 const html=readFileSync('cloudflare/index.html','utf8').replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(html);
});
await new Promise(resolve=>server.listen(8796,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions);
const results=[];
const closingGaps=[];
async function checkSaveCard(button){
 const geometry=await button.evaluate(node=>{
  const card=node.closest('.st-key-company_metrics_card,.st-key-company_pricing_card,.st-key-company_labor_card,[data-testid="stForm"]');
  const s=getComputedStyle(card);
  return {label:node.textContent,gap:card.getBoundingClientRect().bottom-node.getBoundingClientRect().bottom,
   expected:parseFloat(s.paddingBottom)+parseFloat(s.borderBottomWidth)};
 });
 assert.ok(Math.abs(geometry.gap-geometry.expected)<2,JSON.stringify(geometry));
 closingGaps.push(geometry);
}
const buttonStyle=button=>button.evaluate(node=>{
 const text=node.querySelector('p')||node,s=getComputedStyle(text),b=getComputedStyle(node);
 return {height:node.getBoundingClientRect().height,font:s.fontFamily,size:s.fontSize,weight:s.fontWeight,case:s.textTransform,radius:b.borderRadius,color:b.backgroundColor};
});
async function boot(value={},route='',readyObserver=null){
 rmSync(expiry,{force:true});settings(value);
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 page.setDefaultTimeout(10000);
 if(readyObserver)await page.addInitScript(readyObserver);
 await page.addInitScript(()=>{
  if(window!==top)return;
  window.navMessages=[];
  addEventListener('message',event=>{
   if(['costerly:app-ready','costerly:transition-click','costerly:transition-failed'].includes(event.data?.type))
    navMessages.push({type:event.data.type,id:event.data.transitionId,screen:event.data.screen,
      covered:event.data.workflowNavigation,transition:event.data.transition,
      runId:event.data.runId,sentAt:event.data.sentAt,receivedAt:Date.now()});
  });
 });
 await page.goto('http://127.0.0.1:8796/'+route);
 const core=page.frameLocator('#costerly-app-frame');
 await page.locator('iframe.is-ready').waitFor();
 const frame=await (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
 await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
 return {page,core,frame};
}
async function move(ctx,label,target){
 const offset=await ctx.page.evaluate(()=>navMessages.length);
 await ctx.core.getByRole('button',{name:label,exact:true}).click();
 await ctx.page.waitForFunction(({offset,target})=>navMessages.slice(offset).some(
  event=>event.type==='costerly:app-ready'&&event.id&&event.screen===target),{offset,target});
 await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await ctx.core.locator('[data-testid="stException"]').count(),0);
}
const db=statePath('profile-db.json');
const database=()=>JSON.parse(readFileSync(db,'utf8'));
const tab=async(ctx,name)=>{
 const offset=await ctx.page.evaluate(()=>navMessages.length);
 const old=await ctx.core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
 await ctx.core.getByRole('tab',{name,exact:true}).click();
 await ctx.page.waitForFunction(offset=>navMessages.slice(offset).some(
  event=>event.type==='costerly:app-ready'&&event.id&&event.screen==='account'),offset);
 await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const id=await ctx.core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
 assert.notEqual(id,old);
};
async function waitDb(predicate){
 for(let attempt=0;attempt<40;attempt++){
  if(predicate(database()))return;
  await new Promise(resolve=>setTimeout(resolve,100));
 }
 assert.ok(predicate(database()),'Expected a persisted fixture update');
}
try{
 const ctx=await boot();
 await move(ctx,'Profile','account');
 await checkSaveCard(ctx.core.locator('[data-company-settings-save="metrics"]'));
 const rent=ctx.core.locator('.company-metrics-monthly-input[data-field="rent_facilities_cost"]');
 const rentField=await rent.getAttribute('data-field');
 await rent.fill('321');
 await rent.press('Tab');
 await ctx.core.locator('[data-company-settings-save="metrics"]').click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.overhead_monthly[0][rentField]===321);
 await tab(ctx,'Pricing Cost');
 await checkSaveCard(ctx.core.locator('[data-company-settings-save="pricing"]'));
 const reserve=ctx.core.locator('.company-pricing-input[data-field="warranty_reserve_percent"]');
 const pricingButtonStyle=await buttonStyle(ctx.core.locator('[data-company-settings-save="pricing"]'));
 await reserve.fill('7');
 await reserve.press('Tab');
 const advance=ctx.core.locator('.company-pricing-input[data-field="advance_payment_percent"]');
 assert.equal(await advance.innerText(),'');
 await advance.fill('70');await advance.press('Tab');
 await ctx.core.locator('[data-company-settings-save="pricing"]').click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.overhead_settings[0].warranty_reserve_percent===7);
 await waitDb(data=>data.overhead_settings[0].advance_payment_percent===70);
 await tab(ctx,'Overhead Expenses');
 assert.match(await ctx.core.locator('.company-metrics-monthly-input[data-field="rent_facilities_cost"]').innerText(),/321/);
 await tab(ctx,'Contacts');
 await checkSaveCard(ctx.core.getByRole('button',{name:'Save Contacts',exact:true}));
 const email=ctx.core.getByRole('textbox',{name:'Official email',exact:true});
 await email.fill('saved@fixture.invalid');
 assert.deepEqual(await buttonStyle(ctx.core.getByRole('button',{name:'Save Contacts',exact:true})),pricingButtonStyle,'Pricing uses Contacts button geometry and typography');
 await ctx.core.getByRole('button',{name:'Save Contacts',exact:true}).click();
 
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.companies[0].public_email==='saved@fixture.invalid');
 await tab(ctx,'Bank Details');
 await checkSaveCard(ctx.core.getByRole('button',{name:'Save Bank Details',exact:true}));
 await ctx.core.getByRole('textbox',{name:/^Company registration number/}).fill('123456789');
 await ctx.core.getByRole('textbox',{name:/^Account number$/i}).fill('003123');
 await ctx.core.getByRole('button',{name:'Save Bank Details',exact:true}).click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.companies[0].account_number==='003123');
 await tab(ctx,'Contacts');
 assert.equal(await email.inputValue(),'saved@fixture.invalid');
 await tab(ctx,'Bank Details');
 assert.equal(await ctx.core.getByRole('textbox',{name:/^Account number$/i}).inputValue(),'003123');
 await tab(ctx,'Machinery');
 await ctx.core.getByRole('radio',{name:'Yes',exact:true}).first().check();
 await ctx.core.getByRole('textbox',{name:/^Working length/}).fill('2.8');
 await ctx.core.getByRole('textbox',{name:/^Working width/}).fill('2.07');
 await ctx.core.getByRole('textbox',{name:/^Working width/}).press('Tab');
 assert.deepEqual(await buttonStyle(ctx.core.getByRole('button',{name:'Save',exact:true})),pricingButtonStyle,'Machinery uses Contacts button geometry and typography');
 await ctx.core.getByRole('button',{name:'Save',exact:true}).click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.company_machinery.some(row=>row.machine_code==='wood_cnc_router'&&row.availability_status==='in_house'));
 await tab(ctx,'Pricing Cost');
 assert.match(await reserve.innerText(),/7/);
 assert.equal(await advance.innerText(),'70%');
 await advance.fill('0');await advance.press('Tab');
 await ctx.core.locator('[data-company-settings-save="pricing"]').click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.overhead_settings[0].advance_payment_percent===0);
 await advance.focus();assert.equal(await advance.innerText(),'','Explicit zero clears only visually on focus');await advance.press('Tab');
 assert.equal(await advance.innerText(),'0%','Focusing explicit zero must not turn the optional value into blank');
 await advance.fill('');await advance.press('Tab');
 await ctx.core.locator('[data-company-settings-save="pricing"]').click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.overhead_settings[0].advance_payment_percent===null);
 await tab(ctx,'Contacts');await tab(ctx,'Pricing Cost');
 assert.equal(await advance.innerText(),'','Cleared optional advance remains blank after reopening');
 await tab(ctx,'Machinery');
 assert.ok(await ctx.core.getByRole('radio',{name:'Yes',exact:true}).first().isChecked());
 await tab(ctx,'Labor Costs');
 await ctx.core.getByRole('textbox',{name:'Worker name',exact:true}).fill('Profile preload worker');
 const rendered=async(action)=>{
  const id=await ctx.core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
  await action();
  await ctx.core.locator('[data-costerly-screen="account"]:not([data-costerly-render-id="'+id+'"])').waitFor({state:'attached'});
 };
 const select=async(label,option)=>rendered(async()=>{
  await ctx.core.getByRole('combobox',{name:label,exact:true}).click();
  await ctx.core.getByRole('option',{name:option,exact:true}).click();
 });
 await select('Department','Production');
 await select('Position','Carpenter');
 await select('Pay type','Hourly Rate');
 await ctx.core.getByRole('textbox',{name:'Hourly Rate',exact:true}).fill('55');
 await rendered(()=>ctx.core.getByRole('textbox',{name:'Hourly Rate',exact:true}).press('Tab'));
 
 await ctx.core.getByRole('textbox',{name:'Average Hours per Month',exact:true}).fill('186');
 await rendered(()=>ctx.core.getByRole('textbox',{name:'Average Hours per Month',exact:true}).press('Tab'));
 
 await ctx.core.getByRole('textbox',{name:'Total Monthly Cost',exact:true}).waitFor();
 await ctx.core.getByRole('button',{name:'Add Worker',exact:true}).click();
 await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.company_employees.some(row=>row.worker_name==='Profile preload worker'));
 await tab(ctx,'Pricing Cost');
 await tab(ctx,'Labor Costs');
 await ctx.core.getByText('Profile preload worker',{exact:true}).waitFor();
 await ctx.core.getByRole('textbox',{name:'Worker name',exact:true}).fill('Management payroll worker');
 await select('Department','Management');await select('Position','General Manager');await select('Pay type','Monthly Salary');
 await ctx.core.getByRole('textbox',{name:'Monthly Salary',exact:true}).fill('10000');
 await rendered(()=>ctx.core.getByRole('textbox',{name:'Monthly Salary',exact:true}).press('Tab'));
 await ctx.core.getByRole('button',{name:'Add Worker',exact:true}).click();await ctx.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.company_employees.some(row=>row.worker_name==='Management payroll worker'));
 const monthlyEmployer=JSON.parse(readFileSync(statePath('profile-db.json'),'utf8')).company_employees.find(row=>row.worker_name==='Management payroll worker').total_monthly_cost;
 await tab(ctx,'Overhead Expenses');
 const management=ctx.core.locator('[data-metric-field="management_administration_cost"]');
 assert.equal(await management.locator('[contenteditable="true"]').count(),0);
 assert.equal((await management.locator('.company-metrics-monthly-input').innerText()).replace(/[^0-9]/g,''),String(monthlyEmployer));
 assert.equal(await management.locator('[data-company-metrics-vat]').innerText(),'—');
 assert.equal(await ctx.core.locator('.company-metrics-group-summary').first().innerText(),'MANAGEMENT & ADMINISTRATION');
 await tab(ctx,'Users');
 const remove=ctx.core.locator('.company-user-delete').first();
 await remove.click();
 await ctx.core.getByRole('button',{name:'Remove Access',exact:true}).click();
 await ctx.core.locator('[data-profile-save-ack][data-profile-save-action="users_remove"]').waitFor({state:'attached'});
 await waitDb(data=>data.company_members.length===1);
 await tab(ctx,'Contacts');
 await tab(ctx,'Users');
 assert.equal(await ctx.core.locator('.company-user-delete').count(),0);
 await move(ctx,'New Estimate','upload');
 await move(ctx,'Profile','account');
 assert.match(await ctx.core.locator('.company-metrics-monthly-input[data-field="rent_facilities_cost"]').innerText(),/321/);
 assert.equal(await ctx.core.locator('[data-testid="stException"]').count(),0);
 results.push('Overhead, Pricing, Contacts, Bank Details, Machinery, worker addition and user removal persisted through tab changes and Profile reopen');
 writeFileSync(reportPath('profile-save.json'),JSON.stringify(results,null,2));
 writeFileSync(reportPath('profile-save-closing-gaps.json'),JSON.stringify(closingGaps,null,2));
 console.log(results);
 await ctx.page.close();
 for(const width of [1280,390]) {
  const stored=await boot({profile_logo_present:true,read_delay:0.03});
  await stored.page.setViewportSize({width,height:933});
  await move(stored,'Profile','account');
  const times=[];
  for(const name of ['Contacts','Pricing Cost','Contacts','Bank Details','Contacts']) {
   const at=performance.now();await tab(stored,name);times.push({name,ms:Math.round(performance.now()-at)});
   assert.equal(await stored.core.locator('[data-testid="stException"]').count(),0);
  }
  await stored.core.locator('.company-logo-preview img').waitFor();
  const chooser=stored.page.waitForEvent('filechooser');
  await stored.core.getByRole('button',{name:'Change Logo',exact:true}).click();await chooser;
  await stored.page.screenshot({path:reportPath('contacts-stored-logo-'+width+'.png')});
  results.push({storedLogo:true,width,times,exceptions:0,picker:'opened'});
  await stored.page.reload();
  // Reload has the same startup preconditions as boot(): wait for the host's
  // ready reveal and Core protocol before interacting with the restored tabs.
  await stored.page.locator('iframe.is-ready').waitFor();
  const restoredFrame=await(await stored.page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  await restoredFrame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  await stored.core.getByRole('tab',{name:'Contacts',exact:true}).click();
  await stored.core.locator('.company-logo-preview img').waitFor();
  await stored.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  assert.equal(await stored.core.locator('[data-testid="stException"]').count(),0);
  await stored.page.close();
 }
 const feedback=await boot({write_delay:0.5,read_delay:0.03});
 await move(feedback,'Profile','account');await tab(feedback,'Pricing Cost');
 assert.equal(await feedback.core.locator('.st-key-company_profile_feedback_bridge').evaluate(n=>getComputedStyle(n.closest('[data-testid="stLayoutWrapper"]')||n).display),'none','Feedback bridge must not insert a visible layout slot');
 const delivery=feedback.core.locator('.company-pricing-input[data-field="delivery_percent"]');
 await delivery.fill('9');await delivery.press('Tab');
 const feedbackSave=feedback.core.locator('[data-company-settings-save="pricing"]');
 await feedbackSave.click();
 await feedback.core.getByRole('button',{name:'Saving…',exact:true}).waitFor();
 assert.equal(await feedbackSave.getAttribute('data-profile-save-saved'),null);
 await feedback.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await waitDb(data=>data.overhead_settings[0].delivery_percent===9);
 assert.equal(await feedback.core.locator('[data-testid="stAlertContentSuccess"]').count(),0);
 const feedbackRender=await feedback.core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
 await feedback.core.getByRole('button',{name:'SAVE PRICING COST',exact:true}).waitFor({timeout:3500});
 assert.equal(await feedback.core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id'),feedbackRender,'Saved reset must not rerun Profile');
 await delivery.fill('10');await delivery.press('Tab');await feedbackSave.click();
 await feedback.core.getByRole('button',{name:'Saved',exact:true}).waitFor();
 await delivery.fill('11');
 assert.equal(await feedbackSave.getAttribute('data-profile-save-saved'),null,'A new edit immediately resets Saved');
 assert.equal(await feedbackSave.isEnabled(),true);
 await feedback.page.screenshot({path:reportPath('profile-save-feedback.png')});
 results.push({feedback:'pending/acknowledged/reset/new-edit',writes:'existing settings path only'});
 await feedback.page.close();
 const readyCases=await profileReadyRegressions({boot,move,tab,waitDb,database});
 writeFileSync(reportPath('profile-ready-regressions.json'),JSON.stringify(readyCases,null,2));
 console.log('Profile ready regressions',JSON.stringify(readyCases));

}catch(error){
 for (const context of browser.contexts()) for (const page of context.pages()) {
  await page.screenshot({path:reportPath('profile_save-failure.png')}).catch(()=>{});
 }
 console.log('Passed before failure',JSON.stringify(results));
 for(const page of browser.contexts().flatMap(context=>context.pages())){
  console.log('messages',JSON.stringify(await page.evaluate(()=>navMessages.slice(-5)).catch(()=>[])));
  for(const frame of page.frames().filter(frame=>frame.url().startsWith('http://127.0.0.1:8789')))
  {
   const ready=await frame.evaluate(()=>window.profileReadyCase?{
    mode:profileReadyCase.mode,heldRun:profileReadyCase.held?.runId,
    events:profileReadyCase.events,failure:profileReadyCase.failure,
    markers:[...document.querySelectorAll('[data-costerly-render-id]')].map(e=>({id:e.dataset.costerlyRenderId,stale:!!e.closest('[data-stale="true"]')})),
    busy:window.__costerlyWorkflowTransition?.busy(),
   }:null).catch(()=>null);
   if(ready)writeFileSync(reportPath('profile-ready-failure.json'),JSON.stringify(ready,null,2));
   console.log('body',(await frame.locator('body').innerText().catch(()=>'' )).slice(-1500));
  }
 }
 throw error;
}finally{
 rmSync(config,{force:true});rmSync(expiry,{force:true});
 await browser.close();await new Promise(resolve=>server.close(resolve));
}
