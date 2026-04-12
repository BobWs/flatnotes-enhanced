<template>
  <!-- Mobile overlay -->
  <div
    v-if="isOpen"
    class="fixed inset-0 z-30 bg-black/40 md:hidden"
    @click="$emit('close')"
  ></div>

  <aside
    :class="[
      'fixed top-0 left-0 z-40 h-full w-72 flex flex-col',
      'bg-theme-background border-r border-theme-border',
      'transition-transform duration-300 ease-in-out',
      isOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <!-- Header: title + buttons -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border shrink-0">
      <span class="text-xs font-bold uppercase text-theme-text-very-muted tracking-wider">Folders</span>
      <div class="flex items-center gap-1">
        <!-- Move button (only shows if selection mode is active) -->
        <button
          v-if="selectionMode"
          @click="openMoveModal"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          title="Move selected notes"
          :disabled="selectedNotes.size === 0"
          :class="{ 'opacity-40 cursor-not-allowed': selectedNotes.size === 0 }"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M9.5,4L8.5,3H4A2,2 0 0,0 2,5V19A2,2 0 0,0 4,21H20A2,2 0 0,0 22,19V7A2,2 0 0,0 20,5H13.5L12.5,4H9.5M15,11V13H11V16L8,12L11,8V11H15Z"/>
          </svg>
        </button>
        <!-- Expand/Collapse all -->
        <button
          @click="toggleExpandAll"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :title="expandAll === true ? 'Collapse all' : 'Expand all'"
        >
          <svg v-if="expandAll !== true" viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M13,14L18,9L16.6,7.6L13,11.2L9.4,7.6L8,9L13,14Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M8,11L13,6L18,11L16.6,12.4L13,8.8L9.4,12.4L8,11Z"/>
          </svg>
        </button>
        <!-- Refresh button -->
        <button
          @click="loadFolders"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :class="{ 'animate-spin': loading }"
          title="Refresh folders"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
        </button>
        <!-- Selection mode toggle -->
        <button
          @click="toggleSelectionMode"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :class="{ 'text-theme-brand': selectionMode }"
          title="Select notes to move"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M19,5V7H5V5H19Z"/>
          </svg>
        </button>
        <!-- Close button -->
        <button
          @click="$emit('close')"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          title="Close sidebar"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Folder list -->
    <div class="flex-1 overflow-y-auto px-2 py-2">
      <div v-if="loading" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        Loading folders...
      </div>
      <div v-else-if="folderTree.length === 0" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        No folders found
      </div>
      <template v-else>
        <!-- All Notes shortcut -->
        <button
          @click="navigate(null)"
          class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm transition-colors text-left mb-1"
          :class="activeFolder === null
            ? 'font-semibold text-theme-text bg-theme-background-elevated'
            : 'text-theme-text-muted hover:bg-theme-background-elevated'"
        >
          <div class="flex items-center gap-2 min-w-0">
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
              <path d="M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"/>
            </svg>
            <span class="truncate">All Notes</span>
          </div>
          <span v-if="totalCount > 0" class="text-xs tabular-nums font-mono ml-2 text-theme-text-muted">
            {{ totalCount }}
          </span>
        </button>

        <div class="border-t border-theme-border my-1 mx-2"></div>

        <!-- Folder tree -->
        <FolderItem
          v-for="node in folderTree"
          :key="node.path"
          :node="node"
          :activeFolder="activeFolder"
          :activeNote="activeNote"
          :forceExpand="expandAll"
          :showCheckboxes="selectionMode"
          :selectedNotes="selectedNotes"
          @navigate="navigate"
          @openNote="openNote"
          @updateSelection="updateSelection"
          @dropNote="handleDropNote"
        />
      </template>
    </div>

    <!-- Move folder picker modal with search and new folder -->
    <Teleport to="body">
      <div
        v-if="showMoveDialog"
        class="fixed inset-0 z-50 flex items-start justify-start"
        @click.self="closeMoveDialog"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/20 backdrop-blur-sm" @click="closeMoveDialog"></div>
        
        <!-- Modal positioned near sidebar -->
        <div
          class="relative mt-2 ml-[calc(18rem+0.5rem)] w-80 move-folder-modal"
          :class="{
            'ml-[calc(18rem+0.5rem)]': isOpen,
            'ml-2': !isOpen
          }"
        >
          <div class="bg-theme-background rounded-lg shadow-xl border border-theme-border overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border bg-theme-background-elevated">
              <span class="text-sm font-semibold text-theme-text">Move to folder</span>
              <button
                @click="closeMoveDialog"
                class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
                title="Close"
              >
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
              </button>
            </div>

            <!-- Info text -->
            <div class="px-4 pt-3 pb-2">
              <div class="text-xs text-theme-text-muted">
                Moving <span class="font-semibold text-theme-text">{{ selectedNotes.size }}</span> note{{ selectedNotes.size !== 1 ? 's' : '' }} to:
              </div>
            </div>

            <!-- Folder list with search -->
            <div class="px-3 pb-3">
              <!-- Search input -->
              <div class="mb-3">
                <div class="relative">
                  <svg class="absolute left-2 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-theme-text-very-muted" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
                  </svg>
                  <input
                    v-model="folderSearchQuery"
                    type="text"
                    placeholder="Search folders..."
                    class="w-full pl-7 pr-2 py-1.5 text-sm bg-theme-background border border-theme-border rounded-md focus:border-theme-brand outline-none text-theme-text placeholder-theme-text-very-muted"
                  />
                </div>
              </div>

              <!-- Create new folder row -->
              <div class="mb-2">
                <button
                  v-if="!showNewFolderInput"
                  @click="openNewFolderInput"
                  class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                         text-theme-brand hover:bg-theme-background-elevated flex items-center gap-2"
                >
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                    <path d="M20,6A2,2 0 0,1 22,8V18A2,2 0 0,1 20,20H4C2.89,20 2,19.1 2,18V6C2,4.89 2.89,4 4,4H10L12,6H20M19,14H17V12H15V14H13V16H15V18H17V16H19V14Z"/>
                  </svg>
                  <span>Create new folder…</span>
                </button>

                <div v-else class="px-3 py-2 rounded-md border border-theme-brand/40 bg-theme-background-elevated">
                  <div class="text-xs text-theme-text-muted mb-1.5 font-medium">New folder name</div>
                  <div class="flex items-center gap-1.5">
                    <input
                      ref="newFolderInputEl"
                      v-model="newFolderName"
                      type="text"
                      placeholder="e.g. projects/notes"
                      class="flex-1 min-w-0 text-sm bg-theme-background border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted"
                      @keydown.enter.prevent="confirmNewFolder"
                      @keydown.escape.prevent="cancelNewFolder"
                    />
                    <button
                      @click="confirmNewFolder"
                      class="shrink-0 p-1 rounded text-theme-brand hover:bg-theme-brand/10 transition-colors"
                      title="Create and move here"
                    >
                      <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                        <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
                      </svg>
                    </button>
                    <button
                      @click="cancelNewFolder"
                      class="shrink-0 p-1 rounded text-theme-text-muted hover:bg-theme-background-elevated transition-colors"
                      title="Cancel"
                    >
                      <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                        <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                      </svg>
                    </button>
                  </div>
                  <p v-if="newFolderError" class="text-xs text-red-500 mt-1">{{ newFolderError }}</p>
                  <p v-else class="text-xs text-theme-text-very-muted mt-1">
                    Use / for sub-folders. Press Enter to confirm.
                  </p>
                </div>
              </div>

              <!-- Divider -->
              <div v-if="filteredFolderPaths.length > 0" class="border-t border-theme-border my-1"></div>

              <!-- Filtered folder list -->
              <div class="max-h-48 overflow-y-auto">
                <button
                  v-for="folder in filteredFolderPaths"
                  :key="folder"
                  @click="moveNotesTo(folder)"
                  class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors hover:bg-theme-background-elevated text-theme-text"
                >
                  <div class="flex items-center gap-2">
                    <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
                      <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
                    </svg>
                    <span class="truncate">{{ folder || 'Root' }}</span>
                  </div>
                </button>
              </div>

              <!-- No results message -->
              <div v-if="filteredFolderPaths.length === 0 && folderSearchQuery" class="text-center py-4 text-xs text-theme-text-very-muted">
                No folders matching "{{ folderSearchQuery }}"
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";

