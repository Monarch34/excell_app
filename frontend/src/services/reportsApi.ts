import type { ExportRequest } from '@/types/api';
import { postData } from '@/services/httpClient';

export async function exportXlsx(payload: ExportRequest): Promise<Blob> {
  return postData<Blob, ExportRequest>('/reports/xlsx', payload, { responseType: 'blob', timeout: 120_000 });
}
