import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useDatasetStore } from '@/stores/dataset';
import { useChartsStore } from '@/stores/charts';
import { useAnalysisStore } from '@/stores/analysis';
import { calculateMetrics as apiCalculateMetrics } from '@/services/chartsApi';
import type { AnalysisMetric, ChartSpec } from '@/shared/types/domain';
import type { ChartMetrics, MetricsChartSpec } from '@/shared/types/api';
import { logError } from '@/utils/errors';

const REQUEST_DEBOUNCE_MS = 300;

function isAbortLikeError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const err = error as { name?: string; code?: string };
  return err.name === 'AbortError' || err.name === 'CanceledError' || err.code === 'ERR_CANCELED';
}

function isExpiredRunError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const maybeResponse = (error as { response?: { status?: number; data?: { detail?: string } } }).response;
  const status = maybeResponse?.status;
  const detail = maybeResponse?.data?.detail?.toLowerCase() || '';
  return status === 404 || (status === 422 && detail.includes('expired analysis run id'));
}

/**
 * Composable that fetches analysis metrics from backend.
 * Uses processing run id when available to avoid sending large datasets repeatedly.
 */
export function useAnalysisMetrics() {
  const datasetStore = useDatasetStore();
  const chartsStore = useChartsStore();
  const analysisStore = useAnalysisStore();

  const { rows } = storeToRefs(datasetStore);
  const { charts } = storeToRefs(chartsStore);
  const { runId, processedData, hasResults } = storeToRefs(analysisStore);

  const backendMetrics = ref<ChartMetrics[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const requestController = ref<AbortController | null>(null);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let requestVersion = 0;

  function clearDebounce() {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
  }

  function cancelInFlight() {
    requestController.value?.abort();
    requestController.value = null;
  }

  /**
   * Convert frontend ChartSpec to backend MetricsChartSpec format.
   */
  function toMetricsChartSpec(chart: ChartSpec): MetricsChartSpec {
    return {
      id: chart.id,
      title: chart.title || '',
      x_column: chart.xColumn,
      y_columns: chart.yColumns,
      chart_type: (chart.chartType ?? 'line') as 'line' | 'scatter' | 'area',
      area_spec: chart.areaSpec
        ? {
            mode: chart.areaSpec.mode as 'positive' | 'negative' | 'total',
            baseline: chart.areaSpec.baseline || 0,
            baseline_axis: chart.areaSpec.baselineAxis,
            x_column: chart.areaSpec.xColumn,
            y_column: chart.areaSpec.yColumn,
            label: chart.areaSpec.label?.trim() || undefined,
          }
        : null,
      baseline_spec: chart.baselineSpec
        ? {
            x_baseline: chart.baselineSpec.xBaseline || 0,
            y_baseline: chart.baselineSpec.yBaseline || 0,
            regions: chart.baselineSpec.regions || [],
          }
        : null,
    };
  }

  const chartSpecs = computed(() =>
    charts.value
      .filter((chart) => (
        chart.chartType === 'area'
        && chart.xColumn
        && chart.yColumns.length > 0
        && Boolean(chart.areaSpec?.label?.trim())
      ))
      .map(toMetricsChartSpec)
  );

  const chartSignature = computed(() => JSON.stringify(chartSpecs.value));
  const sourceRows = computed(() => (
    hasResults.value && processedData.value.length > 0 ? processedData.value : rows.value
  ));

  /**
   * Convert backend ChartMetrics to frontend AnalysisMetric format.
   */
  function toAnalysisMetrics(chartMetrics: ChartMetrics, chart: ChartSpec): AnalysisMetric[] {
    const metrics: AnalysisMetric[] = [];
    let id = 1;

    const customAreaLabel = chart.areaSpec?.label?.trim();
    if (chartMetrics.area_total !== null && customAreaLabel) {
      metrics.push({
        id: `${chartMetrics.chart_id}-area-${id++}`,
        chartId: chartMetrics.chart_id,
        name: customAreaLabel,
        value: chartMetrics.area_total,
        unit: '',
        computedAt: new Date().toISOString(),
      });
    }

    return metrics;
  }

  async function fetchMetrics() {
    if (chartSpecs.value.length === 0) {
      backendMetrics.value = [];
      return;
    }

    if (!runId.value && sourceRows.value.length === 0) {
      backendMetrics.value = [];
      return;
    }

    cancelInFlight();
    const controller = new AbortController();
    requestController.value = controller;

    const currentVersion = ++requestVersion;
    isLoading.value = true;
    error.value = null;

    try {
      const runIdValue = runId.value;
      const payload =
        runIdValue
          ? { run_id: runIdValue, charts: chartSpecs.value }
          : { data: sourceRows.value, charts: chartSpecs.value };

      const response = await apiCalculateMetrics(payload, controller.signal);
      if (controller.signal.aborted || currentVersion !== requestVersion) return;
      backendMetrics.value = response.metrics;
    } catch (e: unknown) {
      if (isExpiredRunError(e) && runId.value && sourceRows.value.length > 0) {
        try {
          analysisStore.setRunId(null);
          const fallbackResponse = await apiCalculateMetrics(
            { data: sourceRows.value, charts: chartSpecs.value },
            controller.signal,
          );
          if (controller.signal.aborted || currentVersion !== requestVersion) return;
          backendMetrics.value = fallbackResponse.metrics;
          return;
        } catch (fallbackError: unknown) {
          if (isAbortLikeError(fallbackError)) return;
          error.value = 'Failed to calculate metrics';
          logError(fallbackError, 'fetchMetrics:fallback');
          backendMetrics.value = [];
          return;
        }
      }
      if (isAbortLikeError(e)) return;
      error.value = 'Failed to calculate metrics';
      logError(e, 'fetchMetrics');
      backendMetrics.value = [];
    } finally {
      if (currentVersion === requestVersion) {
        isLoading.value = false;
      }
      if (requestController.value === controller) {
        requestController.value = null;
      }
    }
  }

  function scheduleFetch() {
    clearDebounce();
    debounceTimer = setTimeout(() => {
      void fetchMetrics();
    }, REQUEST_DEBOUNCE_MS);
  }

  watch([runId, chartSignature], () => {
    scheduleFetch();
  }, { immediate: true });

  watch(sourceRows, () => {
    if (!runId.value) {
      scheduleFetch();
    }
  });

  onBeforeUnmount(() => {
    clearDebounce();
    cancelInFlight();
  });

  const computedMetrics = computed<AnalysisMetric[]>(() => {
    const allMetrics: AnalysisMetric[] = [];

    for (const [metricIndex, backendMetric] of backendMetrics.value.entries()) {
      const chart = charts.value.find((item) => item.id === backendMetric.chart_id);
      if (!chart) continue;

      const normalized = toAnalysisMetrics(backendMetric, chart).map((metric) => ({
        ...metric,
        id: `${metric.id}-${metricIndex}`,
      }));
      allMetrics.push(...normalized);
    }

    return allMetrics;
  });

  return {
    computedMetrics,
    isLoading,
    error,
    refetch: fetchMetrics,
  };
}
