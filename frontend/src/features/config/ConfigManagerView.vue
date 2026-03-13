<script setup lang="ts">
import { computed, ref } from 'vue';
import { useDatasetStore } from '@/stores/dataset';
import { useConfigManagerStore } from '@/stores/configManager';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useParametersStore } from '@/stores/parameters';
import { useChartsStore } from '@/stores/charts';
import { storeToRefs } from 'pinia';
import type { DerivedColumnDef } from '@/shared/types/domain';
import { normalizeFilenameCandidate, useConfigExportReport } from '@/composables/config/useConfigExportReport';
import { useConfigManagerStep } from '@/composables/config/useConfigManagerStep';
import { DEFAULT_EXPORT_FILENAME } from '@/constants/config';
import ConfigSavePanel from '@/features/config/ConfigSavePanel.vue';
import ConfigValidationReport from '@/features/config/ConfigValidationReport.vue';
import AppPageHeader from '@/shared/components/ui/AppPageHeader.vue';
import AppStepSection from '@/shared/components/ui/AppStepSection.vue';
import AppField from '@/shared/components/ui/AppField.vue';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';

const props = withDefaults(
  defineProps<{
    standalone?: boolean;
  }>(),
  {
    standalone: false,
  }
);

const datasetStore = useDatasetStore();
const configManagerStore = useConfigManagerStore();
const derivedStore = useDerivedColumnsStore();
const parametersStore = useParametersStore();
const chartsStore = useChartsStore();

const { validationResult, lastLoadedConfigName } = storeToRefs(configManagerStore);
const { customFilename, exportLoading, exportError, handleExport: doExport } = useConfigExportReport();
const configStep = useConfigManagerStep();
const exportFilenameTouched = ref(false);
const canExport = computed(() => datasetStore.hasData);
const headerTitle = computed(() => (props.standalone ? 'Configurations' : 'Export'));
const headerIcon = computed(() => (props.standalone ? 'pi-cog' : 'pi-download'));
const introText = computed(() =>
  props.standalone
    ? 'Save reusable analysis configurations and export report files for the current dataset.'
    : 'Export your finalized report and save this analysis configuration for reuse.'
);

const liveConfigCounts = computed(() => ({
  derivedColumns: derivedStore.derivedColumns.filter((c: DerivedColumnDef) => c.type === 'column').length,
  parameters: parametersStore.allParameters.length + derivedStore.derivedColumns.filter((c: DerivedColumnDef) => c.type === 'parameter').length,
  charts: chartsStore.charts.length,
}));

const normalizedExportFilename = computed(() => normalizeFilenameCandidate(customFilename.value));
const exportFilenameError = computed(() => {
  if (!exportFilenameTouched.value) return undefined;
  if (!customFilename.value.trim()) return 'Report filename is required';
  if (!normalizedExportFilename.value) return 'Report filename must include letters or numbers';
  return undefined;
});
const isExportFilenameInvalid = computed(() => !!exportFilenameError.value);
const canGenerateExport = computed(() => (
  canExport.value
  && customFilename.value.trim().length > 0
  && !isExportFilenameInvalid.value
));

function markExportFilenameTouched(): void {
  exportFilenameTouched.value = true;
}

function handleExportFilenameChange(value: string | number | undefined | null): void {
  markExportFilenameTouched();
  customFilename.value = String(value || '');
}

function handleExport(): void {
  markExportFilenameTouched();
  if (isExportFilenameInvalid.value) return;
  void doExport();
}
</script>

