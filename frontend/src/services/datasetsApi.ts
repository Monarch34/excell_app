import type { DetectColumnsResponse, UploadResponse } from '@/shared/types/api';
import { postData } from '@/services/httpClient';

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return postData<UploadResponse, FormData>('/datasets/upload', formData, { timeout: 120_000 });
}

export async function detectColumns(
  data: Record<string, unknown>[],
  patterns?: Record<string, string[]>
): Promise<DetectColumnsResponse> {
  const response = await postData<
    { suggestions: DetectColumnsResponse },
    { data: Record<string, unknown>[]; patterns?: Record<string, string[]> }
  >('/datasets/detect-columns', {
    data,
    patterns,
  });
  return response.suggestions;
}
