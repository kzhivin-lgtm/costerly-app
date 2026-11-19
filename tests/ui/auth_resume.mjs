import {statePath,reportPath,chromeOptions} from './support.mjs';
import {readFileSync,writeFileSync} from 'node:fs';
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const source=readFileSync('cloudflare/index.html','utf8');
const firstBuild=source.match(/const BUILD_VERSION = "([^"]+)"/)[1];
const config=statePath('auth-scenario.json'),provider=statePath('auth-provider.json');
let deliveries=0,versionReads=0;
const settings=value=>writeFileSync(config,JSON.stringify(value));
settings({build:firstBuild});
const server=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 if(req.url.startsWith('/version.json')){versionReads++;return res.writeHead(404).end();}
 if(new URL(req.url,'http://localhost').pathname!=='/')return res.writeHead(204).end();
 deliveries++;
 const build=JSON.parse(readFileSync(config,'utf8')).build;
 const html=source.replace(firstBuild,build).replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"');
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}).end(html);
});
await new Promise(r=>server.listen(8797,'127.0.0.1',r));
const browser=await chromium.launch(chromeOptions),page=await browser.newPage();page.setDefaultTimeout(15000);
const core=page.frameLocator('#costerly-app-frame');
const frame=async()=> (await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
try{
 await page.goto('http://127.0.0.1:8797/');
 await core.getByRole('button',{name:'Fixture sign in',exact:true}).click();
 await core.locator('[data-auth-user="fixture-user"]').waitFor();
 await page.locator('iframe.is-ready').waitFor();
 await (await frame()).waitForFunction(()=>JSON.parse(sessionStorage.getItem('costerly.supabase.session.v1')||'null')?.refresh_token==='synthetic-refresh-1');
 const staleCookie=(await page.context().cookies()).find(c=>c.name==='__Host-costerly-resume-v1');
 assert.ok(staleCookie,'initial sealed resume cookie');
 const report=[];
 for(let n=1;n<=2;n++){
  const build=firstBuild.replace(/-b([0-9]{14})-/,(_,v)=>'-b'+String(BigInt(v)+BigInt(n))+'-');
  settings({build,offset:3601*n});
  await core.getByRole('button',{name:'Fixture rerun',exact:true}).click();
  await page.waitForFunction(build=>[...document.scripts].some(s=>s.textContent.includes('const BUILD_VERSION = "'+build+'"')),build);
  await core.locator('[data-auth-user="fixture-user"]').waitFor();
  await page.locator('iframe.is-ready').waitFor();
  const expected='synthetic-refresh-'+(n+1);
  await (await frame()).waitForFunction(expected=>JSON.parse(sessionStorage.getItem('costerly.supabase.session.v1')||'null')?.refresh_token===expected,expected);
  const data=JSON.parse(readFileSync(provider,'utf8'));
  assert.equal(data.generation,n+1);assert.equal(data.refreshes,n);assert.equal(deliveries,n+1);
  assert.equal(await core.getByRole('button',{name:'Fixture sign in',exact:true}).count(),0);
  report.push({round:n,signedIn:true,generation:data.generation,refreshes:data.refreshes,outerLoads:deliveries,restore:await core.getByText(/^restore:/).innerText()});
 }
 // A shared cookie can lag this tab's rotated session (for example another tab).
 // The rejected cookie must not erase the newer valid tab session.
 await page.context().addCookies([staleCookie]);
 await page.reload();
 await core.locator('[data-auth-user="fixture-user"]').waitFor();
 assert.equal(await core.getByRole('button',{name:'Fixture sign in',exact:true}).count(),0);
 assert.equal(JSON.parse(readFileSync(provider,'utf8')).generation,3);
 // A revoked session must still be rejected, rather than bypass auth.
 const lastBuild=JSON.parse(readFileSync(config,'utf8')).build;
 settings({build:lastBuild,offset:10803,revoked:true});
 await core.getByRole('button',{name:'Fixture rerun',exact:true}).click();
 await core.getByRole('button',{name:'Fixture sign in',exact:true}).waitFor();
 assert.equal(await core.locator('[data-auth-user]').count(),0);
 assert.equal(versionReads,0);
 // Owner sequence: fresh real sign_in callback, then a newer Core on the old wrapper.
 await page.close();
 const oldBuild=firstBuild.replace(/-b([0-9]{14})-/,(_,v)=>'-b'+String(BigInt(v)-1n)+'-');
 writeFileSync(provider,JSON.stringify({generation:0,refreshes:0}));
 settings({build:oldBuild,build_after_signin:firstBuild});deliveries=0;
 const freshContext=await browser.newContext();const fresh=await freshContext.newPage();
 const freshCore=fresh.frameLocator('#costerly-app-frame');
 await fresh.goto('http://127.0.0.1:8797/');
 await freshCore.getByRole('button',{name:'Fixture sign in',exact:true}).click();
 await fresh.waitForFunction(build=>[...document.scripts].some(s=>s.textContent.includes('const BUILD_VERSION = "'+build+'"')),firstBuild);
 await freshCore.locator('[data-auth-user="fixture-user"]').waitFor();
 await fresh.locator('iframe.is-ready').waitFor();
 assert.equal(deliveries,2);assert.equal(JSON.parse(readFileSync(provider,'utf8')).signins,1);
 assert.equal(await freshCore.getByRole('button',{name:'Fixture sign in',exact:true}).count(),0);
 await freshContext.close();
 writeFileSync(reportPath('auth-resume.json'),JSON.stringify({rounds:report,staleCookieRecoveredFromNewerTabSession:true,revokedSessionRejected:true,freshSignInThenVersionReloadRetained:true,versionFileRequests:versionReads},null,2));
 console.log(JSON.stringify(report));
}catch(error){await page.screenshot({path:reportPath('auth-resume-failure.png')}).catch(()=>{});console.error(await core.locator('body').innerText().catch(()=>'(navigating)'));throw error;}
finally{await browser.close();await new Promise(r=>server.close(r));}
