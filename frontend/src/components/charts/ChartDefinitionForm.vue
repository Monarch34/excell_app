<script setup lang="ts">
import { defineAsyncComponent, onMounted, reactive, watch } from 'vue';
import type { ChartSpec } from '@/types/domain';
import { useChartDefinitionForm } from '@/composables/charts/useChartDefinitionForm';
import ChartBasicsSection from '@/components/charts/sections/ChartBasicsSection.vue';
import ChartAxesSection from '@/components/charts/sections/ChartAxesSection.vue';
import ChartStyleSection from '@/components/charts/sections/ChartStyleSection.vue';

const ChartBaselineDialog = defineAsyncComponent(
  () => import('@/components/charts/sections/ChartBaselineDialog.vue')
);

const props = defineProps<{
  chart: ChartSpec;
  availableColumns: string[];
}>();

const emit = defineEmits<{
  update: [updates: Partial<ChartSpec>];
}>();

const update = (updates: Partial<ChartSpec>) => emit('update', updates);

const vm = useChartDefinitionForm(props.chart, update);

type SectionState = {
  basics: boolean;
  axes: boolean;
  style: boolean;
};

const defaultSectionState = (): SectionState => ({
  basics: true,
  axes: true,
  style: false,
});

const expanded = reactive<SectionState>(defaultSectionState());

const storageKeyForType = (chartType: ChartSpec['chartType']) => `charts.form.sections.${chartType ?? 'none'}`;

const applySectionState = (raw: unknown) => {
  const defaults = defaultSectionState();

  if (!raw || typeof raw !== 'object') {
    Object.assign(expanded, defaults);
    return;
  }

  const state = raw as Partial<SectionState>;
  Object.assign(expanded, {
    basics: typeof state.basics === 'boolean' ? state.basics : defaults.basics,
    axes: typeof state.axes === 'boolean' ? state.axes : defaults.axes,
    style: typeof state.style === 'boolean' ? state.style : defaults.style,
  });
};

const loadSectionsState = (chartType: ChartSpec['chartType']) => {
  try {
    const raw = localStorage.getItem(storageKeyForType(chartType));
    applySectionState(raw ? JSON.parse(raw) : null);
  } catch {
    applySectionState(null);
  }
};

const saveSectionsState = (chartType: ChartSpec['chartType']) => {
  try {
    localStorage.setItem(storageKeyForType(chartType), JSON.stringify({ ...expanded }));
  } catch {
    // ignore localStorage errors
  }
};

onMounted(() => {
  loadSectionsState(props.chart.chartType);
});

watch(
  () => props.chart.chartType,
  (chartType) => {
    loadSectionsState(chartType);
  },
);

watch(
  expanded,
  () => {
    saveSectionsState(props.chart.chartType);
  },
  { deep: true },
);
</script>

<template>
  <div class="chart-definition-form">
    <section class="chart-collapsible">
      <button
        type="button"
        class="chart-collapse-trigger"
        :aria-expanded="expanded.basics"
        @click="expanded.basics = !expanded.basics"
      >
        <span>Basics</span>
        <i class="pi" :class="expanded.basics ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true" />
      </button>
      <div v-show="expanded.basics" class="chart-collapse-content">
        <ChartBasicsSection
          :chart="chart"
          :chartTypeOptions="vm.chartTypeOptions"
          hideHeading
          @typeSelect="vm.handleTypeSelect"
          @updateTitle="(v) => update({ title: v })"
          @clearTitle="update({ title: '' })"
        />
      </div>
    </section>

    <section v-if="chart.chartType" class="chart-collapsible">
      <button
        type="button"
        class="chart-collapse-trigger"
        :aria-expanded="expanded.axes"
        @click="expanded.axes = !expanded.axes"
      >
        <span>Axes</span>
        <i class="pi" :class="expanded.axes ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true" />
      </button>
      <div v-show="expanded.axes" class="chart-collapse-content">
        <ChartAxesSection
          :chart="chart"
          :availableColumns="availableColumns"
          hideHeading
          @openConfigure="vm.configDialogOpen.value = true"
          @resetAxes="vm.resetAxes"
          @updateXColumn="(v) => update({ xColumn: v })"
          @updateYColumns="(v) => update({ yColumns: v })"
          @updateXAxisLabel="(v) => update({ xAxisLabel: v })"
          @updateYAxisLabel="(v) => update({ yAxisLabel: v })"
          @resetXAxisLabel="update({ xAxisLabel: '' })"
          @resetYAxisLabel="update({ yAxisLabel: '' })"
        />
      </div>
    </section>

    <section v-if="chart.chartType" class="chart-collapsible">
      <button
        type="button"
        class="chart-collapse-trigger"
        :aria-expanded="expanded.style"
        @click="expanded.style = !expanded.style"
      >
        <span>{{ vm.styleTitle.value }}</span>
        <i class="pi" :class="expanded.style ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true" />
      </button>
      <div v-show="expanded.style" class="chart-collapse-content">
        <ChartStyleSection
          :chart="chart"
          :strokeLabel="vm.strokeLabel.value"
          :styleTitle="vm.styleTitle.value"
          :colorPresets="vm.colorPresets"
          :stripHash="vm.stripHash"
          hideHeading
          @resetStyle="vm.resetStyle"
          @lineColorChange="vm.handleLineColorChange"
          @fillColorChange="vm.handleFillColorChange"
          @applyLineColor="vm.applyLineColor"
          @applyFillColor="vm.applyFillColor"
          @resetLineColor="update({ lineColor: null })"
          @resetFillColor="update({ fillColor: null })"
          @setFillOpacity="(v) => update({ fillOpacity: v })"
          @setLineWidth="(v) => update({ lineWidth: v })"
          @setMarkerSize="(v) => update({ markerSize: v })"
          @resetFillOpacity="update({ fillOpacity: 0.4 })"
          @resetLineWidth="update({ lineWidth: 2 })"
          @resetMarkerSize="update({ markerSize: 8 })"
          @updateAreaSpec="vm.updateAreaSpec"
        />
      </div>
    </section>

    <ChartBaselineDialog
      :visible="vm.configDialogOpen.value"
      :chart="chart"
      @update:visible="(v) => (vm.configDialogOpen.value = v)"
      @updateBaselineSpec="vm.updateBaselineSpec"
      @updateAreaSpec="vm.updateAreaSpec"
    />
  </div>
</template>