import { getFolders, updateNote } from "../api.js";
import FolderItem from "./FolderItem.vue";
import { getToastOptions } from "../helpers.js";

const props = defineProps({ isOpen: Boolean });
const emit = defineEmits(["close"]);

const router = useRouter();
const toast = useToast();

const folderCounts = ref({});
const loading      = ref(false);
const activeFolder = ref(null);
const activeNote   = ref(null);
const expandAll    = ref(null);

// Selection state
const selectionMode = ref(false);
const selectedNotes = ref(new Set());

const showMoveDialog = ref(false);

// ── New-folder-in-dialog state ────────────────────────────────────────────
const showNewFolderInput = ref(false);
const newFolderName      = ref("");
const newFolderError     = ref("");
const newFolderInputEl   = ref(null);

// ── Folder search state ────────────────────────────────────────────────────
const folderSearchQuery = ref("");

const totalCount = computed(() => {
  let total = 0;
  const paths = Object.keys(folderCounts.value);
  for (const p of paths) {
    const hasChildren = paths.some((q) => q !== p && q.startsWith(p + "/"));
    if (!hasChildren) {
      total += folderCounts.value[p] || 0;
    }
  }
  return total;
});

// List of all folder paths (including empty string for root)
const allFolderPaths = computed(() => {
  const paths = Object.keys(folderCounts.value).sort();
  return ['', ...paths]; // empty string = root
});

