<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-start justify-center"
      style="background:rgba(0,0,0,0.45);backdrop-filter:blur(2px);"
      @click.self="cancel"
    >
      <div
        class="relative mx-3 mt-[18vh] w-full max-w-[520px] rounded-xl
               border border-theme-border bg-theme-background shadow-2xl"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 pt-4 pb-3 border-b border-theme-border">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-brand shrink-0">
              <path d="M10,13H4V11H10V13M10,9H4V7H10V9M20,17V19H18V17H16V15H18V13H20V15H22V17H20M14,15V13H4V15H14M14,11V9H12V7H14V5H16V7H18V9H16V11H14Z"/>
            </svg>
            <h2 class="text-base font-semibold text-theme-text">Insert Note Link</h2>
          </div>
          <button @click="cancel"
            class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded touch-manipulation"
            title="Close">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>

        <!-- Search -->
        <div class="px-4 pt-3 pb-2">
          <div class="relative">
            <svg viewBox="0 0 24 24"
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 fill-current text-theme-text-muted pointer-events-none">
              <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
            </svg>
            <input
              ref="searchInput"
              v-model="query"
              placeholder="Search notes by title…"
              class="w-full pl-9 pr-3 py-2.5 text-sm bg-theme-background-elevated
                     border border-theme-border rounded-lg outline-none
                     focus:border-theme-brand text-theme-text"
              @keydown.esc.stop="cancel"
              @keydown.down.prevent="moveDown"
              @keydown.up.prevent="moveUp"
              @keydown.enter.prevent="confirmSelected"
            />
          </div>
        </div>

        <!-- Results list -->
        <div class="px-2 pb-2 max-h-52 overflow-y-auto" style="min-height:2.5rem;">
          <div v-if="loading" class="flex items-center justify-center py-4 text-theme-text-muted text-sm">
            Loading…
          </div>
          <div v-else-if="filtered.length === 0 && query"
            class="text-center py-4 text-sm text-theme-text-muted">
            No notes found matching "{{ query }}"
          </div>
          <button
            v-for="(note, i) in filtered"
            :key="note.title"
            @click="selectNote(note)"
            :ref="el => { if (el) itemRefs[i] = el; }"
            class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
                   flex items-center gap-2 touch-manipulation"
            :class="i === activeIndex
              ? 'bg-theme-brand/15 text-theme-brand'
              : 'text-theme-text hover:bg-theme-background-elevated'"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current text-theme-text-muted shrink-0">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            <span class="truncate">{{ note.title }}</span>
          </button>
        </div>

        <!-- Display text + insert -->
        <div class="px-4 pt-2 pb-4 border-t border-theme-border space-y-3 mt-1">
          <div v-if="selected" class="flex items-center gap-2 text-sm">
            <span class="text-theme-text-muted shrink-0">Selected:</span>
            <span class="truncate font-medium text-theme-brand">{{ selected.title }}</span>
          </div>

          <!-- Display text: hidden for now, feature reserved for future -->
          <!-- Remove v-show="false" below to re-enable custom display text -->
          <div v-show="false">
            <label class="block text-xs font-medium text-theme-text-muted mb-1 uppercase tracking-wide">
              Display text
              <span class="normal-case font-normal ml-1">(optional — leave blank to use note title)</span>
            </label>
            <input
              v-model="displayText"
              :placeholder="selected ? selected.title : 'Custom display text…'"
              class="w-full text-sm bg-theme-background-elevated border border-theme-border
                     rounded-lg px-3 py-2 outline-none focus:border-theme-brand text-theme-text"
              @keydown.esc.stop="cancel"
              @keydown.enter.prevent="confirmSelected"
            />
          </div>

          <!-- Preview — also hidden while display text is hidden -->
          <div v-if="false && selected" class="text-xs text-theme-text-very-muted font-mono bg-theme-background-elevated
               rounded px-2 py-1 truncate">
            {{ previewText }}
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-2">
            <button @click="cancel"
              class="px-3 py-1.5 rounded text-sm text-theme-text-muted border border-theme-border
                     hover:bg-theme-background-elevated transition-colors touch-manipulation">
              Cancel
            </button>
            <button
              @click="confirmSelected"
              :disabled="!selected"
              class="px-4 py-1.5 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                     text-white transition-colors disabled:opacity-40 touch-manipulation"
            >
              Insert link
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { getNotes } from "../api.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["insert", "close"]);

// ── State ─────────────────────────────────────────────────────────────────────
const query       = ref("");
const allNotes    = ref([]);
const loading     = ref(false);
const selected    = ref(null);
const displayText = ref("");
const activeIndex = ref(0);
const searchInput = ref(null);
const itemRefs    = ref([]);

// ── Computed ──────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return allNotes.value.slice(0, 30); // show 30 most recent by default
  return allNotes.value
    .filter(n => n.title.toLowerCase().includes(q))
    .slice(0, 30);
});

const previewText = computed(() => {
  if (!selected.value) return "";
  const label = displayText.value.trim();
  return label ? `[[${selected.value.title}|${label}]]` : `[[${selected.value.title}]]`;
});

// ── Load notes once on first open ────────────────────────────────────────────
let notesLoaded = false;
async function loadNotes() {
  if (notesLoaded) return;
  loading.value = true;
  try {
    const data = await getNotes("*", "lastModified", "desc", 500);
    allNotes.value = data;
    notesLoaded = true;
  } catch {
    allNotes.value = [];
  } finally {
    loading.value = false;
  }
}

// ── Keyboard nav ──────────────────────────────────────────────────────────────
function moveDown() {
  if (activeIndex.value < filtered.value.length - 1) {
    activeIndex.value++;
    scrollActiveIntoView();
  }
}
function moveUp() {
  if (activeIndex.value > 0) {
    activeIndex.value--;
    scrollActiveIntoView();
  }
}
function scrollActiveIntoView() {
  nextTick(() => {
    const el = itemRefs.value[activeIndex.value];
    if (el) el.scrollIntoView({ block: "nearest" });
  });
}

// ── Selection ─────────────────────────────────────────────────────────────────
function selectNote(note) {
  selected.value = note;
  activeIndex.value = filtered.value.indexOf(note);
}

function confirmSelected() {
  if (!selected.value && filtered.value.length > 0) {
    // If nothing explicitly selected but there's a highlighted result, use it
    selected.value = filtered.value[activeIndex.value];
  }
  if (!selected.value) return;
  emit("insert", {
    target:  selected.value.title,
    display: displayText.value.trim() || null,
  });
  resetAndClose();
}

function cancel() {
  emit("close");
  resetAndClose();
}

function resetAndClose() {
  query.value       = "";
  displayText.value = "";
  selected.value    = null;
  activeIndex.value = 0;
  itemRefs.value    = [];
}

// ── Sync activeIndex when query changes ───────────────────────────────────────
watch(query, () => {
  activeIndex.value = 0;
  // Auto-select first result when user types
  selected.value = filtered.value[0] || null;
});

// ── Open/close lifecycle ──────────────────────────────────────────────────────
watch(() => props.show, async (val) => {
  if (val) {
    await loadNotes();
    await nextTick();
    searchInput.value?.focus();
    // Default-select first item
    selected.value = filtered.value[0] || null;
  } else {
    resetAndClose();
  }
});
</script>