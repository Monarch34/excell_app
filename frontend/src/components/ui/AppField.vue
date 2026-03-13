<script setup lang="ts">
import { ref } from 'vue';

withDefaults(defineProps<{
  label: string;
  uppercase?: boolean;
  description?: string;
  error?: string;
  required?: boolean;
  htmlFor?: string;
}>(), {
  uppercase: true,
  required: false,
});

const errorId = ref(`ui-field-error-${Math.random().toString(36).slice(2, 11)}`);
</script>

<template>
  <div class="ui-field" :class="{ 'ui-field--error': error }">
    <component
      :is="htmlFor ? 'label' : 'div'"
      class="ui-field-label"
      :class="{ 'ui-field-label--plain': !uppercase }"
      :for="htmlFor || undefined"
    >
      <span class="ui-field-label-row">
        <span class="ui-field-label-text">
          {{ label }}
          <span v-if="required" class="ui-field-required" aria-label="required">*</span>
        </span>
        <slot name="label-extra" />
      </span>
    </component>
    <slot :errorId="errorId" :hasError="!!error" />
    <small v-if="description && !error" class="ui-field-description">
      {{ description }}
    </small>
    <small v-if="error" :id="errorId" class="ui-field-error" role="alert">
      <i class="pi pi-exclamation-circle" aria-hidden="true"></i>
      {{ error }}
    </small>
  </div>
</template>
