<script setup lang="ts">
import { usePreferencesStore } from '@/stores/preferences';
import { storeToRefs } from 'pinia';
import InputSwitch from 'primevue/inputswitch';
import AppSurfacePanel from '@/shared/components/ui/AppSurfacePanel.vue';
import AppPageHeader from '@/shared/components/ui/AppPageHeader.vue';

const preferencesStore = usePreferencesStore();
const { isDarkMode } = storeToRefs(preferencesStore);
</script>

<template>
  <main class="ui-page-shell ui-page-shell--narrow step-shell fade-in" aria-labelledby="settings-heading">
    <AppPageHeader
      icon="pi-cog"
      title="Settings"
      subtitle="Project-wide display and behavior preferences."
      headingId="settings-heading"
    >
      <div class="ui-settings-sync-indicator">
        <i class="pi pi-sync" aria-hidden="true" />
        <span>Background polling active while online</span>
      </div>
    </AppPageHeader>

    <div class="ui-settings-layout">
      <AppSurfacePanel as="section" class="ui-settings-card">
        <header class="ui-settings-card-head">
          <div class="ui-settings-card-title">
            <i class="pi pi-palette" />
            <span>Appearance</span>
          </div>
          <p class="ui-settings-card-note">
            Choose the theme that fits your environment while keeping titles and controls consistent.
          </p>
        </header>

        <div class="ui-settings-list">
          <div class="ui-settings-item">
            <div class="ui-settings-item-copy">
              <label class="ui-settings-item-label" for="settings-dark-mode">Dark Mode</label>
              <p class="ui-settings-item-help">
                Current theme: {{ isDarkMode ? 'Dark' : 'Light' }}. Toggle to switch to {{ isDarkMode ? 'Light' : 'Dark' }}.
              </p>
            </div>
            <InputSwitch v-model="isDarkMode" input-id="settings-dark-mode" />
          </div>
        </div>
      </AppSurfacePanel>

      <AppSurfacePanel as="section" class="ui-settings-card" tone="neutral">
        <header class="ui-settings-card-head">
          <div class="ui-settings-card-title">
            <i class="pi pi-eye" />
            <span>Light Theme Readability</span>
          </div>
          <p class="ui-settings-card-note">Core text levels use darker values to keep contrast strong on light cards.</p>
        </header>
        <div class="ui-settings-contrast-grid">
          <div class="ui-settings-contrast-chip ui-settings-contrast-chip--title">
            <span class="ui-settings-contrast-chip-key">Title</span>
            <strong class="ui-settings-contrast-chip-value">Brand Blue</strong>
          </div>
          <div class="ui-settings-contrast-chip">
            <span class="ui-settings-contrast-chip-key">Body</span>
            <strong class="ui-settings-contrast-chip-value">Primary Text</strong>
          </div>
          <div class="ui-settings-contrast-chip">
            <span class="ui-settings-contrast-chip-key">Secondary</span>
            <strong class="ui-settings-contrast-chip-value ui-settings-contrast-chip-value--secondary">Supportive Text</strong>
          </div>
        </div>
      </AppSurfacePanel>

      <AppSurfacePanel as="section" class="ui-settings-card ui-settings-card--full">
        <header class="ui-settings-card-head">
          <div class="ui-settings-card-title">
            <i class="pi pi-sliders-h" />
            <span>Current Behavior</span>
          </div>
        </header>
        <ul class="ui-settings-status-list">
          <li class="ui-settings-status-item">
            <i class="pi pi-check-circle ui-color-info" />
            <span>Background polling refreshes configuration lists automatically.</span>
          </li>
          <li class="ui-settings-status-item">
            <i class="pi pi-check-circle ui-color-info" />
            <span>Page and section titles use the shared blue title token for consistency.</span>
          </li>
          <li class="ui-settings-status-item">
            <i class="pi pi-check-circle ui-color-info" />
            <span>Light mode text tones are mapped to primary and secondary text tokens for readability.</span>
          </li>
        </ul>
      </AppSurfacePanel>
    </div>
  </main>
</template>
