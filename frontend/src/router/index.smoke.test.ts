import { describe, expect, it } from 'vitest';
import router from './index';

describe('router smoke', () => {
  it('contains expected top-level routes', () => {
    const names = router.getRoutes().map((r) => r.name);
    expect(names).toContain('dashboard');
    expect(names).toContain('analysis');
    expect(names).toContain('config');
    expect(names).toContain('settings');
  });

  it('uses lazy-loaded route components for main pages', () => {
    const dashboard = router.getRoutes().find((r) => r.name === 'dashboard');
    const analysis = router.getRoutes().find((r) => r.name === 'analysis');
    const config = router.getRoutes().find((r) => r.name === 'config');
    const settings = router.getRoutes().find((r) => r.name === 'settings');

    expect(typeof dashboard?.components?.default).toBe('function');
    expect(typeof analysis?.components?.default).toBe('function');
    expect(typeof config?.components?.default).toBe('function');
    expect(typeof settings?.components?.default).toBe('function');
  });

  it('contains nested analysis step routes', () => {
    const names = router.getRoutes().map((r) => r.name);
    expect(names).toContain('analysis-import');
    expect(names).toContain('analysis-columns-params');
    expect(names).toContain('analysis-calculations');
    expect(names).toContain('analysis-charts-area');
    expect(names).toContain('analysis-review');
    expect(names).toContain('analysis-export');
  });
});

