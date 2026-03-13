<script setup lang="ts">
import Dialog from 'primevue/dialog';
import type { CSSProperties } from 'vue';

withDefaults(defineProps<{
  visible: boolean;
  header?: string;
  modal?: boolean;
  maximizable?: boolean;
  closable?: boolean;
  style?: CSSProperties;
  contentStyle?: CSSProperties;
  breakpoints?: Record<string, string>;
}>(), {
  modal: true,
  maximizable: false,
  closable: true,
});

const emit = defineEmits<{
  'update:visible': [value: boolean];
}>();
</script>

<template>
  <Dialog
    class="ui-dialog-surface"
    :visible="visible"
    :header="header"
    :modal="modal"
    :maximizable="maximizable"
    :closable="closable"
    :style="style"
    :contentStyle="contentStyle"
    :breakpoints="breakpoints"
    @update:visible="(value) => emit('update:visible', value)"
  >
    <slot />
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </Dialog>
</template>
