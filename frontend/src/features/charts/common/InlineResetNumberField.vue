<script setup lang="ts">
import Button from 'primevue/button';
import InputNumber from 'primevue/inputnumber';

withDefaults(defineProps<{
  modelValue: number | null;
  placeholder?: string;
  min?: number;
  max?: number;
  disabled?: boolean;
  ariaLabel: string;
  icon?: string;
  inputId?: string;
}>(), {
  placeholder: '',
  min: -1000000000,
  max: 1000000000,
  disabled: false,
  icon: 'pi pi-times',
  inputId: undefined,
});

const emit = defineEmits<{
  'update:modelValue': [value: number | null];
  clear: [];
}>();

function handleNumericKeydown(event: KeyboardEvent) {
  const key = event.key;
  const isModifier = event.ctrlKey || event.metaKey || event.altKey;
  if (isModifier) return;

  const target = event.target as HTMLInputElement | null;
  const value = target?.value ?? '';
  const selectionStart = target?.selectionStart ?? 0;
  const selectionEnd = target?.selectionEnd ?? selectionStart;
  const selectedText = value.slice(selectionStart, selectionEnd);

  const allowedControlKeys = new Set([
    'Backspace',
    'Delete',
    'Tab',
    'Enter',
    'Escape',
    'ArrowLeft',
    'ArrowRight',
    'ArrowUp',
    'ArrowDown',
    'Home',
    'End',
  ]);
  if (allowedControlKeys.has(key)) return;

  if (key >= '0' && key <= '9') return;
  if (key === '.') {
    const existingDotOutsideSelection = value.includes('.') && !selectedText.includes('.');
    if (!existingDotOutsideSelection) return;
  }
  if (key === '-') {
    const hasMinusOutsideSelection = value.includes('-') && !selectedText.includes('-');
    if (selectionStart === 0 && !hasMinusOutsideSelection) return;
  }

  event.preventDefault();
}

function handleNumericPaste(event: ClipboardEvent) {
  const pasted = event.clipboardData?.getData('text') ?? '';
  if (!/^-?\d*(\.\d*)?$/.test(pasted.trim())) {
    event.preventDefault();
  }
}
</script>

<template>
  <div class="chart-inline-reset-field ui-inline-reset">
    <InputNumber
      :modelValue="modelValue"
      :inputId="inputId"
      class="ui-inline-reset-number"
      inputClass="ui-inline-reset-input"
      :placeholder="placeholder"
      :min="min"
      :max="max"
      :useGrouping="false"
      inputmode="decimal"
      @keydown="handleNumericKeydown"
      @paste="handleNumericPaste"
      @update:modelValue="(v: number | null) => emit('update:modelValue', v)"
    />
    <Button
      :icon="icon"
      severity="secondary"
      text
      size="small"
      class="chart-inline-reset-btn ui-inline-reset-btn"
      :disabled="disabled"
      @click="emit('clear')"
      :aria-label="ariaLabel"
    />
  </div>
</template>
