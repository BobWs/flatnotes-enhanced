<template>
  <LoadingIndicator ref="loadingIndicator" class="mx-auto flex h-full max-w-[999px] flex-col">

    <!-- Confirm single permanent delete -->
    <ConfirmModal
      v-model="isConfirmDeleteVisible"
      title="Permanently Delete"
      :message="`Permanently delete '${displayName(pendingDeleteTitle)}'? This cannot be undone.`"
      confirmButtonText="Delete Forever"
      confirmButtonStyle="danger"
      @confirm="doPermanentDelete"
    />

    <!-- Confirm restore -->
    <ConfirmModal
      v-model="isConfirmRestoreVisible"
      title="Restore Note"
      :message="`Restore '${displayName(pendingRestoreTitle)}' to your notes?`"
      confirmButtonText="Restore"
      confirmButtonStyle="cta"
      @confirm="doRestore"
    />

    <!-- Confirm empty archive -->
    <ConfirmModal
      v-model="isConfirmEmptyVisible"
      title="Empty Archive"
      message="Permanently delete all notes in archive? This cannot be undone."
      confirmButtonText="Empty Archive"
      confirmButtonStyle="danger"
      @confirm="doEmptyArchive"
    />

    <!-- Header row -->
    <div class="flex items-center justify-between mb-4 gap-3 flex-wrap">
      <div class="shrink-0">
        <h1 class="text-2xl font-semibold text-theme-text">Archive</h1>
        <p class="text-sm text-theme-text-muted mt-0.5">
          {{ filteredResults.length }}
          <template v-if="filteredResults.length !== results.length">
            of {{ results.length }}
          </template>
          archived note{{ filteredResults.length !== 1 ? 's' : '' }}
        </p>
      </div>

      <!-- Search + sort + action controls -->
      <div class="flex items-center gap-2 flex-wrap justify-end ml-auto">

        <!-- Search field -->
        <div class="relative">
          <svg viewBox="0 0 24 24" class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 fill-current text-theme-text-very-muted pointer-events-none">
            <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search archive…"
            class="pl-8 pr-8 py-1.5 rounded text-sm bg-theme-background-elevated border border-theme-border
                   text-theme-text placeholder:text-theme-text-very-muted
                   focus:outline-none focus:border-theme-brand transition-colors w-52"
          />
          <!-- Clear button -->
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-theme-text-very-muted hover:text-theme-text transition-colors"
            title="Clear search"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>

        <!-- Sort dropdown -->
        <div class="relative">
          <select
            v-model="sortKey"
            class="appearance-none pl-3 pr-7 py-1.5 rounded text-sm bg-theme-background-elevated
                   border border-theme-border text-theme-text-muted
                   focus:outline-none focus:border-theme-brand transition-colors cursor-pointer"
            title="Sort by"
          >
            <option value="lastModified">Last modified</option>
            <option value="title">Title A–Z</option>
            <option value="titleDesc">Title Z–A</option>
            <option value="oldest">Oldest first</option>
          </select>
          <!-- Chevron icon -->
          <svg viewBox="0 0 24 24" class="absolute right-1.5 top-1/2 -translate-y-1/2 w-4 h-4 fill-current text-theme-text-very-muted pointer-events-none">
            <path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
          </svg>
        </div>

        <!-- Empty archive button -->
        <button
          v-if="results.length > 0"
          @click="confirmEmptyArchive"
          class="inline-flex items-center gap-1 px-3 py-1.5 rounded text-sm font-medium
                 text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
          title="Empty archive"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path :d="mdiDeleteForever"/>
          </svg>
          Empty
        </button>

        <!-- Refresh -->
        <button
          @click="loadArchive"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
                 bg-theme-background-elevated hover:bg-theme-border border border-theme-border transition-colors text-theme-text-muted"
          title="Refresh"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"
               :class="{ 'animate-spin': loading }">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
          Refresh
        </button>
      </div>
    </div>

    <!-- Empty state: no archived notes at all -->
    <div
      v-if="!loading && results.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M3,3H21V7H3V3M4,8H20V21H4V8M9,11V13H15V11H9Z"/>
      </svg>
      <p class="text-sm">Archive is empty</p>
      <p class="text-xs text-theme-text-very-muted">Archived notes will appear here</p>
    </div>

    <!-- Empty state: no results after filtering -->
    <div
      v-else-if="!loading && results.length > 0 && filteredResults.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
      </svg>
      <p class="text-sm">No archived notes match your search.</p>
      <button
        @click="clearFilters"
        class="text-xs text-theme-brand hover:underline"
      >Clear search</button>
    </div>

    <!-- Archive list -->
    <div v-else class="flex flex-col gap-3 overflow-y-auto flex-1 pb-4">
      <div
        v-for="note in filteredResults"
        :key="note.title"
        class="rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <!-- Left side: info -->
        <div class="min-w-0 flex-1 cursor-pointer" @click="previewNote(note.title)">
          <!-- Folder breadcrumb -->
          <p v-if="displayFolder(note.title)" class="text-xs text-theme-text-very-muted mb-0.5">
            {{ displayFolder(note.title) }}
          </p>
          <!-- Title -->
          <p class="font-medium text-theme-text truncate hover:text-theme-brand transition-colors">
            {{ displayName(note.title) }}
          </p>
          <!-- Date -->
          <p class="text-xs text-theme-text-muted mt-0.5">{{ note.lastModifiedAsString }}</p>
        </div>

        <!-- Right side: action buttons -->
        <div class="flex gap-2 shrink-0">
          <!-- Restore button -->
          <button
            @click="promptRestore(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            title="Restore note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiRestore"/>
            </svg>
            Restore
          </button>

          <!-- Delete button -->
          <button
            @click="promptDelete(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
            title="Permanently delete note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiDeleteForever"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

  </LoadingIndicator>
