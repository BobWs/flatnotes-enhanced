<template>
  <!--
    Outer shell is always full-width so the sidebar's fixed 288px offset
    eats into the outer padding/margin space, NOT into the note content.
    Inner centering is applied per-route via the contentClass computed.
  -->
  <LoadingIndicator
    ref="loadingIndicator"
    class="flex h-screen flex-col py-4 print:max-w-full w-full px-2 md:px-4"
  >
    <PrimeToast />
    <SearchModal v-model="isSearchModalVisible" />

    <!-- Tag Sidebar (fixed-position, overlays content) -->
    <TagSidebar
      :isOpen="isSidebarOpen"
      @close="isSidebarOpen = false"
      @tagsChanged="handleTagsChanged"
    />

    <!-- Folder Sidebar (fixed-position, overlays content) -->
    <FolderSidebar
      :isOpen="isFolderSidebarOpen"
      @close="isFolderSidebarOpen = false"
    />

    <!-- Main content area — shifts right when sidebar opens. The outer shell is
         full-width so the 288px shift is absorbed by space outside the inner
         centering wrapper rather than shrinking the note content. -->
    <div
      :class="[
        'flex flex-col flex-1 min-h-0 transition-all duration-300',
        (isSidebarOpen || isFolderSidebarOpen) ? 'md:ml-72' : 'md:ml-0',
      ]"
    >
      <!--
        Inner centering wrapper — constrains both the NavBar and the page content
        to the same max-width so they always stay aligned with each other.

        Normal mode  : max-w-[999px] mx-auto  (centered column, same width as before)
        Fullscreen on note routes: no max-w — full available width with outer padding
        Non-note pages: always max-w-[999px] mx-auto regardless of view mode
      -->
      <div
        :class="[
          'flex flex-col flex-1 min-h-0',
          contentWidthClass,
        ]"
      >
        <!-- NavBar — always shrink-0, inherits the same width as content below -->
        <div class="shrink-0">
          <NavBar
            v-if="showNavBar"
            ref="navBar"
            :class="{ 'print:hidden': route.name == 'note' }"
            :hide-logo="true"
            :isSidebarOpen="isSidebarOpen"
            :isFolderSidebarOpen="isFolderSidebarOpen"
            @toggleSearchModal="toggleSearchModal"
            @toggleSidebar="openTagSidebar"
            @toggleFolderSidebar="openFolderSidebar"
          />
        </div>

        <!-- Note routes: flex column so Note.vue's h-full resolves correctly -->
        <div
          v-if="isNoteRoute"
          class="flex-1 min-h-0 flex flex-col"
        >
          <RouterView :activeTags="activeTags" />
        </div>

        <!-- Non-note pages: scrollable, content has its own internal max-w -->
        <div
          v-else
          class="flex-1 overflow-y-auto min-h-0"
        >
          <RouterView :activeTags="activeTags" />
        </div>

      </div>
    </div>
  </LoadingIndicator>
</template>

<script setup>
import Mousetrap from "mousetrap";
import "mousetrap/plugins/global-bind/mousetrap-global-bind";
import { useToast } from "primevue/usetoast";
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { RouterView, useRoute } from "vue-router";

import { apiErrorHandler, getConfig, getPrefs } from "./api.js";
import PrimeToast from "./components/PrimeToast.vue";
import TagSidebar from "./components/TagSidebar.vue";
import FolderSidebar from "./components/FolderSidebar.vue";
import { useGlobalStore } from "./globalStore.js";
import { loadTheme, initThemeListener, cleanupThemeListener } from "./helpers.js";
import NavBar from "./partials/NavBar.vue";
import SearchModal from "./partials/SearchModal.vue";
import LoadingIndicator from "./components/LoadingIndicator.vue";
import router from "./router.js";
import { initSettingsStore } from "./calloutStore.js";
import { loadTagColors } from "./tagColorStore.js";

const globalStore = useGlobalStore();
const isSearchModalVisible = ref(false);
// Persist sidebar open/closed state across page reloads
// ── Sidebar state — both persisted, mutually exclusive ───────────────────────
const isSidebarOpen = ref(localStorage.getItem("fn_sidebar_open") === "true");
const isFolderSidebarOpen = ref(localStorage.getItem("fn_folder_sidebar_open") === "true");
const activeTags = ref([]);

// Persist both sidebar states whenever they change
watch(isSidebarOpen, (val) => {
  localStorage.setItem("fn_sidebar_open", String(val));
});
watch(isFolderSidebarOpen, (val) => {
  localStorage.setItem("fn_folder_sidebar_open", String(val));
});
const loadingIndicator = ref();
const navBar = ref();
const route = useRoute();
const toast = useToast();

// '/' to search
Mousetrap.bind("/", () => {
  if (route.name !== "login") {
    toggleSearchModal();
    return false;
  }
});

