import { describe, expect, it } from 'vitest';
import { toUserMessage } from '@/utils/errors';

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
});
