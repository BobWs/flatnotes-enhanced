/**
 * pwaService.js — Service Worker registration and messaging.
 *
 * Registers the SW on first call to init().  Subsequent calls are no-ops.
 * Exposes:
 *   init()                     — register SW (call once at app startup)
 *   setOfflineCache(enabled)   — tell the SW to enable/disable API caching
 *   unregisterAll()            — unregister all SWs and clear caches
 */

let _registration = null;

/**
 * Register the service worker.  Safe to call multiple times (idempotent).
 * Returns the ServiceWorkerRegistration, or null if SW is not supported.
 */
export async function init() {
  if (!('serviceWorker' in navigator)) return null;
  if (_registration) return _registration;

  try {
    _registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    // Activate any waiting SW immediately (e.g. after a build update)
    _registration.addEventListener('updatefound', () => {
      const incoming = _registration.installing;
      if (!incoming) return;
      incoming.addEventListener('statechange', () => {
        if (incoming.state === 'installed' && navigator.serviceWorker.controller) {
          // New SW waiting — send skipWaiting so it takes over without forcing a reload.
          incoming.postMessage({ type: 'SKIP_WAITING' });
        }
      });
    });

    return _registration;
  } catch (err) {
    console.warn('[PWA] Service worker registration failed:', err);
    return null;
  }
}

/**
 * Send a message to the active service worker.
 * Returns true if the message was delivered, false otherwise.
 */
function _postMessage(msg) {
  const controller = navigator.serviceWorker?.controller;
  if (!controller) return false;
  controller.postMessage(msg);
  return true;
}

/**
 * Tell the service worker to enable or disable API response caching.
 * If enabling and the SW isn't registered yet, register it first.
 */
export async function setOfflineCache(enabled) {
  if (enabled) {
    await init();
  }
  _postMessage({ type: 'SET_OFFLINE_CACHE', enabled: Boolean(enabled) });
}

/**
 * Unregister all service workers for this scope and delete all caches.
 * Called when the user disables offline caching.
 */
export async function unregisterAll() {
  if (!('serviceWorker' in navigator)) return;

  const registrations = await navigator.serviceWorker.getRegistrations();
  for (const reg of registrations) {
    await reg.unregister();
  }
  _registration = null;

  if ('caches' in window) {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
  }
}
