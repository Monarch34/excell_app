import { useConfigApplicator } from '@/composables/useConfigApplicator';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useChartsStore } from '@/stores/charts';
import { useAnalysisStore } from '@/stores/analysis';
import { useConfigManagerStore } from '@/stores/configManager';
import type { AnalysisConfig } from '@/shared/types/domain';
import type { UploadResponse } from '@/shared/types/api';

/**
 * Central workspace lifecycle composable.
 *
 * All state transitions flow through one of these four actions.
 * Navigation and routing are never touched here.
 */
export function useWorkspaceLifecycle() {
  const datasetStore = useDatasetStore();
  const columnsStore = useColumnsStore();
  const parametersStore = useParametersStore();
  const derivedStore = useDerivedColumnsStore();
  const chartsStore = useChartsStore();
  const analysisStore = useAnalysisStore();
  const configManagerStore = useConfigManagerStore();
  const { applyConfig } = useConfigApplicator();

  /** Resets all subordinate stores (everything except dataset). */
  function resetSubordinateStores() {
    analysisStore.reset();
    chartsStore.reset();
    derivedStore.reset();
    parametersStore.reset();
    columnsStore.reset();
    configManagerStore.resetWorkspaceState();
  }

  /** Full wipe of every store. Used by "Done" and "Upload Different". */
  function resetWorkspace() {
    resetSubordinateStores();
    datasetStore.reset();
  }

  /** File upload without config — clean slate for subordinate stores. */
  function replaceDataset(response: UploadResponse) {
    resetSubordinateStores();
    datasetStore.setFromUploadResponse(response);
  }

  /**
   * Pure hydration via applyConfig — no resets, no navigation.
   * Callers are responsible for setting config metadata on configManagerStore
   * (setConfig, setValidationResult) before or after this call.
   * This is the canonical entry-point for all config hydration.
   */
  function hydrateFromConfig(config: AnalysisConfig) {
    applyConfig(config);
  }

  /**
   * File upload with a valid config: clear analysis results, install the new
   * dataset, then hydrate all subordinate stores from the config in one pass.
   * Subordinate stores (charts, derived, params, columns) are replaced by
   * applyConfig — no prior reset needed since loadFromConfig overwrites fully.
   */
  function replaceDatasetWithConfig(response: UploadResponse, config: AnalysisConfig) {
    analysisStore.reset();
    datasetStore.setFromUploadResponse(response);
    applyConfig(config);
  }

  return {
    resetWorkspace,
    replaceDataset,
    hydrateFromConfig,
    replaceDatasetWithConfig,
  };
}
