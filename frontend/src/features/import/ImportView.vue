<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useConfigManagerStore } from '@/stores/configManager';
import ImportUploadPanel from '@/features/import/ImportUploadPanel.vue';
import ImportDataPreviewPanel from '@/features/import/ImportDataPreviewPanel.vue';
import { useImportUpload } from '@/composables/import/useImportUpload';
import { useWorkspaceLifecycle } from '@/composables/useWorkspaceLifecycle';
import { useNotify } from '@/composables/useNotify';

const emit = defineEmits<{
  next: [];
}>();

const datasetStore = useDatasetStore();
const columnsStore = useColumnsStore();
const configManagerStore = useConfigManagerStore();
const { resetWorkspace } = useWorkspaceLifecycle();
const { notifyWarn } = useNotify();
const { isImporting, importError, hasData, filename, metadata, referenceRowUserSelected } = storeToRefs(datasetStore);
const { lastLoadedConfigName } = storeToRefs(configManagerStore);
const { selectedColumnNames } = storeToRefs(columnsStore);
const { isDragging, showConfig, configFile, fileSummary, handleUpload, onConfigFileSelect, clearConfigFile } = useImportUpload();

function isCsvFile(file: File | null | undefined): file is File {
  return !!file && /\.csv$/i.test(file.name);
}

function toggleConfig() {
  showConfig.value = !showConfig.value;
}

function deleteAppliedConfigSelection() {
  // UI reset only: keep saved config in backend.
  configManagerStore.clearLoadedConfigSelection();
  configManagerStore.clearValidation();
}

function setDragging(value: boolean) {
  isDragging.value = value;
}

async function validateAndUpload(file: File | null | undefined): Promise<void> {
  if (!isCsvFile(file)) {
    if (file) {
      notifyWarn('Invalid file', 'Please select a CSV file (.csv).');
    }
    return;
  }
  await handleUpload(file);
}

async function onFileSelect(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  try {
    await validateAndUpload(file);
  } finally {
    target.value = '';
  }
}

async function onDrop(event: DragEvent): Promise<void> {
  isDragging.value = false;
  const file = event.dataTransfer?.files[0];
  await validateAndUpload(file);
}

function handleNextClick() {
  const available = new Set(datasetStore.columns.map((col) => col.name));
  const hasInvalidSelection = selectedColumnNames.value.some((name) => !available.has(name));

  // Reinitialize when selection is empty or stale for the current dataset.
  if (selectedColumnNames.value.length === 0 || hasInvalidSelection) {
    columnsStore.initializeFromDataset(datasetStore.columns);
  }
  // Emit event to parent (AnalysisView) to advance to Columns & Params.
  emit('next');
}

function handleUploadDifferent() {
  resetWorkspace();
}
</script>

<template>
  <div class="step-shell">
    <ImportUploadPanel
      v-if="!hasData"
      :isImporting="isImporting"
      :importError="importError"
      :isDragging="isDragging"
      :showConfig="showConfig"
      :configFileName="configFile ? configFile.name : null"
      :appliedConfigName="lastLoadedConfigName"
      @fileSelect="onFileSelect"
      @drop="onDrop"
      @configFileSelect="onConfigFileSelect"
      @clearConfigFile="clearConfigFile"
      @deleteAppliedConfig="deleteAppliedConfigSelection"
      @toggleConfig="toggleConfig"
      @updateDragging="setDragging"
    />

    <ImportDataPreviewPanel
      v-else
      :filename="filename || ''"
      :fileSummary="fileSummary"
      :metadata="metadata"
      :columns="datasetStore.columns"
      :rows="datasetStore.rows"
      :referenceRowIndex="datasetStore.referenceRowIndex"
      :referenceRowUserSelected="referenceRowUserSelected"
      @uploadDifferent="handleUploadDifferent"
      @selectReferenceRow="datasetStore.setReferenceRow"
      @next="handleNextClick"
    />
  </div>
</template>
