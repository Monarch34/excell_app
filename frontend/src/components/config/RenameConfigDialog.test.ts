import { mount } from '@vue/test-utils';
import { defineComponent, ref } from 'vue';
import { describe, expect, it } from 'vitest';
import RenameConfigDialog from './RenameConfigDialog.vue';

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

const DialogStub = defineComponent({
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
  },
  emits: ['update:modelValue', 'blur', 'keyup.enter'],
  template: `
    <input
      class="input-text-stub"
      :id="id"
      :value="modelValue ?? ''"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
      @keyup.enter="$emit('keyup.enter', $event)"
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

const RenameDialogHarness = defineComponent({
  components: { RenameConfigDialog },
  setup() {
    const visible = ref(true);
    const renameName = ref('');

    return {
      renameName,
      visible,
    };
  },
  template: `
    <RenameConfigDialog
      :visible="visible"
      :renameName="renameName"
      :renameLoading="false"
      @update:visible="visible = $event"
      @update:renameName="renameName = $event"
      @submit="$emit('submit')"
      @cancel="$emit('cancel')"
    />
  `,
});

describe('RenameConfigDialog', () => {
  it('uses the same live required-name validation pattern as the save panel', async () => {
    const wrapper = mount(RenameDialogHarness, {
      global: {
        stubs: {
          AppField: AppFieldStub,
          Dialog: DialogStub,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const input = wrapper.get('#rename-input');

    await input.trigger('blur');
    expect(wrapper.text()).toContain('Config name is required');

    await input.setValue('Renamed Config');
    expect(wrapper.text()).not.toContain('Config name is required');

    const saveButton = wrapper.findAll('button.button-stub')[1];
    await saveButton.trigger('click');

    const dialog = wrapper.getComponent(RenameConfigDialog);
    expect(dialog.emitted('update:renameName')).toEqual([
      ['Renamed Config'],
    ]);
    expect(wrapper.emitted('submit')).toHaveLength(1);
  });
});
