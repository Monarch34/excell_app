import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useConfirm } from 'primevue/useconfirm';

export function useDirtyState() {
  const isDirtyRef = ref(false);
  const confirm = useConfirm();

  function markDirty() {
    isDirtyRef.value = true;
  }

  function markClean() {
    isDirtyRef.value = false;
  }

  function beforeUnloadHandler(e: BeforeUnloadEvent) {
    if (isDirtyRef.value) {
      e.preventDefault();
      e.returnValue = '';
      return '';
    }
  }

  watch(isDirtyRef, (dirty) => {
    if (dirty) {
      window.addEventListener('beforeunload', beforeUnloadHandler);
    } else {
      window.removeEventListener('beforeunload', beforeUnloadHandler);
    }
  });

  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', beforeUnloadHandler);
  });

  onBeforeRouteLeave((to, from, next) => {
    if (!isDirtyRef.value) {
      next();
      return;
    }

    confirm.require({
      message: 'You have unsaved changes. Are you sure you want to leave?',
      header: 'Unsaved Changes',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Leave',
      rejectLabel: 'Stay',
      acceptClass: 'p-button-warning',
      accept: () => {
        markClean();
        next();
      },
      reject: () => {
        next(false);
      },
    });
  });

  return {
    isDirty: computed(() => isDirtyRef.value),
    markDirty,
    markClean,
  };
}
