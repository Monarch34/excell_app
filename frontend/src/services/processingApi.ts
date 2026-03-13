import type { ProcessRequest, ProcessResponse, ProcessRunDataResponse } from '@/types/api';
import { getData, postData } from '@/services/httpClient';

export async function processData(payload: ProcessRequest, signal?: AbortSignal): Promise<ProcessResponse> {
  return postData<ProcessResponse, ProcessRequest>('/processing/run', payload, { signal });
}

export async function getProcessedRunData(runId: string, signal?: AbortSignal): Promise<ProcessRunDataResponse> {
  return getData<ProcessRunDataResponse>(`/processing/runs/${runId}/data`, { signal });
}
