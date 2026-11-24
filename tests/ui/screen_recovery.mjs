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
try{
 for(const width of [1280,390]){
  const ctx=await boot();await ctx.page.setViewportSize({width,height:900});
  await ctx.page.evaluate(()=>sessionStorage.setItem('offline-auth-canary','retained'));
  let reloads=0;ctx.page.on('framenavigated',frame=>{if(frame===ctx.page.mainFrame())reloads++;});
  await ctx.page.context().setOffline(true);
  const cover=ctx.page.locator('#app-loading-mask.is-offline');await cover.waitFor({state:'visible'});
  assert.equal(await cover.innerText(),'Something went wrong.\nAre you connected to the internet?');
  assert.equal(await cover.locator('img').count(),1);
  assert.equal(await ctx.page.locator('#costerly-app-frame').evaluate(n=>n.inert),true);
  assert(await ctx.page.locator('.embed-footer-mask a').isVisible());
  const layout=await cover.evaluate(n=>{
   const heading=n.querySelector('.connection-heading').getBoundingClientRect();
   return {center:heading.x+heading.width/2,target:innerWidth/2,font:getComputedStyle(n.querySelector('.connection-message')).fontSize};
  });
  assert(Math.abs(layout.center-layout.target)<1,JSON.stringify(layout));
  assert.equal(layout.font,width===1280?'24px':'23.4px');
  assert.equal(reloads,0,'Going offline must not reload the app');
  await ctx.page.screenshot({path:reportPath(`connection-error-${width}.png`)});
  await ctx.page.context().setOffline(false);
  await ctx.page.locator('#app-loading-mask.is-offline').waitFor({state:'detached'});
  await ctx.page.locator('iframe.is-ready').waitFor();
  assert.equal(await ctx.page.evaluate(()=>sessionStorage.getItem('offline-auth-canary')),'retained');
  assert.equal(reloads,1,'Reuse the existing single reconnect navigation');
  await ctx.core.getByRole('button',{name:'Last Estimate',exact:true}).waitFor();
  results.push(`Approved offline artwork and existing reconnect/auth retention at${width}`);
  await ctx.page.close();
 }
 for(const screen of ['projects','account','admin']){
  const label={projects:'All Projects',account:'Profile',admin:'Admin'}[screen];
  let ctx=await boot();
  settings({fail:screen});
  await move(ctx,label,screen);
  await ctx.core.locator('[data-testid="stAlertContentError"]').waitFor();
  settings({});
  await move(ctx,'New Estimate','upload');
  results.push('Handled read failure and return from '+screen);
  await ctx.page.close();
  ctx=await boot();
  await move(ctx,label,screen);
  writeFileSync(expiry,'expired');
  await move(ctx,'New Estimate','login');
  await ctx.core.getByRole('button',{name:'Sign in',exact:true}).waitFor();
  results.push('Expired auth from '+screen+' reached Login');
  await ctx.page.close();
  ctx=await boot();
  await move(ctx,label,screen);
  const offset=await ctx.page.evaluate(()=>navMessages.length);
  await ctx.core.locator('.st-key-company_sign_out button').click();
  await ctx.page.waitForFunction(offset=>navMessages.slice(offset).some(
   event=>event.type==='costerly:app-ready'&&event.id&&event.screen==='login'),offset);
  await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  results.push('Sign out from '+screen+' reached Login');
  await ctx.page.close();
 }
 let ctx=await boot({empty_projects:true});
 await move(ctx,'All Projects','projects');
 await ctx.core.locator('.projects-empty').waitFor();
 await move(ctx,'Profile','account');
 results.push('Empty Projects remains navigable');
 await ctx.page.close();
 ctx=await boot({admin:false,role:'member'});
 assert.equal(await ctx.core.getByRole('button',{name:'Admin',exact:true}).count(),0);
 await move(ctx,'Profile','account');
 assert.equal(await ctx.core.getByRole('button',{name:'Admin',exact:true}).count(),0);
 await move(ctx,'All Projects','projects');
 results.push('Company member sees allowed Projects and Profile actions');
 await ctx.page.close();
 ctx=await boot({admin:false,role:'member'},'?screen=admin');
 await ctx.core.getByText('Platform Admin access is required.',{exact:true}).waitFor();
 assert.equal(await ctx.core.locator('.platform-admin-table-card').count(),0);
 results.push('Direct Admin URL denied without platform access');
 await ctx.page.close();
 ctx=await boot();
 await move(ctx,'Profile','account');
 settings({admin:false});
 await move(ctx,'Admin','admin');
 await ctx.core.getByText('Platform Admin access is required.',{exact:true}).waitFor();
 assert.equal(await ctx.core.locator('.platform-admin-table-card').count(),0);
 results.push('Revoked Admin access handled without exposing dashboard');
 await ctx.page.close();
 ctx=await boot();
 settings({delay:{projects:18}});
 await ctx.core.getByRole('button',{name:'All Projects',exact:true}).dblclick();
 const retry=ctx.core.getByRole('button',{name:'Reload page',exact:true});
 await retry.waitFor({timeout:21000});
 assert.equal(await ctx.page.evaluate(()=>navMessages.filter(x=>x.covered).length),1);
 assert.equal(await ctx.page.evaluate(()=>navMessages.filter(x=>x.type==='costerly:transition-failed').length),1);
 assert.ok(await ctx.frame.evaluate(()=>{
  const cover=document.getElementById('costerly-workflow-transition');
  return cover?.contains(document.elementFromPoint(innerWidth/2,innerHeight/2));
 }));
 settings({});
 await retry.click();
 await ctx.core.locator('.upload-screen__hero').waitFor();
 await ctx.core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 results.push('Slow Projects double click starts one transition with explicit reload recovery');
 await ctx.page.close();
 writeFileSync(reportPath('screen-recovery.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results,null,2));
}catch(error){
 for (const context of browser.contexts()) for (const page of context.pages()) {
  await page.screenshot({path:reportPath('screen_recovery-failure.png')}).catch(()=>{});
 }
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
