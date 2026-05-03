// Namespace the storage key by origin so multiple Flatnotes instances running
// on different domains (e.g. wnotes.example.com and mynotes.example.com) never
// share or overwrite each other's session data in the same browser.
// btoa(origin) gives a stable, filename-safe suffix unique to each deployment.
// Use URL-safe base64 for the key: standard btoa() can produce +, /, = which
// are invalid in cookie names and cause the cookie to be silently dropped.
// This was the root cause of attachment 401s on HTTPS domains.

const tokenStorageKey = `token_${btoa(location.origin)
  .replace(/\+/g, '-')
  .replace(/\//g, '_')
  .replace(/=/g, '')}`; 

function getBasePath() {
  // This relies on the fact that flanotes always has a correctly formatted relative path set in <base> tag
  return document.querySelector('base').getAttribute('href')
}

function getCookieString(token) {
  const basePath = getBasePath();
  return `${tokenStorageKey}=${token}; Path=${basePath}; SameSite=Strict`;
}

export function storeToken(token, persist = false) {
  document.cookie = getCookieString(token);
  sessionStorage.setItem(tokenStorageKey, token);
  if (persist === true) {
    localStorage.setItem(tokenStorageKey, token);
  }
}

export function getStoredToken() {
  return sessionStorage.getItem(tokenStorageKey);
}

export function loadStoredToken() {
  let token = localStorage.getItem(tokenStorageKey);

  // One-time migration: if the new namespaced key is empty but the old "token"
  // key exists, carry it forward and clear the old key so it doesn't persist.
  // This handles users upgrading from a pre-namespacing build without forcing
  // a manual re-login.
  if (token == null) {
    const legacy = localStorage.getItem("token");
    if (legacy != null) {
      localStorage.setItem(tokenStorageKey, legacy);
      localStorage.removeItem("token");
      token = legacy;
    }
  }

  if (token != null) {
    storeToken(token, false);
  }
}

export function clearStoredToken() {
  sessionStorage.removeItem(tokenStorageKey);
  localStorage.removeItem(tokenStorageKey);
  document.cookie =
    getCookieString() + "; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

export function isCurrentTokenStored() {
  const localToken = localStorage.getItem(tokenStorageKey);
  if (localToken == null) {
    return false;
  }
  const sessionToken = sessionStorage.getItem(tokenStorageKey);
  return localToken === sessionToken;
}