<script setup lang="ts">
import type { ConfigReviewModel } from '@/domain/configReviewModel';

defineProps<{
  reviewModel: ConfigReviewModel;
}>();
</script>

<template>
  <div class="cfg-section-body">
    <div class="cfg-static-params cfg-col-grid cfg-col-grid--meta">
      <div
        v-for="(parameter, index) in reviewModel.parameters"
        :key="parameter.name"
        class="cfg-col-item cfg-col-item--meta"
      >
        <div class="cfg-col-num">#{{ index + 1 }}</div>
        <div class="cfg-col-details">
          <div class="cfg-col-main">
            <span class="cfg-col-name">{{ parameter.name }}</span>
            <span class="cfg-col-group-tag cfg-col-group-tag--source">{{ parameter.source }}</span>
          </div>
          <div class="cfg-col-meta-list">
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Name</span>
              <span class="cfg-col-meta-value">{{ parameter.name }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Source</span>
              <span class="cfg-col-meta-value">{{ parameter.source }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Defined Unit</span>
              <span class="cfg-col-meta-value">{{ parameter.definedUnit }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Value</span>
              <span class="cfg-col-meta-value">{{ parameter.valueText }}</span>
            </span>
            <span class="cfg-col-meta-item">
              <span class="cfg-col-meta-label">Description</span>
              <span class="cfg-col-meta-value">{{ parameter.description }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


