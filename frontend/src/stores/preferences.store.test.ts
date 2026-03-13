import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { usePreferencesStore } from '@/stores/preferences';

describe('preferences store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('toggles dark mode', () => {
    const store = usePreferencesStore();
    expect(store.isDarkMode).toBe(true);
    store.toggleDarkMode();
    expect(store.isDarkMode).toBe(false);
  });

  it('sets dark mode explicitly', () => {
    const store = usePreferencesStore();
    store.setDarkMode(false);
    expect(store.isDarkMode).toBe(false);
  });
});
