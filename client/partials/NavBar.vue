<template>
  <nav class="mb-2 md:mb-2">

    <!-- ── Single-row layout on sm+ (original behaviour) ── -->
    <div class="nav-buttons hidden sm:flex items-start justify-end gap-1">
      <CustomButton :iconPath="mdiHome" label="Home" @click="goHome" title="Go home (Ctrl+Alt+H)" :forceLabel="false" />

      <button
        v-if="showNewButton && !globalStore.config.searchDisabled"
        @click="openNewNoteModal"
        title="Create a new note (Ctrl+Alt+N)"
        class="text-nowrap rounded px-2 py-1 inline-flex items-center gap-1
               bg-theme-background text-theme-text-muted
               hover:bg-theme-background-elevated active:bg-theme-background-elevated touch-manipulation"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current flex-shrink-0">
          <path d="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10-4.48 10-10S17.52,2 12,2 M12,20c-4.41,0-8-3.59-8-8s3.59-8,8-8 8,3.59 8,8-3.59,8-8,8 M13,7h-2v4H7v2h4v4h2v-4h4v-2h-4V7z"/>
        </svg>
        <span v-show="globalStore.showButtonLabels" class="hidden sm:inline">New Note</span>
      </button>

      <CustomButton v-if="hasPinnedNotes && !globalStore.config.searchDisabled" :iconPath="mdiBookmark" label="Bookmarks" @click="goToPinned" title="View pinned notes" :forceLabel="false" />
      <CustomButton v-if="!globalStore.config.searchDisabled" :iconPath="mdiTagMultiple" label="Tags" @click="$emit('toggleSidebar')"
        :title="isSidebarOpen ? 'Close tag sidebar (Ctrl+Alt+T)' : 'Open tag sidebar (Ctrl+Alt+T)'"
        :class="{ 'sidebar-active': isSidebarOpen }" :forceLabel="false" />
      <CustomButton :iconPath="mdiFolderMultiple" label="Folders" @click="$emit('toggleFolderSidebar')"
        :title="isFolderSidebarOpen ? 'Close folder browser' : 'Browse folders'"
        :class="{ 'sidebar-active': isFolderSidebarOpen }" :forceLabel="false" />

      <CustomButton :iconPath="mdilMenu" label="Menu" @click="toggleMenu" title="Open menu" :forceLabel="false" />
      <PrimeMenu ref="menu" :model="menuItems" :popup="true" />
    </div>

    <!-- ── Mobile layout: two rows when labels on, single row when icons only ── -->
    <div
      class="nav-buttons sm:hidden"
      :class="globalStore.showButtonLabels
        ? 'flex flex-col items-end gap-0.5'
        : 'flex flex-row items-center justify-end gap-1'"
    >
      <!-- Row 1: primary actions — Home, New Note, Bookmarks -->
      <!-- In single-row mode this div is a transparent passthrough (contents flow into parent) -->
      <div :class="globalStore.showButtonLabels ? 'flex items-center gap-1' : 'contents'">
        <CustomButton :iconPath="mdiHome" label="Home" @click="goHome" title="Go home" :forceLabel="false" />

        <button
          v-if="showNewButton && !globalStore.config.searchDisabled"
          @click="openNewNoteModal"
          title="Create a new note"
          class="text-nowrap rounded px-2 py-1 inline-flex items-center gap-1
                 bg-theme-background text-theme-text-muted
                 hover:bg-theme-background-elevated active:bg-theme-background-elevated touch-manipulation"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current flex-shrink-0">
            <path d="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10-4.48 10-10S17.52,2 12,2 M12,20c-4.41,0-8-3.59-8-8s3.59-8,8-8 8,3.59 8,8-3.59,8-8,8 M13,7h-2v4H7v2h4v4h2v-4h4v-2h-4V7z"/>
          </svg>
        </button>

        <CustomButton v-if="hasPinnedNotes && !globalStore.config.searchDisabled" :iconPath="mdiBookmark" label="Bookmarks" @click="goToPinned" title="View pinned notes" :forceLabel="false" />
      </div>

      <!-- Row 2: navigation/utility — Tags, Folders, Menu -->
      <div :class="globalStore.showButtonLabels ? 'flex items-center gap-1' : 'contents'">
        <CustomButton v-if="!globalStore.config.searchDisabled" :iconPath="mdiTagMultiple" label="Tags" @click="$emit('toggleSidebar')"
          :title="isSidebarOpen ? 'Close tag sidebar' : 'Open tag sidebar'"
          :class="{ 'sidebar-active': isSidebarOpen }" :forceLabel="false" />
        <CustomButton :iconPath="mdiFolderMultiple" label="Folders" @click="$emit('toggleFolderSidebar')"
          :title="isFolderSidebarOpen ? 'Close folder browser' : 'Browse folders'"
          :class="{ 'sidebar-active': isFolderSidebarOpen }" :forceLabel="false" />
        <CustomButton :iconPath="mdilMenu" label="Menu" @click="toggleMenu" title="Open menu" :forceLabel="false" />
        <PrimeMenu ref="menuMobile" :model="menuItems" :popup="true" />
      </div>
    </div>

    <!-- Template Chooser Modal -->
    <div
      v-if="templateModalVisible"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="templateModalVisible = false"
    >
      <div class="bg-theme-background rounded-t-2xl sm:rounded-lg shadow-xl w-full sm:w-96 sm:max-w-full p-4 border border-theme-border">
        <h3 class="text-lg font-semibold text-theme-text mb-3">Create New Note</h3>
        <div class="max-h-[60vh] sm:max-h-64 overflow-y-auto">
          <div class="space-y-1">
            <button
              @click="createEmptyNote"
              class="w-full flex items-center gap-3 px-3 py-3 sm:py-2 rounded hover:bg-theme-background-elevated active:bg-theme-background-elevated transition-colors text-left touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted flex-shrink-0">
                <path d="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10-4.48 10-10S17.52,2 12,2 M12,20c-4.41,0-8-3.59-8-8s3.59-8,8-8 8,3.59 8,8-3.59,8-8,8 M13,7h-2v4H7v2h4v4h2v-4h4v-2h-4V7z"/>
              </svg>
              <span class="text-sm text-theme-text">Empty note</span>
            </button>
            <div v-if="templatesLoading" class="px-3 py-2 text-xs text-theme-text-very-muted">Loading templates…</div>
            <div v-else-if="templates.length === 0" class="px-3 py-2 text-xs text-theme-text-very-muted">No templates yet. Create a note in the <code class="bg-theme-background-elevated px-1 rounded">_templates</code> folder to use it here.</div>
            <button
              v-for="tpl in templates"
              :key="tpl"
              @click="createFromTemplate(tpl)"
              class="w-full flex items-center gap-3 px-3 py-3 sm:py-2 rounded hover:bg-theme-background-elevated active:bg-theme-background-elevated transition-colors text-left touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted flex-shrink-0">
                <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z"/>
              </svg>
              <span class="text-sm text-theme-text">{{ tpl }}</span>
            </button>
          </div>
        </div>
        <div class="mt-4 flex justify-end">
          <button
            @click="templateModalVisible = false"
            class="px-4 py-2 rounded bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-sm text-theme-text touch-manipulation"
          >Cancel</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { mdiHome, mdiTagMultiple, mdiBookmark, mdiFolderMultiple, mdiCog, mdiPaperclip, mdiDeleteClock, mdiArchive, mdiFileDocumentOutline, mdiThemeLightDark, mdiShareVariant } from "@mdi/js";
