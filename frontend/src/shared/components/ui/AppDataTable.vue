<script setup lang="ts">
import DataTable from 'primevue/datatable';

withDefaults(defineProps<{
  value: unknown[];
  scrollHeight?: string;
  virtualItemSize?: number;
  rows?: number;
  rowsPerPageOptions?: number[];
  paginatorThreshold?: number;
  compactPaginator?: boolean;
  alignHeaderTop?: boolean;
  hideSortUi?: boolean;
  clickableRows?: boolean;
  showGridlines?: boolean;
  stripedRows?: boolean;
  rowClass?: (data: unknown) => string;
  caption?: string;
  ariaLabel?: string;
  emptyMessage?: string;
}>(), {
  scrollHeight: '400px',
  virtualItemSize: 40,
  rows: 50,
  rowsPerPageOptions: () => [25, 50, 100, 250],
  paginatorThreshold: 50,
  compactPaginator: false,
  alignHeaderTop: false,
  hideSortUi: false,
  clickableRows: false,
  showGridlines: true,
  stripedRows: true,
  rowClass: undefined,
  caption: undefined,
  ariaLabel: undefined,
  emptyMessage: 'No data available.',
});

const emit = defineEmits<{
  rowClick: [event: unknown];
}>();
</script>

<template>
  <div
    class="ui-data-table"
    :class="{
      'ui-data-table--compact-paginator': compactPaginator,
      'ui-data-table--header-top': alignHeaderTop,
      'ui-data-table--hide-sort-ui': hideSortUi,
      'ui-data-table--clickable-rows': clickableRows,
    }"
  >
    <DataTable
      :value="value"
      :scrollable="true"
      :scrollHeight="scrollHeight"
      :virtualScrollerOptions="{ itemSize: virtualItemSize }"
      :showGridlines="showGridlines"
      :stripedRows="stripedRows"
      class="p-datatable-sm"
      :paginator="value.length > paginatorThreshold"
      :rows="rows"
      :rowsPerPageOptions="rowsPerPageOptions"
      paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
      currentPageReportTemplate="{first} to {last} of {totalRecords}"
      :rowClass="rowClass"
      :aria-label="ariaLabel"
      @row-click="(event) => emit('rowClick', event)"
    >
      <template v-if="caption" #header>
        <span class="ui-data-table-caption">{{ caption }}</span>
      </template>
      <slot />
      <template #empty>
        <slot name="empty">
          <div class="ui-data-table-empty">
            <i class="pi pi-inbox" aria-hidden="true" />
            <span>{{ emptyMessage }}</span>
          </div>
        </slot>
      </template>
    </DataTable>
  </div>
</template>
