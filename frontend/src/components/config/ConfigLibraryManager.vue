<script setup lang="ts">
import SavedConfigsSection from '@/components/config/SavedConfigsSection.vue';
import ConfigReviewSection from '@/components/config/ConfigReviewSection.vue';
import RenameConfigDialog from '@/components/config/RenameConfigDialog.vue';
import { useConfigLibraryManager } from '@/composables/config/useConfigLibraryManager';
import { useConfigPoller } from '@/composables/config/useConfigPoller';

const vm = useConfigLibraryManager();
const {
  savedConfigs,
  listLoading,
  selectedConfigId,
  deleteLoadingId,
  selectedLoading,
  selectedConfig,
  selectedDetail,
  configDependency,
  selectedParamValues,
  renameDialogVisible,
  renameName,
  renameLoading,
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
} = vm;

useConfigPoller((silent) => refreshConfigs(silent));
</script>

<template>
  <div class="flex flex-column gap-5">
    <SavedConfigsSection
      :savedConfigs="savedConfigs"
      :listLoading="listLoading"
      :selectedConfigId="selectedConfigId"
      :deleteLoadingId="deleteLoadingId"
      :formatDate="formatDate"
      @select="selectConfig"
      @rename="startRename"
      @delete="handleDelete"
    />

    <ConfigReviewSection
      v-if="selectedConfigId || selectedLoading"
      :selectedLoading="selectedLoading"
      :selectedConfig="selectedConfig"
      :selectedDetail="selectedDetail"
      :configDependency="configDependency"
      :selectedParamValues="selectedParamValues"
      :formatDate="formatDate"
      :dependencyKindLabel="dependencyKindLabel"
      :dependencyChipClass="dependencyChipClass"
      @apply="applySelectedConfig"
    />

    <RenameConfigDialog
      :visible="renameDialogVisible"
      :renameName="renameName"
      :renameLoading="renameLoading"
      @update:visible="(value) => (renameDialogVisible = value)"
      @update:renameName="(value) => (renameName = value)"
      @cancel="cancelRename"
      @submit="submitRename"
    />
  </div>
</template>
