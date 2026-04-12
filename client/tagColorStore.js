/**
 * tagColorStore.js — reactive store for user-configured tag colors.
 *
 * Loaded once on first use. All components that call tagColor() / tagColorLight()
 * automatically benefit from the override once this store is populated.
 *
 * API shape returned by /api/settings/tag-colors:
 * {
 *   custom_colors_enabled: boolean,
 *   default_color: "#006633",
 *   tag_colors: [{ tag: "work", color: "#337AB7", enabled: true }, ...]
 * }
 */
import { ref } from "vue";
import { getTagColors } from "./api.js";

export const tagColorSettings = ref({
  custom_colors_enabled: false,
  default_color: "#006633",
  tag_colors: [],
});

let loaded = false;
let loading = false;

/** Fetch tag color settings from the server and populate the store. */
export async function loadTagColors(force = false) {
  if (loaded && !force) return;
  if (loading) return;
  loading = true;
  try {
    const data = await getTagColors();
    tagColorSettings.value = data;
    loaded = true;
  } catch {
    // Leave defaults in place if the API fails
  } finally {
    loading = false;
  }
}

/**
 * Look up the custom color for a specific tag.
 * Returns null if custom colors are disabled or no override exists for this tag.
 */
export function getCustomTagColor(tag) {
  const s = tagColorSettings.value;
  if (!s.custom_colors_enabled) return null;

  const tagLower = (tag || "").toLowerCase();
  const entry = s.tag_colors.find(
    (t) => t.tag.toLowerCase() === tagLower && t.enabled
  );
  if (entry) return entry.color;

  // Fall back to the global default color when custom colors are enabled
  return s.default_color || "#006633";
}

/** Returns true when custom tag coloring is active. */
export function isCustomTagColorEnabled() {
  return tagColorSettings.value.custom_colors_enabled === true;
}
