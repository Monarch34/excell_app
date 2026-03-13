import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Parameter } from '@/types/domain';

/**
 * Parameters store - manages user-defined parameters.
 */
export const useParametersStore = defineStore('parameters', () => {

  // State

  const userParameters = ref<Parameter[]>([]);

  // Getters

  const allParameters = computed<Parameter[]>(() => {
    return [...userParameters.value];
  });

  const duplicateNames = computed<string[]>(() => {
    const seen = new Map<string, string>();
    const duplicates = new Set<string>();

    for (const p of userParameters.value) {
      const trimmed = p.name.trim();
      if (!trimmed) continue;
      const key = trimmed.toLowerCase();

      if (seen.has(key)) {
        duplicates.add(seen.get(key) || trimmed);
        duplicates.add(trimmed);
      } else {
        seen.set(key, trimmed);
      }
    }

    return Array.from(duplicates);
  });

  const hasDuplicateNames = computed(() => duplicateNames.value.length > 0);

  const parameterMap = computed<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    const seenLower = new Set<string>();
    for (const p of allParameters.value) {
      const name = p.name.trim();
      if (!name) continue;
      if (typeof p.value !== 'number' || !Number.isFinite(p.value)) continue;
      const key = name.toLowerCase();
      if (seenLower.has(key)) continue;
      seenLower.add(key);
      map[name] = p.value;
    }
    return map;
  });

  const isValid = computed(() => {
    // All user parameters must have names and finite numeric values
    return userParameters.value.every((p) => p.name.trim() !== '' && typeof p.value === 'number' && Number.isFinite(p.value)) && !hasDuplicateNames.value;
  });

  // Actions

  function addParameter(param?: Partial<Parameter>) {
    userParameters.value.push({
      name: param?.name || `param_${userParameters.value.length + 1}`,
      value: param?.value ?? 0,
      unit: param?.unit || '',
    });
  }

  function updateParameter(index: number, updates: Partial<Parameter>) {
    if (index >= 0 && index < userParameters.value.length) {
      if (
        updates.value !== undefined &&
        updates.value !== null &&
        !Number.isFinite(updates.value)
      ) {
        console.warn(`Rejecting non-finite parameter value: ${updates.value}`);
        return;
      }
      userParameters.value[index] = {
        ...userParameters.value[index],
        ...updates,
      };
    }
  }

  function removeParameter(index: number) {
    if (index >= 0 && index < userParameters.value.length) {
      userParameters.value.splice(index, 1);
    }
  }

  function reset() {
    userParameters.value = [];
  }

  return {
    userParameters,
    allParameters,
    duplicateNames,
    hasDuplicateNames,
    parameterMap,
    isValid,
    addParameter,
    updateParameter,
    removeParameter,
    reset,
  };
});
