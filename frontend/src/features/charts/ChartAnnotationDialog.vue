<script setup lang="ts">
import AppDialogSurface from '@/shared/components/ui/AppDialogSurface.vue';
import AppField from '@/shared/components/ui/AppField.vue';
import InputText from 'primevue/inputtext';
import { computed, ref, watch, type CSSProperties } from 'vue';

const props = defineProps<{
  visible: boolean;
  text: string;
}>();

const emit = defineEmits<{
  'update:visible': [visible: boolean];
  'update:text': [text: string];
  save: [];
}>();

const dialogStyle: CSSProperties = { width: 'min(92vw, 30rem)' };
const dialogBreakpoints = { '640px': '96vw' };
const annotationInputId = 'chart-annotation-text';
const touched = ref(false);

const textError = computed(() => {
  if (!touched.value) return undefined;
  if (!props.text.trim()) return 'Annotation text is required';
  return undefined;
});
const canSave = computed(() => props.text.trim().length > 0);

watch(
  () => props.visible,
  (visible) => {
    if (visible) touched.value = false;
  }
);

function markTouched(): void {
  touched.value = true;
}

function handleTextChange(value: string | undefined): void {
  markTouched();
  emit('update:text', value ?? '');
}

function handleSave(): void {
  markTouched();
  if (!canSave.value) return;
  emit('save');
}
</script>

<template>
  <AppDialogSurface
    :visible="visible"
    header="Add Annotation"
    modal
    :style="dialogStyle"
    :breakpoints="dialogBreakpoints"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="ui-annotation-dialog-body">
      <AppField
        label="Annotation"
        :uppercase="false"
        :htmlFor="annotationInputId"
        :required="true"
        :error="textError"
      >
        <InputText
          :id="annotationInputId"
          name="chart_annotation_text"
          :modelValue="text"
          placeholder="Enter annotation text"
          autofocus
          :class="{ 'p-invalid': !!textError }"
          @update:modelValue="handleTextChange"
          @blur="markTouched"
        />
      </AppField>
    </div>
    <template #footer>
      <div class="ui-dialog-actions">
        <button
          type="button"
          class="ui-dialog-btn ui-dialog-btn--secondary"
          @click="emit('update:visible', false)"
        >
          Cancel
        </button>
        <button
          type="button"
          class="ui-dialog-btn ui-dialog-btn--primary"
          :disabled="!canSave"
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </template>
  </AppDialogSurface>
</template>
