<script setup lang="ts">
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';

withDefaults(defineProps<{
  modelValue: string;
  placeholder?: string;
  disabled?: boolean;
  ariaLabel: string;
  maxLength?: number;
  icon?: string;
  inputId?: string;
}>(), {
  placeholder: '',
  disabled: false,
  maxLength: undefined,
  icon: 'pi pi-times',
  inputId: undefined,
});

const emit = defineEmits<{
  'update:modelValue': [value: string | undefined];
  clear: [];
}>();
</script>

<template>
  <div class="chart-inline-reset-field ui-inline-reset">
    <InputText
      :modelValue="modelValue"
      :id="inputId"
      class="ui-inline-reset-input"
      :placeholder="placeholder"
      :maxlength="maxLength"
      @update:modelValue="(v: string | undefined) => emit('update:modelValue', v)"
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
