import { computed, defineComponent } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { describe, expect, it, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { useChartsStore } from './charts';
import ChartBaselineDialog from '@/components/charts/sections/ChartBaselineDialog.vue';
import type { BaselineSpec } from '@/types/domain';

describe('charts baseline integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('updates chart store when setting baselines and selecting regions', async () => {
    const store = useChartsStore();
    const id = store.addChart({
      chartType: 'area',
      xColumn: 'x',
      yColumns: ['y'],
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
    });

    expect(id).toBeTruthy();

    const Host = defineComponent({
      components: { ChartBaselineDialog },
      setup() {
        const chart = computed(() => store.getChartById(id!)!);

        function handleBaseline(updates: Partial<BaselineSpec>) {
          const current = chart.value.baselineSpec ?? {
            xBaseline: 0,
            yBaseline: 0,
            regions: [],
          };
          store.updateChart(id!, {
            baselineSpec: { ...current, ...updates },
          });
        }

        function handleArea(updates: Record<string, unknown>) {
          if (!chart.value.areaSpec) return;
          store.updateChart(id!, {
            areaSpec: { ...chart.value.areaSpec, ...updates },
          });
        }

        return { chart, handleBaseline, handleArea };
      },
      template: `
        <ChartBaselineDialog
          :visible="true"
          :chart="chart"
          @updateBaselineSpec="handleBaseline"
          @updateAreaSpec="handleArea"
        />
      `,
    });

    const wrapper = mount(Host, {
      global: {
        stubs: {
          AppDialogSurface: {
            props: ['visible'],
            template: '<div v-if="visible"><slot /></div>',
          },
          InlineResetNumberField: {
            name: 'InlineResetNumberField',
            template: '<div class="inline-reset-stub"></div>',
          },
          Button: {
            template: '<button class="btn" @click="$emit(\'click\')"><slot /></button>',
          },
        },
      },
    });

    const inputStubs = wrapper.findAllComponents({ name: 'InlineResetNumberField' });
    inputStubs[0].vm.$emit('update:modelValue', 3);
    inputStubs[1].vm.$emit('update:modelValue', 7);

    await wrapper.findAll('button.ui-region-item')[0].trigger('click');

    const updated = store.getChartById(id!)!;
    expect(updated.baselineSpec?.xBaseline).toBe(3);
    expect(updated.baselineSpec?.yBaseline).toBe(7);
    expect(updated.baselineSpec?.regions).toEqual(['top-left']);
    expect(updated.areaSpec?.mode).toBe('positive');
  });
});
