<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisRunner } from '@/composables/analysis/useAnalysisRunner';
import { useWorkspaceLifecycle } from '@/composables/useWorkspaceLifecycle';
import { useNotify } from '@/composables/useNotify';
import {
  ANALYSIS_STEP_CONFIG,
  type AnalysisRouteName,
  getAnalysisRouteAccess,
} from '@/router';
import WizardStepper from '@/components/common/WizardStepper.vue';
import NavigationFooter from '@/components/common/NavigationFooter.vue';

const route = useRoute();
const router = useRouter();
const { runAnalysis } = useAnalysisRunner();
const { resetWorkspace } = useWorkspaceLifecycle();
const { notifyWarn } = useNotify();

const processing = ref(false);

const stepLabels = ANALYSIS_STEP_CONFIG.map((step) => step.label);

function isAnalysisRouteName(routeName: unknown): routeName is AnalysisRouteName {
  return ANALYSIS_STEP_CONFIG.some((step) => step.name === routeName);
}

function resolveRouteName(target: unknown, fallback: AnalysisRouteName | null): AnalysisRouteName | null {
  if (isAnalysisRouteName(target)) {
    return target;
  }
  return fallback;
}

const currentStepIndex = computed(() => {
  const index = ANALYSIS_STEP_CONFIG.findIndex((step) => step.name === route.name);
  return index >= 0 ? index : 0;
});

const currentStep = computed(() => ANALYSIS_STEP_CONFIG[currentStepIndex.value]);
const activeStep = computed(() => currentStepIndex.value);
const isFirstStep = computed(() => currentStep.value.previous === null);
const isLastStep = computed(() => currentStep.value.next === null);
const canGoNext = computed(() => {
  const nextRoute = currentStep.value.next;
  if (!nextRoute) {
    return true;
  }
  return getAnalysisRouteAccess(nextRoute).allowed;
});

async function navigateToRoute(
  targetRoute: AnalysisRouteName | null,
  options: { replace?: boolean; warnOnBlocked?: boolean } = {},
): Promise<void> {
  const { replace = false, warnOnBlocked = true } = options;
  if (!targetRoute) return;

  const access = getAnalysisRouteAccess(targetRoute);
  if (!access.allowed) {
    if (warnOnBlocked) {
      notifyWarn('Cannot proceed', access.reason);
    }
    if (route.name !== access.redirectTo) {
      await router.replace({ name: access.redirectTo });
    }
    return;
  }

  if (route.name === targetRoute) {
    return;
  }

  if (replace) {
    await router.replace({ name: targetRoute });
    return;
  }
  await router.push({ name: targetRoute });
}

function goToChartsStep() {
  void navigateToRoute('analysis-charts-area');
}

function handleImportNext(targetRoute?: AnalysisRouteName) {
  void navigateToRoute(resolveRouteName(targetRoute, currentStep.value.next));
}

function handleBack() {
  if (isFirstStep.value) return;
  void navigateToRoute(currentStep.value.previous);
}

async function handlePrimary() {
  if (isLastStep.value) {
    resetWorkspace();
    await navigateToRoute('analysis-import', { replace: true, warnOnBlocked: false });
    return;
  }

  if (currentStep.value.name === 'analysis-calculations') {
    processing.value = true;
    try {
      await runAnalysis();
    } finally {
      processing.value = false;
    }
    await navigateToRoute(currentStep.value.next);
    return;
  }

  await navigateToRoute(currentStep.value.next);
}
</script>

<template>
  <div class="ui-analysis-view">
    <WizardStepper :steps="stepLabels" :activeStep="activeStep" />

    <div class="ui-analysis-content">
      <RouterView v-slot="{ Component, route: childRoute }">
        <Transition name="ui-fade" mode="out-in">
          <component
            :is="Component"
            :key="childRoute.fullPath"
            @next="handleImportNext"
            @goToCharts="goToChartsStep"
          />
        </Transition>
      </RouterView>
    </div>

    <NavigationFooter
      v-if="!isFirstStep"
      :primaryLabel="isLastStep ? 'Done' : 'Next'"
      :primaryIcon="isLastStep ? 'pi pi-check' : 'pi pi-arrow-right'"
      :primaryDisabled="(!canGoNext && !isLastStep) || processing"
      :primaryLoading="processing"
      @back="handleBack"
      @primary="handlePrimary"
    />
  </div>
</template>
