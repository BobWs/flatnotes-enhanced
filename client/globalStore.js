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

  function bumpPinned() {
    pinnedVersion.value++;
  }

  return { config, pinnedVersion, bumpPinned, showButtonLabels, homeNoteEnabled, homeNote, noteViewMode, notesDefaultSort };
});