<template>
  <div class="step-shell ui-export-page">
    <AppPageHeader :icon="headerIcon" :title="headerTitle" />
    <div class="ui-muted-hint ui-step-intro ui-config-intro text-sm text-color-secondary">
      {{ introText }}
    </div>

    <div class="ui-stat-row ui-stat-row--compact">
      <div class="ui-stat-card ui-stat-card--compact">
        <div class="ui-stat-card-top">
          <div class="ui-stat-card-info">
            <span class="ui-stat-card-label">Derived Columns</span>
            <div class="ui-stat-card-value">{{ liveConfigCounts.derivedColumns }}</div>
          </div>
          <div class="ui-stat-icon ui-stat-icon--blue">
            <i class="pi pi-table"></i>
          </div>
        </div>
        <div class="ui-stat-card-footer">
          <span class="ui-stat-status">Active</span>
          <span class="ui-stat-desc">computations processing data</span>
        </div>
      </div>

      <div class="ui-stat-card ui-stat-card--compact">
        <div class="ui-stat-card-top">
          <div class="ui-stat-card-info">
            <span class="ui-stat-card-label">Parameters</span>
            <div class="ui-stat-card-value">{{ liveConfigCounts.parameters }}</div>
          </div>
          <div class="ui-stat-icon ui-stat-icon--orange">
            <i class="pi pi-sliders-v"></i>
          </div>
        </div>
        <div class="ui-stat-card-footer">
          <span class="ui-stat-status">Active</span>
          <span class="ui-stat-desc">settings influencing logic</span>
        </div>
      </div>

      <div class="ui-stat-card ui-stat-card--compact">
        <div class="ui-stat-card-top">
          <div class="ui-stat-card-info">
            <span class="ui-stat-card-label">Charts</span>
            <div class="ui-stat-card-value">{{ liveConfigCounts.charts }}</div>
          </div>
          <div class="ui-stat-icon ui-stat-icon--purple">
            <i class="pi pi-chart-bar"></i>
          </div>
        </div>
        <div class="ui-stat-card-footer">
          <span class="ui-stat-status">Ready</span>
          <span class="ui-stat-desc">to be rendered in export</span>
        </div>
      </div>
    </div>

    <AppStepSection
      class="ui-config-export-section max-w-full"
      icon="pi-file-excel"
      title="Finalize & Export"
    >
      <div class="ui-export-compact">
        <p class="ui-muted-hint text-sm text-color-secondary ui-export-card-intro">
          Export the current analysis as an XLSX report.
        </p>

        <div class="ui-export-actions">
          <AppField
            label="Report Filename"
            :uppercase="false"
            htmlFor="export-filename"
            class="ui-export-field"
            :required="true"
            :error="exportFilenameError"
          >
            <InputText
              id="export-filename"
              :modelValue="customFilename"
              class="w-full"
              :class="{ 'p-invalid': isExportFilenameInvalid }"
              name="export_filename"
              :placeholder="DEFAULT_EXPORT_FILENAME"
              @update:modelValue="handleExportFilenameChange"
              @blur="markExportFilenameTouched"
            />
          </AppField>

          <Button
            label="Generate Export File"
            icon="pi pi-download"
            severity="primary"
            class="ui-export-submit-btn"
            :disabled="!canGenerateExport"
            :loading="exportLoading"
            @click="handleExport"
          />
        </div>

        <div v-if="!canExport" class="ui-muted-hint text-sm text-color-secondary ui-export-status-note">
          <i class="pi pi-info-circle mr-1"></i> Import a dataset first to enable export
        </div>
        <div
          v-if="exportError"
          class="ui-config-inline-error ui-config-inline-error--spaced ui-config-inline-error-row ui-color-error ui-export-status-note"
        >
          <i class="pi pi-times-circle"></i>
          <span class="text-sm">{{ exportError }}</span>
        </div>
      </div>
    </AppStepSection>

    <ConfigSavePanel
      :defaultName="configStep.defaultConfigName.value"
      @save="configStep.handleSave"
      @saveToDb="configStep.handleSaveToDb"
      :dbLoading="configManagerStore.isLoading"
    />

    <AppStepSection
      icon="pi-check-circle"
      title="Setup Status"
      class="ui-config-validation-section"
    >
      <ConfigValidationReport
        v-if="validationResult"
        :result="validationResult"
        :configName="lastLoadedConfigName || 'Unknown'"
        :counts="liveConfigCounts"
        class="ui-config-validation-wrap shadow-none"
      />
      <div v-else class="ui-export-empty-state">
        <i class="pi pi-check-circle ui-export-empty-icon" aria-hidden="true"></i>
        <p class="ui-export-empty-text">
          Load a configuration or run validation to see export readiness details here.
        </p>
      </div>
    </AppStepSection>
  </div>
</template>
