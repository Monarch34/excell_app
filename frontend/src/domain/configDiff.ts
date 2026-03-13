import type {
  AnalysisConfig,
  ChartSpec,
  DerivedColumnDef,
  Parameter,
} from '@/shared/types/domain';

export interface LiveConfigSnapshot {
  selectedColumns: string[];
  parameters: Parameter[];
  derivedColumns: string[];
  charts: string[];
}

export interface ListDiff {
  added: string[];
  removed: string[];
}

export interface ParameterDiff extends ListDiff {
  changed: string[];
}

export interface ConfigDiffResult {
  hasChanges: boolean;
  selectedColumns: ListDiff;
  parameters: ParameterDiff;
  derivedColumns: ListDiff;
  charts: ListDiff;
  counts: {
    current: {
      selectedColumns: number;
      parameters: number;
      derivedColumns: number;
      charts: number;
    };
    target: {
      selectedColumns: number;
      parameters: number;
      derivedColumns: number;
      charts: number;
    };
  };
}

function toUniqueSorted(values: string[]): string[] {
  return Array.from(
    new Set(
      values
        .map((value) => value.trim())
        .filter((value) => value.length > 0)
    )
  ).sort((a, b) => a.localeCompare(b));
}

function diffList(current: string[], target: string[]): ListDiff {
  const currentSet = new Set(current);
  const targetSet = new Set(target);

  return {
    added: target.filter((item) => !currentSet.has(item)),
    removed: current.filter((item) => !targetSet.has(item)),
  };
}

function chartLabel(chart: ChartSpec): string {
  const title = chart.title.trim();
  if (title) return title;

  const yPart = chart.yColumns.join(', ').trim();
  if (chart.xColumn.trim() && yPart) {
    return `${chart.xColumn.trim()} vs ${yPart}`;
  }

  return chart.id;
}

function toParameterMap(params: Parameter[]): Map<string, Parameter> {
  const map = new Map<string, Parameter>();
  for (const param of params) {
    const key = param.name.trim();
    if (!key || map.has(key)) continue;
    map.set(key, param);
  }
  return map;
}

function formatParameterChange(current: Parameter, target: Parameter): string {
  const currentUnit = current.unit?.trim() ? ` ${current.unit.trim()}` : '';
  const targetUnit = target.unit?.trim() ? ` ${target.unit.trim()}` : '';
  return `${current.name}: ${current.value}${currentUnit} -> ${target.value}${targetUnit}`;
}

function extractDerivedColumnNames(columns: DerivedColumnDef[]): string[] {
  return columns
    .filter((column) => (column.type || 'column') === 'column')
    .map((column) => column.name);
}

export function buildLiveConfigSnapshot(input: {
  selectedColumns: string[];
  parameters: Parameter[];
  derivedColumns: DerivedColumnDef[];
  charts: ChartSpec[];
}): LiveConfigSnapshot {
  return {
    selectedColumns: toUniqueSorted(input.selectedColumns),
    parameters: input.parameters
      .map((param) => ({
        ...param,
        name: param.name.trim(),
      }))
      .filter((param) => param.name.length > 0),
    derivedColumns: toUniqueSorted(extractDerivedColumnNames(input.derivedColumns)),
    charts: toUniqueSorted(input.charts.map(chartLabel)),
  };
}

export function buildConfigDiff(
  current: LiveConfigSnapshot,
  targetConfig: AnalysisConfig
): ConfigDiffResult {
  const targetSelectedColumns = toUniqueSorted(targetConfig.selectedColumns || []);
  const targetDerivedColumns = toUniqueSorted(extractDerivedColumnNames(targetConfig.derivedColumns || []));
  const targetCharts = toUniqueSorted((targetConfig.charts || []).map(chartLabel));

  const selectedColumns = diffList(current.selectedColumns, targetSelectedColumns);
  const derivedColumns = diffList(current.derivedColumns, targetDerivedColumns);
  const charts = diffList(current.charts, targetCharts);

  const currentParamMap = toParameterMap(current.parameters);
  const targetParamMap = toParameterMap(targetConfig.parameters || []);
  const currentParamNames = toUniqueSorted(Array.from(currentParamMap.keys()));
  const targetParamNames = toUniqueSorted(Array.from(targetParamMap.keys()));
  const parameterListDiff = diffList(currentParamNames, targetParamNames);

  const changed: string[] = [];
  for (const name of currentParamNames) {
    const currentParam = currentParamMap.get(name);
    const targetParam = targetParamMap.get(name);
    if (!currentParam || !targetParam) continue;

    const valueChanged = currentParam.value !== targetParam.value;
    const unitChanged = (currentParam.unit || '') !== (targetParam.unit || '');
    if (valueChanged || unitChanged) {
      changed.push(formatParameterChange(currentParam, targetParam));
    }
  }

  const parameters: ParameterDiff = {
    ...parameterListDiff,
    changed: changed.sort((a, b) => a.localeCompare(b)),
  };

  const hasChanges =
    selectedColumns.added.length > 0 ||
    selectedColumns.removed.length > 0 ||
    parameters.added.length > 0 ||
    parameters.removed.length > 0 ||
    parameters.changed.length > 0 ||
    derivedColumns.added.length > 0 ||
    derivedColumns.removed.length > 0 ||
    charts.added.length > 0 ||
    charts.removed.length > 0;

  return {
    hasChanges,
    selectedColumns,
    parameters,
    derivedColumns,
    charts,
    counts: {
      current: {
        selectedColumns: current.selectedColumns.length,
        parameters: currentParamNames.length,
        derivedColumns: current.derivedColumns.length,
        charts: current.charts.length,
      },
      target: {
        selectedColumns: targetSelectedColumns.length,
        parameters: targetParamNames.length,
        derivedColumns: targetDerivedColumns.length,
        charts: targetCharts.length,
      },
    },
  };
}
