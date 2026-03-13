<script setup lang="ts">
import { computed, ref } from 'vue';
import Button from 'primevue/button';

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

const iconToneClass = computed(() => {
  if (props.iconColor === 'success') return 'ui-color-success';
  if (props.iconColor === 'warning') return 'ui-color-warning';
  if (props.iconColor === 'error') return 'ui-color-error';
  return 'ui-color-info';
});

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
      :role="props.collapsible ? 'button' : undefined"
      :tabindex="props.collapsible ? 0 : undefined"
      :aria-expanded="props.collapsible ? isOpen : undefined"
      @click="toggleSection"
      @keydown.enter.prevent="toggleSection"
      @keydown.space.prevent="toggleSection"
    >
      <div class="ui-section-header-title">
        <i :class="['pi', props.icon, iconToneClass]" />
        <span>{{ props.title }}</span>
      </div>
      <div class="ui-section-header-actions" @click.stop @keydown.stop>
        <slot name="action" />
        <Button
          v-if="props.collapsible"
          :icon="isOpen ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
          severity="secondary"
          text
          size="small"
          class="ui-action-icon-btn"
          :aria-label="isOpen ? 'Collapse section' : 'Expand section'"
          @click.stop="toggleSection"
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
