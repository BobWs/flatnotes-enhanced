/**
 * frontmatterStore.js
 *
 * Reactive singleton that holds the user's "strip frontmatter" preference.
 *
 * Consumers (ToastViewer, NotePreview) import stripFrontmatterEnabled and
 * call stripFrontmatter() from frontmatter.js when the ref is true.
 */

import { ref } from 'vue';
import { getPrefs } from './api.js';

/** True → strip frontmatter entirely in view/preview mode. */
export const stripFrontmatterEnabled = ref(false);

let _loaded = false;

/**
 * Load the preference from the backend.
 * Safe to call multiple times — no-op after the first successful load.
 * Pass force=true to re-fetch (used after the user saves settings).
 *
 * @param {boolean} [force=false]
 */
export async function loadFrontmatterPrefs(force = false) {
  if (_loaded && !force) return;
  try {
    const prefs = await getPrefs();
    stripFrontmatterEnabled.value = Boolean(prefs.strip_frontmatter);
    _loaded = true;
  } catch {
    // Non-fatal — leave existing value unchanged.
  }
}

/**
 * Push the updated value immediately after a successful settings save so
 * open viewers re-render without requiring a page reload.
 *
 * @param {boolean} strip
 */
export function setFrontmatterPrefs({ strip }) {
  stripFrontmatterEnabled.value = Boolean(strip);
  _loaded = true;
}
