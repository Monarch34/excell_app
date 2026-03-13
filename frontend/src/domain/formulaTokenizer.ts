import type { FormulaToken } from '@/types/domain';

/**
 * Parse a bracket-syntax formula string into an array of FormulaTokens.
 *
 * References are `[Column Name]` segments.
 * REF([Column Name]) is treated as a special raw reference token.
 * Everything between references is treated as operator tokens.
 */
export function parseFormulaToTokens(formula: string): FormulaToken[] {
  if (!formula.trim()) return [];

  const tokens: FormulaToken[] = [];
  // Match either REF([Column]) or [Column]
  const regex = /REF\(\[([^\]]+)\]\)|\[([^\]]+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null = regex.exec(formula);

  while (match !== null) {
    // Operator text between last match and this reference
    const between = formula.substring(lastIndex, match.index).trim();
    if (between) {
      tokens.push({ type: 'operator', value: between });
    }

    // Check if it's a REF([Column]) match or regular [Column] match
    if (match[1] !== undefined) {
      // REF([Column]) - store as raw token
      tokens.push({ type: 'reference', value: `REF([${match[1]}])`, raw: true });
    } else {
      // Regular [Column]
      tokens.push({ type: 'reference', value: match[2] });
    }
    lastIndex = regex.lastIndex;
    match = regex.exec(formula);
  }

  // Trailing operator text
  const trailing = formula.substring(lastIndex).trim();
  if (trailing) {
    tokens.push({ type: 'operator', value: trailing });
  }

  return tokens;
}

/**
 * Serialize an array of FormulaTokens back to a bracket-syntax formula string.
 * Tokens with raw=true are output as-is (for REF([Column]) syntax).
 */
export function serializeTokensToFormula(tokens: FormulaToken[]): string {
  return tokens
    .map((t) => {
      if (t.type === 'reference') {
        // If raw flag is set, output value as-is (e.g., REF([Column]))
        return t.raw ? t.value : `[${t.value}]`;
      }
      return t.value;
    })
    .join(' ');
}
