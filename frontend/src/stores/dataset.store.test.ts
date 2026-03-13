import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useDatasetStore } from '@/stores/dataset';
import type { UploadResponse } from '@/shared/types/api';

describe('dataset store import domain state', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('exposes import-only status fields and no analysis results state', () => {
    const store = useDatasetStore();
    expect(store.isImporting).toBe(false);
    expect(store.importError).toBeNull();
    expect((store as unknown as Record<string, unknown>).results).toBeUndefined();
  });

  it('clears importError and populates rows on upload response', () => {
    const store = useDatasetStore();
    store.importError = 'Old import error';

    const response: UploadResponse = {
      dataset_id: 'dataset-abc',
      filename: 'sample.csv',
      raw_data: [{ Load: 100 }],
      columns: ['Load'],
      dtypes: { Load: 'numeric' },
      parameters: null,
      parameter_units: {},
      units: { Load: 'N' },
    };

    store.setFromUploadResponse(response);

    expect(store.importError).toBeNull();
    expect(store.datasetId).toBe('dataset-abc');
    expect(store.rows).toEqual([{ Load: 100 }]);
    expect(store.rawRows).toEqual([{ Load: 100 }]);
    expect(store.columnNames).toEqual(['Load']);
  });

  it('reset clears import lifecycle state', () => {
    const store = useDatasetStore();
    store.isImporting = true;
    store.importError = 'Import failed';
    store.rows = [{ A: 1 }];

    store.reset();

    expect(store.isImporting).toBe(false);
    expect(store.importError).toBeNull();
    expect(store.datasetId).toBeNull();
    expect(store.rows).toEqual([]);
  });

  it('auto-names blank column headers as Column N', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-1',
      filename: 'test.csv',
      raw_data: [{ '': 1, 'Load': 2 }],
      columns: ['', 'Load'],
      dtypes: {},
      parameters: null,
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    expect(store.columnNames).toContain('Column 1');
    expect(store.columnNames).toContain('Load');
  });

  it('deduplicates column names with numeric suffix', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-2',
      filename: 'test.csv',
      raw_data: [{ Load: 1, Load_1: 2 }],
      columns: ['Load', 'Load'],
      dtypes: {},
      parameters: null,
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    const names = store.columnNames;
    const uniqueNames = new Set(names);
    expect(uniqueNames.size).toBe(names.length);
  });

  it('normalizes empty parameters object to null metadata', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-3',
      filename: 'test.csv',
      raw_data: [{ A: 1 }],
      columns: ['A'],
      dtypes: {},
      parameters: {},
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    expect(store.metadata.parameters).toBeNull();
  });

  it('defaults raw_data to empty array when not an array', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-4',
      filename: 'test.csv',
      raw_data: null as unknown as Record<string, unknown>[],
      columns: [],
      dtypes: {},
      parameters: null,
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    expect(store.rows).toEqual([]);
    expect(store.hasData).toBe(false);
  });

  it('sets referenceRowIndex to 0 when data is present', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-5',
      filename: 'test.csv',
      raw_data: [{ A: 1 }, { A: 2 }],
      columns: ['A'],
      dtypes: {},
      parameters: null,
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    expect(store.referenceRowIndex).toBe(0);
    expect(store.referenceRowUserSelected).toBe(false);
  });

  it('setReferenceRow marks user-selected', () => {
    const store = useDatasetStore();
    store.setReferenceRow(5);
    expect(store.referenceRowIndex).toBe(5);
    expect(store.referenceRowUserSelected).toBe(true);
  });

  it('hasData returns false initially', () => {
    const store = useDatasetStore();
    expect(store.hasData).toBe(false);
  });

  it('numericColumns filters by type', () => {
    const store = useDatasetStore();
    const response: UploadResponse = {
      dataset_id: 'ds-6',
      filename: 'test.csv',
      raw_data: [{ A: 1, B: 'text' }],
      columns: ['A', 'B'],
      dtypes: { A: 'numeric', B: 'text' },
      parameters: null,
      parameter_units: {},
      units: {},
    };

    store.setFromUploadResponse(response);

    expect(store.numericColumns.map((c) => c.name)).toContain('A');
    expect(store.textColumns.map((c) => c.name)).toContain('B');
  });
});
