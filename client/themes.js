/**
 * themes.js — central registry of predefined color themes.
 *
 * This module is data-only: it describes what themes exist and what they
 * look like (for rendering the ThemePicker's swatches). It intentionally
 * knows nothing about the DOM, localStorage, or how a theme gets applied —
 * that logic lives in helpers.js (applyTheme/setTheme/loadTheme), which
 * imports COLOR_THEMES and ALL_THEME_IDS from here.
 *
 * The actual CSS variable values for each theme live in style.css as
 * `body.theme-<id>` class rules (see the "Predefined color themes" section
 * there). Keeping the full 8-variable definitions there — rather than here
 * — avoids the picker needing to inject styles at runtime, and matches how
 * the existing `body` / `body.dark` default themes already work. This file
 * only duplicates the 3 colors needed for a swatch preview; if you add or
 * edit a theme, update both places.
 */

// The three built-in modes — unchanged behaviour, no CSS class of their own
// (they rely on the existing `body` / `body.dark` base rules in style.css).
// Swatch colors here mirror those base rules, purely for the picker preview
// — a Branding accent can still override the actual applied brand color.
// "system" has no fixed swatch since it resolves to whichever of the two
// above applies; the picker renders it with an icon instead.
export const DEFAULT_THEMES = [
  {
    id: "light",
    label: "Light",
    mode: "light",
    colors: { brand: "248 166 107", background: "255 255 255", backgroundElevated: "243 244 245" },
  },
  {
    id: "dark",
    label: "Dark",
    mode: "dark",
    colors: { brand: "248 166 107", background: "34 38 44", backgroundElevated: "44 49 57" },
  },
  { id: "system", label: "System", mode: null, colors: null },
];

// Predefined third-party color themes, grouped by family for the picker.
// `colors` holds just enough for a swatch preview (brand + the two
// backgrounds) — the full variable set is defined in style.css.
export const COLOR_THEMES = [
  {
    id: "dracula",
    label: "Dracula",
    family: "Dracula",
    mode: "dark",
    colors: { brand: "189 147 249", background: "40 42 54", backgroundElevated: "68 71 90" },
  },
  {
    id: "dracula-alucard",
    label: "Dracula Alucard",
    family: "Dracula",
    mode: "light",
    colors: { brand: "100 74 201", background: "255 251 235", backgroundElevated: "239 233 217" },
  },
  {
    id: "catppuccin-latte",
    label: "Catppuccin Latte",
    family: "Catppuccin",
    mode: "light",
    colors: { brand: "30 102 245", background: "239 241 245", backgroundElevated: "230 233 239" },
  },
  {
    id: "catppuccin-frappe",
    label: "Catppuccin Frappé",
    family: "Catppuccin",
    mode: "dark",
    colors: { brand: "140 170 238", background: "48 52 70", backgroundElevated: "65 69 89" },
  },
  {
    id: "catppuccin-macchiato",
    label: "Catppuccin Macchiato",
    family: "Catppuccin",
    mode: "dark",
    colors: { brand: "138 173 244", background: "36 39 58", backgroundElevated: "54 58 79" },
  },
  {
    id: "catppuccin-mocha",
    label: "Catppuccin Mocha",
    family: "Catppuccin",
    mode: "dark",
    colors: { brand: "137 180 250", background: "30 30 46", backgroundElevated: "49 50 68" },
  },
  {
    id: "gruvbox-light",
    label: "Gruvbox Light",
    family: "Gruvbox",
    mode: "light",
    colors: { brand: "175 58 3", background: "251 241 199", backgroundElevated: "235 219 178" },
  },
  {
    id: "gruvbox-dark",
    label: "Gruvbox Dark",
    family: "Gruvbox",
    mode: "dark",
    colors: { brand: "254 128 25", background: "40 40 40", backgroundElevated: "60 56 54" },
  },
  {
    id: "nord",
    label: "Nord",
    family: "Nord",
    mode: "dark",
    colors: { brand: "136 192 208", background: "46 52 64", backgroundElevated: "59 66 82" },
  },
  {
    id: "solarized-light",
    label: "Solarized Light",
    family: "Solarized",
    mode: "light",
    colors: { brand: "38 139 210", background: "253 246 227", backgroundElevated: "238 232 213" },
  },
  {
    id: "solarized-dark",
    label: "Solarized Dark",
    family: "Solarized",
    mode: "dark",
    colors: { brand: "38 139 210", background: "0 43 54", backgroundElevated: "7 54 66" },
  },
  {
    id: "tokyo-night",
    label: "Tokyo Night",
    family: "Tokyo Night",
    mode: "dark",
    colors: { brand: "122 162 247", background: "26 27 38", backgroundElevated: "36 40 59" },
  },
  {
    id: "tokyo-night-storm",
    label: "Tokyo Night Storm",
    family: "Tokyo Night",
    mode: "dark",
    colors: { brand: "122 162 247", background: "36 40 59", backgroundElevated: "47 51 77" },
  },
  {
    id: "tokyo-night-light",
    label: "Tokyo Night Light",
    family: "Tokyo Night",
    mode: "light",
    colors: { brand: "41 89 170", background: "230 231 237", backgroundElevated: "213 214 219" },
  },
  {
    id: "one-dark",
    label: "One Dark",
    family: "One",
    mode: "dark",
    colors: { brand: "97 175 239", background: "40 44 52", backgroundElevated: "44 49 60" },
  },
  {
    id: "one-light",
    label: "One Light",
    family: "One",
    mode: "light",
    colors: { brand: "64 120 242", background: "250 250 250", backgroundElevated: "234 234 235" },
  },
];

// Every valid theme id, default modes included — used to validate a stored
// `fn_theme` value and to look a theme up by id.
export const ALL_THEMES = [...DEFAULT_THEMES, ...COLOR_THEMES];
export const ALL_THEME_IDS = ALL_THEMES.map((t) => t.id);

export function getTheme(id) {
  return ALL_THEMES.find((t) => t.id === id) || null;
}

// Maps a color theme's id to the `body.theme-*` class its rule uses in
// style.css. applyTheme() in helpers.js looks the class up here instead of
// building it as `theme-${id}` at runtime: Tailwind's content scanner only
// keeps hand-written `@layer` classes (like these) that appear as a literal
// string somewhere under client/**/*.{html,js,vue} — a template literal
// isn't visible to it, so an interpolated class name gets silently purged
// from the build. Every value below must stay a plain string literal.
export const COLOR_THEME_BODY_CLASSES = {
  dracula: "theme-dracula",
  "dracula-alucard": "theme-dracula-alucard",
  "catppuccin-latte": "theme-catppuccin-latte",
  "catppuccin-frappe": "theme-catppuccin-frappe",
  "catppuccin-macchiato": "theme-catppuccin-macchiato",
  "catppuccin-mocha": "theme-catppuccin-mocha",
  "gruvbox-light": "theme-gruvbox-light",
  "gruvbox-dark": "theme-gruvbox-dark",
  nord: "theme-nord",
  "solarized-light": "theme-solarized-light",
  "solarized-dark": "theme-solarized-dark",
  "tokyo-night": "theme-tokyo-night",
  "tokyo-night-storm": "theme-tokyo-night-storm",
  "tokyo-night-light": "theme-tokyo-night-light",
  "one-dark": "theme-one-dark",
  "one-light": "theme-one-light",
};
