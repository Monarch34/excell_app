import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useChartsStore } from './charts';
import { MAX_CHARTS } from './charts.helpers';

describe('charts store actions', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it('addChart returns null when at MAX_CHARTS capacity', () => {
    const store = useChartsStore();
    for (let i = 0; i < MAX_CHARTS; i++) {
      expect(store.addChart()).toBeTruthy();
    }

    expect(store.count).toBe(MAX_CHARTS);
    expect(store.canAdd).toBe(false);
    expect(store.addChart()).toBeNull();
    expect(store.count).toBe(MAX_CHARTS);
  });

  it('addChart collapses existing charts and opens the new one', () => {
    const store = useChartsStore();
    const id1 = store.addChart()!;
    expect(store.chartStates[id1].isOpen).toBe(true);

    const id2 = store.addChart()!;
    expect(store.chartStates[id1].isOpen).toBe(false);
    expect(store.chartStates[id2].isOpen).toBe(true);
  });

  it('removeChart with non-existent id is a no-op', () => {
    const store = useChartsStore();
    store.addChart();
    store.removeChart('does-not-exist');
    expect(store.count).toBe(1);
  });

  it('removeChart removes chart and its UI state', () => {
    const store = useChartsStore();
    const id = store.addChart()!;
    expect(store.count).toBe(1);

    store.removeChart(id);
    expect(store.count).toBe(0);
    expect(store.chartStates[id]).toBeUndefined();
  });

  it('updateChart with non-existent id is a no-op', () => {
    const store = useChartsStore();
    store.addChart();
    store.updateChart('does-not-exist', { title: 'New Title' });
    expect(store.charts[0].title).not.toBe('New Title');
  });

  it('updateChart merges updates into existing chart', () => {
    const store = useChartsStore();
    const id = store.addChart()!;
    store.updateChart(id, { title: 'Updated' });
    expect(store.getChartById(id)!.title).toBe('Updated');
  });

  it('getChartById returns undefined for non-existent id', () => {
    const store = useChartsStore();
    expect(store.getChartById('nope')).toBeUndefined();
  });

  it('addAnnotation on non-existent chart is a no-op', () => {
    const store = useChartsStore();
    store.addAnnotation('nope', 1, 2, 'text');
    expect(store.charts.length).toBe(0);
  });

  it('addAnnotation initializes annotations array when absent', () => {
    const store = useChartsStore();
    const id = store.addChart()!;
    const chart = store.getChartById(id)!;
    expect(chart.annotations).toBeUndefined();

    store.addAnnotation(id, 1, 2, 'Peak');
    expect(chart.annotations).toHaveLength(1);
    expect(chart.annotations![0].text).toBe('Peak');
  });

  it('removeAnnotation on non-existent chart is a no-op', () => {
    const store = useChartsStore();
    store.removeAnnotation('nope', 0);
  });

  it('removeAnnotation removes by index', () => {
    const store = useChartsStore();
    const id = store.addChart()!;
    store.addAnnotation(id, 1, 2, 'A');
    store.addAnnotation(id, 3, 4, 'B');

    store.removeAnnotation(id, 0);
    const chart = store.getChartById(id)!;
    expect(chart.annotations).toHaveLength(1);
    expect(chart.annotations![0].text).toBe('B');
  });

  it('chartsWithArea filters correctly', () => {
    const store = useChartsStore();
    store.addChart({ chartType: 'area', areaSpec: { mode: 'total', baseline: 0, baselineAxis: 'y', xColumn: 'x', yColumn: 'y' } });
    store.addChart({ chartType: 'line' });
    store.addChart({ chartType: 'area' });

    expect(store.chartsWithArea.length).toBe(1);
  });

  it('enableArea and disableArea toggle areaSpec', () => {
    const store = useChartsStore();
    const id = store.addChart({ chartType: 'area' })!;
    expect(store.getChartById(id)!.areaSpec).toBeNull();

    store.enableArea(id, 'total', 'X', 'Y');
    expect(store.getChartById(id)!.areaSpec).not.toBeNull();
    expect(store.getChartById(id)!.areaSpec!.mode).toBe('total');

    store.disableArea(id);
    expect(store.getChartById(id)!.areaSpec).toBeNull();
  });

  it('loadFromConfig with empty array resets to empty', () => {
    const store = useChartsStore();
    store.addChart();
    store.loadFromConfig([]);
    expect(store.count).toBe(0);
  });

  it('reset clears all state', () => {
    const store = useChartsStore();
    store.addChart();
    store.addChart();
    expect(store.count).toBe(2);

    store.reset();
    expect(store.count).toBe(0);
    expect(Object.keys(store.chartStates)).toHaveLength(0);
  });

  it('sortedCharts returns descending order by id', () => {
    const store = useChartsStore();
    store.addChart();
    store.addChart();
    store.addChart();

    const ids = store.sortedCharts.map((c) => c.id);
    for (let i = 0; i < ids.length - 1; i++) {
      expect(ids[i].localeCompare(ids[i + 1])).toBeGreaterThan(0);
    }
  });
});
