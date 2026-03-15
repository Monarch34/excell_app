import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { uploadFile } from '@/services/datasetsApi';
import { fromJSON, validateConfig } from '@/domain/configSerializer';
import { useWorkspaceLifecycle } from '@/composables/useWorkspaceLifecycle';
import { useNotify } from '@/composables/useNotify';
import { useDatasetStore } from '@/stores/dataset';
import { useConfigManagerStore } from '@/stores/configManager';
import type { AnalysisConfig } from '@/shared/types/domain';
import { toUserMessage, logError } from '@/utils/errors';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
const CONFIG_MAX_SIZE = 5 * 1024 * 1024; // 5 MB

export function useImportUpload() {
  const datasetStore = useDatasetStore();
  const configManagerStore = useConfigManagerStore();
  const { metadata } = storeToRefs(datasetStore);
  const { notifySuccess, notifyError, notifyWarn } = useNotify();
  const { replaceDataset, replaceDatasetWithConfig } = useWorkspaceLifecycle();

  const isDragging = ref(false);
  const configFile = ref<File | null>(null);
  const showConfig = ref(false);
  let uploadVersion = 0;
  const metadataParameterNames = computed(() =>
    Object.keys(metadata.value.parameters || {})
  );

  const fileSummary = computed(() => {
    return metadata.value.rowCount > 0 ? `${metadata.value.rowCount.toLocaleString()} rows` : '';
  });

  async function handleUpload(file: File): Promise<void> {
    if (file.size > MAX_FILE_SIZE) {
      notifyError('File too large', `Maximum file size is 50 MB. Selected file is ${(file.size / (1024 * 1024)).toFixed(1)} MB.`);
      return;
    }

    datasetStore.isImporting = true;
    datasetStore.importError = null;
    const thisVersion = ++uploadVersion;

    try {
      // Step 1: Upload file
      const response = await uploadFile(file);
      if (thisVersion !== uploadVersion) return; // stale upload

      // Step 2: Parse config BEFORE any state mutation (if present)
      let parsedConfig: AnalysisConfig | null = null;
      if (configFile.value) {
        if (configFile.value.size > CONFIG_MAX_SIZE) {
          notifyError('Config file too large', 'Maximum config file size is 5 MB.');
          replaceDataset(response);
          notifySuccess('File uploaded', `"${file.name}" uploaded successfully with ${response.raw_data.length} rows`);
          return;
        }
        try {
          const json = await configFile.value.text();
          parsedConfig = fromJSON(json);
        } catch (e: unknown) {
          const userMessage = toUserMessage(e);
          logError(e, 'handleUpload:config');
          notifyError('Config error', userMessage);
          replaceDataset(response);
          notifySuccess('File uploaded', `"${file.name}" uploaded successfully with ${response.raw_data.length} rows`);
          return;
        }
      }

      // Step 3: Fall back to pre-loaded library config if no local config file
      const effectiveConfig = parsedConfig ?? configManagerStore.currentConfig;

      // Step 4: Choose ONE lifecycle action — no destroy→hydrate window
      if (effectiveConfig && applyAndValidateConfig(response, effectiveConfig)) {
        notifySuccess('File uploaded', `"${file.name}" uploaded successfully with ${response.raw_data.length} rows`);
        notifySuccess('Configuration loaded', 'Config applied successfully');
      } else {
        // No config, invalid config, or parse error — clean slate
        replaceDataset(response);
        notifySuccess('File uploaded', `"${file.name}" uploaded successfully with ${response.raw_data.length} rows`);
      }
    } catch (e: unknown) {
      const userMessage = toUserMessage(e);
      datasetStore.importError = userMessage;
      logError(e, 'handleUpload');
      notifyError('Upload failed', userMessage);
    } finally {
      datasetStore.isImporting = false;
    }
  }

  function applyAndValidateConfig(response: import('@/shared/types/api').UploadResponse, config: AnalysisConfig): boolean {
    // Validate BEFORE any state mutation using raw response data
    const columnNames = response.columns || [];
    const parameterNames = Object.keys(response.parameters || {});
    const result = validateConfig(config, columnNames, parameterNames);
    configManagerStore.setValidationResult(result);

    if (!result.valid) {
      const firstError = result.errors[0]?.message || 'Configuration has invalid references.';
      notifyError('Configuration invalid', firstError);
      return false;
    }

    // Validation passed — apply atomically (no destroy→hydrate window)
    replaceDatasetWithConfig(response, config);
    configManagerStore.setConfig(config);

    if (result.warnings.length > 0) {
      notifyWarn('Configuration warnings', `${result.warnings.length} warning(s) detected. Missing items were skipped.`);
    }

    return true;
  }

  function onConfigFileSelect(event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) configFile.value = file;
    target.value = '';
  }

  function clearConfigFile(): void {
    configFile.value = null;
  }

  return {
    isDragging,
    configFile,
    showConfig,
    fileSummary,
    handleUpload,
    onConfigFileSelect,
    clearConfigFile,
  };
}
