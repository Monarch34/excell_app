<script setup lang="ts">
import { useChartsStore } from '@/stores/charts';
import { storeToRefs } from 'pinia';
import AppPageHeader from '@/shared/components/ui/AppPageHeader.vue';
import ChartCard from '@/features/charts/ChartCard.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
const chartsStore = useChartsStore();

const { charts, canAdd, count, sortedCharts } = storeToRefs(chartsStore);
</script>

<template>
  <div class="step-shell">
    <AppPageHeader icon="pi-chart-line" title="Chart Definitions">
      <div class="ui-chart-header-actions">
        <Tag :value="`${count} / ${chartsStore.MAX_CHARTS}`" severity="info" class="text-xs" />
        <Button
          label="Add Chart"
          icon="pi pi-plus"
          size="small"
          severity="primary"
          :disabled="!canAdd"
          @click="chartsStore.addChart()"
        />
      </div>
    </AppPageHeader>
    <div class="ui-muted-hint ui-step-intro ui-chart-intro text-sm text-color-secondary">
      Configure chart type, axes, styling, and baseline behavior. Add annotations from preview by clicking on points.
    </div>

    <div v-if="charts.length === 0" class="step-empty text-center ui-chart-empty">
      <i class="pi pi-chart-line text-4xl text-color-secondary ui-chart-empty-icon"></i>
      <p class="text-color-secondary">No charts defined yet. Click "Add Chart" to create one.</p>
    </div>

    <div class="chart-list ui-chart-list ui-clamp-gap-md">
      <ChartCard
        v-for="chart in sortedCharts"
        :key="chart.id"
        :chartId="chart.id"
      />
    </div>
  </div>
</template>
