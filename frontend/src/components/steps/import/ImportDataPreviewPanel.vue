<script setup lang="ts">
import DataPreviewTable from '@/components/import/DataPreviewTable.vue';
import MetadataPanel from '@/components/import/MetadataPanel.vue';
import AppNotice from '@/components/ui/AppNotice.vue';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import type { ColumnDef, DatasetMetadata } from '@/types/domain';

defineProps<{
  filename: string;
  fileSummary: string;
  metadata: DatasetMetadata;
  columns: ColumnDef[];
  rows: Record<string, number | string | null>[];
  referenceRowIndex: number | null;
  referenceRowUserSelected: boolean;
}>();

const emit = defineEmits<{
  uploadDifferent: [];
  selectReferenceRow: [index: number];
  next: [];
}>();
</script>

<template>
  <div class="fade-in step-grid ui-clamp-gap-sm">
    <AppSurfacePanel class="step-toolbar ui-import-file-toolbar">
      <div class="ui-import-file-meta">
        <i class="pi pi-file text-primary text-2xl"></i>
        <div>
          <h3 class="text-xl font-bold text-color ui-import-file-title">{{ filename }}</h3>
          <span class="text-color-secondary text-sm">{{ fileSummary }}</span>
        </div>
      </div>
      <Button
        label="Upload Different File"
        icon="pi pi-refresh"
        severity="secondary"
        outlined
        @click="emit('uploadDifferent')"
      />
    </AppSurfacePanel>

    <MetadataPanel
      v-if="metadata.parameters || Object.keys(metadata.units).length > 0 || metadata.parseWarnings.length > 0"
      :metadata="metadata"
      class="ui-surface-block ui-surface-block--compact"
    />

    <AppSurfacePanel class="ui-import-reference-panel">
      <div v-if="referenceRowUserSelected" class="ui-import-reference-selected">
        <i class="pi pi-map-marker ui-color-warning"></i>
        <Tag severity="warn" class="font-semibold">
          Reference Row: {{ (referenceRowIndex ?? 0) + 1 }}
        </Tag>
        <span class="text-sm text-color-secondary">Using this row for calculations</span>
      </div>
      <AppNotice v-else severity="info" appearance="ghost" class="ui-import-reference-hint">
        <i class="pi pi-info-circle text-primary"></i>
        <span class="text-sm text-color-secondary">
          Using the first row by default. Click any row to change it.
        </span>
      </AppNotice>
    </AppSurfacePanel>

    <DataPreviewTable
      :columns="columns"
      :rows="rows"
      :selectedRowIndex="referenceRowUserSelected ? referenceRowIndex : null"
      @row-select="(index) => emit('selectReferenceRow', index)"
    />

    <div class="ui-import-footer-actions ui-step-actions">
      <Button
        label="Next"
        icon="pi pi-arrow-right"
        iconPos="right"
        :disabled="referenceRowIndex === null"
        size="large"
        @click="emit('next')"
      />
    </div>
  </div>
</template>
