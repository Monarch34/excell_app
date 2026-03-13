<script setup lang="ts">
withDefaults(defineProps<{
  rows?: number;
  columns?: number;
}>(), {
  rows: 5,
  columns: 4,
});
</script>

<template>
  <div class="ui-table-skeleton">
    <div class="ui-table-skeleton-header">
      <div v-for="col in columns" :key="`header-${col}`" class="ui-table-skeleton-header-cell">
        <div class="ui-table-skeleton-bar ui-table-skeleton-bar--header"></div>
      </div>
    </div>
    <div v-for="row in rows" :key="`row-${row}`" class="ui-table-skeleton-row">
      <div v-for="col in columns" :key="`cell-${row}-${col}`" class="ui-table-skeleton-cell">
        <div
          class="ui-table-skeleton-bar ui-table-skeleton-bar--cell"
          :style="{ width: `${60 + Math.random() * 30}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>
