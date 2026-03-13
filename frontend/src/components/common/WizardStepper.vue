<script setup lang="ts">
const props = defineProps<{
  steps: string[];
  activeStep: number;
}>();
</script>

<template>
  <nav class="ui-wizard-stepper" :style="{ '--wizard-step-count': props.steps.length }" aria-label="Progress tracker">
    <div class="ui-wizard-progress-track" aria-hidden="true">
      <div
        class="ui-wizard-progress-fill"
        :aria-valuetext="`${props.activeStep + 1} of ${props.steps.length}`"
        :style="{ width: `${Math.max(0, Math.min(100, (props.activeStep / Math.max(1, props.steps.length - 1)) * 100))}%` }"
      ></div>
    </div>
    <div
      v-for="(step, index) in props.steps"
      :key="index"
      class="ui-step-item"
      role="listitem"
      :aria-current="index === props.activeStep ? 'step' : undefined"
      :aria-label="`Step ${index + 1}: ${step}`"
      :aria-valuenow="props.activeStep + 1"
      :aria-valuemin="1"
      :aria-valuemax="props.steps.length"
    >
      <div
        class="ui-step-circle"
        :class="{
          'active': index === props.activeStep,
          'completed': index < props.activeStep
        }"
        aria-hidden="true"
      >
        <i v-if="index < props.activeStep" class="pi pi-check"></i>
        <span v-else>{{ index + 1 }}</span>
      </div>

      <span class="ui-step-label" :class="{ 'active': index <= props.activeStep }">
        {{ step }}
      </span>
    </div>
  </nav>
</template>
