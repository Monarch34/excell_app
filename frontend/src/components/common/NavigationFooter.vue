<script setup lang="ts">
import Button from 'primevue/button';

defineProps({
    backLabel: { type: String, default: 'Back' },
    primaryLabel: { type: String, default: 'Next' },
    primaryIcon: { type: String, default: 'pi pi-arrow-right' },
    primaryDisabled: { type: Boolean, default: false },
    primaryLoading: { type: Boolean, default: false }
});

const emit = defineEmits(['back', 'primary']);
</script>

<template>
    <div class="ui-nav-footer ui-nav-footer--wizard">
        <div class="ui-nav-footer-left">
            <Button
                :label="backLabel"
                icon="pi pi-arrow-left"
                class="p-button-secondary p-button-outlined ui-footer-back-btn"
                @click="emit('back')"
/>
            <slot name="left-actions"></slot>
        </div>
        <div class="ui-nav-footer-right">
            <slot name="right-actions"></slot>
            <Button
                :label="primaryLabel"
                :icon="primaryIcon"
                iconPos="right"
                :disabled="primaryDisabled"
                :loading="primaryLoading"
                class="p-button-primary ui-footer-primary-btn"
                @click="emit('primary')"
/>
        </div>
    </div>
</template>
