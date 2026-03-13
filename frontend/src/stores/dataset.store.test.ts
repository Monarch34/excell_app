import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useDatasetStore } from '@/stores/dataset';
import type { UploadResponse } from '@/types/api';

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
});
