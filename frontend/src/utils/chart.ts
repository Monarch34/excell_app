import type { ChartSpec } from '@/shared/types/domain';

/** Returns true when chart has type, x/y columns, and those columns exist in the data. */
export function chartDataReady(
  chart: ChartSpec | null | undefined,
  data: Record<string, unknown>[],
): boolean {
  if (!chart?.chartType) return false;
  if (!chart.xColumn || chart.yColumns.length === 0) return false;
  if (data.length === 0) return false;

  const firstRow = data[0];
  const xExists = chart.xColumn in firstRow;
  const yExists = chart.yColumns.every((column) => column in firstRow);
  return xExists && yExists;
}
