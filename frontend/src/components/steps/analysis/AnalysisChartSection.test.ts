import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import AnalysisChartSection from './AnalysisChartSection.vue';
import type { ChartSpec } from '@/types/domain';

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

describe('AnalysisChartSection', () => {
  it('uses the shared chart-card design on the analysis dashboard', () => {
    const wrapper = mount(AnalysisChartSection, {
      props: {
        chart,
        data: [{ Strain: 0.1, Stress: 100 }],
      },
      global: {
        stubs: {
          Button: true,
          Tag: true,
          ChartRenderer: true,
        },
      },
    });

    expect(wrapper.find('.ui-chart-card').exists()).toBe(true);
    expect(wrapper.find('.ui-chart-card-header').exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'Tag' }).exists()).toBe(true);
    expect(wrapper.text()).toContain('Preview');
  });
});
