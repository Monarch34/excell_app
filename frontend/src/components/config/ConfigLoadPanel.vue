<script setup lang="ts">
import { ref, watch } from "vue";
import Button from "primevue/button";
import AppNotice from "@/components/ui/AppNotice.vue";
import AppSurfacePanel from "@/components/ui/AppSurfacePanel.vue";
import { useConfigManagerStore } from "@/stores/configManager";
import { storeToRefs } from "pinia";
import { useConfirmDialog } from "@/composables/useConfirmDialog";
import { useNotify } from "@/composables/useNotify";
import { useConfigPoller } from "@/composables/config/useConfigPoller";

const props = defineProps<{
  domain?: string;
}>();

const emit = defineEmits<{
  load: [json: string];
  loadById: [id: number];
}>();

const configManagerStore = useConfigManagerStore();
const { savedConfigs, lastLoadedConfigId } = storeToRefs(configManagerStore);
const { confirmDelete } = useConfirmDialog();
const { notifyError } = useNotify();
const fileInput = ref<HTMLInputElement | null>(null);
const error = ref<string | null>(null);
const listLoading = ref(false);
const deletingId = ref<number | null>(null);
const MAX_CONFIG_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

async function refreshConfigs(silent: boolean): Promise<boolean> {
  if (!silent) listLoading.value = true;
  try {
    await configManagerStore.fetchAllFromBackend(props.domain, { background: silent });
    return true;
  } catch (e) {
    if (!silent) notifyError('Failed to refresh configurations', e);
    return false;
  } finally {
    if (!silent) listLoading.value = false;
  }
}

useConfigPoller(refreshConfigs);

watch(
  () => props.domain,
  () => {
    void refreshConfigs(false);
  }
);

function triggerFileInput() {
  fileInput.value?.click();
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  target.value = '';

  error.value = null;

  if (file.size > MAX_CONFIG_FILE_SIZE) {
    error.value = `Config file too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 5 MB.`;
    return;
  }

  try {
    const text = await file.text();
    emit("load", text);
  } catch {
    error.value = "Failed to read config file";
  }
}

async function handleDelete(id: number, name: string) {
  confirmDelete(name, async () => {
    deletingId.value = id;
    try {
      await configManagerStore.deleteFromBackend(id);
      await refreshConfigs(false);
    } catch (e) {
      notifyError('Delete failed', e);
    } finally {
      deletingId.value = null;
    }
  });
}
</script>

<template>
  <AppSurfacePanel class="config-load-panel ui-config-panel">
    <div class="ui-config-panel-head ui-config-load-head">
      <i class="pi pi-upload ui-color-info" aria-hidden="true"></i>
      <span class="font-bold text-color">Load Configuration</span>
    </div>

    <div class="ui-config-load-list-block">
      <div class="ui-config-list-head ui-config-load-list-head">
        <span class="text-sm font-semibold text-color-secondary"
          >Saved in Workspace</span
        >
      </div>

      <div v-if="listLoading" class="ui-config-load-loading">
        <i class="pi pi-spinner pi-spin ui-color-info"></i>
        <span class="ui-config-load-loading-text text-sm text-color-secondary"
          >Loading configurations...</span
        >
      </div>

      <AppNotice
        v-else-if="savedConfigs.length === 0"
        severity="info"
        class="ui-config-load-empty text-sm italic text-color-secondary"
      >
        No configurations saved yet.
      </AppNotice>

      <div v-else class="ui-config-list ui-config-load-list-scroll">
        <div
          v-for="cfg in savedConfigs"
          :key="cfg.id"
          :class="[
            'ui-select-item ui-config-list-item ui-config-list-item-row transition-colors',
            cfg.id === lastLoadedConfigId ? 'ui-select-item--selected' : '',
          ]"
        >
          <button
            type="button"
            class="ui-config-list-item-trigger"
            :aria-label="`Load configuration ${cfg.name}`"
            @click="emit('loadById', cfg.id)"
          >
            <div class="ui-config-list-item-main">
              <i class="pi pi-file ui-color-info" aria-hidden="true"></i>
              <div class="ui-config-list-item-text">
                <span class="text-sm font-medium">{{ cfg.name }}</span>
                <span class="text-xs text-color-secondary">{{
                  new Date(cfg.updated_at).toLocaleDateString()
                }}</span>
              </div>
            </div>
          </button>
          <Button
            icon="pi pi-trash"
            severity="danger"
            text
            size="small"
            class="ui-action-icon-btn ui-delete-btn"
            :loading="deletingId === cfg.id"
            :aria-label="`Delete configuration ${cfg.name}`"
            @click="handleDelete(cfg.id, cfg.name)"
            v-tooltip.left="'Delete from workspace'"
          />
        </div>
      </div>
    </div>

    <div class="ui-config-load-divider-row">
      <div class="ui-config-load-divider-line ui-divider-line"></div>
      <span
        class="ui-config-load-divider-label ui-config-load-divider-label-text text-xs text-color-secondary uppercase"
        >or upload file</span
      >
      <div class="ui-config-load-divider-line ui-divider-line"></div>
    </div>

    <input
      type="file"
      ref="fileInput"
      class="hidden"
      name="config_file"
      accept=".json"
      @change="handleFileSelect"
    />

    <Button
      label="Browse Local File"
      icon="pi pi-folder-open"
      severity="secondary"
      outlined
      aria-label="Browse local configuration file"
      @click="triggerFileInput"
      class="ui-config-load-browse-btn"
    />

    <AppNotice
      v-if="error"
      severity="error"
      class="ui-config-load-error ui-color-error text-sm"
    >
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      <span>{{ error }}</span>
    </AppNotice>
  </AppSurfacePanel>
</template>
