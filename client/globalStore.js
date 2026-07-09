import { defineStore } from "pinia";
import { ref } from "vue";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const pinnedVersion = ref(0); // increment to trigger re-check of pinned notes
  // Whether to show text labels next to nav/toolbar buttons.
  // true = labels visible (default), false = icons only.
  const showButtonLabels = ref(true);
  // Custom home note: when enabled the Home button navigates to a specific note
  // instead of the default quick-access home page.
  const homeNoteEnabled = ref(false);
  const homeNote = ref('');
  // Note view mode: 'normal' = centered container (default), 'fullscreen' = expanded width
  const noteViewMode = ref('normal');
  // Default sort for "All Notes" page: '' | 'title' | 'lastModified' | 'score'
  // Empty string means "app default" (falls back to title sort).
  const notesDefaultSort = ref('');
  // PWA offline caching toggle — when true, the service worker caches API responses.
  const offlineCacheEnabled = ref(false);
  // Current server reachability (true = server responding, false = unreachable).
  // Starts optimistically true; the heartbeat poller in App.vue corrects it
  // within the first poll cycle (5 s timeout). This avoids a false offline
  // flash on startup when navigator.onLine would have been unreliable anyway.
  const isOnline = ref(true);
  // Date formatting preferences.
  // dateLocale: 'system' uses the browser/OS default; any BCP 47 tag is valid.
  // dateStyle:  'short' | 'medium' | 'long'  (default: 'medium')
  const dateLocale = ref('system');
  const dateStyle  = ref('medium');
  // Saved searches — mirrored from backend so sidebar stays reactive.
  // savedSearchesEnabled: whether to show the section in the sidebar.
  // savedSearches: the ordered array of {id, name, query, sort_by, ...} objects.
  const savedSearchesEnabled = ref(false);
  const savedSearches = ref([]);

  function bumpPinned() {
    pinnedVersion.value++;
  }

  return {
    config,
    pinnedVersion,
    bumpPinned,
    showButtonLabels,
    homeNoteEnabled,
    homeNote,
    noteViewMode,
    notesDefaultSort,
    offlineCacheEnabled,
    isOnline,
    dateLocale,
    dateStyle,
    savedSearchesEnabled,
    savedSearches,
  };
});
