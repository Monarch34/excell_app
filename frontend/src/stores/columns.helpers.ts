import type { MatchingColumnGroup } from '@/types/domain';

export const DEFAULT_MATCHING_COLORS = [
  '#60A5FA',
  '#34D399',
  '#F59E0B',
  '#A78BFA',
  '#F87171',
  '#22D3EE',
];

export function normalizeHexColor(value: string | null | undefined): string | null {
  if (!value) return null;
  const cleaned = String(value).trim().replace(/^#/, '');
  if (!/^[0-9a-fA-F]{6}$/.test(cleaned)) return null;
  return `#${cleaned.toUpperCase()}`;
}

export function createGroupId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `mg_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

export function resolveAvailableColumns(
  allowedColumns: string[] | undefined,
  columnOrder: string[],
  selectedColumnNames: string[]
): string[] {
  if (allowedColumns && allowedColumns.length > 0) return allowedColumns;
  if (columnOrder.length > 0) return columnOrder;
  return selectedColumnNames;
}

export function reorderColumnsWithLinkedGroups(
  order: string[],
  linkedGroups: string[][],
  fromIndex: number,
  toIndex: number
): string[] {
  if (
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= order.length ||
    toIndex >= order.length ||
    fromIndex === toIndex
  ) {
    return order;
  }

  const nextOrder = [...order];
  const draggedName = nextOrder[fromIndex];
  const group = linkedGroups.find((g) => g.includes(draggedName));

  if (group && group.length > 1) {
    const groupIndices = group
      .map((name) => nextOrder.indexOf(name))
      .filter((index) => index >= 0)
      .sort((a, b) => a - b);

    const groupNames = groupIndices.map((index) => nextOrder[index]);
    const filtered = nextOrder.filter((_, index) => !groupIndices.includes(index));

    let insertAt = toIndex;
    for (const groupIndex of groupIndices) {
      if (groupIndex < toIndex) insertAt -= 1;
    }
    insertAt = Math.max(0, Math.min(insertAt, filtered.length));
    filtered.splice(insertAt, 0, ...groupNames);
    return filtered;
  }

  const [item] = nextOrder.splice(fromIndex, 1);
  nextOrder.splice(toIndex, 0, item);
  return nextOrder;
}

export function clampSeparatorIndices(separators: number[], columnOrderLength: number): number[] {
  const maxIdx = columnOrderLength - 2;
  return separators.filter((index) => index >= 0 && index <= maxIdx);
}

export function sanitizeMatchingGroups(
  groups: MatchingColumnGroup[],
  availableColumns: string[]
): MatchingColumnGroup[] {
  const available = new Set(availableColumns);
  const assigned = new Set<string>();
  const next: MatchingColumnGroup[] = [];

  for (let idx = 0; idx < groups.length; idx += 1) {
    const group = groups[idx];
    const color = normalizeHexColor(group.color) || DEFAULT_MATCHING_COLORS[idx % DEFAULT_MATCHING_COLORS.length];
    const name = (group.name || `Group ${idx + 1}`).trim();
    const columns: string[] = [];

    for (const columnName of group.columns || []) {
      if (!available.has(columnName) || assigned.has(columnName)) continue;
      assigned.add(columnName);
      columns.push(columnName);
    }

    next.push({
      id: group.id || createGroupId(),
      name: name || `Group ${idx + 1}`,
      color,
      columns,
    });
  }

  return next;
}
