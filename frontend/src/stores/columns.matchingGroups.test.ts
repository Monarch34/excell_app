import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useColumnsStore } from '@/stores/columns';
import type { MatchingColumnGroup } from '@/shared/types/domain';

describe('columns matching groups', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('enforces one-group-per-column when assigning columns', () => {
    const store = useColumnsStore();
    store.initializeOrder(['Time', 'Load', 'Stress']);

    const g1 = store.createMatchingGroup({ name: 'Group A', color: '#FF0000' });
    const g2 = store.createMatchingGroup({ name: 'Group B', color: '#00FF00' });

    store.setMatchingGroupColumns(g1, ['Time', 'Load']);
    store.setMatchingGroupColumns(g2, ['Load', 'Stress']);

    const groupA = store.matchingGroups.find((g) => g.id === g1);
    const groupB = store.matchingGroups.find((g) => g.id === g2);

    expect(groupA?.columns).toEqual(['Time']);
    expect(groupB?.columns).toEqual(['Load', 'Stress']);
  });

  it('sanitizes missing and duplicate columns when loading matching groups', () => {
    const store = useColumnsStore();
    store.initializeOrder(['Time', 'Load']);

    const incoming: MatchingColumnGroup[] = [
      { id: 'g1', name: 'A', color: '#ABCDEF', columns: ['Time', 'Missing'] },
      { id: 'g2', name: 'B', color: '#123456', columns: ['Time', 'Load'] },
    ];

    store.setMatchingGroups(incoming, ['Time', 'Load']);

    expect(store.matchingGroups).toHaveLength(2);
    expect(store.matchingGroups[0].columns).toEqual(['Time']);
    expect(store.matchingGroups[1].columns).toEqual(['Load']);
  });

  it('syncs order, separators, and matching groups against available columns', () => {
    const store = useColumnsStore();
    store.initializeOrder(['A', 'B', 'C']);
    store.separators = [0, 1, 4];

    const incoming: MatchingColumnGroup[] = [
      { id: 'g1', name: 'Group 1', color: '#ABCDEF', columns: ['A', 'C'] },
      { id: 'g2', name: 'Group 2', color: '#123456', columns: ['C', 'D'] },
    ];
    store.setMatchingGroups(incoming, ['A', 'B', 'C', 'D']);

    store.syncOrderLayout(['B', 'D', 'A']);

    expect(store.columnOrder).toEqual(['A', 'B', 'D']);
    expect(store.separators).toEqual([0, 1]);
    expect(store.matchingGroups.find((group) => group.id === 'g1')?.columns).toEqual(['A']);
    expect(store.matchingGroups.find((group) => group.id === 'g2')?.columns).toEqual(['D']);
  });
});
