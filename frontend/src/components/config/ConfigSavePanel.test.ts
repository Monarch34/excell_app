import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { describe, expect, it } from 'vitest';
import ConfigSavePanel from './ConfigSavePanel.vue';

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

const TextareaStub = defineComponent({
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
  emits: ['update:modelValue'],
  template: `
    <textarea
      class="textarea-stub"
      :id="id"
      :name="name"
      :placeholder="placeholder"
      :value="modelValue ?? ''"
      @input="$emit('update:modelValue', $event.target.value)"
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
    <button
      class="button-stub"
      :disabled="disabled"
      @click="$emit('click', $event)"
    >
      {{ label }}
    </button>
  `,
});

const AppSurfacePanelStub = defineComponent({
  template: '<div class="app-surface-panel-stub"><slot /></div>',
});

describe('ConfigSavePanel', () => {
  it('shows a name error after interaction and clears it when the input becomes valid', async () => {
    const wrapper = mount(ConfigSavePanel, {
      props: {
        defaultName: '   ',
      },
      global: {
        stubs: {
          AppSurfacePanel: AppSurfacePanelStub,
          AppField: AppFieldStub,
          InputText: InputTextStub,
          Textarea: TextareaStub,
          Button: ButtonStub,
        },
      },
    });

    const nameInput = wrapper.get('input[name="save_config_name"]');
    const nameInputComponent = wrapper.findComponent(InputTextStub);

    nameInputComponent.vm.$emit('blur');
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('Config name is required');

    await nameInput.setValue('  Tensile Config  ');
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).not.toContain('Config name is required');

    const buttons = wrapper.findAll('button.button-stub');
    await buttons[0].trigger('click');
    await buttons[1].trigger('click');

    expect(wrapper.emitted('saveToDb')).toEqual([
      ['Tensile Config', ''],
    ]);
    expect(wrapper.emitted('save')).toEqual([
      ['Tensile Config', ''],
    ]);
  });
});