// Filtered folder paths based on search query
const filteredFolderPaths = computed(() => {
  if (!folderSearchQuery.value.trim()) {
    return allFolderPaths.value;
  }
  const query = folderSearchQuery.value.toLowerCase().trim();
  return allFolderPaths.value.filter(folder => 
    folder.toLowerCase().includes(query)
  );
});

const folderTree = computed(() => {
  const root = [];
  const map  = {};
  const sorted = Object.keys(folderCounts.value).sort();

  for (const path of sorted) {
    const parts = path.split("/");
    let accumulated = "";
    for (let i = 0; i < parts.length; i++) {
      const parent = accumulated;
      accumulated = accumulated ? `${accumulated}/${parts[i]}` : parts[i];
      if (!map[accumulated]) {
        const node = {
          name:     parts[i],
          path:     accumulated,
          count:    folderCounts.value[accumulated] || 0,
          children: [],
        };
        map[accumulated] = node;
        if (i === 0)           root.push(node);
        else if (map[parent])  map[parent].children.push(node);
      }
    }
  }
  return root;
});

async function loadFolders() {
  loading.value = true;
  try {
    const data = await getFolders();
    if (data && typeof data === "object" && !Array.isArray(data)) {
      folderCounts.value = { ...data };
    } else if (Array.isArray(data)) {
      const d = {};
      data.forEach((p) => { d[p] = 0; });
      folderCounts.value = d;
    } else {
      folderCounts.value = {};
    }
  } catch {
    folderCounts.value = {};
  } finally {
    loading.value = false;
  }
}

function toggleExpandAll() {
  expandAll.value = expandAll.value !== true ? true : false;
}

function toggleSelectionMode() {
  selectionMode.value = !selectionMode.value;
  if (!selectionMode.value) {
    selectedNotes.value.clear();
  }
}

function updateSelection({ noteTitle, checked }) {
  if (checked) {
    selectedNotes.value.add(noteTitle);
  } else {
    selectedNotes.value.delete(noteTitle);
  }
}

function openMoveModal() {
  if (selectedNotes.value.size === 0) {
    toast.add(getToastOptions("No notes selected", "Info", "info"));
    return;
  }
  folderSearchQuery.value = ""; // Reset search when opening
  showMoveDialog.value = true;
}

function closeMoveDialog() {
  showMoveDialog.value = false;
  cancelNewFolder();
  folderSearchQuery.value = ""; // Reset search on close
}

// ── New-folder helpers ────────────────────────────────────────────────────

function openNewFolderInput() {
  showNewFolderInput.value = true;
  newFolderName.value      = "";
  newFolderError.value     = "";
  nextTick(() => {
    newFolderInputEl.value?.focus();
  });
}

function cancelNewFolder() {
  showNewFolderInput.value = false;
  newFolderName.value      = "";
  newFolderError.value     = "";
}

