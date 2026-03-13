import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import ChartStyleSection from './ChartStyleSection.vue';
import InlineResetTextField from '@/features/charts/common/InlineResetTextField.vue';
import type { ChartSpec } from '@/shared/types/domain';

const areaChart: ChartSpec = {
  id: 'chart-001',
  title: 'Area Demo',
  xColumn: 'x',
  yColumns: ['y'],
  xAxisLabel: 'x',
  yAxisLabel: 'y',
  chartType: 'area',
  areaSpec: {
    mode: 'total',
    baseline: 0,
    baselineAxis: 'y',
    xColumn: 'x',
    yColumn: 'y',
    label: '',
  },
  baselineSpec: {
    xBaseline: 0,
    yBaseline: 0,
    regions: [],
  },
  lineColor: '#2F5597',
  fillColor: '#7FB3D5',
  fillOpacity: 0.4,
  lineWidth: 2,
  markerSize: null,
  annotations: [],
};

describe('ChartStyleSection', () => {
  it('places Stroke before Fill for area charts and keeps result name editable', () => {
    const wrapper = mount(ChartStyleSection, {
      props: {
        chart: areaChart,
        strokeLabel: 'Stroke Color',
        styleTitle: 'Area Style',
        colorPresets: ['#2F5597'],
        stripHash: (color: string | null) => color?.replace('#', ''),
        hideHeading: true,
      },
      global: {
        stubs: {
          Button: true,
          ColorPicker: true,
          Slider: true,
          InputText: true,
        },
      },
    });

    const text = wrapper.text();
    expect(text.indexOf('Stroke')).toBeGreaterThan(-1);
    expect(text.indexOf('Fill')).toBeGreaterThan(-1);
    expect(text.indexOf('Stroke')).toBeLessThan(text.indexOf('Fill'));

    const resultField = wrapper
      .findAllComponents(InlineResetTextField)
      .find((component) => component.props('inputId') === 'chart-chart-001-area-result-name');

    expect(resultField).toBeTruthy();
    expect(resultField?.props('disabled')).toBe(false);
  });
});
