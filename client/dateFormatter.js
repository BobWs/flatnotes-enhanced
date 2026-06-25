/**
 * dateFormatter.js — Memoised, locale-aware date formatting.
 *
 * Reads dateLocale and dateStyle from the global Pinia store so every call
 * site just writes:
 *   formatDate(note.lastModified)          // timestamp seconds → date only
 *   formatDate(note.lastModified, true)    // timestamp seconds → date + time
 *   formatDateIso('2026-03-16T14:00:00')  // ISO string → date + time
 *
 * Supported styles (map to Intl.DateTimeFormat options):
 *   short  → 02/06/2026          (numeric parts, most compact)
 *   medium → 2 Jun 2026          (abbreviated month — DEFAULT)
 *   long   → 2 June 2026         (full month name)
 *
 * Time format (12h vs 24h) is intentionally NOT forced — Intl infers the
 * convention from the locale, which is the correct production-grade approach.
 *
 * The formatter cache avoids recreating Intl objects on every render; it is
 * keyed by locale|style|includeTime so at most a handful of objects live in
 * memory at once.
 */

import { useGlobalStore } from "./globalStore.js";

// ── Intl options per style ───────────────────────────────────────────────────

const DATE_OPTIONS = {
  short: {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  },
  medium: {
    year: "numeric",
    month: "short",
    day: "numeric",
  },
  long: {
    year: "numeric",
    month: "long",
    day: "numeric",
  },
};

const TIME_OPTIONS = {
  hour: "2-digit",
  minute: "2-digit",
  // hour12 is intentionally omitted: Intl derives it from the locale.
  // This is the correct production approach — e.g. 'nl' → 24h, 'en-US' → 12h.
};

// ── Formatter cache ──────────────────────────────────────────────────────────

const _cache = new Map();

function _getFormatter(locale, style, includeTime) {
  const key = `${locale}|${style}|${includeTime}`;
  if (!_cache.has(key)) {
    // 'system' → pass undefined, letting Intl use the browser/OS default
    const resolvedLocale = locale === "system" ? undefined : locale;
    const opts = {
      ...(DATE_OPTIONS[style] ?? DATE_OPTIONS.medium),
      ...(includeTime ? TIME_OPTIONS : {}),
    };
    try {
      _cache.set(key, new Intl.DateTimeFormat(resolvedLocale, opts));
    } catch {
      // Fallback: if an invalid locale was somehow stored, use system default
      _cache.set(key, new Intl.DateTimeFormat(undefined, opts));
    }
  }
  return _cache.get(key);
}

// Clear the cache when preferences change (called from SettingsPrefs.vue on save)
export function clearDateFormatterCache() {
  _cache.clear();
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Format a Unix timestamp (seconds) using the user's locale/style preferences.
 *
 * @param {number} timestampSeconds  - Unix timestamp in seconds (from the API)
 * @param {boolean} includeTime      - Whether to append HH:MM
 * @returns {string}
 */
export function formatDate(timestampSeconds, includeTime = false) {
  if (timestampSeconds == null) return "";
  try {
    const store = useGlobalStore();
    const locale = store.dateLocale || "system";
    const style  = store.dateStyle  || "medium";
    return _getFormatter(locale, style, includeTime).format(
      new Date(timestampSeconds * 1000)
    );
  } catch {
    // Graceful fallback: always return something readable
    return new Date(timestampSeconds * 1000).toLocaleString();
  }
}

/**
 * Format an ISO 8601 date/time string (e.g. from note metadata) using the
 * user's locale/style preferences.  Always includes time.
 *
 * @param {string|null} iso  - ISO 8601 string, or null/undefined
 * @returns {string|null}
 */
export function formatDateIso(iso) {
  if (!iso) return null;
  try {
    const store = useGlobalStore();
    const locale = store.dateLocale || "system";
    const style  = store.dateStyle  || "medium";
    return _getFormatter(locale, style, true).format(new Date(iso));
  } catch {
    return iso;
  }
}
