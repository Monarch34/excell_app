<script setup lang="ts">
import { ref } from 'vue';
import Chip from 'primevue/chip';
import type { FormulaToken } from '@/types/domain';

const props = defineProps<{
  tokens: FormulaToken[];
}>();

const emit = defineEmits<{
  'update:tokens': [tokens: FormulaToken[]];
}>();

const containerRef = ref<HTMLDivElement | null>(null);

function removeToken(index: number) {
  const updated = [...props.tokens];
  updated.splice(index, 1);
  emit('update:tokens', updated);
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Backspace' && props.tokens.length > 0) {
    event.preventDefault();
    removeToken(props.tokens.length - 1);
  }
}

function focusContainer() {
  containerRef.value?.focus();
}
</script>

<template>
  <div
    ref="containerRef"
    class="ui-token-editor"
    tabindex="0"
    role="textbox"
    aria-multiline="true"
    @keydown="handleKeydown"
    @click="focusContainer"
  >
    <template v-if="tokens.length > 0">
      <template v-for="(token, index) in tokens" :key="index">
        <Chip
          v-if="token.type === 'reference'"
          :label="token.value"
          removable
          class="ui-token-chip ui-token-chip--reference"
          @remove="removeToken(index)"
        />
        <Chip
          v-else
          :label="token.value"
          removable
          class="ui-token-chip ui-token-chip--operator"
          @remove="removeToken(index)"
        />
      </template>
    </template>
    <span v-else class="ui-token-placeholder">
      Click columns/parameters above and operators below to build formula
    </span>
  </div>
</template>
