<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import TokenFormulaEditor from '@/features/formulas/TokenFormulaEditor.vue';
import AppTooltip from '@/shared/components/ui/AppTooltip.vue';
import AppField from '@/shared/components/ui/AppField.vue';
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import { parseFormulaToTokens, serializeTokensToFormula } from '@/domain/formulaTokenizer';
import { TOOLTIPS } from '@/constants/tooltips';
import type { DerivedColumnDef, FormulaToken } from '@/shared/types/domain';
import { validateFormula } from '@/services/formulasApi';

const props = defineProps<{
  column: DerivedColumnDef;
  previewLoading: boolean;
  availableColumns?: string[];
  availableParameters?: string[];
}>();

const emit = defineEmits<{
  update: [columnId: string, updates: Partial<DerivedColumnDef>];
  preview: [formula: string];
}>();

const tokens = ref<FormulaToken[]>(parseFormulaToTokens(props.column.formula));
const draftName = ref(props.column.name);
const draftUnit = ref(props.column.unit);
const draftDescription = ref(props.column.description);
const nameTouched = ref(false);

watch(
  () => [props.column.id, props.column.name, props.column.unit, props.column.description, props.column.formula] as const,
  ([, name, unit, description, formula]) => {
    draftName.value = name;
    draftUnit.value = unit;
    draftDescription.value = description;
    tokens.value = parseFormulaToTokens(formula);
    nameTouched.value = false;
  },
);

function handleTokensUpdate(newTokens: FormulaToken[]) {
  tokens.value = newTokens;
}

const operators = [
  { label: '+', value: '+' },
  { label: '-', value: '-' },
  { label: '*', value: '*' },
  { label: '/', value: '/' },
  { label: '^', value: '^' },
  { label: ',', value: ',' },
  { label: '(', value: '(' },
  { label: ')', value: ')' },
];

const formulaFunctions = [
  { label: 'ABS', value: 'ABS' },
  { label: 'SQRT', value: 'SQRT' },
  { label: 'LOG', value: 'LOG' },
  { label: 'LOG10', value: 'LOG10' },
  { label: 'EXP', value: 'EXP' },
  { label: 'ROUND', value: 'ROUND' },
  { label: 'FLOOR', value: 'FLOOR' },
  { label: 'CEIL', value: 'CEIL' },
  { label: 'POW', value: 'POW' },
  { label: 'MIN', value: 'MIN' },
  { label: 'MAX', value: 'MAX' },
  { label: 'SUM', value: 'SUM' },
  { label: 'AVERAGE', value: 'AVERAGE' },
  { label: 'MEAN', value: 'MEAN' },
  { label: 'MEDIAN', value: 'MEDIAN' },
  { label: 'COUNT', value: 'COUNT' },
  { label: 'STDEV', value: 'STDEV' },
  { label: 'COMPLIMENT', value: 'COMPLIMENT' },
];

function insertOperator(op: string) {
  tokens.value = [...tokens.value, { type: 'operator', value: op }];
}

function insertFunction(fn: string) {
  tokens.value = [...tokens.value, { type: 'operator', value: `${fn}(` }];
}

function insertReference(varName: string) {
  tokens.value = [...tokens.value, { type: 'reference', value: varName }];
}

function insertText(text: string) {
  // Insert raw text as a reference token (for REF([Column]) syntax)
  tokens.value = [...tokens.value, { type: 'reference', value: text, raw: true }];
}

defineExpose({ insertReference, insertText });

function handleNameChange(value: string | undefined) {
  nameTouched.value = true;
  draftName.value = value ?? '';
}

function handleUnitChange(value: string | undefined) {
  draftUnit.value = value ?? '';
}

function handleDescriptionChange(value: string | undefined) {
  draftDescription.value = value ?? '';
}

const draftFormula = computed(() => serializeTokensToFormula(tokens.value));
const canPreview = computed(() => draftFormula.value.trim().length > 0);

const isDirty = computed(() => {
  return (
    draftName.value !== props.column.name ||
    draftUnit.value !== props.column.unit ||
    draftDescription.value !== props.column.description ||
    draftFormula.value !== props.column.formula
  );
});


async function validateBeforeSave(): Promise<boolean> {
  if (!canPreview.value) {
    validationErrors.value = [];
    return true;
  }

  isValidating.value = true;
  try {
    const res = await validateFormula({
      formula: draftFormula.value,
      available_columns: props.availableColumns ?? [],
      available_parameters: props.availableParameters ?? [],
    });
    validationErrors.value = res.errors;
    return res.errors.length === 0;
  } catch (err) {
    validationErrors.value = ['Validation service unavailable'];
    return false;
  } finally {
    isValidating.value = false;
  }
}

const nameError = computed(() => {
  if (!nameTouched.value) return undefined;
  if (!draftName.value.trim()) return 'Name is required';
  return undefined;
});

async function handleSave() {
  nameTouched.value = true;
  if (!draftName.value.trim()) {
    return;
  }
  const isValid = await validateBeforeSave();
  if (!isValid) return;

  emit(
    'update',
    props.column.id,
    {
      name: draftName.value,
      unit: draftUnit.value,
      description: draftDescription.value,
      formula: draftFormula.value,
    }
  );
}

const validationErrors = ref<string[]>([]);
const isValidating = ref(false);

// Only trigger preview explicitly on button click now
function handlePreviewClick() {
  if (!canPreview.value) return;
  emit('preview', draftFormula.value);
}

