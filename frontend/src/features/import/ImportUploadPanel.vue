<script setup lang="ts">
import { computed, ref } from 'vue';
import Button from 'primevue/button';
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import AppStatusStrip from '@/shared/components/ui/AppStatusStrip.vue';

const props = defineProps<{
  isImporting: boolean;
  importError: string | null;
  isDragging: boolean;
  showConfig: boolean;
  configFileName: string | null;
  appliedConfigName: string | null;
}>();

const emit = defineEmits<{
  fileSelect: [event: Event];
  drop: [event: DragEvent];
  configFileSelect: [event: Event];
  clearConfigFile: [];
  deleteAppliedConfig: [];
  toggleConfig: [];
  updateDragging: [value: boolean];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const configFileInput = ref<HTMLInputElement | null>(null);

const activeConfigSource = computed(() => {
  if (props.appliedConfigName) return 'Workspace';
  if (props.configFileName) return 'Local file';
  return null;
});

function triggerFileInput(): void {
  fileInput.value?.click();
}

function triggerConfigInput(): void {
  configFileInput.value?.click();
}

function deleteAppliedConfig(): void {
  emit('deleteAppliedConfig');
}
</script>

<template>
  <div class="ui-upload-shell ui-upload-shell-layout fade-in">
    <AppSurfacePanel class="ui-upload-card ui-upload-card-frame ui-upload-card--clean">
      <div class="ui-upload-content-wrap">
        <header class="ui-upload-head">
          <h2 class="ui-upload-headline">Upload CSV</h2>
          <p class="ui-upload-subtitle">Import your data file to continue with columns, formulas, and charts.</p>
        </header>

        <section class="ui-upload-section">
          <div class="ui-upload-section-head">
            <span class="ui-upload-section-title">Data file</span>
            <span class="ui-upload-section-note">CSV only</span>
          </div>

          <button
            type="button"
            class="ui-upload-drop-zone"
            :class="{ 'ui-upload-drop-zone--active': isDragging }"
            aria-label="Upload CSV file by clicking, pressing Enter, or dragging and dropping"
            @dragover.prevent="emit('updateDragging', true)"
            @dragleave.prevent="emit('updateDragging', false)"
            @drop.prevent="emit('drop', $event)"
            @click="triggerFileInput"
          >
            <input ref="fileInput" type="file" class="hidden" name="dataset_csv_file" accept=".csv" @change="emit('fileSelect', $event)" />

            <div class="ui-upload-drop-body">
              <div class="ui-upload-icon-circle" aria-hidden="true">
                <i :class="['pi', isDragging ? 'pi-arrow-down' : 'pi-cloud-upload']" aria-hidden="true"></i>
              </div>

              <div v-if="!isDragging">
                <h3 class="ui-upload-zone-title">Drag and drop your CSV</h3>
                <p class="ui-upload-zone-subtitle ui-upload-zone-subtitle-reset">
                  or <span class="ui-upload-link">browse your computer</span>
                </p>
              </div>
              <div v-else>
                <h3 class="ui-upload-zone-title ui-upload-zone-title--active">Drop to upload</h3>
                <p class="ui-upload-zone-subtitle ui-upload-zone-subtitle-reset">Release the file here</p>
              </div>

              <span class="ui-upload-choose-btn"><i class="pi pi-upload" aria-hidden="true"></i>Choose CSV File</span>
            </div>
          </button>

          <div class="ui-upload-capability-row">
            <div class="ui-muted-hint ui-upload-capability text-color-secondary text-sm">
              <i class="pi pi-file-excel ui-color-success"></i>
              <span>CSV format</span>
            </div>
            <div class="ui-muted-hint ui-upload-capability text-color-secondary text-sm">
              <i class="pi pi-database ui-color-info"></i>
              <span>Up to 50MB</span>
            </div>
          </div>
        </section>

        <section class="ui-upload-section ui-upload-section--secondary">
          <div class="ui-upload-section-head">
            <span class="ui-upload-section-title">Configuration</span>
            <span class="ui-upload-section-note">Optional</span>
          </div>

          <div class="ui-upload-config-head">
            <div class="ui-upload-config-title-wrap">
              <i class="pi pi-sliders-h text-color-secondary"></i>
              <span class="text-color-secondary text-sm font-semibold">Apply saved settings</span>
            </div>
            <Button
              :label="showConfig ? 'Hide' : 'Show'"
              :icon="showConfig ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
              size="small"
              severity="secondary"
              text
              class="ui-upload-config-toggle"
              @click="emit('toggleConfig')"
            />
          </div>
          <div v-show="showConfig" class="ui-upload-config-body">
            <p class="text-color-secondary text-sm ui-upload-config-note">
              Load a saved configuration to apply formulas and charts automatically.
            </p>
            <div v-if="activeConfigSource" class="ui-upload-config-source-row">
              <span class="ui-upload-config-source-label text-xs text-color-secondary">
                Source: {{ activeConfigSource }}
              </span>
            </div>
            <div class="ui-upload-config-actions">
              <input ref="configFileInput" type="file" class="hidden" name="upload_config_file" accept=".json" @change="emit('configFileSelect', $event)" />
              <Button
                v-if="appliedConfigName"
                :label="appliedConfigName"
                icon="pi pi-times"
                iconPos="right"
                size="small"
                severity="success"
                outlined
                class="ui-upload-config-clear-btn"
                aria-label="Clear applied configuration"
                @click="deleteAppliedConfig"
                v-tooltip.top="'Clear applied config'"
              />
              <template v-else-if="configFileName">
                <Button
                  :label="configFileName"
                  icon="pi pi-times"
                  iconPos="right"
                  size="small"
                  severity="success"
                  outlined
                  @click="emit('clearConfigFile')"
                  class="ui-upload-config-clear-btn"
                  aria-label="Clear selected config file"
                  v-tooltip.top="'Clear selected config file'"
                />
              </template>
              <Button
                v-else
                label="Browse config..."
                icon="pi pi-file"
                size="small"
                severity="secondary"
                outlined
                @click="triggerConfigInput"
              />
            </div>
          </div>
        </section>

        <div class="ui-upload-status-inline" aria-live="polite">
          <AppStatusStrip :isLoading="isImporting" :error="importError" minHeight="44px">
            <template #loading>
              <i class="pi pi-spin pi-spinner text-primary text-xl"></i>
              <div class="ui-upload-status-copy">
                <span class="font-bold text-color">Processing data</span>
                <span class="text-sm text-color-secondary">Parsing CSV file...</span>
              </div>
            </template>
            <template #error="{ error: errorMessage }">
              <i class="pi pi-exclamation-triangle ui-color-error text-xl"></i>
              <div class="ui-upload-status-copy">
                <span class="font-bold ui-color-error-strong">Upload failed</span>
                <span class="text-sm ui-color-error">{{ errorMessage }}</span>
              </div>
            </template>
            <template #idle>
              <div class="ui-upload-status-ready text-color-secondary text-sm">
                Ready to upload
              </div>
            </template>
          </AppStatusStrip>
        </div>
      </div>
    </AppSurfacePanel>
  </div>
</template>
