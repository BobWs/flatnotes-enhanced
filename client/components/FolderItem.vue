<template>
  <div>
    <!-- Folder row -->
    <div
      class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm transition-colors text-left group"
      :class="isActive
        ? 'font-semibold text-theme-text bg-theme-background-elevated'
        : 'text-theme-text-muted hover:bg-theme-background-elevated'"
      :data-folder-path="node.path"
      @dragover.prevent
      @drop="handleDrop"
    >
      <div class="flex items-center gap-1.5 min-w-0 flex-1">
        <!-- Expand/collapse button -->
        <button
          @click.stop="toggleExpand"
          class="shrink-0 p-0.5 rounded transition-transform duration-150"
          :class="isExpanded ? 'rotate-90' : ''"
          :title="isExpanded ? 'Collapse' : 'Expand'"
        >
          <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
            <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
          </svg>
        </button>

        <!-- Folder icon and name -->
        <button
          @click.stop="emit('navigate', node.path)"
          class="flex items-center gap-1.5 min-w-0 flex-1"
          :title="node.path"
        >
          <svg v-if="isExpanded" viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-70">
            <path d="M19,20H4C2.89,20 2,19.1 2,18V6C2,4.89 2.89,4 4,4H10L12,6H19A2,2 0 0,1 21,8H21L19,20M19,8H4V18H19V8Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
            <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
          </svg>
          <span class="truncate font-medium">{{ node.name }}</span>
        </button>
      </div>

      <!-- Note count badge -->
      <span
        v-if="node.count > 0"
        class="text-xs shrink-0 ml-2 tabular-nums font-mono text-theme-text-muted"
      >{{ node.count }}</span>
    </div>

    <!-- Expanded content: sub-folders + notes -->
    <div
      v-if="isExpanded"
      class="ml-5 border-l-2 pl-1 mt-0.5 mb-0.5"
      style="border-color: rgba(136,145,161,0.4)"
    >
      <!-- Recursive sub-folders -->
      <FolderItem
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :activeFolder="activeFolder"
        :activeNote="activeNote"
        :forceExpand="forceExpand"
        :showCheckboxes="showCheckboxes"
        :selectedNotes="selectedNotes"
        @navigate="emit('navigate', $event)"
        @openNote="emit('openNote', $event)"
        @updateSelection="emit('updateSelection', $event)"
        @dropNote="emit('dropNote', $event)"
      />

      <!-- Notes list -->
      <div v-if="notesLoading" class="flex items-center gap-2 px-2 py-1.5 text-xs text-theme-text-very-muted">
        <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current animate-spin shrink-0">
          <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z"/>
        </svg>
        Loading notes…
      </div>

      <!-- Note rows -->
      <div
        v-for="noteTitle in notes"
        :key="noteTitle"
        class="group w-full flex items-center gap-1.5 px-2 py-1 rounded text-xs text-left transition-colors"
        :class="activeNote === noteTitle
          ? 'text-theme-text font-medium bg-theme-background-elevated'
          : 'text-theme-text-muted hover:bg-theme-background-elevated hover:text-theme-text'"
      >
        <!-- Checkbox (if selection mode) -->
        <input
          v-if="showCheckboxes"
          type="checkbox"
          :checked="selectedNotes.has(noteTitle)"
          @change="(e) => onCheckboxChange(noteTitle, e.target.checked)"
          @click.stop
          class="w-3.5 h-3.5 accent-theme-brand shrink-0 cursor-pointer"
        />
        <!-- Note icon (only if checkbox not shown) -->
        <svg v-if="!showCheckboxes" viewBox="0 0 24 24" class="w-3 h-3 fill-current shrink-0 opacity-50">
          <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z"/>
        </svg>
        
        <!-- Note title (clickable) -->
        <button
          @click.stop="emit('openNote', noteTitle)"
          class="flex-1 text-left truncate"
          :title="noteTitle"
          :draggable="!showCheckboxes"
          @dragstart="handleDragStart($event, noteTitle)"
          @dragend="handleDragEnd"
        >
          {{ displayName(noteTitle) }}
        </button>
        
        <!-- Preview button -->
        <button
          v-if="previewEnabled && !showCheckboxes"
          :data-note-title="noteTitle"
          @click.stop="onPreviewClick($event, noteTitle)"
          class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded text-theme-text-muted hover:text-theme-brand hover:bg-theme-background-elevated"
          title="Preview note"
        >
          <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
            <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"/>
          </svg>
        </button>
      </div>

      <!-- Empty folder state -->
      <div
        v-if="!notesLoading && notes.length === 0 && node.children.length === 0"
        class="px-2 py-1 text-xs text-theme-text-very-muted italic"
      >
        Empty folder
      </div>
    </div>

    <!-- Preview popup -->
    <NotePreview ref="previewPopup" :noteTitle="currentPreviewNote" :target="previewTarget" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { getFolderNotes } from "../api.js";
