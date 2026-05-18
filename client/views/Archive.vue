<template>
  <div class="mx-auto flex h-full max-w-[999px] flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text">Archive</h1>
        <p class="text-xs text-theme-text-muted mt-0.5">
          {{ results.length }} archived note{{ results.length !== 1 ? 's' : '' }}
          · Notes moved here are hidden from regular search but can be restored or permanently deleted.
        </p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="results.length > 0"
          @click="confirmEmptyArchive"
          class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                 text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
          title="Empty archive"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
            <path :d="mdiDeleteForever"/>
          </svg>
          Empty Archive
        </button>
        <button
          @click="loadArchive"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
                 bg-theme-background-elevated hover:bg-theme-border transition-colors text-theme-text-muted"
          title="Refresh"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"
               :class="{ 'animate-spin': loading }">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
          Refresh
        </button>
      </div>
    </div>

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

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Empty state -->
      <div
        v-if="results.length === 0 && !loading"
        class="flex flex-col items-center justify-center py-16 text-theme-text-very-muted"
      >
        <svg viewBox="0 0 64 64" class="w-16 h-16 mb-3 opacity-40">
          <path fill="currentColor" d="M3,3H21V7H3V3M4,8H20V21H4V8M9,11V13H15V11H9M3,23H21V27H3V23M4,28H20V41H4V28M9,31V33H15V31H9M3,43H21V47H3V43M4,48H20V61H4V48M9,51V53H15V51H9Z"/>
        </svg>
        <p class="text-sm">Archive is empty</p>
        <p class="text-xs mt-1 text-theme-text-very-muted">Archived notes will appear here</p>
      </div>

      <!-- Archive items -->
      <div
        v-for="note in results"
        :key="note.title"
        class="mb-2 rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <div class="min-w-0 flex-1 cursor-pointer" @click="previewNote(note.title)">
          <p v-if="displayFolder(note.title)" class="text-xs text-theme-text-very-muted mb-0.5">
            {{ displayFolder(note.title) }}
          </p>
          <p class="font-medium text-theme-text truncate hover:text-theme-brand transition-colors">
            {{ displayName(note.title) }}
          </p>
          <p class="text-xs text-theme-text-muted mt-0.5">{{ note.lastModifiedAsString }}</p>
        </div>
        <div class="flex gap-2 shrink-0">
          <!-- Restore button (gray, matches Trash.vue) -->
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
          
          <!-- Delete button (RED, matches Trash.vue and Attachments.vue) -->
          <button
            @click="promptDelete(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
            title="Permanently delete note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiDeleteForever"/>
            </svg>
          <!--  Delete -->
          </button>
        </div>
      </div>
    </LoadingIndicator>
  </div>
</template>

<script setup>
import { mdiDeleteForever, mdiRestore } from "@mdi/js";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";
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

// Strip _archive/ prefix then return just the filename (no extension shown)
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

async function loadArchive() {
  loading.value = true;
  loadingIndicator.value?.setLoading();
  try {
    // Use include_archived=true to get archived notes
    const all = await getNotes("*", "lastModified", "desc", null, true, false);
    // Filter client-side to only notes that are actually in _archive/
    results.value = all.filter((n) => n.title.startsWith("_archive/"));
    loadingIndicator.value?.setLoaded();
  } catch (error) {
    loadingIndicator.value?.setFailed();
    apiErrorHandler(error, toast);
  } finally {
    loading.value = false;
  }
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

function promptRestore(title) {
  pendingRestoreTitle.value = title;
  isConfirmRestoreVisible.value = true;
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
    // Delete one at a time to avoid race conditions
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