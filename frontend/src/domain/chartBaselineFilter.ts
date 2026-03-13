import type { ChartSpec } from '@/types/domain';

export function filterRowsForChartBaseline(
  rows: Record<string, unknown>[],
  chart: Pick<ChartSpec, 'chartType' | 'xColumn' | 'yColumns' | 'baselineSpec' | 'areaSpec'>
) {
  const areaSpec = chart.areaSpec;
  const baselineSpec = chart.baselineSpec;
  const xCol = chart.xColumn;
  const yCols = chart.yColumns;

  return rows.filter((row) => {
    const x = Number(row[xCol]);
    if (Number.isNaN(x)) return false;

    const yValues = yCols.map((col) => Number(row[col]));
    if (yValues.some((v) => Number.isNaN(v))) return false;

    const effectiveRegions = (baselineSpec?.regions ?? []).filter((r) => r !== 'all');
    const applyRegionFilter = effectiveRegions.length > 0;
    if (applyRegionFilter) {
      const xBaseline = baselineSpec?.xBaseline ?? 0;
      const yBaseline = baselineSpec?.yBaseline ?? 0;
      const isLeft = x <= xBaseline;
      const isRight = x >= xBaseline;
      const isTop = yValues.every((v) => v >= yBaseline);
      const isBottom = yValues.every((v) => v <= yBaseline);
      const matches = effectiveRegions.some((region) => {
        if (region === 'top-right') return isRight && isTop;
        if (region === 'top-left') return isLeft && isTop;
        if (region === 'bottom-right') return isRight && isBottom;
        if (region === 'bottom-left') return isLeft && isBottom;
        return false;
      });
      if (!matches) return false;
    }

    if (chart.chartType === 'area' && areaSpec && effectiveRegions.length === 0) {
      if (areaSpec.mode !== 'total') {
        const baseline = areaSpec.baseline ?? 0;
        const axis = areaSpec.baselineAxis ?? 'y';
        if (axis === 'y') {
          const isPositive = areaSpec.mode === 'positive';
          if (isPositive && yValues.some((v) => v < baseline)) return false;
          if (!isPositive && yValues.some((v) => v > baseline)) return false;
        } else {
          const isPositive = areaSpec.mode === 'positive';
          if (isPositive && x < baseline) return false;
          if (!isPositive && x > baseline) return false;
        }
      }
    }

    return true;
  });
}
