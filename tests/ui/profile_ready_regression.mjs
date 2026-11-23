import assert from 'node:assert/strict';

// Test-only receipt delivery control. It holds a genuine Add Worker receipt
// until the genuine destination receipt, making the race deterministic.
export function observeProfileReady() {
 if(window===top||parent!==top)return;
 let controller;
 const state={mode:null,held:null,events:[],failure:null};
 window.profileReadyCase=state;
 Object.defineProperty(window,'__costerlyWorkflowTransition',{
  configurable:true,get:()=>controller,set:value=>{
   controller=value;
   const original=value.ready;
   value.ready=function(message){
    if(!state.mode)return original.call(this,message);
    const selected=document.querySelector('.st-key-company_profile_tab [aria-selected="true"]')?.textContent.trim();
    if(selected==='Labor Costs'&&document.querySelector('[data-profile-save-ack][data-profile-save-action="labor"]')){
     state.held=message;return true;
    }
    if(state.held&&message.runId===state.held.runId)return true;
    const marker=document.querySelector('[data-costerly-render-id]');
    if(selected!=='Pricing Cost'||!state.held||!value.busy()||marker?.dataset.costerlyRenderId!==message.runId)
     return original.call(this,message);
    const mode=state.mode;state.mode=null;
    const worker=state.held;
    state.events.push({kind:'injected',mode,workerRun:worker.runId,destinationRun:message.runId,at:Date.now()});
    const deliver=receipt=>original.call(this,receipt);
    const requireCovered=()=>{
     if(!value.busy()||!document.querySelector('#costerly-workflow-transition'))
      state.failure='The unfinished or wrong-tab render was revealed';
    };
    if(mode==='worker-first'){deliver(worker);return deliver(message);}
    if(mode==='pricing-first'){deliver(message);return deliver(worker);}
    if(mode==='duplicates'){deliver(worker);deliver(message);deliver(worker);return deliver(message);}
    if(mode==='ready-before-DOM'){
     const previous=marker.cloneNode(true);previous.dataset.costerlyRenderId=worker.runId;
     marker.replaceWith(previous);deliver(message);
     requestAnimationFrame(()=>{requireCovered();previous.replaceWith(marker);});
     return true;
    }
    if(mode==='stale-DOM'){
     const stale=document.createElement('span');stale.dataset.stale='true';stale.hidden=true;
     document.body.append(stale);deliver(message);
     requestAnimationFrame(()=>{requireCovered();stale.remove();});
     return true;
    }
    if(mode==='wrong-receipt'){
     deliver(worker);
     requestAnimationFrame(()=>{requireCovered();deliver(message);});
     return true;
    }
    if(mode==='wrong-tab'){
     const previous=marker.cloneNode(true);previous.dataset.costerlyRenderId=worker.runId;
     marker.replaceWith(previous);deliver(worker);
     requestAnimationFrame(()=>requestAnimationFrame(()=>{
      requireCovered();previous.replaceWith(marker);deliver(message);
     }));
     return true;
    }
    throw new Error('Unknown ready regression case');
   };
  },
 });
}

async function addWorker(ctx,name) {
 const {core}=ctx;
 const rendered=async action=>{
  const id=await core.locator('[data-costerly-render-id]').last().getAttribute('data-costerly-render-id');
  await action();
  await core.locator('[data-costerly-screen="account"]:not([data-costerly-render-id="'+id+'"])').waitFor({state:'attached'});
 };
 const select=async(label,option)=>rendered(async()=>{
  const control=core.getByRole('combobox',{name:label,exact:true});
  // Later cases have saved worker rows above the form. Center its native
  // picker so its options stay clear of the unchanged fixed embed footer.
  await control.evaluate(node=>node.scrollIntoView({block:'center'}));
  await control.click();
  await core.getByRole('option',{name:option,exact:true}).click();
 });
 await core.getByRole('textbox',{name:'Worker name',exact:true}).fill(name);
 await select('Department','Production');await select('Position','Carpenter');await select('Pay type','Hourly Rate');
 await rendered(()=>core.getByRole('textbox',{name:'Hourly Rate',exact:true}).fill('55').then(()=>core.getByRole('textbox',{name:'Hourly Rate',exact:true}).press('Tab')));
 await rendered(()=>core.getByRole('textbox',{name:'Average Hours per Month',exact:true}).fill('186').then(()=>core.getByRole('textbox',{name:'Average Hours per Month',exact:true}).press('Tab')));
 await core.getByRole('textbox',{name:'Total Monthly Cost',exact:true}).waitFor();
 await core.getByRole('button',{name:'Add Worker',exact:true}).click();
 await core.getByRole('button',{name:'Saved',exact:true}).waitFor();
}

