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
