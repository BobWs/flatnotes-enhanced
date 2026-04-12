export function getToastOptions(description, title, severity) {
  return {
    summary: title,
    detail: description,
    severity: severity,
    closable: false,
    life: 5000,
  };
}

export function setDarkThemeOn(save = true) {
  document.body.classList.add("dark");
  if (save) localStorage.setItem("darkTheme", "true");
}

export function setDarkThemeOff(save = true) {
  document.body.classList.remove("dark");
  if (save) localStorage.setItem("darkTheme", "false");
}

export function toggleTheme() {
  if (document.body.classList.contains("dark")) {
    setDarkThemeOff();
  } else {
    setDarkThemeOn();
  }
}

// Get system preference
function getSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Apply theme based on stored preference or system
export function loadTheme() {
  const storedTheme = localStorage.getItem("darkTheme");
  
  if (storedTheme === "true") {
    setDarkThemeOn(false);
  } else if (storedTheme === "false") {
    setDarkThemeOff(false);
  } else {
    // No stored preference, use system preference
    if (getSystemTheme() === "dark") {
      setDarkThemeOn(false);
    } else {
      setDarkThemeOff(false);
    }
  }
}

// Listen for system theme changes
let mediaQueryListener = null;

export function initThemeListener() {
  // Remove existing listener if any
  if (mediaQueryListener) {
    const oldQuery = window.matchMedia("(prefers-color-scheme: dark)");
    oldQuery.removeEventListener("change", mediaQueryListener);
  }
  
  // Create new listener
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  
  mediaQueryListener = (e) => {
    // Only auto-switch if user hasn't manually set a preference
    if (localStorage.getItem("darkTheme") === null) {
      if (e.matches) {
        setDarkThemeOn(false);
      } else {
        setDarkThemeOff(false);
      }
    }
  };
  
  mediaQuery.addEventListener("change", mediaQueryListener);
}

// Optional: cleanup function if needed
export function cleanupThemeListener() {
  if (mediaQueryListener) {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.removeEventListener("change", mediaQueryListener);
    mediaQueryListener = null;
  }
}

/**
 * Clear any manually-saved theme preference and follow OS system setting.
 * After calling this the initThemeListener will auto-switch on OS changes.
 */
export function followSystemTheme() {
  localStorage.removeItem("darkTheme");
  if (getSystemTheme() === "dark") {
    setDarkThemeOn(false);   // apply without saving to localStorage
  } else {
    setDarkThemeOff(false);  // apply without saving to localStorage
  }
}

/** Returns true when the user has an explicit manual preference stored. */
export function hasManualThemePreference() {
  return localStorage.getItem("darkTheme") !== null;
}

/** Returns "dark" | "light" | "system" */
export function getCurrentThemeMode() {
  const stored = localStorage.getItem("darkTheme");
  if (stored === null) return "system";
  return stored === "true" ? "dark" : "light";
}