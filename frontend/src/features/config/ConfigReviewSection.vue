<script setup lang="ts">
import { computed, ref } from 'vue';
import Button from 'primevue/button';
import AppStepSection from '@/shared/components/ui/AppStepSection.vue';
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import { isBuiltinTypeParameter, type DependencyKind, type ConfigDependencyModel, type FormulaTreeNode, type FormulaTreeEntry } from '@/domain/configDependency';
import { buildConfigReviewModel } from '@/domain/configReviewModel';
import type { SavedConfigDetail } from '@/services/configsApi';
import type { AnalysisConfig } from '@/shared/types/domain';

// Import newly extracted child components
import ConfigIdentityCard from './review/ConfigIdentityCard.vue';
import ConfigColumnStructure from './review/ConfigColumnStructure.vue';
import ConfigStaticParameters from './review/ConfigStaticParameters.vue';
import ConfigExecutedCalculations from './review/ConfigExecutedCalculations.vue';
import ConfigChartDefinitions from './review/ConfigChartDefinitions.vue';

const props = defineProps<{
  selectedLoading: boolean;
  selectedConfig: AnalysisConfig | null;
  selectedDetail: SavedConfigDetail | null;
  configDependency: ConfigDependencyModel | null;
  selectedParamValues: Map<string, { value: number; unit: string }>;
  formatDate: (value: string | null | undefined) => string;
  dependencyKindLabel: (kind: DependencyKind) => string;
  dependencyChipClass: (kind: DependencyKind) => string;
}>();

const emit = defineEmits<{
  apply: [];
}>();

/* ── Collapsible section state ──────────────────────────────────────────────── */
const openSections = ref<Record<string, boolean>>({
  columns: true,
  params: false,
  formulas: true,
  charts: false,
});

function toggle(key: string) {
  openSections.value[key] = !openSections.value[key];
}

/* ── Helpers ────────────────────────────────────────────────────────────────── */
function getDerived(name: string) {
  return props.selectedConfig?.derivedColumns.find(d => d.name === name) ?? null;
}

/* ── Formula dependency trees ───────────────────────────────────────────────── */
const formulaTrees = computed<FormulaTreeEntry[]>(() => {
  if (!props.selectedConfig || !props.configDependency) return [];

  const formulaItemMap = new Map((props.configDependency?.derivedItems || []).map(f => [f.name, f]));

  function buildDependencyTree(depName: string, idPrefix: string, visited = new Set<string>()): FormulaTreeNode {
    if (visited.has(depName)) {
       return { key: `${idPrefix}-cyc-${depName}`, type: 'cycle', label: depName };
    }

    const nextVisited = new Set(visited).add(depName);
    const formulaItem = formulaItemMap.get(depName);

    if (formulaItem) {
      return {
        key: `${idPrefix}-form-${formulaItem.id}`,
        type: 'formula',
        label: formulaItem.name,
        data: { 
          formula: formulaItem.formula, 
          dataType: formulaItem.type === 'parameter' ? 'derived-parameter' : 'derived-column',
          details: formulaItem.type === 'parameter' ? 'Derived Parameter' : 'Derived Column' 
        },
        children: formulaItem.dependencies.map(d => buildDependencyTree(d.name, `${idPrefix}-form-${formulaItem.id}`, nextVisited))
      };
    }

    if (isBuiltinTypeParameter(depName) || (props.configDependency && !props.configDependency.inputColumns.includes(depName))) {
      return { key: `${idPrefix}-param-${depName}`, type: 'input', label: depName, data: { icon: 'pi-sliders-v', details: 'Base Parameter', dataType: 'parameter' } };
    }

    return { key: `${idPrefix}-col-${depName}`, type: 'input', label: depName, data: { icon: 'pi-table', details: 'Base Column', dataType: 'column' } };
  }

  return (props.configDependency?.derivedItems || []).map(f => {
    return {
      formula: f,
      derived: getDerived(f.name),
      treeData: buildDependencyTree(f.name, `root-${f.id}`)
    };
  });
});

const referencedParameterNames = computed(() => {
  if (!props.configDependency) return [];

  const ordered = new Set<string>(props.configDependency.inputParameters);

  for (const item of props.configDependency.derivedItems) {
    for (const dependency of item.dependencies) {
      if (dependency.kind === 'parameter') ordered.add(dependency.name);
    }
  }

  for (const chart of props.configDependency.charts) {
    if (chart.xDependency?.kind === 'parameter') ordered.add(chart.xDependency.name);
    for (const dependency of chart.yDependencies) {
      if (dependency.kind === 'parameter') ordered.add(dependency.name);
    }
  }

  return [...ordered];
});

const reviewModel = computed(() => {
  if (!props.selectedConfig) return null;
  return buildConfigReviewModel(
    props.selectedConfig,
    props.selectedParamValues,
    referencedParameterNames.value,
  );
});

const xrayHeaderIcon = computed(() => {
  if (props.selectedLoading) return 'pi-spinner pi-spin';
  if (props.selectedConfig && props.configDependency) return 'pi-search';
  return 'pi-search-plus';
});

</script>

