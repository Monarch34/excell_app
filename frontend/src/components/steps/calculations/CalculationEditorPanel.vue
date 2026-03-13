<script setup lang="ts">
import { computed, ref } from 'vue';
import type { DerivedColumnDef } from '@/types/domain';
import VariablePalette from '@/components/formulas/VariablePalette.vue';
import FormulaEditor from '@/components/formulas/FormulaEditor.vue';
import AppPageHeader from '@/components/ui/AppPageHeader.vue';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';
import { useNumberFormat } from '@/composables/useNumberFormat';
import Tag from 'primevue/tag';

const props = defineProps<{
  activeColumn: DerivedColumnDef | null;
  columnNames: string[];
  metadataParameterNames: string[];
  userParameterNames: string[];
  derivedParameterNames: string[];
  derivedColumnNames: string[];
  referenceRowIndex: number | null;
  previewLoading: boolean;
  previewValues: number[];
  previewError: string | null;
  errorIcon: string;
  errorHint: string;
}>();

const emit = defineEmits<{
  update: [columnId: string, updates: Partial<DerivedColumnDef>];
  preview: [formulaOverride?: string];
}>();

const formulaEditorRef = ref<InstanceType<typeof FormulaEditor> | null>(null);
const { formatValue } = useNumberFormat('fixed');

const previewVisible = computed(() => {
  return props.previewLoading || props.previewValues.length > 0 || !!props.previewError;
});

function handleInsertVariable(varName: string) {
  formulaEditorRef.value?.insertReference(varName);
}

function handleInsertRefVariable(varName: string) {
  formulaEditorRef.value?.insertText(`REF([${varName}])`);
}
</script>

<template>
  <div v-if="activeColumn" class="ui-calc-right-panel">
    <AppSurfacePanel class="ui-calc-section ui-calc-editor-card">
      <AppPageHeader icon="pi-code" title="Formula Editor" class="ui-calc-editor-header" />

      <div class="ui-calc-block">
        <div class="ui-section-label">Variables</div>
        <VariablePalette
          :columns="columnNames"
          :metadataParameters="metadataParameterNames"
          :parameters="userParameterNames"
          :derivedParameters="derivedParameterNames"
          :derivedColumnNames="derivedColumnNames"
          :referenceRowIndex="referenceRowIndex"
          @insert="handleInsertVariable"
          @insertRef="handleInsertRefVariable"
        />
      </div>

      <FormulaEditor
        ref="formulaEditorRef"
        :column="activeColumn"
        :previewLoading="previewLoading"
        :availableColumns="[...columnNames, ...derivedColumnNames]"
        :availableParameters="[...metadataParameterNames, ...userParameterNames, ...derivedParameterNames]"
        @update="(columnId, updates) => emit('update', columnId, updates)"
        @preview="emit('preview', $event)"
      />
    </AppSurfacePanel>

    <AppSurfacePanel class="ui-calc-section ui-calc-preview-panel" :class="{ 'ui-calc-preview-hidden': !previewVisible }">
      <div class="ui-section-label">Preview</div>
      <div v-if="previewLoading" class="ui-calc-preview-spinner text-color-secondary">
        <i class="pi pi-spin pi-spinner"></i>
      </div>
      <div class="ui-calc-preview-content" :class="{ 'ui-calc-preview-content-hidden': previewLoading }">
        <div v-if="previewError" class="ui-calc-preview-error">
          <div class="ui-calc-preview-error-row ui-color-error">
            <i :class="errorIcon"></i>
            <span class="text-sm">{{ previewError }}</span>
          </div>
          <div v-if="errorHint" class="text-xs text-color-secondary ui-calc-preview-hint">
            <i class="pi pi-info-circle ui-calc-preview-hint-icon"></i>{{ errorHint }}
          </div>
        </div>
        <div v-else>
          <span class="text-color-secondary text-sm font-semibold ui-calc-preview-heading">Preview (first {{ previewValues.length }} values):</span>
          <div class="ui-calc-preview-tags">
            <Tag
              v-for="(val, i) in previewValues"
              :key="i"
              :value="formatValue(val)"
              severity="info"
              class="text-xs"
            />
          </div>
        </div>
      </div>
    </AppSurfacePanel>
  </div>

  <div v-else class="flex flex-column align-items-center justify-content-center ui-calc-empty-editor">
    <i class="pi pi-calculator text-4xl text-color-secondary ui-calc-empty-icon"></i>
    <span class="text-color-secondary">Select or create a derived item to edit</span>
  </div>
</template>
