import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter, type RouteRecordRaw } from 'vue-router';
import AnalysisView from './AnalysisView.vue';
import { useColumnsStore } from '@/stores/columns';
import { useDatasetStore } from '@/stores/dataset';
import { createAnalysisStepGuard } from '@/router';

const runAnalysisMock = vi.fn<() => Promise<void>>();
const notifyWarnMock = vi.fn();

vi.mock('@/composables/analysis/useAnalysisRunner', () => ({
  useAnalysisRunner: () => ({
    runAnalysis: runAnalysisMock,
  }),
}));

vi.mock('@/composables/useNotify', () => ({
  useNotify: () => ({
    notifyWarn: notifyWarnMock,
  }),
}));

const ImportStepStub = defineComponent({
  emits: ['next'],
  template: '<button class="import-next" @click="$emit(\'next\')">next</button>',
});

const ColumnsStepStub = defineComponent({
  template: '<div class="columns-step">columns</div>',
});

const CalculationsStepStub = defineComponent({
  template: '<div class="calculations-step">calculations</div>',
});

const ChartsStepStub = defineComponent({
  template: '<div class="charts-step">charts</div>',
});

const ReviewStepStub = defineComponent({
  emits: ['rerun'],
  template: '<button class="review-rerun" @click="$emit(\'rerun\')">rerun</button>',
});

const ExportStepStub = defineComponent({
  template: '<div class="export-step">export</div>',
});

const routes: RouteRecordRaw[] = [
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisView,
    redirect: { name: 'analysis-import' },
    children: [
      {
        path: 'import',
        name: 'analysis-import',
        component: ImportStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-import'),
      },
      {
        path: 'columns-params',
        name: 'analysis-columns-params',
        component: ColumnsStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-columns-params'),
      },
      {
        path: 'calculations',
        name: 'analysis-calculations',
        component: CalculationsStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-calculations'),
      },
      {
        path: 'charts-area',
        name: 'analysis-charts-area',
        component: ChartsStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-charts-area'),
      },
      {
        path: 'review',
        name: 'analysis-review',
        component: ReviewStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-review'),
      },
      {
        path: 'export',
        name: 'analysis-export',
        component: ExportStepStub,
        beforeEnter: createAnalysisStepGuard('analysis-export'),
      },
    ],
  },
];

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes,
  });
}

async function mountAnalysis(initialPath: string, setupState?: () => void) {
  const pinia = createPinia();
  setActivePinia(pinia);
  setupState?.();

  const router = createTestRouter();
  await router.push(initialPath);
  await router.isReady();

  const wrapper = mount(AnalysisView, {
    global: {
      plugins: [pinia, router],
      stubs: {
        WizardStepper: {
          props: ['steps', 'activeStep'],
          template: '<div class="wizard-stepper">{{ activeStep }}</div>',
        },
        NavigationFooter: {
          props: ['primaryLabel', 'primaryIcon', 'primaryDisabled', 'primaryLoading'],
          emits: ['back', 'primary'],
          template: `
            <div class="footer-stub">
              <button class="footer-back" @click="$emit('back')">back</button>
              <button class="footer-primary" :disabled="primaryDisabled" @click="$emit('primary')">primary</button>
            </div>
          `,
        },
      },
    },
  });

  await flushPromises();
  return { wrapper, router };
}

describe('AnalysisView route-driven wizard', () => {
  beforeEach(() => {
    runAnalysisMock.mockReset();
    runAnalysisMock.mockResolvedValue();
    notifyWarnMock.mockReset();
    setActivePinia(createPinia());
  });

  it('redirects blocked deep links back to import', async () => {
    const { router } = await mountAnalysis('/analysis/charts-area');
    await flushPromises();
    expect(router.currentRoute.value.name).toBe('analysis-import');
  });

  it('moves from import to columns on next event', async () => {
    const { wrapper, router } = await mountAnalysis('/analysis/import', () => {
      const datasetStore = useDatasetStore();
      datasetStore.rows = [{ A: 1 }];
    });

    await wrapper.get('.import-next').trigger('click');
    await flushPromises();

    expect(router.currentRoute.value.name).toBe('analysis-columns-params');
  });

  it('runs analysis before moving from calculations to charts', async () => {
    const { wrapper, router } = await mountAnalysis('/analysis/calculations', () => {
      const datasetStore = useDatasetStore();
      const columnsStore = useColumnsStore();
      datasetStore.rows = [{ A: 1 }];
      columnsStore.selectAll(['A']);
    });

    await flushPromises();
    expect(router.currentRoute.value.name).toBe('analysis-calculations');

    await wrapper.get('.footer-primary').trigger('click');
    await flushPromises();

    expect(runAnalysisMock).toHaveBeenCalledTimes(1);
    expect(router.currentRoute.value.name).toBe('analysis-charts-area');
  });

  it('done on export resets flow and returns to import', async () => {
    const { wrapper, router } = await mountAnalysis('/analysis/export', () => {
      const datasetStore = useDatasetStore();
      const columnsStore = useColumnsStore();
      datasetStore.rows = [{ A: 1 }];
      datasetStore.rawRows = [{ A: 1 }];
      datasetStore.columns = [{ name: 'A', type: 'numeric', unit: '', selected: true }];
      columnsStore.selectAll(['A']);
    });

    await flushPromises();

    await wrapper.get('.footer-primary').trigger('click');
    await flushPromises();

    const datasetStore = useDatasetStore();
    const columnsStore = useColumnsStore();
    expect(router.currentRoute.value.name).toBe('analysis-import');
    expect(datasetStore.rows.length).toBe(0);
    expect(columnsStore.selectedColumnNames.length).toBe(0);
  });
});
