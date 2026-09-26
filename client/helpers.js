import { ALL_THEME_IDS, COLOR_THEME_BODY_CLASSES, COLOR_THEMES, DEFAULT_THEMES, getTheme } from "./themes.js";

/**
 * Convert a "#rrggbb" hex color into the "r g b" space-separated triplet
 * that --theme-brand (see style.css) is declared in, for use with Tailwind's
 * `rgb(var(--theme-brand) / <alpha>)` pattern. Returns null for anything
 * that isn't a valid 6-digit hex color.
 */
export function hexToRgbTriplet(hex) {
  if (!hex) return null;
  const match = /^#?([0-9a-fA-F]{6})$/.exec(String(hex).trim());
  if (!match) return null;
  const value = parseInt(match[1], 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `${r} ${g} ${b}`;
}

/**
 * Apply a custom accent color to the whole document.
 *
 * --theme-brand is declared on `body`, not `:root` (see style.css) — setting
 * it on documentElement would be silently shadowed by body's own
 * declaration, so it must be set here too.
 *
 * With no accent (unset, or an invalid value) the inline override is
 * removed so the stylesheet's own default — the built-in Flatnotes-Enhanced
 * orange — takes over. That's what "Reset to defaults" relies on: it never
 * needs to know the default value, just to stop overriding it.
 */
export function applyBranding(accent) {
  const rgb = hexToRgbTriplet(accent);
  if (rgb) {
    document.body.style.setProperty("--theme-brand", rgb);
  } else {
    document.body.style.removeProperty("--theme-brand");
  }
}

const ICON_LINK_SELECTOR = 'link[rel="icon"], link[rel="shortcut icon"]';
// Captured once, lazily, from whatever index.html shipped (Vite's hashed
// build filenames) — the only reliable way to know what "default" means
// without hardcoding a filename here.
let defaultIconHrefs = null;

// Same mark as the icon rendered in Logo.vue (viewBox 0 0 36 36), but with
// its rect's fill parameterized instead of "currentColor" — a favicon link
// can't read CSS variables the way the in-page logo does, so the accent
// has to be baked into the SVG source itself.
function tintedFaviconSvg(accentHex) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><rect width="36" height="36" rx="4" fill="${accentHex}"/><path d="M9.904 28.88C9.75467 28.88 9.59467 28.7733 9.424 28.56C9.27467 28.3467 9.14667 28.1013 9.04 27.824C8.95467 27.5467 8.912 27.3227 8.912 27.152C8.95467 26.32 9.14667 25.3813 9.488 24.336C9.59467 24.0373 9.75467 23.9093 9.968 23.952C10.0107 23.5893 10.0533 23.1307 10.096 22.576C10.16 22.0213 10.2347 21.3813 10.32 20.656C10.2133 20.3573 9.98933 20.208 9.648 20.208C9.56267 20.208 9.24267 20.2613 8.688 20.368C8.15467 20.4747 7.36533 20.6347 6.32 20.848C6.29867 20.848 6.27733 20.8587 6.256 20.88C6.23467 20.88 6.20267 20.8693 6.16 20.848C5.94667 20.848 5.84 20.72 5.84 20.464C5.84 20.1653 5.97867 19.952 6.256 19.824L6.224 19.856C6.544 19.7067 7.32267 19.4827 8.56 19.184C9.47733 18.9493 10.2133 18.6507 10.768 18.288L10.96 16.656C11.0453 15.8667 11.184 15.056 11.376 14.224C11.568 13.3707 11.8347 12.5067 12.176 11.632C12.88 9.73333 13.712 8.208 14.672 7.056C15.4827 6.11733 16.2933 5.648 17.104 5.648C17.808 5.648 18.4267 5.97867 18.96 6.64C19.0453 6.72533 19.088 6.82133 19.088 6.928C19.088 7.16267 18.96 7.28 18.704 7.28C18.5547 7.28 18.4267 7.216 18.32 7.088C17.9787 6.68267 17.6053 6.48 17.2 6.48C16.24 6.48 15.2267 7.536 14.16 9.648C13.7333 10.5013 13.36 11.5147 13.04 12.688C12.72 13.84 12.4747 15.1413 12.304 16.592L12.272 17.136L12.208 18C12.8267 18.192 13.5093 18.288 14.256 18.288L16.304 18.224C16.944 18.2453 17.264 18.4587 17.264 18.864C17.264 19.2267 17.0933 19.408 16.752 19.408H14.256C13.36 19.472 12.5707 19.7173 11.888 20.144C11.248 25.0933 10.704 27.92 10.256 28.624C10.1493 28.7947 10.032 28.88 9.904 28.88ZM17.839 27.856C17.3483 27.856 16.9643 27.792 16.687 27.664C16.431 27.536 16.303 27.3973 16.303 27.248C16.303 27.12 16.367 27.0027 16.495 26.896C16.6443 26.7893 16.8897 26.7253 17.231 26.704C17.6577 26.6827 18.255 26.6613 19.023 26.64C19.791 26.6187 20.6337 26.5973 21.551 26.576C22.4897 26.5547 23.407 26.544 24.303 26.544C24.7723 26.544 25.231 26.544 25.679 26.544C26.127 26.544 26.5217 26.5547 26.863 26.576C27.2257 26.5973 27.4923 26.6293 27.663 26.672C27.8337 26.7147 27.919 26.832 27.919 27.024C27.919 27.2587 27.823 27.408 27.631 27.472C27.439 27.536 27.2043 27.568 26.927 27.568C26.4363 27.568 25.7963 27.5787 25.007 27.6C24.2177 27.6427 23.375 27.6747 22.479 27.696C21.583 27.7387 20.719 27.7707 19.887 27.792C19.0763 27.8347 18.3937 27.856 17.839 27.856Z" fill="white"/></svg>`;
}

/**
 * Point the browser tab's favicon links at:
 *   1. the custom uploaded favicon, if there is one;
 *   2. otherwise, the built-in mark tinted with the custom accent color, if
 *      one is set — a browser favicon can't read --theme-brand the way the
 *      in-page logo does, so this bakes the same color into a data: URI;
 *   3. otherwise, the app's original built-in favicon.
 * This is what makes "Reset to defaults" work for the tab icon, and what
 * keeps it in sync with the accent color, without a page reload.
 */
export function applyBrandFavicon(iconFilename, accent, version) {
  const links = document.querySelectorAll(ICON_LINK_SELECTOR);
  if (defaultIconHrefs === null) {
    defaultIconHrefs = new Map();
    links.forEach((link) => defaultIconHrefs.set(link, link.getAttribute("href")));
  }
  const rgb = hexToRgbTriplet(accent);
  if (iconFilename) {
    const href = `api/brand/favicon?v=${version}`;
    links.forEach((link) => link.setAttribute("href", href));
  } else if (rgb) {
    const href = `data:image/svg+xml,${encodeURIComponent(tintedFaviconSvg(accent))}`;
    links.forEach((link) => link.setAttribute("href", href));
  } else {
    links.forEach((link) => {
      const original = defaultIconHrefs.get(link);
      if (original) link.setAttribute("href", original);
    });
  }
}

export function getToastOptions(description, title, severity) {
  return {
    summary: title,
    detail: description,
    severity: severity,
    closable: false,
    life: 5000,
  };
}

// ── Theme Selector (v1.18.0) ────────────────────────────────────────────────
//
// Extends the previous Light/Dark/System toggle (which stored a plain
// "darkTheme" true/false/unset flag) with a picker over the predefined
// color themes registered in themes.js. A theme is applied as a class on
// `body` (e.g. `body.theme-dracula`, see style.css); the three built-in
// modes don't get a class of their own and rely on the existing
// `body` / `body.dark` base rules instead. `body.dark` is toggled for
// every theme, named ones included, so existing `.dark`-scoped component
// styles keep working unchanged.
//
// A Branding accent (see applyBranding above) is set as an inline style on
// `body`, which always beats a class selector's `--theme-brand` regardless
// of theme — so it doesn't need special-casing here.

const THEME_STORAGE_KEY = "fn_theme";
// Deprecated key from the old Light/Dark/System toggle — still read once,
// for migration, and never written again.
const LEGACY_DARK_KEY = "darkTheme";

function getSystemPrefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Resolve any theme id ("system" included) to its effective "light" | "dark" mode. */
export function resolveThemeMode(id) {
  const theme = getTheme(id);
  if (!theme || theme.mode === null) {
    return getSystemPrefersDark() ? "dark" : "light";
  }
  return theme.mode;
}

/**
 * Apply a theme by id to the document, without touching localStorage — see
 * setTheme() to also persist the choice. Falls back to "system" for an
 * unrecognized id (e.g. a theme removed in a future version).
 */
export function applyTheme(id) {
  const resolved = ALL_THEME_IDS.includes(id) ? id : "system";
  Array.from(document.body.classList)
    .filter((cls) => cls.startsWith("theme-"))
    .forEach((cls) => document.body.classList.remove(cls));
  // Looked up rather than interpolated as `theme-${resolved}` — see the
  // comment on COLOR_THEME_BODY_CLASSES in themes.js for why that matters.
  const bodyClass = COLOR_THEME_BODY_CLASSES[resolved];
  if (bodyClass) {
    document.body.classList.add(bodyClass);
  }
  document.body.classList.toggle("dark", resolveThemeMode(resolved) === "dark");
}

/** Apply a theme and persist it as the user's preference. */
export function setTheme(id) {
  applyTheme(id);
  localStorage.setItem(THEME_STORAGE_KEY, id);
}

/** Returns the currently selected theme id, defaulting to "system". */
export function getCurrentTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return ALL_THEME_IDS.includes(stored) ? stored : "system";
}

/** All themes available in the picker, grouped for display. */
export function getAvailableThemes() {
  return { default: DEFAULT_THEMES, colors: COLOR_THEMES };
}

// Apply the stored theme, migrating the deprecated "darkTheme" flag on
// first load after the update: fn_theme wins if present; otherwise a
// legacy darkTheme=true/false migrates to dark/light and is cleaned up;
// otherwise the default is "system".
export function loadTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (ALL_THEME_IDS.includes(stored)) {
    applyTheme(stored);
    return;
  }

  const legacy = localStorage.getItem(LEGACY_DARK_KEY);
  if (legacy === "true" || legacy === "false") {
    const migrated = legacy === "true" ? "dark" : "light";
    localStorage.setItem(THEME_STORAGE_KEY, migrated);
    localStorage.removeItem(LEGACY_DARK_KEY);
    applyTheme(migrated);
    return;
  }

  applyTheme("system");
}

// Listen for OS theme changes, so "system" keeps following them live.
let mediaQueryListener = null;

export function initThemeListener() {
  if (mediaQueryListener) {
    window.matchMedia("(prefers-color-scheme: dark)").removeEventListener("change", mediaQueryListener);
  }

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

  mediaQueryListener = () => {
    // Only re-apply if the user's selected theme is "system" — a named
    // theme (or plain light/dark) always ignores the OS preference.
    if (getCurrentTheme() === "system") {
      applyTheme("system");
    }
  };

  mediaQuery.addEventListener("change", mediaQueryListener);
}

export function cleanupThemeListener() {
  if (mediaQueryListener) {
    window.matchMedia("(prefers-color-scheme: dark)").removeEventListener("change", mediaQueryListener);
    mediaQueryListener = null;
  }
}