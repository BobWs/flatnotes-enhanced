/**
 * taskIconStore.js — reactive store for user-configured task icon settings.
 *
 * Loaded once on first use. ToastViewer imports getTaskIconColor() to
 * resolve the fill color for each rendered task icon SVG.
 *
 * API shape returned by GET /api/settings/task-icons:
 * {
 *   enabled: boolean,
 *   colors: [{ marker: "?", color: "#6B7280" }, ...]
 * }
 */
import { ref } from "vue";
import { getTaskIcons } from "./api.js";

export const taskIconSettings = ref({
  enabled: true,
  colors: [],
});

let loaded = false;
let loading = false;

/** Fetch task icon settings from the server and populate the store. */
export async function loadTaskIcons(force = false) {
  if (loaded && !force) return;
  if (loading) return;
  loading = true;
  try {
    const data = await getTaskIcons();
    taskIconSettings.value = data;
    loaded = true;
  } catch {
    // Leave defaults in place if the API fails
  } finally {
    loading = false;
  }
}

/**
 * Look up the color for a specific task marker.
 * Returns the stored color, or "#6B7280" (default gray) if none configured.
 * Returns null when the feature is disabled (caller should use currentColor).
 */
export function getTaskIconColor(marker) {
  const s = taskIconSettings.value;
  if (!s.enabled) return null;

  const entry = s.colors.find(c => c.marker === marker);
  return entry ? entry.color : "#6B7280";
}

/** Returns true when the task icon feature is active. */
export function isTaskIconsEnabled() {
  return taskIconSettings.value.enabled === true;
}
