<template>
  <div class="flex h-full max-w-[999px] flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text">Bookmarks</h1>
        <p class="text-xs text-theme-text-muted mt-0.5">
          {{ results.length }} bookmark{{ results.length !== 1 ? 's' : '' }}
          · Notes tagged with <code class="bg-theme-background-elevated px-1 rounded">#pin</code>
          appear here. Unpin a note to remove it from this list.
        </p>
      </div>
      <button
        @click="loadBookmarks"
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

    <!-- Confirm unpin -->
    <ConfirmModal
      v-model="isConfirmUnpinVisible"
      title="Remove Bookmark"
      :message="`Remove bookmark from '${displayName(pendingUnpinTitle)}'?`"
      confirmButtonText="Unpin"
      confirmButtonStyle="cta"
      @confirm="doUnpin"
    />

    <!-- Confirm delete -->
    <ConfirmModal
      v-model="isConfirmDeleteVisible"
      title="Move to Trash"
      :message="`Move '${displayName(pendingDeleteTitle)}' to trash?`"
      confirmButtonText="Move to Trash"
      confirmButtonStyle="danger"
      @confirm="doDelete"
    />

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Empty state -->
      <div
        v-if="results.length === 0 && !loading"
        class="flex flex-col items-center justify-center py-16 text-theme-text-very-muted"
      >
        <svg viewBox="0 0 24 24" class="w-16 h-16 mb-3 opacity-40 fill-current">
          <path d="M17,3H7A2,2 0 0,0 5,5V21L12,18L19,21V5C19,3.89 18.1,3 17,3Z"/>
        </svg>
        <p class="text-sm">No bookmarks yet</p>
        <p class="text-xs mt-1 text-theme-text-very-muted">
          Tag any note with <code class="bg-theme-background-elevated px-1 rounded">#pin</code> to bookmark it
        </p>
      </div>

      <!-- Bookmark items -->
      <div
        v-for="note in results"
        :key="note.title"
        class="mb-2 rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <!-- Left: title + folder + date — click opens preview -->
        <div class="min-w-0 flex-1 cursor-pointer" @click="previewNote(note.title)">
          <p v-if="displayFolder(note.title)" class="text-xs text-theme-text-very-muted mb-0.5">
            {{ displayFolder(note.title) }}
          </p>
          <p class="font-medium text-theme-text truncate hover:text-theme-brand transition-colors">
            {{ displayName(note.title) }}
          </p>
          <p class="text-xs text-theme-text-muted mt-0.5">{{ note.lastModifiedAsString }}</p>
        </div>

        <!-- Right: action buttons -->
        <div class="flex gap-2 shrink-0">
          <!-- Edit button -->
          <button
            @click="editNote(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            title="Edit note"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiPencil"/>
            </svg>
            Edit
          </button>

          <!-- Unpin button -->
          <button
            @click="promptUnpin(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            title="Remove bookmark"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiBookmarkRemove"/>
            </svg>
            Unpin
          </button>

          <!-- Delete button -->
          <button
            @click="promptDelete(note.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
            title="Move to trash"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path :d="mdiDeleteForever"/>
            </svg>
          </button>
        </div>
      </div>
    </LoadingIndicator>
  </div>
</template>

<script setup>
import { mdiPencil, mdiBookmarkRemove, mdiDeleteForever } from "@mdi/js";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getNotes, unpinNote, deleteNote } from "../api.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions } from "../helpers.js";

const loadingIndicator = ref();
const loading = ref(false);
const results = ref([]);
const toast = useToast();
const router = useRouter();
const globalStore = useGlobalStore();

const isConfirmUnpinVisible = ref(false);
const isConfirmDeleteVisible = ref(false);
const pendingUnpinTitle = ref("");
const pendingDeleteTitle = ref("");

// Return just the note filename (last path segment, no extension displayed)
function displayName(title) {
  const parts = (title || "").split("/");
  return parts[parts.length - 1];
}

// Return the folder path (everything before the last segment), or empty string
function displayFolder(title) {
  const idx = (title || "").lastIndexOf("/");
  return idx > -1 ? (title || "").slice(0, idx) : "";
}

function previewNote(title) {
  router.push({ name: "note", params: { title } });
}

function editNote(title) {
  router.push({ name: "note", params: { title }, query: { edit: "true" } });
}

async function loadBookmarks() {
  loading.value = true;
  loadingIndicator.value?.setLoading();
  try {
    const all = await getNotes("tags:pin", "lastModified", "desc", null, false, false);
    results.value = all;
    loadingIndicator.value?.setLoaded();
  } catch (error) {
    loadingIndicator.value?.setFailed();
    apiErrorHandler(error, toast);
  } finally {
    loading.value = false;
  }
}

function promptUnpin(title) {
  pendingUnpinTitle.value = title;
  isConfirmUnpinVisible.value = true;
}

async function doUnpin() {
  try {
    await unpinNote(pendingUnpinTitle.value);
    toast.add(getToastOptions(`'${displayName(pendingUnpinTitle.value)}' unpinned ✓`, "Success", "success"));
    pendingUnpinTitle.value = "";
    globalStore.bumpPinned(); // keeps NavBar bookmark button in sync
    await loadBookmarks();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

function promptDelete(title) {
  pendingDeleteTitle.value = title;
  isConfirmDeleteVisible.value = true;
}

async function doDelete() {
  try {
    await deleteNote(pendingDeleteTitle.value);
    toast.add(getToastOptions(`'${displayName(pendingDeleteTitle.value)}' moved to trash ✓`, "Success", "success"));
    pendingDeleteTitle.value = "";
    globalStore.bumpPinned(); // note is gone, so pinned count may change
    await loadBookmarks();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

onMounted(loadBookmarks);
</script>