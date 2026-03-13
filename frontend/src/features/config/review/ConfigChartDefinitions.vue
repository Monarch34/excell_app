<script setup lang="ts">
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import Tag from 'primevue/tag';
import type { AnalysisConfig, ChartSpec } from '@/shared/types/domain';
import { normalizeColorToHex } from '@/utils/color';

defineProps<{
  config: AnalysisConfig;
}>();

const previewLinePath = 'M10 56 L34 38 L62 44 L92 24 L124 31 L158 14';
const previewAreaPath = 'M10 56 L34 38 L62 44 L92 24 L124 31 L158 14 L158 58 L10 58 Z';
const previewScatterPoints = [
  [22, 50],
  [52, 36],
  [82, 42],
  [112, 26],
  [142, 18],
] as const;

function getChartType(chart: ChartSpec): string {
  return chart.chartType || 'line';
}

function getLineColor(chart: ChartSpec): string {
  return chart.lineColor || 'var(--primary-500)';
}

function getFillColor(chart: ChartSpec): string {
  return chart.fillColor || chart.lineColor || 'var(--primary-300)';
}

function getFillOpacity(chart: ChartSpec): number {
  if (chart.fillOpacity != null) return chart.fillOpacity;
  return getChartType(chart) === 'area' ? 0.3 : 0.18;
}

function getLineWidth(chart: ChartSpec): number {
  if (chart.lineWidth != null && Number.isFinite(chart.lineWidth)) {
    return Math.max(1, Math.min(6, chart.lineWidth));
  }
  return 2;
}

function getMarkerSize(chart: ChartSpec): number {
  if (chart.markerSize != null && Number.isFinite(chart.markerSize)) {
    return Math.max(4, Math.min(16, chart.markerSize));
  }
  return 8;
}

function getAnnotationCount(chart: ChartSpec): number {
  return chart.annotations?.length ?? 0;
}

function getYAxisText(chart: ChartSpec): string {
  return chart.yColumns?.length ? chart.yColumns.join(', ') : 'Not defined';
}

function getBaselineText(chart: ChartSpec): string {
  if (!chart.baselineSpec) return 'None';
  return `X=${chart.baselineSpec.xBaseline}, Y=${chart.baselineSpec.yBaseline}`;
}

function getPrimaryColorLabel(chart: ChartSpec): string {
  return getChartType(chart) === 'scatter' ? 'Marker' : 'Line';
}

function isDefaultPrimaryColor(chart: ChartSpec): boolean {
  return !chart.lineColor?.trim();
}

function isDefaultFillColor(chart: ChartSpec): boolean {
  return !chart.fillColor?.trim();
}

function getPreviewFillOpacity(chart: ChartSpec): number {
  const effective = getFillOpacity(chart);
  if (getChartType(chart) !== 'area') return effective;
  return Math.max(0.35, effective);
}

function resolveColorValue(color: string): string {
  const trimmed = color.trim();
  if (!trimmed.startsWith('var(') || typeof window === 'undefined') return trimmed;

  const varNameMatch = trimmed.match(/var\((--[^,\s)]+)/);
  if (!varNameMatch) return trimmed;

  const resolved = window
    .getComputedStyle(document.documentElement)
    .getPropertyValue(varNameMatch[1])
    .trim();

  return resolved || trimmed;
}

function getColorText(color: string, isDefault = false): string {
  const resolved = resolveColorValue(color);
  const normalized = normalizeColorToHex(resolved)?.toUpperCase() ?? 'Not defined';
  return isDefault ? `${normalized} (default)` : normalized;
}
</script>

