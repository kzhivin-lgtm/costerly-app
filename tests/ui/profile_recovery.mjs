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
 const journal=statePath('browser-journal');
 const reads=()=>readFileSync(journal,'utf8').split('\n');
 let ctx=await boot({read_delay:0.25});
 const start=reads().length;
 const before=performance.now();
 await move(ctx,'Profile','account');
 const initialMs=Math.round(performance.now()-before);
 const wanted=['companies','company_members','company_employees','company_machinery','company_suppliers','company_supplier_services'];
 for(let i=0;i<30;i++){
  if(wanted.every(name=>reads().slice(start).includes('read '+name)))break;
  await new Promise(resolve=>setTimeout(resolve,100));
 }
 assert.ok(wanted.every(name=>reads().slice(start).includes('read '+name)), 'All remaining tab data preloads before opening a tab');
 const after=reads().length;
 const times=[];
 for(const name of ['Labor Costs','Machinery','Contacts','Bank Details','Users']){
  const t=performance.now();await tab(ctx,name);times.push({name,ms:Math.round(performance.now()-t)});
 }
 assert.deepEqual(reads().slice(after).filter(line=>wanted.some(name=>line==='read '+name)),[],'Warm tabs use prepared reads');
 results.push({preloaded:wanted,initialMs,warmTabs:times});
 await tab(ctx,'Overhead Expenses');
 for(const [name,key,target] of [['Overhead Expenses','ArrowRight','Labor Costs'],['Labor Costs','End','Users'],['Users','Home','Overhead Expenses']]){
  await ctx.core.getByRole('tab',{name,exact:true}).focus();
  const offset=await ctx.page.evaluate(()=>navMessages.length);
  await ctx.core.getByRole('tab',{name,exact:true}).press(key);
  await ctx.page.waitForFunction(offset=>navMessages.slice(offset).some(event=>event.type==='costerly:app-ready'&&event.id&&event.screen==='account'),offset);
  await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  assert.equal(await ctx.core.getByRole('tab',{name:target,exact:true}).getAttribute('aria-selected'),'true');
 }
 results.push('Keyboard ArrowRight, End, Home');
 writeFileSync(expiry,'expired');
 const offset=await ctx.page.evaluate(()=>navMessages.length);
 await ctx.core.getByRole('tab',{name:'Contacts',exact:true}).click();
 await ctx.core.getByRole('button',{name:'Sign in',exact:true}).waitFor();
 await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 assert.equal(await ctx.core.locator('.company-profile-heading').count(),0);
 await ctx.page.waitForFunction(offset=>navMessages.slice(offset).some(event=>event.type==='costerly:app-ready'&&event.id&&event.screen==='login'),offset);
 results.push('Expired session during Profile tab change reaches Login');
 await ctx.page.close();
 ctx=await boot();
 await move(ctx,'Profile','account');
 await tab(ctx,'Contacts');
 const email=ctx.core.getByRole('textbox',{name:'Official email',exact:true});
 await email.fill('retry@fixture.invalid');
 settings({fail_write:'companies'});
 await ctx.core.getByRole('button',{name:'Save Contacts',exact:true}).click();
 await ctx.core.getByText('Company details were not saved. Try again in a moment.',{exact:true}).waitFor();
 assert.equal(await email.inputValue(),'retry@fixture.invalid');
 assert.notEqual(database().companies[0].public_email,'retry@fixture.invalid');
 assert.equal(await ctx.core.getByText('Contacts saved',{exact:true}).count(),0);
 settings({});
 await ctx.core.getByRole('button',{name:'Save Contacts',exact:true}).click();
 await ctx.core.getByText('Contacts saved',{exact:true}).waitFor();
 await waitDb(data=>data.companies[0].public_email==='retry@fixture.invalid');
 await tab(ctx,'Bank Details');await tab(ctx,'Contacts');
 assert.equal(await email.inputValue(),'retry@fixture.invalid');
 results.push('Failed Save retains edit and error, retry persists, reopened tab shows authoritative value');
 await ctx.page.close();
 ctx=await boot({role:'member',admin:false});
 await move(ctx,'Profile','account');
 await tab(ctx,'Contacts');
 assert.equal(await ctx.core.getByRole('button',{name:'Save Contacts',exact:true}).count(),0);
 await tab(ctx,'Labor Costs');
 assert.equal(await ctx.core.getByRole('button',{name:'Add Worker',exact:true}).count(),0);
 await ctx.page.close();
 results.push('Member receives read-only Contacts and no worker actions');
 writeFileSync(reportPath('profile-recovery.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results,null,2));
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
