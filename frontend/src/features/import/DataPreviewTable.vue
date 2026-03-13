<script setup lang="ts">
import { computed } from 'vue';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import AppDataTable from '@/shared/components/ui/AppDataTable.vue';
import type { ColumnDef } from '@/shared/types/domain';

const props = defineProps<{
  columns: ColumnDef[];
  rows: Record<string, number | string | null>[];
  selectedRowIndex?: number | null;
}>();

const emit = defineEmits<{
  rowSelect: [index: number];
}>();

type PreviewRow = Record<string, number | string | null>;
type RowClickEvent = { data: PreviewRow };
const ROW_INDEX_KEY = '__rowIndex';
type IndexedPreviewRow = PreviewRow & { [ROW_INDEX_KEY]: number };

const pageSize = 50;
const pageSizeOptions = [25, 50, 100, 250];

const tableColumns = computed(() => {
  const seenFields = new Set<string>();
  const normalized: Array<{ key: string; field: string; header: string; type: ColumnDef['type']; unit: string }> = [];

  for (const col of props.columns) {
    // Skip duplicate field bindings to avoid duplicate visual columns in preview.
    if (seenFields.has(col.name)) continue;
    seenFields.add(col.name);

    normalized.push({
      key: col.name,
      field: col.name,
      header: col.name,
      type: col.type,
      unit: col.unit,
    });
  }

  return normalized;
});

const indexedRows = computed<IndexedPreviewRow[]>(() =>
  props.rows.map((row, index) => ({
    [ROW_INDEX_KEY]: index,
    ...row,
  })),
);

function typeSeverity(type: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | undefined {
  return type === 'numeric' ? 'info' : 'secondary';
}

function rowClass(data: unknown) {
  const row = data as IndexedPreviewRow;
  const index = row?.[ROW_INDEX_KEY];
  if (index === props.selectedRowIndex) {
    return 'ui-selected-row';
  }
  return '';
}

function onRowClick(event: unknown) {
  const row = (event as RowClickEvent | null)?.data as IndexedPreviewRow | undefined;
  if (!row) return;
  const index = row[ROW_INDEX_KEY];
  // Allow selecting any row including row 0 (first data row)
  if (typeof index === 'number' && index >= 0) {
    emit('rowSelect', index);
  }
}
</script>

<template>
  <div class="ui-data-preview-table">
    <AppDataTable
      :value="indexedRows"
      scrollHeight="min(56vh, 34rem)"
      :rows="pageSize"
      :paginatorThreshold="pageSize"
      :rowsPerPageOptions="pageSizeOptions"
      compactPaginator
      alignHeaderTop
      clickableRows
      :rowClass="rowClass"
      ariaLabel="Imported data preview"
      emptyMessage="No rows to preview."
      @rowClick="onRowClick"
    >
      <Column
        v-for="col in tableColumns"
        :key="col.key"
        :field="col.field"
        :sortable="true"
        class="ui-data-table-col--wide"
      >
        <template #header>
          <div class="ui-data-preview-col-header">
            <span class="ui-data-preview-col-title">{{ col.header }}</span>
            <div class="ui-data-preview-col-meta">
              <Tag
                :value="col.type"
                :severity="typeSeverity(col.type)"
                class="text-xs"
              />
              <Tag
                v-if="col.unit"
                :value="col.unit"
                severity="warn"
                class="text-xs"
              />
            </div>
          </div>
        </template>
        <template #body="{ data }">
          <span>{{ data[col.field] != null ? data[col.field] : '' }}</span>
        </template>
      </Column>
    </AppDataTable>
  </div>
</template>
