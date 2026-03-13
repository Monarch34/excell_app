<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import AppStepSection from '@/components/ui/AppStepSection.vue';
import type { SavedConfigSummary } from '@/services/configsApi';

const props = defineProps<{
  savedConfigs: SavedConfigSummary[];
  listLoading: boolean;
  selectedConfigId: number | null;
  deleteLoadingId: number | null;
  formatDate: (value: string | null | undefined) => string;
}>();

const emit = defineEmits<{
  select: [id: number];
  rename: [config: SavedConfigSummary];
  delete: [config: SavedConfigSummary];
}>();

const hasDomainValues = computed(() =>
  props.savedConfigs.some((config) => (config.domain || '').trim().length > 0)
);
const isMobile = ref(false);

function syncViewport() {
  isMobile.value = window.innerWidth <= 768;
}

onMounted(() => {
  syncViewport();
  window.addEventListener('resize', syncViewport);
});

onUnmounted(() => {
  window.removeEventListener('resize', syncViewport);
});

function resolveRowClass(config: SavedConfigSummary): string {
  return config.id === props.selectedConfigId ? 'ui-selected-row' : '';
}

function onRowClick(event: { data: SavedConfigSummary }) {
  emit('select', event.data.id);
}
</script>

<template>
  <AppStepSection
    icon="pi-database"
    title="Saved Configurations"
    class="cfg-list-section"
    collapsible
    :initiallyOpen="true"
  >
    <p class="ui-muted-hint text-sm cfg-section-intro">
      Select a saved configuration to inspect its dependency flow and apply it to the current workspace.
    </p>

    <div v-if="isMobile" class="cfg-library-mobile-list">
      <div v-if="listLoading" class="ui-empty-state text-center">
        <i class="pi pi-spinner pi-spin"></i>
        <div>Loading saved configurations...</div>
      </div>
      <div v-else-if="savedConfigs.length === 0" class="ui-empty-state text-center">
        <i class="pi pi-inbox"></i>
        <div>No configurations found.</div>
      </div>
      <article
        v-else
        v-for="config in savedConfigs"
        :key="`mobile-${config.id}`"
        class="cfg-library-mobile-card"
        :class="{ 'cfg-library-mobile-card--selected': config.id === selectedConfigId }"
      >
        <button
          type="button"
          class="cfg-library-mobile-main"
          @click="emit('select', config.id)"
        >
          <div class="cfg-library-mobile-name">{{ config.name }}</div>
          <div class="cfg-library-mobile-meta">
            <span>{{ formatDate(config.updated_at) }}</span>
            <span v-if="hasDomainValues && (config.domain || '').trim().length > 0">
              Domain: {{ config.domain }}
            </span>
          </div>
        </button>

        <div class="cfg-library-mobile-actions">
          <Button
            label="Inspect"
            icon="pi pi-search"
            size="small"
            severity="secondary"
            outlined
            @click="emit('select', config.id)"
          />
          <Button
            label="Rename"
            icon="pi pi-pencil"
            size="small"
            severity="secondary"
            text
            @click="emit('rename', config)"
          />
          <Button
            label="Delete"
            icon="pi pi-trash"
            size="small"
            severity="danger"
            text
            :loading="deleteLoadingId === config.id"
            @click="emit('delete', config)"
          />
        </div>
      </article>
    </div>

    <DataTable
      v-else
      :value="savedConfigs"
      :loading="listLoading"
      :rowClass="resolveRowClass"
      dataKey="id"
      class="ui-data-table ui-data-table--clickable-rows p-datatable-sm cfg-library-table"
      stripedRows
      scrollable
      scrollHeight="32rem"
      emptyMessage="No configurations found."
      @row-click="onRowClick"
    >
      <Column field="name" header="Name" sortable style="min-width: 220px">
        <template #body="slotProps">
          <span class="font-medium">{{ slotProps.data.name }}</span>
        </template>
      </Column>

      <Column v-if="hasDomainValues" field="domain" header="Domain" sortable style="min-width: 120px" />

      <Column
        field="updated_at"
        header="Last Updated"
        sortable
        style="min-width: 180px"
        headerClass="cfg-table-cell-right"
        bodyClass="cfg-table-cell-right"
      >
        <template #body="slotProps">
          {{ formatDate(slotProps.data.updated_at) }}
        </template>
      </Column>

      <Column header="Actions" :exportable="false" style="min-width: 7.5rem">
        <template #body="slotProps">
          <div class="flex gap-2 justify-content-end">
            <Button
              icon="pi pi-pencil"
              text
              rounded
              size="small"
              aria-label="Rename"
              @click.stop="emit('rename', slotProps.data)"
              v-tooltip.top="'Rename'"
            />
            <Button
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              size="small"
              :aria-label="`Delete ${slotProps.data.name}`"
              :loading="deleteLoadingId === slotProps.data.id"
              @click.stop="emit('delete', slotProps.data)"
              v-tooltip.top="'Delete'"
            />
          </div>
        </template>
      </Column>
    </DataTable>
  </AppStepSection>
</template>
