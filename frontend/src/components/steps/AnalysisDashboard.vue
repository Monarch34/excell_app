<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useChartsStore } from '@/stores/charts';
import { useAnalysisStore } from '@/stores/analysis';
import { useAnalysisMetrics } from '@/composables/useAnalysisMetrics';
import { useAnalysisRunner } from '@/composables/analysis/useAnalysisRunner';
import type { ChartSpec } from '@/types/domain';
import type { ProcessResultValue } from '@/types/api';
import type { OrderableColumn } from '@/components/analysis/ColumnOrderPanel.vue';
import ChartFullscreenDialog from '@/components/analysis/ChartFullscreenDialog.vue';
import AnalysisStatePanel from '@/components/steps/analysis/AnalysisStatePanel.vue';
import AnalysisOrderSection from '@/components/steps/analysis/AnalysisOrderSection.vue';
import AnalysisChartSection from '@/components/steps/analysis/AnalysisChartSection.vue';
import ConfigLoadPanel from '@/components/config/ConfigLoadPanel.vue';
import { useConfigManagerStore } from '@/stores/configManager';
import { useConfigManagerStep } from '@/composables/config/useConfigManagerStep';
import AppPageHeader from '@/components/ui/AppPageHeader.vue';
import Button from 'primevue/button';

const datasetStore = useDatasetStore();
const columnsStore = useColumnsStore();
const derivedStore = useDerivedColumnsStore();
const chartsStore = useChartsStore();
const analysisStore = useAnalysisStore();
const configManagerStore = useConfigManagerStore();
const configStepVm = useConfigManagerStep();
const { runAnalysis } = useAnalysisRunner();

const { rows } = storeToRefs(datasetStore);
const { charts } = storeToRefs(chartsStore);
const { lastLoadedConfigName } = storeToRefs(configManagerStore);
const { processedData, hasResults, isAnalyzing, analysisError, results } = storeToRefs(analysisStore);
const { selectedColumnNames, columnOrder, parameterOrder, separators, separatorColor, matchingGroups } =
  storeToRefs(columnsStore);
const { computedMetrics } = useAnalysisMetrics();

const fullscreenVisible = ref(false);
const fullscreenChart = ref<ChartSpec | null>(null);
const showConfigControl = ref(false);

const sortedCharts = computed(() => {
  return [...charts.value].sort((a, b) => b.id.localeCompare(a.id));
});

const sourceRows = computed(() =>
  hasResults.value && processedData.value.length > 0 ? processedData.value : rows.value,
);

const allOrderableColumns = computed<OrderableColumn[]>(() => {
  const selected = selectedColumnNames.value;
  const derived = derivedStore.enabledColumns
    .filter((dc) => dc.type !== 'parameter')
    .map((dc) => dc.name);
  const names = [...selected, ...derived.filter((name) => !selected.includes(name))];

  if (columnOrder.value.length > 0) {
    const orderMap = new Map(columnOrder.value.map((name, index) => [name, index]));
    names.sort((a, b) => (orderMap.get(a) ?? 999) - (orderMap.get(b) ?? 999));
  }

  return names.map((name) => ({
    name,
    source: (derived.includes(name) ? 'derived' : 'original') as 'original' | 'derived',
  }));
});

const derivedParameterRows = computed(() => {
  const formulaRows = derivedStore.derivedColumns
    .filter((item) => item.type === 'parameter' && item.enabled)
    .map((item) => ({
      id: item.id,
      name: item.name,
      unit: item.unit || '',
      value: Object.prototype.hasOwnProperty.call(results.value, item.name)
        ? results.value[item.name]
        : null,
    }));

  const labeledAreaRows = computedMetrics.value.map((metric) => ({
    id: metric.id,
    name: metric.name,
    unit: '',
    value: metric.value,
  }));

  return [...formulaRows, ...labeledAreaRows];
});

const orderedDerivedParameterRows = computed(() => {
  const rowsByName = new Map(derivedParameterRows.value.map((row) => [row.name, row]));
  return parameterOrder.value.flatMap((name) => {
    const row = rowsByName.get(name);
    return row ? [row] : [];
  });
});

const previewRows = computed<Record<string, ProcessResultValue>[]>(() => {
  return sourceRows.value
    .slice(0, 10)
    .map((row) => row as Record<string, ProcessResultValue>);
});

watch(
  derivedParameterRows,
  (rows) => {
    const nextNames = rows.map((row) => row.name);
    const current = parameterOrder.value.filter((name) => nextNames.includes(name));
    for (const name of nextNames) {
      if (!current.includes(name)) current.push(name);
    }
    columnsStore.setParameterOrder(current);
  },
  { immediate: true },
);

