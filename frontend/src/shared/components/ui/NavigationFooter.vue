<script setup lang="ts">
import Button from 'primevue/button';

interface Props {
  backLabel?: string;
  primaryLabel?: string;
  primaryIcon?: string;
  primaryDisabled?: boolean;
  primaryLoading?: boolean;
  stepDescription?: string;
}

withDefaults(defineProps<Props>(), {
  backLabel: 'Back',
  primaryLabel: 'Next',
  primaryIcon: 'pi pi-arrow-right',
  primaryDisabled: false,
  primaryLoading: false,
  stepDescription: undefined,
});

const emit = defineEmits<{ back: []; primary: [] }>();
</script>

<template>
  <nav class="ui-nav-footer ui-nav-footer--wizard" aria-label="Step navigation">
    <div class="ui-nav-footer-left">
      <Button
        :label="backLabel"
        icon="pi pi-arrow-left"
        class="p-button-secondary p-button-outlined ui-footer-back-btn"
        @click="emit('back')"
      />
      <slot name="left-actions" />
    </div>
    <span v-if="stepDescription" class="ui-nav-footer-step-info">{{ stepDescription }}</span>
    <div class="ui-nav-footer-right">
      <slot name="right-actions" />
      <Button
        :label="primaryLabel"
        :icon="primaryIcon"
        iconPos="right"
        :disabled="primaryDisabled"
        :loading="primaryLoading"
        class="p-button-primary ui-footer-primary-btn"
        @click="emit('primary')"
      />
    </div>
  </nav>
</template>
