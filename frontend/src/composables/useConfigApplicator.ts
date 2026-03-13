import { useColumnsStore } from '@/stores/columns';
import { useParametersStore } from '@/stores/parameters';
import { useDerivedColumnsStore } from '@/stores/derivedColumns';
import { useChartsStore } from '@/stores/charts';
import { useDatasetStore } from '@/stores/dataset';
import type { AnalysisConfig, MatchingColumnGroup } from '@/shared/types/domain';

/**
 * Composable that applies a loaded AnalysisConfig to all relevant stores.
 */
export function useConfigApplicator() {
  const datasetStore = useDatasetStore();
  const columnsStore = useColumnsStore();
  const parametersStore = useParametersStore();
  const derivedStore = useDerivedColumnsStore();
  const chartsStore = useChartsStore();

  function applyConfig(config: AnalysisConfig) {
    const availableColumns = datasetStore.columnNames;
    const derivedNames = config.derivedColumns.map((d) => d.name);
    const selected = (config.selectedColumns || []).filter((name) =>
      availableColumns.includes(name)
    );

    // Apply selected columns
    columnsStore.selectAll(selected);

    // Apply column order + separators
    const availableForOrder = new Set([...availableColumns, ...derivedNames]);
    const orderSource = Array.isArray(config.columnOrder) ? config.columnOrder : [];
    const order = orderSource.filter((name) => availableForOrder.has(name));
    columnsStore.initializeOrder(order);

    const maxSeparatorIndex = Math.max(-1, order.length - 2);
    const separatorsSource = Array.isArray(config.separators) ? config.separators : [];
    const sanitizedSeparators = Array.from(
      new Set(
        separatorsSource.filter(
          (index) => Number.isInteger(index) && index >= 0 && index <= maxSeparatorIndex
        )
      )
    ).sort((a, b) => a - b);
    columnsStore.separators = sanitizedSeparators;
    if (typeof config.separatorColor === 'string') {
      columnsStore.setSeparatorColor(config.separatorColor);
    }

    const matchingGroupsSource = Array.isArray(config.matchingGroups) ? config.matchingGroups : [];
    columnsStore.setMatchingGroups(
      matchingGroupsSource as MatchingColumnGroup[],
      Array.from(availableForOrder)
    );

    // All loaded parameters map directly to user parameters.
    parametersStore.userParameters = [...config.parameters];

    // Apply derived columns
    derivedStore.loadFromConfig(config.derivedColumns);

    // Apply charts
    chartsStore.loadFromConfig(config.charts);

    const parameterNames = config.derivedColumns
      .filter((item) => item.type === 'parameter')
      .map((item) => item.name);
    const areaNames = config.charts
      .map((chart) => chart.areaSpec?.label?.trim() || '')
      .filter((label) => label.length > 0);
    const availableParameterNames = new Set([...parameterNames, ...areaNames]);
    const savedParameterOrder = Array.isArray(config.parameterOrder) ? config.parameterOrder : [];
    const nextParameterOrder = savedParameterOrder.filter((name) => availableParameterNames.has(name));
    for (const name of availableParameterNames) {
      if (!nextParameterOrder.includes(name)) nextParameterOrder.push(name);
    }
    columnsStore.setParameterOrder(nextParameterOrder);
  }

  return { applyConfig };
}
