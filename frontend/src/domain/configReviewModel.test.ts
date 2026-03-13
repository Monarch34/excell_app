import { describe, expect, it } from 'vitest';
import { buildConfigReviewModel } from './configReviewModel';
import type { AnalysisConfig } from '@/types/domain';

function createConfig(overrides?: Partial<AnalysisConfig>): AnalysisConfig {
  return {
    version: '1.0.0',
    name: 'Review Demo',
    description: '',
    selectedColumns: ['Force', 'Disp'],
    parameters: [],
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

describe('buildConfigReviewModel', () => {
  it('includes metadata-only referenced parameters even before live metadata is loaded', () => {
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
      ],
    });

    const model = buildConfigReviewModel(config, undefined, ['Gauge']);
    expect(model.parameters).toEqual([
      {
        name: 'Gauge',
        source: 'Metadata Reference',
        definedUnit: 'Relative',
        valueText: 'Waiting for dataset metadata',
        description: 'Referenced by formulas and expected from dataset metadata.',
      },
    ]);
  });

  it('prefers live metadata values for metadata parameters on the config page', () => {
    const config = createConfig({
      parameters: [{ name: 'Gauge', value: 10, unit: 'mm' }],
    });

    const metadataValues = new Map([['Gauge', { value: 12, unit: 'mm' }]]);
    const model = buildConfigReviewModel(config, metadataValues, ['Gauge']);

    expect(model.parameters[0]).toMatchObject({
      name: 'Gauge',
      source: 'Config + Metadata',
      definedUnit: 'mm',
      valueText: '12 mm (config 10 mm)',
    });
  });
});