export async function profileReadyRegressions({boot,move,tab,waitDb,database}) {
 const results=[];
 for(const mode of ['worker-first','pricing-first','duplicates','ready-before-DOM','stale-DOM','wrong-receipt','wrong-tab']){
  const ctx=await boot({},'',observeProfileReady);
  await move(ctx,'Profile','account');await tab(ctx,'Labor Costs');
  const before=database().company_employees.length,name='Ready '+mode;
  await ctx.frame.evaluate(mode=>{profileReadyCase.mode=mode;},mode);
  await addWorker(ctx,name);
  await waitDb(data=>data.company_employees.length===before+1&&data.company_employees.some(row=>row.worker_name===name));
  await ctx.frame.waitForFunction(()=>Boolean(profileReadyCase.held));
  const offset=await ctx.page.evaluate(()=>navMessages.length);
  await ctx.frame.evaluate(()=>{
   const state=profileReadyCase,header=document.querySelector('.company-profile-heading');
   const samples=[];let active=true;
   const sample=()=>{
    if(!active)return;
    const cover=document.querySelector('#costerly-workflow-transition'),bounds=cover?.getBoundingClientRect();
    const covered=Boolean(bounds?.width&&bounds.height&&cover.contains(document.elementFromPoint(bounds.x+bounds.width/2,bounds.y+Math.min(30,bounds.height/2))));
    samples.push({at:Date.now(),covered});requestAnimationFrame(sample);
   };
   state.stop=()=>{active=false;return {samples,headerRetained:header===document.querySelector('.company-profile-heading'),failure:state.failure,events:state.events};};
   sample();
  });
  await tab(ctx,'Pricing Cost');
  const observed=await ctx.frame.evaluate(()=>profileReadyCase.stop());
  assert.equal(observed.failure,null,mode);
  assert.equal(observed.headerRetained,true,mode);
  assert.equal(observed.events.length,1,mode);
  const events=await ctx.page.evaluate(offset=>navMessages.slice(offset),offset);
  const clicks=events.filter(e=>e.type==='costerly:transition-click'&&e.covered);
  assert.equal(clicks.length,1,JSON.stringify({mode,events}));
  const ready=events.filter(e=>e.type==='costerly:app-ready'&&e.id===clicks[0].id);
  assert.equal(ready.length,1,JSON.stringify({mode,events}));
  assert.equal(ready[0].runId,observed.events[0].destinationRun,mode);
  assert(Number.isFinite(ready[0].sentAt));
  const pending=observed.samples.filter(s=>s.at>=clicks[0].receivedAt&&s.at<ready[0].sentAt);
  assert(pending.length>0,mode+' must sample the pending cover');
  assert.equal(pending.filter(s=>!s.covered).length,0,JSON.stringify({mode,pending}));
  assert.equal(await ctx.core.locator('[data-testid="stException"]').count(),0);
  assert.equal(database().company_employees.length,before+1,mode+' must not duplicate writes');
  await tab(ctx,'Labor Costs');await ctx.core.getByText(name,{exact:true}).waitFor();
  results.push({mode,correlatedReady:ready[0].runId,coveredFrames:pending.length,uncoveredBeforeReady:0,workerWrites:1});
  await ctx.page.close();
 }
 return results;
}
