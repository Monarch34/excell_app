<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import { useNumberFormat, type NumberFormatMode } from '@/composables/useNumberFormat';
import type { ProcessResultValue } from '@/shared/types/api';
import type { MatchingColumnGroup } from '@/shared/types/domain';
import type { OrderableColumn } from '@/features/analysis/ColumnOrderPanel.vue';
import { sourceLabel } from '@/utils/ui';

const props = defineProps<{
  columns: OrderableColumn[];
  previewRows: Record<string, ProcessResultValue>[];
  separators: number[];
  separatorColor: string;
  matchingGroups: MatchingColumnGroup[];
  numberFormatMode?: NumberFormatMode;
}>();

const emit = defineEmits<{
  reorder: [fromIndex: number, toIndex: number];
  toggleSeparator: [index: number];
}>();

const localColumns = ref<OrderableColumn[]>([]);
const { mode: formatMode, formatValue } = useNumberFormat('scientific');

watch(
  () => props.numberFormatMode,
  (next) => {
    if (next) formatMode.value = next;
  },
  { immediate: true },
);

watch(
  () => props.columns,
  (next) => {
    localColumns.value = [...next];
  },
  { immediate: true, deep: true },
);

const previewLimit = 10;
const limitedRows = computed(() => props.previewRows.slice(0, previewLimit));



function hasSeparator(index: number): boolean {
  return props.separators.includes(index);
}

function separatorStyle(index: number): Record<string, string> {
  if (!hasSeparator(index)) return {};
  return {
    borderRightColor: props.separatorColor,
    borderRightWidth: '3px',
    borderRightStyle: 'solid',
  };
}

function groupForColumn(name: string): MatchingColumnGroup | undefined {
  return props.matchingGroups.find((group) => group.columns.includes(name));
}

function groupStyle(name: string): Record<string, string> {
  const group = groupForColumn(name);
  if (!group?.color) return {};
  return {
    boxShadow: `inset 0 3px 0 ${group.color}`,
  };
}

const liveAnnouncement = ref('');

function onDragEnd(event: { oldIndex?: number; newIndex?: number }): void {
  if (event.oldIndex === undefined || event.newIndex === undefined) return;
  emit('reorder', event.oldIndex, event.newIndex);
}

function moveColumn(index: number, direction: -1 | 1): void {
  const target = index + direction;
  if (target < 0 || target >= localColumns.value.length) return;
  emit('reorder', index, target);
  const name = localColumns.value[index].name;
  liveAnnouncement.value = `Moved ${name} to position ${target + 1} of ${localColumns.value.length}`;
}
</script>

<template>
  <div class="ui-derived-columns-preview">
    <div aria-live="polite" class="ui-visually-hidden">{{ liveAnnouncement }}</div>
    <div class="ui-derived-columns-preview-head">
      <p class="ui-analysis-order-subpanel-note">
        Drag column headers or use arrow keys to reorder export columns. Preview shows first 10 rows.
      </p>
    </div>

    <div v-if="columns.length === 0" class="ui-select-empty">
      No columns available for preview.
    </div>

    <div v-else class="ui-derived-columns-scroll">
      <draggable
        :list="localColumns"
        item-key="name"
        tag="div"
        class="ui-derived-columns-flex"
        handle=".ui-derived-col-drag"
        :animation="180"
        ghost-class="ui-drag-ghost"
        chosen-class="ui-drag-chosen"
        @end="onDragEnd"
      >
        <template #item="{ element: column, index }">
          <div
            class="ui-derived-col-wrapper"
            :style="separatorStyle(index)"
          >
            <!-- Header Segment -->
            <div 
              class="ui-derived-col-header"
              :style="groupStyle(column.name)"
            >
              <div class="ui-derived-col-header-main">
                <button
                  type="button"
                  class="ui-derived-col-drag"
                  :aria-label="`Move column ${column.name}. Use left and right arrows to reorder.`"
                  @keydown.left.prevent="moveColumn(index, -1)"
                  @keydown.right.prevent="moveColumn(index, 1)"
                >
                  <i class="pi pi-bars" aria-hidden="true"></i>
                </button>
                <span class="ui-derived-col-title" :title="column.name">{{ column.name }}</span>
              </div>
              <div class="ui-derived-col-meta">
                <Tag
                  :value="sourceLabel(column.source)"
                  :severity="column.source === 'derived' ? 'success' : 'info'"
                  class="ui-derived-col-source-tag"
                />
                <Tag
                  v-if="groupForColumn(column.name)"
                  :value="groupForColumn(column.name)?.name"
                  class="ui-derived-col-group-tag"
                />
              </div>
              <Button
                :icon="hasSeparator(index) ? 'pi pi-minus' : 'pi pi-ellipsis-h'"
                size="small"
                :severity="hasSeparator(index) ? 'primary' : 'secondary'"
                text
                class="ui-derived-col-separator-btn"
                v-tooltip.top="hasSeparator(index) ? 'Remove separator after column' : 'Add separator after column'"
                @click.stop="emit('toggleSeparator', index)"
              />
            </div>
            
            <!-- Data Rows Segment -->
            <div class="ui-derived-col-body">
              <div
                v-for="(row, rowIndex) in limitedRows"
                :key="`preview-${rowIndex}`"
                class="ui-derived-col-cell"
                :title="formatValue(row[column.name])"
              >
                {{ formatValue(row[column.name]) }}
              </div>
            </div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>
