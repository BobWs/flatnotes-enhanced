<template>
  <div class="mx-auto flex h-full max-w-[999px] flex-col">
    <!-- Search Input -->
    <SearchInput :initialSearchTerm="props.searchTerm" class="mb-2" />

    <!-- Active folder filter banner -->
    <div
      v-if="props.folder"
      class="flex items-center justify-between mb-2 px-3 py-1.5 rounded-lg bg-theme-background-elevated border border-theme-border text-sm"
    >
      <span class="text-theme-text-muted">
        Folder: <span class="font-medium text-theme-text">{{ props.folder }}</span>
      </span>
      <button
        @click="clearFolder"
        class="text-xs text-theme-text-muted hover:text-theme-text transition-colors ml-2"
        title="Clear folder filter"
      >✕ clear</button>
    </div>

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Toolbar -->
      <div class="flex items-center justify-between mb-1">
        <label class="flex items-center gap-1.5 text-xs text-theme-text-muted cursor-pointer select-none">
          <input
            type="checkbox"
            v-model="showArchived"
            class="accent-theme-brand"
            @change="init"
          />
          Include archived
        </label>
        <div class="flex items-center gap-1">
          <CustomButton
            :label="`Sort By: ${sortByName}`"
            :iconPath="mdiSort"
            @click="toggleSortMenu"
          />
          <PrimeMenu ref="sortMenu" :model="menuItems" :popup="true" />
        </div>
      </div>

      <!-- Results -->
      <div
        v-for="result in displayResults"
        :key="result.title"
        class="mb-4 cursor-pointer rounded px-2 py-1 hover:bg-theme-background-elevated group"
      >
        <div class="flex items-start gap-2">
          <div class="flex-1 min-w-0">
            <RouterLink :to="{ name: 'note', params: { title: result.title } }">
              <!-- Folder breadcrumb -->
              <div v-if="resultFolder(result)" class="text-xs text-theme-text-very-muted mb-0.5">
                {{ resultFolder(result) }} /
              </div>
              <!-- Title + badges + tags -->
              <div class="flex flex-wrap items-center gap-1">
                <span v-html="result.titleHighlightsOrTitle" class="mr-1"></span>
                <span
                  v-if="result.title.startsWith('_archive/')"
                  class="text-xs rounded-full bg-theme-background-elevated border border-theme-border px-2 py-0.5 text-theme-text-muted"
                >archived</span>
                <Tag v-for="tag in result.tagMatches" :tag="tag" :key="tag" class="mr-1" />
              </div>
              <!-- Date + content snippet -->
              <div>
                <span class="text-theme-text-muted">{{ result.lastModifiedAsString }}</span>
                <span v-if="result.contentHighlights"> - </span>
                <span v-html="result.contentHighlights" class="text-theme-text-muted"></span>
              </div>
            </RouterLink>
          </div>
          
          <!-- Preview button -->
          <button
            v-if="previewEnabled"
            ref="previewButtonRefs"
            :data-note-title="result.title"
            @click.stop="onPreviewClick($event, result.title)"
            class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded text-theme-text-muted hover:text-theme-brand hover:bg-theme-background-elevated"
            title="Preview note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"/>
            </svg>
          </button>
        </div>
      </div>
    </LoadingIndicator>

    <!-- Preview popup -->
    <NotePreview ref="previewPopup" :noteTitle="currentPreviewNote" :target="previewTarget" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import { mdiMagnify, mdiSort } from "@mdi/js";

import { apiErrorHandler, getNotes } from "../api.js";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import NotePreview from "../components/NotePreview.vue";
import PrimeMenu from "../components/PrimeMenu.vue";
import Tag from "../components/Tag.vue";
import { params, searchSortOptions } from "../constants.js";
import SearchInput from "../partials/SearchInput.vue";

const props = defineProps({
  searchTerm: String,
  sortBy: {
    type: Number,
    default: searchSortOptions.score,
  },
  // If set, only show notes whose title starts with this folder path
  folder: {
    type: String,
    default: null,
  },
  // If true, pre-enable the "include archived" toggle (used by Archive menu link)
  initShowArchived: {
    type: Boolean,
    default: false,
  },
  // If true, show ONLY archived notes (Archive view)
  onlyArchived: {
    type: Boolean,
    default: false,
  },
});

