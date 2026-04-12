/**
 * calloutStore.js — shared reactive callout registry.
 *
 * Loaded once on first use. Both ToastViewer (rendering) and
 * ToastEditor (autocomplete) import from here so they stay in sync
 * with the user's saved callout configuration.
 *
 * Appearance settings (headers, highlights, table, quote) live in
 * appearanceStore.js. Tag color settings live in tagColorStore.js.
 */
import { ref } from "vue";
import { getCallouts } from "./api.js";
import {
  loadHeaderColors,
  loadHighlightColors,
  loadTableStyle,
  loadQuoteStyle,
} from "./appearanceStore.js";
import { loadTagColors } from "./tagColorStore.js";
import { loadTaskIcons } from "./taskIconStore.js";

// ── State ────────────────────────────────────────────────────────────────────

export const callouts = ref([]);

let calloutsLoaded = false;
let calloutsLoading = false;

// ── Loaders ──────────────────────────────────────────────────────────────────

export async function loadCallouts(force = false) {
  if (calloutsLoaded && !force) return;
  if (calloutsLoading) return;
  calloutsLoading = true;
  try {
    const data = await getCallouts();
    callouts.value = data;
    calloutsLoaded = true;
  } catch {
    // If API fails, leave existing data in place
  } finally {
    calloutsLoading = false;
  }
}

/**
 * Initialise all settings stores in parallel on app startup.
 * Called once after authentication succeeds.
 */
export async function initSettingsStore() {
  await Promise.all([
    loadCallouts(),
    loadHeaderColors(),
    loadHighlightColors(),
    loadTableStyle(),
    loadQuoteStyle(),
    loadTagColors(),
    loadTaskIcons(),
  ]);
}

// ── Accessors ─────────────────────────────────────────────────────────────────

export function getCalloutIcon(type) {
  const found = callouts.value.find((c) => c.type === type);
  if (found) return found.icon;
  // Default: comment/speech bubble
  return "M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2Z";
}

export function getCalloutColor(type) {
  const found = callouts.value.find((c) => c.type === type);
  return found ? found.color : "#82D0D8";
}

export function getCalloutTypes() {
  if (callouts.value.length === 0) {
    return ["note", "info", "warning", "danger", "success", "tip", "question"];
  }
  return callouts.value.map((c) => c.type).sort();
}

/** Convert #RRGGBB to "R, G, B" for use in CSS rgb() / rgba(). */
export function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  return `${r}, ${g}, ${b}`;
}
