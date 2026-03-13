<script setup lang="ts">
import ColorPicker from 'primevue/colorpicker';
import Slider from 'primevue/slider';
import Button from 'primevue/button';
import type { AreaSpec, ChartSpec } from '@/shared/types/domain';
import InlineResetTextField from '@/features/charts/common/InlineResetTextField.vue';
import { DEFAULT_CHART_COLOR } from '@/constants/chartColors';

defineProps<{
  chart: ChartSpec;
  strokeLabel: string;
  styleTitle: string;
  colorPresets: string[];
  stripHash: (color: string | null) => string | undefined;
  hideHeading?: boolean;
}>();

const emit = defineEmits<{
  resetStyle: [];
  lineColorChange: [value: string | undefined];
  fillColorChange: [value: string | undefined];
  applyLineColor: [value: string];
  applyFillColor: [value: string];
  resetLineColor: [];
  resetFillColor: [];
  setFillOpacity: [value: number];
  setLineWidth: [value: number];
  setMarkerSize: [value: number];
  resetFillOpacity: [];
  resetLineWidth: [];
  resetMarkerSize: [];
  updateAreaSpec: [updates: Partial<AreaSpec>];
}>();
</script>

<template>
  <div v-if="chart.chartType" class="form-section">
    <div v-if="!hideHeading" class="section-header">
      <div class="section-title">{{ styleTitle }}</div>
    </div>
    <div class="style-subsection">
      <div class="subsection-title">Colors</div>
      <div class="grid">
        <div class="col-12 md:col-6">
          <label class="ui-chart-field-label" :for="`chart-${chart.id}-line-color`">{{ strokeLabel }}</label>
          <div class="chart-color-input-row">
            <ColorPicker
              :modelValue="stripHash(chart.lineColor)"
              @update:modelValue="(v) => emit('lineColorChange', v as string | undefined)"
            />
            <InlineResetTextField
              class="w-full"
              :modelValue="chart.lineColor || DEFAULT_CHART_COLOR"
              :inputId="`chart-${chart.id}-line-color`"
              placeholder="#RRGGBB"
              :maxLength="7"
              :disabled="!chart.lineColor"
              ariaLabel="Reset line color"
              @update:modelValue="(v) => emit('lineColorChange', v)"
              @clear="emit('resetLineColor')"
            />
          </div>
          <div class="chart-color-swatches">
            <button
              v-for="color in colorPresets"
              :key="`line-${color}`"
              class="chart-color-swatch"
              :style="{ backgroundColor: color }"
              type="button"
              @click="emit('applyLineColor', color)"
              aria-label="Set line color"
            />
          </div>
        </div>

        <div v-if="chart.chartType === 'area'" class="col-12 md:col-6">
          <label class="ui-chart-field-label" :for="`chart-${chart.id}-fill-color`">Fill Color</label>
          <div class="chart-color-input-row">
            <ColorPicker
              :modelValue="stripHash(chart.fillColor)"
              @update:modelValue="(v) => emit('fillColorChange', v as string | undefined)"
            />
            <InlineResetTextField
              class="w-full"
              :modelValue="chart.fillColor || DEFAULT_CHART_COLOR"
              :inputId="`chart-${chart.id}-fill-color`"
              placeholder="#RRGGBB"
              :maxLength="7"
              :disabled="!chart.fillColor"
              ariaLabel="Reset fill color"
              @update:modelValue="(v) => emit('fillColorChange', v)"
              @clear="emit('resetFillColor')"
            />
          </div>
          <div class="chart-color-swatches">
            <button
              v-for="color in colorPresets"
              :key="`fill-${color}`"
              class="chart-color-swatch"
              :style="{ backgroundColor: color }"
              type="button"
              @click="emit('applyFillColor', color)"
              aria-label="Set fill color"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="style-subsection">
      <div class="subsection-title">Stroke</div>
      <div class="grid">
        <div v-if="chart.chartType === 'line' || chart.chartType === 'area'" class="col-12 md:col-6">
          <div class="ui-chart-field-label">Line Width</div>
          <div class="ui-style-slider-head">
            <small class="ui-chart-help-text">Width: {{ chart.lineWidth ?? 2 }}</small>
            <Button
              icon="pi pi-times"
              severity="secondary"
              text
              :disabled="(chart.lineWidth ?? 2) === 2"
              @click="emit('resetLineWidth')"
              aria-label="Reset line width"
            />
          </div>
          <Slider
            :modelValue="chart.lineWidth ?? 2"
            :min="1"
            :max="6"
            :step="1"
            class="w-full ui-style-slider"
            @update:modelValue="(v: number | number[]) => emit('setLineWidth', Array.isArray(v) ? v[0] : v)"
          />
        </div>
        <div v-if="chart.chartType === 'area' && chart.areaSpec" class="col-12 md:col-6">
          <label class="ui-chart-field-label" :for="`chart-${chart.id}-area-result-name`">Result Name</label>
          <InlineResetTextField
            class="w-full"
            :modelValue="chart.areaSpec.label || ''"
            :inputId="`chart-${chart.id}-area-result-name`"
            placeholder="e.g. Energy Absorption"
            :disabled="false"
            ariaLabel="Reset result name"
            @update:modelValue="(v) => emit('updateAreaSpec', { label: v ?? '' })"
            @clear="emit('updateAreaSpec', { label: '' })"
          />
        </div>
        <div v-else-if="chart.chartType === 'scatter'" class="col-12 md:col-6">
          <div class="ui-chart-field-label">Marker Size</div>
          <div class="ui-style-slider-head">
            <small class="ui-chart-help-text">Size: {{ chart.markerSize ?? 8 }}</small>
            <Button
              icon="pi pi-times"
              severity="secondary"
              text
              :disabled="(chart.markerSize ?? 8) === 8"
              @click="emit('resetMarkerSize')"
              aria-label="Reset marker size"
            />
          </div>
          <Slider
            :modelValue="chart.markerSize ?? 8"
            :min="3"
            :max="20"
            :step="1"
            class="w-full ui-style-slider"
            @update:modelValue="(v: number | number[]) => emit('setMarkerSize', Array.isArray(v) ? v[0] : v)"
          />
        </div>
      </div>
    </div>

    <div v-if="chart.chartType === 'area'" class="style-subsection">
      <div class="subsection-title">Fill</div>
      <div class="grid">
        <div class="col-12 md:col-6">
          <div class="ui-style-slider-head">
            <div class="ui-chart-field-label ui-chart-field-label--inline">Opacity: {{ Math.round((chart.fillOpacity ?? 0.4) * 100) }}%</div>
            <Button
              icon="pi pi-times"
              severity="secondary"
              text
              :disabled="(chart.fillOpacity ?? 0.4) === 0.4"
              @click="emit('resetFillOpacity')"
              aria-label="Reset opacity"
            />
          </div>
          <Slider
            :modelValue="(chart.fillOpacity ?? 0.4) * 100"
            :min="0"
            :max="100"
            :step="5"
            class="w-full ui-style-slider ui-style-slider--spaced"
            @update:modelValue="(v: number | number[]) => emit('setFillOpacity', (Array.isArray(v) ? v[0] : v) / 100)"
          />
        </div>
      </div>
    </div>

    <div class="ui-chart-section-footer-actions ui-chart-section-footer-actions--end">
      <Button label="Reset Style" severity="secondary" text size="small" class="action-btn" @click="emit('resetStyle')" />
    </div>
  </div>
</template>
