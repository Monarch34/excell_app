/**
 * Shared color normalization utilities.
 */

function toHex(channel: number): string {
  return channel.toString(16).padStart(2, '0').toUpperCase();
}

/** Strips `#`, validates 6-char hex, returns `#AABBCC` or `null`. */
export function normalizeHexColor(value: string | null | undefined): string | null {
  if (!value) return null;
  const cleaned = String(value).trim().replace(/^#/, '');
  if (!/^[0-9a-fA-F]{6}$/.test(cleaned)) return null;
  return `#${cleaned.toUpperCase()}`;
}

/** Handles `#RGB`, `#RRGGBB`, `rgb()`, `rgba()` → `#RRGGBB[AA]` or `null`. */
export function normalizeColorToHex(color: string | null | undefined): string | null {
  if (!color) return null;
  const value = color.trim();
  if (!value) return null;

  const hexMatch = value.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hexMatch) {
    const hex = hexMatch[1];
    if (hex.length === 3) {
      return `#${hex
        .split('')
        .map((part) => `${part}${part}`)
        .join('')
        .toUpperCase()}`;
    }
    return `#${hex.toUpperCase()}`;
  }

  if (/^rgba?\(/i.test(value)) {
    const channels = value.match(/[\d.]+/g);
    if (!channels || channels.length < 3) return null;
    const [r, g, b] = channels.slice(0, 3).map((channel) => {
      const numeric = Number(channel);
      if (Number.isNaN(numeric)) return 0;
      return Math.max(0, Math.min(255, Math.round(numeric)));
    });
    const base = `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    if (channels.length < 4) return base;

    const alphaNumber = Number(channels[3]);
    if (Number.isNaN(alphaNumber)) return base;
    const alpha = Math.max(0, Math.min(1, alphaNumber));
    if (alpha >= 1) return base;
    return `${base}${toHex(Math.round(alpha * 255))}`;
  }

  return null;
}

/** For form color inputs: strips non-hex chars, returns `#AABBCC`, `null` (empty), or `undefined` (incomplete). */
export function normalizeHexColorInput(input: string | undefined): string | null | undefined {
  if (!input) return null;
  const cleaned = input.replace(/[^0-9a-fA-F]/g, '').slice(0, 6);
  if (!cleaned) return null;
  if (cleaned.length !== 6) return undefined;
  return `#${cleaned.toUpperCase()}`;
}
