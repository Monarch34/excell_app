import { describe, expect, it } from 'vitest';
import type { ChartSpec } from '@/types/domain';
import {
  computeNextIdSeed,
  createChartId,
  normalizeChartConfig,
  readChartUiState,
  writeChartUiState,
} from './charts.helpers';

describe('charts.helpers', () => {
  it('creates zero-padded chart ids', () => {
    expect(createChartId(1)).toEqual({ id: 'chart-001', next: 2 });
    expect(createChartId(42)).toEqual({ id: 'chart-042', next: 43 });
  });

  it('reads and writes minimal UI state payload', () => {
    const parsed = readChartUiState('{"chart-001":{"isOpen":true},"chart-002":{}}');
    expect(parsed['chart-001']?.isOpen).toBe(true);
    expect(parsed['chart-002']?.hiddenTraces).toEqual([]);

    const minimized = writeChartUiState(parsed);
    expect(minimized).toEqual({
      'chart-001': { isOpen: true },
    });
  });

  it('normalizes chart config ids, chartType, baseline defaults, and area defaults', () => {
    const input: ChartSpec[] = [
      {
        id: '',
        title: 'First',
        xColumn: 'X',
        yColumns: ['Y'],
        chartType: null,
        baselineSpec: { xBaseline: 1, yBaseline: 2, regions: [] },
        areaSpec: {
          mode: 'positive',
          baseline: 0,
          baselineAxis: undefined,
          xColumn: 'X',
          yColumn: 'Y',
        },
        lineColor: null,
        fillColor: null,
        fillOpacity: null,
      },
      {
        id: 'chart-010',
        title: 'Second',
        xColumn: 'X',
        yColumns: ['Y'],
        chartType: 'line',
        baselineSpec: null,
        areaSpec: null,
        lineColor: null,
        fillColor: null,
        fillOpacity: null,
      },
    ];

    let seed = 1;
    const normalized = normalizeChartConfig(input, () => {
      const next = createChartId(seed);
      seed = next.next;
      return next.id;
    });

    expect(normalized[0].id).toBe('chart-001');
    expect(normalized[0].chartType).toBe('area');
    expect(normalized[0].areaSpec?.baselineAxis).toBe('y');
    expect(normalized[1].id).toBe('chart-010');
    expect(normalized[1].chartType).toBe('line');
  });

  it('computes next seed from existing numeric chart ids', () => {
    const charts = [
      { id: 'chart-002' },
      { id: 'chart-019' },
      { id: 'custom-id' },
    ] as ChartSpec[];
    expect(computeNextIdSeed(charts, 1)).toBe(20);
    expect(computeNextIdSeed(charts, 25)).toBe(25);
  });
});
