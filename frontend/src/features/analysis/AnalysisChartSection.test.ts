import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import AnalysisChartSection from './AnalysisChartSection.vue';
import type { ChartSpec } from '@/shared/types/domain';

const chart: ChartSpec = {
  id: 'chart-001',
  title: 'Stress Curve',
  xColumn: 'Strain',
  yColumns: ['Stress'],
  xAxisLabel: 'Strain',
  yAxisLabel: 'Stress',
  chartType: 'line',
  baselineSpec: null,
  areaSpec: null,
  lineColor: null,
  fillColor: null,
  fillOpacity: null,
  lineWidth: 2,
  markerSize: null,
  annotations: [],
};

function mountChart(chartOverrides: Partial<ChartSpec> = {}, data: Record<string, unknown>[] = [{ Strain: 0.1, Stress: 100 }]) {
  return mount(AnalysisChartSection, {
    props: {
      chart: { ...chart, ...chartOverrides },
      data,
    },
    global: {
      stubs: {
        Button: true,
        Tag: true,
        ChartRenderer: true,
      },
    },
  });
}

describe('AnalysisChartSection', () => {
  it('uses the shared chart-card design on the analysis dashboard', () => {
    const wrapper = mountChart();

    expect(wrapper.find('.ui-chart-card').exists()).toBe(true);
    expect(wrapper.find('.ui-chart-card-header').exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'Tag' }).exists()).toBe(true);
    expect(wrapper.text()).toContain('Preview');
  });

  it('shows "Select a chart type" when chartType is null', () => {
    const wrapper = mountChart({ chartType: null });
    expect(wrapper.text()).toContain('Select a chart type');
  });

  it('shows "Configure X and Y" when xColumn is missing', () => {
    const wrapper = mountChart({ xColumn: '' });
    expect(wrapper.text()).toContain('X');
    expect(wrapper.text()).toContain('Y');
  });

  it('shows "Configure X and Y" when yColumns is empty', () => {
    const wrapper = mountChart({ yColumns: [] });
    expect(wrapper.text()).toContain('X');
    expect(wrapper.text()).toContain('Y');
  });

  it('shows analysis-needed message when data is empty', () => {
    const wrapper = mountChart({}, []);
    expect(wrapper.text()).toContain('analysis');
  });

  it('shows analysis-needed message when columns are not in data', () => {
    const wrapper = mountChart({}, [{ OtherCol: 1 }]);
    expect(wrapper.text()).toContain('analysis');
  });

  it('falls back to Untitled Chart when title is empty', () => {
    const wrapper = mountChart({ title: '' });
    expect(wrapper.text()).toContain('Untitled Chart');
  });
});
