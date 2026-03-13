<script setup lang="ts">
import { computed, ref, watch, type CSSProperties } from 'vue';
import draggable from 'vuedraggable';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import AppDialogSurface from '@/shared/components/ui/AppDialogSurface.vue';
import DerivedColumnsPreviewTable from '@/features/analysis/DerivedColumnsPreviewTable.vue';
import ColumnMatchingGroupsPanel from '@/features/analysis/ColumnMatchingGroupsPanel.vue';
import AppStepSection from '@/shared/components/ui/AppStepSection.vue';
import { useNumberFormat } from '@/composables/useNumberFormat';
import type { ProcessResultValue } from '@/shared/types/api';
import type { OrderableColumn } from '@/features/analysis/ColumnOrderPanel.vue';
import type { MatchingColumnGroup } from '@/shared/types/domain';

type ParameterRow = {
  id: string;
  name: string;
  value: ProcessResultValue | undefined;
  unit: string;
};

const props = defineProps<{
  parameterRows: ParameterRow[];
  columns: OrderableColumn[];
  separators: number[];
  separatorColor: string;
  matchingGroups: MatchingColumnGroup[];
  previewRows: Record<string, ProcessResultValue>[];
}>();

const emit = defineEmits<{
  reorderParameters: [fromIndex: number, toIndex: number];
  reorder: [fromIndex: number, toIndex: number];
  toggleSeparator: [index: number];
  updateSeparatorColor: [color: string];
  createMatchingGroup: [];
  deleteMatchingGroup: [groupId: string];
  updateMatchingGroup: [groupId: string, patch: { name?: string; color?: string }];
  setMatchingGroupColumns: [groupId: string, columns: string[]];
}>();

const isExpanded = ref(true);
const activeTab = ref<'parameters' | 'columns'>('parameters');
const groupsDialogVisible = ref(false);
const draggableParameters = ref<ParameterRow[]>([]);
const { mode: valueMode, formatValue } = useNumberFormat('fixed');

watch(
  () => props.parameterRows,
  (rows) => {
    draggableParameters.value = [...rows];
  },
  { deep: true, immediate: true },
);

const parameterCount = computed(() => draggableParameters.value.length);
const groupCount = computed(() => props.matchingGroups.length);
const separatorCount = computed(() => props.separators.length);
const dialogStyle: CSSProperties = { width: 'min(92vw, 44rem)' };
const dialogContentStyle: CSSProperties = { maxHeight: 'min(72vh, 42rem)', overflowY: 'auto' };
const dialogBreakpoints = { '960px': '90vw', '640px': '96vw' };

function onParameterDragEnd(event: { oldIndex?: number; newIndex?: number }) {
  if (event.oldIndex === undefined || event.newIndex === undefined) return;
  emit('reorderParameters', event.oldIndex, event.newIndex);
}
</script>

