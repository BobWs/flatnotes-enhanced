/**
 * tagColor.js — shared deterministic tag → color mapping.
 *
 * Priority order:
 *   1. User-configured custom color (from tagColorStore)  ← NEW
 *   2. FNV-1a hash-based HSL color (original behaviour)
 *
 * Special case: "pin" always returns orange regardless of any setting.
 *
 * Components that already import tagColor() / tagColorLight() automatically
 * get user-configured colors without any changes to their own code.
 */
import { getCustomTagColor, isCustomTagColorEnabled } from "./tagColorStore.js";

// ── FNV-1a hash helpers (used when no custom color is set) ────────────────────

function _fnvHue(tag) {
  const str = (tag || "").toLowerCase();
  let hash = 2166136261;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = (hash * 16777619) >>> 0;
  }
  let hue = hash % 360;
  if (hue >= 65 && hue <= 95) hue = (hue + 40) % 360;
  return hue;
}

/** Convert a hex color like "#337AB7" to "hsl(210, 55%, 45%)" for use in HSL contexts. */
function hexToHsl(hex) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return `hsl(${Math.round(h * 360)}, ${Math.round(s * 100)}%, ${Math.round(l * 100)}%)`;
}

/** Convert hex to a light tint for chip backgrounds. */
function hexToHslLight(hex) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s;
  const d = max - min;
  s = (max + min) > 1 ? d / (2 - max - min) : d / (max + min);
  if (!d) { h = 0; s = 0; }
  else {
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  // Force lightness to 92% for the chip background tint
  return `hsl(${Math.round(h * 360)}, ${Math.round((s || 0.55) * 100)}%, 92%)`;
}


// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Returns an HSL color string for a given tag name.
 * Uses user-configured color when available, otherwise FNV hash.
 */
export function tagColor(tag) {
  if (tag === "pin") return "hsl(25, 95%, 50%)";

  const custom = getCustomTagColor(tag);
  if (custom) return hexToHsl(custom);

  // Original FNV-1a hash behaviour
  const hue = _fnvHue(tag);
  return `hsl(${hue}, 55%, 48%)`;
}

/**
 * Returns a very light tint of the tag color for chip backgrounds.
 */
export function tagColorLight(tag) {
  if (tag === "pin") return "hsl(25, 95%, 92%)";

  const custom = getCustomTagColor(tag);
  if (custom) return hexToHslLight(custom);

  const hue = _fnvHue(tag);
  return `hsl(${hue}, 55%, 92%)`;
}
