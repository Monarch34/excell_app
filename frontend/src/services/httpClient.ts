import axios, { AxiosHeaders, type AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios';
import type { ApiError } from '@/types/api';
import { toUserMessage, normalizeErrorDetail } from '@/utils/errors';

function resolveApiBaseUrl(): string {
  if (!import.meta.env.DEV) return '/api/v3';
  const configured = import.meta.env.VITE_API_URL?.trim() || '';
  if (!configured) return '/api/v3';
  return configured.replace(/\/+$/, '');
}

const apiBaseUrl = resolveApiBaseUrl();

const httpClient: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30_000,
});

function createRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

httpClient.interceptors.request.use((config) => {
  const requestId = createRequestId();
  const headers = AxiosHeaders.from(config.headers || {});

  // Let the browser set multipart boundaries for FormData uploads.
  // For non-FormData payloads, default to JSON if no explicit header is provided.
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    headers.delete('Content-Type');
  } else if (!headers.get('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (!headers.get('X-Request-ID')) {
    headers.set('X-Request-ID', requestId);
  }
  config.headers = headers;
  return config;
});

export function extractErrorMessage(err: unknown): string {
  if (typeof err === 'string') return err;

  const axiosErr = err as AxiosError<ApiError>;
  const responseRequestId = axiosErr.response?.headers?.['x-request-id'] || axiosErr.response?.data?.request_id;
  const responseStatus = axiosErr.response?.status;
  if (axiosErr.response?.data) {
    const data = axiosErr.response.data;
    if (typeof data === 'string') return data;
    if (data.detail) {
      const normalized = normalizeErrorDetail(data.detail, responseStatus, data.code);
      if (normalized) {
        return responseRequestId ? `${normalized} (Request ID: ${String(responseRequestId)})` : normalized;
      }
    }
    const dataWithMessage = data as { message?: string };
    if (dataWithMessage.message) {
      const normalized = normalizeErrorDetail(dataWithMessage.message, responseStatus, data.code);
      if (normalized) {
        return responseRequestId
          ? `${normalized} (Request ID: ${String(responseRequestId)})`
          : normalized;
      }
      return responseRequestId
        ? `${dataWithMessage.message} (Request ID: ${String(responseRequestId)})`
        : dataWithMessage.message;
    }
    const normalizedFromStatus = normalizeErrorDetail(undefined, responseStatus, data.code);
    if (normalizedFromStatus) {
      return responseRequestId
        ? `${normalizedFromStatus} (Request ID: ${String(responseRequestId)})`
        : normalizedFromStatus;
    }
    return responseStatus === 500 ? 'Server error. Please try again later.' : 'Unknown server error';
  }

  if (responseRequestId) {
    const base = toUserMessage(axiosErr);
    return `${base} (Request ID: ${String(responseRequestId)})`;
  }
  return toUserMessage(axiosErr);
}

export async function getData<TResponse>(url: string, config?: AxiosRequestConfig): Promise<TResponse> {
  const response = await httpClient.get<TResponse>(url, config);
  return response.data;
}

export async function postData<TResponse, TPayload = unknown>(
  url: string,
  payload?: TPayload,
  config?: AxiosRequestConfig<TPayload>
): Promise<TResponse> {
  const response = await httpClient.post<TResponse>(url, payload, config);
  return response.data;
}

export async function deleteData<TResponse>(url: string, config?: AxiosRequestConfig): Promise<TResponse> {
  const response = await httpClient.delete<TResponse>(url, config);
  return response.data;
}

export default httpClient;
