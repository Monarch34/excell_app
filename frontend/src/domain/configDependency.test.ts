import { describe, expect, it } from 'vitest';
import {
  buildConfigDependencyModel,
  extractFormulaReferences,
} from './configDependency';
import type { AnalysisConfig } from '@/types/domain';

function createConfig(overrides?: Partial<AnalysisConfig>): AnalysisConfig {
  return {
    version: '1.0.0',
    name: 'Tree Demo',
    description: '',
    selectedColumns: ['Force', 'Disp'],
    parameters: [{ name: 'Gauge', value: 10, unit: 'mm' }],
    derivedColumns: [],
    charts: [],
    columnOrder: [],
    parameterOrder: [],
    separators: [],
    createdAt: '2026-01-01T00:00:00.000Z',
    updatedAt: '2026-01-01T00:00:00.000Z',
    ...overrides,
  };
}

describe('extractFormulaReferences', () => {
  it('extracts bracket and REF references in order without duplicates', () => {
    const refs = extractFormulaReferences('[Force] / REF([Gauge]) + [Force]');
    expect(refs).toEqual(['Force', 'Gauge']);
  });
});

describe('buildConfigDependencyModel', () => {
  it('builds derived and chart dependency relationships', () => {
    const config = createConfig({
      derivedColumns: [
        {
          id: 'dc-1',
          name: 'Stress',
          formula: '[Force] / [Gauge]',
          unit: 'MPa',
          description: '',
          dependencies: [],
          enabled: true,
          type: 'column',
        },
        {
          id: 'dp-1',
          name: 'Shift',
          formula: '[Gauge] * 0.1',
          unit: '',
          description: '',
          dependencies: [],
          enabled: true,
          type: 'parameter',
        },
      ],
      charts: [
        {
          id: 'ch-1',
          title: 'Stress Curve',
          xColumn: 'Disp',
          yColumns: ['Stress'],
          chartType: 'line',
          areaSpec: null,
          baselineSpec: null,
          lineColor: null,
          fillColor: null,
          fillOpacity: null,
        },
      ],
    });

    const model = buildConfigDependencyModel(config);
    expect(model.inputColumns).toEqual(['Force', 'Disp']);
    expect(model.inputParameters).toEqual(['Gauge']);
    expect(model.derivedItems.length).toBe(2);
    expect(model.derivedItems[0].dependencies.map((item) => item.name)).toEqual(['Force', 'Gauge']);
    expect(model.derivedItems[0].usedByCharts).toEqual(['Stress Curve']);
    expect(model.charts[0].yDependencies[0].kind).toBe('derived-column');
  });
});
