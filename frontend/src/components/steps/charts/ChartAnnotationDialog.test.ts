import { mount } from '@vue/test-utils';
import { defineComponent, ref } from 'vue';
import { describe, expect, it } from 'vitest';
import ChartAnnotationDialog from './ChartAnnotationDialog.vue';

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

const AppDialogSurfaceStub = defineComponent({
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:visible'],
  template: `
    <div v-if="visible" class="dialog-stub">
      <slot />
      <slot name="footer" />
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

const AnnotationHarness = defineComponent({
  components: { ChartAnnotationDialog },
  setup() {
    const visible = ref(true);
    const text = ref('');

    return {
      text,
      visible,
    };
  },
  template: `
    <ChartAnnotationDialog
      :visible="visible"
      :text="text"
      @update:visible="visible = $event"
      @update:text="text = $event"
      @save="$emit('save')"
    />
  `,
});

describe('ChartAnnotationDialog', () => {
  it('shows and clears the required annotation error using the same field validation pattern', async () => {
    const wrapper = mount(AnnotationHarness, {
      global: {
        stubs: {
          AppField: AppFieldStub,
          AppDialogSurface: AppDialogSurfaceStub,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const input = wrapper.get('input[name="chart_annotation_text"]');
    const saveButton = wrapper.findAll('button.button-stub')[1];

    await input.trigger('blur');
    expect(wrapper.text()).toContain('Annotation text is required');

    await input.setValue('Peak load');
    expect(wrapper.text()).not.toContain('Annotation text is required');

    await saveButton.trigger('click');
    expect(wrapper.emitted('save')).toHaveLength(1);
  });
});
