import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { AnalysisConfig, ValidationResult } from '@/types/domain';
import { toUserMessage, logError } from '@/utils/errors';
import { CONFIG_VERSION } from '@/constants/config';
import {
  saveConfig as apiSaveConfig,
  fetchConfigs as apiFetchConfigs,
  fetchConfig as apiFetchConfig,
  deleteConfig as apiDeleteConfig,
  type SavedConfigDetail,
  type SavedConfigSummary,
  type SaveConfigResponse,
} from '@/services/configsApi';

/**
 * Config Manager store - handles saving/loading analysis configurations.
 */
export const useConfigManagerStore = defineStore(
  'configManager',
  () => {
    const currentConfig = ref<AnalysisConfig | null>(null);
    const lastLoadedConfigName = ref<string | null>(null);
    const lastLoadedConfigId = ref<number | null>(null);
    const validationResult = ref<ValidationResult | null>(null);
    const savedConfigs = ref<SavedConfigSummary[]>([]);

    const hasConfig = computed(() => currentConfig.value !== null);
    const configVersion = computed(() => currentConfig.value?.version || CONFIG_VERSION);

    function createConfig(
      config: Omit<AnalysisConfig, 'version' | 'createdAt' | 'updatedAt'>
    ): AnalysisConfig {
      const now = new Date().toISOString();
      const fullConfig: AnalysisConfig = {
        ...config,
        version: CONFIG_VERSION,
        createdAt: now,
        updatedAt: now,
      };
      currentConfig.value = fullConfig;
      validationResult.value = null;
      return fullConfig;
    }

    function setConfig(config: AnalysisConfig, sourceConfigId: number | null = null) {
      currentConfig.value = config;
      lastLoadedConfigName.value = config.name;
      lastLoadedConfigId.value = sourceConfigId;
    }

    function setValidationResult(result: ValidationResult) {
      validationResult.value = result;
    }

    function clearValidation() {
      validationResult.value = null;
    }

    function clearLoadedConfigSelection() {
      lastLoadedConfigName.value = null;
      lastLoadedConfigId.value = null;
    }

    const isLoading = ref(false);
    const error = ref<string | null>(null);

    async function saveToBackend(
      name: string,
      domain: string | null | undefined,
      configData: AnalysisConfig
    ): Promise<SaveConfigResponse> {
      isLoading.value = true;
      error.value = null;
      try {
        return await apiSaveConfig(name, domain, configData);
      } catch (e: unknown) {
        const userMessage = toUserMessage(e);
        error.value = userMessage;
        logError(e, 'saveToBackend');
        throw e;
      } finally {
        isLoading.value = false;
      }
    }

    async function fetchAllFromBackend(
      domain?: string,
      options?: { background?: boolean }
    ): Promise<SavedConfigSummary[]> {
      const background = options?.background === true;
      if (!background) {
        isLoading.value = true;
        error.value = null;
      }
      try {
        const configs = await apiFetchConfigs(domain);
        savedConfigs.value = Array.isArray(configs) ? configs : [];
        return savedConfigs.value;
      } catch (e: unknown) {
        const userMessage = toUserMessage(e);
        if (!background) {
          error.value = userMessage;
        }
        logError(e, 'fetchAllFromBackend');
        throw e;
      } finally {
        if (!background) {
          isLoading.value = false;
        }
      }
    }

    async function loadFromBackend(id: number): Promise<SavedConfigDetail> {
      isLoading.value = true;
      error.value = null;
      try {
        return await apiFetchConfig(id);
      } catch (e: unknown) {
        const userMessage = toUserMessage(e);
        error.value = userMessage;
        logError(e, 'loadFromBackend');
        throw e;
      } finally {
        isLoading.value = false;
      }
    }

    async function deleteFromBackend(id: number) {
      isLoading.value = true;
      error.value = null;
      try {
        await apiDeleteConfig(id);
      } catch (e: unknown) {
        const userMessage = toUserMessage(e);
        error.value = userMessage;
        logError(e, 'deleteFromBackend');
        throw e;
      } finally {
        isLoading.value = false;
      }
    }

    /** Clears workspace-scoped state but preserves the saved config library. */
    function resetWorkspaceState() {
      currentConfig.value = null;
      clearLoadedConfigSelection();
      validationResult.value = null;
    }

    function reset() {
      resetWorkspaceState();
      savedConfigs.value = [];
      isLoading.value = false;
      error.value = null;
    }

    return {
      currentConfig,
      lastLoadedConfigName,
      lastLoadedConfigId,
      validationResult,
      hasConfig,
      configVersion,
      createConfig,
      setConfig,
      setValidationResult,
      clearValidation,
      clearLoadedConfigSelection,
      resetWorkspaceState,
      saveToBackend,
      fetchAllFromBackend,
      loadFromBackend,
      savedConfigs,
      isLoading,
      error,
      deleteFromBackend,
      reset,
    };
  },
  {
    persist: {
      key: 'excell-config-manager-storage',
      pick: [],
    },
  }
);
