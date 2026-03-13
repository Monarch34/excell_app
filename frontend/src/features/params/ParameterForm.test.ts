import { mount } from '@vue/test-utils';
import { defineComponent, ref } from 'vue';
import { describe, expect, it } from 'vitest';
import ParameterForm from './ParameterForm.vue';
import type { Parameter } from '@/shared/types/domain';

const AppFieldStub = defineComponent({
  inheritAttrs: false,
  template: '<div class="app-field-stub" :class="$attrs.class"><slot /></div>',
});

const InputTextStub = defineComponent({
  props: {
    id: {
      type: String,
      default: undefined,
    },
    name: {
      type: String,
      default: undefined,
    },
    modelValue: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: undefined,
    },
    ariaLabel: {
      type: String,
      default: undefined,
    },
    size: {
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
      :aria-label="ariaLabel"
      :value="modelValue ?? ''"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
    />
  `,
});

const InputNumberStub = defineComponent({
  props: {
    inputId: {
      type: String,
      default: undefined,
    },
    name: {
      type: String,
      default: undefined,
    },
    modelValue: {
      type: Number,
      default: null,
    },
    placeholder: {
      type: String,
      default: undefined,
    },
    ariaLabel: {
      type: String,
      default: undefined,
    },
    pt: {
      type: Object,
      default: () => ({}),
    },
    size: {
      type: String,
      default: undefined,
    },
  },
  emits: ['input', 'update:modelValue', 'blur'],
  methods: {
    handleInput(event: Event) {
      const target = event.target as HTMLInputElement;
      const rawValue = target.value;
      const parsedValue = rawValue === '' ? null : Number(rawValue);
      const normalizedValue = Number.isFinite(parsedValue) ? parsedValue : null;

      this.$emit('input', {
        originalEvent: event,
        value: normalizedValue,
        formattedValue: rawValue,
      });
      this.$emit('update:modelValue', normalizedValue);
    },
  },
  template: `
    <input
      class="input-number-stub"
      :id="inputId"
      :name="pt?.input?.name || name"
      :placeholder="placeholder"
      :aria-label="ariaLabel"
      :value="modelValue ?? ''"
      @input="handleInput"
      @blur="$emit('blur', { originalEvent: $event, value: $event.target.value })"
    />
  `,
});

const ParameterFormHarness = defineComponent({
  components: { ParameterForm },
  props: {
    initialUserParameters: {
      type: Array as () => Parameter[],
      required: true,
    },
  },
  setup(props) {
    const userParameters = ref(props.initialUserParameters.map((param) => ({ ...param })));

    function handleUpdate(index: number, updates: Partial<Parameter>) {
      userParameters.value[index] = {
        ...userParameters.value[index],
        ...updates,
      };
    }

    function handleRemove(index: number) {
      userParameters.value.splice(index, 1);
    }

    return {
      handleRemove,
      handleUpdate,
      userParameters,
    };
  },
  template: `
    <ParameterForm
      :metadataParameters="{}"
      :metadataParameterUnits="{}"
      :userParameters="userParameters"
      @updateParameter="handleUpdate"
      @removeParameter="handleRemove"
    />
  `,
});

function mountForm(userParameters: Parameter[]) {
  return mount(ParameterFormHarness, {
    props: {
      initialUserParameters: userParameters,
    },
    global: {
      stubs: {
        AppField: AppFieldStub,
        AppTooltip: true,
        InputText: InputTextStub,
        InputNumber: InputNumberStub,
        Button: true,
      },
    },
  });
}

describe('ParameterForm', () => {
  it('clears name and value validation as soon as the fields become valid', async () => {
    const wrapper = mountForm([
      { name: '', value: null, unit: '' },
    ]);

    const nameInput = wrapper.get('input[name="user_param_name_0"]');
    const valueInput = wrapper.get('input[name="user_param_value_0"]');

    await nameInput.trigger('blur');
    await valueInput.trigger('blur');

    expect(wrapper.text()).toContain('Name is required');
    expect(wrapper.text()).toContain('Value is required');
    expect(wrapper.findAll('.app-field-stub.ui-param-field--invalid')).toHaveLength(2);

    await nameInput.setValue('Length');
    await valueInput.setValue('12.5');

    expect(wrapper.text()).not.toContain('Name is required');
    expect(wrapper.text()).not.toContain('Value is required');
    expect(wrapper.findAll('.app-field-stub.ui-param-field--invalid')).toHaveLength(0);

    const form = wrapper.getComponent(ParameterForm);
    expect(form.emitted('updateParameter')).toEqual([
      [0, { name: 'Length' }],
      [0, { value: 12.5 }],
      [0, { value: 12.5 }],
    ]);
  });

  it('flags duplicate names after interaction', async () => {
    const wrapper = mountForm([
      { name: 'Width', value: 2, unit: 'mm' },
      { name: 'Width', value: 3, unit: 'mm' },
    ]);

    const nameInputs = [
      wrapper.get('input[name="user_param_name_0"]'),
      wrapper.get('input[name="user_param_name_1"]'),
    ];

    await nameInputs[0].trigger('blur');
    await nameInputs[1].trigger('blur');

    expect(wrapper.text()).toContain('Name must be unique');
    expect(wrapper.findAll('.app-field-stub.ui-param-field--invalid')).toHaveLength(2);
  });
});
