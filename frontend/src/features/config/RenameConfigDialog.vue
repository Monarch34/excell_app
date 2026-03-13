<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import AppField from '@/shared/components/ui/AppField.vue';

const inputRef = ref<InstanceType<typeof InputText> | null>(null);

const props = defineProps<{
  visible: boolean;
  renameName: string;
  renameLoading: boolean;
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  'update:renameName': [value: string];
  submit: [];
  cancel: [];
}>();

const nameModel = computed({
  get: () => props.renameName,
  set: (value: string) => emit('update:renameName', value),
});

const touched = ref(false);
const trimmedName = computed(() => props.renameName.trim());
const nameError = computed(() => {
  if (!touched.value) return undefined;
  if (!trimmedName.value) return 'Config name is required';
  return undefined;
});
const canSubmit = computed(() => trimmedName.value.length > 0);

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      touched.value = false;
      nextTick(() => {
        const el = inputRef.value?.$el;
        if (el && typeof (el as HTMLElement).focus === 'function') (el as HTMLElement).focus();
      });
    }
  }
);

function markTouched(): void {
  touched.value = true;
}

function handleNameChange(value: string | undefined): void {
  markTouched();
  emit('update:renameName', value ?? '');
}

function handleSubmit(): void {
  markTouched();
  if (!canSubmit.value) return;
  emit('submit');
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="Rename Configuration"
    :style="{ width: '30rem' }"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="flex flex-column gap-3 pt-2">
      <AppField
        label="New Name"
        :uppercase="false"
        htmlFor="rename-input"
        :required="true"
        :error="nameError"
      >
        <template #default="{ errorId, hasError }">
          <InputText
            ref="inputRef"
            id="rename-input"
            :modelValue="nameModel"
            class="w-full"
            :class="{ 'p-invalid': !!nameError }"
            :aria-describedby="hasError ? errorId : undefined"
            :aria-invalid="hasError"
            @update:modelValue="handleNameChange"
            @blur="markTouched"
            @keyup.enter="handleSubmit"
          />
        </template>
      </AppField>
    </div>
    <template #footer>
      <div class="ui-dialog-actions">
        <button
          type="button"
          class="ui-dialog-btn ui-dialog-btn--secondary"
          @click="emit('cancel')"
        >
          Cancel
        </button>
        <button
          type="button"
          class="ui-dialog-btn ui-dialog-btn--primary"
          :disabled="!canSubmit || renameLoading"
          @click="handleSubmit"
        >
          <span v-if="renameLoading">Saving…</span>
          <span v-else>Save Name</span>
        </button>
      </div>
    </template>
  </Dialog>
</template>
