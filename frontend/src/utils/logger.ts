/**
 * Structured logging utility with breadcrumb tracking.
 * Usage: const log = createLogger('MyComponent'); log.error('something failed', err);
 */

import { logError } from '@/utils/errors';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  context: string;
  message: string;
  timestamp: number;
}

const MAX_BREADCRUMBS = 50;
const breadcrumbs: LogEntry[] = [];
const isProd = import.meta.env.PROD;

function record(level: LogLevel, context: string, message: string) {
  breadcrumbs.push({ level, context, message, timestamp: Date.now() });
  if (breadcrumbs.length > MAX_BREADCRUMBS) breadcrumbs.shift();
}

export function createLogger(context: string) {
  return {
    debug(msg: string, ...args: unknown[]) {
      if (!isProd) {
        record('debug', context, msg);
        console.debug(`[${context}]`, msg, ...args);
      }
    },
    info(msg: string, ...args: unknown[]) {
      if (!isProd) {
        record('info', context, msg);
        console.info(`[${context}]`, msg, ...args);
      }
    },
    warn(msg: string, ...args: unknown[]) {
      record('warn', context, msg);
      console.warn(`[${context}]`, msg, ...args);
    },
    error(msg: string, error?: unknown) {
      record('error', context, msg);
      logError(error ?? msg, context);
    },
  };
}

/**
 * Returns a readonly snapshot of recent log breadcrumbs (newest last).
 * Useful for attaching to error reports.
 */
export function getRecentBreadcrumbs(): ReadonlyArray<LogEntry> {
  return breadcrumbs;
}
