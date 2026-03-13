<script setup lang="ts">
import Button from 'primevue/button';
import AppStatusStrip from '@/shared/components/ui/AppStatusStrip.vue';

defineProps<{
  loading: boolean;
  error: string | null;
}>();

const emit = defineEmits<{
  retry: [];
}>();
</script>

<template>
  <AppStatusStrip :isLoading="loading" :error="error" minHeight="220px">
    <template #loading>
      <div class="ui-analysis-state-block ui-analysis-state-block--loading">
        <i class="pi pi-spin pi-spinner ui-analysis-state-icon" aria-hidden="true"></i>
        <h3 class="ui-analysis-state-title">Processing Data</h3>
        <p class="ui-analysis-state-text">Processing data and calculating results...</p>
      </div>
    </template>
    <template #error="{ error: errorMessage }">
      <div class="ui-analysis-state-block ui-analysis-state-block--error">
        <i class="pi pi-exclamation-circle ui-analysis-state-icon ui-analysis-state-icon--error" aria-hidden="true"></i>
        <h3 class="ui-analysis-state-title ui-analysis-state-title--error">Analysis Failed</h3>
        <p class="ui-analysis-state-text ui-analysis-state-text--error">{{ errorMessage }}</p>
        <Button label="Try Again" icon="pi pi-refresh" severity="secondary" @click="emit('retry')" />
      </div>
    </template>
    <template #idle />
  </AppStatusStrip>
</template>
