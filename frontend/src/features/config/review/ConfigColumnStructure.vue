<script setup lang="ts">
import { computed } from 'vue';
import type { ConfigReviewColumnItem, ConfigReviewModel } from '@/domain/configReviewModel';

const props = defineProps<{
  reviewModel: ConfigReviewModel;
}>();

const separatorStyleVars = computed<Record<string, string>>(() => ({
  '--cfg-separator-color': props.reviewModel.separators.color,
}));

function getColumnStyle(column: ConfigReviewColumnItem): Record<string, string> {
  const style: Record<string, string> = {};
  if (column.groupColor) style.borderLeft = `3px solid ${column.groupColor}`;
  return style;
}
</script>

<template>
  <div class="cfg-section-body cfg-section-body--columns" :style="separatorStyleVars">
    <div v-if="reviewModel.separators.positions.length" class="cfg-separator-row">
      <i class="pi pi-minus cfg-sep-icon"></i>
      <span class="cfg-sep-label">Separators:</span>
      <span class="cfg-sep-key">
        <span class="cfg-sep-swatch" :style="{ backgroundColor: reviewModel.separators.color }"></span>
        <code class="cfg-sep-hex">{{ reviewModel.separators.colorText }}</code>
      </span>
      <span v-for="sep in reviewModel.separators.positions" :key="sep" class="cfg-sep-chip">
        After #{{ sep + 1 }}
      </span>
    </div>

    <div v-if="reviewModel.groups.length" class="cfg-groups-legend">
      <span v-for="group in reviewModel.groups" :key="group.id" class="cfg-group-chip">
        <span class="cfg-group-dot" :style="{ background: group.color }"></span>
        {{ group.name }} ({{ group.count }})
      </span>
    </div>

    <div class="cfg-col-grid">
      <div
        v-for="column in reviewModel.columns"
        :key="column.name"
        class="cfg-col-item"
        :class="{ 'cfg-col-item--separator': column.isSeparator }"
        :style="getColumnStyle(column)"
      >
        <div class="cfg-col-num">#{{ column.index + 1 }}</div>
        <div class="cfg-col-details">
          <div class="cfg-col-main">
            <span class="cfg-col-name">{{ column.name }}</span>
            <span class="cfg-col-group-tag">{{ column.groupName }}</span>
          </div>
          <div class="cfg-col-meta-list">
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Name</span>
              <span class="cfg-col-meta-value">{{ column.name }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Description</span>
              <span class="cfg-col-meta-value">{{ column.description }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Defined Unit</span>
              <span class="cfg-col-meta-value">{{ column.unit }}</span>
            </span>
            <span class="cfg-col-meta-item cfg-col-meta-item--color">
              <span class="cfg-col-meta-label">Color</span>
              <span class="cfg-col-meta-value cfg-col-meta-value--color">
                <span
                  v-if="column.colorRaw"
                  class="cfg-sep-swatch cfg-sep-swatch--tiny"
                  :style="{ backgroundColor: column.colorRaw }"
                ></span>
                {{ column.colorText }}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


