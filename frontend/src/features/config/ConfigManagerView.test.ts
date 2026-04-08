import { mount } from '@vue/test-utils';
import { computed, defineComponent, ref } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_EXPORT_FILENAME } from '@/constants/config';

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

describe('ConfigManagerView', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('validates the export filename locally and only exports after the field becomes valid', { timeout: 15_000 }, async () => {
    const mockCustomFilename = ref(DEFAULT_EXPORT_FILENAME);
    const mockExportLoading = ref(false);
    const mockExportError = ref<string | null>(null);
    const mockHandleExport = vi.fn();

    vi.doMock('pinia', async () => {
      const actual = await vi.importActual<typeof import('pinia')>('pinia');
      return {
        ...actual,
        storeToRefs: (store: unknown) => store,
      };
    });

    vi.doMock('@/stores/dataset', () => ({
      useDatasetStore: () => ({
        hasData: true,
      }),
    }));

    vi.doMock('@/stores/configManager', () => ({
      useConfigManagerStore: () => ({
        validationResult: ref(null),
        lastLoadedConfigName: ref(null),
        isLoading: false,
      }),
    }));

    vi.doMock('@/stores/derivedColumns', () => ({
      useDerivedColumnsStore: () => ({
        derivedColumns: [],
      }),
    }));

    vi.doMock('@/stores/parameters', () => ({
      useParametersStore: () => ({
        allParameters: [],
      }),
    }));

    vi.doMock('@/stores/charts', () => ({
      useChartsStore: () => ({
        charts: [],
      }),
    }));

    vi.doMock('@/composables/config/useConfigExportReport', async () => {
      const actual = await vi.importActual<typeof import('@/composables/config/useConfigExportReport')>('@/composables/config/useConfigExportReport');

      return {
        ...actual,
        useConfigExportReport: () => ({
          customFilename: mockCustomFilename,
          exportLoading: mockExportLoading,
          exportError: mockExportError,
          handleExport: mockHandleExport,
        }),
      };
    });

    vi.doMock('@/composables/config/useConfigManagerStep', () => ({
      useConfigManagerStep: () => ({
        defaultConfigName: computed(() => 'My Analysis'),
        handleSave: vi.fn(),
        handleSaveToDb: vi.fn(),
      }),
    }));

    const { default: ConfigManagerView } = await import('./ConfigManagerView.vue');

    const wrapper = mount(ConfigManagerView, {
      global: {
        stubs: {
          AppPageHeader: true,
          AppStepSection: {
            template: '<section><slot /></section>',
          },
          AppField: AppFieldStub,
          ConfigSavePanel: true,
          ConfigValidationReport: true,
          InputText: InputTextStub,
          Button: ButtonStub,
        },
      },
    });

    const filenameInput = wrapper.get('input[name="export_filename"]');
    const exportButton = wrapper.findAll('button.button-stub')[0];

    await filenameInput.setValue('***');
    expect(wrapper.text()).toContain('Report filename must include letters or numbers');

    await exportButton.trigger('click');
    expect(mockHandleExport).not.toHaveBeenCalled();

    await filenameInput.setValue('tensile_export');
    expect(wrapper.text()).not.toContain('Report filename must include letters or numbers');

    await exportButton.trigger('click');
    expect(mockHandleExport).toHaveBeenCalledTimes(1);
  });
});
