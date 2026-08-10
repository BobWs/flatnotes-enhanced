/**
 * sw.js — Flatnotes-Enhanced Service Worker
 *
 * Strategy:
 *   App shell (JS/CSS/fonts/icons) → CacheFirst, 30-day TTL
 *   API GET responses              → NetworkFirst, 7-day TTL (only when offline cache is enabled)
 *
 * The app sends a SET_OFFLINE_CACHE message to toggle API caching at runtime.
 * The flag is persisted in IndexedDB so it survives SW restarts.
 */

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, setDefaultHandler } from 'workbox-routing';
import {
  NetworkFirst,
  CacheFirst,
  NetworkOnly,
} from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// ── Constants ────────────────────────────────────────────────────────────────
const API_CACHE        = 'fn-api-v1';
const ASSETS_CACHE     = 'fn-assets-v1';
const OFFLINE_PAGE     = '/offline.html';
const DB_NAME          = 'fn-sw-settings';
const DB_STORE         = 'settings';
const CACHE_ENABLED_KEY = 'offlineCacheEnabled';

// API_MAX_ENTRIES: cap at 200 entries to avoid unbounded growth.
// After this limit the oldest entries are evicted automatically.
const API_MAX_ENTRIES   = 200;
const API_MAX_AGE_SECS  = 7 * 24 * 60 * 60;   // 7 days
const ASSET_MAX_AGE_SECS = 30 * 24 * 60 * 60; // 30 days

// ── Precache app shell (injected by vite-plugin-pwa at build time) ────────────
precacheAndRoute(self.__WB_MANIFEST || []);
cleanupOutdatedCaches();

// ── IndexedDB helpers (store the offline-cache toggle) ───────────────────────
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore(DB_STORE);
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror   = (e) => reject(e.target.error);
  });
}

async function getSetting(key) {
  try {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx  = db.transaction(DB_STORE, 'readonly');
      const req = tx.objectStore(DB_STORE).get(key);
      req.onsuccess = (e) => resolve(e.target.result);
      req.onerror   = (e) => reject(e.target.error);
    });
  } catch {
    return null;
  }
}

async function setSetting(key, value) {
  try {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx  = db.transaction(DB_STORE, 'readwrite');
      const req = tx.objectStore(DB_STORE).put(value, key);
      req.onsuccess = () => resolve();
      req.onerror   = (e) => reject(e.target.error);
    });
  } catch {
    // non-fatal
  }
}

// ── Runtime cache-enabled flag ────────────────────────────────────────────────
// Initialised from DB so the setting survives SW restarts.
let apiCacheEnabled = false;

(async () => {
  const stored = await getSetting(CACHE_ENABLED_KEY);
  apiCacheEnabled = stored === true;
})();

// ── Message handler (from the app) ───────────────────────────────────────────
self.addEventListener('message', async (event) => {
  if (!event.data) return;

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }

  if (event.data.type === 'SET_OFFLINE_CACHE') {
    const enabled = Boolean(event.data.enabled);
    apiCacheEnabled = enabled;
    await setSetting(CACHE_ENABLED_KEY, enabled);

    // When turning off, wipe the API cache so stale data is cleared.
    if (!enabled) {
      await caches.delete(API_CACHE);
    }

    // Acknowledge
    if (event.source) {
      event.source.postMessage({ type: 'OFFLINE_CACHE_SET', enabled });
    }
  }

  if (event.data.type === 'GET_OFFLINE_CACHE_STATUS') {
    if (event.source) {
      event.source.postMessage({ type: 'OFFLINE_CACHE_STATUS', enabled: apiCacheEnabled });
    }
  }
});

// ── Share routes: always NetworkOnly (tokens may be revoked at any time) ─────
// /api/share/* and /api/shared/* must never be served from cache — a revoked
// share token would otherwise continue to grant access while offline.
registerRoute(
  ({ url }) =>
    url.pathname.startsWith('/api/share/') ||
    url.pathname.startsWith('/api/shared/'),
  new NetworkOnly()
);

// ── API route: NetworkFirst (only when enabled) ───────────────────────────────
// Matches all /api/* GET requests.  When offline cache is disabled we fall
// through to a plain NetworkOnly handler (transparent, no caching).
registerRoute(
  ({ url, request }) =>
    url.pathname.startsWith('/api/') &&
    !url.pathname.startsWith('/api/share/') &&
    !url.pathname.startsWith('/api/shared/') &&
    request.method === 'GET',
  async (context) => {
    if (!apiCacheEnabled) {
      // Pass-through — no caching
      return new NetworkOnly().handle(context);
    }

    return new NetworkFirst({
      cacheName: API_CACHE,
      plugins: [
        new ExpirationPlugin({
          maxEntries:    API_MAX_ENTRIES,
          maxAgeSeconds: API_MAX_AGE_SECS,
          purgeOnQuotaError: true,
        }),
        // Only cache 200-range responses; skip 401/403/404 etc.
        new CacheableResponsePlugin({ statuses: [200] }),
      ],
      // Network timeout before falling back to cache (3 seconds)
      networkTimeoutSeconds: 3,
    }).handle(context);
  }
);

// ── Static assets: CacheFirst ────────────────────────────────────────────────
// JS/CSS/fonts/images from the same origin — aggressive caching with hashed names.
registerRoute(
  ({ request }) =>
    ['script', 'style', 'font', 'image'].includes(request.destination),
  new CacheFirst({
    cacheName: ASSETS_CACHE,
    plugins: [
      new ExpirationPlugin({
        maxEntries:    150,
        maxAgeSeconds: ASSET_MAX_AGE_SECS,
        purgeOnQuotaError: true,
      }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
  })
);

// ── Offline fallback for navigation requests ──────────────────────────────────
// When the user navigates to a page and both network and precache miss, serve
// the offline page (which is itself precached).
setDefaultHandler(new NetworkOnly());

self.addEventListener('fetch', (event) => {
  if (event.request.mode !== 'navigate') return;
  event.respondWith(
    fetch(event.request).catch(async () => {
      const cache = await caches.open('workbox-precache-v2');
      const cached = await caches.match(OFFLINE_PAGE);
      return cached || new Response('You are offline.', {
        status: 503,
        headers: { 'Content-Type': 'text/plain' },
      });
    })
  );
});
