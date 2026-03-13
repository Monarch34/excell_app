import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAnalysisStore } from '@/stores/analysis';

describe('analysis store processing state', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes with analysis lifecycle defaults', () => {
    const store = useAnalysisStore();

    expect(store.isAnalyzing).toBe(false);
    expect(store.analysisError).toBeNull();
    expect(store.results).toEqual({});
    expect(store.processedData).toEqual([]);
    expect(store.runId).toBeNull();
  });

  it('reset clears processed data, error, and derived results', () => {
    const store = useAnalysisStore();
    store.isAnalyzing = true;
    store.analysisError = 'Processing failed';
    store.results = { computed_count: 12 };
    store.setProcessedData([{ A: 1 }]);
    store.setRunId('run-123');

    store.reset();

    expect(store.isAnalyzing).toBe(false);
    expect(store.analysisError).toBeNull();
    expect(store.results).toEqual({});
    expect(store.processedData).toEqual([]);
    expect(store.runId).toBeNull();
  });
});
