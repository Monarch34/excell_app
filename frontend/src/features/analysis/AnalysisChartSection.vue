<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import type { ChartSpec } from '@/shared/types/domain';
import { chartDataReady } from '@/utils/chart';

const ChartRenderer = defineAsyncComponent(() => import('@/features/charts/ChartRenderer.vue'));

const props = defineProps<{
  chart: ChartSpec;
  data: Record<string, unknown>[];
}>();

const emit = defineEmits<{
  fullscreen: [];
}>();

const chartColumnsExist = computed(() => chartDataReady(props.chart, props.data));
</script>

<template>
  <div class="ui-analysis-chart-section">
    <AppSurfacePanel as="section" tone="chart" class="ui-chart-card" interactive>
      <div class="ui-chart-card-header ui-chart-card-header-row">
        <div class="ui-chart-card-title-wrap">
          <i class="pi pi-chart-line text-primary"></i>
          <span class="font-bold ui-chart-card-title">{{ chart.title || 'Untitled Chart' }}</span>
        </div>
        <div class="ui-chart-card-actions">
          <Tag
            v-if="chartColumnsExist"
            value="Ready"
            severity="success"
            class="text-xs"
          />
          <Tag
            v-else-if="!chart.xColumn || chart.yColumns.length === 0"
            value="Needs X/Y"
            severity="warning"
            class="text-xs"
          />
          <Tag
            v-else
            value="Needs Analysis"
            severity="info"
            class="text-xs"
          />
          <Button
            icon="pi pi-expand"
            severity="secondary"
            text
            size="small"
            class="ui-action-icon-btn"
            aria-label="Open chart fullscreen"
            @click="emit('fullscreen')"
            v-tooltip.top="'Full screen'"
          />
        </div>
      </div>

      <div class="ui-chart-card-body">
        <div class="ui-chart-preview-header">
          <div class="ui-chart-preview-label">
            <i class="pi pi-eye text-color-secondary"></i>
            <span class="font-medium text-color">Preview</span>
          </div>
        </div>

        <div v-if="chartColumnsExist" class="ui-analysis-chart-renderer">
        <ChartRenderer
          :spec="chart"
          :data="data"
          height="clamp(280px, 54vh, 480px)"
        />
        </div>
        <div v-else-if="!chart.chartType" class="ui-chart-empty-preview ui-chart-empty-preview--simple text-center text-color-secondary text-sm">
          Select a chart type to configure this chart
        </div>
        <div v-else-if="!chart.xColumn || chart.yColumns.length === 0" class="ui-chart-empty-preview ui-chart-empty-preview--simple text-center text-color-secondary text-sm">
          Configure X and Y columns in Charts &amp; Area to render this chart
        </div>
        <div v-else class="ui-chart-empty-preview ui-chart-empty-preview--analysis text-center">
          <i class="pi pi-info-circle text-primary ui-chart-empty-analysis-icon"></i>
          <p class="text-color-secondary text-sm ui-chart-empty-analysis-text">
            Chart preview will be available after running analysis.
            <br />
            <span class="text-xs">Columns <strong>{{ chart.xColumn }}</strong> and <strong>{{ chart.yColumns.join(', ') }}</strong> need to be computed first.</span>
          </p>
        </div>
      </div>
    </AppSurfacePanel>
  </div>
</template>
