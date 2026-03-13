import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DerivedColumnDef } from '@/shared/types/domain';
import { fetchLimits } from '@/services/configsApi';

// The authoritative limit comes from the backend at startup (see initLimits).
// 50 is used as the default to match the backend default until the fetch resolves.
const maxDerivedColumnsRef = ref(50);

export async function initDerivedColumnLimits(): Promise<void> {
  try {
    const limits = await fetchLimits();
    maxDerivedColumnsRef.value = limits.max_derived_columns;
  } catch {
    // Keep the safe default if the fetch fails (e.g. backend not yet up).
  }
}

let nextId = 1;
function generateId(): string {
  return `dc-${String(nextId++).padStart(3, '0')}`;
}

/**
 * Derived Columns store - manages user-defined calculated columns.
 */
export const useDerivedColumnsStore = defineStore('derivedColumns', () => {
  // ─── State ─────────────────────────────────────────────────────────────────

  const derivedColumns = ref<DerivedColumnDef[]>([]);
  const activeColumnId = ref<string | null>(null);

  // ─── Getters ───────────────────────────────────────────────────────────────

  const count = computed(() => derivedColumns.value.length);

  const canAdd = computed(() => derivedColumns.value.length < maxDerivedColumnsRef.value);

  const enabledColumns = computed(() =>
    derivedColumns.value.filter((dc) => dc.enabled)
  );

  const activeColumn = computed(() =>
    derivedColumns.value.find((dc) => dc.id === activeColumnId.value) || null
  );

  const columnNames = computed(() =>
    derivedColumns.value.map((dc) => dc.name)
  );

  // ─── Actions ───────────────────────────────────────────────────────────────

  function addColumn(partial?: Partial<DerivedColumnDef>): string | null {
    if (!canAdd.value) return null;

    const id = generateId();
    const column: DerivedColumnDef = {
      id,
      name: partial?.name || `Derived_${count.value + 1}`,
      formula: partial?.formula || '',
      unit: partial?.unit || '',
      description: partial?.description || '',
      dependencies: partial?.dependencies || [],
      enabled: partial?.enabled ?? true,
      type: partial?.type || 'column',
    };

    derivedColumns.value.push(column);
    activeColumnId.value = id;
    return id;
  }

  function updateColumn(id: string, updates: Partial<DerivedColumnDef>) {
    const col = derivedColumns.value.find((dc) => dc.id === id);
    if (col) {
      Object.assign(col, updates);
    }
  }

  function removeColumn(id: string) {
    const idx = derivedColumns.value.findIndex((dc) => dc.id === id);
    if (idx >= 0) {
      derivedColumns.value.splice(idx, 1);
      if (activeColumnId.value === id) {
        activeColumnId.value = derivedColumns.value[0]?.id || null;
      }
    }
  }

  function toggleEnabled(id: string) {
    const col = derivedColumns.value.find((dc) => dc.id === id);
    if (col) {
      col.enabled = !col.enabled;
    }
  }

  function setActiveColumn(id: string | null) {
    activeColumnId.value = id;
  }

  function reorder(fromIndex: number, toIndex: number) {
    if (
      fromIndex >= 0 &&
      fromIndex < derivedColumns.value.length &&
      toIndex >= 0 &&
      toIndex < derivedColumns.value.length
    ) {
      const [item] = derivedColumns.value.splice(fromIndex, 1);
      derivedColumns.value.splice(toIndex, 0, item);
    }
  }

  function loadFromConfig(columns: DerivedColumnDef[]) {
    if (!Array.isArray(columns)) {
      derivedColumns.value = [];
      activeColumnId.value = null;
      return;
    }
    derivedColumns.value = columns
      .filter((c) => typeof c === 'object' && c !== null && typeof c.id === 'string')
      .map((c) => ({ ...c }));
    activeColumnId.value = derivedColumns.value[0]?.id || null;
    // Update nextId to avoid collisions
    const maxNum = columns.reduce((max, c) => {
      const match = c.id.match(/dc-(\d+)/);
      return match ? Math.max(max, parseInt(match[1], 10)) : max;
    }, 0);
    if (maxNum >= nextId) {
      nextId = maxNum + 1;
    }
  }

  function reset() {
    derivedColumns.value = [];
    activeColumnId.value = null;
    nextId = 1;
  }

  return {
    derivedColumns,
    activeColumnId,
    count,
    canAdd,
    enabledColumns,
    activeColumn,
    columnNames,
    addColumn,
    updateColumn,
    removeColumn,
    toggleEnabled,
    setActiveColumn,
    reorder,
    loadFromConfig,
    reset,
    maxDerivedColumns: maxDerivedColumnsRef,
  };
});
