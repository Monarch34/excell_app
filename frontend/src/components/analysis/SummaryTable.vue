<script setup lang="ts">
import Column from 'primevue/column';
import AppDataTable from '@/components/ui/AppDataTable.vue';
import { useNumberFormat } from '@/composables/useNumberFormat';
import type { ProcessResultValue } from '@/types/api';

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
    >
      <Column field="name" header="Parameter Name" sortable style="min-width: 200px" />
      <Column field="value" header="Value" sortable style="min-width: 120px">
        <template #body="{ data }">
          {{ formatValue(data.value) }}
        </template>
      </Column>
      <Column field="unit" header="Unit" style="min-width: 120px" />
    </AppDataTable>
  </div>
</template>
