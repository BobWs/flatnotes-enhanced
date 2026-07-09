import * as constants from "./constants.js";

import { Note, SearchResult } from "./classes.js";

import axios from "axios";
import { getStoredToken } from "./tokenStorage.js";
import { getToastOptions } from "./helpers.js";
import router from "./router.js";

const api = axios.create();

api.interceptors.request.use(
  // If the request is not for the token endpoint, add the token to the headers.
  function (config) {
    if (config.url !== "api/token") {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  function (error) {
    return Promise.reject(error);
  },
);

export function apiErrorHandler(error, toast) {
  if (error.response?.status === 401) {
    const redirectPath = router.currentRoute.value.fullPath;
    router.push({
      name: "login",
      query: { [constants.params.redirect]: redirectPath },
    });
  } else if (error.request && !error.response) {
    // No response received — the server is unreachable (network failure, timeout,
    // or the service worker had no cached entry for this request).
    // Show a specific offline message rather than the generic "Unknown Error".
    toast.add(
      getToastOptions(
        "This content isn't available offline. Connect to your server to access it.",
        "Not Available Offline",
        "warn",
      ),
    );
  } else {
    console.error(error);
    toast.add(
      getToastOptions(
        "Unknown error communicating with the server. Please try again.",
        "Unknown Error",
        "error",
      ),
    );
  }
}

export async function getConfig() {
  try {
    const response = await api.get("api/config");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getTotpSetup() {
  try {
    const response = await api.get("api/totp-setup");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getToken(username, password, totp) {
  try {
    const response = await api.post("api/token", {
      username: username,
      password: totp ? password + totp : password,
    });
    return response.data.access_token;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function authCheck() {
  try {
    const response = await api.get("api/auth-check");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getNotes(term, sort, order, limit, includeArchived = false, includeTrash = false) {
  try {
    const response = await api.get("api/search", {
      params: {
        term: term,
        sort: sort,
        order: order,
        limit: limit,
        include_archived: includeArchived,
        include_trash: includeTrash,
      },
    });
    return response.data.map((note) => new SearchResult(note));
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function createNote(title, content) {
  try {
    const response = await api.post("api/notes", {
      title: title,
      content: content,
    });
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getNote(title) {
  try {
    const response = await api.get(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updateNote(title, newTitle, newContent) {
  try {
    const response = await api.patch(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}`, {
      newTitle: newTitle,
      newContent: newContent,
    });
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function deleteNote(title) {
  // Soft-delete: moves note to _trash/ on the server
  try {
    await api.delete(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function restoreNote(title) {
  // Uses /api/trash/ prefix to avoid FastAPI {title:path} routing conflicts
  try {
    const encodedTitle = title.split("/").map(encodeURIComponent).join("/");
    const response = await api.post(`api/trash/${encodedTitle}/restore`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function permanentDeleteNote(title) {
  // Uses /api/trash/ prefix to avoid FastAPI {title:path} routing conflicts
  try {
    const encodedTitle = title.split("/").map(encodeURIComponent).join("/");
    await api.delete(`api/trash/${encodedTitle}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function permanentDeleteArchivedNote(title) {
  // Uses /api/archive/ prefix to avoid FastAPI {title:path} routing conflicts
  try {
    const encodedTitle = title.split("/").map(encodeURIComponent).join("/");
    await api.delete(`api/archive/${encodedTitle}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getTags() {
  try {
    const response = await api.get("api/tags");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function listAttachments() {
  try {
    const response = await api.get("api/attachments");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function deleteAttachment(filename) {
  try {
    await api.delete(`api/attachments/${encodeURIComponent(filename)}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function createAttachment(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("api/attachments", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function archiveNote(title) {
  try {
    const response = await api.post(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}/archive`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function unarchiveNote(title) {
  try {
    const response = await api.post(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}/unarchive`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

// ========== PIN METHODS ==========
export async function pinNote(title) {
  try {
    const response = await api.post(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}/pin`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function unpinNote(title) {
  try {
    const response = await api.post(`api/notes/${title.split("/").map(encodeURIComponent).join("/")}/unpin`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Settings API ─────────────────────────────────────────────────────────────

export async function getCallouts() {
  try {
    const response = await api.get("api/settings/callouts");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveCallouts(callouts) {
  try {
    const response = await api.put("api/settings/callouts", callouts);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getPrefs() {
  try {
    const response = await api.get("api/settings/prefs");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function savePrefs(prefs) {
  try {
    const response = await api.put("api/settings/prefs", prefs);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getTagColors() {
  try {
    const response = await api.get("api/settings/tag-colors");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveTagColors(settings) {
  try {
    const response = await api.put("api/settings/tag-colors", settings);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getFolders() {
  try {
    const response = await api.get("api/folders");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Get notes in folder ──────────────────────────────────────────────────────
export async function getFolderNotes(folder) {
  try {
    const response = await api.get(`api/folders/${folder.split("/").map(encodeURIComponent).join("/")}/notes`);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Header colors API ────────────────────────────────────────────────────────
export async function getHeaderColors() {
  try {
    const response = await api.get("api/settings/header-colors");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveHeaderColors(colors) {
  try {
    const response = await api.put("api/settings/header-colors", colors);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Highlight colors API ─────────────────────────────────────────────────────
export async function getHighlightColors() {
  try {
    const response = await api.get("api/settings/highlight-colors");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveHighlightColors(colors) {
  try {
    const response = await api.put("api/settings/highlight-colors", colors);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getDefaultHighlight() {
  try {
    const response = await api.get("api/settings/default-highlight");
    return response.data.default;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveDefaultHighlight(defaultName) {
  try {
    const response = await api.put("api/settings/default-highlight", { default: defaultName });
    return response.data.default;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Table style API ──────────────────────────────────────────────────────────
export async function getTableStyle() {
  try {
    const response = await api.get("api/settings/table-style");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveTableStyle(style) {
  try {
    const response = await api.put("api/settings/table-style", style);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Quote style API ──────────────────────────────────────────────────────────
export async function getQuoteStyle() {
  try {
    const response = await api.get("api/settings/quote-style");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveQuoteStyle(style) {
  try {
    const response = await api.put("api/settings/quote-style", style);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// In client/api.js, add near the other get functions:

export async function getTemplates() {
  try {
    const response = await api.get("api/templates");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getTaskIcons() {
  try {
    const response = await api.get("api/settings/task-icons");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveTaskIcons(settings) {
  try {
    const response = await api.put("api/settings/task-icons", settings);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Maintenance API ───────────────────────────────────────────────────────────

export async function getMaintenanceStatus() {
  try {
    const response = await api.get("api/maintenance/status");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function emptyTrashNow(days = 0) {
  try {
    const response = await api.post("api/maintenance/trash/empty", { days });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getBackups() {
  try {
    const response = await api.get("api/maintenance/backups");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function createBackup(label = "manual") {
  try {
    const response = await api.post("api/maintenance/backups", { label });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function restoreBackup(filename) {
  try {
    const response = await api.post("api/maintenance/backups/restore", { filename });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function deleteBackup(filename) {
  try {
    await api.delete(`api/maintenance/backups/${encodeURIComponent(filename)}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

// ── Saved Searches API ────────────────────────────────────────────────────────

export async function getSavedSearches() {
  try {
    const response = await api.get("api/settings/saved-searches");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function saveSavedSearches(settings) {
  try {
    const response = await api.put("api/settings/saved-searches", settings);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}