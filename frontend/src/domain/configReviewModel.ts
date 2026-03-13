import type { AnalysisConfig, MatchingColumnGroup } from '@/shared/types/domain';
import { normalizeColorToHex } from '@/utils/color';

const FALLBACK_SEPARATOR_COLOR = '#2F855A';

export interface ConfigReviewSeparatorSummary {
  color: string;
  colorText: string;
  positions: number[];
}

export interface ConfigReviewGroupLegend {
  id: string;
  name: string;
  color: string;
  count: number;
}

export interface ConfigReviewColumnItem {
  index: number;
  name: string;
  description: string;
  unit: string;
  colorRaw: string | null;
  colorText: string;
  groupName: string;
  groupColor: string | null;
  isSeparator: boolean;
}

export interface ConfigReviewParameterItem {
  name: string;
  source: string;
  definedUnit: string;
  valueText: string;
  description: string;
}

export interface ConfigReviewModel {
  separators: ConfigReviewSeparatorSummary;
  groups: ConfigReviewGroupLegend[];
  columns: ConfigReviewColumnItem[];
  parameters: ConfigReviewParameterItem[];
}

export function buildConfigReviewModel(
  config: AnalysisConfig,
  metadataParamValues?: Map<string, { value: number; unit: string }>,
  referencedParameterNames: string[] = [],
): ConfigReviewModel {
  const groupByColumn = buildGroupMap(config.matchingGroups ?? []);
  const separatorSet = new Set(config.separators ?? []);
  const columnOrder = resolveColumnOrder(config);
  const separatorColorRaw = (config.separatorColor || '').trim();
  const separatorColor = separatorColorRaw || 'var(--separator-color)';

  const columns: ConfigReviewColumnItem[] = columnOrder.map((name, index) => {
    const metadata = config.columnMetadata?.[name];
    const group = groupByColumn.get(name);
    const colorRaw = (metadata?.color || '').trim() || null;

    return {
      index,
      name,
      description: (metadata?.label || '').trim() || 'Same as column name',
      unit: (metadata?.unit || '').trim() || 'Relative',
      colorRaw,
      colorText: formatColorValue(colorRaw),
      groupName: group?.name || 'Ungrouped',
      groupColor: group?.color || null,
      isSeparator: separatorSet.has(index),
    };
  });

  const parameters = buildParameters(config, metadataParamValues, referencedParameterNames);
  const groups: ConfigReviewGroupLegend[] = (config.matchingGroups ?? []).map((group) => ({
    id: group.id,
    name: group.name,
    color: group.color,
    count: group.columns.length,
  }));

  const separatorBaseColor = separatorColorRaw || FALLBACK_SEPARATOR_COLOR;
  const separatorColorHex = normalizeColorToHex(separatorBaseColor) ?? FALLBACK_SEPARATOR_COLOR;

  return {
    separators: {
      color: separatorColor,
      colorText: separatorColorHex,
      positions: [...(config.separators ?? [])],
    },
    groups,
    columns,
    parameters,
  };
}

function resolveColumnOrder(config: AnalysisConfig): string[] {
  const order = Array.isArray(config.columnOrder) ? [...config.columnOrder] : [];
  if (order.length > 0) return order;
  return [...(config.selectedColumns ?? [])];
}

function buildGroupMap(groups: MatchingColumnGroup[]): Map<string, MatchingColumnGroup> {
  const map = new Map<string, MatchingColumnGroup>();
  for (const group of groups) {
    for (const column of group.columns) {
      if (!map.has(column)) map.set(column, group);
    }
  }
  return map;
}

function buildParameters(
  config: AnalysisConfig,
  metadataParamValues?: Map<string, { value: number; unit: string }>,
  referencedParameterNames: string[] = [],
): ConfigReviewParameterItem[] {
  const configParamMap = new Map(config.parameters.map((parameter) => [parameter.name, parameter]));
  const derivedParamMap = new Map(
    (config.derivedColumns ?? [])
      .filter((item) => item.type === 'parameter')
      .map((item) => [item.name, item]),
  );

  const ordered = new Set<string>(config.parameterOrder ?? []);
  for (const name of configParamMap.keys()) ordered.add(name);
  for (const name of derivedParamMap.keys()) ordered.add(name);
  for (const name of referencedParameterNames) ordered.add(name);
  for (const name of metadataParamValues?.keys() ?? []) ordered.add(name);

  return [...ordered].map((name) => {
    const configParam = configParamMap.get(name);
    const derivedParam = derivedParamMap.get(name);
    const metadataParam = metadataParamValues?.get(name);
    const isReferenced = referencedParameterNames.includes(name);

    const inConfig = Boolean(configParam);
    const inDerived = Boolean(derivedParam);
    const inMetadata = Boolean(metadataParam);

    return {
      name,
      source: resolveParameterSource({ inConfig, inDerived, inMetadata, isReferenced }),
      definedUnit:
        (configParam?.unit || '').trim()
        || (derivedParam?.unit || '').trim()
        || (metadataParam?.unit || '').trim()
        || 'Relative',
      valueText: formatParameterValue({
        configParam,
        derivedParam,
        metadataParam,
        isReferenced,
      }),
      description:
        (derivedParam?.description || '').trim()
        || (inConfig ? 'Configured parameter.' : '')
        || (inMetadata ? 'Loaded from dataset metadata.' : '')
        || (isReferenced ? 'Referenced by formulas and expected from dataset metadata.' : '')
        || 'Not defined',
    };
  });
}

function resolveParameterSource(input: {
  inConfig: boolean;
  inDerived: boolean;
  inMetadata: boolean;
  isReferenced: boolean;
}): string {
  const { inConfig, inDerived, inMetadata, isReferenced } = input;
  if (inConfig && inMetadata) return 'Config + Metadata';
  if (inDerived && inMetadata) return 'Derived + Metadata';
  if (inConfig) return 'Config';
  if (inDerived) return 'Derived';
  if (inMetadata) return 'Metadata';
  if (isReferenced) return 'Metadata Reference';
  return 'Unknown';
}

function formatParameterValue(input: {
  configParam?: AnalysisConfig['parameters'][number];
  derivedParam?: AnalysisConfig['derivedColumns'][number];
  metadataParam?: { value: number; unit: string };
  isReferenced: boolean;
}): string {
  const { configParam, derivedParam, metadataParam, isReferenced } = input;

  if (metadataParam && configParam) {
    const liveText = formatScalarValue(metadataParam.value, metadataParam.unit);
    const configText = formatScalarValue(configParam.value, configParam.unit);
    return liveText === configText ? liveText : `${liveText} (config ${configText})`;
  }

  if (metadataParam) return formatScalarValue(metadataParam.value, metadataParam.unit);
  if (configParam) return formatScalarValue(configParam.value, configParam.unit);
  if (derivedParam) return 'Computed at runtime';
  if (isReferenced) return 'Waiting for dataset metadata';
  return 'Not defined';
}

function formatScalarValue(value: number | null, unit: string): string {
  if (value === null || !Number.isFinite(value)) return 'Not defined';
  return unit.trim() ? `${value} ${unit.trim()}` : `${value}`;
}

function formatColorValue(color: string | null): string {
  if (!color) return 'Auto';
  const normalized = normalizeColorToHex(color);
  if (!normalized) return color.toUpperCase();
  if (normalized.toLowerCase() === color.toLowerCase()) return normalized;
  return `${normalized} (${color})`;
}

