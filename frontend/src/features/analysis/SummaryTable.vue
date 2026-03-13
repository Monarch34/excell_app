<script setup lang="ts">
import Column from 'primevue/column';
import AppDataTable from '@/shared/components/ui/AppDataTable.vue';
import { useNumberFormat } from '@/composables/useNumberFormat';
import type { ProcessResultValue } from '@/shared/types/api';

defineProps<{
  rows: Array<{
    id: string;
    name: string;
    value: ProcessResultValue | undefined;
    unit: string;
  }>;
}>();

const { formatValue } = useNumberFormat('fixed');
</script>

<template>
  <div class="summary-table ui-summary-table">
    <AppDataTable
      :value="rows"
      scrollHeight="400px"
      :paginatorThreshold="50"
      :rows="50"
      ariaLabel="Summary parameters"
      emptyMessage="No summary parameters available yet."
    >
      <Column field="name" header="Parameter Name" sortable class="ui-data-table-col--name" />
      <Column field="value" header="Value" sortable class="ui-data-table-col--wide">
        <template #body="{ data }">
          {{ formatValue(data.value) }}
        </template>
      </Column>
      <Column field="unit" header="Unit" class="ui-data-table-col--wide" />
    </AppDataTable>
  </div>
</template>
