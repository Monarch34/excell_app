<script setup lang="ts">
// TODO: Unsaved formula edits are lost on navigation. To fix:
//  1. Wire `useDirtyState` composable here
//  2. Expose `isDirty` from FormulaEditor
//  3. Add `onBeforeRouteLeave` guard that prompts when dirty
import { ref, computed, watch } from 'vue';
import { useDatasetStore } from '@/stores/dataset';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useParametersStore } from '@/stores/parameters';
import { useConfigManagerStore } from '@/stores/configManager';
import { buildHeaderMappingFromConfig } from '@/utils/headerMapping';
import { storeToRefs } from 'pinia';
import { previewFormula } from '@/services/formulasApi';
import { extractErrorMessage } from '@/services/httpClient';
import type { FormulaPreviewErrorCode } from '@/shared/types/api';
import CalculationItemsPanel from '@/features/calculations/CalculationItemsPanel.vue';
import CalculationEditorPanel from '@/features/calculations/CalculationEditorPanel.vue';

const datasetStore = useDatasetStore();
const derivedStore = useDerivedColumnsStore();
const parametersStore = useParametersStore();
const configManagerStore = useConfigManagerStore();
const { columnNames, metadata } = storeToRefs(datasetStore);
const { derivedColumns, activeColumn, canAdd } = storeToRefs(derivedStore);
const { allParameters, parameterMap } = storeToRefs(parametersStore);

const previewValues = ref<number[]>([]);
const previewError = ref<string | null>(null);
const previewErrorCode = ref<FormulaPreviewErrorCode | null>(null);
const previewLoading = ref(false);
let previewVersion = 0;

const metadataParameterNames = computed(() => Object.keys(metadata.value.parameters || {}));
const userParameterNames = computed(() => allParameters.value.map((p) => p.name));
const derivedParameterNames = computed(() => derivedColumns.value.filter(d => d.type === 'parameter').map(p => p.name));
const derivedColumnNames = computed(() => derivedColumns.value.filter(d => d.type !== 'parameter').map(c => c.name));

// Split derived items into parameters and columns
const parametersList = computed(() => derivedColumns.value.filter(d => d.type === 'parameter'));
const columnsList = computed(() => derivedColumns.value.filter(d => d.type !== 'parameter'));
const isLeftEmpty = computed(() => parametersList.value.length === 0 && columnsList.value.length === 0);

watch(
  () => activeColumn.value?.id,
  () => {
    previewValues.value = [];
    previewError.value = null;
    previewErrorCode.value = null;
  }
);

async function handlePreview(formulaOverride?: string) {
  if (!activeColumn.value) return;
  const formula = formulaOverride || activeColumn.value.formula;
  if (!formula || formula.trim().length === 0) return;

  previewLoading.value = true;
  previewError.value = null;
  previewErrorCode.value = null;
  const thisPreview = ++previewVersion;

  try {
    const headerMapping = buildHeaderMappingFromConfig(configManagerStore.currentConfig);

    // Collect other derived items as context for the backend to evaluate first
    const userFormulas = derivedColumns.value
      .filter(d => d.id !== activeColumn.value?.id && d.enabled && d.formula && d.type !== 'parameter')
      .map(d => ({ name: d.name, formula: d.formula, description: d.description || '', unit: d.unit || '', enabled: true }));

    const derivedParameters = derivedColumns.value
      .filter(d => d.id !== activeColumn.value?.id && d.enabled && d.formula && d.type === 'parameter')
      .map(d => ({ name: d.name, formula: d.formula }));

    const target_type = activeColumn.value.type === 'parameter' ? 'parameter' : 'column';

    if (!datasetStore.datasetId) {
      throw new Error('Dataset session is missing. Please re-upload your file.');
    }

    if (datasetStore.referenceRowIndex === null) {
      console.warn('referenceRowIndex is null; defaulting to 0 for preview');
    }
    const refIndex = datasetStore.referenceRowIndex ?? 0;
    const result = await previewFormula({
      dataset_id: datasetStore.datasetId,
      formula,
      target_type,
      sample_start: refIndex,
      sample_size: 50,
      parameters: { ...(metadata.value.parameters || {}), ...parameterMap.value },
      reference_index: refIndex,
      header_mapping: headerMapping,
      derived_parameters: derivedParameters,
      user_formulas: userFormulas,
    });

    if (thisPreview !== previewVersion) return; // stale preview
    if (result.success) {
      previewValues.value = result.values;
    } else {
      previewError.value = result.error || 'Preview failed';
      previewErrorCode.value = result.errorCode ?? 'generic';
    }
  } catch (e: unknown) {
    const message = extractErrorMessage(e);
    previewError.value = message || 'Preview request failed';
    previewErrorCode.value = message.includes('Dataset session expired') ? 'dataset_expired' : 'generic';
  } finally {
    previewLoading.value = false;
  }
}

