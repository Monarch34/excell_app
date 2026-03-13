<script setup lang="ts">
import Button from 'primevue/button';
import Select from 'primevue/select';
import MultiSelect from 'primevue/multiselect';
import InlineResetTextField from '@/features/charts/common/InlineResetTextField.vue';
import type { ChartSpec } from '@/shared/types/domain';

defineProps<{
  chart: ChartSpec;
  availableColumns: string[];
  hideHeading?: boolean;
}>();

const emit = defineEmits<{
  openConfigure: [];
  resetAxes: [];
  updateXColumn: [value: string];
  updateYColumns: [value: string[]];
  updateXAxisLabel: [value: string];
  updateYAxisLabel: [value: string];
  resetXAxisLabel: [];
  resetYAxisLabel: [];
}>();
</script>

<template>
  <div v-if="chart.chartType" class="form-section">
    <div v-if="!hideHeading" class="section-header">
      <div class="section-title">Axes</div>
    </div>
    <div class="grid axes-grid">
      <div class="col-12 md:col-6 axes-field">
        <label class="ui-chart-field-label" :for="`chart-${chart.id}-x-column`">X Column</label>
        <Select
          :modelValue="chart.xColumn"
          :inputId="`chart-${chart.id}-x-column`"
          :options="availableColumns"
          class="w-full compact-field"
          appendTo="body"
          placeholder="Select X axis"
          @update:modelValue="(v: string) => emit('updateXColumn', v)"
        />
      </div>
      <div class="col-12 md:col-6 axes-field">
        <label class="ui-chart-field-label" :for="`chart-${chart.id}-y-columns`">Y Column(s)</label>
        <MultiSelect
          :modelValue="chart.yColumns"
          :inputId="`chart-${chart.id}-y-columns`"
          :options="availableColumns"
          :showToggleAll="false"
          class="w-full compact-field"
          appendTo="body"
          placeholder="Select Y axis"
          @update:modelValue="(v: string[]) => emit('updateYColumns', v)"
        />
      </div>
      <div class="col-12 md:col-6 axes-field">
        <label class="ui-chart-field-label" :for="`chart-${chart.id}-x-axis-name`">X Axis Name</label>
        <InlineResetTextField
          :modelValue="chart.xAxisLabel || ''"
          :inputId="`chart-${chart.id}-x-axis-name`"
          class="w-full"
          placeholder="Optional custom X axis name"
          :disabled="!(chart.xAxisLabel && chart.xAxisLabel.trim().length > 0)"
          ariaLabel="Reset X axis name"
          @update:modelValue="(v) => emit('updateXAxisLabel', v ?? '')"
          @clear="emit('resetXAxisLabel')"
        />
      </div>
      <div class="col-12 md:col-6 axes-field">
        <label class="ui-chart-field-label" :for="`chart-${chart.id}-y-axis-name`">Y Axis Name</label>
        <InlineResetTextField
          :modelValue="chart.yAxisLabel || ''"
          :inputId="`chart-${chart.id}-y-axis-name`"
          class="w-full"
          placeholder="Optional custom Y axis name"
          :disabled="!(chart.yAxisLabel && chart.yAxisLabel.trim().length > 0)"
          ariaLabel="Reset Y axis name"
          @update:modelValue="(v) => emit('updateYAxisLabel', v ?? '')"
          @clear="emit('resetYAxisLabel')"
        />
      </div>
    </div>

    <small v-if="!chart.xColumn || chart.yColumns.length === 0" class="ui-chart-help-text">
      Select X and Y columns to enable preview.
    </small>

    <div class="ui-chart-section-footer-actions">
      <Button label="Baseline" severity="secondary" text size="small" class="action-btn" @click="emit('openConfigure')" />
      <Button label="Reset Axes" severity="secondary" text size="small" class="action-btn" @click="emit('resetAxes')" />
    </div>
  </div>
</template>
