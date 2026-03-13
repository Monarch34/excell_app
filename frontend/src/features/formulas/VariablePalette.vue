<script setup lang="ts">
import Button from 'primevue/button';
import { computed } from 'vue';

const props = defineProps<{
  columns: string[];
  metadataParameters: string[];
  parameters: string[];
  derivedParameters: string[];
  derivedColumnNames: string[];
  referenceRowIndex: number | null;
}>();

const emit = defineEmits<{
  insert: [varName: string];
  insertRef: [varName: string];
}>();

const combinedParameters = computed(() => {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const name of props.metadataParameters) {
    if (!seen.has(name)) {
      seen.add(name);
      ordered.push(name);
    }
  }
  for (const name of props.parameters) {
    if (!seen.has(name)) {
      seen.add(name);
      ordered.push(name);
    }
  }
  return ordered;
});

// Show REF section only when reference row is selected
const showRefSection = computed(() => props.referenceRowIndex !== null);
</script>

<template>
  <div class="ui-variable-palette">
    <!-- Dataset Columns -->
    <div class="ui-variable-section" v-if="columns.length > 0">
      <span class="ui-variable-group-title">Dataset Columns</span>
      <div class="ui-variable-chip-row">
        <Button
          v-for="col in columns"
          :key="col"
          :label="col"
          size="small"
          severity="info"
          text
          class="ui-variable-chip ui-variable-chip--info"
          @click="emit('insert', col)"
        />
      </div>
    </div>

    <!-- Parameters -->
    <div class="ui-variable-section" v-if="combinedParameters.length > 0">
      <span class="ui-variable-group-title">Parameters</span>
      <div class="ui-variable-chip-row">
        <Button
          v-for="param in combinedParameters"
          :key="param"
          :label="param"
          size="small"
          severity="warn"
          text
          class="ui-variable-chip ui-variable-chip--warn"
          @click="emit('insert', param)"
        />
      </div>
    </div>

    <!-- Derived Parameters -->
    <div class="ui-variable-section" v-if="derivedParameters.length > 0">
      <span class="ui-variable-group-title">Derived Parameters</span>
      <div class="ui-variable-chip-row">
        <Button
          v-for="dp in derivedParameters"
          :key="dp"
          :label="dp"
          size="small"
          severity="help"
          text
          class="ui-variable-chip ui-variable-chip--help"
          @click="emit('insert', dp)"
        />
      </div>
    </div>

    <!-- Derived Columns -->
    <div class="ui-variable-section" v-if="derivedColumnNames.length > 0">
      <span class="ui-variable-group-title">Derived Columns</span>
      <div class="ui-variable-chip-row">
        <Button
          v-for="dc in derivedColumnNames"
          :key="dc"
          :label="dc"
          size="small"
          severity="success"
          text
          class="ui-variable-chip ui-variable-chip--success"
          @click="emit('insert', dc)"
        />
      </div>
    </div>

    <!-- Reference Row Values -->
    <div v-if="showRefSection && columns.length > 0">
      <span class="ui-variable-group-title">Reference Row Values</span>
      <div class="ui-variable-chip-row">
        <Button
          v-for="col in columns"
          :key="'ref-' + col"
          :label="'REF([' + col + '])'"
          size="small"
          severity="danger"
          text
          class="ui-variable-chip ui-variable-chip--danger"
          @click="emit('insertRef', col)"
        />
      </div>
    </div>
  </div>
</template>
