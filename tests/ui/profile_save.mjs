import { statePath, reportPath, fixturePath, chromeOptions } from './support.mjs';
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,rmSync } from 'node:fs';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
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
async function boot(value={},route=''){
 rmSync(expiry,{force:true});settings(value);
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 page.setDefaultTimeout(10000);
 await page.addInitScript(()=>{
  if(window!==top)return;
  window.navMessages=[];
  addEventListener('message',event=>{
   if(['costerly:app-ready','costerly:transition-click','costerly:transition-failed'].includes(event.data?.type))
    navMessages.push({type:event.data.type,id:event.data.transitionId,screen:event.data.screen,
      covered:event.data.workflowNavigation,transition:event.data.transition});
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
 const rent=ctx.core.locator('.company-metrics-monthly-input').first();
 const rentField=await rent.getAttribute('data-field');
 await rent.fill('321');
 await rent.press('Tab');
 await ctx.core.locator('[data-company-settings-save="metrics"]').click();
 await ctx.core.getByText('Overhead expenses saved',{exact:true}).waitFor();
 await waitDb(data=>data.overhead_monthly[0][rentField]===321);
 await tab(ctx,'Pricing Cost');
 const reserve=ctx.core.locator('.company-pricing-input[data-field="warranty_reserve_percent"]');
 await reserve.fill('7');
 await reserve.press('Tab');
 await ctx.core.locator('[data-company-settings-save="pricing"]').click();
 await ctx.core.getByText('Pricing Cost saved',{exact:true}).waitFor();
 await waitDb(data=>data.overhead_settings[0].warranty_reserve_percent===7);
 await tab(ctx,'Overhead Expenses');
 assert.match(await ctx.core.locator('.company-metrics-monthly-input').first().innerText(),/321/);
 await tab(ctx,'Contacts');
 const email=ctx.core.getByRole('textbox',{name:'Official email',exact:true});
 await email.fill('saved@fixture.invalid');
 await ctx.core.getByRole('button',{name:'Save Contacts',exact:true}).click();
 
 await ctx.core.getByText('Contacts saved',{exact:true}).waitFor();
 await waitDb(data=>data.companies[0].public_email==='saved@fixture.invalid');
 await tab(ctx,'Bank Details');
 await ctx.core.getByRole('textbox',{name:/^Company registration number/}).fill('123456789');
 await ctx.core.getByRole('textbox',{name:/^Account number$/i}).fill('003123');
 await ctx.core.getByRole('button',{name:'Save Bank Details',exact:true}).click();
 await ctx.core.getByText('Bank details saved',{exact:true}).waitFor();
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
 await ctx.core.getByRole('button',{name:'Save',exact:true}).click();
 await ctx.core.getByText('Machinery saved',{exact:true}).waitFor();
 await waitDb(data=>data.company_machinery.some(row=>row.machine_code==='wood_cnc_router'&&row.availability_status==='in_house'));
 await tab(ctx,'Pricing Cost');
 assert.match(await reserve.innerText(),/7/);
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
 await ctx.core.getByText('Worker added',{exact:true}).waitFor();
 await waitDb(data=>data.company_employees.some(row=>row.worker_name==='Profile preload worker'));
 await tab(ctx,'Pricing Cost');
 await tab(ctx,'Labor Costs');
 await ctx.core.getByText('Profile preload worker',{exact:true}).waitFor();
 await tab(ctx,'Users');
 const remove=ctx.core.locator('.company-user-delete').first();
 await remove.click();
 await ctx.core.getByRole('button',{name:'Remove Access',exact:true}).click();
 await ctx.core.getByText('User access removed',{exact:true}).waitFor();
 await waitDb(data=>data.company_members.length===1);
 await tab(ctx,'Contacts');
 await tab(ctx,'Users');
 assert.equal(await ctx.core.locator('.company-user-delete').count(),0);
 await move(ctx,'New Estimate','upload');
 await move(ctx,'Profile','account');
 assert.match(await ctx.core.locator('.company-metrics-monthly-input').first().innerText(),/321/);
 assert.equal(await ctx.core.locator('[data-testid="stException"]').count(),0);
 results.push('Overhead, Pricing, Contacts, Bank Details, Machinery, worker addition and user removal persisted through tab changes and Profile reopen');
 writeFileSync(reportPath('profile-save.json'),JSON.stringify(results,null,2));
 console.log(results);
 await ctx.page.close();

}catch(error){
 console.log('Passed before failure',JSON.stringify(results));
 for(const page of browser.contexts().flatMap(context=>context.pages())){
  console.log('messages',JSON.stringify(await page.evaluate(()=>navMessages.slice(-5)).catch(()=>[])));
  for(const frame of page.frames().filter(frame=>frame.url().startsWith('http://127.0.0.1:8789')))
   console.log('body',(await frame.locator('body').innerText().catch(()=>'' )).slice(-1500));
 }
 throw error;
}finally{
 rmSync(config,{force:true});rmSync(expiry,{force:true});
 await browser.close();await new Promise(resolve=>server.close(resolve));
}
