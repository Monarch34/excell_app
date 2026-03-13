<script setup lang="ts">
import { computed, defineAsyncComponent, ref } from 'vue';
import { storeToRefs } from 'pinia';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';
import ChartAnnotationDialog from '@/components/steps/charts/ChartAnnotationDialog.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import type { ChartSpec } from '@/types/domain';
import { useConfirmDialog } from '@/composables/useConfirmDialog';
import { useDatasetStore } from '@/stores/dataset';
import { useAnalysisStore } from '@/stores/analysis';
import { useChartsStore } from '@/stores/charts';
import { useColumnsStore } from '@/stores/columns';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';

const AsyncErrorFallback = { template: '<div class="text-sm ui-color-error p-2">Failed to load component</div>' };
const ChartDefinitionForm = defineAsyncComponent({
  loader: () => import('@/components/charts/ChartDefinitionForm.vue'),
  errorComponent: AsyncErrorFallback,
  timeout: 10000,
});
const ChartRenderer = defineAsyncComponent({
  loader: () => import('@/components/charts/ChartRenderer.vue'),
  errorComponent: AsyncErrorFallback,
  timeout: 10000,
});

const props = defineProps<{
  chartId: string;
}>();

const datasetStore = useDatasetStore();
const analysisStore = useAnalysisStore();
const chartsStore = useChartsStore();
const columnsStore = useColumnsStore();
const derivedStore = useDerivedColumnsStore();
const { rows } = storeToRefs(datasetStore);
const { processedData } = storeToRefs(analysisStore);
const { charts, chartStates } = storeToRefs(chartsStore);

const chart = computed(() => charts.value.find((value) => value.id === props.chartId) || null);

const chartData = computed(() =>
  processedData.value.length > 0 ? processedData.value : rows.value,
);

const availableColumns = computed(() => {
  const selected = columnsStore.selectedColumnNames;
  const derived = derivedStore.enabledColumns.map((column) => column.name);
  return Array.from(new Set([...selected, ...derived]));
});

const isOpen = computed(() => {
  const state = chartStates.value[props.chartId];
  if (state?.isOpen !== undefined) return state.isOpen;
  return charts.value[0]?.id === props.chartId;
});

const chartColumnsExist = computed(() => {
  const currentChart = chart.value;
  if (!currentChart?.chartType) return false;
  if (!currentChart.xColumn || currentChart.yColumns.length === 0) return false;
  if (chartData.value.length === 0) return false;

  const firstRow = chartData.value[0];
  const xExists = currentChart.xColumn in firstRow;
  const yExists = currentChart.yColumns.every((column) => column in firstRow);
  return xExists && yExists;
});

const isAnnotationDialogOpen = ref(false);
const annotationText = ref('');
const pendingPoint = ref<{ x: number; y: number } | null>(null);

const { confirmDelete } = useConfirmDialog();

function toggleOpen(): void {
  chartsStore.updateChartState(props.chartId, { isOpen: !isOpen.value });
}

function handleUpdate(updates: Partial<ChartSpec>): void {
  chartsStore.updateChart(props.chartId, updates);
}

function handleDelete() {
  const chartName = chart.value?.title || 'Untitled Chart';
  confirmDelete(chartName, () => {
    chartsStore.removeChart(props.chartId);
  });
}

function handleChartClick(point: { x: number; y: number }): void {
  pendingPoint.value = { x: point.x, y: point.y };
  annotationText.value = '';
  isAnnotationDialogOpen.value = true;
}

function saveAnnotation(): void {
  if (!pendingPoint.value) return;
  const text = annotationText.value.trim();
  if (!text) return;
  chartsStore.addAnnotation(props.chartId, pendingPoint.value.x, pendingPoint.value.y, text);
  isAnnotationDialogOpen.value = false;
}

function removeAnnotation(index: number): void {
  chartsStore.removeAnnotation(props.chartId, index);
}
</script>

