import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { AreaMode, AreaSpec, ChartSpec, ChartState } from '@/shared/types/domain';
import {
  CHART_UI_STATE_STORAGE_KEY,
  MAX_CHARTS,
  computeNextIdSeed,
  createChartId,
  normalizeChartConfig,
  readChartUiState,
  writeChartUiState,
} from './charts.helpers';

let nextId = 1;

/**
 * Charts store - manages chart definitions and area-under-curve settings.
 */
export const useChartsStore = defineStore('charts', () => {
  const charts = ref<ChartSpec[]>([]);
  const chartStates = ref<Record<string, ChartState>>({});

  function generateId(): string {
    const result = createChartId(nextId);
    nextId = result.next;
    return result.id;
  }

  function loadUiState() {
    try {
      chartStates.value = readChartUiState(localStorage.getItem(CHART_UI_STATE_STORAGE_KEY));
    } catch {
      // ignore localStorage errors
    }
  }

  function saveUiState() {
    try {
      const minimal = writeChartUiState(chartStates.value);
      localStorage.setItem(CHART_UI_STATE_STORAGE_KEY, JSON.stringify(minimal));
    } catch {
      // ignore localStorage errors
    }
  }

  const count = computed(() => charts.value.length);
  const canAdd = computed(() => charts.value.length < MAX_CHARTS);
  const chartsWithArea = computed(() =>
    charts.value.filter((chart) => chart.chartType === 'area' && chart.areaSpec !== null)
  );
  const sortedCharts = computed(() =>
    [...charts.value].sort((a, b) => b.id.localeCompare(a.id))
  );

  function addChart(partial?: Partial<ChartSpec>): string | null {
    if (!canAdd.value) return null;

    const id = generateId();
    const chart: ChartSpec = {
      id,
      title: partial?.title || `Chart ${count.value + 1}`,
      xColumn: partial?.xColumn || '',
      yColumns: partial?.yColumns || [],
      xAxisLabel: partial?.xAxisLabel || '',
      yAxisLabel: partial?.yAxisLabel || '',
      chartType: partial?.chartType ?? null,
      baselineSpec: partial?.baselineSpec ?? null,
      areaSpec: partial?.areaSpec || null,
      lineColor: partial?.lineColor || null,
      fillColor: partial?.fillColor || null,
      fillOpacity: partial?.fillOpacity ?? 0.4,
      lineWidth: partial?.lineWidth ?? null,
      markerSize: partial?.markerSize ?? null,
    };

    charts.value.unshift(chart);

    for (const key of Object.keys(chartStates.value)) {
      chartStates.value[key] = { ...chartStates.value[key], isOpen: false };
    }

    chartStates.value[id] = {
      chartId: id,
      xRange: null,
      yRange: null,
      hiddenTraces: [],
      isOpen: true,
    };
    saveUiState();
    return id;
  }

  function addAnnotation(chartId: string, x: number, y: number, text: string) {
    const chart = charts.value.find((value) => value.id === chartId);
    if (!chart) return;
    if (!chart.annotations) chart.annotations = [];
    chart.annotations.push({ x, y, text, showArrow: true });
  }

  function removeAnnotation(chartId: string, index: number) {
    const chart = charts.value.find((value) => value.id === chartId);
    if (!chart?.annotations) return;
    chart.annotations.splice(index, 1);
  }

  function updateChart(id: string, updates: Partial<ChartSpec>) {
    const chart = charts.value.find((value) => value.id === id);
    if (chart) Object.assign(chart, updates);
  }

  function removeChart(id: string) {
    const index = charts.value.findIndex((value) => value.id === id);
    if (index < 0) return;
    charts.value.splice(index, 1);
    delete chartStates.value[id];
  }

  function setAreaSpec(chartId: string, areaSpec: AreaSpec | null) {
    const chart = charts.value.find((value) => value.id === chartId);
    if (chart) chart.areaSpec = areaSpec;
  }

  function enableArea(chartId: string, mode: AreaMode, xColumn: string, yColumn: string) {
    setAreaSpec(chartId, {
      mode,
      baseline: 0,
      baselineAxis: 'y',
      xColumn,
      yColumn,
    });
  }

  function disableArea(chartId: string) {
    setAreaSpec(chartId, null);
  }

  function updateChartState(chartId: string, state: Partial<ChartState>) {
    const existing = chartStates.value[chartId] || {
      chartId,
      xRange: null,
      yRange: null,
      hiddenTraces: [],
    };
    chartStates.value[chartId] = { ...existing, ...state };
    saveUiState();
  }

  function getChartById(id: string): ChartSpec | undefined {
    return charts.value.find((chart) => chart.id === id);
  }

  function loadFromConfig(configCharts: ChartSpec[]) {
    charts.value = normalizeChartConfig(configCharts, generateId);
    chartStates.value = {};
    loadUiState();

    if (charts.value.length > 0) {
      const firstId = charts.value[0].id;
      for (const chart of charts.value) {
        const existing = chartStates.value[chart.id];
        chartStates.value[chart.id] = {
          chartId: chart.id,
          xRange: null,
          yRange: null,
          hiddenTraces: [],
          isOpen: existing?.isOpen ?? chart.id === firstId,
        };
      }
    }

    saveUiState();
    nextId = computeNextIdSeed(configCharts, nextId);
  }

  function reset() {
    charts.value = [];
    chartStates.value = {};
    nextId = 1;
    try {
      localStorage.removeItem(CHART_UI_STATE_STORAGE_KEY);
    } catch {
      // ignore localStorage errors
    }
  }

  loadUiState();

  return {
    charts,
    chartStates,
    count,
    canAdd,
    chartsWithArea,
    sortedCharts,
    addChart,
    updateChart,
    removeChart,
    addAnnotation,
    removeAnnotation,
    setAreaSpec,
    enableArea,
    disableArea,
    updateChartState,
    getChartById,
    loadFromConfig,
    reset,
    MAX_CHARTS,
  };
});
