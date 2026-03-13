<script setup lang="ts">
import { computed } from 'vue';
import type { ValidationResult } from '@/shared/types/domain';
import Tag from 'primevue/tag';
import AppNotice from '@/shared/components/ui/AppNotice.vue';

const props = defineProps<{
  result: ValidationResult;
  configName: string;
  counts?: {
    derivedColumns: number;
    parameters: number;
    charts: number;
  };
}>();

const successSummary = computed(() => {
  const counts = props.counts ?? { derivedColumns: 0, parameters: 0, charts: 0 };
  return `${counts.derivedColumns} Derived Columns, ${counts.parameters} Parameters, ${counts.charts} Charts applied`;
});

const hasErrors = computed(() => props.result.errors.length > 0);
const hasWarnings = computed(() => props.result.warnings.length > 0);
const isCleanSuccess = computed(() => props.result.valid && !hasErrors.value && !hasWarnings.value);
</script>

<template>
  <AppNotice
    class="validation-report ui-config-validation-report"
    :severity="hasErrors ? 'error' : (isCleanSuccess ? 'success' : 'warn')"
  >
    <div class="ui-config-validation-head ui-config-validation-head-row">
      <i :class="['pi', isCleanSuccess ? 'pi-check-circle ui-color-success' : 'pi-exclamation-triangle ui-color-warning']" aria-hidden="true"></i>
      <span class="font-bold text-color">
        {{ isCleanSuccess ? 'Config Loaded Successfully' : 'Config Loaded with Issues' }}
      </span>
      <Tag :value="configName" severity="info" class="text-xs" />
    </div>

    <!-- Errors -->
    <div v-if="result.errors.length > 0" class="ui-config-validation-block ui-config-validation-block--error ui-config-validation-block--spaced">
      <span class="ui-color-error font-semibold text-sm block ui-config-validation-title">Errors (must fix)</span>
      <div v-for="(err, i) in result.errors" :key="`err-${i}`" class="ui-config-validation-item ui-config-validation-item-row">
        <i class="pi pi-times-circle ui-color-error text-xs ui-config-validation-item-icon" aria-hidden="true"></i>
        <div>
          <span class="text-color text-sm">{{ err.message }}</span>
          <div v-if="err.suggestions && err.suggestions.length > 0" class="ui-config-validation-suggestions">
            <span class="text-color-secondary text-xs">Suggestions: </span>
            <Tag
              v-for="s in err.suggestions"
              :key="s"
              :value="s"
              severity="info"
              class="text-xs ui-config-validation-suggestion-tag"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="result.warnings.length > 0" class="ui-config-validation-block ui-config-validation-block--warn">
      <span class="ui-color-warning font-semibold text-sm block ui-config-validation-title">Warnings</span>
      <div v-for="(warn, i) in result.warnings" :key="`warn-${i}`" class="ui-config-validation-item ui-config-validation-item-row">
        <i class="pi pi-exclamation-triangle ui-color-warning text-xs ui-config-validation-item-icon" aria-hidden="true"></i>
        <div>
          <span class="text-color text-sm">{{ warn.message }}</span>
          <div v-if="warn.suggestions && warn.suggestions.length > 0" class="ui-config-validation-suggestions">
            <span class="text-color-secondary text-xs">Suggestions: </span>
            <Tag
              v-for="s in warn.suggestions"
              :key="s"
              :value="s"
              severity="info"
              class="text-xs ui-config-validation-suggestion-tag"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- All Clear -->
    <div v-if="isCleanSuccess" class="ui-color-success text-sm">
      <div class="font-semibold">Configuration loaded successfully.</div>
      <div class="mt-1">{{ successSummary }}</div>
    </div>
  </AppNotice>
</template>
