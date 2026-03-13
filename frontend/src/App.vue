<script setup lang="ts">
import { onMounted, onUnmounted, watchEffect } from 'vue';
import { useToast } from 'primevue/usetoast';
import AppLayout from './layout/AppLayout.vue';
import Toast from 'primevue/toast';
import ConfirmDialog from 'primevue/confirmdialog';
import { usePreferencesStore } from '@/stores/preferences';
import { storeToRefs } from 'pinia';

const preferencesStore = usePreferencesStore();
const { isDarkMode } = storeToRefs(preferencesStore);
const toast = useToast();

// Sync theme class with document root for CSS variable inheritance
watchEffect(() => {
    if (isDarkMode.value) {
        document.documentElement.classList.add('app-dark');
    } else {
        document.documentElement.classList.remove('app-dark');
    }
});

function handleUnhandledError(e: Event) {
    const detail = (e as CustomEvent<{ message: string }>).detail;
    toast.add({
        severity: 'error',
        summary: 'Unexpected Error',
        detail: detail?.message || 'An unexpected error occurred',
        life: 5000,
    });
}

onMounted(() => {
    window.addEventListener('app:unhandled-error', handleUnhandledError);
});

onUnmounted(() => {
    window.removeEventListener('app:unhandled-error', handleUnhandledError);
});
</script>

<template>
  <div>
    <AppLayout />
    <Toast position="top-right" />
    <ConfirmDialog />
  </div>
</template>
