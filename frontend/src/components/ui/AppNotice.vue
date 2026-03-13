<script setup lang="ts">
withDefaults(defineProps<{
  severity?: 'info' | 'success' | 'warn' | 'error';
  appearance?: 'solid' | 'ghost';
}>(), {
  severity: 'info',
  appearance: 'solid',
});
</script>

<template>
  <div class="ui-notice" :class="[`ui-notice--${severity}`, `ui-notice--${appearance}`]">
    <slot />
  </div>
</template>
