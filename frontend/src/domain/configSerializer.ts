/**
 * Config serialization, deserialization, and validation.
 */

import type { AnalysisConfig, ValidationResult, ValidationError } from '@/shared/types/domain';
import { CONFIG_VERSION } from '@/constants/config';

const CURRENT_VERSION = CONFIG_VERSION;

/**
 * Serialize an AnalysisConfig to a JSON string.
 */
export function toJSON(config: AnalysisConfig): string {
  return JSON.stringify(config, null, 2);
}

/**
 * Deserialize a JSON string to an AnalysisConfig.
 * Throws on invalid JSON or missing required fields.
 */
export function fromJSON(json: string): AnalysisConfig {
  let parsed: unknown;
  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error('Invalid JSON format');
  }

  if (typeof parsed !== 'object' || parsed === null) {
    throw new Error('Config must be a JSON object');
  }

  const obj = parsed as Record<string, unknown>;

  // Validate required fields
  if (!obj.version || typeof obj.version !== 'string') {
    throw new Error('Missing or invalid "version" field');
  }

  if (!obj.name || typeof obj.name !== 'string') {
    throw new Error('Missing or invalid "name" field');
  }

  // Validate array fields before casting
  const arrayFields = ['selectedColumns', 'parameters', 'derivedColumns', 'charts', 'columnOrder', 'parameterOrder', 'separators', 'matchingGroups'] as const;
  for (const field of arrayFields) {
    if (obj[field] !== undefined && !Array.isArray(obj[field])) {
      throw new Error(`"${field}" must be an array`);
    }
  }

  // Basic shape validation for chart elements
  if (Array.isArray(obj.charts)) {
    for (const [i, chart] of (obj.charts as unknown[]).entries()) {
      if (!chart || typeof chart !== 'object') {
        throw new Error(`charts[${i}] must be an object`);
      }
      const c = chart as Record<string, unknown>;
      if (c.id !== undefined && typeof c.id !== 'string') {
        throw new Error(`charts[${i}].id must be a string`);
      }
    }
  }

  const config = normalizeConfig(obj as unknown as AnalysisConfig);

  return config;
}

/**
 * Normalize config shape to current defaults.
 */
function normalizeConfig(config: AnalysisConfig): AnalysisConfig {
  if (config.version !== CURRENT_VERSION) {
    console.warn(`Config version ${config.version} differs from current ${CURRENT_VERSION}`);
  }

  return {
    version: CURRENT_VERSION,
    name: config.name || 'Untitled',
    description: config.description || '',
    selectedColumns: config.selectedColumns || [],
    parameters: config.parameters || [],
    derivedColumns: config.derivedColumns || [],
    charts: config.charts || [],
    columnOrder: config.columnOrder || [],
    parameterOrder: config.parameterOrder || [],
    separators: config.separators || [],
    separatorColor: config.separatorColor || '#2F855A',
    columnMetadata: config.columnMetadata || undefined,
    matchingGroups: config.matchingGroups || [],
    createdAt: config.createdAt || new Date().toISOString(),
    updatedAt: config.updatedAt || new Date().toISOString(),
  };
}

/**
 * Validate a config against the current dataset.
 * Returns missing columns, broken formulas, etc.
 */
