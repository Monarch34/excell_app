<script setup lang="ts">
import Button from 'primevue/button';
import AppTooltip from '@/shared/components/ui/AppTooltip.vue';
import { TOOLTIPS } from '@/constants/tooltips';
import type { ChartSpec, ChartType } from '@/shared/types/domain';
import InlineResetTextField from '@/features/charts/common/InlineResetTextField.vue';

defineProps<{
  chart: ChartSpec;
  chartTypeOptions: Array<{ label: string; value: ChartType; icon: string }>;
  hideHeading?: boolean;
}>();

const emit = defineEmits<{
  typeSelect: [value: ChartType];
  updateTitle: [value: string];
  clearTitle: [];
}>();
</script>

<template>
  <div class="form-section">
    <div v-if="!hideHeading" class="section-title">Basics</div>
    <div class="grid">
      <div class="col-12">
        <div class="ui-chart-field-label">
          Chart Type
          <AppTooltip :text="TOOLTIPS.CHART_TYPE" />
        </div>
        <div class="chart-type-toggle">
          <Button
            v-for="opt in chartTypeOptions"
            :key="opt.value"
            :label="opt.label"
            :icon="opt.icon"
            :severity="chart.chartType === opt.value ? 'primary' : 'secondary'"
            :outlined="chart.chartType !== opt.value"
            size="small"
            class="chart-type-btn"
            @click="emit('typeSelect', opt.value)"
          />
        </div>
        <small v-if="!chart.chartType" class="ui-chart-help-text">Select a type to configure this chart.</small>
      </div>
      <div v-if="chart.chartType" class="col-12">
        <label class="ui-chart-field-label" :for="`chart-${chart.id}-title`">Chart Title</label>
        <InlineResetTextField
          :modelValue="chart.title"
          :inputId="`chart-${chart.id}-title`"
          placeholder="Enter chart title"
          :disabled="!chart.title"
          ariaLabel="Clear chart title"
          @update:modelValue="(v) => emit('updateTitle', v ?? '')"
          @clear="emit('clearTitle')"
        />
      </div>
    </div>
  </div>
</template>
