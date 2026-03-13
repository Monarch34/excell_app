<script setup lang="ts">
import { ref } from 'vue';
import Button from 'primevue/button';
import { resolveIconToneClass } from '@/utils/ui';

type IconTone = 'primary' | 'success' | 'warning' | 'error';

const props = withDefaults(
  defineProps<{
    icon: string;
    title: string;
    iconColor?: IconTone;
    collapsible?: boolean;
    initiallyOpen?: boolean;
  }>(),
  {
    iconColor: 'primary',
    collapsible: false,
    initiallyOpen: true,
  }
);

const isOpen = ref(props.initiallyOpen);

function toggleSection() {
  if (!props.collapsible) return;
  isOpen.value = !isOpen.value;
}
</script>

<template>
  <section class="step-panel ui-step-section">
    <div
      class="ui-section-header"
      :class="{
        'ui-section-header--collapsible': props.collapsible,
        'ui-section-header--collapsed': props.collapsible && !isOpen,
      }"
      @click="toggleSection"
    >
      <div class="ui-section-header-title">
        <i :class="['pi', props.icon, resolveIconToneClass(props.iconColor)]" />
        <span>{{ props.title }}</span>
      </div>
      <div class="ui-section-header-actions" @click.stop>
        <slot name="action" />
        <Button
          v-if="props.collapsible"
          :icon="isOpen ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
          severity="secondary"
          text
          size="small"
          class="ui-action-icon-btn"
          :aria-label="isOpen ? `Collapse ${props.title}` : `Expand ${props.title}`"
          :aria-expanded="isOpen"
          @click.stop="toggleSection"
          @keydown.enter.prevent="toggleSection"
          @keydown.space.prevent="toggleSection"
        />
      </div>
    </div>
    <transition name="ui-chart-expand">
      <div v-if="!props.collapsible || isOpen">
        <slot />
      </div>
    </transition>
  </section>
</template>
