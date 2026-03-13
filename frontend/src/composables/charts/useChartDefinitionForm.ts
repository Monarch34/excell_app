import { computed, ref } from 'vue';
import type { AreaSpec, BaselineSpec, ChartSpec, ChartType } from '@/types/domain';
import { CHART_COLOR_PRESETS } from '@/constants/chartColors';

export function useChartDefinitionForm(
  chart: ChartSpec,
  update: (updates: Partial<ChartSpec>) => void
) {
  function normalizeHexColorInput(input: string | undefined): string | null | undefined {
    if (!input) return null;
    const cleaned = input.replace(/[^0-9a-fA-F]/g, '').slice(0, 6);
    if (!cleaned) return null;
    if (cleaned.length !== 6) return undefined;
    return `#${cleaned.toUpperCase()}`;
  }

  const chartTypeOptions = [
    { label: 'Line', value: 'line' as ChartType, icon: 'pi pi-chart-line' },
    { label: 'Scatter', value: 'scatter' as ChartType, icon: 'pi pi-circle' },
    { label: 'Area', value: 'area' as ChartType, icon: 'pi pi-chart-bar' },
  ];

  const colorPresets = CHART_COLOR_PRESETS;
  const configDialogOpen = ref(false);

  const strokeLabel = computed(() => (chart.chartType === 'scatter' ? 'Marker Color' : 'Line Color'));
  const styleTitle = computed(() => {
    if (chart.chartType === 'scatter') return 'Scatter Style';
    if (chart.chartType === 'area') return 'Area Style';
    return 'Line Style';
  });
  function updateAreaSpec(updates: Partial<AreaSpec>) {
    const current: AreaSpec = chart.areaSpec || {
      mode: 'total',
      baseline: 0,
      baselineAxis: 'y',
      xColumn: chart.xColumn,
      yColumn: chart.yColumns[0] || '',
    };
    update({ areaSpec: { ...current, ...updates } });
  }

  function updateBaselineSpec(updates: Partial<BaselineSpec>) {
    const current: BaselineSpec = chart.baselineSpec || {
      xBaseline: 0,
      yBaseline: 0,
      regions: [],
    };
    update({ baselineSpec: { ...current, ...updates } });
  }

  function handleTypeSelect(value: ChartType) {
    const existingAreaSpec = chart.areaSpec;
    if (value === 'area') {
      const current: AreaSpec = existingAreaSpec || {
        mode: 'total',
        baseline: 0,
      baselineAxis: 'y',
      xColumn: chart.xColumn,
      yColumn: chart.yColumns[0] || '',
    };
      update({ chartType: value, areaSpec: current });
      return;
    }
    update({ chartType: value, areaSpec: existingAreaSpec ?? null });
  }

  function handleLineColorChange(hex: string | undefined) {
    const color = normalizeHexColorInput(hex);
    if (color === undefined) return;
    update({ lineColor: color });
  }

  function handleFillColorChange(hex: string | undefined) {
    const color = normalizeHexColorInput(hex);
    if (color === undefined) return;
    update({ fillColor: color });
  }

  function applyLineColor(color: string) {
    const normalized = normalizeHexColorInput(color);
    if (normalized === undefined) return;
    update({ lineColor: normalized });
  }

  function applyFillColor(color: string) {
    const normalized = normalizeHexColorInput(color);
    if (normalized === undefined) return;
    update({ fillColor: normalized });
  }

  function resetStyle() {
    if (chart.chartType === 'scatter') {
      update({ lineColor: null, markerSize: 8 });
      return;
    }
    if (chart.chartType === 'area') {
      update({
        lineColor: null,
        fillColor: null,
        fillOpacity: 0.4,
        lineWidth: 2,
      });
      return;
    }
    update({ lineColor: null, lineWidth: 2 });
  }

  function resetAxes() {
    update({
      xColumn: '',
      yColumns: [],
      xAxisLabel: '',
      yAxisLabel: '',
    });
  }

  function stripHash(color: string | null): string | undefined {
    if (!color) return undefined;
    return color.replace('#', '');
  }

  return {
    chartTypeOptions,
    colorPresets,
    configDialogOpen,
    strokeLabel,
    styleTitle,
    updateAreaSpec,
    updateBaselineSpec,
    handleTypeSelect,
    handleLineColorChange,
    handleFillColorChange,
    applyLineColor,
    applyFillColor,
    resetStyle,
    resetAxes,
    stripHash,
  };
}
