import type { AnalysisConfig, DerivedColumnDef } from '@/shared/types/domain';

export type DependencyKind =
  | 'column'
  | 'parameter'
  | 'derived-column'
  | 'derived-parameter'
  | 'unknown';

export interface DependencyReference {
  name: string;
  kind: DependencyKind;
}

export interface DerivedDependencyItem {
  id: string;
  name: string;
  type: 'column' | 'parameter';
  formula: string;
  dependencies: DependencyReference[];
  usedByCharts: string[];
}

export interface ChartDependencyItem {
  id: string;
  title: string;
  chartType: string;
  xDependency: DependencyReference | null;
  yDependencies: DependencyReference[];
}

export interface FormulaTreeNode {
  key: string;
  type: 'formula' | 'input' | 'cycle';
  label: string;
  data?: {
    formula?: string;
    dataType?: string;
    details?: string;
    icon?: string;
  };
  children?: FormulaTreeNode[];
}

export interface FormulaTreeEntry {
  formula: DerivedDependencyItem;
  derived: DerivedColumnDef | null;
  treeData: FormulaTreeNode;
}

export interface ConfigDependencyModel {
  inputColumns: string[];
  inputParameters: string[];
  derivedItems: DerivedDependencyItem[];
  charts: ChartDependencyItem[];
}

function toUnique(values: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const value of values) {
    const trimmed = value.trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    out.push(trimmed);
  }
  return out;
}

export function extractFormulaReferences(formula: string): string[] {
  if (!formula.trim()) return [];

  const refs: string[] = [];
  const regex = /REF\(\[([^\]]+)\]\)|\[([^\]]+)\]/g;
  let match: RegExpExecArray | null = regex.exec(formula);

  while (match !== null) {
    const raw = (match[1] ?? match[2] ?? '').trim();
    if (raw.length > 0) refs.push(raw);
    match = regex.exec(formula);
  }

  return toUnique(refs);
}

export function isBuiltinTypeParameter(name: string): boolean {
  return /^(width|length|thickness|area|diameter|radius)$/i.test(name.trim());
}

function getDerivedType(item: DerivedColumnDef): 'derived-column' | 'derived-parameter' {
  return item.type === 'parameter' ? 'derived-parameter' : 'derived-column';
}

function classifyReference(
  name: string,
  derivedLookup: Map<string, 'derived-column' | 'derived-parameter'>,
  parameterSet: Set<string>,
  inputColumnSet: Set<string>
): DependencyReference {
  const derivedType = derivedLookup.get(name);
  if (derivedType) {
    return { name, kind: derivedType };
  }
  if (parameterSet.has(name)) {
    return { name, kind: 'parameter' };
  }
  if (!name.trim()) {
    return { name, kind: 'unknown' };
  }

  // Explicitly keep type parameters as parameters, even if they happen to be in input columns
  if (isBuiltinTypeParameter(name)) {
    return { name, kind: 'parameter' };
  }

  if (inputColumnSet.has(name)) {
    return { name, kind: 'column' };
  }
  // If not explicitly an input column, assume it's a metadata parameter (which is a scalar)
  return { name, kind: 'parameter' };
}

export function buildConfigDependencyModel(config: AnalysisConfig): ConfigDependencyModel {
  const inputColumns = toUnique(config.selectedColumns || []);
  const inputColumnSet = new Set(inputColumns);
  const inputParameters = toUnique((config.parameters || []).map((param) => param.name));
  const parameterSet = new Set(inputParameters);

  const derivedLookup = new Map<string, 'derived-column' | 'derived-parameter'>();
  for (const item of config.derivedColumns || []) {
    if (!item.name.trim()) continue;
    derivedLookup.set(item.name.trim(), getDerivedType(item));
  }

  const chartUsage = new Map<string, string[]>();
  for (const chart of config.charts || []) {
    const chartTitle = chart.title?.trim() || chart.id;
    const refs = toUnique([chart.xColumn || '', ...(chart.yColumns || [])]);
    for (const ref of refs) {
      if (!ref) continue;
      if (!chartUsage.has(ref)) chartUsage.set(ref, []);
      const list = chartUsage.get(ref);
      if (list && !list.includes(chartTitle)) list.push(chartTitle);
    }
  }

  const derivedItems: DerivedDependencyItem[] = (config.derivedColumns || []).map((item) => {
    const deps = item.dependencies && item.dependencies.length > 0
      ? toUnique(item.dependencies)
      : extractFormulaReferences(item.formula || '');
    return {
      id: item.id,
      name: item.name,
      type: item.type === 'parameter' ? 'parameter' : 'column',
      formula: item.formula || '',
      dependencies: deps.map((dep) => classifyReference(dep, derivedLookup, parameterSet, inputColumnSet)),
      usedByCharts: toUnique(chartUsage.get(item.name) || []),
    };
  });

  const charts: ChartDependencyItem[] = (config.charts || []).map((chart) => {
    const xName = chart.xColumn?.trim() || '';
    const yNames = toUnique(chart.yColumns || []);
    return {
      id: chart.id,
      title: chart.title?.trim() || chart.id,
      chartType: chart.chartType || 'unknown',
      xDependency: xName ? classifyReference(xName, derivedLookup, parameterSet, inputColumnSet) : null,
      yDependencies: yNames.map((name) => classifyReference(name, derivedLookup, parameterSet, inputColumnSet)),
    };
  });

  return {
    inputColumns,
    inputParameters,
    derivedItems,
    charts,
  };
}
