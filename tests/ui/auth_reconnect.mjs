import {readFileSync,writeFileSync,openSync,existsSync,unlinkSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
import {statePath,reportPath,chromeOptions} from './support.mjs';
import {chromium} from 'playwright';
const config=statePath('auth-scenario.json'),db=statePath('auth-provider.json');
if(existsSync(db))unlinkSync(db);
const source=readFileSync('cloudflare/index.html','utf8');
const current=source.match(/const BUILD_VERSION = "([^"]+)"/)[1];
const old=current.replace(/-b([0-9]{14})-/,(_,v)=>'-b'+String(BigInt(v)-1n)+'-');
writeFileSync(config,JSON.stringify({build:old}));let proc,loads=0;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function start(label){
 proc=spawn('.venv/bin/python',['-m','streamlit','run','tests/ui/auth_resume_fixture.py','--server.port=8789','--server.address=127.0.0.1','--server.headless=true','--browser.gatherUsageStats=false'],{env:{...process.env,COSTERLY_UI_STATE_DIR:process.env.COSTERLY_UI_STATE_DIR,COSTERLY_UI_REPORT_DIR:process.env.COSTERLY_UI_REPORT_DIR},stdio:['ignore',openSync(reportPath('auth-reconnect-'+label+'-server.log'),'w'),'pipe']});
 proc.stderr.on('data',()=>{});
 for(let n=0;n<80;n++){try{if((await fetch('http://127.0.0.1:8789/_stcore/health',{signal:AbortSignal.timeout(200)})).ok)return;}catch{}await delay(100);}
 throw Error('Server not ready');
}
async function stop(){
 if(!proc||proc.exitCode!==null||proc.signalCode!==null)return;
 const p=proc,exited=new Promise(r=>p.once('exit',r));let timer;
 p.kill('SIGTERM');await Promise.race([exited,new Promise(r=>timer=setTimeout(r,1500))]);clearTimeout(timer);
 if(p.exitCode===null&&p.signalCode===null){p.kill('SIGKILL');await exited;}
}
const server=createServer((req,res)=>{
 if(req.url.startsWith('/api/'))return res.writeHead(202).end();
 if(new URL(req.url,'http://localhost').pathname!=='/')return res.writeHead(204).end();
 loads++;const build=JSON.parse(readFileSync(config,'utf8')).build;
 res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'}).end(source.replace(current,build).replace('data-src="https://core.costerly.ai/?embed=true"','data-src="http://127.0.0.1:8789/?embed=true"'));
});
await new Promise(r=>server.listen(8797,'127.0.0.1',r));let browser;
try{
 await start('first');browser=await chromium.launch(chromeOptions);
 const page=await browser.newPage();page.setDefaultTimeout(12000);const core=page.frameLocator('#costerly-app-frame');
 await page.goto('http://127.0.0.1:8797/');await page.locator('iframe.is-ready').waitFor();
 await core.getByLabel('Email',{exact:true}).fill('fixture@example.invalid');await core.getByLabel('Password',{exact:true}).fill('SyntheticPassword1!');
 await stop();writeFileSync(config,JSON.stringify({build:current}));await start('restarted');
 const before=loads;await core.getByRole('button',{name:'Sign in',exact:true}).click();
 let signedIn=true;try{
  await page.waitForFunction(build=>[...document.scripts].some(s=>s.textContent.includes('const BUILD_VERSION = "'+build+'"')),current,{timeout:12000});
  await core.locator('[data-auth-user="fixture-user"]').waitFor({timeout:12000});
  await page.locator('iframe.is-ready').waitFor();
 }catch{signedIn=false;}
 const data=existsSync(db)?JSON.parse(readFileSync(db,'utf8')):{signins:0};
 const report={loadsBeforeClick:before,outerLoads:loads,signins:data.signins||0,signedIn,body:(await core.locator('body').innerText()).slice(-500)};
 writeFileSync(reportPath('auth-reconnect.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 assert.equal(before,1,'The submitted form must belong to the previous server');
 assert.equal(data.signins,1,'One native submit must authenticate exactly once');
 assert.equal(signedIn,true,'One submit after server restart must retain login');
 assert.equal(loads,2,'The newer build must automatically reload the outer page once');
}finally{await browser?.close();await stop();await new Promise(r=>server.close(r));}
