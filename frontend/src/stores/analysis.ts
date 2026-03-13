import { defineStore } from 'pinia';
import { computed, ref, shallowRef } from 'vue';
import type { ProcessResults, ProcessRow } from '@/types/api';

/**
 * Analysis store - manages processed data and processing run state.
 */
export const useAnalysisStore = defineStore('analysis', () => {
  const processedData = shallowRef<ProcessRow[]>([]);
  const runId = shallowRef<string | null>(null);
  const isAnalyzing = ref(false);
  const analysisError = ref<string | null>(null);
  const results = ref<ProcessResults>({});

  const hasResults = computed(() => processedData.value.length > 0);

  function setProcessedData(data: ProcessRow[]) {
    processedData.value = data;
  }

  function setRunId(value: string | null) {
    runId.value = value;
  }

  function setResults(value: ProcessResults) {
    results.value = value;
  }

  function reset() {
    processedData.value = [];
    runId.value = null;
    isAnalyzing.value = false;
    analysisError.value = null;
    results.value = {};
  }

  return {
    processedData,
    runId,
    isAnalyzing,
    analysisError,
    results,
    hasResults,
    setProcessedData,
    setRunId,
    setResults,
    reset,
  };
});
