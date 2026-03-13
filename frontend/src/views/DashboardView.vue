<script setup lang="ts">
import { useRouter } from 'vue-router';
import AppSurfacePanel from '@/components/ui/AppSurfacePanel.vue';

const router = useRouter();

const startAnalysis = () => {
    router.push('/analysis');
};
</script>

<template>
    <div class="ui-page-shell ui-page-shell--wide step-shell">
        <div class="ui-page-hero">
            <div class="ui-page-logo">
                <i class="pi pi-chart-bar"></i>
            </div>
            <h1 class="ui-page-title ui-page-title--xl">Excell App</h1>
            <p class="ui-page-subtitle ui-page-subtitle--lg">Mechanical Test Data Analyzer</p>
        </div>

        <div class="ui-feature-grid">
            <div class="ui-feature-cell">
                <AppSurfacePanel class="ui-feature-card ui-feature-card--primary" interactive @click="startAnalysis">
                    <div class="ui-feature-icon">
                        <i class="pi pi-plus"></i>
                    </div>
                    <h2 class="ui-feature-title">New Analysis</h2>
                    <p class="ui-feature-text">
                        Start a new analysis from Excel/CSV data. Upload, configure, and generate reports.
                    </p>
                </AppSurfacePanel>
            </div>

            <div class="ui-feature-cell">
                <AppSurfacePanel class="ui-feature-card ui-feature-card--disabled" muted>
                    <div class="ui-feature-icon ui-feature-icon--muted">
                        <i class="pi pi-history"></i>
                    </div>
                    <h2 class="ui-feature-title">Recent History</h2>
                    <p class="ui-feature-text">View past analysis reports. Coming soon.</p>
                </AppSurfacePanel>
            </div>

            <div class="ui-feature-cell">
                <AppSurfacePanel class="ui-feature-card ui-feature-card--disabled" muted>
                    <div class="ui-feature-icon ui-feature-icon--muted">
                        <i class="pi pi-cog"></i>
                    </div>
                    <h2 class="ui-feature-title">Templates</h2>
                    <p class="ui-feature-text">Manage report templates. Coming soon.</p>
                </AppSurfacePanel>
            </div>
        </div>
    </div>
</template>
