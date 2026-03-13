import { useToast } from 'primevue/usetoast';
import { getCurrentInstance } from 'vue';
import { extractErrorMessage } from '@/services/httpClient';

/**
 * Composable for standardized notifications across the app.
 * Wraps PrimeVue's useToast with consistent styling and error extraction.
 */
export function useNotify() {
    let toast: ReturnType<typeof useToast> | null = null;
    if (getCurrentInstance()) {
        toast = useToast();
    }

    const push = (payload: { severity: 'success' | 'error' | 'info' | 'warn'; summary: string; detail: string; life: number }) => {
        if (toast) {
            toast.add(payload);
            return;
        }

        // Fallback path for tests: keep behavior non-throwing.
        if (payload.severity === 'error') {
            console.error(`[notify:${payload.severity}] ${payload.summary}: ${payload.detail}`);
            return;
        }
        console.info(`[notify:${payload.severity}] ${payload.summary}: ${payload.detail}`);
    };

    const notifySuccess = (title: string, message: string = '') => {
        push({
            severity: 'success',
            summary: title,
            detail: message,
            life: 3000,
        });
    };

    const notifyError = (title: string, error: unknown) => {
        const message = typeof error === 'string' ? error : extractErrorMessage(error);

        // Check for specific error codes if available (future proofing)
        // const code = (error as any)?.response?.data?.code;

        push({
            severity: 'error',
            summary: title,
            detail: message,
            life: 5000, // Longer duration for errors
        });
    };

    const notifyInfo = (title: string, message: string) => {
        push({
            severity: 'info',
            summary: title,
            detail: message,
            life: 3000,
        });
    };

    const notifyWarn = (title: string, message: string) => {
        push({
            severity: 'warn',
            summary: title,
            detail: message,
            life: 4000,
        });
    };

    return {
        notifySuccess,
        notifyError,
        notifyInfo,
        notifyWarn
    };
}