type ErrorType = 'division' | 'variable' | 'syntax' | 'dataset_expired' | 'generic';

const errorType = computed<ErrorType | null>(() => {
  if (!previewError.value) return null;
  return previewErrorCode.value ?? 'generic';
});

const errorIcon = computed(() => {
  switch (errorType.value) {
    case 'division': return 'pi pi-percentage';
    case 'variable': return 'pi pi-question-circle';
    case 'syntax': return 'pi pi-code';
    case 'dataset_expired': return 'pi pi-history';
    default: return 'pi pi-times-circle';
  }
});

const errorHint = computed(() => {
  switch (errorType.value) {
    case 'division': return 'Check that your denominator is never zero';
    case 'variable': return 'Make sure column/parameter names match exactly (use the palette above)';
    case 'syntax': return 'Check for missing operators, brackets, or parentheses';
    case 'dataset_expired': return 'Re-upload your CSV to start a fresh dataset session.';
    default: return '';
  }
});

function handleAddColumn() {
  derivedStore.addColumn({ type: 'column' });
}

function handleAddParameter() {
  derivedStore.addColumn({ type: 'parameter', name: 'New_Param' });
}

function handleRemoveColumn(id: string) {
  derivedStore.removeColumn(id);
  previewValues.value = [];
  previewError.value = null;
  previewErrorCode.value = null;
}
</script>

<template>
  <div class="ui-calculations-view step-shell">
    <div class="grid" :class="{ 'ui-calc-grid-center-left': isLeftEmpty }">
      <!-- LEFT SIDE: LISTS -->
      <div class="col-12 lg:col-4 ui-calc-left-panel">
        <CalculationItemsPanel
          title="Derived Parameters"
          headerIcon="pi-sliders-h"
          itemIcon="pi pi-cog"
          :items="parametersList"
          :activeId="activeColumn?.id || null"
          :canAdd="canAdd"
          :maxItems="derivedStore.maxDerivedColumns"
          emptyMessage="No derived parameters."
          countLabel="parameters"
          :addTooltip="canAdd ? 'Add parameter' : `Max ${derivedStore.maxDerivedColumns} derived items`"
          tagSeverity="info"
          @add="handleAddParameter"
          @select="derivedStore.setActiveColumn"
          @toggle="derivedStore.toggleEnabled"
          @remove="handleRemoveColumn"
        />

        <CalculationItemsPanel
          title="Derived Columns"
          headerIcon="pi-list"
          itemIcon="pi pi-calculator"
          :items="columnsList"
          :activeId="activeColumn?.id || null"
          :canAdd="canAdd"
          :maxItems="derivedStore.maxDerivedColumns"
          emptyMessage="No derived columns yet."
          countLabel="columns"
          :addTooltip="canAdd ? 'Add column' : `Max ${derivedStore.maxDerivedColumns} columns`"
          tagSeverity="warn"
          @add="handleAddColumn"
          @select="derivedStore.setActiveColumn"
          @toggle="derivedStore.toggleEnabled"
          @remove="handleRemoveColumn"
        />
      </div>

      <!-- RIGHT SIDE: EDITOR -->
      <div class="col-12 lg:col-8 ui-calc-right-shell" :class="{ 'ui-calc-right-collapsed': isLeftEmpty }">
        <CalculationEditorPanel
          :activeColumn="activeColumn"
          :columnNames="columnNames"
          :metadataParameterNames="metadataParameterNames"
          :userParameterNames="userParameterNames"
          :derivedParameterNames="derivedParameterNames"
          :derivedColumnNames="derivedColumnNames"
          :referenceRowIndex="datasetStore.referenceRowIndex"
          :previewLoading="previewLoading"
          :previewValues="previewValues"
          :previewError="previewError"
          :errorIcon="errorIcon"
          :errorHint="errorHint"
          @update="(columnId, updates) => derivedStore.updateColumn(columnId, updates)"
          @preview="handlePreview"
        />
      </div>
    </div>
  </div>
</template>
