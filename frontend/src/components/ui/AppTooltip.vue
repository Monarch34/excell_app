<script setup lang="ts">
withDefaults(
  defineProps<{
    text: string;
    position?: 'top' | 'bottom' | 'left' | 'right';
    showIcon?: boolean;
  }>(),
  {
    position: 'top',
    showIcon: true,
  }
);
</script>

<template>
  <span
    v-tooltip:[position]="text"
    class="app-tooltip ui-tooltip"
    :class="{ 'with-icon': showIcon }"
  >
    <slot>
      <i v-if="showIcon" class="pi pi-question-circle"></i>
    </slot>
  </span>
</template>
