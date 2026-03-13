import { DEFAULT_CHART_COLOR } from '@/constants/chartColors';
import { filterRowsForChartBaseline } from '@/domain/chartBaselineFilter';
import type { ChartSpec } from '@/types/domain';

type ChartRow = Record<string, unknown>;

function getCSSVariable(varName: string, fallback = DEFAULT_CHART_COLOR): string {
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return value || fallback;
}

function hexToRgba(hex: string, alpha: number): string {
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) {
    return `rgba(100, 116, 139, ${alpha})`;
  }
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function niceStep(target: number): number {
  if (!Number.isFinite(target) || target <= 0) return 1;
  const power = 10 ** Math.floor(Math.log10(target));
  const normalized = target / power;
  if (normalized <= 1) return 1 * power;
  if (normalized <= 2) return 2 * power;
  if (normalized <= 5) return 5 * power;
  return 10 * power;
}

function roundToStep(value: number, step: number): number {
  if (!Number.isFinite(value) || !Number.isFinite(step) || step <= 0) return value;
  const rounded = Math.round((value / step) * 1e8) / 1e8;
  return rounded * step;
}

function toNumericRange(range: unknown): [number, number] | undefined {
  if (!Array.isArray(range) || range.length !== 2) return undefined;
  const low = Number(range[0]);
  const high = Number(range[1]);
  if (!Number.isFinite(low) || !Number.isFinite(high)) return undefined;
  return [Math.min(low, high), Math.max(low, high)];
}

function expandRange(range: [number, number], factor = 0.12): [number, number] {
  const [low, high] = range;
  const span = high - low;
  const base = span > 0 ? span : Math.max(Math.abs(high), Math.abs(low), 1);
  const pad = base * factor;
  let nextLow = low - pad;
  let nextHigh = high + pad;
  if (low >= 0 && nextLow < 0) nextLow = 0;
  if (high <= 0 && nextHigh > 0) nextHigh = 0;
  return [nextLow, nextHigh];
}

function safeMin(values: number[]): number {
  let min = Infinity;
  for (const v of values) if (v < min) min = v;
  return min;
}

function safeMax(values: number[]): number {
  let max = -Infinity;
  for (const v of values) if (v > max) max = v;
  return max;
}

function buildScopedRange(values: number[]): [number, number] | undefined {
  if (values.length === 0) return undefined;
  const min = safeMin(values);
  const max = safeMax(values);
  if (!Number.isFinite(min) || !Number.isFinite(max)) return undefined;

  const span = Math.abs(max - min);
  const step = niceStep((span || Math.max(Math.abs(max), 1)) / 5);

  let low: number;
  let high: number;

  if (span === 0) {
    low = min - 2 * step;
    high = max + 2 * step;
  } else {
    // Add one "nice step" on each side so the graph has visible breathing room.
    low = Math.floor(min / step) * step - step;
    high = Math.ceil(max / step) * step + step;
  }

  if (min >= 0 && low < 0) low = 0;
  if (max <= 0 && high > 0) high = 0;
  if (low === high) high = low + step;

  return [roundToStep(low, step), roundToStep(high, step)];
}

export function buildChartTraces(
  spec: ChartSpec,
  data: ChartRow[]
): Array<Record<string, unknown>> {
  if (!spec.chartType) return [];
  const shouldFill = spec.chartType === 'area';

  return spec.yColumns.map((yCol) => {
    const filtered = filterRowsForChartBaseline(data, {
      ...spec,
      yColumns: [yCol],
    });
    const xValues = filtered.map((row) => Number(row[spec.xColumn]));
    const yValues = filtered.map((row) => Number(row[yCol]));

    const trace: Record<string, unknown> = {
      x: xValues,
      y: yValues,
      name: yCol,
      type: 'scatter',
    };

    if (shouldFill) {
      if (xValues.length >= 2) {
        trace.fill = 'tozeroy';
        trace.mode = 'lines';
        if (spec.fillColor) {
          const opacity = spec.fillOpacity ?? 0.4;
          trace.fillcolor = hexToRgba(spec.fillColor, opacity);
        } else {
          // Keep area visible without forcing Plotly's default blue-tinted fill.
          const fallbackFillBase = spec.lineColor || getCSSVariable('--text-color-secondary', '#64748b');
          const fallbackFillOpacity = Math.min(spec.fillOpacity ?? 0.4, 0.18);
          trace.fillcolor = hexToRgba(fallbackFillBase, fallbackFillOpacity);
        }
        trace.line = {
          color: spec.lineColor || getCSSVariable('--primary-600'),
          width: spec.lineWidth ?? 2,
          simplify: false,
        };
      } else {
        trace.mode = 'markers';
        trace.marker = {
          color: spec.lineColor || getCSSVariable('--primary-600'),
          size: Math.max(6, spec.markerSize ?? 8),
        };
      }
    } else if (spec.chartType === 'line') {
      trace.mode = 'lines';
      trace.line = {
        color: spec.lineColor || getCSSVariable('--primary-600'),
        width: spec.lineWidth ?? 2,
        simplify: false,
      };
    } else {
      trace.mode = 'markers';
      trace.marker = {
        color: spec.lineColor || getCSSVariable('--primary-600'),
        size: spec.markerSize ?? 8,
      };
    }

    return trace;
  });
}

