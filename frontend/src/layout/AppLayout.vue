<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

const menuItems = [
    { label: 'Dashboard', icon: 'pi pi-home', to: '/' },
    { label: 'Analysis', icon: 'pi pi-chart-line', to: '/analysis' },
    { label: 'Config', icon: 'pi pi-sliders-h', to: '/config' },
    { label: 'Settings', icon: 'pi pi-cog', to: '/settings' }
];

const isSidebarOpen = ref(true);
const isMobile = ref(false);
const pageTitleMap: Record<string, string> = {
    '/': 'Dashboard',
    '/analysis': 'Analysis',
    '/config': 'Config',
    '/settings': 'Settings',
};

const currentPageTitle = computed(() => {
    if (!route?.path) return 'Excell App';
    if (route.path.startsWith('/analysis')) return pageTitleMap['/analysis'];
    if (route.path.startsWith('/config')) return pageTitleMap['/config'];
    if (route.path.startsWith('/settings')) return pageTitleMap['/settings'];
    return pageTitleMap['/'];
});

const checkMobile = () => {
    const wasMobile = isMobile.value;
    isMobile.value = window.innerWidth <= 768;

    // Auto-close only when entering mobile; preserve user state otherwise.
    if (!wasMobile && isMobile.value) {
        isSidebarOpen.value = false;
    }
};

const toggleSidebar = () => {
    isSidebarOpen.value = !isSidebarOpen.value;
};

const handleNavClick = (path: string) => {
    router.push(path).catch((err: unknown) => {
        // Ignore duplicate navigation (user clicked same link)
        if (err instanceof Error && err.message.includes('Avoided redundant navigation')) return;
    });
    if (isMobile.value) {
        isSidebarOpen.value = false;
    }
};

const isLinkActive = (itemPath: string) => {
    const currentPath = route?.path || '';
    if (itemPath === '/') {
        return currentPath === '/';
    }
    return currentPath === itemPath || currentPath.startsWith(`${itemPath}/`);
};

onMounted(() => {
    checkMobile();
    window.addEventListener('resize', checkMobile);
});

onUnmounted(() => {
    window.removeEventListener('resize', checkMobile);
});
</script>

<template>
    <div class="app-layout" :class="{ 'app-layout--sidebar-collapsed': !isSidebarOpen && !isMobile }">
        <aside class="app-sidebar" :class="{ 'sidebar-collapsed': !isSidebarOpen && !isMobile, 'sidebar-mobile-open': isSidebarOpen && isMobile }">
            <div class="sidebar-header">
                <span v-if="isSidebarOpen || isMobile" class="logo-text">Excell App</span>
                <button class="menu-toggle" type="button" aria-label="Toggle sidebar" @click="toggleSidebar">
                    <i class="pi pi-bars"></i>
                </button>
            </div>

            <nav class="sidebar-nav">
                <ul>
                    <li v-for="item in menuItems" :key="item.to">
                        <button
                           type="button"
                           @click="handleNavClick(item.to)"
                           class="nav-link"
                           :class="{ 'nav-link-active': isLinkActive(item.to) }"
                           :title="!isSidebarOpen && !isMobile ? item.label : ''"
                        >
                            <i :class="item.icon"></i>
                            <span v-if="isSidebarOpen || isMobile" class="nav-link-label">{{ item.label }}</span>
                        </button>
                    </li>
                </ul>
            </nav>
        </aside>

        <button
          v-if="isMobile && isSidebarOpen"
          type="button"
          class="sidebar-overlay"
          aria-label="Close menu"
          tabindex="0"
          @click="toggleSidebar"
          @keydown.enter.prevent="toggleSidebar"
          @keydown.space.prevent="toggleSidebar"
        ></button>

        <div class="app-main">
            <header class="app-topbar">
                <button class="topbar-menu-btn" type="button" aria-label="Open menu" @click="toggleSidebar">
                    <i class="pi pi-bars"></i>
                </button>
                <h1 class="topbar-title">{{ currentPageTitle }}</h1>
            </header>

            <main class="app-content">
                <router-view v-slot="{ Component }">
                    <transition name="ui-fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </main>
        </div>
    </div>
</template>

