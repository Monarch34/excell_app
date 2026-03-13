import {
  createRouter,
  createWebHistory,
  type NavigationGuard,
  type RouteRecordName,
  type RouteRecordRaw,
} from 'vue-router';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';

export const ANALYSIS_STEP_CONFIG = [
  {
    name: 'analysis-import',
    path: 'import',
    label: 'Import',
    previous: null,
    next: 'analysis-columns-params',
  },
  {
    name: 'analysis-columns-params',
    path: 'columns-params',
    label: 'Columns & Params',
    previous: 'analysis-import',
    next: 'analysis-calculations',
  },
  {
    name: 'analysis-calculations',
    path: 'calculations',
    label: 'Calculations',
    previous: 'analysis-columns-params',
    next: 'analysis-charts-area',
  },
  {
    name: 'analysis-charts-area',
    path: 'charts-area',
    label: 'Charts & Area',
    previous: 'analysis-calculations',
    next: 'analysis-review',
  },
  {
    name: 'analysis-review',
    path: 'review',
    label: 'Analysis',
    previous: 'analysis-charts-area',
    next: 'analysis-export',
  },
  {
    name: 'analysis-export',
    path: 'export',
    label: 'Export',
    previous: 'analysis-review',
    next: null,
  },
] as const;

export type AnalysisRouteName = (typeof ANALYSIS_STEP_CONFIG)[number]['name'];

type RouteAccessAllowed = {
  allowed: true;
};

type RouteAccessBlocked = {
  allowed: false;
  redirectTo: AnalysisRouteName;
  reason: string;
};

export type AnalysisRouteAccess = RouteAccessAllowed | RouteAccessBlocked;

const ROUTES_REQUIRING_DATASET: ReadonlySet<AnalysisRouteName> = new Set([
  'analysis-columns-params',
  'analysis-calculations',
  'analysis-charts-area',
  'analysis-review',
  'analysis-export',
]);

const ROUTES_REQUIRING_COLUMNS_AND_PARAMS: ReadonlySet<AnalysisRouteName> = new Set([
  'analysis-calculations',
  'analysis-charts-area',
  'analysis-review',
  'analysis-export',
]);

function isAnalysisRouteName(routeName: unknown): routeName is AnalysisRouteName {
  return ANALYSIS_STEP_CONFIG.some((step) => step.name === routeName);
}

export function getAnalysisRouteAccess(
  routeName: RouteRecordName | null | undefined,
): AnalysisRouteAccess {
  if (!isAnalysisRouteName(routeName)) {
    return { allowed: true };
  }

  const datasetStore = useDatasetStore();
  const columnsStore = useColumnsStore();
  const parametersStore = useParametersStore();

  if (ROUTES_REQUIRING_DATASET.has(routeName) && !datasetStore.hasData) {
    return {
      allowed: false,
      redirectTo: 'analysis-import',
      reason: 'Please upload a data file before proceeding',
    };
  }

  if (ROUTES_REQUIRING_COLUMNS_AND_PARAMS.has(routeName)) {
    if (!columnsStore.hasSelection) {
      return {
        allowed: false,
        redirectTo: 'analysis-columns-params',
        reason: 'Please select at least one column to analyze',
      };
    }
    if (!parametersStore.isValid) {
      return {
        allowed: false,
        redirectTo: 'analysis-columns-params',
        reason: 'Please fix parameter validation errors before proceeding',
      };
    }
  }

  return { allowed: true };
}

export function createAnalysisStepGuard(routeName: AnalysisRouteName): NavigationGuard {
  return () => {
    const access = getAnalysisRouteAccess(routeName);
    if (access.allowed) {
      return true;
    }
    return { name: access.redirectTo };
  };
}

const ANALYSIS_STEP_COMPONENTS: Record<AnalysisRouteName, () => Promise<unknown>> = {
  'analysis-import': () => import('../components/steps/ImportView.vue'),
  'analysis-columns-params': () => import('../components/steps/ColumnsParamsView.vue'),
  'analysis-calculations': () => import('../components/steps/CalculationsView.vue'),
  'analysis-charts-area': () => import('../components/steps/ChartsAreaView.vue'),
  'analysis-review': () => import('../components/steps/AnalysisDashboard.vue'),
  'analysis-export': () => import('../components/steps/ConfigManagerView.vue'),
};

const analysisChildRoutes: RouteRecordRaw[] = ANALYSIS_STEP_CONFIG.map((step) => ({
  path: step.path,
  name: step.name,
  component: ANALYSIS_STEP_COMPONENTS[step.name],
  beforeEnter: createAnalysisStepGuard(step.name),
  meta: { wizardStep: step },
}));

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('../views/AnalysisView.vue'),
    redirect: { name: 'analysis-import' },
    children: analysisChildRoutes,
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/config',
    name: 'config',
    component: () => import('../views/ConfigView.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
