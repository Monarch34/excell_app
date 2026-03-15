import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import FormulaEditor from './FormulaEditor.vue';
import type { DerivedColumnDef } from '@/shared/types/domain';

import { validateFormula } from '@/services/formulasApi';

vi.mock('@/services/formulasApi', () => ({
  validateFormula: vi.fn(async () => ({ valid: true, errors: [], referenced_columns: [] })),
}));

const AppFieldStub = defineComponent({
  inheritAttrs: false,
  props: {
    error: {
      type: String,
      default: undefined,
    },
  },
  template: `
    <div class="app-field-stub" :class="$attrs.class">
      <slot />
      <small v-if="error" class="app-field-error">{{ error }}</small>
    </div>
  `,
});

const InputTextStub = defineComponent({
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    id: {
      type: String,
      default: undefined,
    },
    name: {
      type: String,
      default: undefined,
    },
    placeholder: {
      type: String,
      default: undefined,
    },
  },
  emits: ['update:modelValue', 'blur'],
  template: `
    <input
      class="input-text-stub"
      :id="id"
      :name="name"
      :placeholder="placeholder"
      :value="modelValue ?? ''"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
    />
  `,
});

const ButtonStub = defineComponent({
  props: {
    label: {
      type: String,
      default: '',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['click'],
  template: `
    <button class="button-stub" :disabled="disabled" @click="$emit('click', $event)">
      {{ label }}
    </button>
  `,
});

const column: DerivedColumnDef = {
  id: 'dc-1',
  name: '',
  formula: '',
  unit: '',
  description: '',
  dependencies: [],
  enabled: true,
  type: 'column',
};

describe('FormulaEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows and clears the required name error using touched-style validation', async () => {
    const wrapper = mount(FormulaEditor, {
      props: {
        column,
        previewLoading: false,
      },
      global: {
        stubs: {
          AppField: AppFieldStub,
          AppSurfacePanel: {
            template: '<div><slot /></div>',
          },
          AppTooltip: true,
          TokenFormulaEditor: true,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const nameInput = wrapper.get('input[name="formula_column_name_dc-1"]');
    const saveButton = wrapper.findAll('button.button-stub').find((button) => button.text() === 'Save');

    expect(saveButton).toBeTruthy();

    await nameInput.trigger('blur');
    expect(wrapper.text()).toContain('Name is required');

    await nameInput.setValue('Stress');
    expect(wrapper.text()).not.toContain('Name is required');

    await saveButton!.trigger('click');
    expect(wrapper.emitted('update')).toEqual([
      ['dc-1', {
        name: 'Stress',
        unit: '',
        description: '',
        formula: '',
      }],
    ]);
  });

  it('blocks save when API validation returns errors', async () => {
    vi.mocked(validateFormula).mockResolvedValueOnce({
      valid: false,
      errors: ['Unknown column [Foo]'],
      referenced_columns: [],
    });

    const wrapper = mount(FormulaEditor, {
      props: {
        column: { ...column, formula: '[Foo] * 2' },
        previewLoading: false,
      },
      global: {
        stubs: {
          AppField: AppFieldStub,
          AppSurfacePanel: { template: '<div><slot /></div>' },
          AppTooltip: true,
          TokenFormulaEditor: true,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const nameInput = wrapper.get('input[name="formula_column_name_dc-1"]');
    await nameInput.setValue('Result');

    const saveButton = wrapper.findAll('button.button-stub').find((b) => b.text() === 'Save');
    await saveButton!.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Unknown column [Foo]');
    });
    expect(wrapper.emitted('update')).toBeUndefined();
  });

  it('shows service-unavailable when validation API throws', async () => {
    vi.mocked(validateFormula).mockRejectedValueOnce(new Error('Network error'));

    const wrapper = mount(FormulaEditor, {
      props: {
        column: { ...column, formula: '[Load] * 2' },
        previewLoading: false,
      },
      global: {
        stubs: {
          AppField: AppFieldStub,
          AppSurfacePanel: { template: '<div><slot /></div>' },
          AppTooltip: true,
          TokenFormulaEditor: true,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const nameInput = wrapper.get('input[name="formula_column_name_dc-1"]');
    await nameInput.setValue('Result');

    const saveButton = wrapper.findAll('button.button-stub').find((b) => b.text() === 'Save');
    await saveButton!.trigger('click');

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Validation service unavailable');
    });
    expect(wrapper.emitted('update')).toBeUndefined();
  });

  it('does not emit update when name is blank on save', async () => {
    const wrapper = mount(FormulaEditor, {
      props: {
        column,
        previewLoading: false,
      },
      global: {
        stubs: {
          AppField: AppFieldStub,
          AppSurfacePanel: { template: '<div><slot /></div>' },
          AppTooltip: true,
          TokenFormulaEditor: true,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const nameInput = wrapper.get('input[name="formula_column_name_dc-1"]');
    await nameInput.trigger('blur');

    expect(wrapper.text()).toContain('Name is required');
    expect(wrapper.emitted('update')).toBeUndefined();
  });
});
