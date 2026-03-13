import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import { extractErrorMessage } from '@/services/httpClient';
import { exportXlsx } from '@/services/reportsApi';
import { useDatasetStore } from '@/stores/dataset';
import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useChartsStore } from '@/stores/charts';
import { useConfigManagerStore } from '@/stores/configManager';
import { useAnalysisStore } from '@/stores/analysis';
import { DEFAULT_EXPORT_FILENAME } from '@/constants/config';
import { buildHeaderMappingFromConfig } from '@/utils/headerMapping';
import type { ExportRequest } from '@/types/api';

export function normalizeFilenameCandidate(value: string | null | undefined): string {
  return (value || '').trim().replace(/[^a-zA-Z0-9 _-]/g, '').trim();
}

export function useConfigExportReport() {
  const datasetStore = useDatasetStore();
  const columnsStore = useColumnsStore();
  const parametersStore = useParametersStore();
  const derivedStore = useDerivedColumnsStore();
  const chartsStore = useChartsStore();
  const configManagerStore = useConfigManagerStore();
  const analysisStore = useAnalysisStore();
  const { charts } = storeToRefs(chartsStore);

  const customFilename = ref(DEFAULT_EXPORT_FILENAME);
  const exportLoading = ref(false);
  const exportError = ref<string | null>(null);

  function sanitizeFilename(value: string | null | undefined): string {
    const safe = normalizeFilenameCandidate(value);
    return safe || DEFAULT_EXPORT_FILENAME;
  }

  function buildDownloadFilename(baseName: string): string {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    const stamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    return `${baseName}-${stamp}.xlsx`;
  }

  function normalizeHex(value: string | null | undefined): string | null {
    if (!value) return null;
    const cleaned = String(value).trim().replace(/^#/, '');
    if (!/^[0-9a-fA-F]{6}$/.test(cleaned)) return null;
    return cleaned.toUpperCase();
  }

  async function handleExport(): Promise<void> {
    exportLoading.value = true;
    exportError.value = null;

    try {
      if (!datasetStore.datasetId) {
        throw new Error('Dataset session is missing. Please upload the file again before export.');
      }
      const {
        selectedColumnNames,
        columnOrder,
        parameterOrder,
        linkedGroups,
        matchingGroups,
        separators,
        separatorColor,
      } = columnsStore;
      const { derivedColumns } = derivedStore;
      const enabledDerivedColumns = derivedColumns.filter((dc) => dc.enabled && dc.type !== 'parameter');
      const enabledDerivedNames = enabledDerivedColumns.map((dc) => dc.name);
      const enabledDerivedParameters = derivedColumns.filter((dc) => dc.enabled && dc.type === 'parameter');
      const orderPool = new Set<string>([...selectedColumnNames, ...enabledDerivedNames]);
      const exportColumnOrder = columnOrder
        .filter((name, idx, arr) => arr.indexOf(name) === idx && orderPool.has(name));
      for (const name of [...selectedColumnNames, ...enabledDerivedNames]) {
        if (!exportColumnOrder.includes(name)) exportColumnOrder.push(name);
      }

      const columnColors: Record<string, string> = {};
      const headerMapping = buildHeaderMappingFromConfig(configManagerStore.currentConfig);
      const parameterUnits: Record<string, string> = { ...(datasetStore.metadata?.parameterUnits || {}) };
      const columnUnits = { ...(datasetStore.metadata?.units || {}) };

      for (const dp of derivedColumns) {
        if (dp.type === 'parameter' && dp.unit) parameterUnits[dp.name] = dp.unit;
      }

      const currentConfig = configManagerStore.currentConfig;
      if (currentConfig?.columnMetadata) {
        for (const [col, meta] of Object.entries(currentConfig.columnMetadata)) {
          if (meta.unit) columnUnits[col] = meta.unit;
        }
      }

      for (const group of matchingGroups) {
        const normalizedColor = normalizeHex(group.color);
        if (!normalizedColor) continue;
        for (const col of group.columns) {
          columnColors[col] = normalizedColor;
        }
      }

      const exportCharts = charts.value
        .map((c) => {
          const resolvedChartType = (c.chartType === 'line' || c.chartType === 'scatter' || c.chartType === 'area')
            ? c.chartType
            : (c.areaSpec ? 'area' : null);
          if (!resolvedChartType) return null;
          return {
            id: c.id,
            title: c.title,
            x_column: c.xColumn,
            y_columns: c.yColumns,
            chart_type: resolvedChartType as 'line' | 'scatter' | 'area',
            // Baseline selection drives chart region filtering and area partitioning.
            baseline_spec: c.baselineSpec
              ? {
                  x_baseline: c.baselineSpec.xBaseline ?? 0,
                  y_baseline: c.baselineSpec.yBaseline ?? 0,
                  regions: c.baselineSpec.regions || [],
                }
              : null,
            line_width: c.lineWidth ?? null,
            marker_size: c.markerSize ?? null,
            area_spec: resolvedChartType === 'area' && c.areaSpec
              ? {
                  mode: c.areaSpec.mode,
                  baseline: c.areaSpec.baseline ?? 0,
                  baseline_axis: c.areaSpec.baselineAxis ?? 'y',
                  x_column: c.areaSpec.xColumn,
                  y_column: c.areaSpec.yColumn,
                  label: c.areaSpec.label?.trim() || null,
                }
              : null,
            line_color: c.lineColor,
            fill_color: c.fillColor,
            fill_opacity: c.fillOpacity ?? 0.4,
          };
        })
        .filter((chart): chart is NonNullable<typeof chart> => chart !== null);

      const parameterByName = new Map(
        enabledDerivedParameters.map((parameter) => [parameter.name, parameter] as const)
      );
      const orderedParameterNames = parameterOrder.filter((name) => parameterByName.has(name));
      for (const parameter of enabledDerivedParameters) {
        if (!orderedParameterNames.includes(parameter.name)) {
          orderedParameterNames.push(parameter.name);
        }
      }
      const exportMetrics = orderedParameterNames
        .map((name, idx) => {
          const raw = analysisStore.results[name];
          if (typeof raw !== 'number' || !Number.isFinite(raw)) return null;
          const parameter = parameterByName.get(name);
          return {
            id: `param-${idx + 1}`,
            chart_id: '',
            chart_title: '',
            name,
            value: raw,
            unit: parameter?.unit || '',
            x_column: '',
            y_column: '',
          };
        })
        .filter((metric): metric is NonNullable<typeof metric> => metric !== null);

      const payload: ExportRequest = {
        dataset_id: datasetStore.datasetId,
        schema_version: '1.0',
        units: columnUnits,
        project_name: customFilename.value || DEFAULT_EXPORT_FILENAME,
        custom_filename: customFilename.value || undefined,
        selected_columns: selectedColumnNames,
        column_mapping: columnsStore.columnMapping,
        derived_columns: derivedColumns
          .filter((dc) => dc.enabled && dc.type !== 'parameter')
          .map((dc) => ({
            id: dc.id,
            name: dc.name,
            formula: dc.formula,
            unit: dc.unit,
            description: dc.description,
            dependencies: dc.dependencies,
            enabled: dc.enabled,
          })),
        charts: exportCharts,
        parameters: { ...(datasetStore.metadata?.parameters || {}), ...parametersStore.parameterMap },
        operations: [],
        derived_parameters: derivedColumns
          .filter((dc) => dc.enabled && dc.type === 'parameter')
          .map((dp) => ({ name: dp.name, formula: dp.formula })),
        metrics: exportMetrics,
        column_layout: {
          column_order: exportColumnOrder,
          linked_groups: linkedGroups,
          matching_groups: matchingGroups,
          separator_indices: separators,
          separator_color: separatorColor,
        },
        column_colors: columnColors,
        header_mapping: headerMapping,
        parameter_units: parameterUnits,
        reference_index: datasetStore.referenceRowIndex,
      };

      const blob = await exportXlsx(payload);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = buildDownloadFilename(sanitizeFilename(customFilename.value));
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: unknown) {
      exportError.value = extractErrorMessage(e);
    } finally {
      exportLoading.value = false;
    }
  }

  return {
    customFilename,
    exportLoading,
    exportError,
    handleExport,
  };
}
