/* global console, process */

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const TARGET_DIRS = [
  'src/components/steps',
  'src/components/charts',
  'src/components/config',
  'src/components/import',
  'src/components/analysis',
  'src/components/columns',
  'src/components/params',
  'src/components/formulas',
  'src/views',
];

const CLASS_ATTR_RE = /class\s*=\s*["']([^"']*)["']/g;
const BANNED_SPACING_RE = /^(m|p)(t|r|b|l|x|y)?-\d+$/;

function collectVueFiles(dir) {
  const out = [];
  const fullDir = path.join(ROOT, dir);
  if (!fs.existsSync(fullDir)) return out;

  const stack = [fullDir];
  while (stack.length > 0) {
    const current = stack.pop();
    if (!current) continue;
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
      } else if (entry.isFile() && fullPath.endsWith('.vue')) {
        out.push(fullPath);
      }
    }
  }
  return out;
}

function toPosix(p) {
  return p.split(path.sep).join('/');
}

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const rel = toPosix(path.relative(ROOT, filePath));
  const violations = [];

  let match = CLASS_ATTR_RE.exec(content);
  while (match !== null) {
    const classValue = match[1];
    const tokens = classValue.split(/\s+/).filter(Boolean);
    for (const token of tokens) {
      if (BANNED_SPACING_RE.test(token)) {
        violations.push({ file: rel, token });
      }
    }
    match = CLASS_ATTR_RE.exec(content);
  }
  return violations;
}

function main() {
  const files = TARGET_DIRS.flatMap(collectVueFiles);
  const violations = files.flatMap(scanFile);

  if (violations.length === 0) {
    console.log('ui-guard: no banned spacing utility classes found in guarded UI directories.');
    process.exit(0);
  }

  console.error('ui-guard: banned spacing utility classes found:');
  for (const v of violations) {
    console.error(`- ${v.file}: ${v.token}`);
  }
  console.error('\nUse semantic ui-* classes + ui-foundation tokens instead of spacing utility tokens.');
  process.exit(1);
}

main();
