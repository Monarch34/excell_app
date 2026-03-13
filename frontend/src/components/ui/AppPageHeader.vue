<script setup lang="ts">
import { computed } from 'vue';

type IconTone = 'primary' | 'success' | 'warning' | 'error';

const props = withDefaults(
  defineProps<{
    icon: string;
    title: string;
    iconColor?: IconTone;
  }>(),
  {
    iconColor: 'primary',
  }
);

const iconToneClass = computed(() => {
  if (props.iconColor === 'success') return 'ui-color-success';
  if (props.iconColor === 'warning') return 'ui-color-warning';
  if (props.iconColor === 'error') return 'ui-color-error';
  return 'ui-color-info';
});
</script>

<template>
  <div class="step-toolbar ui-page-header ui-page-header-bar">
    <div class="ui-section-header-title">
      <i :class="['pi', props.icon, iconToneClass]" />
      <span>{{ props.title }}</span>
    </div>
    <div v-if="$slots.default" class="ui-page-header-actions">
      <slot />
    </div>
  </div>
</template>
