/**
 * Composable for confirmation dialogs using PrimeVue's ConfirmDialog
 */

import { useConfirm } from 'primevue/useconfirm';

export function useConfirmDialog() {
  const confirm = useConfirm();

  function confirmDelete(
    itemName: string,
    onConfirm: () => void | Promise<void>
  ): void {
    confirm.require({
      message: `Are you sure you want to delete "${itemName}"? This action cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Delete',
      rejectLabel: 'Cancel',
      acceptClass: 'p-button-danger',
      accept: async () => {
        await onConfirm();
      },
    });
  }

  function confirmReset(
    message: string,
    onConfirm: () => void | Promise<void>
  ): void {
    confirm.require({
      message: message || 'This will reset all your current work. Continue?',
      header: 'Confirm Reset',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Reset',
      rejectLabel: 'Cancel',
      acceptClass: 'p-button-warning',
      accept: async () => {
        await onConfirm();
      },
    });
  }

  function confirmAction(
    options: {
      message: string;
      header: string;
      icon?: string;
      acceptLabel?: string;
      rejectLabel?: string;
      acceptClass?: string;
    },
    onConfirm: () => void | Promise<void>
  ): void {
    confirm.require({
      message: options.message,
      header: options.header,
      icon: options.icon || 'pi pi-exclamation-triangle',
      acceptLabel: options.acceptLabel || 'Confirm',
      rejectLabel: options.rejectLabel || 'Cancel',
      acceptClass: options.acceptClass,
      accept: async () => {
        await onConfirm();
      },
    });
  }

  return { confirmDelete, confirmReset, confirmAction };
}
