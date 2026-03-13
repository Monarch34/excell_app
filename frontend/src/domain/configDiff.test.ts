import { describe, expect, it } from 'vitest';
import {
  buildConfigDiff,
  buildLiveConfigSnapshot,
} from './configDiff';
import type { AnalysisConfig, ChartSpec, DerivedColumnDef, Parameter } from '@/shared/types/domain';

function createConfig(overrides?: Partial<AnalysisConfig>): AnalysisConfig {
  return {
    version: '1.0.0',
    name: 'Config A',
    description: '',
    selectedColumns: ['A', 'B'],
    parameters: [{ name: 'p1', value: 1, unit: 'mm' }],
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

describe('configDiff', () => {
  it('handles empty arrays for all fields in snapshot and config', () => {
    const snapshot = buildLiveConfigSnapshot({
      selectedColumns: [],
      parameters: [],
      derivedColumns: [],
      charts: [],
    });

    const target = createConfig({
      selectedColumns: [],
      parameters: [],
      derivedColumns: [],
      charts: [],
    });

    const diff = buildConfigDiff(snapshot, target);
    expect(diff.hasChanges).toBe(false);
    expect(diff.counts.current.selectedColumns).toBe(0);
    expect(diff.counts.target.selectedColumns).toBe(0);
  });

  it('handles undefined/missing optional arrays on target config', () => {
    const snapshot = buildLiveConfigSnapshot({
      selectedColumns: ['A'],
      parameters: [],
      derivedColumns: [],
      charts: [],
    });

    const target = {
      ...createConfig(),
      selectedColumns: undefined as unknown as string[],
      parameters: undefined as unknown as Parameter[],
      derivedColumns: undefined as unknown as DerivedColumnDef[],
      charts: undefined as unknown as ChartSpec[],
    };

    const diff = buildConfigDiff(snapshot, target);
    expect(diff.selectedColumns.removed).toEqual(['A']);
    expect(diff.counts.target.selectedColumns).toBe(0);
  });

  it('filters blank-name parameters from snapshot', () => {
    const snapshot = buildLiveConfigSnapshot({
      selectedColumns: [],
      parameters: [
        { name: '', value: 1, unit: '' },
        { name: '  ', value: 2, unit: '' },
        { name: 'valid', value: 3, unit: 'mm' },
      ],
      derivedColumns: [],
      charts: [],
    });

    expect(snapshot.parameters).toHaveLength(1);
    expect(snapshot.parameters[0].name).toBe('valid');
  });


  it('returns no changes when current snapshot matches target config', () => {
    const config = createConfig({
      derivedColumns: [{ id: 'dc-001', name: 'C', formula: '', unit: '', description: '', dependencies: [], enabled: true, type: 'column' }],
      charts: [{ id: 'ch-001', title: 'Main', xColumn: 'A', yColumns: ['B'], chartType: 'line', areaSpec: null, baselineSpec: null, lineColor: null, fillColor: null, fillOpacity: null }],
    });

    const snapshot = buildLiveConfigSnapshot({
      selectedColumns: ['A', 'B'],
      parameters: [{ name: 'p1', value: 1, unit: 'mm' }],
      derivedColumns: [{ id: 'dc-001', name: 'C', formula: '', unit: '', description: '', dependencies: [], enabled: true, type: 'column' }],
      charts: [{ id: 'ch-001', title: 'Main', xColumn: 'A', yColumns: ['B'], chartType: 'line', areaSpec: null, baselineSpec: null, lineColor: null, fillColor: null, fillOpacity: null }],
    });

    const diff = buildConfigDiff(snapshot, config);
    expect(diff.hasChanges).toBe(false);
  });

  it('detects added/removed entities and parameter value updates', () => {
    const snapshot = buildLiveConfigSnapshot({
      selectedColumns: ['A', 'Legacy'],
      parameters: [
        { name: 'p1', value: 1, unit: 'mm' },
        { name: 'p2', value: 5, unit: '' },
      ],
      derivedColumns: [{ id: 'dc-001', name: 'OldDerived', formula: '', unit: '', description: '', dependencies: [], enabled: true, type: 'column' }],
      charts: [{ id: 'ch-001', title: 'Old Chart', xColumn: 'A', yColumns: ['Legacy'], chartType: 'line', areaSpec: null, baselineSpec: null, lineColor: null, fillColor: null, fillOpacity: null }],
    });

    const target = createConfig({
      selectedColumns: ['A', 'B'],
      parameters: [
        { name: 'p1', value: 2, unit: 'mm' },
        { name: 'p3', value: 10, unit: '' },
      ],
      derivedColumns: [{ id: 'dc-002', name: 'NewDerived', formula: '', unit: '', description: '', dependencies: [], enabled: true, type: 'column' }],
      charts: [{ id: 'ch-002', title: 'New Chart', xColumn: 'A', yColumns: ['B'], chartType: 'line', areaSpec: null, baselineSpec: null, lineColor: null, fillColor: null, fillOpacity: null }],
    });

    const diff = buildConfigDiff(snapshot, target);
    expect(diff.hasChanges).toBe(true);
    expect(diff.selectedColumns.added).toEqual(['B']);
    expect(diff.selectedColumns.removed).toEqual(['Legacy']);
    expect(diff.parameters.added).toEqual(['p3']);
    expect(diff.parameters.removed).toEqual(['p2']);
    expect(diff.parameters.changed.some((line) => line.includes('p1'))).toBe(true);
    expect(diff.derivedColumns.added).toEqual(['NewDerived']);
    expect(diff.derivedColumns.removed).toEqual(['OldDerived']);
    expect(diff.charts.added).toEqual(['New Chart']);
    expect(diff.charts.removed).toEqual(['Old Chart']);
  });
});
