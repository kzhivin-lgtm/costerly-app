import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync} from 'node:fs';
import {statePath,reportPath} from './support.mjs';

export async function checkLastEstimateRestore(browser,url){
 writeFileSync(statePath('scenario.json'),JSON.stringify({last_estimate_latency:true,labor_ready:true}));
 const page=await browser.newPage({viewport:{width:1280,height:1000}});
 page.setDefaultTimeout(18000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
  if(window!==top)return;
  window.restoreMessages=[];
  addEventListener('message',e=>{
   if(['costerly:app-ready','costerly:transition-click','costerly:transition-failed'].includes(e.data?.type))
    restoreMessages.push({type:e.data.type,screen:e.data.screen,id:e.data.transitionId,transition:e.data.transition,at:performance.now()});
  });
 });
 try{
  await page.goto(url);await page.locator('iframe.is-ready').waitFor();
  const core=page.frameLocator('#costerly-app-frame');
  const frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  await frame.waitForFunction(()=>window.__costerlyWorkflowTransition?.enabled());
  const before=readFileSync(statePath('browser-journal'),'utf8');
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  await page.waitForFunction(()=>{
   const click=restoreMessages.find(x=>x.type==='costerly:transition-click'&&x.transition==='last_estimate');
   return click&&restoreMessages.some(x=>x.type==='costerly:app-ready'&&x.screen==='file_review'&&x.id===click.id);
  });
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  const messages=await page.evaluate(()=>restoreMessages);
  const click=messages.find(x=>x.type==='costerly:transition-click'&&x.transition==='last_estimate');
  const ready=messages.find(x=>x.type==='costerly:app-ready'&&x.screen==='file_review'&&x.id===click.id);
  assert.ok(ready.at-click.at<15000,'Restore must finish before the unchanged native15s deadline');
  assert.equal(messages.some(x=>x.type==='costerly:transition-failed'),false);
  assert.ok(await core.getByRole('button',{name:/^continue to project$/i}).isEnabled());
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  const calls=readFileSync(statePath('browser-journal'),'utf8').slice(before.length);
  for(const name of ['source','naming','identity','fetch_rfq_object_estimates','fetch_rfq_estimate_pricing_overrides','fetch_rfq_estimate_material_plan']){
   assert.ok(calls.includes('restore-read-start '+name)&&calls.includes('restore-read-end '+name),name+' must actually complete');
  }
  assert.ok(!calls.includes('ERROR tried to estimate'),'Last Estimate must reuse saved calculations');
  assert.deepEqual(errors,[]);
  const result={clickToReadyMs:Math.round(ready.at-click.at),deadlineMs:15000,allCanonicalReadsCompleted:true};
  writeFileSync(reportPath('last-estimate-restore.json'),JSON.stringify(result,null,2));
  await page.screenshot({path:reportPath('last-estimate-restore.png'),fullPage:true});
  // Real outer document reload destroys Python session caches. It must restore
  // the same owned route/data with every canonical read, not start estimation.
  const beforeReload=readFileSync(statePath('browser-journal'),'utf8');
  const reloadStarted=Date.now();
  await page.reload({waitUntil:'domcontentloaded'});
  await page.locator('iframe.is-ready').waitFor();
  await core.getByRole('button',{name:/^continue to project$/i}).waitFor();
  assert.ok(await core.getByRole('button',{name:/^continue to project$/i}).isEnabled());
  const reloadMs=Date.now()-reloadStarted;
  assert.ok(reloadMs<15000,'Full restore must complete the same delayed reads within15s');
  const restoredCalls=readFileSync(statePath('browser-journal'),'utf8').slice(beforeReload.length);
  for(const name of ['source','naming','identity','fetch_rfq_object_estimates','fetch_rfq_estimate_pricing_overrides','fetch_rfq_estimate_material_plan'])
   assert.ok(restoredCalls.includes('restore-read-start '+name)&&restoredCalls.includes('restore-read-end '+name),name+' must complete on reload');
  assert.ok(!restoredCalls.includes('ERROR tried to estimate'));
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  result.fullReloadMs=reloadMs;
  writeFileSync(reportPath('last-estimate-restore.json'),JSON.stringify(result,null,2));
  await page.screenshot({path:reportPath('file-review-full-reload.png'),fullPage:true});
  return result;
 }catch(error){
  writeFileSync(reportPath('last-estimate-restore-failure.json'),JSON.stringify(await page.evaluate(()=>restoreMessages),null,2));
  await page.screenshot({path:reportPath('last-estimate-restore-failure.png'),fullPage:true});
  throw error;
 }finally{await page.close();rmSync(statePath('scenario.json'),{force:true});}
}
