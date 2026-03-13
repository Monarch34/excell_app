import { getProcessedRunData, processData } from '@/services/processingApi';
import type { ProcessRequest, ProcessResponse } from '@/types/api';
import type { DerivedColumnDef } from '@/types/domain';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useConfigManagerStore } from '@/stores/configManager';
import { useAnalysisStore } from '@/stores/analysis';
import { buildHeaderMappingFromConfig } from '@/utils/headerMapping';
import { toUserMessage, logError, isAbortError } from '@/utils/errors';

interface RunAnalysisInput {
  filename: string;
  datasetId: string | null;
  metadataParameters: Record<string, number> | null;
  metadataUnits: Record<string, string>;
  columnMapping: Record<string, string>;
  headerMapping: Record<string, string>;
  parameterMap: Record<string, number>;
  referenceRowIndex: number | null;
  derivedColumns: DerivedColumnDef[];
}

function buildInitialResults(referenceRowIndex: number | null): ProcessRequest['initial_results'] {
  if (referenceRowIndex === null) {
    return {};
  }
  return {
    manual_reference_index: referenceRowIndex,
  };
}

export async function runAnalysisRequest(
  input: RunAnalysisInput,
  signal?: AbortSignal,
): Promise<ProcessResponse> {
  if (!input.datasetId) {
    throw new Error('Dataset not initialized. Please upload a file again.');
  }
  const payload: ProcessRequest = {
    dataset_id: input.datasetId,
    parameters: { ...(input.metadataParameters || {}), ...input.parameterMap },
    units: input.metadataUnits,
    column_mapping: input.columnMapping,
    header_mapping: input.headerMapping,
    project_name: (input.filename.lastIndexOf('.') > 0
      ? input.filename.slice(0, input.filename.lastIndexOf('.'))
      : input.filename) || 'Analysis',
    operations: [],
    initial_results: buildInitialResults(input.referenceRowIndex),
    user_formulas: input.derivedColumns
      .filter((dc) => dc.type !== 'parameter')
      .map((dc) => ({
        name: dc.name,
        formula: dc.formula,
        unit: dc.unit,
        description: dc.description,
        enabled: dc.enabled,
      })),
    derived_parameters: input.derivedColumns
      .filter((dc) => dc.type === 'parameter' && dc.enabled)
      .map((dp) => ({
        name: dp.name,
        formula: dp.formula,
      })),
  };

  return processData(payload, signal);
}

/**
 * Module-level controller — intentionally a singleton so that only one analysis
 * request is in-flight at a time across all callers (components, composables).
 * Any new `runAnalysis()` call aborts the previous request first.
 */
let currentController: AbortController | null = null;

export function useAnalysisRunner() {
  async function loadProcessedData(runId?: string, signal?: AbortSignal): Promise<void> {
    const analysisStore = useAnalysisStore();
    const targetRunId = runId || analysisStore.runId;
    if (!targetRunId) return;

    try {
      const response = await getProcessedRunData(targetRunId, signal);
      analysisStore.setProcessedData(response.processed_data || []);
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        // Run snapshots are ephemeral in backend memory; clear stale id immediately.
        analysisStore.setRunId(null);
      }
      if (status === 404 && analysisStore.processedData.length > 0) {
        // Compatibility: keep inline processed rows when run snapshot is unavailable.
        return;
      }
      analysisStore.analysisError = toUserMessage(e);
      logError(e, 'loadProcessedData');
    }
  }

  async function runAnalysis(): Promise<void> {
    // Cancel any in-flight request.
    if (currentController) {
      currentController.abort();
    }
    currentController = new AbortController();
    const { signal } = currentController;

    const datasetStore = useDatasetStore();
    const columnsStore = useColumnsStore();
    const parametersStore = useParametersStore();
    const derivedStore = useDerivedColumnsStore();
    const configManagerStore = useConfigManagerStore();
    const analysisStore = useAnalysisStore();

    analysisStore.isAnalyzing = true;
    analysisStore.analysisError = null;

    try {
      const headerMapping = buildHeaderMappingFromConfig(configManagerStore.currentConfig);
      const data = await runAnalysisRequest(
        {
          filename: datasetStore.filename,
          datasetId: datasetStore.datasetId,
          metadataParameters: datasetStore.metadata.parameters,
          metadataUnits: datasetStore.metadata.units,
          columnMapping: columnsStore.columnMapping,
          headerMapping,
          parameterMap: parametersStore.parameterMap,
          referenceRowIndex: datasetStore.referenceRowIndex,
          derivedColumns: derivedStore.derivedColumns,
        },
        signal,
      );

      if (signal.aborted) return;

      analysisStore.setResults(data.results);
      analysisStore.setRunId(data.run_id);
      const inlineProcessedData = data.processed_data || [];
      analysisStore.setProcessedData(inlineProcessedData);
      if (inlineProcessedData.length === 0 && data.run_id) {
        await loadProcessedData(data.run_id, signal);
      }
    } catch (e: unknown) {
      if (signal.aborted || isAbortError(e)) return;
      analysisStore.setRunId(null);
      analysisStore.setProcessedData([]);
      analysisStore.setResults({});
      analysisStore.analysisError = toUserMessage(e);
      logError(e, 'runAnalysis');
    } finally {
      if (!currentController || currentController.signal === signal) {
        analysisStore.isAnalyzing = false;
        currentController = null;
      }
    }
  }

  /** Abort any in-flight analysis request. Callers should invoke in onBeforeUnmount. */
  function cancelAnalysis(): void {
    if (currentController) {
      currentController.abort();
      currentController = null;
    }
  }

  return { runAnalysis, loadProcessedData, cancelAnalysis };
}
