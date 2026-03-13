<script setup lang="ts">
import Button from 'primevue/button';
import type { BaselineRegion } from '@/types/domain';

const regionOptions: Array<{ label: string; value: BaselineRegion }> = [
  { label: 'Top-Left', value: 'top-left' },
  { label: 'Top-Right', value: 'top-right' },
  { label: 'Bottom-Left', value: 'bottom-left' },
  { label: 'Bottom-Right', value: 'bottom-right' },
];

defineProps<{
  selectedRegions: BaselineRegion[];
}>();

const emit = defineEmits<{
  toggle: [region: BaselineRegion];
  selectAll: [];
  clear: [];
}>();

function regionNumber(region: BaselineRegion): string {
  if (region === 'top-right') return '1';
  if (region === 'top-left') return '2';
  if (region === 'bottom-left') return '3';
  if (region === 'bottom-right') return '4';
  return '';
}

function isSelected(region: BaselineRegion, selectedRegions: BaselineRegion[]) {
  return selectedRegions.includes(region);
}
</script>

<template>
  <div class="ui-region-panel">
    <div class="ui-region-panel-head">
      <span class="ui-region-panel-title">Coordinate Regions</span>
      <span class="ui-region-panel-note">Select one or more</span>
    </div>
    <div class="ui-region-plane-wrap">
      <div
        class="ui-region-grid"
        role="group"
        aria-label="Coordinate regions"
        :class="{ 'ui-region-grid--has-selection': selectedRegions.length > 0 }"
      >
        <button
          v-for="opt in regionOptions"
          :key="opt.value"
          type="button"
          class="ui-region-item"
          :class="{ 'is-selected': isSelected(opt.value, selectedRegions) }"
          :aria-pressed="isSelected(opt.value, selectedRegions)"
          @click="emit('toggle', opt.value)"
        >
          <span class="ui-region-q">Q{{ regionNumber(opt.value) }}</span>
          <span>{{ opt.label }}</span>
        </button>
      </div>
    </div>
    <div class="ui-region-actions">
      <Button label="Select All" severity="secondary" text size="small" @click="emit('selectAll')" />
      <Button label="Clear" severity="secondary" text size="small" @click="emit('clear')" />
    </div>
    <small class="ui-region-footnote">No selection means all regions.</small>
  </div>
</template>
