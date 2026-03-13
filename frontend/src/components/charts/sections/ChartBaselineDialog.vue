<script setup lang="ts">
import AppDialogSurface from '@/components/ui/AppDialogSurface.vue';
import type { AreaSpec, BaselineRegion, BaselineSpec, ChartSpec } from '@/types/domain';
import BaselineRegionSelector from '@/components/charts/sections/baseline/BaselineRegionSelector.vue';
import InlineResetNumberField from '@/components/charts/common/InlineResetNumberField.vue';
import type { CSSProperties } from 'vue';

defineProps<{
  visible: boolean;
  chart: ChartSpec;
}>();

const emit = defineEmits<{
  'update:visible': [visible: boolean];
  updateBaselineSpec: [updates: Partial<BaselineSpec>];
  updateAreaSpec: [updates: Partial<AreaSpec>];
}>();

const regionOptions: Array<{ label: string; value: BaselineRegion }> = [
  { label: 'Top-Left', value: 'top-left' },
  { label: 'Top-Right', value: 'top-right' },
  { label: 'Bottom-Left', value: 'bottom-left' },
  { label: 'Bottom-Right', value: 'bottom-right' },
];
const NUMBER_MIN = -1000000000;
const NUMBER_MAX = 1000000000;
const dialogStyle: CSSProperties = { width: 'min(92vw, 48rem)' };
const dialogContentStyle: CSSProperties = { maxHeight: 'min(72vh, 42rem)', overflowY: 'auto' };
const dialogBreakpoints = { '960px': '90vw', '640px': '96vw' };

function baselineSummary(chart: ChartSpec): string {
  const effectiveRegions = (chart.baselineSpec?.regions ?? []).filter((r) => r !== 'all');
  const regionLabel = effectiveRegions.length === 0
    ? 'All'
    : effectiveRegions
      .map((r) => r.split('-').map((part) => part[0].toUpperCase() + part.slice(1)).join('-'))
      .join(' + ');
  return `Regions: ${regionLabel}`;
}

function getSelectedRegions(chart: ChartSpec): BaselineRegion[] {
  return (chart.baselineSpec?.regions ?? []).filter((r): r is BaselineRegion => r !== 'all');
}

function updateSelectedRegions(chart: ChartSpec, regions: BaselineRegion[]) {
  if (regions.length === 0) {
    emit('updateBaselineSpec', { regions: [] });
    if (chart.chartType === 'area') emit('updateAreaSpec', { mode: 'total', baselineAxis: 'y' });
    return;
  }
  const allTop = regions.every((r) => r.startsWith('top-'));
  const allBottom = regions.every((r) => r.startsWith('bottom-'));
  const mode = allTop ? 'positive' : allBottom ? 'negative' : 'total';
  emit('updateBaselineSpec', { regions });
  if (chart.chartType === 'area') emit('updateAreaSpec', { mode, baselineAxis: 'y' });
}

function toggleRegion(chart: ChartSpec, region: BaselineRegion) {
  const current = getSelectedRegions(chart);
  const next = current.includes(region)
    ? current.filter((r) => r !== region)
    : [...current, region];
  updateSelectedRegions(chart, next);
}

function selectAllRegions(chart: ChartSpec) {
  updateSelectedRegions(chart, [...regionOptions.map((opt) => opt.value)]);
}

function clearRegions(chart: ChartSpec) {
  updateSelectedRegions(chart, []);
}
</script>

<template>
  <AppDialogSurface
    :visible="visible"
    header="Reference Baseline"
    modal
    :style="dialogStyle"
    :contentStyle="dialogContentStyle"
    :breakpoints="dialogBreakpoints"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="ui-baseline-dialog-panel ui-baseline-dialog-stack">
      <div class="chart-dialog-subtitle">Baseline</div>
      <div class="text-color-secondary text-sm ui-baseline-dialog-note">
        Set reference lines for this chart. Region selection filters chart display for all chart types.
      </div>
      <div class="ui-baseline-dialog-grid">
        <div class="ui-baseline-fields">
          <div class="chart-dialog-field">
            <label class="ui-chart-field-label" :for="`chart-${chart.id}-baseline-x`">X Line (x = c)</label>
            <InlineResetNumberField
              :modelValue="chart.baselineSpec?.xBaseline ?? 0"
              :inputId="`chart-${chart.id}-baseline-x`"
              placeholder="0"
              :min="NUMBER_MIN"
              :max="NUMBER_MAX"
              :disabled="(chart.baselineSpec?.xBaseline ?? 0) === 0"
              ariaLabel="Reset X line value"
              @update:modelValue="(v) => emit('updateBaselineSpec', { xBaseline: v ?? 0 })"
              @clear="emit('updateBaselineSpec', { xBaseline: 0 })"
            />
          </div>
          <div class="chart-dialog-field">
            <label class="ui-chart-field-label" :for="`chart-${chart.id}-baseline-y`">Y Line (y = c)</label>
            <InlineResetNumberField
              :modelValue="chart.baselineSpec?.yBaseline ?? 0"
              :inputId="`chart-${chart.id}-baseline-y`"
              placeholder="0"
              :min="NUMBER_MIN"
              :max="NUMBER_MAX"
              :disabled="(chart.baselineSpec?.yBaseline ?? 0) === 0"
              ariaLabel="Reset Y line value"
              @update:modelValue="(v) => emit('updateBaselineSpec', { yBaseline: v ?? 0 })"
              @clear="emit('updateBaselineSpec', { yBaseline: 0 })"
            />
          </div>
        </div>
        <BaselineRegionSelector
          :selectedRegions="getSelectedRegions(chart)"
          @toggle="(region) => toggleRegion(chart, region)"
          @selectAll="selectAllRegions(chart)"
          @clear="clearRegions(chart)"
        />
        <div class="ui-baseline-summary-row">
          <span class="ui-baseline-summary-chip">x = {{ chart.baselineSpec?.xBaseline ?? 0 }}</span>
          <span class="ui-baseline-summary-chip">y = {{ chart.baselineSpec?.yBaseline ?? 0 }}</span>
          <span class="ui-baseline-summary-chip">{{ baselineSummary(chart) }}</span>
        </div>
      </div>
    </div>
  </AppDialogSurface>
</template>
