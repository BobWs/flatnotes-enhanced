/**
 * appearanceStore.js — reactive store for appearance settings.
 *
 * Manages header colors, highlight colors, table style, and quote style.
 * Loaded once on first use by initSettingsStore(). All components that
 * render content import from here to stay in sync with saved configuration.
 */
import { ref } from "vue";
import {
  getHeaderColors,
  getHighlightColors,
  getDefaultHighlight,
  getTableStyle,
  getQuoteStyle,
} from "./api.js";

// ── State ────────────────────────────────────────────────────────────────────

export const headerColors = ref([]);

export const highlightColors = ref([]);
export const defaultHighlight = ref("Yellow");

export const tableStyle = ref({
  header_color: "#085294",
  zebra_striping: true,
  enabled: true,
});

export const quoteStyle = ref({
  border_color: "#006633",
  background_color: "#f9f9f9",
  dark_background_color: "rgba(0, 102, 51, 0.17)",
  enabled: true,
});

// ── Loading flags ─────────────────────────────────────────────────────────────

let headersLoaded = false;
let highlightsLoaded = false;
let tableLoaded = false;
let quoteLoaded = false;

// ── Loaders ──────────────────────────────────────────────────────────────────

export async function loadHeaderColors(force = false) {
  if (headersLoaded && !force) return;
  try {
    const data = await getHeaderColors();
    headerColors.value = data;
    headersLoaded = true;
  } catch {
    // Keep defaults on API failure
  }
}

export async function loadHighlightColors(force = false) {
  if (highlightsLoaded && !force) return;
  try {
    const data = await getHighlightColors();
    highlightColors.value = data;
    try {
      const defaultName = await getDefaultHighlight();
      defaultHighlight.value = defaultName;
    } catch {}
    highlightsLoaded = true;
  } catch {
    // Keep defaults on API failure
  }
}

export async function loadTableStyle(force = false) {
  if (tableLoaded && !force) return;
  try {
    const data = await getTableStyle();
    tableStyle.value = data;
    tableLoaded = true;
  } catch {
    // Keep defaults on API failure
  }
}

export async function loadQuoteStyle(force = false) {
  if (quoteLoaded && !force) return;
  try {
    const data = await getQuoteStyle();
    quoteStyle.value = data;
    quoteLoaded = true;
  } catch {
    // Keep defaults on API failure
  }
}

// ── Accessors ─────────────────────────────────────────────────────────────────

export function getHeaderColor(level) {
  const found = headerColors.value.find((c) => c.level === level);
  // If the header entry exists and is enabled, return its custom color.
  // If disabled (individually or via the global toggle), return null so the
  // renderer knows NOT to apply any color — allowing browser/CSS defaults.
  // If headerColors hasn't loaded yet (empty array), also return null.
  if (found && found.enabled) return found.color;
  return null;
}

/** Returns true when at least one header level has a custom color enabled. */
export function hasAnyHeaderEnabled() {
  return headerColors.value.some((c) => c.enabled);
}

export function getDefaultHighlightColor() {
  const found = highlightColors.value.find((c) => c.name === defaultHighlight.value);
  if (found && found.enabled) return found.color;
  const first = highlightColors.value.find((c) => c.enabled);
  return first ? first.color : "#ffffcc";
}

export function getEnabledHighlightColors() {
  return highlightColors.value.filter((c) => c.enabled);
}

export function getTableStyleEnabled() {
  return tableStyle.value.enabled;
}

export function getTableHeaderColor() {
  return tableStyle.value.enabled ? tableStyle.value.header_color : "";
}

export function getZebraStriping() {
  return tableStyle.value.enabled && tableStyle.value.zebra_striping;
}

export function getQuoteStyleEnabled() {
  return quoteStyle.value.enabled;
}

export function getQuoteBorderColor() {
  return quoteStyle.value.enabled ? quoteStyle.value.border_color : "";
}

export function getQuoteBackgroundColor() {
  return quoteStyle.value.enabled ? quoteStyle.value.background_color : "";
}

export function getQuoteDarkBackgroundColor() {
  return quoteStyle.value.enabled ? quoteStyle.value.dark_background_color : "";
}