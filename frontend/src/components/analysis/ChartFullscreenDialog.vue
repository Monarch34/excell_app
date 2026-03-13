<script setup lang="ts">
import { defineAsyncComponent } from 'vue';
import AppDialogSurface from '@/components/ui/AppDialogSurface.vue';
import type { ChartSpec } from '@/types/domain';
import type { CSSProperties } from 'vue';

const ChartRenderer = defineAsyncComponent(() => import('@/components/charts/ChartRenderer.vue'));

defineProps<{
  visible: boolean;
  chart: ChartSpec | null;
  data: Record<string, unknown>[];
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
}>();

const dialogStyle: CSSProperties = { width: 'min(96vw, 1200px)' };
const dialogBreakpoints = { '960px': '96vw', '640px': '98vw' };
</script>

<template>
  <AppDialogSurface
    class="chart-fullscreen-dialog"
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    :modal="true"
    :maximizable="true"
    :style="dialogStyle"
    :breakpoints="dialogBreakpoints"
    :header="chart?.title || 'Chart'"
    :closable="true"
  >
    <div v-if="chart" class="ui-chart-fullscreen-body">
      <ChartRenderer
        :spec="chart"
        :data="data"
        height="100%"
      />
    </div>
  </AppDialogSurface>
</template>