</template>

<script setup>
import { mdiDeleteForever, mdiRestore } from "@mdi/js";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import {
  apiErrorHandler,
  getNotes,
  unarchiveNote,
  permanentDeleteArchivedNote,
} from "../api.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import { getToastOptions } from "../helpers.js";

const loadingIndicator = ref();
const loading = ref(false);
const results = ref([]);
const toast = useToast();
const router = useRouter();

const isConfirmDeleteVisible = ref(false);
const isConfirmRestoreVisible = ref(false);
const isConfirmEmptyVisible = ref(false);
const pendingDeleteTitle = ref("");
const pendingRestoreTitle = ref("");

// ── Search / sort state ───────────────────────────────────────────────────────
const searchQuery = ref("");
const sortKey = ref("lastModified"); // 'lastModified' | 'title' | 'titleDesc' | 'oldest'

function clearFilters() {
  searchQuery.value = "";
}

// ── Derived list ──────────────────────────────────────────────────────────────
const filteredResults = computed(() => {
  let list = results.value;

  // 1. Text search (title)
  const q = searchQuery.value.trim().toLowerCase();
  if (q) {
    list = list.filter((n) =>
      displayName(n.title).toLowerCase().includes(q) ||
      displayFolder(n.title).toLowerCase().includes(q)
    );
  }

  // 2. Sort
  list = [...list].sort((a, b) => {
    if (sortKey.value === "title") {
      return displayName(a.title).localeCompare(displayName(b.title), undefined, { sensitivity: "base" });
    } else if (sortKey.value === "titleDesc") {
      return displayName(b.title).localeCompare(displayName(a.title), undefined, { sensitivity: "base" });
    } else if (sortKey.value === "oldest") {
      return (a.lastModified || 0) - (b.lastModified || 0);
    }
    // Default: lastModified descending
    return (b.lastModified || 0) - (a.lastModified || 0);
  });

  return list;
});

// ── Helpers ───────────────────────────────────────────────────────────────────

// Strip _archive/ prefix then return just the filename
function displayName(title) {
  const stripped = (title || "").replace(/^_archive\//, "");
  const parts = stripped.split("/");
  return parts[parts.length - 1];
}

// Strip _archive/ prefix then return only the folder portion (if any)
function displayFolder(title) {
  const stripped = (title || "").replace(/^_archive\//, "");
  const idx = stripped.lastIndexOf("/");
  return idx > -1 ? stripped.slice(0, idx) : "";
}

function previewNote(title) {
  router.push({ name: "note", params: { title } });
}

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadArchive() {
  loading.value = true;
  loadingIndicator.value?.setLoading();
  try {
    const all = await getNotes("*", "lastModified", "desc", null, true, false);
    results.value = all.filter((n) => n.title.startsWith("_archive/"));
    loadingIndicator.value?.setLoaded();
  } catch (error) {
    loadingIndicator.value?.setFailed();
    apiErrorHandler(error, toast);
  } finally {
    loading.value = false;
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────

function promptRestore(title) {
  pendingRestoreTitle.value = title;
  isConfirmRestoreVisible.value = true;
}

async function doRestore() {
  try {
    await unarchiveNote(pendingRestoreTitle.value);
    toast.add(getToastOptions(`'${displayName(pendingRestoreTitle.value)}' restored ✓`, "Success", "success"));
    pendingRestoreTitle.value = "";
    await loadArchive();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

function promptDelete(title) {
  pendingDeleteTitle.value = title;
  isConfirmDeleteVisible.value = true;
}

async function doPermanentDelete() {
  try {
    await permanentDeleteArchivedNote(pendingDeleteTitle.value);
    toast.add(getToastOptions("Permanently deleted ✓", "Success", "success"));
    pendingDeleteTitle.value = "";
    await loadArchive();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

function confirmEmptyArchive() {
  isConfirmEmptyVisible.value = true;
}

async function doEmptyArchive() {
  try {
    for (const note of results.value) {
      await permanentDeleteArchivedNote(note.title);
    }
    toast.add(getToastOptions("Archive emptied ✓", "Success", "success"));
    await loadArchive();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

onMounted(loadArchive);
</script>