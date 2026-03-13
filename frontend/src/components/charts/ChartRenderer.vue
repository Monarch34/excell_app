<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useDatasetStore } from '@/stores/dataset';
import type { ChartSpec } from '@/types/domain';
import { buildChartLayout, buildChartTraces } from './chartRendererUtils';

type PlotlyPoint = {
  x: unknown;
  y: unknown;
};

type PlotlyClickEvent = {
  points?: PlotlyPoint[];
};

const props = defineProps<{
  spec: ChartSpec;
  data: Record<string, unknown>[];
  height?: string;
}>();

const emit = defineEmits<{
  relayout: [event: unknown];
  clickPoint: [point: { x: number; y: number }];
  renderError: [error: string];
}>();

const datasetStore = useDatasetStore();
const chartContainer = ref<HTMLDivElement | null>(null);
const renderError = ref<string | null>(null);
let Plotly: typeof import('plotly.js-dist-min') | null = null;
let hasInitializedPlot = false;
let eventsBound = false;
let renderQueued = false;
let unmounted = false;

const plotConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['sendDataToCloud', 'toImage'],
};

async function loadPlotly() {
  Plotly = await import('plotly.js-dist-min');
}

function isPlotlyHTMLElement(el: HTMLDivElement | null): el is PlotlyHTMLElement {
  return !!el && typeof (el as PlotlyHTMLElement).on === 'function';
}

function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function bindPlotlyEvents(root: PlotlyHTMLElement) {
  if (eventsBound) return;

  root.on('plotly_relayout', (event: unknown) => {
    emit('relayout', event);
  });

  root.on('plotly_click', (raw: unknown) => {
    const data = raw as PlotlyClickEvent;
    const point = data.points?.[0];
    if (!point) return;

    const x = toNumber(point.x);
    const y = toNumber(point.y);
    if (x === null || y === null) return;

    emit('clickPoint', { x, y });
  });

  eventsBound = true;
}

async function renderChart() {
  if (unmounted || !chartContainer.value) return;
  if (!Plotly) await loadPlotly();
  if (unmounted || !Plotly || !chartContainer.value) return;

  try {
    const traces = buildChartTraces(props.spec, props.data);
    const layout = buildChartLayout(props.spec, props.data, datasetStore.metadata.units);

    if (!hasInitializedPlot) {
      await Plotly.newPlot(chartContainer.value, traces, layout, plotConfig);
      hasInitializedPlot = true;

      if (isPlotlyHTMLElement(chartContainer.value)) {
        bindPlotlyEvents(chartContainer.value);
      }
      renderError.value = null;
      return;
    }

    await Plotly.react(chartContainer.value, traces, layout, plotConfig);
    renderError.value = null;
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Chart rendering failed';
    renderError.value = message;
    emit('renderError', message);
  }
}

function queueRender() {
  if (renderQueued) return;
  renderQueued = true;

  Promise.resolve().then(async () => {
    renderQueued = false;
    if (unmounted) return;
    await nextTick();
    await renderChart();
  });
}

onMounted(async () => {
  await loadPlotly();
  queueRender();
});

onBeforeUnmount(() => {
  unmounted = true;
  renderQueued = false;
  if (chartContainer.value && Plotly) {
    Plotly.purge(chartContainer.value);
  }
  hasInitializedPlot = false;
  eventsBound = false;
});

watch(() => props.data, () => {
  queueRender();
});

const specFingerprint = computed(() => JSON.stringify(props.spec));
watch(specFingerprint, () => { queueRender(); });

const unitsFingerprint = computed(() => JSON.stringify(datasetStore.metadata.units));
watch(unitsFingerprint, () => { queueRender(); });

const ariaLabel = computed(() => {
  const chartTitle = props.spec.title || 'Chart';
  const chartType = props.spec.chartType || 'chart';
  const yColumnsText = props.spec.yColumns.join(', ') || 'data';
  const xColumn = props.spec.xColumn || 'values';
  return `${chartTitle}: ${chartType} showing ${yColumnsText} vs ${xColumn}`;
});
</script>

<template>
  <div v-if="renderError" class="ui-chart-render-error" :style="{ height: height || '400px' }">
    <i class="pi pi-exclamation-triangle ui-chart-render-error-icon"></i>
    <span class="text-sm ui-chart-render-error-text">{{ renderError }}</span>
  </div>
  <div
    v-show="!renderError"
    ref="chartContainer"
    role="img"
    :aria-label="ariaLabel"
    class="ui-chart-renderer"
    :style="{ height: height || '400px' }"
  ></div>
</template>
