import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import DataPreviewTable from './DataPreviewTable.vue';

describe('DataPreviewTable smoke', () => {
  it('renders unique preview headers and emits row selection', async () => {
    const rows = [
      { time: 1, load: 10 },
      { time: 2, load: 20 },
    ];

    const wrapper = mount(DataPreviewTable, {
      props: {
        columns: [
          { name: 'time', type: 'numeric', unit: 's', selected: true },
          { name: 'time', type: 'numeric', unit: 's', selected: true },
          { name: 'load', type: 'numeric', unit: 'N', selected: true },
          { name: 'load', type: 'numeric', unit: 'N', selected: true },
        ],
        rows,
      },
      global: {
        stubs: {
          AppDataTable: {
            inheritAttrs: false,
            props: ['value'],
            template: `
              <div>
                <slot />
                <button
                  v-for="(row, idx) in value"
                  :key="idx"
                  class="row-btn"
                  @click="$emit('rowClick', { data: row })"
                >
                  {{ idx }}
                </button>
              </div>
            `,
          },
          Column: {
            template: `
              <div class="column-stub">
                <slot name="header" />
              </div>
            `,
          },
          Tag: true,
        },
      },
    });

    const titles = wrapper.findAll('.ui-data-preview-col-title').map((n) => n.text());
    expect(titles).toEqual(['time', 'load']);

    await wrapper.get('.row-btn').trigger('click');
    expect(wrapper.emitted('rowSelect')?.[0]).toEqual([0]);
  });
});
