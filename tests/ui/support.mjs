import { mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const stateDir = resolve(process.env.COSTERLY_UI_STATE_DIR || '.ui-artifacts/state');
export const reportDir = resolve(process.env.COSTERLY_UI_REPORT_DIR || '.ui-artifacts/browser');
mkdirSync(stateDir, { recursive: true });
mkdirSync(reportDir, { recursive: true });
export const statePath = name => join(stateDir, name);
export const reportPath = name => join(reportDir, name);
export const fixturePath = name => fileURLToPath(new URL('./fixtures/' + name, import.meta.url));
export const chromeOptions = { headless: true, ...(process.env.COSTERLY_CHROME ? { executablePath: process.env.COSTERLY_CHROME } : {}) };

// V3.2: actions follow content at every zoom. Retain26px clearance at scroll end;
// short pages may leave unused viewport below, never between business content/actions.
export async function checkClosingGap(frame,selector){
 await frame.locator(selector).waitFor();
 await frame.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const result=await frame.evaluate(async selector=>{
  const main=document.querySelector('[data-testid="stMain"]');
  main.scrollTop=main.scrollHeight;await new Promise(requestAnimationFrame);
  const node=document.querySelector(selector),rect=node.getBoundingClientRect();
  const previous=selector.includes('file_review')?'.file-review-missing-card':selector.includes('objects_actions')?'.objects-pricing-summary':'.object-detail-overhead-band';
  const content=document.querySelector(previous).getBoundingClientRect();
  const closing=selector.includes('object-detail')?document.querySelector('.object-detail-page-end').getBoundingClientRect():rect;
  const result={gap:innerHeight-46-rect.bottom,bottom:rect.bottom,height:innerHeight,
   scrollable:main.scrollHeight-main.clientHeight>1,contentGap:closing.top-content.bottom};
  main.scrollTop=0;await new Promise(requestAnimationFrame);return result;
 },selector);
 if((result.scrollable&&Math.abs(result.gap-26)>2)||result.gap<24||result.contentGap<0||result.contentGap>=100||
    (selector.includes('file_review')&&Math.abs(result.contentGap-28)>2))
  throw new Error('Closing content/Privacy gap '+JSON.stringify({selector,...result}));
 return result;
}
