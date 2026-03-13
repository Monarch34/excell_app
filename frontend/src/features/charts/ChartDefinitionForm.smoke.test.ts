import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import ChartDefinitionForm from './ChartDefinitionForm.vue';
import type { ChartSpec } from '@/shared/types/domain';

const baseChart: ChartSpec = {
  id: 'chart-001',
  title: 'Smoke',
  xColumn: 'x',
  yColumns: ['y'],
  chartType: 'area',
  areaSpec: {
    mode: 'total',
    baseline: 0,
    baselineAxis: 'y',
    xColumn: 'x',
    yColumn: 'y',
  },
  lineColor: '#2F5597',
  fillColor: '#2F5597',
  fillOpacity: 0.4,
  lineWidth: 2,
  markerSize: 8,
  annotations: [],
};

describe('ChartDefinitionForm smoke', () => {
  it('renders collapsible section headers and keeps basics/axes open by default', () => {
    const wrapper = mount(ChartDefinitionForm, {
      props: {
        chart: baseChart,
        availableColumns: ['x', 'y', 'z'],
      },
      global: {
        stubs: {
          Button: true,
          Select: true,
          MultiSelect: true,
          InputText: true,
          InputGroup: true,
          InputGroupAddon: true,
          ColorPicker: true,
          Slider: true,
          Dialog: true,
          SelectButton: true,
          InputNumber: true,
        },
      },
    });

    expect(wrapper.text()).toContain('Basics');
    expect(wrapper.text()).toContain('Axes');
    expect(wrapper.text()).toContain('Area Style');
    expect(wrapper.text()).toContain('Chart Type');
    expect(wrapper.text()).toContain('X Column');
  });

  it('emits chart updates from basics section edit actions', async () => {
    const wrapper = mount(ChartDefinitionForm, {
      props: {
        chart: baseChart,
        availableColumns: ['x', 'y'],
      },
      global: {
        stubs: {
          ChartBasicsSection: {
            template: '<button class="emit-title" @click="$emit(\'updateTitle\', \'Updated Title\')">emit</button>',
          },
          ChartAxesSection: true,
          ChartStyleSection: true,
          ChartBaselineDialog: true,
        },
      },
    });

    await wrapper.get('.emit-title').trigger('click');
    expect(wrapper.emitted('update')?.[0]).toEqual([{ title: 'Updated Title' }]);
  });
});
