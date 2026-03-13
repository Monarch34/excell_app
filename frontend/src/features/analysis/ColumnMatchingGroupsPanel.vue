<script setup lang="ts">
import { reactive, watch } from 'vue';
import MultiSelect from 'primevue/multiselect';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import AppField from '@/shared/components/ui/AppField.vue';
import type { MatchingColumnGroup } from '@/shared/types/domain';
import type { OrderableColumn } from '@/features/analysis/ColumnOrderPanel.vue';

const props = defineProps<{
  columns: OrderableColumn[];
  groups: MatchingColumnGroup[];
}>();

const emit = defineEmits<{
  createGroup: [];
  deleteGroup: [groupId: string];
  updateGroup: [groupId: string, patch: { name?: string; color?: string }];
  setGroupColumns: [groupId: string, columns: string[]];
}>();

function resolveHexToken(tokenName: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(tokenName).trim();
  return /^#[0-9a-fA-F]{6}$/.test(value) ? value : fallback;
}

const defaultGroupColor = resolveHexToken('--primary-400', '#60A5FA');
const draftNames = reactive<Record<string, string>>({});
const touchedNames = reactive<Record<string, boolean>>({});
const syncedNames = reactive<Record<string, string>>({});

function normalizeColor(value: string): string {
  if (/^#[0-9a-fA-F]{6}$/.test(value)) return value;
  const clean = value.replace(/^#/, '');
  if (/^[0-9a-fA-F]{6}$/.test(clean)) return `#${clean}`;
  return defaultGroupColor;
}

function optionsFor(groupId: string) {
  const assignedElsewhere = new Set(
    props.groups
      .filter((g) => g.id !== groupId)
      .flatMap((g) => g.columns)
  );

  return props.columns.map((column) => ({
    label: column.name,
    value: column.name,
    disabled: assignedElsewhere.has(column.name),
  }));
}

function handleColumnsUpdate(groupId: string, value: string[] | null | undefined) {
  emit('setGroupColumns', groupId, Array.isArray(value) ? value : []);
}

function columnCountLabel(count: number): string {
  return count === 1 ? '1 column' : `${count} columns`;
}

function syncGroupDrafts() {
  const activeIds = new Set(props.groups.map((group) => group.id));

  for (const group of props.groups) {
    const previousSynced = syncedNames[group.id];
    const currentDraft = draftNames[group.id];

    if (!(group.id in draftNames) || currentDraft === previousSynced) {
      draftNames[group.id] = group.name;
    }

    syncedNames[group.id] = group.name;
    touchedNames[group.id] = touchedNames[group.id] === true;
  }

  for (const id of Object.keys(draftNames)) {
    if (!activeIds.has(id)) {
      delete draftNames[id];
      delete touchedNames[id];
      delete syncedNames[id];
    }
  }
}

watch(
  () => props.groups.map((group) => ({ id: group.id, name: group.name })),
  syncGroupDrafts,
  { immediate: true }
);

function markNameTouched(groupId: string): void {
  touchedNames[groupId] = true;
}

function getDraftName(group: MatchingColumnGroup): string {
  return draftNames[group.id] ?? group.name;
}

function getNameError(group: MatchingColumnGroup): string | undefined {
  if (!touchedNames[group.id]) return undefined;
  if (!getDraftName(group).trim()) return 'Group name is required';
  return undefined;
}

function handleNameChange(group: MatchingColumnGroup, value: string | undefined): void {
  markNameTouched(group.id);
  const nextValue = value ?? '';
  draftNames[group.id] = nextValue;

  if (!nextValue.trim()) return;
  emit('updateGroup', group.id, { name: nextValue });
}

function handleNameBlur(group: MatchingColumnGroup): void {
  markNameTouched(group.id);

  const nextValue = getDraftName(group);
  if (!nextValue.trim()) return;
  emit('updateGroup', group.id, { name: nextValue });
}
</script>

<template>
  <div class="ui-baseline-dialog-panel ui-baseline-dialog-stack ui-match-groups">
    <div class="chart-dialog-subtitle">Column Groups</div>
    <p class="text-sm text-color-secondary ui-baseline-dialog-note">
      Create column groups and assign a color. Export uses the group color for unit and data cells.
    </p>
    <div class="chart-dialog-field ui-match-groups-head">
      <Button
        label="Add Group"
        icon="pi pi-plus"
        severity="secondary"
        outlined
        size="small"
        @click="emit('createGroup')"
      />
    </div>

    <div v-if="groups.length === 0" class="chart-dialog-field ui-match-groups-empty-state">
      <i class="pi pi-palette ui-match-groups-empty-icon" aria-hidden="true"></i>
      <p class="ui-match-groups-empty-text">
        No column groups yet. Create groups to color-code your exports.
      </p>
      <Button
        label="Create First Group"
        icon="pi pi-plus"
        severity="primary"
        size="small"
        @click="emit('createGroup')"
      />
    </div>

    <div v-else class="ui-match-groups-list">
      <div
        v-for="(group, index) in groups"
        :key="group.id"
        class="chart-dialog-field ui-match-group-card"
        :style="{ '--group-accent': normalizeColor(group.color) }"
      >
        <!-- Header row: Color | Group name title | Column count | Delete (all aligned) -->
        <div class="ui-match-group-header-row">
          <div class="ui-match-group-color-cell">
            <input
              :id="`match-group-color-${group.id}`"
              type="color"
              class="ui-match-group-color-swatch"
              :value="normalizeColor(group.color)"
              :aria-label="`Color for ${group.name}`"
              @input="emit('updateGroup', group.id, { color: ($event.target as HTMLInputElement).value })"
            />
          </div>
          <span class="ui-match-group-title">{{ getDraftName(group).trim() || `Group ${index + 1}` }}</span>
          <Tag
            :value="columnCountLabel(group.columns.length)"
            :severity="group.columns.length > 0 ? 'info' : 'secondary'"
            class="ui-match-group-count-badge"
          />
          <Button
            icon="pi pi-trash"
            severity="danger"
            text
            rounded
            size="small"
            :aria-label="`Delete ${group.name}`"
            @click="emit('deleteGroup', group.id)"
          />
        </div>

        <!-- Vertical inputs -->
        <div class="ui-match-group-fields">
          <AppField
            label="Group Name"
            :uppercase="false"
            :htmlFor="`match-group-name-${group.id}`"
            :required="true"
            :error="getNameError(group)"
            class="ui-match-group-name-field"
          >
            <InputText
              :id="`match-group-name-${group.id}`"
              :modelValue="getDraftName(group)"
              class="w-full ui-match-group-name-input"
              :class="{ 'p-invalid': !!getNameError(group) }"
              :placeholder="`Group ${index + 1}`"
              @update:modelValue="(v) => handleNameChange(group, String(v || ''))"
              @blur="handleNameBlur(group)"
            />
          </AppField>
          <div class="ui-match-group-columns-row">
          <MultiSelect
            :id="`match-group-columns-${group.id}`"
            :modelValue="group.columns"
            :options="optionsFor(group.id)"
            optionLabel="label"
            optionValue="value"
            optionDisabled="disabled"
            display="chip"
            filter
            :showToggleAll="false"
            class="w-full"
            :maxSelectedLabels="5"
            :placeholder="`Select columns for ${group.name || 'Group ' + (index + 1)}`"
            @update:modelValue="(v) => handleColumnsUpdate(group.id, v as string[])"
          />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