import {
  mdilLogout,
  mdilMagnify,
  mdilMenu,
  mdilNoteMultiple,
  mdilPlusCircle,
} from "@mdi/light-js";
import { computed, ref, onMounted, onUnmounted, watch } from "vue";
import { RouterLink, useRouter } from "vue-router";

import CustomButton from "../components/CustomButton.vue";
import PrimeMenu from "../components/PrimeMenu.vue";
import { authTypes, params, searchSortOptions } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { setDarkThemeOn, setDarkThemeOff, followSystemTheme, getCurrentThemeMode } from "../helpers.js";
import { clearStoredToken } from "../tokenStorage.js";
import { getTags, getTemplates } from "../api.js";

const globalStore = useGlobalStore();
const menu = ref();
const menuMobile = ref();
const router = useRouter();

const props = defineProps({
  isSidebarOpen: Boolean,
  isFolderSidebarOpen: Boolean,
});

const emit = defineEmits(["toggleSearchModal", "toggleSidebar", "toggleFolderSidebar"]);

const hasPinnedNotes = ref(false);

// ── Theme cycle ───────────────────────────────────────────────────────────────
const themeMode = ref(getCurrentThemeMode());
let _navThemeObserver = null;

const themeButtonTitle = computed(() => {
  if (themeMode.value === 'light') return 'Light theme — click for Dark';
  if (themeMode.value === 'dark')  return 'Dark theme — click to follow OS';
  return 'Following OS theme — click for Light';
});

function cycleTheme() {
  if (themeMode.value === 'light')       { setDarkThemeOn();    themeMode.value = 'dark';   }
  else if (themeMode.value === 'dark')   { followSystemTheme(); themeMode.value = 'system'; }
  else                                   { setDarkThemeOff();   themeMode.value = 'light';  }
}

const templateModalVisible = ref(false);
const templates = ref([]);
const templatesLoading = ref(false);

async function checkPinned() {
  try {
    const tags = await getTags();
    hasPinnedNotes.value = tags && tags.pin > 0;
  } catch {
    hasPinnedNotes.value = false;
  }
}

watch(() => globalStore.pinnedVersion, checkPinned, { immediate: true });

onMounted(() => {
  checkPinned();
  _navThemeObserver = new MutationObserver(() => {
    themeMode.value = getCurrentThemeMode();
  });
  _navThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] });
});

onUnmounted(() => {
  if (_navThemeObserver) _navThemeObserver.disconnect();
});

