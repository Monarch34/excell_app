import { onMounted, onUnmounted } from 'vue';

const BASE_POLL_INTERVAL_MS = 3000;
const MAX_POLL_INTERVAL_MS = 30000;

/**
 * Shared polling composable for config list auto-refresh.
 * Handles backoff, visibility/online listeners, and in-flight guards.
 *
 * @param fetchFn - Async function that fetches configs. Receives `silent` flag.
 *   Should return `true` on success, `false` on failure.
 */
export function useConfigPoller(
  fetchFn: (silent: boolean) => Promise<boolean>,
) {
  let pollingTimeout: number | null = null;
  let pollingActive = false;
  let refreshInFlight = false;
  let consecutiveFailures = 0;

  function clearPollingTimeout() {
    if (pollingTimeout !== null) {
      clearTimeout(pollingTimeout);
      pollingTimeout = null;
    }
  }

  function shouldPoll() {
    return !document.hidden && navigator.onLine;
  }

  async function poll(silent: boolean): Promise<void> {
    if (refreshInFlight) return;
    refreshInFlight = true;
    try {
      const success = await fetchFn(silent);
      consecutiveFailures = success ? 0 : consecutiveFailures + 1;
    } catch {
      consecutiveFailures++;
    } finally {
      refreshInFlight = false;
    }
  }

  function scheduleNextPoll() {
    clearPollingTimeout();
    if (!pollingActive) return;
    const interval = Math.min(
      BASE_POLL_INTERVAL_MS * Math.pow(2, consecutiveFailures),
      MAX_POLL_INTERVAL_MS,
    );
    pollingTimeout = window.setTimeout(async () => {
      if (!pollingActive) return;
      if (shouldPoll()) {
        await poll(true);
      }
      scheduleNextPoll();
    }, interval);
  }

  function handleVisibilityChange() {
    if (!pollingActive || document.hidden) return;
    void poll(true);
  }

  function handleOnline() {
    if (!pollingActive) return;
    void poll(true);
  }

  onMounted(() => {
    pollingActive = true;
    void poll(false);
    scheduleNextPoll();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('online', handleOnline);
  });

  onUnmounted(() => {
    pollingActive = false;
    clearPollingTimeout();
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    window.removeEventListener('online', handleOnline);
  });
}