// 'CTRL + ALT/OPT + N' to create new note
Mousetrap.bindGlobal("ctrl+alt+n", () => {
  if (route.name !== "login") {
    router.push({ name: "new" });
    return false;
  }
});

// 'CTRL + ALT/OPT + H' to go to home
Mousetrap.bindGlobal("ctrl+alt+h", () => {
  if (route.name !== "login") {
    if (globalStore.homeNoteEnabled && globalStore.homeNote) {
      router.push({ name: "note", params: { title: globalStore.homeNote } });
    } else {
      router.push({ name: "home" });
    }
    return false;
  }
});

// 'CTRL + ALT/OPT + T' to toggle tag sidebar (mutually exclusive)
Mousetrap.bindGlobal("ctrl+alt+t", () => {
  if (route.name !== "login") {
    openTagSidebar();
    return false;
  }
});

getConfig()
  .then(async (data) => {
    globalStore.config = data;
    await initSettingsStore();
    // Load show_button_labels preference so it persists across page refreshes.
    // We do this after auth is confirmed (getConfig succeeds only when authenticated).
    try {
      const prefs = await getPrefs();
      globalStore.showButtonLabels  = prefs.show_button_labels !== false;
      globalStore.homeNoteEnabled   = prefs.home_note_enabled === true;
      globalStore.homeNote          = prefs.home_note || '';
      const vm = prefs.notes_default_view;
      globalStore.noteViewMode      = (vm === 'fullscreen' || vm === 'wide') ? vm : 'normal';
      globalStore.notesDefaultSort  = prefs.notes_default_sort || '';
      // If a custom home note is configured and we're currently on the
      // default home route, navigate there immediately on startup.
      if (
        globalStore.homeNoteEnabled &&
        globalStore.homeNote &&
        router.currentRoute.value.name === 'home'
      ) {
        router.replace({ name: 'note', params: { title: globalStore.homeNote } });
      }
    } catch {
      // Non-fatal: defaults apply
    }
    loadingIndicator.value.setLoaded();
  })
  .catch((error) => {
    apiErrorHandler(error, toast);
    loadingIndicator.value.setFailed();
  });

const showNavBar = computed(() => {
  return route.name !== "login";
});

// Note routes are the only ones that expand beyond normal width
const isNoteRoute = computed(() => route.name === 'note' || route.name === 'new');

// True when fullscreen mode is active AND we're on a note route
const isFullscreenNoteRoute = computed(() =>
  globalStore.noteViewMode === 'fullscreen' && isNoteRoute.value
);

// True when wide mode is active AND we're on a note route
const isWideNoteRoute = computed(() =>
  globalStore.noteViewMode === 'wide' && isNoteRoute.value
);

// The max-width class applied to the shared NavBar + content centering wrapper.
// Normal : max-w-[999px]  — original behaviour, unchanged
// Wide   : max-w-[1400px] — comfortable reading width on large desktops
// Full   : w-full         — uses full available width (outer padding provides breathing room)
const contentWidthClass = computed(() => {
  if (isFullscreenNoteRoute.value) return 'w-full';
  if (isWideNoteRoute.value)       return 'max-w-[1400px] w-full mx-auto';
  return 'max-w-[999px] w-full mx-auto';
});

function toggleSearchModal() {
  isSearchModalVisible.value = !isSearchModalVisible.value;
}

// ── Sidebar mutual-exclusion helpers ─────────────────────────────────────────
// Opening one sidebar always closes the other so they never overlap.
// Clicking the button of an already-open sidebar closes it (toggle behaviour).
function openTagSidebar() {
  if (isSidebarOpen.value) {
    // Already open — close it
    isSidebarOpen.value = false;
  } else {
    isFolderSidebarOpen.value = false;  // close folder sidebar first
    isSidebarOpen.value = true;
  }
}

function openFolderSidebar() {
  if (isFolderSidebarOpen.value) {
    // Already open — close it
    isFolderSidebarOpen.value = false;
  } else {
    isSidebarOpen.value = false;  // close tag sidebar first
    isFolderSidebarOpen.value = true;
  }
}

function handleTagsChanged(tags) {
  activeTags.value = tags;
  if (tags.length > 0) {
    // For each selected tag, use a Whoosh prefix wildcard query:
    // "tags:bookmark*" matches both "bookmark" (exact) and "bookmark/todo" (nested).
    // This means clicking "bookmark" shows notes with #bookmark AND #bookmark/todo etc.
    // Multiple tags use OR logic.
    const tagQuery = tags.map((t) => `tags:${t}*`).join(" OR ");
    router.push({ name: "search", query: { term: tagQuery } });
  }
}

// Initialize theme on mount
onMounted(() => {
  loadTheme();
loadTagColors(); // pre-load tag color config so chips render correctly on first paint
  initThemeListener();
});

// Cleanup on unmount
onUnmounted(() => {
  cleanupThemeListener();
});
</script>