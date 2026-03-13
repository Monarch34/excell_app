<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';
import AppField from '@/components/ui/AppField.vue';

const props = defineProps<{
  defaultName: string;
  dbLoading?: boolean;
}>();

const emit = defineEmits<{
  save: [name: string, description: string];
  saveToDb: [name: string, description: string];
}>();

const configName = ref(props.defaultName || 'My Analysis Config');
const configDescription = ref('');
const nameTouched = ref(false);

const trimmedConfigName = computed(() => configName.value.trim());
const nameError = computed(() => {
  if (!nameTouched.value) return undefined;
  if (!trimmedConfigName.value) return 'Config name is required';
  return undefined;
});
const isNameInvalid = computed(() => !!nameError.value);
const canSubmit = computed(() => trimmedConfigName.value.length > 0);

watch(
  () => props.defaultName,
  (next) => {
    if (!next) return;
    if (!configName.value.trim()) {
      configName.value = next;
    }
  }
);

function markNameTouched(): void {
  nameTouched.value = true;
}

function handleNameChange(value: string | undefined): void {
  markNameTouched();
  configName.value = value ?? '';
}

function handleSave(): void {
  markNameTouched();
  if (!canSubmit.value) return;
  emit('save', trimmedConfigName.value, configDescription.value);
}

function handleSaveToDb(): void {
  markNameTouched();
  if (!canSubmit.value) return;
  emit('saveToDb', trimmedConfigName.value, configDescription.value);
}
</script>

<template>
  <AppSurfacePanel class="config-save-panel ui-config-panel">
    <div class="ui-config-panel-head ui-config-save-head">
      <i class="pi pi-save ui-color-info" aria-hidden="true"></i>
      <span class="font-bold text-color">Save Configuration</span>
    </div>

    <div class="ui-config-save-body">
      <AppField
        label="Config Name"
        :uppercase="false"
        htmlFor="save-config-name"
        :required="true"
        :error="nameError"
      >
        <template #default="{ errorId, hasError }">
          <InputText
            id="save-config-name"
            :modelValue="configName"
            class="w-full"
            :class="{ 'p-invalid': isNameInvalid }"
            name="save_config_name"
            placeholder="Enter config name"
            :aria-describedby="hasError ? errorId : undefined"
            :aria-invalid="hasError"
            @update:modelValue="handleNameChange"
            @blur="markNameTouched"
          />
        </template>
      </AppField>
      <AppField
        label="Description (optional)"
        :uppercase="false"
        htmlFor="save-config-description"
      >
        <Textarea
          id="save-config-description"
          v-model="configDescription"
          class="w-full"
          name="save_config_description"
          rows="3"
          placeholder="Describe this configuration"
        />
      </AppField>
      <div class="ui-config-action-row">
        <Button
          label="Save to Workspace"
          icon="pi pi-database"
          severity="primary"
          class="flex-grow-1"
          @click="handleSaveToDb"
          :disabled="!canSubmit"
          :loading="dbLoading"
        />
        <Button
          label="Download File"
          icon="pi pi-download"
          severity="secondary"
          outlined
          @click="handleSave"
          :disabled="!canSubmit"
          v-tooltip.top="'Download as JSON'"
        />
      </div>
    </div>
  </AppSurfacePanel>
</template>