<template>
  <div class="cfg-section-body">
    <div class="ui-chart-list ui-clamp-gap-md">
      <AppSurfacePanel
        v-for="chart in config.charts"
        :key="chart.id"
        as="section"
        tone="chart"
        class="ui-chart-card"
      >
        <div class="ui-chart-card-header ui-chart-card-header-row">
          <div class="ui-chart-card-title-wrap">
            <i class="pi pi-chart-line text-primary"></i>
            <span class="font-bold ui-chart-card-title">{{ chart.title || 'Untitled Chart' }}</span>
          </div>
          <div class="ui-chart-card-actions">
            <Tag :value="getChartType(chart)" severity="info" class="text-xs" />
          </div>
        </div>

        <div class="ui-chart-card-body">
          <div class="ui-chart-preview-header">
            <div class="ui-chart-preview-label">
              <i class="pi pi-eye text-color-secondary"></i>
              <span class="font-medium text-color">Preview</span>
            </div>
            <Tag value="Configured" severity="success" class="text-xs" />
          </div>

          <div class="cfg-chart-preview" aria-hidden="true">
            <svg class="cfg-chart-preview-svg" viewBox="0 0 168 64" role="img">
              <rect x="1" y="1" width="166" height="62" rx="6" class="cfg-chart-preview-bg"></rect>
              <line x1="10" y1="58" x2="158" y2="58" class="cfg-chart-preview-axis"></line>
              <line x1="10" y1="8" x2="10" y2="58" class="cfg-chart-preview-axis"></line>

              <path
                v-if="getChartType(chart) === 'area'"
                :d="previewAreaPath"
                :fill="getFillColor(chart)"
                :opacity="getPreviewFillOpacity(chart)"
              ></path>

              <path
                v-if="getChartType(chart) !== 'scatter'"
                :d="previewLinePath"
                fill="none"
                :stroke="getLineColor(chart)"
                :stroke-width="getLineWidth(chart)"
                stroke-linecap="round"
                stroke-linejoin="round"
              ></path>

              <g v-if="getChartType(chart) === 'scatter'">
                <circle
                  v-for="[cx, cy] in previewScatterPoints"
                  :key="`${chart.id}-${cx}-${cy}`"
                  :cx="cx"
                  :cy="cy"
                  :r="Math.max(2, getMarkerSize(chart) / 3)"
                  :fill="getLineColor(chart)"
                ></circle>
              </g>
            </svg>
          </div>

          <div class="cfg-chart-info-grid">
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">X Axis</span>
              <span class="cfg-chart-info-value">{{ chart.xAxisLabel || chart.xColumn || 'Not defined' }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Y Axis</span>
              <span class="cfg-chart-info-value">{{ chart.yAxisLabel || getYAxisText(chart) }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Series</span>
              <span class="cfg-chart-info-value">{{ chart.yColumns?.length || 0 }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Line Width</span>
              <span class="cfg-chart-info-value">{{ getLineWidth(chart) }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Marker Size</span>
              <span class="cfg-chart-info-value">{{ getMarkerSize(chart) }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Fill Opacity</span>
              <span class="cfg-chart-info-value">{{ getFillOpacity(chart) }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Baseline</span>
              <span class="cfg-chart-info-value">{{ getBaselineText(chart) }}</span>
            </div>
            <div class="cfg-chart-info-item">
              <span class="cfg-chart-info-label">Annotations</span>
              <span class="cfg-chart-info-value">{{ getAnnotationCount(chart) }}</span>
            </div>
          </div>

          <div class="cfg-chart-colors cfg-chart-colors--detail">
            <span class="cfg-chart-color-item cfg-chart-color-item--primary">
              <span class="cfg-chart-color-swatch" :style="{ background: getLineColor(chart) }"></span>
              <span class="cfg-chart-color-text">
                {{ getPrimaryColorLabel(chart) }} {{ getColorText(getLineColor(chart), isDefaultPrimaryColor(chart)) }}
              </span>
            </span>
            <span v-if="getChartType(chart) === 'area'" class="cfg-chart-color-item">
              <span class="cfg-chart-color-swatch" :style="{ background: getFillColor(chart) }"></span>
              <span class="cfg-chart-color-text">
                Fill {{ getColorText(getFillColor(chart), isDefaultFillColor(chart)) }}
              </span>
            </span>
          </div>
        </div>
      </AppSurfacePanel>
    </div>
  </div>
</template>
