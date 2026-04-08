import { readdir, readFile } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as ts from 'typescript';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SRC = join(ROOT, 'src');
const TARGET_DIRS = ['domain', 'types', 'services'];
const EXCLUDED_PREFIXES = [join(SRC, 'types', 'generated')];

async function listTsFiles(dir) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw err;
  }
  const files = [];

  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (EXCLUDED_PREFIXES.some((prefix) => full.startsWith(prefix))) {
      continue;
    }
    if (entry.isDirectory()) {
      files.push(...(await listTsFiles(full)));
      continue;
    }
    if (entry.isFile() && full.endsWith('.ts')) {
      files.push(full);
    }
  }

  return files;
}

function isAnyNode(node) {
  return node.kind === ts.SyntaxKind.AnyKeyword;
}

async function findAnyViolations(filePath) {
  const source = await readFile(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true);
  const violations = [];

  function walk(node) {
    if (isAnyNode(node)) {
      const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
      violations.push({
        file: relative(ROOT, filePath).replaceAll('\\', '/'),
        line: line + 1,
        column: character + 1,
      });
    }
    ts.forEachChild(node, walk);
  }

  walk(sourceFile);
  return violations;
}

async function main() {
  const files = (
    await Promise.all(TARGET_DIRS.map((segment) => listTsFiles(join(SRC, segment))))
  ).flat();
  const violations = (await Promise.all(files.map((file) => findAnyViolations(file)))).flat();

  if (violations.length === 0) {
    console.log('No explicit any found in src/domain, src/types, src/services.');
    return;
  }

  console.error('Explicit any is not allowed in domain/types/services:');
  for (const violation of violations) {
    console.error(`- ${violation.file}:${violation.line}:${violation.column}`);
  }
  process.exit(1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
