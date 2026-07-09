<template>
  <div>
    <!-- Header row -->
    <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
      <div>
        <h3 class="text-lg font-medium text-theme-text mb-1">Saved Searches</h3>
        <p class="text-sm text-theme-text-muted">
          Save frequently-used search queries for one-click access from the folder sidebar.
    <!--      Enable the sidebar section in
          <button
            type="button"
            @click="goToPreferences"
            class="text-theme-brand hover:underline focus:outline-none"
          >Settings → Preferences</button>. -->
        </p>
      </div>
      <button
        @click="openCreate"
        class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
               bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors touch-manipulation"
      >
        <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
          <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
        </svg>
        Add search
      </button>
    </div>

    <!-- Create / Edit modal -->
    <SavedSearchModal
      :show="modalVisible"
      :search="editingSearch"
      @save="handleModalSave"
      @close="closeModal"
    />

    <!-- Delete confirmation -->
    <ConfirmModal
      v-model="isDeleteModalVisible"
      title="Delete Saved Search"
      :message="`Delete '${pendingDelete?.name}'? This cannot be undone.`"
      confirmButtonText="Delete"
      confirmButtonStyle="danger"
      @confirm="confirmDelete"
    />

    <!-- Empty state -->
    <div
      v-if="!loading && searches.length === 0"
      class="flex flex-col items-center justify-center py-14 text-theme-text-very-muted gap-3
             border border-dashed border-theme-border rounded-xl"
    >
      <svg viewBox="0 0 24 24" class="w-12 h-12 fill-current opacity-30">
        <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4M15.5,11H17V13H15.5V14.5H13.5V13H12V11H13.5V9.5H15.5V11Z"/>
      </svg>
      <p class="text-sm">No saved searches yet.</p>
      <p class="text-xs text-center max-w-xs leading-relaxed">
        Click "Add search" to save a query. You can use any search term, tag filter, or phrase.
      </p>
    </div>

    <!-- Search list -->
    <div v-else class="border border-theme-border rounded-xl overflow-hidden">
      <!-- Loading skeleton -->
      <template v-if="loading">
        <div class="p-3 space-y-2">
          <div v-for="n in 3" :key="n" class="h-14 rounded-lg bg-theme-background-elevated animate-pulse"></div>
        </div>
      </template>

      <div v-else class="divide-y divide-theme-border">
        <div
          v-for="(search, idx) in searches"
          :key="search.id"
          draggable="true"
          @dragstart="onDragStart($event, idx)"
          @dragover.prevent="onDragOver($event, idx)"
          @dragleave="onDragLeave"
          @drop.prevent="onDrop($event, idx)"
          @dragend="onDragEnd"
          class="flex items-center gap-3 px-4 py-3 bg-theme-background
                 hover:bg-theme-background-elevated/50 transition-colors group select-none"
          :class="{
            'opacity-40': dragSrcIdx === idx,
            'border-t-2 border-t-theme-brand': dragOverIdx === idx && dragOverIdx !== dragSrcIdx && idx <= dragSrcIdx,
            'border-b-2 border-b-theme-brand': dragOverIdx === idx && dragOverIdx !== dragSrcIdx && idx > dragSrcIdx,
          }"
        >
          <!-- Drag handle -->
          <div class="shrink-0 text-theme-text-very-muted cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity">
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
              <path d="M9,3H11V5H9V3M13,3H15V5H13V3M9,7H11V9H9V7M13,7H15V9H13V7M9,11H11V13H9V11M13,11H15V13H13V11M9,15H11V17H9V15M13,15H15V17H13V15M9,19H11V21H9V19M13,19H15V21H13V19Z"/>
            </svg>
          </div>

          <!-- Search icon -->
          <div class="shrink-0 w-8 h-8 rounded-lg bg-theme-brand/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current text-theme-brand">
              <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-theme-text truncate">{{ search.name }}</p>
            <div class="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5">
              <code class="text-xs text-theme-text-muted font-mono truncate max-w-[240px]">{{ search.query }}</code>
              <span
                v-if="search.sort_by"
                class="text-xs text-theme-text-very-muted"
              >Sort: {{ sortLabel(search.sort_by) }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 shrink-0">
            <!-- Run search -->
            <RouterLink
              :to="searchRoute(search)"
              class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium
                     text-theme-text-muted border border-theme-border
                     hover:bg-theme-background-elevated transition-colors touch-manipulation"
              title="Run this search"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
                <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
              </svg>
              Run
            </RouterLink>

            <!-- Edit -->
            <button
              @click="openEdit(search)"
              class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium
                     text-theme-text-muted border border-theme-border
                     hover:bg-theme-background-elevated transition-colors touch-manipulation"
              title="Edit saved search"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
                <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
              </svg>
              Edit
            </button>

            <!-- Delete -->
            <button
              @click="promptDelete(search)"
              class="inline-flex items-center p-1.5 rounded-lg text-theme-text-muted
                     hover:text-red-500 hover:bg-red-500/10 transition-colors touch-manipulation"
              title="Delete saved search"
            >
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Save feedback -->
    <p v-if="saveMsg" class="mt-3 text-sm" :class="saveOk ? 'text-green-500' : 'text-red-500'">
      {{ saveMsg }}
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { getSavedSearches, saveSavedSearches } from "../api.js";
import { useGlobalStore } from "../globalStore.js";
import { searchSortOptions } from "../constants.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import SavedSearchModal from "../components/SavedSearchModal.vue";

const globalStore = useGlobalStore();
const router = useRouter();

function goToPreferences() {
  router.push({ name: "settings", query: { tab: "prefs" } });
}

// ── Drag-and-drop reordering ──────────────────────────────────────────────────
const dragSrcIdx  = ref(null);  // index of the row being dragged
const dragOverIdx = ref(null);  // index of the row currently hovered over

function onDragStart(event, idx) {
  dragSrcIdx.value = idx;
  // Required for Firefox — set any data so the drag fires
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", String(idx));
}

function onDragOver(event, idx) {
  if (idx === dragSrcIdx.value) return;
  dragOverIdx.value = idx;
}

function onDragLeave() {
  // Only clear if the pointer has genuinely left the list area.
  // We keep dragOverIdx set while hovering over child elements inside
  // the row (icon, text, buttons) — dragLeave fires for those too.
  // The drop handler clears it definitively.
}

function onDrop(event, toIdx) {
  const fromIdx = dragSrcIdx.value;
  dragSrcIdx.value  = null;
  dragOverIdx.value = null;

  if (fromIdx === null || fromIdx === toIdx) return;

  // Reorder the array: remove from source position, insert at target position
  const reordered = [...searches.value];
  const [moved] = reordered.splice(fromIdx, 1);
  reordered.splice(toIdx, 0, moved);

  // Persist immediately — same pattern as delete/edit
  persist(reordered).then(ok => {
    if (ok) showMsg("Order saved ✓");
  });
}

function onDragEnd() {
  // Always clean up visual state even if drop fired outside the list
  dragSrcIdx.value  = null;
  dragOverIdx.value = null;
}

// ── State ─────────────────────────────────────────────────────────────────────
const searches   = ref([]);
const enabled    = ref(false);   // mirrors the enabled flag from backend
const loading    = ref(false);
const saveMsg    = ref("");
const saveOk     = ref(true);

const modalVisible  = ref(false);
const editingSearch = ref(null);   // null = create mode

const isDeleteModalVisible = ref(false);
const pendingDelete        = ref(null);

// ── Helpers ───────────────────────────────────────────────────────────────────
const SORT_LABELS = {
  score:        "Relevance",
  title:        "Title A–Z",
  titleDesc:    "Title Z–A",
  lastModified: "Last modified",
};

function sortLabel(sortBy) {
  return SORT_LABELS[sortBy] || sortBy;
}

const SORT_MAP = {
  lastModified: searchSortOptions.lastModified,
  title:        searchSortOptions.title,
  titleDesc:    searchSortOptions.titleDesc,
  score:        searchSortOptions.score,
};

function searchRoute(search) {
  const q = { term: search.query };
  if (search.sort_by && SORT_MAP[search.sort_by] !== undefined) {
    q.sortBy = SORT_MAP[search.sort_by];
  }
  return { name: "search", query: q };
}

function showMsg(msg, ok = true) {
  saveMsg.value = msg;
  saveOk.value  = ok;
  setTimeout(() => { saveMsg.value = ""; }, 3000);
}

// ── Persist helper ────────────────────────────────────────────────────────────
async function persist(list) {
  try {
    const result = await saveSavedSearches({ enabled: enabled.value, searches: list });
    searches.value = Array.isArray(result.searches) ? result.searches : list;
    // Keep global store in sync so the sidebar reflects changes immediately
    globalStore.savedSearches = searches.value;
    return true;
  } catch {
    showMsg("Failed to save. Please try again.", false);
    return false;
  }
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  try {
    const data = await getSavedSearches();
    enabled.value  = data.enabled === true;
    searches.value = Array.isArray(data.searches) ? data.searches : [];
  } catch {
    searches.value = [];
  } finally {
    loading.value = false;
  }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openCreate() {
  editingSearch.value = null;
  modalVisible.value  = true;
}

function openEdit(search) {
  editingSearch.value = search;
  modalVisible.value  = true;
}

function closeModal() {
  modalVisible.value  = false;
  editingSearch.value = null;
}

async function handleModalSave({ name, query, sort_by }) {
  const now = new Date().toISOString();

  if (editingSearch.value) {
    // Update existing
    const updated = searches.value.map(s =>
      s.id === editingSearch.value.id
        ? { ...s, name, query, sort_by, updated_at: now }
        : s
    );
    const ok = await persist(updated);
    if (ok) showMsg("Saved search updated ✓");
  } else {
    // Create new — client-generated UUID
    const newEntry = {
      id:         crypto.randomUUID(),
      name,
      query,
      sort_by,
      created_at: now,
      updated_at: now,
    };
    const ok = await persist([...searches.value, newEntry]);
    if (ok) showMsg("Saved search created ✓");
  }

  closeModal();
}

// ── Delete ────────────────────────────────────────────────────────────────────
function promptDelete(search) {
  pendingDelete.value        = search;
  isDeleteModalVisible.value = true;
}

async function confirmDelete() {
  if (!pendingDelete.value) return;
  const filtered = searches.value.filter(s => s.id !== pendingDelete.value.id);
  const ok = await persist(filtered);
  if (ok) showMsg("Saved search deleted ✓");
  pendingDelete.value = null;
}

// ── Mount ─────────────────────────────────────────────────────────────────────
onMounted(load);
</script>
