<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { DerivedColumnDef } from '@/types/domain';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';
import AppPageHeader from '@/components/ui/AppPageHeader.vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';

const props = withDefaults(defineProps<{
  title: string;
  headerIcon: string;
  itemIcon: string;
  items: DerivedColumnDef[];
  activeId: string | null;
  canAdd: boolean;
  maxItems: number;
  emptyMessage: string;
  countLabel: string;
  addTooltip: string;
  tagSeverity?: 'info' | 'warn' | 'success' | 'secondary' | 'danger' | 'contrast';
  pageSize?: number;
}>(), {
  pageSize: 4,
  tagSeverity: 'info',
});

const emit = defineEmits<{
  add: [];
  select: [id: string];
  toggle: [id: string];
  remove: [id: string];
}>();

const page = ref(1);

const totalPages = computed(() => Math.max(1, Math.ceil(props.items.length / props.pageSize)));
const pagedItems = computed(() => {
  const start = (page.value - 1) * props.pageSize;
  return props.items.slice(start, start + props.pageSize);
});

watch(
  () => props.items.length,
  () => {
    page.value = Math.min(page.value, totalPages.value);
  }
);
</script>

<template>
  <AppSurfacePanel class="ui-calc-section">
    <AppPageHeader :icon="headerIcon" :title="title" class="ui-calc-section-header">
      <Button
        icon="pi pi-plus"
        size="small"
        severity="primary"
        rounded
        :disabled="!canAdd"
        @click="emit('add')"
        v-tooltip.top="addTooltip"
      />
    </AppPageHeader>

    <div class="text-color-secondary text-xs ui-calc-count">
      {{ items.length }} / {{ maxItems }} {{ countLabel }}
    </div>

    <div v-if="items.length === 0" class="ui-empty-state">
      {{ emptyMessage }}
    </div>

    <div class="ui-calc-list">
      <div
        v-for="item in pagedItems"
        :key="item.id"
        class="ui-calc-item"
        :class="{ 'ui-calc-item--active': activeId === item.id, 'ui-calc-item--disabled': !item.enabled }"
        @click="emit('select', item.id)"
      >
        <div class="ui-calc-item-main">
          <i class="text-primary ui-calc-item-icon" :class="itemIcon"></i>
          <span class="font-semibold text-color ui-calc-item-text">{{ item.name }}</span>
          <Tag v-if="item.unit" :value="item.unit" :severity="tagSeverity" class="text-xs" />
        </div>
        <div class="ui-calc-item-actions">
          <Button
            :icon="item.enabled ? 'pi pi-eye' : 'pi pi-eye-slash'"
            size="small"
            :severity="item.enabled ? 'secondary' : 'danger'"
            text
            class="ui-action-icon-btn"
            @click.stop="emit('toggle', item.id)"
          />
          <Button
            icon="pi pi-trash"
            size="small"
            severity="danger"
            text
            class="ui-action-icon-btn ui-delete-btn"
            @click.stop="emit('remove', item.id)"
          />
        </div>
      </div>
    </div>

    <div v-if="items.length > pageSize" class="ui-calc-pager">
      <Button
        icon="pi pi-chevron-left"
        text
        size="small"
        :disabled="page === 1"
        @click="page = Math.max(1, page - 1)"
      />
      <span class="ui-calc-pager-text">{{ page }} / {{ totalPages }}</span>
      <Button
        icon="pi pi-chevron-right"
        text
        size="small"
        :disabled="page === totalPages"
        @click="page = Math.min(totalPages, page + 1)"
      />
    </div>
  </AppSurfacePanel>
</template>
