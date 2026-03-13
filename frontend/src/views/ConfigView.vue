<script setup lang="ts">
import ConfigLibraryManager from '@/features/config/ConfigLibraryManager.vue';
import AppPageHeader from '@/shared/components/ui/AppPageHeader.vue';
</script>

<template>
  <main class="ui-page-shell ui-page-shell--wide step-shell fade-in" aria-labelledby="config-heading">
    <AppPageHeader
      icon="pi-sliders-h"
      title="Config Management"
      subtitle="Manage saved configurations, rename them, and inspect a detailed dependency map before applying."
      headingId="config-heading"
    />
    <ConfigLibraryManager />
  </main>
</template>