export function buildChartLayout(
  spec: ChartSpec,
  data: ChartRow[],
  units: Record<string, string>
): Record<string, unknown> {
  const chartPaperBg = getCSSVariable('--chart-paper-bg', 'rgba(0,0,0,0)');
  const chartPlotBg = getCSSVariable('--chart-plot-bg', 'rgba(0,0,0,0)');
  const chartMargin = {
    topWithTitle: 48,
    topNoTitle: 28,
    right: 28,
    bottom: 60,
    left: 72,
  };

  if (!spec.chartType) {
    return {
      margin: { t: chartMargin.topNoTitle, r: chartMargin.right, b: chartMargin.bottom, l: chartMargin.left },
      template: 'none',
      paper_bgcolor: chartPaperBg,
      plot_bgcolor: chartPlotBg,
      font: { color: getCSSVariable('--text-color-secondary') },
      showlegend: false,
      autosize: true,
    };
  }

  const hasAreaSpec = spec.chartType === 'area' && spec.areaSpec !== null;

  const getLabelWithUnit = (colName: string) => {
    const unit = units[colName];
    return unit ? `${colName} (${unit})` : colName;
  };

  const xaxis: Record<string, unknown> = {
    title: spec.xAxisLabel?.trim() || getLabelWithUnit(spec.xColumn),
    nticks: 12,
    automargin: true,
  };
  const yaxis: Record<string, unknown> = {
    title: spec.yAxisLabel?.trim() || (
      spec.yColumns.length > 3
        ? spec.yColumns.slice(0, 2).map(getLabelWithUnit).join(', ') + ` (+${spec.yColumns.length - 2} more)`
        : spec.yColumns.map(getLabelWithUnit).join(', ')
    ),
    nticks: 12,
    automargin: true,
  };

  if (hasAreaSpec) {
    xaxis.rangemode = 'tozero';
    yaxis.rangemode = 'tozero';
  }

  const baselineFiltered = filterRowsForChartBaseline(data, spec);
  const hasSelectedRegions = (spec.baselineSpec?.regions ?? []).filter((r) => r !== 'all').length > 0;
  const layoutRows = hasSelectedRegions
    ? baselineFiltered
    : baselineFiltered.length > 0
      ? baselineFiltered
      : data;

  const numericX = layoutRows.map((row) => Number(row[spec.xColumn])).filter(Number.isFinite);
  const maxX = numericX.length > 0 ? safeMax(numericX) : null;
  const minX = numericX.length > 0 ? safeMin(numericX) : null;

  const allY: number[] = [];
  for (const yCol of spec.yColumns) {
    allY.push(...layoutRows.map((row) => Number(row[yCol])).filter(Number.isFinite));
  }
  const maxY = allY.length > 0 ? safeMax(allY) : null;
  const minY = allY.length > 0 ? safeMin(allY) : null;

  const selectedRegions = (spec.baselineSpec?.regions ?? []).filter((r) => r !== 'all');
  if (selectedRegions.length > 0 && minX !== null && maxX !== null && minY !== null && maxY !== null) {
    const xBaseline = spec.baselineSpec?.xBaseline ?? 0;
    const yBaseline = spec.baselineSpec?.yBaseline ?? 0;
    const hasLeft = selectedRegions.some((r) => r.endsWith('left'));
    const hasRight = selectedRegions.some((r) => r.endsWith('right'));
    const hasTop = selectedRegions.some((r) => r.startsWith('top-'));
    const hasBottom = selectedRegions.some((r) => r.startsWith('bottom-'));

    if (hasRight && !hasLeft) xaxis.range = [xBaseline, maxX];
    if (hasLeft && !hasRight) xaxis.range = [minX, xBaseline];
    if (hasTop && !hasBottom) yaxis.range = [yBaseline, maxY];
    if (hasBottom && !hasTop) yaxis.range = [minY, yBaseline];
  }

  if (
    spec.chartType === 'area'
    && spec.areaSpec
    && spec.areaSpec.mode !== 'total'
    && selectedRegions.length === 0
  ) {
    const axis = spec.areaSpec.baselineAxis ?? 'y';
    const baseline = spec.areaSpec.baseline ?? 0;
    if (axis === 'y' && yaxis.range === undefined && maxY !== null && minY !== null) {
      if (spec.areaSpec.mode === 'positive') {
        yaxis.range = [baseline, maxY];
      } else if (spec.areaSpec.mode === 'negative') {
        yaxis.range = [minY, baseline];
      }
    }
    if (axis === 'x' && xaxis.range === undefined && maxX !== null && minX !== null) {
      if (spec.areaSpec.mode === 'positive') {
        xaxis.range = [baseline, maxX];
      } else if (spec.areaSpec.mode === 'negative') {
        xaxis.range = [minX, baseline];
      }
    }
  }

  if (xaxis.range === undefined) {
    const scopedX = buildScopedRange(numericX);
    if (scopedX) xaxis.range = scopedX;
  }
  if (yaxis.range === undefined) {
    const scopedY = buildScopedRange(allY);
    if (scopedY) yaxis.range = scopedY;
  }

  const zoomedX = toNumericRange(xaxis.range);
  if (zoomedX) {
    xaxis.range = expandRange(zoomedX, 0.06);
  }
  const zoomedY = toNumericRange(yaxis.range);
  if (zoomedY) {
    yaxis.range = expandRange(zoomedY, 0.12);
  }

  const baselineShapes: Array<Record<string, unknown>> = [];
  const baselineSpec = spec.baselineSpec;
  if (baselineSpec) {
    const xBaseline = baselineSpec.xBaseline;
    const yBaseline = baselineSpec.yBaseline;
    baselineShapes.push(
      {
        type: 'line',
        x0: xBaseline,
        x1: xBaseline,
        xref: 'x',
        y0: 0,
        y1: 1,
        yref: 'paper',
        line: { color: getCSSVariable('--text-color-secondary'), width: 1, dash: 'dot' },
        layer: 'above',
      },
      {
        type: 'line',
        x0: 0,
        x1: 1,
        xref: 'paper',
        y0: yBaseline,
        y1: yBaseline,
        yref: 'y',
        line: { color: getCSSVariable('--text-color-secondary'), width: 1, dash: 'dot' },
        layer: 'above',
      }
    );

    const regions = (baselineSpec.regions ?? []).filter((r) => r !== 'all');

    if (regions.length > 0 && minX !== null && maxX !== null && minY !== null && maxY !== null) {
      const regionRect = (region: string) => {
        if (region === 'top-left') return { x0: minX, x1: xBaseline, y0: yBaseline, y1: maxY };
        if (region === 'top-right') return { x0: xBaseline, x1: maxX, y0: yBaseline, y1: maxY };
        if (region === 'bottom-left') return { x0: minX, x1: xBaseline, y0: minY, y1: yBaseline };
        if (region === 'bottom-right') return { x0: xBaseline, x1: maxX, y0: minY, y1: yBaseline };
        return null;
      };

      for (const region of regions) {
        const rect = regionRect(region);
        if (!rect) continue;
        const x0 = Math.min(rect.x0, rect.x1);
        const x1 = Math.max(rect.x0, rect.x1);
        const y0 = Math.min(rect.y0, rect.y1);
        const y1 = Math.max(rect.y0, rect.y1);
        if (x0 === x1 || y0 === y1) continue;
        baselineShapes.push({
          type: 'rect',
          xref: 'x',
          yref: 'y',
          x0,
          x1,
          y0,
          y1,
          // Keep region geometry logic, but remove tinted overlay fill.
          fillcolor: 'rgba(0,0,0,0)',
          line: { width: 0 },
          layer: 'below',
        });
      }
    }
  }

  return {
    title: spec.title || undefined,
    template: 'none',
    xaxis,
    yaxis,
    margin: {
      t: spec.title ? chartMargin.topWithTitle : chartMargin.topNoTitle,
      r: chartMargin.right,
      b: chartMargin.bottom,
      l: chartMargin.left,
    },
    paper_bgcolor: chartPaperBg,
    plot_bgcolor: chartPlotBg,
    font: { color: getCSSVariable('--text-color-secondary') },
    showlegend: spec.yColumns.length > 1,
    autosize: true,
    shapes: baselineShapes,
    annotations:
      spec.annotations?.map((anno) => ({
        x: anno.x,
        y: anno.y,
        text: anno.text,
        showarrow: anno.showArrow ?? true,
        arrowhead: 2,
        ax: -40,
        ay: -40,
        font: { color: getCSSVariable('--text-color-inverse'), size: 12 },
        bgcolor: hexToRgba(getCSSVariable('--surface-overlay'), 0.9),
        bordercolor: getCSSVariable('--primary-500'),
        borderwidth: 1,
        borderpad: 4,
      })) || [],
  };
}
