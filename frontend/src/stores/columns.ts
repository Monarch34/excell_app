import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { ColumnDef, MatchingColumnGroup } from '@/types/domain';
import {
  DEFAULT_MATCHING_COLORS,
  clampSeparatorIndices,
  createGroupId,
  normalizeHexColor,
  reorderColumnsWithLinkedGroups,
  resolveAvailableColumns,
  sanitizeMatchingGroups,
} from './columns.helpers';

/**
 * Columns store - manages column selection, ordering, linking, and separators.
 */
export const useColumnsStore = defineStore('columns', () => {
  const selectedColumnNames = ref<string[]>([]);
  const columnOrder = ref<string[]>([]);
  const parameterOrder = ref<string[]>([]);
  const linkedGroups = ref<string[][]>([]);
  const matchingGroups = ref<MatchingColumnGroup[]>([]);
  const separators = ref<number[]>([]);
  const separatorColor = ref('#2F855A');
  const columnMapping = ref<Record<string, string>>({});

  const hasSelection = computed(() => selectedColumnNames.value.length > 0);
  const selectionCount = computed(() => selectedColumnNames.value.length);
  const orderedSelectedColumns = computed(() => {
    if (columnOrder.value.length === 0) return selectedColumnNames.value;
    return columnOrder.value.filter((name) => selectedColumnNames.value.includes(name));
  });

  function initializeFromDataset(columns: ColumnDef[]) {
    selectedColumnNames.value = columns.filter((col) => col.selected).map((col) => col.name);
  }

  function initializeOrder(names: string[]) {
    columnOrder.value = [...names];
  }

  function setParameterOrder(names: string[]) {
    const unique = Array.from(new Set(names.map((name) => name.trim()).filter(Boolean)));
    parameterOrder.value = unique;
  }

  function reorderParameters(fromIndex: number, toIndex: number) {
    if (
      fromIndex < 0
      || toIndex < 0
      || fromIndex >= parameterOrder.value.length
      || toIndex >= parameterOrder.value.length
    ) {
      return;
    }
    const next = [...parameterOrder.value];
    const [moved] = next.splice(fromIndex, 1);
    next.splice(toIndex, 0, moved);
    parameterOrder.value = next;
  }

  function syncOrderLayout(availableNames: string[]) {
    const uniqueAvailable = Array.from(new Set(availableNames));
    const currentOrder = columnOrder.value;
    const nextOrder = currentOrder.filter((name) => uniqueAvailable.includes(name));

    for (const name of uniqueAvailable) {
      if (!nextOrder.includes(name)) {
        nextOrder.push(name);
      }
    }

    const orderChanged =
      nextOrder.length !== currentOrder.length ||
      nextOrder.some((name, idx) => name !== currentOrder[idx]);

    if (orderChanged) {
      columnOrder.value = nextOrder;
    }

    separators.value = clampSeparatorIndices(separators.value, nextOrder.length);
    matchingGroups.value = sanitizeMatchingGroups(matchingGroups.value, uniqueAvailable);
  }

  function toggleColumn(name: string) {
    const idx = selectedColumnNames.value.indexOf(name);
    if (idx >= 0) {
      selectedColumnNames.value.splice(idx, 1);
    } else {
      selectedColumnNames.value.push(name);
    }
  }

  function selectAll(columnNames: string[]) {
    selectedColumnNames.value = [...columnNames];
  }

  function deselectAll() {
    selectedColumnNames.value = [];
  }

  function isSelected(name: string): boolean {
    return selectedColumnNames.value.includes(name);
  }

  function reorderColumns(fromIndex: number, toIndex: number) {
    columnOrder.value = reorderColumnsWithLinkedGroups(
      columnOrder.value,
      linkedGroups.value,
      fromIndex,
      toIndex
    );
    separators.value = clampSeparatorIndices(separators.value, columnOrder.value.length);
  }

  function linkColumns(names: string[]) {
    if (names.length < 2) return;
    linkedGroups.value = linkedGroups.value.filter((group) => !group.some((name) => names.includes(name)));
    linkedGroups.value.push([...names]);
  }

  function unlinkColumn(name: string) {
    linkedGroups.value = linkedGroups.value
      .map((group) => group.filter((value) => value !== name))
      .filter((group) => group.length >= 2);
  }

  function addSeparatorAfter(index: number) {
    if (!separators.value.includes(index)) {
      separators.value.push(index);
      separators.value.sort((a, b) => a - b);
    }
  }

  function removeSeparator(index: number) {
    separators.value = separators.value.filter((value) => value !== index);
  }

  function toggleSeparator(index: number) {
    if (separators.value.includes(index)) {
      removeSeparator(index);
    } else {
      addSeparatorAfter(index);
    }
  }

  function getLinkedGroup(name: string): string[] | undefined {
    return linkedGroups.value.find((group) => group.includes(name));
  }

  function getAvailableColumns(allowedColumns?: string[]): string[] {
    return resolveAvailableColumns(allowedColumns, columnOrder.value, selectedColumnNames.value);
  }

  function setSeparatorColor(color: string) {
    const normalized = normalizeHexColor(color);
    if (!normalized) return;
    separatorColor.value = normalized;
  }

  function createMatchingGroup(initial?: Partial<MatchingColumnGroup>): string {
    const groupIndex = matchingGroups.value.length;
    const newGroup: MatchingColumnGroup = {
      id: initial?.id || createGroupId(),
      name: (initial?.name || `Group ${groupIndex + 1}`).trim(),
      color:
        normalizeHexColor(initial?.color) ||
        DEFAULT_MATCHING_COLORS[groupIndex % DEFAULT_MATCHING_COLORS.length],
      columns: [],
    };
    matchingGroups.value.push(newGroup);
    return newGroup.id;
  }

  function updateMatchingGroup(
    id: string,
    patch: Partial<Pick<MatchingColumnGroup, 'name' | 'color'>>
  ) {
    const group = matchingGroups.value.find((value) => value.id === id);
    if (!group) return;

    if (typeof patch.name === 'string') {
      const trimmed = patch.name.trim();
      group.name = trimmed || group.name;
    }

    if (typeof patch.color === 'string') {
      const normalized = normalizeHexColor(patch.color);
      if (normalized) group.color = normalized;
    }
  }

  function setMatchingGroupColumns(id: string, names: string[], allowedColumns?: string[]) {
    const group = matchingGroups.value.find((value) => value.id === id);
    if (!group) return;

    const allowed = new Set(getAvailableColumns(allowedColumns));
    const nextColumns = Array.from(new Set(names.filter((name) => allowed.has(name))));

    for (const other of matchingGroups.value) {
      if (other.id === id) continue;
      other.columns = other.columns.filter((name) => !nextColumns.includes(name));
    }

    group.columns = nextColumns;
  }

  function deleteMatchingGroup(id: string) {
    matchingGroups.value = matchingGroups.value.filter((group) => group.id !== id);
  }

  function getMatchingGroupForColumn(columnName: string): MatchingColumnGroup | undefined {
    return matchingGroups.value.find((group) => group.columns.includes(columnName));
  }

  function setMatchingGroups(groups: MatchingColumnGroup[], allowedColumns?: string[]) {
    const available = getAvailableColumns(allowedColumns);
    matchingGroups.value = sanitizeMatchingGroups(groups, available);
  }

  function sanitizeExistingMatchingGroups(allowedColumns?: string[]) {
    setMatchingGroups(matchingGroups.value, allowedColumns);
  }

  function reset() {
    selectedColumnNames.value = [];
    columnOrder.value = [];
    parameterOrder.value = [];
    linkedGroups.value = [];
    matchingGroups.value = [];
    separators.value = [];
    separatorColor.value = '#2F855A';
    columnMapping.value = {};
  }

  function setColumnMapping(role: string, columnName: string) {
    columnMapping.value[role] = columnName;
  }

  function getColumnForRole(role: string): string | undefined {
    return columnMapping.value[role];
  }

  return {
    selectedColumnNames,
    columnOrder,
    parameterOrder,
    linkedGroups,
    matchingGroups,
    separators,
    separatorColor,
    hasSelection,
    selectionCount,
    orderedSelectedColumns,
    initializeFromDataset,
    initializeOrder,
    setParameterOrder,
    reorderParameters,
    syncOrderLayout,
    toggleColumn,
    selectAll,
    deselectAll,
    isSelected,
    reorderColumns,
    linkColumns,
    unlinkColumn,
    addSeparatorAfter,
    removeSeparator,
    toggleSeparator,
    getLinkedGroup,
    createMatchingGroup,
    updateMatchingGroup,
    setMatchingGroupColumns,
    deleteMatchingGroup,
    getMatchingGroupForColumn,
    setMatchingGroups,
    sanitizeMatchingGroups: sanitizeExistingMatchingGroups,
    setSeparatorColor,
    reset,
    columnMapping,
    setColumnMapping,
    getColumnForRole,
  };
});
