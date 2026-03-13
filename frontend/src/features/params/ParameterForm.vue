<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import InputNumber from 'primevue/inputnumber';
import type { InputNumberInputEvent } from 'primevue/inputnumber';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import AppField from '@/shared/components/ui/AppField.vue';
import AppTooltip from '@/shared/components/ui/AppTooltip.vue';
import { TOOLTIPS } from '@/constants/tooltips';
import type { Parameter } from '@/shared/types/domain';

type EditableField = 'name' | 'value';

const props = defineProps<{
  metadataParameters: Record<string, number>;
  metadataParameterUnits: Record<string, string>;
  userParameters: Parameter[];
}>();

const emit = defineEmits<{
  updateParameter: [index: number, updates: Partial<Parameter>];
  removeParameter: [index: number];
}>();

const expanded = reactive({
  metadata: true,
  user: true,
});

const touchedFields = ref<Record<string, boolean>>({});

const hasMetadataParameters = computed(() => Object.keys(props.metadataParameters).length > 0);
const hasUserParameters = computed(() => props.userParameters.length > 0);
const isEmpty = computed(() => !hasMetadataParameters.value && !hasUserParameters.value);

const duplicateNameSet = computed(() => {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const param of props.userParameters) {
    const normalizedName = normalizeName(param.name);
    if (!normalizedName) continue;

    if (seen.has(normalizedName)) {
      duplicates.add(normalizedName);
    } else {
      seen.add(normalizedName);
    }
  }

  return duplicates;
});

function normalizeName(name: string): string {
  return name.trim().toLowerCase();
}

function getFieldKey(index: number, field: EditableField): string {
  return `${field}-${index}`;
}

function markTouched(index: number, field: EditableField): void {
  touchedFields.value[getFieldKey(index, field)] = true;
}

function isTouched(index: number, field: EditableField): boolean {
  return touchedFields.value[getFieldKey(index, field)] === true;
}

function validateName(param: Parameter): string | undefined {
  const normalizedName = normalizeName(param.name);

  if (!normalizedName) {
    return 'Name is required';
  }

  if (duplicateNameSet.value.has(normalizedName)) {
    return 'Name must be unique';
  }

  return undefined;
}

function validateValue(param: Parameter): string | undefined {
  if (param.value === null) return 'Value is required';
  if (!Number.isFinite(param.value)) return 'Value must be numeric';
  return undefined;
}

function getFieldError(field: EditableField, param: Parameter): string | undefined {
  return field === 'name' ? validateName(param) : validateValue(param);
}

function getVisibleFieldError(index: number, field: EditableField, param: Parameter): string | undefined {
  if (!isTouched(index, field)) return undefined;
  return getFieldError(field, param);
}

function hasFieldError(index: number, field: EditableField, param: Parameter): boolean {
  return !!getVisibleFieldError(index, field, param);
}

function getRowErrors(index: number, param: Parameter): string[] {
  return (['name', 'value'] as const)
    .map((field) => getVisibleFieldError(index, field, param))
    .filter((error): error is string => !!error);
}

function handleNameChange(index: number, value: string | undefined): void {
  markTouched(index, 'name');
  emit('updateParameter', index, { name: value ?? '' });
}

function normalizeNumericValue(value: string | number | undefined | null): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function handleValueInput(index: number, event: InputNumberInputEvent): void {
  markTouched(index, 'value');
  emit('updateParameter', index, { value: normalizeNumericValue(event.value) });
}

function handleValueChange(index: number, value: number | null): void {
  markTouched(index, 'value');
  emit('updateParameter', index, { value: normalizeNumericValue(value) });
}

function handleUnitChange(index: number, value: string | undefined): void {
  emit('updateParameter', index, { unit: value ?? '' });
}

function handleFieldBlur(index: number, field: EditableField): void {
  markTouched(index, field);
}

function removeParameter(index: number): void {
  emit('removeParameter', index);
}
</script>

