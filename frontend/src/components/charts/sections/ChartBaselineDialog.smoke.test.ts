import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import ChartBaselineDialog from './ChartBaselineDialog.vue';
import type { ChartSpec } from '@/types/domain';

const chart: ChartSpec = {
  id: 'chart-1',
  title: 'Area',
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
  baselineSpec: {
    xBaseline: 0,
    yBaseline: 0,
    regions: [],
  },
  lineColor: null,
  fillColor: null,
  fillOpacity: 0.4,
  lineWidth: 2,
  markerSize: 8,
  annotations: [],
};

describe('ChartBaselineDialog smoke', () => {
  it('emits baseline and area updates when selecting a region', async () => {
    const wrapper = mount(ChartBaselineDialog, {
      props: {
        visible: true,
        chart,
      },
      global: {
        stubs: {
          AppDialogSurface: {
            props: ['visible'],
            template: '<div v-if="visible"><slot /></div>',
          },
          InlineResetNumberField: true,
          Button: {
            props: ['label'],
            template: '<button class="btn" @click="$emit(\'click\')">{{ label }}</button>',
          },
        },
      },
    });

    const regionButtons = wrapper.findAll('button.ui-region-item');
    await regionButtons[0].trigger('click');

    expect(wrapper.emitted('updateBaselineSpec')?.[0]).toEqual([
      { regions: ['top-left'] },
    ]);
    expect(wrapper.emitted('updateAreaSpec')?.[0]).toEqual([
      { mode: 'positive', baselineAxis: 'y' },
    ]);
  });
});
