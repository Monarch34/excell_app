import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useConfigManagerStore } from '@/stores/configManager';
import { useDatasetStore } from '@/stores/dataset';
import { useConfirmDialog } from '@/composables/useConfirmDialog';
import { useNotify } from '@/composables/useNotify';
import { validateConfig } from '@/domain/configSerializer';
import { useWorkspaceLifecycle } from '@/composables/useWorkspaceLifecycle';
import {
  buildConfigDependencyModel,
  type DependencyKind,
} from '@/domain/configDependency';
import { CONFIG_VERSION } from '@/constants/config';
import { toUserMessage } from '@/utils/errors';
import type { SavedConfigDetail, SavedConfigSummary } from '@/services/configsApi';
import type { AnalysisConfig } from '@/types/domain';

export function useConfigLibraryManager() {
  const router = useRouter();
  const configManagerStore = useConfigManagerStore();
  const datasetStore = useDatasetStore();
  const { hydrateFromConfig } = useWorkspaceLifecycle();
  const { confirmDelete } = useConfirmDialog();
  const { notifyError, notifySuccess, notifyWarn } = useNotify();
  const { savedConfigs } = storeToRefs(configManagerStore);

  const listLoading = ref(false);
  const selectedLoading = ref(false);
  const selectedConfigId = ref<number | null>(null);
  const selectedDetail = ref<SavedConfigDetail | null>(null);

  const renameDialogVisible = ref(false);
  const renamingConfig = ref<SavedConfigSummary | null>(null);
  const renameName = ref('');
  const renameLoading = ref(false);

  const deleteLoadingId = ref<number | null>(null);
  let refreshInFlight = false;

  const selectedConfig = computed<AnalysisConfig | null>(() => {
    if (!selectedDetail.value?.config_data) return null;
    const raw = selectedDetail.value.config_data as Partial<AnalysisConfig>;
    return {
      version: raw.version || CONFIG_VERSION,
      name: raw.name || selectedDetail.value.name || 'Unnamed Config',
      description: raw.description || '',
      selectedColumns: raw.selectedColumns || [],
      parameters: raw.parameters || [],
      derivedColumns: raw.derivedColumns || [],
      charts: raw.charts || [],
      columnOrder: raw.columnOrder || [],
      parameterOrder: raw.parameterOrder || [],
      separators: raw.separators || [],
      separatorColor: raw.separatorColor,
      columnMetadata: raw.columnMetadata,
      matchingGroups: raw.matchingGroups || [],
      createdAt: raw.createdAt || selectedDetail.value.created_at || '',
      updatedAt: raw.updatedAt || selectedDetail.value.updated_at || '',
    };
  });

  const configDependency = computed(() =>
    selectedConfig.value ? buildConfigDependencyModel(selectedConfig.value) : null,
  );

  const selectedParamValues = computed(() => {
    const map = new Map<string, { value: number; unit: string }>();
    const metadataParams = datasetStore.metadata.parameters || {};
    const metadataUnits = datasetStore.metadata.parameterUnits || {};

    for (const [name, rawValue] of Object.entries(metadataParams)) {
      const value = Number(rawValue);
      if (!Number.isFinite(value)) continue;
      map.set(name, { value, unit: metadataUnits[name] || '' });
    }

    return map;
  });

  function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    const parsed = new Date(dateStr);
    if (Number.isNaN(parsed.getTime())) return '-';
    return parsed.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function dependencyKindLabel(kind: DependencyKind): string {
    switch (kind) {
      case 'column':
        return 'Column';
      case 'parameter':
        return 'Parameter';
      case 'derived-column':
        return 'Derived Column';
      case 'derived-parameter':
        return 'Derived Parameter';
      default:
        return 'Unknown';
    }
  }

  function dependencyChipClass(kind: DependencyKind): string {
    if (kind === 'column') return 'ui-variable-chip ui-variable-chip--info';
    if (kind === 'parameter') return 'ui-variable-chip ui-variable-chip--warn';
    if (kind === 'derived-column') return 'ui-variable-chip ui-variable-chip--success';
    if (kind === 'derived-parameter') return 'ui-variable-chip ui-variable-chip--info';
    return 'ui-variable-chip';
  }

  async function refreshConfigs(silent = false): Promise<boolean> {
    if (refreshInFlight) return false;
    refreshInFlight = true;
    if (!silent) listLoading.value = true;
    try {
      await configManagerStore.fetchAllFromBackend(undefined, { background: silent });
      return true;
    } catch (error) {
      if (!silent) {
        notifyError('Failed to load configurations', toUserMessage(error));
      }
      return false;
    } finally {
      refreshInFlight = false;
      if (!silent) listLoading.value = false;
    }
  }

  async function selectConfig(configId: number) {
    if (selectedLoading.value && selectedConfigId.value === configId) return;
    if (selectedConfigId.value === configId && selectedDetail.value?.id === configId) return;

    selectedConfigId.value = configId;
    selectedLoading.value = true;
    try {
      selectedDetail.value = await configManagerStore.loadFromBackend(configId);
    } catch (error) {
      selectedDetail.value = null;
      notifyError('Failed to load configuration details', toUserMessage(error));
    } finally {
      selectedLoading.value = false;
    }
  }

  async function handleDelete(config: SavedConfigSummary) {
    confirmDelete(config.name, async () => {
      deleteLoadingId.value = config.id;
      try {
        await configManagerStore.deleteFromBackend(config.id);
        if (selectedConfigId.value === config.id) {
          selectedConfigId.value = null;
          selectedDetail.value = null;
        }
        await refreshConfigs();
        notifySuccess('Configuration deleted', `"${config.name}" was removed.`);
      } catch (error) {
        notifyError('Failed to delete configuration', toUserMessage(error));
      } finally {
        deleteLoadingId.value = null;
      }
    });
  }

  function startRename(config: SavedConfigSummary) {
    renamingConfig.value = config;
    renameName.value = config.name;
    renameDialogVisible.value = true;
  }

  function cancelRename() {
    renameDialogVisible.value = false;
    renamingConfig.value = null;
    renameName.value = '';
  }

  async function submitRename() {
    if (!renamingConfig.value) return;
    const config = renamingConfig.value;
    const trimmed = renameName.value.trim();

    if (!trimmed) {
      notifyWarn('Name required', 'Please enter a new configuration name.');
      return;
    }

    if (trimmed === config.name) {
      cancelRename();
      return;
    }

    const duplicate = savedConfigs.value.find(
      (item) =>
        item.id !== config.id &&
        item.domain === config.domain &&
        item.name.trim().toLowerCase() === trimmed.toLowerCase(),
    );
    if (duplicate) {
      notifyWarn('Name already used', `A configuration named "${trimmed}" already exists.`);
      return;
    }

    renameLoading.value = true;

    // Step 1: Load detail and save with new name
    let savedId: number;
    try {
      const detail =
        selectedDetail.value && selectedDetail.value.id === config.id
          ? selectedDetail.value
          : await configManagerStore.loadFromBackend(config.id);

      const renamedConfig = {
        ...detail.config_data,
        name: trimmed,
        updatedAt: new Date().toISOString(),
      };

      const response = await configManagerStore.saveToBackend(trimmed, config.domain, renamedConfig);
      savedId = response.id;
    } catch (error) {
      notifyError('Failed to rename configuration', toUserMessage(error));
      renameLoading.value = false;
      return;
    }

    // Step 2: Delete old config (rollback new save on failure)
    try {
      await configManagerStore.deleteFromBackend(config.id);
    } catch (deleteError) {
      try {
        await configManagerStore.deleteFromBackend(savedId);
      } catch {
        await refreshConfigs(false);
      }
      notifyError('Rename partially failed', 'The original configuration was preserved. Please try again.');
      renameLoading.value = false;
      return;
    }

    // Step 3: Refresh and finalize
    try {
      await refreshConfigs();
      cancelRename();

      if (selectedConfigId.value === config.id) {
        await selectConfig(savedId);
      }

      notifySuccess('Configuration renamed', `"${config.name}" is now "${trimmed}".`);
    } finally {
      renameLoading.value = false;
    }
  }

  function applySelectedConfig() {
    if (!selectedConfig.value) return;

    const hasDataset = datasetStore.columnNames.length > 0;

    if (hasDataset) {
      // Dataset exists — validate config against actual columns
      const metadataParamNames = Object.keys(datasetStore.metadata.parameters || {});
      const result = validateConfig(selectedConfig.value, datasetStore.columnNames, metadataParamNames);
      configManagerStore.setValidationResult(result);

      if (result.errors.length > 0) {
        const firstError = result.errors[0]?.message || 'Configuration has invalid references.';
        notifyError('Configuration invalid', firstError);
        return;
      }
    }

    // No dataset yet or validation passed — just apply the config
    configManagerStore.setConfig(selectedConfig.value, selectedDetail.value?.id ?? null);
    hydrateFromConfig(selectedConfig.value);
    notifySuccess('Configuration loaded', `"${selectedConfig.value.name}" was applied to the current workspace.`);

    if (router.currentRoute.value.name !== 'analysis-import') {
      void router.push({ name: 'analysis-import' }).catch(() => {});
    }
  }

  return {
    savedConfigs,
    listLoading,
    selectedLoading,
    selectedConfigId,
    selectedDetail,
    selectedConfig,
    configDependency,
    selectedParamValues,
    renameDialogVisible,
    renameName,
    renameLoading,
    deleteLoadingId,
    formatDate,
    dependencyKindLabel,
    dependencyChipClass,
    refreshConfigs,
    selectConfig,
    handleDelete,
    startRename,
    cancelRename,
    submitRename,
    applySelectedConfig,
  };
}
