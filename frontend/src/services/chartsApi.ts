import type { CalculateMetricsRequest, CalculateMetricsResponse } from '@/shared/types/api';
import { postData } from '@/services/httpClient';

export async function calculateMetrics(
  payload: CalculateMetricsRequest,
  signal?: AbortSignal,
): Promise<CalculateMetricsResponse> {
  return postData<CalculateMetricsResponse, CalculateMetricsRequest>('/charts/metrics', payload, { signal });
}
