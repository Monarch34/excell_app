import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const baselineDirUrl = new globalThis.URL('./baseline/', import.meta.url);
const baselineDir = fileURLToPath(baselineDirUrl);
mkdirSync(baselineDir, { recursive: true });

globalThis.console.log('Visual baseline scaffold ready.');
globalThis.console.log(`Baseline directory: ${baselineDir}`);
globalThis.console.log('Capture these key screens in a network-enabled environment:');
globalThis.console.log('1) Import Preview (desktop/tablet/mobile)');
globalThis.console.log('2) Charts (card collapsed + expanded + baseline dialog)');
globalThis.console.log('3) Analysis (chart section + fullscreen dialog)');
globalThis.console.log('4) Config (export panel + load panel)');
globalThis.console.log('Suggested capture approach: Playwright headed screenshots via skill workflow.');
