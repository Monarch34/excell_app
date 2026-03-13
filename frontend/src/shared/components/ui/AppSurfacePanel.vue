<script setup lang="ts">
withDefaults(defineProps<{
  as?: 'div' | 'section';
  compact?: boolean;
  muted?: boolean;
  interactive?: boolean;
  tone?: 'default' | 'muted' | 'neutral' | 'chart';
}>(), {
  as: 'div',
  compact: false,
  muted: false,
  interactive: false,
  tone: 'default',
});
</script>

<template>
  <component
    :is="as"
    class="ui-surface-block"
    :class="{
      'ui-surface-block--compact': compact,
      'ui-surface-block--muted': muted || tone === 'muted',
      'ui-surface-block--neutral': tone === 'neutral',
      'ui-surface-block--chart': tone === 'chart',
      'ui-surface-block--interactive': interactive,
    }"
  >
    <slot />
  </component>
</template>
