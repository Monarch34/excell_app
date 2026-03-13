<script setup lang="ts">
import { computed } from 'vue';
import Checkbox from 'primevue/checkbox';
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import type { ColumnDef } from '@/types/domain';

const props = defineProps<{
  columns: ColumnDef[];
  selectedNames: string[];
}>();

const emit = defineEmits<{
  toggle: [name: string];
  selectAll: [];
  deselectAll: [];
}>();

const numericCount = computed(() =>
  props.columns.filter((c) => c.type === 'numeric').length
);

const selectedCount = computed(() => props.selectedNames.length);

function isSelected(name: string): boolean {
  return props.selectedNames.includes(name);
}
</script>

<template>
  <div class="column-toggle-list ui-column-toggle-list">
    <div class="ui-column-toggle-head">
      <span class="text-color-secondary text-sm">
        {{ selectedCount }} of {{ columns.length }} columns selected
        ({{ numericCount }} numeric)
      </span>
      <div class="ui-column-toggle-actions">
        <Button label="Select All" size="small" severity="secondary" text @click="emit('selectAll')" />
        <Button label="Deselect All" size="small" severity="secondary" text @click="emit('deselectAll')" />
      </div>
    </div>

    <div class="ui-column-list-scroll ui-select-list">
      <label
        v-for="(col, index) in columns"
        :key="`${col.name}-${index}`"
        :for="`column-toggle-${index}`"
        class="column-item ui-select-item ui-column-toggle-item cursor-pointer"
        :class="{ 'ui-select-item--selected': isSelected(col.name) }"
        :aria-pressed="isSelected(col.name)"
        :aria-label="`Toggle column ${col.name}`"
      >
        <Checkbox
          :inputId="`column-toggle-${index}`"
          :name="`column_toggle_${index}`"
          :modelValue="isSelected(col.name)"
          :binary="true"
          @click.stop
          @update:modelValue="emit('toggle', col.name)"
        />

        <span class="font-semibold text-color ui-column-toggle-item-name">
          {{ col.name }}
        </span>

        <Tag
          :value="col.type"
          :severity="col.type === 'numeric' ? 'info' : 'secondary'"
          class="text-xs"
        />
        <Tag
          v-if="col.unit"
          :value="col.unit"
          severity="warn"
          class="text-xs"
        />
      </label>
    </div>
  </div>
</template>
