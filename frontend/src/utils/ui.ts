type IconTone = 'primary' | 'success' | 'warning' | 'error' | string;
type ColumnSource = 'derived' | 'original';

/** Maps a tone string to its CSS class. */
export function resolveIconToneClass(color: IconTone): string {
  if (color === 'success') return 'ui-color-success';
  if (color === 'warning') return 'ui-color-warning';
  if (color === 'error') return 'ui-color-error';
  return 'ui-color-info';
}

/** Returns a human-readable label for a column source. */
export function sourceLabel(source: ColumnSource): string {
  return source === 'derived' ? 'Derived' : 'Original';
}
