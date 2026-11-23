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

// Owner-approved9.45 closing geometry. Keep fixed Privacy and all body axes.
export async function checkClosingGap(frame,selector){
 await frame.locator(selector).waitFor();
 await frame.locator('#costerly-workflow-transition').waitFor({state:'hidden'});
 const result=await frame.evaluate(async selector=>{
  const main=document.querySelector('[data-testid="stMain"]');
  main.scrollTop=main.scrollHeight;await new Promise(requestAnimationFrame);
  const node=document.querySelector(selector),rect=node.getBoundingClientRect();
  const result={gap:innerHeight-46-rect.bottom,bottom:rect.bottom,height:innerHeight};
  main.scrollTop=0;await new Promise(requestAnimationFrame);return result;
 },selector);
 if(Math.abs(result.gap-26)>2)throw new Error('Fixed Privacy gap '+JSON.stringify({selector,...result}));
 return result;
}