function validateFolderName(name) {
  if (!name || !name.trim()) {
    return "Folder name cannot be empty.";
  }
  const trimmed = name.trim();
  if (trimmed.startsWith("/") || trimmed.endsWith("/")) {
    return "Folder name cannot start or end with a slash.";
  }
  if (trimmed.includes("//")) {
    return "Folder name cannot contain consecutive slashes.";
  }
  if (/[\:*?"<>|]/.test(trimmed)) {
    return "Folder name contains invalid characters.";
  }
  if (trimmed.split("/").some((part) => part === ".." || part === ".")) {
    return "Folder name cannot contain '.' or '..'.";
  }
  return null;
}

async function confirmNewFolder() {
  const trimmed = newFolderName.value.trim();
  const error   = validateFolderName(trimmed);
  if (error) {
    newFolderError.value = error;
    return;
  }
  newFolderError.value = "";
  await moveNotesTo(trimmed);
  cancelNewFolder();
}

async function moveNotesTo(targetFolder) {
  showMoveDialog.value = false;
  const notesToMove = Array.from(selectedNotes.value);
  let successCount = 0;
  let failCount = 0;

  for (const oldTitle of notesToMove) {
    const parts = oldTitle.split("/");
    const basename = parts.pop();
    let newTitle;
    if (targetFolder) {
      newTitle = `${targetFolder}/${basename}`;
    } else {
      newTitle = basename;
    }

    try {
      // Use undefined for newContent to omit it from the JSON body
      await updateNote(oldTitle, newTitle, undefined);
      successCount++;
    } catch (error) {
      if (error.response?.status === 409) {
        toast.add(getToastOptions(`Note "${basename}" already exists in destination. Skipping.`, "Conflict", "warn"));
      } else if (error.response?.status === 404) {
        // Source was already moved (cleanup_empty_dirs removed the directory) — count as success
        successCount++;
      } else {
        console.error(`Failed to move ${oldTitle}:`, error);
        failCount++;
      }
    }
  }

  if (successCount > 0) {
    toast.add(getToastOptions(`Moved ${successCount} note(s)`, "Success", "success"));
    selectedNotes.value.clear();
    selectionMode.value = false;
    await loadFolders();
  }
  if (failCount > 0) {
    toast.add(getToastOptions(`Failed to move ${failCount} note(s)`, "Error", "error"));
  }
}

async function handleDropNote({ noteTitle, targetFolder }) {
  const parts = noteTitle.split("/");
  const basename = parts.pop();
  const newTitle = targetFolder ? `${targetFolder}/${basename}` : basename;

  try {
    // Use undefined for newContent to omit it from the JSON body
    await updateNote(noteTitle, newTitle, undefined);
    toast.add(getToastOptions(`Moved "${basename}"`, "Success", "success"));
    await loadFolders();
  } catch (error) {
    if (error.response?.status === 409) {
      toast.add(getToastOptions(`Note "${basename}" already exists in destination folder.`, "Conflict", "warn"));
    } else if (error.response?.status === 404) {
      // Note was already moved — treat as success
      toast.add(getToastOptions(`Moved "${basename}"`, "Success", "success"));
      await loadFolders();
    } else {
      toast.add(getToastOptions(`Failed to move "${basename}"`, "Error", "error"));
      console.error(`Failed to move ${noteTitle}:`, error);
    }
  }
}

function navigate(folderPath) {
  activeFolder.value = folderPath;
  activeNote.value   = null;
  if (!folderPath) {
    router.push({ name: "search", query: { term: "*", sortBy: 1 } });
  } else {
    router.push({ name: "search", query: { term: "*", folder: folderPath, sortBy: 1 } });
  }
  if (selectionMode.value) toggleSelectionMode();
  // Auto-close sidebar on mobile (below md breakpoint = 768px)
  if (window.innerWidth < 768) {
    emit("close");
  }
}

function openNote(noteTitle) {
  activeNote.value   = noteTitle;
  activeFolder.value = null;
  router.push({ name: "note", params: { title: noteTitle } });
  if (selectionMode.value) toggleSelectionMode();
  // Auto-close sidebar on mobile (below md breakpoint = 768px)
  if (window.innerWidth < 768) {
    emit("close");
  }
}

watch(() => props.isOpen, (open) => {
  if (open) loadFolders();
});

watch(
  () => router.currentRoute.value.query.folder,
  (f) => {
    activeFolder.value = f || null;
    if (f) activeNote.value = null;
  },
  { immediate: true }
);

watch(
  () => router.currentRoute.value.params.title,
  (t) => {
    if (t) {
      activeNote.value   = t;
      activeFolder.value = null;
    }
  },
  { immediate: true }
);

onMounted(() => {
  if (props.isOpen) loadFolders();
});
</script>

<style scoped>
.move-folder-modal {
  animation: modalFadeIn 0.15s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>