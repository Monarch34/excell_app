<script setup lang="ts">
import ConfigLibraryManager from '@/components/config/ConfigLibraryManager.vue';
</script>

<template>
  <div class="ui-page-shell ui-page-shell--wide step-shell fade-in">
    <div class="ui-page-header ui-settings-header">
      <div class="ui-settings-header-copy">
        <h1 class="ui-page-title ui-page-title--lg">Config Management</h1>
        <p class="ui-page-subtitle">
          Manage saved configurations, rename them, and inspect a detailed dependency map before applying.
        </p>
      </div>
    </div>
    <ConfigLibraryManager />
  </div>
</template>
