import { ref } from 'vue';
import type { ProcessResultValue } from '@/shared/types/api';

export type NumberFormatMode = 'compact' | 'fixed' | 'scientific';

const DECIMAL_NUMBER_PATTERN = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
const ARTIFACT_TAIL_PATTERN = /(0{6,}[1-9]|9{6,})$/;

/**
 * Shared number formatting composable.
 * Provides three modes:
 *   - compact: non-scientific plain representation (no rounding).
 *   - fixed: raw float string without rounding.
 *   - scientific: exponential notation.
 */
export function useNumberFormat(defaultMode: NumberFormatMode = 'scientific') {
  const mode = ref<NumberFormatMode>(defaultMode);

  function toleranceFor(num: number): number {
    return Math.max(Number.EPSILON * Math.max(1, Math.abs(num)) * 32, 1e-20);
  }

  function normalizeDecimalString(value: string): string {
    if (!value.includes('.')) return value;
    const normalized = value.replace(/\.?0+$/, '');
    return normalized === '-0' || normalized === '' ? '0' : normalized;
  }

  function stabilizeArtifactNumber(num: number): number {
    const raw = String(num);
    if (!raw.includes('.') || raw.includes('e') || raw.includes('E')) return num;

    const fraction = raw.split('.')[1] ?? '';
    if (!ARTIFACT_TAIL_PATTERN.test(fraction)) return num;

    const zeroRunStart = fraction.search(/0{6,}[1-9]$/);
    const nineRunStart = fraction.search(/9{6,}$/);
    const runStart = zeroRunStart >= 0 ? zeroRunStart : nineRunStart;
    if (runStart < 0) return num;

    const candidate = Number(num.toFixed(runStart));
    if (!Number.isFinite(candidate)) return num;

    const delta = Math.abs(num - candidate);
    return delta <= toleranceFor(num) ? candidate : num;
  }

  function parseNumericString(value: string): number | null {
    const trimmed = value.trim();
    if (!trimmed || !DECIMAL_NUMBER_PATTERN.test(trimmed)) return null;
    const numeric = Number(trimmed);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function formatNumber(num: number): string {
    if (num === 0) return '0';
    const stabilized = stabilizeArtifactNumber(num);
    const stabilizedText = normalizeDecimalString(String(stabilized));
    switch (mode.value) {
      case 'scientific':
        return stabilized.toExponential().toUpperCase();
      case 'fixed':
      case 'compact':
        return stabilizedText;
      default:
        return stabilizedText;
    }
  }

  function formatValue(value: ProcessResultValue | undefined): string {
    if (value === null || value === undefined || value === '') return 'N/A';

    if (typeof value === 'number') {
      if (!Number.isFinite(value)) return 'N/A';
      return formatNumber(value);
    }

    if (typeof value === 'string') {
      if (mode.value === 'fixed' || mode.value === 'compact') {
        return value;
      }
      const numeric = parseNumericString(value);
      if (numeric !== null) {
        return formatNumber(numeric);
      }
    }

    if (typeof value === 'boolean') return value ? 'true' : 'false';
    return String(value);
  }

  return {
    mode,
    formatNumber,
    formatValue,
  };
}
