import { readdir, readFile } from 'node:fs/promises'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const SRC_ROOT = join(ROOT, 'src')

const DOMAIN_DISALLOWED = [
  '@/components/',
  '@/stores/',
  '@/services/',
  'vue',
  'pinia'
]

const STORE_DISALLOWED = ['@/components/']

const IMPORT_RE = /(?:import\s+[^'"]*from\s+|import\s*\(\s*)['"]([^'"]+)['"]/g
const CODE_EXT_RE = /\.(?:[cm]?[jt]sx?|vue)$/i
const TEST_EXT_RE = /\.(?:test|spec)\.[cm]?[jt]sx?$/i

async function listCodeFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await listCodeFiles(full)))
      continue
    }
    if (CODE_EXT_RE.test(entry.name)) {
      files.push(full)
    }
  }

  return files
}

async function collectViolations(files, checkFn) {
  const violations = []

  for (const file of files) {
    const rel = relative(SRC_ROOT, file).replaceAll('\\', '/')
    const source = await readFile(file, 'utf8')

    for (const match of source.matchAll(IMPORT_RE)) {
      const importPath = match[1]
      const reason = checkFn(importPath, rel)
      if (reason) {
        violations.push(`${rel}: ${importPath} (${reason})`)
      }
    }
  }

  return violations
}

function checkDomainImport(importPath) {
  if (DOMAIN_DISALLOWED.includes(importPath)) {
    return 'domain must stay framework/UI/transport agnostic'
  }

  if (DOMAIN_DISALLOWED.some((prefix) => prefix.endsWith('/') && importPath.startsWith(prefix))) {
    return 'domain must stay framework/UI/transport agnostic'
  }

  return null
}

function checkStoreImport(importPath, relPath) {
  if (TEST_EXT_RE.test(relPath)) {
    return null
  }

  if (STORE_DISALLOWED.some((prefix) => importPath.startsWith(prefix))) {
    return 'stores must not depend on components'
  }

  return null
}

async function main() {
  const domainDir = join(SRC_ROOT, 'domain')
  const storesDir = join(SRC_ROOT, 'stores')

  const [domainFiles, storeFiles] = await Promise.all([
    listCodeFiles(domainDir),
    listCodeFiles(storesDir)
  ])

  const [domainViolations, storeViolations] = await Promise.all([
    collectViolations(domainFiles, checkDomainImport),
    collectViolations(storeFiles, checkStoreImport)
  ])

  const violations = [...domainViolations, ...storeViolations]
  if (violations.length === 0) {
    console.log('Frontend boundary checks passed.')
    return
  }

  console.error('Frontend boundary violations found:')
  for (const violation of violations) {
    console.error(`- ${violation}`)
  }
  process.exit(1)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
