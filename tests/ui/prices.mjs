import {statePath,reportPath,chromeOptions} from './support.mjs';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync} from 'node:fs';
import {createServer} from 'node:http';
import {chromium} from 'playwright';
const server=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(readFileSync('cloudflare/index.html','utf8').replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"'));
});
await new Promise(resolve=>server.listen(8796,'127.0.0.1',resolve));
const browser=await chromium.launch(chromeOptions);
const results=[];
let page,core;
try{
  rmSync(statePath('auth-expired'),{force:true});rmSync(statePath('profile-db.json'),{force:true});
  writeFileSync(statePath('scenario.json'),JSON.stringify({prices_catalog_size:300,prices_projection_delays:{catalog:3,sources:20,review:20,material_jobs:20}}));
  page=await browser.newPage({viewport:{width:1280,height:900}});page.setDefaultTimeout(10000);
  await page.goto('http://127.0.0.1:8796/');
  core=page.frameLocator('#costerly-app-frame');
  await page.locator('iframe.is-ready').waitFor();
  await core.getByRole('button',{name:'Profile',exact:true}).click();
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  await core.getByRole('tab',{name:'Price Lists',exact:true}).click();
  const groups=core.locator('[data-testid="stExpander"]');
  const metal=groups.filter({hasText:/Metal/});
  await metal.locator('summary').waitFor().catch(async error=>{
   writeFileSync(reportPath('prices-failure-dom.txt'),await core.locator('body').innerText());
   await page.screenshot({path:reportPath('prices-failure.png')});
   throw error;
  });
  assert.equal(await core.locator('[class*="st-key-price_catalog_row_"]').count(),0,'Closed catalog builds no row widgets');
  await metal.locator('summary').click();
  await core.locator('.st-key-price_catalog_row_price-row-0').waitFor();
  assert.equal(await core.locator('[class*="st-key-price_catalog_row_"]').count(),10,'Selected group renders while other catalog groups remain closed');
  const journal=readFileSync(statePath('browser-journal'),'utf8');
  if(width===1280)assert(!journal.includes('prices finished sources'),'Selected group must not wait for unrelated source-library read');
  await metal.locator('summary').click();
  await core.locator('.st-key-price_catalog_row_price-row-0').waitFor({state:'hidden'});
  await metal.locator('details:not([open])').waitFor({state:'attached'});
  assert.equal(await metal.locator('details').first().evaluate(node=>node.open),false,'Closed group hides its cached content');
  await metal.locator('summary').click();
  await core.locator('.st-key-price_catalog_row_price-row-0').waitFor();
  assert.equal(readFileSync(statePath('browser-journal'),'utf8').split('prices started catalog').length-1,1,'Reopening reuses the prepared snapshot');
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  await page.screenshot({path:reportPath('prices-lazy-'+width+'.png')});
  results.push({width,rows:10,closedRows:290,independentRead:true});
  await metal.locator('summary').click();
  await core.locator('.st-key-price_catalog_row_price-row-0').waitFor({state:'hidden'});
  await metal.locator('details:not([open])').waitFor({state:'attached'});
  assert.equal(await metal.locator('details').first().evaluate(node=>node.open),false,'Closed group hides its cached content');
  await core.getByRole('tab',{name:'Contacts',exact:true}).click();
  await core.getByRole('button',{name:'Save Contacts',exact:true}).waitFor();
 }
 await page.close();
 writeFileSync(reportPath('prices.json'),JSON.stringify({status:'passed',results},null,2));
 console.log(JSON.stringify(results));
}catch(error){
 if(page&&core){writeFileSync(reportPath('prices-failure-dom.txt'),await core.locator('body').innerText());writeFileSync(reportPath('prices-failure-classes.txt'),JSON.stringify(await core.locator('[class*=\"st-key-\"]').evaluateAll(nodes=>nodes.map(n=>n.className))));await page.screenshot({path:reportPath('prices-failure.png')});}
 throw error;
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