export function validateConfig(
  config: AnalysisConfig,
  availableColumns: string[],
  availableParameters: string[] = []
): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  // Check selected columns
  for (const col of config.selectedColumns) {
    if (!availableColumns.includes(col)) {
      warnings.push({
        code: 'MISSING_COLUMN',
        message: `Selected column "${col}" not found in dataset`,
        field: 'selectedColumns',
        suggestions: findSimilar(col, availableColumns),
      });
    }
  }

  // Check matching-group references (a column can belong to one group at most)
  const seenGroupedColumns = new Set<string>();
  const groupAvailableColumns = new Set([
    ...availableColumns,
    ...config.derivedColumns.map((d) => d.name),
  ]);
  for (const group of config.matchingGroups || []) {
    for (const col of group.columns || []) {
      if (!groupAvailableColumns.has(col)) {
        warnings.push({
          code: 'MISSING_GROUP_COLUMN',
          message: `Matching group "${group.name}" references missing column "${col}"`,
          field: 'matchingGroups',
        });
        continue;
      }

      if (seenGroupedColumns.has(col)) {
        warnings.push({
          code: 'DUPLICATE_GROUP_COLUMN',
          message: `Column "${col}" appears in more than one matching group`,
          field: 'matchingGroups',
        });
        continue;
      }
      seenGroupedColumns.add(col);
    }
  }

  // Check derived column references
  for (const dc of config.derivedColumns) {
    const refs = dc.formula.match(/\[([^\]]+)\]/g) || [];
    for (const ref of refs) {
      const name = ref.slice(1, -1);
      const allAvailable = [
        ...availableColumns,
        ...availableParameters,
        ...config.derivedColumns.map((d) => d.name),
        ...config.parameters.map((p) => p.name),
      ];
      if (!allAvailable.includes(name)) {
        errors.push({
          code: 'BROKEN_REFERENCE',
          message: `Derived column "${dc.name}" references missing "${name}"`,
          field: `derivedColumns.${dc.id}`,
        });
      }
    }
  }

  // Check for cycles in derived column formula references
  {
    const graph = new Map<string, string[]>();
    for (const dc of config.derivedColumns) {
      const refs = dc.formula.match(/\[([^\]]+)\]/g) || [];
      const depNames = refs
        .map((r) => r.slice(1, -1))
        .filter((name) => config.derivedColumns.some((d) => d.name === name));
      graph.set(dc.name, depNames);
    }

    const color = new Map<string, 'white' | 'gray' | 'black'>();

    function hasCycle(node: string): boolean {
      const state = color.get(node) ?? 'white';
      if (state === 'gray') return true;
      if (state === 'black') return false;
      color.set(node, 'gray');
      for (const dep of graph.get(node) || []) {
        if (hasCycle(dep)) return true;
      }
      color.set(node, 'black');
      return false;
    }

    for (const dc of config.derivedColumns) {
      if (hasCycle(dc.name)) {
        errors.push({
          code: 'CYCLE_DETECTED',
          message: `Derived column "${dc.name}" is involved in a circular reference`,
          field: `derivedColumns.${dc.id}`,
        });
        break;
      }
    }
  }

  // Check chart column references
  for (const chart of config.charts) {
    const allAvailable = [
      ...availableColumns,
      ...config.derivedColumns.map((d) => d.name),
    ];

    if (chart.xColumn && !allAvailable.includes(chart.xColumn)) {
      warnings.push({
        code: 'MISSING_CHART_COLUMN',
        message: `Chart "${chart.title}" X column "${chart.xColumn}" not found`,
        field: `charts.${chart.id}`,
      });
    }

    for (const yCol of chart.yColumns) {
      if (!allAvailable.includes(yCol)) {
        warnings.push({
          code: 'MISSING_CHART_COLUMN',
          message: `Chart "${chart.title}" Y column "${yCol}" not found`,
          field: `charts.${chart.id}`,
        });
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Find similar column names (basic Levenshtein-like matching).
 */
function findSimilar(name: string, candidates: string[]): string[] {
  const lower = name.toLowerCase();
  return candidates
    .filter((c) => {
      const cl = c.toLowerCase();
      return cl.includes(lower) || lower.includes(cl) || levenshteinDistance(lower, cl) <= 3;
    })
    .slice(0, 3);
}

function levenshteinDistance(a: string, b: string): number {
  const matrix: number[][] = [];
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      const cost = b[i - 1] === a[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  return matrix[b.length][a.length];
}

/**
 * Trigger download of config as JSON file.
 */
export function downloadConfig(config: AnalysisConfig): void {
  const json = toJSON(config);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${config.name.replace(/[^a-zA-Z0-9_-]/g, '_')}_config.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 100);
}
