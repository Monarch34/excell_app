<script setup lang="ts">
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';

withDefaults(defineProps<{
  isLoading?: boolean;
  error?: string | null;
  minHeight?: string;
}>(), {
  isLoading: false,
  error: null,
  minHeight: '60px',
});
</script>

<template>
  <div class="ui-status-strip" :style="{ minHeight }">
    <Transition name="ui-status-fade" mode="out-in">
      <AppSurfacePanel
        v-if="isLoading"
        compact
        class="ui-status-strip-panel ui-status-strip-panel--centered"
        key="loading"
      >
        <slot name="loading" />
      </AppSurfacePanel>

      <AppSurfacePanel
        v-else-if="error"
        compact
        class="ui-status-strip-panel ui-status-strip-error ui-status-strip-panel--centered"
        key="error"
      >
        <slot name="error" :error="error" />
      </AppSurfacePanel>

      <div v-else class="ui-status-strip-idle" key="idle">
        <slot name="idle" />
      </div>
    </Transition>
  </div>
</template>
