<script setup lang="ts">
import { ref } from 'vue';
import OrganizationChart from 'primevue/organizationchart';
import type { FormulaTreeEntry } from '@/domain/configDependency';

defineProps<{
  formulaTrees: FormulaTreeEntry[];
}>();

/* ── Open/close individual formula trees ────────────────────────────────────── */
const openTrees = ref<Set<string>>(new Set());

function toggleTree(id: string) {
  if (openTrees.value.has(id)) {
    openTrees.value.delete(id);
  } else {
    openTrees.value.add(id);
  }
  // Force reactivity
  openTrees.value = new Set(openTrees.value);
}
</script>

<template>
  <div class="cfg-section-body">
    <div class="cfg-formula-list">
      <div v-for="(item, index) in formulaTrees" :key="item.formula.id" class="cfg-formula-card">
        <!-- Formula Header (collapsible) -->
        <button
          type="button"
          class="cfg-formula-header"
          :aria-expanded="openTrees.has(item.formula.id)"
          :aria-controls="`cfg-formula-body-${item.formula.id}`"
          @click="toggleTree(item.formula.id)"
        >
          <div class="cfg-formula-title-wrap">
            <span class="cfg-formula-idx">{{ index + 1 }}</span>
            <span class="cfg-formula-name">{{ item.formula.name }}</span>
            <span class="cfg-formula-type-chip">{{ item.formula.type === 'parameter' ? 'Scalar' : 'Column' }}</span>
          </div>
          <div class="cfg-formula-header-right">
            <span v-if="item.derived?.unit" class="cfg-formula-unit">{{ item.derived.unit }}</span>
            <i class="pi cfg-formula-toggle-icon" :class="openTrees.has(item.formula.id) ? 'pi-chevron-up' : 'pi-chevron-down'" aria-hidden="true"></i>
          </div>
        </button>

        <!-- Formula Detail + Tree (expandable) -->
        <transition name="cfg-expand">
          <div v-if="openTrees.has(item.formula.id)" :id="`cfg-formula-body-${item.formula.id}`" class="cfg-formula-body" role="region">
            <!-- Description -->
            <p v-if="item.derived?.description" class="cfg-formula-desc">{{ item.derived.description }}</p>

            <!-- Formula expression -->
            <div class="cfg-formula-expr">
              <span class="cfg-formula-expr-label">ƒ</span>
              <code class="cfg-formula-expr-code">{{ item.formula.formula }}</code>
            </div>

            <!-- Dependencies list -->
            <div v-if="item.formula.dependencies.length" class="cfg-formula-deps">
              <span class="cfg-formula-deps-label">Dependencies:</span>
              <span v-for="dep in item.formula.dependencies" :key="dep.name" class="cfg-dep-chip" :class="'cfg-dep-chip--' + dep.kind">{{ dep.name }}</span>
            </div>

            <!-- Tree Visualization -->
            <div class="cfg-tree-wrap">
              <OrganizationChart :value="item.treeData" class="cfg-org-chart">
                <template #default="{ node }">
                  <template v-if="node">
                    <div class="cfg-tree-node-card" :class="['cfg-tree-node-card--' + node.type, node.data?.dataType ? 'cfg-tree-node-card--' + node.data.dataType : '']">
                        <div class="cfg-tree-node-header">
                          <i v-if="node.type === 'formula'" class="pi pi-bolt"></i>
                          <i v-else-if="node.type === 'input' && node.data?.icon" :class="['pi', node.data.icon]"></i>
                          <i v-else-if="node.type === 'cycle'" class="pi pi-exclamation-triangle"></i>
                          <span class="cfg-tree-node-title">{{ node.label }}</span>
                          <span v-if="node.data?.dataType" class="cfg-tree-node-type-badge">{{ node.data.dataType }}</span>
                        </div>
                        <div v-if="node.data?.formula || node.data?.details" class="cfg-tree-node-content">
                            <div v-if="node.data?.formula" class="cfg-tree-node-meta">
                              <span class="cfg-tree-node-meta-label">ƒ</span>
                              <span class="cfg-tree-node-meta-value cfg-tree-node-mono">{{ node.data.formula }}</span>
                            </div>
                            <div v-if="node.data?.details" class="cfg-tree-node-meta">
                              <span class="cfg-tree-node-meta-label">Type</span>
                              <span class="cfg-tree-node-meta-value">{{ node.data.details }}</span>
                            </div>
                        </div>
                    </div>
                  </template>
                </template>
              </OrganizationChart>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>


