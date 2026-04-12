<template>
  <div class="flex h-full max-w-[999px] flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text">Trash</h1>
        <p class="text-xs text-theme-text-muted mt-0.5">
          {{ results.length }} trashed note{{ results.length !== 1 ? 's' : '' }}
          · Notes moved here are hidden from search.
        </p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="results.length > 0"
          @click="confirmEmptyTrash"
          class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                 text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
          title="Empty trash"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
            <path :d="mdiDeleteForever"/>
          </svg>
          Empty Trash
        </button>
        <button
          @click="loadTrash"
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

    <!-- Confirm empty trash -->
    <ConfirmModal
      v-model="isConfirmEmptyVisible"
      title="Empty Trash"
      message="Permanently delete all notes in trash? This cannot be undone."
      confirmButtonText="Empty Trash"
      confirmButtonStyle="danger"
      @confirm="doEmptyTrash"
    />

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Empty state -->
      <div
        v-if="results.length === 0 && !loading"
        class="flex flex-col items-center justify-center py-16 text-theme-text-very-muted"
      >
        <svg viewBox="0 0 64 64" class="w-16 h-16 mb-3 opacity-40">
          <path fill="currentColor" d="M52 8h-12V6a2 2 0 0 0-2-2H26a2 2 0 0 0-2 2v2H12a2 2 0 0 0 0 4h2l2 44h32l2-44h2a2 2 0 0 0 0-4zm-24-2h8v2h-8V6zM46 52H18l-1.9-40h31.8L46 52z"/>
          <path fill="currentColor" d="M24 24h4v20h-4zm12 0h4v20h-4z"/>
        </svg>
        <p class="text-sm">Trash is empty</p>
      </div>

      <!-- Trash items -->
      <div
        v-for="note in results"
        :key="note.title"
        class="mb-2 rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <div class="min-w-0">
          <p v-if="displayFolder(note.title)" class="text-xs text-theme-text-very-muted mb-0.5">
            {{ displayFolder(note.title) }}
          </p>
          <p class="font-medium text-theme-text truncate">{{ displayName(note.title) }}</p>
          <p class="text-xs text-theme-text-muted mt-0.5">{{ note.lastModifiedAsString }}</p>
        </div>
        <div class="flex gap-2 shrink-0">
          <!-- Restore button (gray) -->
          <button
            @click="doRestore(note.title)"
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
          
          <!-- Delete button (RED) -->
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

import {
  apiErrorHandler,
  getNotes,
  restoreNote,
  permanentDeleteNote,
} from "../api.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import { getToastOptions } from "../helpers.js";

const loadingIndicator = ref();
const loading = ref(false);
const results = ref([]);
const toast = useToast();
const isConfirmDeleteVisible = ref(false);
const isConfirmEmptyVisible = ref(false);
const pendingDeleteTitle = ref("");

// Strip _trash/ prefix then return just the filename (no extension shown)
function displayName(title) {
  const stripped = (title || "").replace(/^_trash\//, "");
  const parts = stripped.split("/");
  return parts[parts.length - 1];
}

// Strip _trash/ prefix then return only the folder portion (if any)
function displayFolder(title) {
  const stripped = (title || "").replace(/^_trash\//, "");
  const idx = stripped.lastIndexOf("/");
  return idx > -1 ? stripped.slice(0, idx) : "";
}

async function loadTrash() {
  loading.value = true;
  loadingIndicator.value.setLoading();
  try {
    // Use include_trash=true so the search backend returns _trash/* notes
    const all = await getNotes("*", "lastModified", "desc", null, false, true);
    // Filter client-side to only notes that are actually in _trash/
    results.value = all.filter((n) => n.title.startsWith("_trash/"));
    loadingIndicator.value.setLoaded();
  } catch (error) {
    loadingIndicator.value.setFailed();
    apiErrorHandler(error, toast);
  } finally {
    loading.value = false;
  }
}

async function doRestore(title) {
  try {
    await restoreNote(title);
    toast.add(getToastOptions(`'${displayName(title)}' restored ✓`, "Success", "success"));
    await loadTrash();
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
    await permanentDeleteNote(pendingDeleteTitle.value);
    toast.add(getToastOptions("Permanently deleted ✓", "Success", "success"));
    pendingDeleteTitle.value = "";
    await loadTrash();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

function confirmEmptyTrash() {
  isConfirmEmptyVisible.value = true;
}

async function doEmptyTrash() {
  try {
    // Delete one at a time to avoid race conditions; collect errors
    for (const note of results.value) {
      await permanentDeleteNote(note.title);
    }
    toast.add(getToastOptions("Trash emptied ✓", "Success", "success"));
    await loadTrash();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

onMounted(loadTrash);
</script>