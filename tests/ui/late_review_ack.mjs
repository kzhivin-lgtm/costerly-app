import assert from 'node:assert/strict';
import {existsSync, readFileSync, writeFileSync, rmSync} from 'node:fs';
import {statePath, reportPath} from './support.mjs';

// Send a late empty native text-widget ACK with the next two real auto-reruns.
// The framework retains the unmounted widget metadata. Before V3.8 its callback
// changed screen during a fragment-only run, clearing Project without an error.
async function carryLateAcknowledgements(frame, ids) {
 await frame.evaluate(ids => {
  const enc = new TextEncoder();
  const varint = n => {
   const out=[];
   do {const byte=n&127;n>>>=7;out.push(byte|(n?128:0));} while(n);
   return out;
  };
  const field = (number,value) => {
   const bytes=typeof value==='string'?[...enc.encode(value)]:value;
   return [...varint((number<<3)|2),...varint(bytes.length),...bytes];
  };
  const fields = bytes => {
   let i=0;const result=[];
   const read=()=>{let n=0,shift=0,byte;do{byte=bytes[i++];n+=(byte&127)*2**shift;shift+=7;}while(byte&128);return n;};
   while(i<bytes.length){
    const key=read(),wire=key&7;let value;
    if(wire===0)value=read();
    else if(wire===2){const size=read();value=bytes.slice(i,i+size);i+=size;}
    else if(wire===1)i+=8;
    else if(wire===5)i+=4;
    else throw new Error('Unexpected protobuf wire type '+wire);
    result.push({number:key>>3,value});
   }
   return result;
  };
  // BackMsg.rerun_script(11).widget_states(2).widgets(1), id(1), string_value(6).
  // Singular embedded messages merge, retaining the timer's real fragment id,
  // route, cache hashes and all other native widget values.
  const patches=ids.map(id=>field(11,field(2,field(1,[...field(1,id),...field(6,'')]))));
  window.__lateReviewAcksInjected=0;
  const original=WebSocket.prototype.send;
  WebSocket.prototype.send=function(data){
   const bytes=data instanceof ArrayBuffer?new Uint8Array(data):ArrayBuffer.isView(data)?new Uint8Array(data.buffer,data.byteOffset,data.byteLength):null;
   const client=bytes&&fields(bytes).find(f=>f.number===11)?.value;
   if(patches.length&&client&&fields(client).some(f=>f.number===6&&f.value===1)){
    const patch=patches.shift(),merged=new Uint8Array(bytes.length+patch.length);
    merged.set(bytes);merged.set(patch,bytes.length);window.__lateReviewAcksInjected++;
    if(!patches.length)WebSocket.prototype.send=original;
    return original.call(this,merged);
   }
   return original.call(this,data);
  };
 },ids);
}

export async function checkLateFileReviewAcknowledgements(browser, url) {
 writeFileSync(statePath('scenario.json'),JSON.stringify({objects_v2:true,labor_ready:true,late_review_ack:true}));
 const hold=statePath('hold-object-preparation');
 rmSync(hold,{force:true});
 const page=await browser.newPage({viewport:{width:1280,height:1000}});
 page.setDefaultTimeout(12000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  await page.goto(url);await page.locator('iframe.is-ready').waitFor();
  const core=page.frameLocator('#costerly-app-frame');
  const frame=await(await page.locator('#costerly-app-frame').elementHandle()).contentFrame();
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  await core.getByRole('button',{name:/^continue to project$/i}).click();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).waitFor();
  await core.getByRole('link',{name:/^(Done|Review)$/i}).click();
  await core.locator('.object-detail-shell').waitFor();
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  await core.getByRole('button',{name:'New Estimate',exact:true}).click();
  await core.getByRole('button',{name:'Last Estimate',exact:true}).click();
  await core.locator('[data-testid="stTextInput"] input').first().waitFor();
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  const journal=readFileSync(statePath('browser-journal'),'utf8').split('\n');
  const ids=['file_review_run_metadata.project_name','file_review_object_edits.object-001.name'].map(key=>{
   const row=journal.filter(x=>x.startsWith('review-field-widget-id ')&&x.endsWith('-'+key)).at(-1);
   assert.ok(row,'Native File Review metadata must register '+key);
   return row.slice('review-field-widget-id '.length);
  });
  const savedFiles=['project-metadata.json','object-names.json'].map(name=>{
   const path=statePath(name);return {path,before:existsSync(path)?readFileSync(path,'utf8'):null};
  });
  writeFileSync(hold,'hold');
  await core.getByRole('button',{name:/^continue to project$/i}).click();
  await core.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
  const renderId=await core.locator('[data-costerly-render-id]').getAttribute('data-costerly-render-id');
  await carryLateAcknowledgements(frame,ids);
  const samples=await frame.evaluate(async()=>{
   const samples=[],until=performance.now()+4000;
   do {
    const visible=s=>{const n=document.querySelector(s);return !!n&&n.getBoundingClientRect().height>0&&n.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});};
    samples.push({title:visible('.objects-estimation-header'),table:visible('.objects-pricing-table'),actions:visible('.st-key-objects_actions')});
    await new Promise(r=>setTimeout(r,50));
   }while(performance.now()<until);
   return {samples,injected:window.__lateReviewAcksInjected};
  });
  writeFileSync(reportPath('late-review-ack.json'),JSON.stringify(samples,null,2));
  await page.screenshot({path:reportPath('late-review-ack.png'),fullPage:true});
  assert.equal(samples.injected,2,'Both empty native acknowledgements must reach real fragment reruns');
  assert.ok(samples.samples.every(s=>s.title&&s.table&&s.actions),'Project must remain visible throughout late File Review ACKs');
  assert.equal(await core.locator('[data-costerly-render-id]').getAttribute('data-costerly-render-id'),renderId,'No compensating app rerun');
  for(const {path,before} of savedFiles)assert.equal(existsSync(path)?readFileSync(path,'utf8'):null,before,'Empty ACK must never write');
  rmSync(hold);
  await core.getByRole('link',{name:/^(Done|Review)$/i}).waitFor();
  assert.equal(await core.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  return {injected:samples.injected,visibleSamples:samples.samples.length,appReruns:0};
 } finally {rmSync(hold,{force:true});await page.close();}
}