<template>
  <div class="ui-parameter-form">
    <div
      v-if="isEmpty"
      class="text-color-secondary text-sm text-center ui-param-empty"
    >
      No parameters available. Click "Add Parameter" to create one.
    </div>

    <div v-else class="ui-param-stack">
      <section v-if="hasMetadataParameters" class="chart-collapsible">
        <button
          type="button"
          class="chart-collapse-trigger"
          :aria-expanded="expanded.metadata"
          @click="expanded.metadata = !expanded.metadata"
        >
          <span>Metadata Parameters</span>
          <i class="pi" :class="expanded.metadata ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true" />
        </button>
        <div v-show="expanded.metadata" class="chart-collapse-content">
          <div class="ui-param-group ui-param-group--subsection">
            <div
              v-for="(value, name, metaIndex) in props.metadataParameters"
              :key="'meta-' + name"
              class="ui-param-row ui-param-row--meta"
            >
              <AppField label="Name" :uppercase="false" :htmlFor="`meta-param-name-${metaIndex}`">
                <InputText
                  :id="`meta-param-name-${metaIndex}`"
                  :name="`meta_param_name_${metaIndex}`"
                  :modelValue="name"
                  size="small"
                  class="w-full compact-input ui-compact-control"
                  disabled
                />
              </AppField>
              <AppField label="Value" :uppercase="false" :htmlFor="`meta-param-value-${metaIndex}`">
                <InputNumber
                  :inputId="`meta-param-value-${metaIndex}`"
                  :name="`meta_param_value_${metaIndex}`"
                  :pt="{ input: { name: `meta_param_value_${metaIndex}` } }"
                  :modelValue="value"
                  mode="decimal"
                  :minFractionDigits="1"
                  :maxFractionDigits="6"
                  size="small"
                  class="w-full compact-input ui-compact-control"
                  disabled
                />
              </AppField>
              <AppField label="Unit" :uppercase="false" :htmlFor="`meta-param-unit-${metaIndex}`">
                <InputText
                  :id="`meta-param-unit-${metaIndex}`"
                  :name="`meta_param_unit_${metaIndex}`"
                  :modelValue="props.metadataParameterUnits[name] || ''"
                  size="small"
                  class="w-full compact-input ui-compact-control"
                  placeholder="Unit"
                  disabled
                />
              </AppField>
              <div class="ui-param-field-group ui-param-field-group--action">
                <Button
                  icon="pi pi-lock"
                  severity="secondary"
                  text
                  size="small"
                  class="ui-action-icon-btn ui-param-action-btn"
                  :aria-label="`Metadata parameter ${name} is locked`"
                  disabled
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="hasUserParameters" class="chart-collapsible">
        <button
          type="button"
          class="chart-collapse-trigger"
          :aria-expanded="expanded.user"
          @click="expanded.user = !expanded.user"
        >
          <span>User Parameters</span>
          <i class="pi" :class="expanded.user ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true" />
        </button>
        <div v-show="expanded.user" class="chart-collapse-content">
          <div class="ui-param-group ui-param-group--subsection">
            <div
              v-for="(param, index) in userParameters"
              :key="index"
              class="ui-param-entry"
            >
              <div class="ui-param-row ui-param-row--user">
                <AppField
                  label="Name"
                  :uppercase="false"
                  :htmlFor="`param-name-${index}`"
                  :class="[
                    'ui-param-field',
                    { 'ui-param-field--invalid': hasFieldError(index, 'name', param) }
                  ]"
                >
                  <InputText
                    :id="`param-name-${index}`"
                    :name="`user_param_name_${index}`"
                    :modelValue="param.name"
                    @update:modelValue="handleNameChange(index, $event)"
                    @blur="handleFieldBlur(index, 'name')"
                    size="small"
                    class="w-full compact-input ui-compact-control"
                    placeholder="Name"
                    :aria-label="`Parameter name ${index + 1}`"
                  />
                </AppField>
                <AppField
                  label="Value"
                  :uppercase="false"
                  :htmlFor="`param-value-${index}`"
                  :class="[
                    'ui-param-field',
                    { 'ui-param-field--invalid': hasFieldError(index, 'value', param) }
                  ]"
                >
                  <InputNumber
                    :inputId="`param-value-${index}`"
                    :name="`user_param_value_${index}`"
                    :pt="{ input: { name: `user_param_value_${index}` } }"
                    :modelValue="param.value"
                    @input="(event: InputNumberInputEvent) => handleValueInput(index, event)"
                    @update:modelValue="handleValueChange(index, $event)"
                    @blur="handleFieldBlur(index, 'value')"
                    mode="decimal"
                    :minFractionDigits="1"
                    :maxFractionDigits="6"
                    size="small"
                    class="w-full compact-input ui-compact-control"
                    :aria-label="`Parameter value ${index + 1}`"
                  />
                </AppField>
                <AppField label="Unit" :uppercase="false" :htmlFor="`param-unit-${index}`" class="ui-param-field">
                  <InputText
                    :id="`param-unit-${index}`"
                    :name="`user_param_unit_${index}`"
                    :modelValue="param.unit"
                    @update:modelValue="handleUnitChange(index, $event)"
                    size="small"
                    class="w-full compact-input ui-compact-control"
                    placeholder="Unit"
                    :aria-label="`Parameter unit ${index + 1}`"
                  />
                </AppField>
                <div class="ui-param-field-group ui-param-field-group--action">
                  <AppTooltip :text="TOOLTIPS.PARAMETER_NAME + ' / ' + TOOLTIPS.PARAMETER_VALUE + ' / ' + TOOLTIPS.PARAMETER_UNIT" />
                  <Button
                    icon="pi pi-trash"
                    severity="danger"
                    text
                    size="small"
                    class="ui-action-icon-btn ui-param-action-btn ui-delete-btn"
                    :aria-label="`Delete parameter ${param.name || index + 1}`"
                    @click="removeParameter(index)"
                  />
                </div>
              </div>

              <div v-if="getRowErrors(index, param).length > 0" class="ui-param-row-error" aria-live="polite">
                <i class="pi pi-exclamation-circle"></i>
                <span>{{ getRowErrors(index, param).join(' / ') }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
