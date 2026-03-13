/**
 * Typed error handling utilities for the application
 */

export class AppError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', context);
    this.name = 'ValidationError';
  }
}

export class ApiError extends AppError {
  constructor(
    message: string,
    public readonly statusCode?: number,
    context?: Record<string, unknown>
  ) {
    super(message, 'API_ERROR', context);
    this.name = 'ApiError';
  }
}

export class NetworkError extends AppError {
  constructor(message: string = 'Network request failed') {
    super(message, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

/**
 * Normalizes a server error response into a user-friendly message.
 * Single source of truth for all error message normalization.
 */
export function normalizeErrorDetail(detail?: string, status?: number, code?: string): string | null {
  const lowered = detail?.toLowerCase() || '';

  if (
    code === 'DATASET_EXPIRED'
    || status === 410
    || lowered.includes('unknown or expired dataset id')
  ) {
    return 'Dataset session expired. Please re-upload your file.';
  }

  if (status === 404) return detail || 'Resource not found';
  if (status === 403) return detail || 'Permission denied';
  if (status === 500) {
    return 'Server error. Please try again later.';
  }
  if (detail) return detail;
  return null;
}

/**
 * Converts any error type to a user-friendly message
 */
export function toUserMessage(error: unknown): string {
  if (typeof error === 'string') return error;

  if (error && typeof error === 'object') {
    const maybeResponse = (
      error as {
        response?: {
          status?: number;
          data?: {
            detail?: unknown;
            message?: unknown;
            code?: unknown;
          };
        };
      }
    ).response;

    const status = maybeResponse?.status;
    const code = typeof maybeResponse?.data?.code === 'string' ? maybeResponse.data.code : undefined;
    const detail =
      typeof maybeResponse?.data?.detail === 'string'
        ? maybeResponse.data.detail
        : typeof maybeResponse?.data?.message === 'string'
          ? maybeResponse.data.message
          : undefined;

    const normalized = normalizeErrorDetail(detail, status, code);
    if (normalized) return normalized;
  }

  if (error instanceof ValidationError) {
    return `Validation failed: ${error.message}`;
  }

  if (error instanceof ApiError) {
    if (error.statusCode === 404) return 'Resource not found';
    if (error.statusCode === 403) return 'Permission denied';
    if (error.statusCode === 500) return 'Server error. Please try again later.';
    return error.message;
  }

  if (error instanceof NetworkError) {
    return 'Network error. Please check your connection.';
  }

  if (error instanceof Error) {
    if (error.message.includes('fetch')) return 'Network error. Please check your connection.';
    if (error.message.includes('timeout')) return 'Request timed out. Please try again.';
    return error.message;
  }

  return 'An unexpected error occurred';
}

/**
 * Extracts error details from API response
 */
export async function extractApiError(response: Response): Promise<ApiError> {
  let message = 'Request failed';
  let code: string | undefined;

  try {
    const data = await response.json();
    message = data.detail || data.message || message;
    code = data.code;
  } catch {
    message = response.statusText || message;
  }

  return new ApiError(message, response.status, { code });
}

/**
 * Checks if an error is an AbortError (from AbortController or fetch cancellation).
 */
export function isAbortError(e: unknown): boolean {
  return (e instanceof DOMException || e instanceof Error) && e.name === 'AbortError';
}

/**
 * Logs error with optional context prefix
 */
export function logError(error: unknown, context?: string): void {
  const prefix = context ? `[${context}]` : '[Error]';
  if (error instanceof Error) {
    console.error(prefix, error.message, error);
  } else {
    console.error(prefix, error);
  }
}
