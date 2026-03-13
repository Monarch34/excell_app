/**
 * Lightweight retry utility for transient network failures.
 * Retries on network errors and 5xx responses; skips 4xx and AbortError.
 */

import { isAbortError } from '@/utils/errors';

export interface RetryOptions {
  /** Maximum number of attempts (default: 3) */
  maxAttempts?: number;
  /** Base delay in milliseconds, multiplied by attempt number (default: 1000) */
  baseDelayMs?: number;
  /** Custom predicate to decide whether to retry (default: retry on network/5xx) */
  shouldRetry?: (error: unknown, attempt: number) => boolean;
}

function defaultShouldRetry(error: unknown): boolean {
  if (isAbortError(error)) return false;
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status !== undefined && status < 500) return false;
  return true;
}

export async function withRetry<T>(
  fn: (signal?: AbortSignal) => Promise<T>,
  options?: RetryOptions,
  signal?: AbortSignal,
): Promise<T> {
  const maxAttempts = options?.maxAttempts ?? 3;
  const baseDelay = options?.baseDelayMs ?? 1000;
  const shouldRetry = options?.shouldRetry ?? defaultShouldRetry;

  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn(signal);
    } catch (e) {
      lastError = e;
      if (signal?.aborted) throw e;
      if (attempt === maxAttempts || !shouldRetry(e, attempt)) throw e;
      await new Promise((r) => setTimeout(r, baseDelay * attempt));
    }
  }
  throw lastError;
}