<template>
  <AppSurfacePanel v-if="chart" as="section" tone="chart" class="ui-chart-card" interactive>
    <div
      class="ui-chart-card-header ui-chart-card-header-row"
      :class="{ 'ui-chart-card-header--collapsed': !isOpen }"
    >
      <button
        type="button"
        class="ui-chart-card-toggle"
        :aria-expanded="isOpen"
        :aria-label="`Toggle chart ${chart.title || 'Untitled Chart'}`"
        @click="toggleOpen"
      >
        <div class="ui-chart-card-title-wrap">
          <i class="pi pi-chart-line text-primary" aria-hidden="true"></i>
          <span class="font-bold ui-chart-card-title">{{ chart.title || 'Untitled Chart' }}</span>
        </div>
        <i class="pi ui-action-icon-btn" :class="isOpen ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
      </button>
      <Button
        icon="pi pi-trash"
        severity="danger"
        text
        size="small"
        class="ui-action-icon-btn ui-delete-btn"
        aria-label="Delete chart"
        @click="handleDelete"
      />
    </div>

    <transition name="ui-chart-expand">
      <div v-if="isOpen" class="ui-chart-card-body">
        <ChartDefinitionForm
          :chart="chart"
          :availableColumns="availableColumns"
          @update="handleUpdate"
          class="ui-chart-form-spacing"
        />

        <div class="ui-chart-divider"></div>

        <div class="ui-chart-preview-header">
          <div class="ui-chart-preview-label">
            <i class="pi pi-eye text-color-secondary"></i>
            <span class="font-medium text-color">Preview</span>
          </div>
          <Tag
            v-if="chartColumnsExist"
            value="Ready"
            severity="success"
            class="text-xs"
          />
          <Tag
            v-else-if="!chart.xColumn || chart.yColumns.length === 0"
            value="Needs X/Y"
            severity="warning"
            class="text-xs"
          />
          <Tag
            v-else
            value="Needs Analysis"
            severity="info"
            class="text-xs"
          />
        </div>

        <div v-if="chartColumnsExist">
          <ChartRenderer
            :spec="chart"
            :data="chartData"
            height="380px"
            @clickPoint="handleChartClick"
          />
          <div v-if="chart.annotations && chart.annotations.length > 0" class="ui-chart-annotation-list ui-chart-annotation-list--spaced">
            <span v-for="(anno, idx) in chart.annotations" :key="idx" class="ui-chart-annotation-chip">
              <i class="pi pi-tag text-primary"></i>
              <span>{{ anno.text }} ({{ anno.x.toFixed(2) }}, {{ anno.y.toFixed(2) }})</span>
              <i class="pi pi-times cursor-pointer ui-color-error" @click="removeAnnotation(idx)"></i>
            </span>
          </div>
          <div class="text-xs text-color-secondary ui-chart-preview-tip">
            Tip: click the chart to add an annotation.
          </div>
        </div>
        <div v-else-if="!chart.chartType" class="ui-chart-empty-preview ui-chart-empty-preview--simple text-center text-color-secondary text-sm">
          Select a chart type to configure this chart
        </div>
        <div v-else-if="!chart.xColumn || chart.yColumns.length === 0" class="ui-chart-empty-preview ui-chart-empty-preview--simple text-center text-color-secondary text-sm">
          Configure X and Y columns to see chart preview
        </div>
        <div v-else class="ui-chart-empty-preview ui-chart-empty-preview--analysis text-center">
          <i class="pi pi-info-circle text-primary ui-chart-empty-analysis-icon"></i>
          <p class="text-color-secondary text-sm ui-chart-empty-analysis-text">
            Chart preview will be available after running analysis.
            <br />
            <span class="text-xs">Columns <strong>{{ chart.xColumn }}</strong> and <strong>{{ chart.yColumns.join(', ') }}</strong> need to be computed first.</span>
          </p>
        </div>
      </div>
    </transition>

    <ChartAnnotationDialog
      :visible="isAnnotationDialogOpen"
      :text="annotationText"
      @update:visible="(visible) => (isAnnotationDialogOpen = visible)"
      @update:text="(value) => (annotationText = value)"
      @save="saveAnnotation"
    />
  </AppSurfacePanel>
</template>
