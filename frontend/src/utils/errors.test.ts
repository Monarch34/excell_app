import { describe, expect, it } from 'vitest';
import {
  toUserMessage,
  normalizeErrorDetail,
  ValidationError,
  ApiError,
  NetworkError,
  isAbortError,
} from '@/utils/errors';

describe('normalizeErrorDetail', () => {
  it('returns dataset expiry message for DATASET_EXPIRED code', () => {
    expect(normalizeErrorDetail('any', 422, 'DATASET_EXPIRED'))
      .toBe('Dataset session expired. Please re-upload your file.');
  });

  it('returns dataset expiry message for status 410', () => {
    expect(normalizeErrorDetail(undefined, 410))
      .toBe('Dataset session expired. Please re-upload your file.');
  });

  it('returns dataset expiry message when detail contains the keyword', () => {
    expect(normalizeErrorDetail('unknown or expired dataset id: abc'))
      .toBe('Dataset session expired. Please re-upload your file.');
  });

  it('returns detail or fallback for 404', () => {
    expect(normalizeErrorDetail('Item missing', 404)).toBe('Item missing');
    expect(normalizeErrorDetail(undefined, 404)).toBe('Resource not found');
  });

  it('returns detail or fallback for 403', () => {
    expect(normalizeErrorDetail('Nope', 403)).toBe('Nope');
    expect(normalizeErrorDetail(undefined, 403)).toBe('Permission denied');
  });

  it('returns safe generic message for 500', () => {
    expect(normalizeErrorDetail('stack trace leak', 500))
      .toBe('Server error. Please try again later.');
  });

  it('returns raw detail when present and no special status', () => {
    expect(normalizeErrorDetail('something happened', 422)).toBe('something happened');
  });

  it('returns null when nothing matches', () => {
    expect(normalizeErrorDetail(undefined, undefined, undefined)).toBeNull();
    expect(normalizeErrorDetail(undefined, 200)).toBeNull();
  });
});

describe('toUserMessage', () => {
  it('maps dataset expiry detail to re-upload guidance', () => {
    const error = {
      response: {
        status: 422,
        data: {
          detail: 'Unknown or expired dataset id: abc123',
        },
      },
    };
    expect(toUserMessage(error)).toBe('Dataset session expired. Please re-upload your file.');
  });

  it('maps DATASET_EXPIRED code to re-upload guidance', () => {
    const error = {
      response: {
        status: 410,
        data: {
          detail: 'dataset is no longer available',
          code: 'DATASET_EXPIRED',
        },
      },
    };
    expect(toUserMessage(error)).toBe('Dataset session expired. Please re-upload your file.');
  });

  it('maps 500 errors to a safe generic message', () => {
    const error = {
      response: {
        status: 500,
        data: {
          detail: 'stacktrace leaked',
        },
      },
    };
    expect(toUserMessage(error)).toBe('Server error. Please try again later.');
  });

  it('returns the string directly for plain string errors', () => {
    expect(toUserMessage('something broke')).toBe('something broke');
  });

  it('formats ValidationError with prefix', () => {
    expect(toUserMessage(new ValidationError('bad input')))
      .toBe('Validation failed: bad input');
  });

  it('maps ApiError status codes to user messages', () => {
    expect(toUserMessage(new ApiError('not here', 404))).toBe('Resource not found');
    expect(toUserMessage(new ApiError('denied', 403))).toBe('Permission denied');
    expect(toUserMessage(new ApiError('boom', 500))).toBe('Server error. Please try again later.');
    expect(toUserMessage(new ApiError('custom problem', 422))).toBe('custom problem');
  });

  it('returns network error message for NetworkError', () => {
    expect(toUserMessage(new NetworkError()))
      .toBe('Network error. Please check your connection.');
  });

  it('detects fetch keyword in generic Error as network error', () => {
    expect(toUserMessage(new Error('Failed to fetch')))
      .toBe('Network error. Please check your connection.');
  });

  it('detects timeout keyword in generic Error', () => {
    expect(toUserMessage(new Error('Request timeout after 30s')))
      .toBe('Request timed out. Please try again.');
  });

  it('passes through generic Error message', () => {
    expect(toUserMessage(new Error('something else')))
      .toBe('something else');
  });

  it('returns fallback for null, undefined, and non-object values', () => {
    expect(toUserMessage(null)).toBe('An unexpected error occurred');
    expect(toUserMessage(undefined)).toBe('An unexpected error occurred');
    expect(toUserMessage(42)).toBe('An unexpected error occurred');
  });
});

describe('isAbortError', () => {
  it('returns true for AbortError DOMException', () => {
    const e = new DOMException('Aborted', 'AbortError');
    expect(isAbortError(e)).toBe(true);
  });

  it('returns false for non-AbortError', () => {
    expect(isAbortError(new Error('not abort'))).toBe(false);
    expect(isAbortError(null)).toBe(false);
    expect(isAbortError('AbortError')).toBe(false);
  });
});
