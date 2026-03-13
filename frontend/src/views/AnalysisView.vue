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
import WizardStepper from '@/shared/components/ui/WizardStepper.vue';
import NavigationFooter from '@/shared/components/ui/NavigationFooter.vue';

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

const nextStepLabel = computed(() => {
  const nextName = currentStep.value.next;
  if (!nextName) return 'Next';
  const nextConfig = ANALYSIS_STEP_CONFIG.find((s) => s.name === nextName);
  return nextConfig ? `Next: ${nextConfig.label}` : 'Next';
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
  const resolved = isAnalysisRouteName(targetRoute) ? targetRoute : currentStep.value.next;
  void navigateToRoute(resolved);
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
  <main class="ui-analysis-view" aria-labelledby="analysis-heading">
    <h1 id="analysis-heading" class="ui-visually-hidden">Analysis</h1>
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
      :primaryLabel="isLastStep ? 'Done' : nextStepLabel"
      :primaryIcon="isLastStep ? 'pi pi-check' : 'pi pi-arrow-right'"
      :primaryDisabled="(!canGoNext && !isLastStep) || processing"
      :primaryLoading="processing"
      :stepDescription="`Step ${currentStepIndex + 1} of ${ANALYSIS_STEP_CONFIG.length}`"
      @back="handleBack"
      @primary="handlePrimary"
    />
  </main>
</template>
