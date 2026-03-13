import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import type { AnalysisConfig } from '@/types/domain';
import { fromJSON, validateConfig, downloadConfig } from '@/domain/configSerializer';
import { useWorkspaceLifecycle } from '@/composables/useWorkspaceLifecycle';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useChartsStore } from '@/stores/charts';
import { useConfigManagerStore } from '@/stores/configManager';
import { useNotify } from '@/composables/useNotify';

export function useConfigManagerStep() {
  const router = useRouter();
  const datasetStore = useDatasetStore();
  const columnsStore = useColumnsStore();
  const parametersStore = useParametersStore();
  const derivedStore = useDerivedColumnsStore();
  const chartsStore = useChartsStore();
  const configManagerStore = useConfigManagerStore();
  const { notifySuccess, notifyError } = useNotify();

  const { columnNames, metadata } = storeToRefs(datasetStore);
  const { hydrateFromConfig } = useWorkspaceLifecycle();

  const metadataParameterNames = computed(() =>
    Object.keys(metadata.value.parameters || {})
  );

  const defaultConfigName = computed(() =>
    datasetStore.filename ? datasetStore.filename.replace(/\.csv$/i, '') : 'My Analysis'
  );

  function buildConfigPayload(name: string, description: string) {
    return {
      name,
      description,
      selectedColumns: columnsStore.selectedColumnNames,
      parameters: parametersStore.allParameters,
      derivedColumns: derivedStore.derivedColumns,
      charts: chartsStore.charts,
      columnOrder: columnsStore.columnOrder,
      parameterOrder: columnsStore.parameterOrder,
      separators: columnsStore.separators,
      separatorColor: columnsStore.separatorColor,
      columnMetadata: configManagerStore.currentConfig?.columnMetadata,
      matchingGroups: columnsStore.matchingGroups,
    };
  }

  function applyLoadedConfig(config: AnalysisConfig, sourceConfigId: number | null = null) {
    const result = validateConfig(config, columnNames.value, metadataParameterNames.value);
    configManagerStore.setValidationResult(result);

    if (result.errors.length === 0) {
      configManagerStore.setConfig(config, sourceConfigId);
      hydrateFromConfig(config);
    }

    if (router.currentRoute.value.name !== 'analysis-import') {
      void router.push({ name: 'analysis-import' }).catch(() => {});
    }
  }

  function handleSave(name: string, description: string) {
    if (!parametersStore.isValid) {
      notifyError('Save Failed', 'Please fix parameter validation errors before saving.');
      return;
    }
    const config = configManagerStore.createConfig(buildConfigPayload(name, description));
    downloadConfig(config);
  }

  async function handleSaveToDb(name: string, description: string) {
    if (!parametersStore.isValid) {
      notifyError('Save Failed', 'Please fix parameter validation errors before saving.');
      return;
    }
    const config = configManagerStore.createConfig(buildConfigPayload(name, description));
    try {
      await configManagerStore.saveToBackend(name, '', config);
      await configManagerStore.fetchAllFromBackend();
      notifySuccess('Configuration Saved', `"${name}" is now available in your workspace.`);
    } catch (error) {
      notifyError('Save Failed', error);
    }
  }

  function handleLoad(json: string) {
    try {
      const config = fromJSON(json);
      applyLoadedConfig(config, null);
    } catch (error: unknown) {
      const err = error as { message?: string };
      configManagerStore.setValidationResult({
        valid: false,
        errors: [{
          code: 'PARSE_ERROR',
          message: err.message || 'Failed to parse config file',
        }],
        warnings: [],
      });
    }
  }

  async function handleLoadById(id: number) {
    try {
      const fullData = await configManagerStore.loadFromBackend(id);
      applyLoadedConfig(fullData.config_data, id);
    } catch (error) {
      notifyError('Load Failed', error);
    }
  }

  return {
    defaultConfigName,
    handleSave,
    handleSaveToDb,
    handleLoad,
    handleLoadById,
  };
}
