import type { AnalysisConfig } from '@/shared/types/domain';
import { deleteData, getData, postData } from '@/services/httpClient';

export interface SavedConfigSummary {
  id: number;
  name: string;
  domain: string;
  created_at: string;
  updated_at: string;
}

export interface SavedConfigDetail extends SavedConfigSummary {
  config_data: AnalysisConfig;
}

export interface SaveConfigResponse {
  status: 'success';
  id: number;
}

export interface DeleteConfigResponse {
  status: 'success';
}

export interface AppLimits {
  max_derived_columns: number;
  max_file_size_mb: number;
}

export async function fetchLimits(): Promise<AppLimits> {
  return getData<AppLimits>('/configs/limits');
}

export async function saveConfig(
  name: string,
  domain: string | null | undefined,
  config: AnalysisConfig
): Promise<SaveConfigResponse> {
  const normalizedDomain = typeof domain === 'string' ? domain : '';
  return postData<SaveConfigResponse, { name: string; domain: string; config_data: AnalysisConfig }>('/configs', {
    name,
    domain: normalizedDomain,
    config_data: config,
  });
}

export async function fetchConfigs(domain?: string): Promise<SavedConfigSummary[]> {
  const params = domain ? { domain } : undefined;
  return getData<SavedConfigSummary[]>('/configs', { params });
}

export async function fetchConfig(id: number): Promise<SavedConfigDetail> {
  return getData<SavedConfigDetail>(`/configs/${id}`);
}

export async function deleteConfig(id: number): Promise<DeleteConfigResponse> {
  return deleteData<DeleteConfigResponse>(`/configs/${id}`);
}
