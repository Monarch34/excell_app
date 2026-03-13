import type { BaselineSpec, ChartSpec, ChartState } from '@/shared/types/domain';

export const CHART_UI_STATE_STORAGE_KEY = 'charts.ui.state';
export const MAX_CHARTS = 10;

export function createChartId(nextId: number): { id: string; next: number } {
  return {
    id: `chart-${String(nextId).padStart(3, '0')}`,
    next: nextId + 1,
  };
}

export function readChartUiState(raw: string | null): Record<string, ChartState> {
  if (!raw) return {};
  let parsed: Record<string, { isOpen?: boolean }>;
  try {
    parsed = JSON.parse(raw) as Record<string, { isOpen?: boolean }>;
  } catch {
    return {};
  }
  if (!parsed || typeof parsed !== 'object') return {};
  const state: Record<string, ChartState> = {};

  for (const [id, item] of Object.entries(parsed)) {
    state[id] = {
      chartId: id,
      xRange: null,
      yRange: null,
      hiddenTraces: [],
      isOpen: item.isOpen ?? undefined,
    };
  }
  return state;
}

export function writeChartUiState(state: Record<string, ChartState>): Record<string, { isOpen?: boolean }> {
  const minimal: Record<string, { isOpen?: boolean }> = {};
  for (const [id, value] of Object.entries(state)) {
    if (value.isOpen !== undefined) minimal[id] = { isOpen: value.isOpen };
  }
  return minimal;
}

export function normalizeChartConfig(
  configCharts: ChartSpec[],
  createId: () => string
): ChartSpec[] {
  const seenIds = new Set<string>();

  return configCharts.map((chart, index) => {
    let id = (chart.id || '').trim();
    if (!id) id = createId();
    if (seenIds.has(id)) id = `${id}-${index + 1}`;
    seenIds.add(id);

    const chartType =
      chart.chartType === 'line' || chart.chartType === 'scatter' || chart.chartType === 'area'
        ? chart.chartType
        : chart.areaSpec
          ? 'area'
          : null;

    const areaSpec = chart.areaSpec
      ? { ...chart.areaSpec, baselineAxis: chart.areaSpec.baselineAxis ?? 'y' }
      : null;

    const baselineSpec: BaselineSpec | null = chart.baselineSpec
      ? {
          xBaseline: chart.baselineSpec.xBaseline ?? 0,
          yBaseline: chart.baselineSpec.yBaseline ?? 0,
          regions: chart.baselineSpec.regions ?? [],
        }
      : null;

    return {
      ...chart,
      id,
      chartType,
      baselineSpec,
      areaSpec,
    };
  });
}

export function computeNextIdSeed(configCharts: ChartSpec[], currentSeed: number): number {
  const maxNum = configCharts.reduce((max, chart) => {
    const match = chart.id.match(/chart-(\d+)/);
    return match ? Math.max(max, parseInt(match[1], 10)) : max;
  }, 0);

  if (maxNum >= currentSeed) return maxNum + 1;
  return currentSeed;
}