<template>
  <AppStepSection
    :icon="xrayHeaderIcon"
    title="Configuration X-Ray"
    class="cfg-review-section"
    collapsible
    :initiallyOpen="true"
  >
    <template #action>
      <Button
        label="Apply Configuration"
        icon="pi pi-check"
        size="small"
        severity="primary"
        :disabled="!selectedConfig || selectedLoading"
        @click="emit('apply')"
      />
    </template>

    <div v-if="!selectedConfig || !configDependency" class="ui-empty-state text-center">
      <template v-if="selectedLoading">
        <i class="pi pi-spinner pi-spin cfg-review-loading-state-icon"></i>
      </template>
      <template v-else>
      <i class="pi pi-search" aria-hidden="true"></i>
      <div>Select a configuration to view its exact processing rules.</div>
      </template>
    </div>

    <div v-else class="cfg-review-content-shell">
      <div class="cfg-xray-wrap" :class="{ 'cfg-xray-wrap--loading': selectedLoading }" :aria-busy="selectedLoading" aria-live="polite">
      <!-- 1. Config Identity -->
      <ConfigIdentityCard 
        :config="selectedConfig" 
        :formatDate="formatDate" 
      />

      <!-- 2. Column Structure (Collapsible) -->
      <AppSurfacePanel class="cfg-section-panel">
        <button
          type="button"
          class="cfg-section-header cfg-section-header--plain"
          :aria-expanded="openSections.columns"
          aria-controls="cfg-section-columns"
          @click="toggle('columns')"
        >
          <div class="cfg-section-title-wrap">
            <i class="pi pi-table ui-color-info" aria-hidden="true"></i>
            <span class="cfg-section-title">Column Structure</span>
            <span class="cfg-count-badge">{{ reviewModel?.columns.length || 0 }}</span>
          </div>
          <i class="pi ui-action-icon-btn" :class="openSections.columns ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
        </button>

        <transition name="cfg-expand">
          <div v-if="openSections.columns && reviewModel" id="cfg-section-columns" role="region">
            <ConfigColumnStructure :reviewModel="reviewModel" />
          </div>
        </transition>
      </AppSurfacePanel>

      <!-- 3. Static Parameters (Collapsible) -->
      <AppSurfacePanel class="cfg-section-panel">
        <button
          type="button"
          class="cfg-section-header cfg-section-header--plain"
          :aria-expanded="openSections.params"
          aria-controls="cfg-section-params"
          @click="toggle('params')"
        >
          <div class="cfg-section-title-wrap">
            <i class="pi pi-sliders-v ui-color-warning" aria-hidden="true"></i>
            <span class="cfg-section-title">Static Parameters</span>
            <span class="cfg-count-badge">{{ reviewModel?.parameters.length || 0 }}</span>
          </div>
          <i class="pi ui-action-icon-btn" :class="openSections.params ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
        </button>

        <transition name="cfg-expand">
          <div v-if="openSections.params && reviewModel" id="cfg-section-params" role="region">
            <ConfigStaticParameters :reviewModel="reviewModel" />
          </div>
        </transition>
      </AppSurfacePanel>

      <!-- 4. Executed Calculations / Formula Trees (Collapsible) -->
      <AppSurfacePanel class="cfg-section-panel">
        <button
          type="button"
          class="cfg-section-header cfg-section-header--plain"
          :aria-expanded="openSections.formulas"
          aria-controls="cfg-section-formulas"
          @click="toggle('formulas')"
        >
          <div class="cfg-section-title-wrap">
            <i class="pi pi-bolt ui-color-warning" aria-hidden="true"></i>
            <span class="cfg-section-title">Executed Calculations</span>
            <span class="cfg-count-badge">{{ formulaTrees.length }}</span>
          </div>
          <i class="pi ui-action-icon-btn" :class="openSections.formulas ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
        </button>

        <transition name="cfg-expand">
          <div v-if="openSections.formulas" id="cfg-section-formulas" role="region">
            <ConfigExecutedCalculations :formulaTrees="formulaTrees" />
          </div>
        </transition>
      </AppSurfacePanel>

      <!-- 5. Chart Definitions (Collapsible) -->
      <AppSurfacePanel v-if="selectedConfig.charts.length" class="cfg-section-panel">
        <button
          type="button"
          class="cfg-section-header cfg-section-header--plain"
          :aria-expanded="openSections.charts"
          aria-controls="cfg-section-charts"
          @click="toggle('charts')"
        >
          <div class="cfg-section-title-wrap">
            <i class="pi pi-chart-line ui-color-info" aria-hidden="true"></i>
            <span class="cfg-section-title">Chart Definitions</span>
            <span class="cfg-count-badge">{{ selectedConfig.charts.length }}</span>
          </div>
          <i class="pi ui-action-icon-btn" :class="openSections.charts ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
        </button>

        <transition name="cfg-expand">
          <div v-if="openSections.charts" id="cfg-section-charts" role="region">
            <ConfigChartDefinitions :config="selectedConfig" />
          </div>
        </transition>
      </AppSurfacePanel>
      </div>
    </div>
  </AppStepSection>
</template>


