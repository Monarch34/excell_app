const SCHEMA_VERSION_KEY = 'excell-app-schema-version';
const REMOVAL_PREFIXES = ['charts.form.sections.'];
const REMOVAL_KEYS = ['charts.ui.state', 'excell-config-manager-storage'];

function collectKeysForRemoval(storage: Storage): string[] {
  const keys: string[] = [];

  for (let i = 0; i < storage.length; i += 1) {
    const key = storage.key(i);
    if (!key) continue;

    if (REMOVAL_KEYS.includes(key)) {
      keys.push(key);
      continue;
    }

    if (REMOVAL_PREFIXES.some((prefix) => key.startsWith(prefix))) {
      keys.push(key);
    }
  }

  return keys;
}

export function invalidateStorageForSchema(nextVersion: string): void {
  const storedVersion = localStorage.getItem(SCHEMA_VERSION_KEY);
  if (storedVersion === nextVersion) return;

  const keysToRemove = collectKeysForRemoval(localStorage);
  for (const key of keysToRemove) {
    localStorage.removeItem(key);
  }

  localStorage.setItem(SCHEMA_VERSION_KEY, nextVersion);
}