<template>
  <AppStepSection icon="pi-list" title="Analysis Summary">
    <template #action>
      <Button
        :icon="isExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
        severity="secondary"
        outlined
        size="small"
        class="ui-analysis-order-toggle"
        :aria-label="isExpanded ? 'Collapse analysis summary' : 'Expand analysis summary'"
        @click="isExpanded = !isExpanded"
      />
    </template>

    <div v-if="isExpanded" class="ui-analysis-order-body">
      <div class="ui-analysis-tabs">
        <button
          type="button"
          class="ui-analysis-tab-btn"
          :class="{ 'is-active': activeTab === 'parameters' }"
          @click="activeTab = 'parameters'"
        >
          Derived Parameters
          <Tag :value="String(parameterCount)" severity="info" />
        </button>
        <button
          type="button"
          class="ui-analysis-tab-btn"
          :class="{ 'is-active': activeTab === 'columns' }"
          @click="activeTab = 'columns'"
        >
          Derived Columns
          <Tag :value="String(columns.length)" severity="success" />
        </button>
      </div>

      <!-- ═══════════ Parameters Tab ═══════════ -->
      <section v-if="activeTab === 'parameters'" class="ui-analysis-order-subpanel">
        <div class="ui-analysis-order-head">
          <p class="text-sm ui-step-intro ui-analysis-order-help ui-analysis-order-intro">
            Drag rows to set the display order for derived parameter outputs.
          </p>
          <div class="ui-analysis-value-mode">
            <Button
              size="small"
              severity="secondary"
              :outlined="valueMode !== 'compact'"
              label="Compact"
              @click="valueMode = 'compact'"
            />
            <Button
              size="small"
              severity="secondary"
              :outlined="valueMode !== 'fixed'"
              label="Fixed"
              @click="valueMode = 'fixed'"
            />
            <Button
              size="small"
              severity="secondary"
              :outlined="valueMode !== 'scientific'"
              label="Scientific"
              @click="valueMode = 'scientific'"
            />
          </div>
        </div>

        <div v-if="draggableParameters.length === 0" class="ui-select-empty">
          No derived parameters available yet.
        </div>
        <div v-else class="ui-analysis-parameter-list">
          <draggable
            class="ui-analysis-parameter-draggable"
            :list="draggableParameters"
            item-key="id"
            handle=".ui-analysis-parameter-drag"
            :animation="180"
            ghost-class="ui-drag-ghost"
            chosen-class="ui-drag-chosen"
            @end="onParameterDragEnd"
          >
            <template #item="{ element }">
              <div class="ui-analysis-parameter-row">
                <i class="pi pi-bars ui-analysis-parameter-drag" aria-hidden="true"></i>
                <span class="ui-analysis-parameter-name">{{ element.name }}</span>
                <span class="ui-analysis-parameter-value">{{ formatValue(element.value) }}</span>
                <span class="ui-analysis-parameter-unit">{{ element.unit || '-' }}</span>
              </div>
            </template>
          </draggable>
        </div>
      </section>

      <!-- ═══════════ Columns Tab ═══════════ -->
      <section v-else class="ui-analysis-order-subpanel">
        <!-- Compact Toolbar -->
        <div class="ui-analysis-columns-toolbar">
          <Button
            label="Column Groups"
            :badge="groupCount > 0 ? String(groupCount) : undefined"
            icon="pi pi-palette"
            severity="secondary"
            outlined
            size="small"
            @click="groupsDialogVisible = true"
          />

          <div class="ui-analysis-toolbar-separator-color">
            <label class="ui-order-head-label" for="analysis-separator-color">
              <i class="pi pi-minus"></i> Separator
            </label>
            <input
              id="analysis-separator-color"
              type="color"
              class="ui-match-group-color-input ui-analysis-separator-color-input"
              :value="separatorColor"
              @input="emit('updateSeparatorColor', ($event.target as HTMLInputElement).value)"
            />
          </div>

          <span v-if="separatorCount > 0" class="ui-analysis-toolbar-hint">
            {{ separatorCount }} separator{{ separatorCount !== 1 ? 's' : '' }} active
          </span>
        </div>

        <!-- Data Preview Table -->
        <DerivedColumnsPreviewTable
          :columns="columns"
          :previewRows="previewRows"
          :separators="separators"
          :separatorColor="separatorColor"
          :matchingGroups="matchingGroups"
          :numberFormatMode="valueMode"
          @reorder="(fromIndex, toIndex) => emit('reorder', fromIndex, toIndex)"
          @toggleSeparator="(index) => emit('toggleSeparator', index)"
        />
      </section>
    </div>
  </AppStepSection>

  <!-- ═══════════ Column Groups Dialog ═══════════ -->
  <AppDialogSurface
    v-model:visible="groupsDialogVisible"
    header="Column Groups"
    modal
    :style="dialogStyle"
    :contentStyle="dialogContentStyle"
    :breakpoints="dialogBreakpoints"
  >
    <ColumnMatchingGroupsPanel
      :columns="columns"
      :groups="matchingGroups"
      @createGroup="emit('createMatchingGroup')"
      @deleteGroup="(groupId) => emit('deleteMatchingGroup', groupId)"
      @updateGroup="(groupId, patch) => emit('updateMatchingGroup', groupId, patch)"
      @setGroupColumns="(groupId, cols) => emit('setMatchingGroupColumns', groupId, cols)"
    />
  </AppDialogSurface>
</template>


