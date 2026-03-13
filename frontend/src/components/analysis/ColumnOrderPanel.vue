<script setup lang="ts">
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import type { ProcessResultValue } from '@/types/api';

export interface OrderableColumn {
  name: string;
  source: 'original' | 'derived';
}

const props = defineProps<{
  columns: OrderableColumn[];
  separators: number[];
  previewByColumn?: Record<string, ProcessResultValue[]>;
}>();

const emit = defineEmits<{
  reorder: [fromIndex: number, toIndex: number];
  toggleSeparator: [index: number];
}>();

const draggableColumns = ref<OrderableColumn[]>([]);
const isDragging = ref(false);
const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 });

watch(
  () => props.columns,
  (next) => {
    draggableColumns.value = [...next];
  },
  { immediate: true, deep: true }
);

function sourceLabel(source: OrderableColumn['source']): string {
  return source === 'derived' ? 'Derived' : 'Original';
}

function hasSeparator(index: number): boolean {
  return props.separators.includes(index);
}

function formatPreviewValue(value: ProcessResultValue): string {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return '-';
    return numberFormatter.format(value);
  }
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  return String(value);
}

function previewForColumn(name: string): string {
  const values = props.previewByColumn?.[name] || [];
  if (values.length === 0) return 'No preview values';
  return values.slice(0, 10).map(formatPreviewValue).join(', ');
}

function onDragStart() {
  isDragging.value = true;
}

function onDragEnd(event: { oldIndex?: number; newIndex?: number }) {
  isDragging.value = false;
  if (event.oldIndex !== undefined && event.newIndex !== undefined) {
    emit('reorder', event.oldIndex, event.newIndex);
  }
}
</script>

<template>
  <div class="ui-column-order-panel">
    <div class="ui-order-head" aria-hidden="true">
      <span class="ui-order-head-spacer"></span>
      <span class="ui-order-head-label">Column</span>
      <span class="ui-order-head-label">Type</span>
      <span class="ui-order-head-spacer"></span>
    </div>
    <div class="ui-column-order-list ui-select-list" :class="{ 'is-dragging': isDragging }">
      <draggable
        :list="draggableColumns"
        item-key="name"
        handle=".ui-order-item-row"
        filter=".ui-order-action-btn, .ui-order-action-btn *"
        :preventOnFilter="false"
        :animation="180"
        easing="cubic-bezier(0.2, 0.8, 0.2, 1)"
        :scrollSensitivity="80"
        :scrollSpeed="14"
        :delayOnTouchOnly="true"
        :touchStartThreshold="4"
        chosen-class="ui-drag-chosen"
        drag-class="ui-drag-active"
        ghost-class="ui-drag-ghost"
        @start="onDragStart"
        @end="onDragEnd"
      >
        <template #item="{ element: col, index }">
          <div>
            <div class="ui-order-item ui-select-item ui-order-item-row ui-order-grid">
              <span class="ui-order-drag-cell">
                <i class="pi pi-bars ui-drag-handle text-color-secondary cursor-move" aria-hidden="true"></i>
              </span>
              <span class="ui-order-item-name font-semibold text-color text-sm">{{ col.name }}</span>
              <Tag
                :value="sourceLabel(col.source)"
                :severity="col.source === 'original' ? 'info' : 'success'"
                class="ui-order-type-tag"
              />
              <Button
                :icon="hasSeparator(index) ? 'pi pi-minus' : 'pi pi-ellipsis-h'"
                size="small"
                :severity="hasSeparator(index) ? 'primary' : 'secondary'"
                text
                class="ui-separator-btn ui-order-action-btn"
                v-tooltip.top="hasSeparator(index) ? 'Remove separator' : 'Add separator after'"
                @click.stop="emit('toggleSeparator', index)"
              />
            </div>
            <div class="ui-order-item-preview text-xs text-color-secondary">
              {{ previewForColumn(col.name) }}
            </div>
            <div v-if="hasSeparator(index)" class="ui-separator-line"></div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>