import NotePreview from "./NotePreview.vue";

const props = defineProps({
  node: Object,
  activeFolder: { type: String, default: null },
  activeNote:   { type: String, default: null },
  forceExpand:  { type: Boolean, default: null },
  showCheckboxes: { type: Boolean, default: false },
  selectedNotes: { type: Set, default: () => new Set() },
});

const emit = defineEmits(["navigate", "openNote", "updateSelection", "dropNote"]);

const localExpanded = ref(false);
const notes         = ref([]);
const notesLoading  = ref(false);
const notesFetched  = ref(false);

// Preview state
const previewEnabled = ref(true);
const previewPopup = ref(null);
const currentPreviewNote = ref("");
const previewTarget = ref(null);

// Load preview setting from localStorage
function loadPreviewSetting() {
  const stored = localStorage.getItem("fn_preview_enabled");
  if (stored === null) {
    previewEnabled.value = true;
  } else {
    previewEnabled.value = stored === "true";
  }
}

function onPreviewClick(event, noteTitle) {
  if (!previewEnabled.value) return;
  currentPreviewNote.value = noteTitle;
  previewTarget.value = event.currentTarget;
  setTimeout(() => {
    previewPopup.value?.show();
  }, 50);
}

const isExpanded = computed(() => {
  if (props.forceExpand === true)  return true;
  if (props.forceExpand === false) return false;
  return localExpanded.value;
});

watch(() => props.forceExpand, (val) => {
  if (val === true)  localExpanded.value = true;
  if (val === false) localExpanded.value = false;
});

async function fetchNotes() {
  if (notesFetched.value || notesLoading.value) return;
  notesLoading.value = true;
  try {
    const data = await getFolderNotes(props.node.path);
    notes.value = Array.isArray(data) ? data : [];
  } catch {
    notes.value = [];
  } finally {
    notesLoading.value = false;
    notesFetched.value  = true;
  }
}

watch(isExpanded, (expanded) => {
  if (expanded) fetchNotes();
}, { immediate: true });

function toggleExpand() {
  localExpanded.value = !localExpanded.value;
}

const isActive = computed(() => props.activeFolder === props.node.path);

function displayName(title) {
  const prefix = props.node.path + "/";
  return title.startsWith(prefix) ? title.slice(prefix.length) : title;
}

// ── Checkbox selection ─────────────────────────────────────────────────────
function onCheckboxChange(noteTitle, checked) {
  emit("updateSelection", { noteTitle, checked });
}

// ── Drag and drop ─────────────────────────────────────────────────────────
let dragData = null;

function handleDragStart(event, noteTitle) {
  event.dataTransfer.setData("text/plain", noteTitle);
  event.dataTransfer.effectAllowed = "move";
  dragData = noteTitle;
}

function handleDragEnd(event) {
  dragData = null;
}

function handleDrop(event) {
  const noteTitle = event.dataTransfer.getData("text/plain");
  if (!noteTitle) return;
  const targetFolder = event.currentTarget.getAttribute("data-folder-path");
  if (targetFolder && noteTitle) {
    emit("dropNote", { noteTitle, targetFolder });
  }
  event.preventDefault();
}

onMounted(() => {
  loadPreviewSetting();
});
</script>