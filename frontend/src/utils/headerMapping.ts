import type { AnalysisConfig } from '@/shared/types/domain';

/**
 * Build API header mapping payload from the currently loaded config metadata.
 */
export function buildHeaderMappingFromConfig(
  config: AnalysisConfig | null | undefined
): Record<string, string> {
  const mapping: Record<string, string> = {};
  const metadata = config?.columnMetadata;
  if (!metadata) return mapping;

  for (const [columnKey, meta] of Object.entries(metadata)) {
    if (meta.label) mapping[columnKey] = meta.label;
  }
  return mapping;
}
