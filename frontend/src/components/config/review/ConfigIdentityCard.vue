<script setup lang="ts">
import type { AnalysisConfig } from '@/types/domain';

defineProps<{
  config: AnalysisConfig;
  formatDate: (value: string | null | undefined) => string;
}>();
</script>

<template>
  <section class="cfg-identity">
    <div class="cfg-identity-row">
      <div class="cfg-identity-left">
        <h3 class="cfg-identity-name">{{ config.name }}</h3>
        <span class="cfg-version-badge">v{{ config.version }}</span>
      </div>
      <div class="cfg-identity-dates">
        <span v-if="config.createdAt" class="cfg-date-chip"><i class="pi pi-calendar-plus"></i> {{ formatDate(config.createdAt) }}</span>
        <span v-if="config.updatedAt" class="cfg-date-chip"><i class="pi pi-refresh"></i> {{ formatDate(config.updatedAt) }}</span>
      </div>
    </div>
    <p v-if="config.description" class="cfg-description">{{ config.description }}</p>
  </section>
</template>


