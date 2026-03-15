<script setup lang="ts">
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import type { DatasetMetadata } from '@/shared/types/domain';
import Tag from 'primevue/tag';

defineProps<{
  metadata: DatasetMetadata;
}>();
</script>

<template>
  <AppSurfacePanel class="ui-metadata-panel">
    <h3 class="ui-metadata-header">
      <i class="pi pi-info-circle text-primary" aria-hidden="true"></i>
      <span class="font-bold text-color">Detected Metadata</span>
    </h3>

    <div class="grid">
      <!-- Parameters -->
      <div v-if="metadata.parameters && Object.keys(metadata.parameters).length > 0" class="col-12 md:col-6 lg:col-4">
        <div class="ui-metadata-block">
          <span class="text-color-secondary text-sm font-semibold">Parameters</span>
          <div class="ui-metadata-tags-row ui-metadata-tags-row--spacious">
            <div v-for="[key, value] in Object.entries(metadata.parameters)" :key="key" class="ui-metadata-param-item">
              <span class="text-color-secondary text-sm">{{ key }}:</span>
              <Tag
                :value="metadata.parameterUnits?.[key] ? `${value} ${metadata.parameterUnits[key]}` : `${value}`"
                severity="info"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Row count -->
      <div class="col-12 md:col-6 lg:col-4">
        <div class="ui-metadata-block">
          <span class="text-color-secondary text-sm font-semibold">Data Summary</span>
          <div class="ui-metadata-tags-row ui-metadata-tags-row--spacious">
            <Tag :value="`${metadata.rowCount.toLocaleString()} rows`" severity="success" />
          </div>
        </div>
      </div>

      <!-- Units -->
      <div v-if="Object.keys(metadata.units).length > 0" class="col-12 md:col-6 lg:col-4">
        <div class="ui-metadata-block">
          <span class="text-color-secondary text-sm font-semibold">Detected Units</span>
          <div class="ui-metadata-tags-row">
            <Tag
              v-for="(unit, col) in metadata.units"
              :key="col"
              :value="`${col}: ${unit}`"
              severity="warn"
              class="text-xs"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="metadata.parseWarnings.length > 0" class="ui-metadata-warnings">
      <div class="ui-metadata-warnings-head">
        <i class="pi pi-exclamation-triangle ui-color-warning"></i>
        <span class="font-semibold ui-color-warning text-sm">Warnings</span>
      </div>
      <ul class="ui-metadata-warnings-list">
        <li v-for="(warning, i) in metadata.parseWarnings" :key="i" class="text-sm text-color-secondary">
          {{ warning }}
        </li>
      </ul>
    </div>
  </AppSurfacePanel>
</template>