watch(
  () => draftFormula.value,
  () => {
    if (validationErrors.value.length > 0) {
      validationErrors.value = [];
    }
  }
);
</script>

<template>
  <div class="ui-formula-editor">
    <AppSurfacePanel compact class="ui-formula-meta-card">
      <div class="ui-formula-fields-grid ui-formula-fields-grid--meta">
        <div class="ui-formula-meta-field">
          <AppField
            label="Column Name"
            :uppercase="false"
            :htmlFor="`formula-column-name-${props.column.id}`"
            class="ui-formula-field"
            :required="true"
            :error="nameError"
          >
            <InputText
              :id="`formula-column-name-${props.column.id}`"
              :name="`formula_column_name_${props.column.id}`"
              :modelValue="draftName"
              @update:modelValue="handleNameChange"
              @blur="nameTouched = true"
              class="w-full"
              :class="{ 'p-invalid': !!nameError }"
              placeholder="Enter column name"
            />
          </AppField>
        </div>
        <div class="ui-formula-meta-field">
          <AppField label="Unit (optional)" :uppercase="false" :htmlFor="`formula-column-unit-${props.column.id}`" class="ui-formula-field">
            <InputText
              :id="`formula-column-unit-${props.column.id}`"
              :name="`formula_column_unit_${props.column.id}`"
              :modelValue="draftUnit"
              @update:modelValue="handleUnitChange"
              class="w-full"
              placeholder="e.g., MPa"
            />
          </AppField>
        </div>
        <div class="ui-formula-meta-field">
          <AppField label="Description (optional)" :uppercase="false" :htmlFor="`formula-column-description-${props.column.id}`" class="ui-formula-field">
            <InputText
              :id="`formula-column-description-${props.column.id}`"
              :name="`formula_column_description_${props.column.id}`"
              :modelValue="draftDescription"
              @update:modelValue="handleDescriptionChange"
              class="w-full"
              placeholder="What this calculates"
            />
          </AppField>
        </div>
      </div>

      <div class="ui-formula-operator-toolbar ui-formula-operator-toolbar--spaced">
        <span class="text-color-secondary text-xs ui-formula-op-label">Operators:</span>
        <Button
          v-for="op in operators"
          :key="op.label"
          :label="op.label"
          size="small"
          severity="help"
          text
          class="ui-formula-op-btn"
          @click="insertOperator(op.value)"
        />
      </div>

      <div class="ui-formula-operator-toolbar ui-formula-function-toolbar">
        <span class="text-color-secondary text-xs ui-formula-op-label">Functions:</span>
        <Button
          v-for="fn in formulaFunctions"
          :key="fn.label"
          :label="fn.label"
          size="small"
          severity="secondary"
          text
          class="ui-formula-fn-btn"
          @click="insertFunction(fn.value)"
        />
      </div>
    </AppSurfacePanel>

    <!-- Token-based Formula Input -->
    <div class="ui-formula-input-section">
      <AppField label="Formula" :uppercase="false" :htmlFor="`formula-tokens-${props.column.id}`" class="ui-formula-field">
        <template #label-extra>
          <AppTooltip :text="TOOLTIPS.FORMULA_SYNTAX" />
        </template>
        <TokenFormulaEditor
          :id="`formula-tokens-${props.column.id}`"
          :aria-label="`Formula editor for ${draftName || props.column.name || 'derived item'}`"
          :tokens="tokens"
          @update:tokens="handleTokensUpdate"
        />
      </AppField>
      <!-- Validation Errors Display -->
      <div v-if="validationErrors.length > 0" class="ui-formula-validation-errors mt-2">
        <div v-for="(err, i) in validationErrors" :key="i" class="text-xs ui-color-error flex align-items-center mb-1">
          <i class="pi pi-exclamation-triangle mr-1"></i>
          <span>{{ err }}</span>
        </div>
      </div>
      <div v-else-if="isValidating" class="ui-formula-helper-row mt-2">
        <span class="text-color-secondary text-xs ui-formula-helper">
          <i class="pi pi-spin pi-spinner mr-1"></i> Validating formula...
        </span>
      </div>
      <div v-else class="ui-formula-helper-row mt-2">
        <span class="text-color-secondary text-xs ui-formula-helper">
          Click variables to insert references. Use function buttons above, then add a reference and close with ")"
        </span>
      </div>
    </div>

    <div class="ui-formula-action-row">
      <Button
        label="Save"
        icon="pi pi-save"
        severity="secondary"
        :disabled="!isDirty || isValidating"
        :class="['save-button', isDirty ? 'formula-save-btn--dirty' : 'formula-save-btn--clean']"
        @click="handleSave"
      />
      <Button
        label="Preview"
        icon="pi pi-play"
        severity="secondary"
        :disabled="!canPreview || previewLoading || validationErrors.length > 0"
        class="preview-button"
        @click="handlePreviewClick"
      />
      <span v-if="isDirty" class="text-color-secondary text-xs">
        Unsaved changes
      </span>
    </div>
  </div>
</template>

<style scoped>
.formula-save-btn--dirty :deep(.p-button-label),
.formula-save-btn--dirty :deep(.p-button-icon) {
  color: var(--primary-500);
}

.formula-save-btn--clean {
  border-color: transparent;
  box-shadow: none;
  filter: none;
  background: var(--surface-card);
  pointer-events: none;
}
</style>
