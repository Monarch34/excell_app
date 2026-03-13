import { describe, expect, it } from 'vitest';
import type { MatchingColumnGroup } from '@/shared/types/domain';
import {
  clampSeparatorIndices,
  normalizeHexColor,
  reorderColumnsWithLinkedGroups,
  resolveAvailableColumns,
  sanitizeMatchingGroups,
} from './columns.helpers';

describe('columns.helpers', () => {
  it('normalizes valid hex colors and rejects invalid values', () => {
    expect(normalizeHexColor('#aabbcc')).toBe('#AABBCC');
    expect(normalizeHexColor('A1b2c3')).toBe('#A1B2C3');
    expect(normalizeHexColor('#abc')).toBeNull();
    expect(normalizeHexColor('not-a-color')).toBeNull();
  });

  it('resolves available columns by priority', () => {
    expect(resolveAvailableColumns(['A'], ['B'], ['C'])).toEqual(['A']);
    expect(resolveAvailableColumns([], ['B'], ['C'])).toEqual(['B']);
    expect(resolveAvailableColumns(undefined, ['B'], ['C'])).toEqual(['B']);
    expect(resolveAvailableColumns(undefined, [], ['C'])).toEqual(['C']);
  });

  it('reorders linked group members together', () => {
    const order = ['A', 'B', 'C', 'D'];
    const linked = [['B', 'C']];
    const moved = reorderColumnsWithLinkedGroups(order, linked, 1, 0);
    expect(moved).toEqual(['B', 'C', 'A', 'D']);
  });

  it('clamps separators to valid positions', () => {
    expect(clampSeparatorIndices([-1, 0, 1, 4], 4)).toEqual([0, 1]);
    expect(clampSeparatorIndices([0, 1], 1)).toEqual([]);
  });

  it('sanitizes matching groups against allowed columns and duplicate assignments', () => {
    const groups: MatchingColumnGroup[] = [
      { id: 'g1', name: 'G1', color: '#11aa22', columns: ['A', 'B'] },
      { id: 'g2', name: 'G2', color: '#zzzzzz', columns: ['B', 'C'] },
    ];
    const sanitized = sanitizeMatchingGroups(groups, ['A', 'B', 'C']);

    expect(sanitized[0].columns).toEqual(['A', 'B']);
    // B is already assigned to first group, second keeps only C.
    expect(sanitized[1].columns).toEqual(['C']);
    // Invalid color falls back to default palette value.
    expect(sanitized[1].color).toMatch(/^#[0-9A-F]{6}$/);
  });
});