const loadingIndicator = ref();
const results = ref([]);
const router = useRouter();
const sortMenu = ref();
const toast = useToast();
const showArchived = ref(props.initShowArchived);

// Preview state
const previewEnabled = ref(true); // Will be loaded from localStorage
const previewPopup = ref(null);
const currentPreviewNote = ref("");
const previewTarget = ref(null);

// Load preview setting from localStorage
function loadPreviewSetting() {
  const stored = localStorage.getItem("fn_preview_enabled");
  if (stored === null) {
    previewEnabled.value = true; // Default: enabled
  } else {
    previewEnabled.value = stored === "true";
  }
}

function onPreviewClick(event, noteTitle) {
  if (!previewEnabled.value) return;
  currentPreviewNote.value = noteTitle;
  previewTarget.value = event.currentTarget;
  // Small delay to let the target be properly set
  setTimeout(() => {
    previewPopup.value?.show();
  }, 50);
}

const sortByName = computed(() => ({
  [searchSortOptions.title]: "Title",
  [searchSortOptions.lastModified]: "Last Modified",
  [searchSortOptions.score]: "Score",
}[props.sortBy] ?? "Score"));

// Apply folder and/or archive filters client-side
const displayResults = computed(() => {
  let filtered = results.value;
  // Archive view: only notes inside _archive/
  if (props.onlyArchived) {
    filtered = filtered.filter((r) => r.title.startsWith("_archive/"));
  }
  // Folder view: only notes whose path starts with the given folder
  if (props.folder) {
    const prefix = props.folder.replace(/\/$/, "") + "/";
    filtered = filtered.filter((r) => r.title.startsWith(prefix));
  }
  return filtered;
});

function resultFolder(result) {
  const idx = result.title.lastIndexOf("/");
  return idx > -1 ? result.title.slice(0, idx) : "";
}

function clearFolder() {
  router.push({
    name: "search",
    query: { [params.searchTerm]: props.searchTerm, [params.sortBy]: props.sortBy },
  });
}

async function init() {
  loadingIndicator.value.setLoading();
  try {
    const data = await getNotes(
      props.searchTerm,
      undefined,
      undefined,
      undefined,
      showArchived.value,
    );
    results.value = sortResults(data);
    // After sorting, let the computed displayResults determine the visible count
    // Use nextTick to let Vue update displayResults before checking
    if (data.length > 0) {
      loadingIndicator.value.setLoaded();
    } else {
      loadingIndicator.value.setFailed("No Results", mdiMagnify);
    }
  } catch (error) {
    loadingIndicator.value.setFailed();
    apiErrorHandler(error, toast);
  }
}

function sortResults(data) {
  if (props.sortBy === searchSortOptions.title) {
    return [...data].sort((a, b) => a.title.localeCompare(b.title));
  } else if (props.sortBy === searchSortOptions.lastModified) {
    return [...data].sort((a, b) => b.lastModified - a.lastModified);
  } else {
    return [...data].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  }
}

function reSortResults() {
  results.value = sortResults(results.value);
}

function updateSortByParam(sortBy) {
  router.push({
    name: "search",
    query: {
      [params.searchTerm]: props.searchTerm,
      [params.sortBy]: sortBy,
      ...(props.folder ? { [params.folder]: props.folder } : {}),
    },
  });
}

const menuItems = [
  { label: "Sort By: Score", command: () => updateSortByParam(searchSortOptions.score) },
  { label: "Sort By: Title", command: () => updateSortByParam(searchSortOptions.title) },
  { label: "Sort By: Last Modified", command: () => updateSortByParam(searchSortOptions.lastModified) },
];

function toggleSortMenu(event) {
  sortMenu.value.toggle(event);
}

watch(() => props.searchTerm, init);
watch(() => props.folder, init);
watch(() => props.sortBy, reSortResults);
onMounted(() => {
  loadPreviewSetting();
  init();
});
</script>

<style>
.match {
  @apply text-theme-brand;
}
</style>