const hasMounted = ref(false);

watch(
  lastLoadedConfigName,
  async () => {
    if (!hasMounted.value) return;
    if (!datasetStore.hasData) return;
    if (configManagerStore.validationResult?.valid === false) return;
    await runAnalysis();
  }
);

onMounted(async () => {
  hasMounted.value = true;
  columnsStore.syncOrderLayout(allOrderableColumns.value.map((column) => column.name));
  await runAnalysis();
});

function handleReorder(fromIndex: number, toIndex: number): void {
  columnsStore.reorderColumns(fromIndex, toIndex);
}

function handleToggleSeparator(index: number): void {
  columnsStore.toggleSeparator(index);
}

function handleSeparatorColorChange(color: string): void {
  columnsStore.setSeparatorColor(color);
}

function handleCreateMatchingGroup(): void {
  columnsStore.createMatchingGroup();
}

function handleDeleteMatchingGroup(groupId: string): void {
  columnsStore.deleteMatchingGroup(groupId);
}

function handleUpdateMatchingGroup(groupId: string, patch: { name?: string; color?: string }): void {
  columnsStore.updateMatchingGroup(groupId, patch);
}

function handleSetMatchingGroupColumns(groupId: string, columns: string[]): void {
  columnsStore.setMatchingGroupColumns(
    groupId,
    columns,
    allOrderableColumns.value.map((column) => column.name),
  );
}

function handleReorderParameters(fromIndex: number, toIndex: number): void {
  columnsStore.reorderParameters(fromIndex, toIndex);
}

function openFullscreen(chart: ChartSpec): void {
  fullscreenChart.value = chart;
  fullscreenVisible.value = true;
}

async function rerunAnalysis(): Promise<void> {
  await runAnalysis();
}

const emit = defineEmits<{
  goToCharts: [];
}>();
</script>

<template>
  <div class="step-shell">
    <AppPageHeader class="ui-analysis-header" icon="pi-chart-bar" title="Analysis Dashboard">
      <Button
        label="Re-run Analysis"
        icon="pi pi-refresh"
        severity="secondary"
        outlined
        :loading="isAnalyzing"
        @click="rerunAnalysis"
      />
    </AppPageHeader>
    <p class="ui-muted-hint ui-step-intro">
      Inspect charts, organize derived parameters, and finalize export column order.
    </p>

    <AnalysisStatePanel
      v-if="isAnalyzing || !!analysisError"
      :loading="isAnalyzing"
      :error="analysisError"
      @retry="rerunAnalysis"
    />

    <div v-else class="ui-analysis-dashboard-body">
      <!-- Column Order Panel (collapsible) -->
      <AnalysisOrderSection
        class="ui-analysis-order-section"
        :parameterRows="orderedDerivedParameterRows"
        :columns="allOrderableColumns"
        :separators="separators"
        :separatorColor="separatorColor"
        :matchingGroups="matchingGroups"
        :previewRows="previewRows"
        @reorderParameters="handleReorderParameters"
        @reorder="handleReorder"
        @toggleSeparator="handleToggleSeparator"
        @updateSeparatorColor="handleSeparatorColorChange"
        @createMatchingGroup="handleCreateMatchingGroup"
        @deleteMatchingGroup="handleDeleteMatchingGroup"
        @updateMatchingGroup="handleUpdateMatchingGroup"
        @setMatchingGroupColumns="handleSetMatchingGroupColumns"
      />

      <div v-if="charts.length === 0" class="step-empty text-center ui-analysis-empty">
        <i class="pi pi-chart-bar text-4xl text-color-secondary ui-analysis-empty-icon"></i>
        <p class="text-color-secondary">No charts defined yet. Go to Charts &amp; Area to add chart definitions.</p>
        <Button
          label="Go to Charts & Area"
          icon="pi pi-arrow-right"
          severity="primary"
          size="small"
          class="ui-analysis-empty-cta"
          @click="emit('goToCharts')"
        />
      </div>

      <!-- Charts -->
      <div class="ui-analysis-chart-list">
        <AnalysisChartSection
          v-for="chart in sortedCharts"
          :key="chart.id"
          :chart="chart"
          :data="sourceRows as unknown as Record<string, unknown>[]"
          @fullscreen="openFullscreen(chart)"
        />
      </div>
    </div>

    <!-- Fullscreen Dialog -->
    <ChartFullscreenDialog
      v-model:visible="fullscreenVisible"
      :chart="fullscreenChart"
      :data="(sourceRows as unknown as Record<string, unknown>[])"
    />
  </div>
</template>
