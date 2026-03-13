import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAnalysisRunner } from '@/composables/analysis/useAnalysisRunner';
import { useDatasetStore } from '@/stores/dataset';
import { useAnalysisStore } from '@/stores/analysis';

const processDataMock = vi.fn();
const getProcessedRunDataMock = vi.fn();

vi.mock('@/services/processingApi', () => ({
  processData: (...args: unknown[]) => processDataMock(...args),
  getProcessedRunData: (...args: unknown[]) => getProcessedRunDataMock(...args),
}));

describe('useAnalysisRunner store boundaries', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    processDataMock.mockReset();
    getProcessedRunDataMock.mockReset();
  });

  it('does not overwrite dataset rows after analysis run', async () => {
    const datasetStore = useDatasetStore();
    const analysisStore = useAnalysisStore();
    const { runAnalysis } = useAnalysisRunner();

    const baseRows = [{ Time: 0, Load: 100 }];
    datasetStore.filename = 'sample.csv';
    datasetStore.datasetId = 'dataset-123';
    datasetStore.rows = [...baseRows];
    datasetStore.rawRows = [...baseRows];
    datasetStore.metadata.parameters = { A0: 10 };
    datasetStore.metadata.units = { Load: 'N' };

    processDataMock.mockResolvedValue({
      results: { peak_stress: 10 },
      project_name: 'sample',
      units: { Load: 'N', Stress: 'MPa' },
      run_id: 'run-abc',
    });
    getProcessedRunDataMock.mockResolvedValue({
      processed_data: [],
    });

    await runAnalysis();

    expect(datasetStore.rows).toEqual(baseRows);
    expect(datasetStore.rawRows).toEqual(baseRows);
    expect(analysisStore.processedData).toEqual([]);
    expect(analysisStore.results).toEqual({ peak_stress: 10 });
    expect(analysisStore.runId).toBe('run-abc');
    expect(analysisStore.analysisError).toBeNull();
    expect(analysisStore.isAnalyzing).toBe(false);
  });

  it('uses inline processed_data when provided and does not fetch by run id', async () => {
    const datasetStore = useDatasetStore();
    const analysisStore = useAnalysisStore();
    const { runAnalysis } = useAnalysisRunner();

    datasetStore.filename = 'sample.csv';
    datasetStore.datasetId = 'dataset-123';
    datasetStore.rows = [{ Time: 0, Load: 100 }];
    datasetStore.rawRows = [{ Time: 0, Load: 100 }];

    processDataMock.mockResolvedValue({
      processed_data: [{ Time: 0, Load: 100, Stress: 10 }],
      results: { peak_stress: 10 },
      project_name: 'sample',
      units: { Load: 'N', Stress: 'MPa' },
      run_id: 'run-inline',
    });

    await runAnalysis();

    expect(getProcessedRunDataMock).not.toHaveBeenCalled();
    expect(analysisStore.processedData).toEqual([{ Time: 0, Load: 100, Stress: 10 }]);
    expect(analysisStore.analysisError).toBeNull();
  });

  it('loads processed rows on demand by run id', async () => {
    const analysisStore = useAnalysisStore();
    const { loadProcessedData } = useAnalysisRunner();

    analysisStore.setRunId('run-abc');
    getProcessedRunDataMock.mockResolvedValue({
      processed_data: [{ Time: 0, Load: 100, Stress: 10 }],
    });

    await loadProcessedData();

    expect(getProcessedRunDataMock).toHaveBeenCalledWith('run-abc', undefined);
    expect(analysisStore.processedData).toEqual([{ Time: 0, Load: 100, Stress: 10 }]);
  });

  it('keeps inline processed rows when run-data endpoint returns 404', async () => {
    const analysisStore = useAnalysisStore();
    const { loadProcessedData } = useAnalysisRunner();

    analysisStore.setRunId('run-legacy');
    analysisStore.setProcessedData([{ Time: 0, Load: 100 }]);
    getProcessedRunDataMock.mockRejectedValue({
      response: { status: 404 },
    });

    await loadProcessedData();

    expect(analysisStore.processedData).toEqual([{ Time: 0, Load: 100 }]);
    expect(analysisStore.analysisError).toBeNull();
  });
});
