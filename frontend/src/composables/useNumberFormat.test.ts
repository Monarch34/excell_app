import { describe, expect, it } from 'vitest';
import { useNumberFormat } from '@/composables/useNumberFormat';

describe('useNumberFormat', () => {
  it('formats numeric values in fixed mode without rounding', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue(12.3456789)).toBe('12.3456789');
    expect(formatValue(-2)).toBe('-2');
  });

  it('formats decimal numeric strings but does not coerce non-decimal strings', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue('3.5')).toBe('3.5');
    expect(formatValue('1e3')).toBe('1e3');
    expect(formatValue('0x10')).toBe('0x10');
    expect(formatValue('12-34')).toBe('12-34');
  });

  it('returns N/A for nullish and non-finite values', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue(null)).toBe('N/A');
    expect(formatValue(undefined)).toBe('N/A');
    expect(formatValue(Number.NaN)).toBe('N/A');
    expect(formatValue(Number.POSITIVE_INFINITY)).toBe('N/A');
  });

  it('does not mutate source values when toggling format modes', () => {
    const { mode, formatValue } = useNumberFormat('fixed');
    const row = { value: 0.12345678901234566 };
    const original = row.value;

    expect(formatValue(row.value)).toBe(String(original));
    mode.value = 'scientific';
    formatValue(row.value);
    mode.value = 'compact';
    formatValue(row.value);
    mode.value = 'fixed';
    expect(formatValue(row.value)).toBe(String(original));
    expect(row.value).toBe(original);
  });

  it('keeps compact mode non-rounding and preserves literal strings', () => {
    const { formatValue } = useNumberFormat('compact');
    expect(formatValue(0.12345678901234566)).toBe('0.12345678901234566');
    expect(formatValue('0.123456789012345600')).toBe('0.123456789012345600');
  });

  it('stabilizes binary-artifact tails for display in fixed mode', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue(0.0012500000000000002)).toBe('0.00125');
    expect(formatValue(0.001398210290827741)).toBe('0.001398210290827741');
  });

  it('formats values in scientific (exponential) mode', () => {
    const { formatValue } = useNumberFormat('scientific');
    expect(formatValue(12345)).toBe('1.2345E+4');
    expect(formatValue(-0.005)).toBe('-5E-3');
    expect(formatValue(1)).toBe('1E+0');
  });

  it('parses numeric strings in scientific mode', () => {
    const { formatValue } = useNumberFormat('scientific');
    expect(formatValue('42.5')).toBe('4.25E+1');
    expect(formatValue('not-a-number')).toBe('not-a-number');
  });

  it('returns zero as "0" in all modes', () => {
    for (const m of ['fixed', 'compact', 'scientific'] as const) {
      const { formatValue } = useNumberFormat(m);
      expect(formatValue(0)).toBe('0');
    }
  });

  it('returns N/A for empty string', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue('')).toBe('N/A');
  });

  it('formats booleans as true/false strings', () => {
    const { formatValue } = useNumberFormat('fixed');
    expect(formatValue(true as unknown as number)).toBe('true');
    expect(formatValue(false as unknown as number)).toBe('false');
  });
});