// Helper to get dynamic theme label
function getThemeLabel() {
  const mode = themeMode.value;
  if (mode === "light") return "Light Theme";
  if (mode === "dark") return "Dark Theme";
  return "Auto Theme";
}

// Helper to get dynamic theme hover title
function getThemeTitle() {
  const mode = themeMode.value;
  if (mode === "light") return "Switch to Dark Theme";
  if (mode === "dark") return "Switch to Auto Theme (follows system)";
  return "Switch to Light Theme";
}

// Make menu items reactive with computed
const menuItems = computed(() => {
  const showcaseMode = globalStore.config.searchDisabled;
  return [
    {
      label: "Search",
      icon: mdilMagnify,
      command: () => emit("toggleSearchModal"),
      keyboardShortcut: "/",
      title: "Search notes (press / to open)",
      visible: !showcaseMode,
    },
    {
      label: "All Notes",
      icon: mdilNoteMultiple,
      command: () => {
        // Map the user's saved sort preference string to the numeric constant.
        // Falls back to title sort when no preference is set ("app default").
        const sortMap = {
          lastModified: searchSortOptions.lastModified,
          title:        searchSortOptions.title,
          titleDesc:    searchSortOptions.titleDesc,
          score:        searchSortOptions.score,        
        };
        const savedSort = globalStore.notesDefaultSort;
        const resolvedSort = sortMap[savedSort] ?? searchSortOptions.title;
        router.push({
          name: "search",
          query: {
            [params.searchTerm]: "*",
            [params.sortBy]: resolvedSort,
          },
        });
      },
      title: "View all notes",
      visible: !showcaseMode,
    },
    {
      label: "Templates",
      icon: mdiFileDocumentOutline,
      command: () => router.push({ name: "templates" }),
      title: "Manage note templates",
      visible: !showcaseMode,
    },
    {
      label: "Attachments",
      icon: mdiPaperclip,
      command: () => router.push({ name: "attachments" }),
      title: "View and manage attachments",
      visible: !showcaseMode,
    },
    {
      label: "Shared Links",
      icon: mdiShareVariant,
      command: () => router.push({ name: "shares" }),
      title: "Manage all share links",
      visible: !showcaseMode,
    },    
    {
      label: "Archive",
      icon: mdiArchive,
      command: () => router.push({ name: "archive" }),
      title: "View archived notes",
      visible: !showcaseMode,
    },
    {
      label: "Settings",
      icon: mdiCog,
      command: () => router.push({ name: "settings" }),
      title: "Application settings",
      visible: !showcaseMode,
    },
    {
      label: "Trash",
      icon: mdiDeleteClock,
      command: () => router.push({ name: "trash" }),
      title: "View deleted notes",
      visible: !showcaseMode,
    },
    {
      separator: true,
    },
    {
      label: getThemeLabel(),
      icon: mdiThemeLightDark,
      command: cycleTheme,
      title: getThemeTitle(),
    },
    {
      separator: true,
      visible: showLogOutButton,
    },
    {
      label: "Log Out",
      icon: mdilLogout,
      command: logOut,
      title: "Sign out of your account",
      visible: showLogOutButton,
    },
  ];
});

const showNewButton = computed(() => {
  return globalStore.config.authType !== authTypes.readOnly;
});

function goHome() {
  localStorage.removeItem("fn_active_tags");
  if (globalStore.homeNoteEnabled && globalStore.homeNote) {
    router.push({ name: "note", params: { title: globalStore.homeNote } });
  } else {
    router.push({ name: "home" });
  }
}

function goToPinned() {
  router.push({ name: "bookmarks" });
}

function logOut() {
  clearStoredToken();
  localStorage.clear();
  router.push({ name: "login" });
}

function toggleMenu(event) {
  // Toggle whichever PrimeMenu instance is currently in the DOM
  const activeMenu = menu.value || menuMobile.value;
  if (activeMenu) activeMenu.toggle(event);
}

function showLogOutButton() {
  return ![authTypes.none, authTypes.readOnly].includes(globalStore.config.authType);
}

async function openNewNoteModal() {
  templateModalVisible.value = true;
  if (templates.value.length === 0 && !templatesLoading.value) {
    templatesLoading.value = true;
    try {
      templates.value = await getTemplates();
    } catch {
      templates.value = [];
    } finally {
      templatesLoading.value = false;
    }
  }
}

function createEmptyNote() {
  templateModalVisible.value = false;
  router.push({ name: "new" });
}

function createFromTemplate(templateName) {
  templateModalVisible.value = false;
  router.push({ name: "new", query: { template: templateName } });
}
</script>

<style scoped>
.sidebar-active {
  color: rgb(var(--theme-brand));
  border-color: rgb(var(--theme-brand));
}

/* Mobile responsive adjustments */
@media (max-width: 640px) {
  /* Hide text labels on navbar buttons only — NOT modal buttons */
  .nav-buttons :deep(.custom-button span) {
    display: none;
  }

  /* Minimum 44×44px tap targets on navbar buttons only */
  .nav-buttons :deep(.custom-button) {
    padding: 0.5rem;
    min-width: 2.75rem;
    min-height: 2.75rem;
  }
}
</style>