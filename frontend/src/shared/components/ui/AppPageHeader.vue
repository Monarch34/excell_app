<script setup lang="ts">
import { resolveIconToneClass } from '@/utils/ui';

type IconTone = 'primary' | 'success' | 'warning' | 'error';

const props = withDefaults(
  defineProps<{
    icon: string;
    title: string;
    subtitle?: string;
    iconColor?: IconTone;
    headingId?: string;
  }>(),
  {
    iconColor: 'primary',
    subtitle: undefined,
    headingId: undefined,
  }
);
</script>

<template>
  <div class="step-toolbar ui-page-header ui-page-header-bar">
    <div class="ui-section-header-title">
      <i :class="['pi', props.icon, resolveIconToneClass(props.iconColor)]" />
      <span :id="props.headingId">{{ props.title }}</span>
    </div>
    <p v-if="props.subtitle" class="ui-page-subtitle">{{ props.subtitle }}</p>
    <div v-if="$slots.default" class="ui-page-header-actions">
      <slot />
    </div>
  </div>
</template>
