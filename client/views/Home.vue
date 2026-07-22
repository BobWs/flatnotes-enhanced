<template>
  <div class="flex h-full justify-center">
    <div class="flex max-w-[500px] flex-1 flex-col items-center pt-[25vh]">
      <Logo class="mb-5" />

      <!-- Showcase mode: read-only notice -->
      <div
        v-if="globalStore.config.searchDisabled"
        class="mb-5 flex items-center gap-2 px-4 py-2.5 rounded-lg
               border border-theme-brand/30 bg-theme-brand/8
               text-sm text-theme-text-muted text-center"
      >
        <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 text-theme-brand/70">
          <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
        </svg>
        These are read-only shared notes. Nothing can be edited.
      </div>

      <SearchInput v-if="!globalStore.config.searchDisabled" class="mb-5 shadow-[0_0_20px] shadow-theme-shadow" />
      <LoadingIndicator
        ref="loadingIndicator"
        class="flex min-h-56 flex-col items-center"
        hideLoader
      >
        <p
          v-if="notes.length > 0"
          class="mb-2 text-xs font-bold uppercase text-theme-text-very-muted"
        >
          {{ globalStore.config.quickAccessTitle }}
        </p>
        <!--
          Wrapper div is relative + auto-width so items-center on the parent
          still centers it. The eye button sits absolutely to the right,
          completely outside the flow, so it never affects centering.
        -->
        <div
          v-for="note in notes.slice(0, globalStore.config.quickAccessLimit)"
          :key="note.title"
          class="relative mb-1 group"
        >
          <RouterLink :to="{ name: 'note', params: { title: note.title } }">
            <CustomButton :label="note.title" />
          </RouterLink>
          <button
            v-if="previewEnabled"
            @click.stop="onPreviewClick($event, note.title)"
            class="absolute top-1/2 -translate-y-1/2 -right-8 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded text-theme-text-muted hover:text-theme-brand hover:bg-theme-background-elevated"
            title="Preview note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"/>
            </svg>
          </button>
        </div>
        <RouterLink
          v-if="notes.length > globalStore.config.quickAccessLimit"
          :to="{
            name: 'search',
            query: {
              term: globalStore.config.quickAccessTerm,
              sortBy: showMoreSort,
            },
          }"
          title="Show more"
          ><CustomButton :iconPath="mdiDotsHorizontal"
        /></RouterLink>
      </LoadingIndicator>
    </div>

    <!-- Preview popup -->
    <NotePreview ref="previewPopup" :noteTitle="currentPreviewNote" :target="previewTarget" />
  </div>
</template>

<script setup>
import { mdiDotsHorizontal } from "@mdi/js";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { apiErrorHandler, getNotes } from "../api.js";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import Logo from "../components/Logo.vue";
import NotePreview from "../components/NotePreview.vue";
import { searchSortOptions } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import SearchInput from "../partials/SearchInput.vue";

const globalStore = useGlobalStore();
const loadingIndicator = ref();
const notes = ref([]);
const toast = useToast();

// Fallback chain for "Show more" sort:
// 1. User preference (Settings → Default note sort)
// 2. Docker env (FLATNOTES_QUICK_ACCESS_SORT)
// 3. App default (title)
const SORT_MAP = {
  lastModified: searchSortOptions.lastModified,
  title:        searchSortOptions.title,
  titleDesc:    searchSortOptions.titleDesc,  
  score:        searchSortOptions.score,
};
const showMoreSort = computed(() => {
  const userPref = globalStore.notesDefaultSort;
  const envSort  = globalStore.config?.quickAccessSort;
  return SORT_MAP[userPref] ?? SORT_MAP[envSort] ?? searchSortOptions.title;
});

// Preview state
const previewEnabled = ref(true);
const previewPopup = ref(null);
const currentPreviewNote = ref("");
const previewTarget = ref(null);

function loadPreviewSetting() {
  const stored = localStorage.getItem("fn_preview_enabled");
  previewEnabled.value = stored === null ? true : stored === "true";
}

function onPreviewClick(event, noteTitle) {
  if (!previewEnabled.value) return;
  currentPreviewNote.value = noteTitle;
  previewTarget.value = event.currentTarget;
  setTimeout(() => {
    previewPopup.value?.show();
  }, 50);
}

function init() {
  if (globalStore.config.quickAccessHide || globalStore.config.searchDisabled) {
    return;
  }
  getNotes(
    globalStore.config.quickAccessTerm,
    globalStore.config.quickAccessSort,
    // Order by ascending if sorting by title, descending otherwise.
    globalStore.config.quickAccessSort === "title"
      ? "asc"
      : "desc",
    // Limit is increased by 1 to check if there are more notes than the limit.
    globalStore.config.quickAccessLimit + 1,
  )
    .then((data) => {
      notes.value = data;
      loadingIndicator.value.setLoaded();
    })
    .catch((error) => {
      loadingIndicator.value.setFailed();
      apiErrorHandler(error, toast);
    });
}

// Watch to allow for delayed config load.
watch(() => globalStore.config.hideRecentlyModified, init);
onMounted(() => {
  loadPreviewSetting();
  init();
});
</script>