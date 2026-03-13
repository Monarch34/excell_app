<script setup lang="ts">
withDefaults(defineProps<{
  rows?: number;
  columns?: number;
}>(), {
  rows: 5,
  columns: 4,
});

const cellWidths = [72, 85, 63, 78, 91, 67, 82, 74, 88, 65, 76, 83, 69, 87, 71, 80, 64, 90, 75, 68];

function getCellWidth(row: number, col: number): string {
  return `${cellWidths[(row * 7 + col * 3) % cellWidths.length]}%`;
}
</script>

<template>
  <div class="ui-table-skeleton" role="status" aria-busy="true">
    <span class="ui-visually-hidden">Loading table data…</span>
    <div class="ui-table-skeleton-header">
      <div v-for="col in columns" :key="`header-${col}`" class="ui-table-skeleton-header-cell">
        <div class="ui-table-skeleton-bar ui-table-skeleton-bar--header"></div>
      </div>
    </div>
    <div v-for="row in rows" :key="`row-${row}`" class="ui-table-skeleton-row">
      <div v-for="col in columns" :key="`cell-${row}-${col}`" class="ui-table-skeleton-cell">
        <div
          class="ui-table-skeleton-bar ui-table-skeleton-bar--cell"
          :style="{ width: getCellWidth(row, col) }"
        ></div>
      </div>
    </div>
  </div>
</template>
