<script setup lang="ts">
import { computed } from 'vue';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { storeToRefs } from 'pinia';
import ColumnToggleList from '@/features/columns/ColumnToggleList.vue';
import ParameterForm from '@/features/params/ParameterForm.vue';
import AppStepSection from '@/shared/components/ui/AppStepSection.vue';
import AppNotice from '@/shared/components/ui/AppNotice.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
const datasetStore = useDatasetStore();
const columnsStore = useColumnsStore();
const parametersStore = useParametersStore();

const { columns, columnNames, metadata } = storeToRefs(datasetStore);
const { selectedColumnNames } = storeToRefs(columnsStore);
const { userParameters, isValid, hasDuplicateNames, duplicateNames } = storeToRefs(parametersStore);
const metadataParameterCount = computed(() => Object.keys(metadata.value.parameters || {}).length);
const userParameterCount = computed(() => userParameters.value.length);

const hasNumericSelected = computed(() => {
  return columns.value
    .filter((c) => selectedColumnNames.value.includes(c.name))
    .some((c) => c.type === 'numeric');
});

const columnValidationMessage = computed(() => {
  if (selectedColumnNames.value.length === 0) return 'Select at least one column';
  if (!hasNumericSelected.value) return 'At least one numeric column required';
  return null;
});

const parameterValidationMessage = computed(() => {
  if (hasDuplicateNames.value) {
    const preview = duplicateNames.value.slice(0, 3).join(', ');
    return `Parameter names must be unique: ${preview}`;
  }
  if (!isValid.value) return 'All parameters must have valid numeric values';
  return null;
});


</script>

<template>
  <div class="step-shell">
    <div class="ui-columns-params-stack">
      <!-- Column Selection & Mapping -->
      <div class="ui-columns-params-col">
        <AppStepSection icon="pi-table" title="Select Columns" class="ui-columns-params-panel">
          <div class="ui-columns-params-panel-body">
            <ColumnToggleList
              :columns="columns"
              :selectedNames="selectedColumnNames"
              @toggle="columnsStore.toggleColumn"
              @selectAll="() => columnsStore.selectAll(columnNames)"
              @deselectAll="columnsStore.deselectAll"
            />

            <AppNotice
              v-if="columnValidationMessage"
              severity="warn"
              class="ui-columns-params-validation"
            >
              <div class="ui-columns-params-validation-row ui-color-warning">
                <i class="pi pi-exclamation-triangle"></i>
                <span class="text-sm font-semibold">{{ columnValidationMessage }}</span>
              </div>
            </AppNotice>
          </div>
        </AppStepSection>
      </div>

      <!-- Parameters -->
      <div class="ui-columns-params-col">
        <AppStepSection icon="pi-cog" title="Parameters" class="ui-columns-params-panel">
          <template #action>
            <Tag
              v-if="metadataParameterCount > 0"
              :value="`${metadataParameterCount} Metadata`"
              severity="warn"
              class="text-xs"
            />
            <Tag
              v-if="userParameterCount > 0"
              :value="`${userParameterCount} User`"
              severity="info"
              class="text-xs"
            />
            <Button
              label="Add Parameter"
              icon="pi pi-plus"
              size="small"
              severity="secondary"
              outlined
              @click="parametersStore.addParameter()"
            />
          </template>
          <div class="ui-columns-params-panel-body ui-columns-params-panel-body--params">
            <p class="ui-columns-params-intro text-sm text-color-secondary">
              Manage dataset metadata parameters and user-defined parameters in one place.
            </p>

            <AppNotice
              v-if="parameterValidationMessage"
              severity="warn"
              class="ui-columns-params-validation"
            >
              <div class="ui-columns-params-validation-row ui-color-warning">
                <i class="pi pi-exclamation-triangle"></i>
                <span class="text-sm font-semibold">{{ parameterValidationMessage }}</span>
              </div>
            </AppNotice>

            <ParameterForm
              :metadataParameters="metadata.parameters || {}"
              :metadataParameterUnits="metadata.parameterUnits || {}"
              :userParameters="userParameters"
              @updateParameter="parametersStore.updateParameter"
              @removeParameter="parametersStore.removeParameter"
            />
          </div>
        </AppStepSection>
      </div>
    </div>
  </div>
</template>

