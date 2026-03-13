import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { Dataset, DatasetMetadata, ColumnDef } from '@/types/domain';
import type { ProcessRow, UploadResponse } from '@/types/api';

export const useDatasetStore = defineStore('dataset', () => {
  // State

  const filename = ref('');
  const datasetId = ref<string | null>(null);
  const rows = shallowRef<ProcessRow[]>([]);
  const rawRows = shallowRef<ProcessRow[]>([]);
  const columns = ref<ColumnDef[]>([]);
  const metadata = ref<DatasetMetadata>({
    parameters: null,
    parameterUnits: {},
    units: {},
    rowCount: 0,
    parseWarnings: [],
  });
  const isImporting = ref(false);
  const importError = ref<string | null>(null);

  // Manual reference row selection (session-only, not persisted in configs)
  const referenceRowIndex = ref<number | null>(null);
  const referenceRowUserSelected = ref(false);

  // Getters

  const hasData = computed(() => rows.value.length > 0);

  const numericColumns = computed(() =>
    columns.value.filter((col) => col.type === 'numeric')
  );

  const textColumns = computed(() =>
    columns.value.filter((col) => col.type === 'text')
  );

  const columnNames = computed(() =>
    columns.value.map((col) => col.name)
  );

  const selectedColumns = computed(() =>
    columns.value.filter((col) => col.selected)
  );

  const dataset = computed<Dataset>(() => ({
    filename: filename.value,
    datasetId: datasetId.value,
    columns: columns.value,
    rows: rows.value,
    metadata: metadata.value,
  }));

  // Actions

  function createNormalizedColumnNames(sourceColumns: string[]) {
    const seen = new Map<string, number>();
    const usedNames = new Set(sourceColumns.map((c) => (c || '').trim()));
    const normalized: string[] = [];
    const renamedPairs: Array<{ from: string; to: string }> = [];

    for (let i = 0; i < sourceColumns.length; i += 1) {
      const original = sourceColumns[i];
      const base = (original || '').trim() || `Column ${i + 1}`;
      const count = (seen.get(base) || 0) + 1;
      seen.set(base, count);

      let nextName = count === 1 ? base : `${base} (${count})`;
      // Avoid collisions with original column names
      while (nextName !== original && usedNames.has(nextName)) {
        const bump = (seen.get(base) || count) + 1;
        seen.set(base, bump);
        nextName = `${base} (${bump})`;
      }
      usedNames.add(nextName);
      normalized.push(nextName);

      if (nextName !== original) {
        renamedPairs.push({ from: original || '(blank)', to: nextName });
      }
    }

    return { normalized, renamedPairs };
  }

  function remapRowKeys(
    inputRows: Record<string, unknown>[],
    sourceColumns: string[],
    targetColumns: string[],
  ): ProcessRow[] {
    const sourceSet = new Set(sourceColumns);

    return inputRows.map((row) => {
      const next: ProcessRow = {};
      const sourceRecord = row as Record<string, unknown>;

      // Primary mapping follows declared column order.
      for (let i = 0; i < sourceColumns.length; i += 1) {
        const source = sourceColumns[i];
        const target = targetColumns[i];
        next[target] = (sourceRecord[source] as number | string | null) ?? null;
      }

      // Preserve extra keys not declared in columns.
      for (const [key, value] of Object.entries(sourceRecord)) {
        if (!sourceSet.has(key)) {
          next[key] = (value as number | string | null) ?? null;
        }
      }

      return next;
    });
  }

  function remapStringLookup(
    lookup: Record<string, string> | undefined,
    sourceColumns: string[],
    targetColumns: string[],
  ): Record<string, string> {
    const next: Record<string, string> = {};

    for (let i = 0; i < sourceColumns.length; i += 1) {
      const source = sourceColumns[i];
      const target = targetColumns[i];
      const value = lookup?.[source];
      if (value !== undefined) {
        next[target] = value;
      }
    }

    return next;
  }

  function setFromUploadResponse(response: UploadResponse) {
    const sourceColumns = response.columns || [];
    const { normalized: normalizedColumns, renamedPairs } = createNormalizedColumnNames(sourceColumns);
    const rawData = Array.isArray(response.raw_data) ? response.raw_data : [];
    const normalizedRows = remapRowKeys(rawData as Record<string, unknown>[], sourceColumns, normalizedColumns);
    const normalizedDtypes = remapStringLookup(response.dtypes || {}, sourceColumns, normalizedColumns);
    const normalizedUnits = remapStringLookup(response.units || {}, sourceColumns, normalizedColumns);

    filename.value = response.filename;
    datasetId.value = response.dataset_id;
    rows.value = normalizedRows;
    rawRows.value = normalizedRows;

    // Build ColumnDef array from response
    columns.value = normalizedColumns.map((name) => ({
      name,
      type: normalizedDtypes[name] === 'numeric' ? 'numeric' as const : 'text' as const,
      unit: normalizedUnits[name] || '',
      selected: true,
    }));

    const parseWarnings: string[] = [];
    if (renamedPairs.length > 0) {
      const sample = renamedPairs.slice(0, 4).map((pair) => `${pair.from} -> ${pair.to}`).join(', ');
      const more = renamedPairs.length > 4 ? ` (+${renamedPairs.length - 4} more)` : '';
      parseWarnings.push(`Column names were normalized: ${sample}${more}.`);
    }

    metadata.value = {
      parameters: response.parameters && Object.keys(response.parameters).length > 0 ? response.parameters : null,
      parameterUnits: response.parameter_units || {},
      units: normalizedUnits,
      rowCount: rawData.length,
      parseWarnings,
    };

    // Default to first row as reference if data exists
    referenceRowIndex.value = rows.value.length > 0 ? 0 : null;
    referenceRowUserSelected.value = false;
    importError.value = null;
  }

  function setReferenceRow(index: number) {
    referenceRowIndex.value = index;
    referenceRowUserSelected.value = true;
  }

  function reset() {
    filename.value = '';
    datasetId.value = null;
    rows.value = [];
    rawRows.value = [];
    columns.value = [];
    metadata.value = {
      parameters: null,
      parameterUnits: {},
      units: {},
      rowCount: 0,
      parseWarnings: [],
    };
    isImporting.value = false;
    importError.value = null;
    referenceRowIndex.value = null;
    referenceRowUserSelected.value = false;
  }

  return {
    // State
    filename,
    datasetId,
    rows,
    rawRows,
    columns,
    metadata,
    isImporting,
    importError,
    referenceRowIndex,
    referenceRowUserSelected,
    // Getters
    hasData,
    numericColumns,
    textColumns,
    columnNames,
    selectedColumns,
    dataset,
    // Actions
    setFromUploadResponse,
    setReferenceRow,
    reset,
  };
});
