<template>
  <!-- Delete confirmation modal -->
  <ConfirmModal
    v-model="isDeleteModalVisible"
    title="Delete Attachment"
    :message="`Permanently delete '${pendingDelete?.filename}'? This cannot be undone.`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="confirmDelete"
  />

  <LoadingIndicator ref="loadingIndicator" class="flex h-full max-w-[999px] flex-col">

    <!-- Header row -->
    <div class="flex items-center justify-between mb-4 gap-3 flex-wrap">
      <div class="shrink-0">
        <h1 class="text-2xl font-semibold text-theme-text">Attachments</h1>
        <p class="text-sm text-theme-text-muted mt-0.5">
          {{ filteredAttachments.length }}
          <template v-if="filteredAttachments.length !== attachments.length">
            of {{ attachments.length }}
          </template>
          file{{ filteredAttachments.length !== 1 ? 's' : '' }}
          · {{ formatSize(filteredTotalSize) }} total
        </p>
      </div>

      <!-- Search + sort + refresh controls -->
      <div class="flex items-center gap-2 flex-wrap">

        <!-- Search field -->
        <div class="relative">
          <svg viewBox="0 0 24 24" class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 fill-current text-theme-text-very-muted pointer-events-none">
            <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search attachments…"
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

        <!-- Usage filter -->
        <div class="flex rounded border border-theme-border overflow-hidden text-xs">
          <button
            v-for="opt in USAGE_FILTERS"
            :key="opt.value"
            @click="usageFilter = opt.value"
            :class="[
              'px-2.5 py-1.5 transition-colors',
              usageFilter === opt.value
                ? 'bg-theme-brand text-white'
                : 'bg-theme-background-elevated text-theme-text-muted hover:bg-theme-border'
            ]"
            :title="opt.label"
          >{{ opt.label }}</button>
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
            <option value="name">Name</option>
            <option value="category">Category</option>
            <option value="size">Size</option>
            <option value="usage">Usage</option>
          </select>
          <!-- Chevron icon -->
          <svg viewBox="0 0 24 24" class="absolute right-1.5 top-1/2 -translate-y-1/2 w-4 h-4 fill-current text-theme-text-very-muted pointer-events-none">
            <path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
          </svg>
        </div>

        <!-- Sort direction toggle -->
        <button
          @click="sortAsc = !sortAsc"
          class="flex items-center justify-center w-8 h-8 rounded border border-theme-border
                 bg-theme-background-elevated text-theme-text-muted hover:bg-theme-border transition-colors"
          :title="sortAsc ? 'Ascending — click for descending' : 'Descending — click for ascending'"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current transition-transform"
               :class="{ 'rotate-180': !sortAsc }">
            <path d="M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"/>
          </svg>
        </button>

        <!-- Refresh -->
        <button
          @click="load"
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

    <!-- Empty state: no attachments at all -->
    <div
      v-if="!loading && attachments.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
      </svg>
      <p class="text-sm">No attachments yet.</p>
    </div>

    <!-- Empty state: no results after filtering -->
    <div
      v-else-if="!loading && attachments.length > 0 && filteredAttachments.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
      </svg>
      <p class="text-sm">No attachments match your search.</p>
      <button
        @click="clearFilters"
        class="text-xs text-theme-brand hover:underline"
      >Clear filters</button>
    </div>

    <!-- Attachment list -->
    <div v-else class="flex flex-col gap-3 overflow-y-auto flex-1 pb-4">
      <div
        v-for="att in filteredAttachments"
        :key="att.filename"
        class="rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <!-- Left side: thumbnail + info -->
        <div class="flex items-start gap-3 min-w-0 flex-1">

          <!-- Thumbnail -->
          <div class="shrink-0 w-12 h-12 rounded-lg bg-theme-background-elevated
                      border border-theme-border flex items-center justify-center overflow-hidden">
            <img
              v-if="att.is_image"
              :src="att.url"
              :alt="att.filename"
              class="w-full h-full object-cover"
              loading="lazy"
            />
            <div v-else class="flex items-center justify-center">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                   :style="{ backgroundColor: getFileInfo(att.filename).color }">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-white">
                  <path :d="getFileInfo(att.filename).iconPath" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Info column -->
          <div class="min-w-0 flex-1">
            <!-- Filename + copy URL -->
            <div class="flex items-center gap-2 mb-1">
              <a
                :href="att.url"
                target="_blank"
                class="font-medium text-theme-text hover:text-theme-brand transition-colors truncate text-sm"
                :title="att.filename"
              >{{ att.filename }}</a>
              <button
                @click="copyUrl(att.url)"
                class="shrink-0 text-theme-text-muted hover:text-theme-text transition-colors"
                title="Copy URL"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
                </svg>
              </button>
            </div>

            <!-- Size + category badge + usage -->
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-theme-text-muted">
              <span>{{ formatSize(att.size_bytes) }}</span>
              <!-- Category badge -->
              <span
                class="px-1.5 py-0.5 rounded text-white font-medium uppercase tracking-wide"
                style="font-size: 0.6rem;"
                :style="{ backgroundColor: getFileInfo(att.filename).color }"
              >{{ getCategory(att) }}</span>
              <!-- Usage -->
              <span v-if="att.used_in.length === 0" class="text-theme-text-very-muted italic">
                Not used in any notes
              </span>
              <span v-else class="flex items-center gap-1 flex-wrap">
                <span class="text-theme-text-very-muted">Used in:</span>
                <RouterLink
                  v-for="noteTitle in att.used_in"
                  :key="noteTitle"
                  :to="{ name: 'note', params: { title: noteTitle } }"
                  class="text-theme-brand hover:underline"
                >{{ noteName(noteTitle) }}</RouterLink>
              </span>
            </div>
          </div>
        </div>

        <!-- Right side: action buttons -->
        <div class="flex gap-2 shrink-0">
          <!-- Preview -->
          <a
            v-if="canPreview(att)"
            :href="att.url"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            :title="`Preview ${att.filename} in new tab`"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
            </svg>
          </a>

          <!-- Download -->
          <a
            v-else
            :href="att.url"
            download
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            :title="`Download ${att.filename}`"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
            </svg>
          </a>

          <!-- Delete (unused only) -->
          <button
            v-if="att.used_in.length === 0"
            @click="requestDelete(att)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
            title="Delete attachment"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
          </button>

          <!-- In-use lock indicator -->
          <span
            v-else
            class="inline-flex items-center gap-1 text-xs text-theme-text-very-muted"
            title="Remove references from notes before deleting"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
            </svg>
          </span>
        </div>
      </div>
    </div>
  </LoadingIndicator>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { useToast } from "primevue/usetoast";
import { listAttachments, deleteAttachment } from "../api.js";
import { getToastOptions } from "../helpers.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";

const loadingIndicator = ref();
const loading = ref(false);
const attachments = ref([]);
const toast = useToast();

const isDeleteModalVisible = ref(false);
const pendingDelete = ref(null);

// ── Search / filter / sort state ─────────────────────────────────────────────
const searchQuery = ref('');
const sortKey     = ref('name');   // 'name' | 'category' | 'size' | 'usage'
const sortAsc     = ref(true);

const USAGE_FILTERS = [
  { value: 'all',     label: 'All'     },
  { value: 'in_use',  label: 'In use'  },
  { value: 'unused',  label: 'Unused'  },
];
const usageFilter = ref('all');

function clearFilters() {
  searchQuery.value = '';
  usageFilter.value = 'all';
  sortKey.value     = 'name';
  sortAsc.value     = true;
}

// ── Category ordering for "category" sort ────────────────────────────────────
// Lower number = earlier in ascending order.
const CATEGORY_ORDER = {
  Image: 0, PDF: 1, Document: 2, Spreadsheet: 3, Presentation: 4,
  'Apple iWork': 5, Text: 6, Data: 7, Web: 8, Archive: 9,
  Code: 10, Audio: 11, Video: 12, Font: 13, Other: 14,
};

// ── Derived list ─────────────────────────────────────────────────────────────
const filteredAttachments = computed(() => {
  let list = attachments.value;

  // 1. Text search (filename)
  const q = searchQuery.value.trim().toLowerCase();
  if (q) {
    list = list.filter(a => a.filename.toLowerCase().includes(q));
  }

  // 2. Usage filter
  if (usageFilter.value === 'in_use') {
    list = list.filter(a => a.used_in.length > 0);
  } else if (usageFilter.value === 'unused') {
    list = list.filter(a => a.used_in.length === 0);
  }

  // 3. Sort
  list = [...list].sort((a, b) => {
    let cmp = 0;
    if (sortKey.value === 'name') {
      cmp = a.filename.localeCompare(b.filename, undefined, { sensitivity: 'base' });
    } else if (sortKey.value === 'category') {
      const catA = CATEGORY_ORDER[getCategory(a)] ?? 99;
      const catB = CATEGORY_ORDER[getCategory(b)] ?? 99;
      cmp = catA - catB || a.filename.localeCompare(b.filename, undefined, { sensitivity: 'base' });
    } else if (sortKey.value === 'size') {
      cmp = a.size_bytes - b.size_bytes;
    } else if (sortKey.value === 'usage') {
      // Sort by number of references, then by filename
      cmp = a.used_in.length - b.used_in.length
         || a.filename.localeCompare(b.filename, undefined, { sensitivity: 'base' });
    }
    return sortAsc.value ? cmp : -cmp;
  });

  return list;
});

const filteredTotalSize = computed(() =>
  filteredAttachments.value.reduce((sum, a) => sum + a.size_bytes, 0)
);

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function noteName(title) {
  const parts = title.split("/");
  return parts[parts.length - 1];
}

// Human-readable category label derived from the attachment's flags / extension.
function getCategory(att) {
  if (att.is_image) return 'Image';
  if (att.is_pdf)   return 'PDF';
  const ext = att.filename.split('.').pop().toLowerCase();
  const map = {
    doc: 'Document', docx: 'Document', odt: 'Document',
    xls: 'Spreadsheet', xlsx: 'Spreadsheet', ods: 'Spreadsheet', csv: 'Spreadsheet',
    ppt: 'Presentation', pptx: 'Presentation', odp: 'Presentation',
    numbers: 'Apple iWork', pages: 'Apple iWork', key: 'Apple iWork',
    txt: 'Text', rtf: 'Text',
    json: 'Data', yaml: 'Data', yml: 'Data', xml: 'Data', toml: 'Data',
    html: 'Web', htm: 'Web',
    zip: 'Archive', gz: 'Archive', tar: 'Archive', '7z': 'Archive',
    rar: 'Archive', bz2: 'Archive', xz: 'Archive',
    js: 'Code', ts: 'Code', py: 'Code', sh: 'Code', rb: 'Code', php: 'Code', vue: 'Code',
    mp3: 'Audio', m3u: 'Audio', m4a: 'Audio', ogg: 'Audio', wav: 'Audio', flac: 'Audio', aac: 'Audio',
    mp4: 'Video', mkv: 'Video', mov: 'Video', avi: 'Video', webm: 'Video',
    ttf: 'Font', otf: 'Font', woff: 'Font',
  };
  return map[ext] ?? 'Other';
}

async function load() {
  loading.value = true;
  try {
    attachments.value = await listAttachments();
  } catch {
    toast.add(getToastOptions("Failed to load attachments.", "Error", "error"));
  } finally {
    loading.value = false;
    loadingIndicator.value?.setLoaded();
  }
}

function copyUrl(url) {
  const full = `${window.location.origin}/${url}`;
  navigator.clipboard.writeText(full).then(() => {
    toast.add(getToastOptions("URL copied to clipboard.", "Copied", "success"));
  }).catch(() => {
    toast.add(getToastOptions("Could not copy URL.", "Error", "error"));
  });
}

function requestDelete(att) {
  pendingDelete.value = att;
  isDeleteModalVisible.value = true;
}

async function confirmDelete() {
  if (!pendingDelete.value) return;
  try {
    await deleteAttachment(pendingDelete.value.filename);
    attachments.value = attachments.value.filter(
      a => a.filename !== pendingDelete.value.filename
    );
    toast.add(getToastOptions("Attachment deleted.", "Deleted", "success"));
  } catch {
    toast.add(getToastOptions("Failed to delete attachment.", "Error", "error"));
  } finally {
    pendingDelete.value = null;
  }
}

// ── SVG icon paths, one per visual category ──────────────────────────────────
const FILE_ICON_PATHS = {
  // Generic document / file
  file:  'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z',
  
  // Archive / zip
  zip:   'M14,17H12V15H10V13H12V11H10V9H12V7H10V5H12V3H6A2,2 0 0,0 4,5V19A2,2 0 0,0 6,21H18A2,2 0 0,0 20,19V9L14,3V5H16V7H14V9H16V11H14V13H16V15H14V17M14,17',
  
  // Music note
  audio: 'M21,3V15.5A3.5,3.5 0 0,1 17.5,19A3.5,3.5 0 0,1 14,15.5A3.5,3.5 0 0,1 17.5,12C18.04,12 18.55,12.12 19,12.34V6.47L9,8.6V17.5A3.5,3.5 0 0,1 5.5,21A3.5,3.5 0 0,1 2,17.5A3.5,3.5 0 0,1 5.5,14C6.04,14 6.55,14.12 7,14.34V6L21,3Z',
  
  // Video camera
  video: 'M17,10.5V7A1,1 0 0,0 16,6H4A1,1 0 0,0 3,7V17A1,1 0 0,0 4,18H16A1,1 0 0,0 17,17V13.5L21,17.5V6.5L17,10.5Z',
  
  // Code files (angle brackets / braces)
  code:  'M8,3L16,3L20,7L20,21L4,21L4,7L8,3M8,5L6,7L6,19L18,19L18,9L14,9L14,5L8,5M9,11L7,13L9,15M13,11L15,13L13,15',
  
  // Web files (globe)
  web:   'M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12C4,14 4.8,15.8 6.1,17.1C7.1,15.6 8.6,14.5 10.3,14C9.5,13.2 9,12.2 9,11C9,9.6 9.8,8.4 10.8,7.6C10.3,6.9 9.5,6.3 8.6,6C9.6,5.1 10.8,4.5 12,4.3V5C12,6.1 11.1,7 10,7H9V9C9,9.6 8.6,10 8,10H6V12H8C8.6,12 9,12.4 9,13V15H11C11.6,15 12,15.4 12,16V18H14V16.9C14,15.7 14.9,14.8 16.1,14.8C16.8,14.8 17.5,15.2 17.8,15.9C18.7,14.8 19.2,13.5 19.2,12.1C19.2,10.6 18.7,9.2 17.8,8.1L17,9H15V7H13V5.3C14.2,5.5 15.4,6.1 16.4,7Z',
  
  // Data files (database cylinder)
  data:  'M12,2C8.13,2 5,4.69 5,8C5,11.31 8.13,14 12,14C15.87,14 19,11.31 19,8C19,4.69 15.87,2 12,2M12,4C14.21,4 16,5.79 16,8C16,10.21 14.21,12 12,12C9.79,12 8,10.21 8,8C8,5.79 9.79,4 12,4M5,16V19C5,22.31 8.13,25 12,25C15.87,25 19,22.31 19,19V16C17.5,17.6 14.9,18.5 12,18.5C9.1,18.5 6.5,17.6 5,16M7,19.5C7,17.6 9.2,16 12,16C14.8,16 17,17.6 17,19.5C17,21.4 14.8,23 12,23C9.2,23 7,21.4 7,19.5Z',
  
  // Spreadsheet (grid/chart)
  spreadsheet: 'M4,2H20A2,2 0 0,1 22,4V20A2,2 0 0,1 20,22H4A2,2 0 0,1 2,20V4A2,2 0 0,1 4,2M4,4V8H20V4H4M4,20H20V10H4V20M6,12H8V14H6V12M6,16H8V18H6V16M10,12H18V14H10V12M10,16H15V18H10V16Z',
  
  // Presentation (slides/chart)
  presentation: 'M8,4H16V2H8V4M18,8H20V18H18V8M4,8H6V18H4V8M2,20H22V22H2V20M12,4C15.3,4 18,6.7 18,10V18H6V10C6,6.7 8.7,4 12,4M12,6C9.8,6 8,7.8 8,10V16H16V10C16,7.8 14.2,6 12,6Z',
  
  // Text file
  text: 'M4,4H20V20H4V4M6,6V18H18V6H6M8,8H16V10H8V8M8,12H14V14H8V12M8,16H12V18H8V16Z',
  
  // Apple iWork
  iwork: 'M12,2C6.48,2 2,6.48 2,12C2,17.52 6.48,22 12,22C17.52,22 22,17.52 22,12C22,6.48 17.52,2 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M11,7V9H9V11H11V13H9V15H11V17H13V15H15V13H13V11H15V9H13V7H11Z',
  
  // Font file
  font: 'M9.5,7L8.9,5H6L10,18H12L16,5H13.1L12.5,7H9.5M10.5,9H11.5L13,14H9L10.5,9Z',
};

const EXT_INFO = {
  pdf:      { color: '#EF4444', icon: 'file' },
  doc:      { color: '#2B5797', icon: 'file' }, docx: { color: '#2B5797', icon: 'file' }, odt: { color: '#2B5797', icon: 'file' },
  xls:      { color: '#217346', icon: 'spreadsheet' }, xlsx: { color: '#217346', icon: 'spreadsheet' }, ods: { color: '#217346', icon: 'spreadsheet' }, csv: { color: '#217346', icon: 'spreadsheet' },
  ppt:      { color: '#D04423', icon: 'presentation' }, pptx: { color: '#D04423', icon: 'presentation' }, odp: { color: '#D04423', icon: 'presentation' },
  numbers:  { color: '#FFA500', icon: 'iwork' }, pages: { color: '#FFA500', icon: 'iwork' }, key: { color: '#FFA500', icon: 'iwork' },
  txt:      { color: '#6B7280', icon: 'text' }, rtf: { color: '#6B7280', icon: 'text' },
  json:     { color: '#F59E0B', icon: 'data' }, yaml: { color: '#F59E0B', icon: 'data' }, yml: { color: '#F59E0B', icon: 'data' }, xml: { color: '#F59E0B', icon: 'data' }, toml: { color: '#F59E0B', icon: 'data' },
  html:     { color: '#3B82F6', icon: 'web' }, htm: { color: '#3B82F6', icon: 'web' },
  zip:      { color: '#8B5CF6', icon: 'zip' }, gz: { color: '#8B5CF6', icon: 'zip' }, tar: { color: '#8B5CF6', icon: 'zip' },
  '7z':     { color: '#8B5CF6', icon: 'zip' }, rar: { color: '#8B5CF6', icon: 'zip' }, bz2: { color: '#8B5CF6', icon: 'zip' }, xz: { color: '#8B5CF6', icon: 'zip' },
  js:       { color: '#3776AB', icon: 'code' }, ts: { color: '#3776AB', icon: 'code' }, py: { color: '#3776AB', icon: 'code' }, vue: { color: '#3776AB', icon: 'code' },
  sh:       { color: '#3776AB', icon: 'code' }, rb: { color: '#3776AB', icon: 'code' }, php: { color: '#3776AB', icon: 'code' },
  mp3:      { color: '#EC4899', icon: 'audio' }, m3u: { color: '#EC4899', icon: 'audio' }, m4a: { color: '#EC4899', icon: 'audio' }, ogg: { color: '#EC4899', icon: 'audio' },
  wav:      { color: '#EC4899', icon: 'audio' }, flac: { color: '#EC4899', icon: 'audio' }, aac: { color: '#EC4899', icon: 'audio' },
  mp4:      { color: '#F97316', icon: 'video' }, mkv: { color: '#F97316', icon: 'video' }, mov: { color: '#F97316', icon: 'video' },
  avi:      { color: '#F97316', icon: 'video' }, webm: { color: '#F97316', icon: 'video' },
  ttf:      { color: '#6B7280', icon: 'font' }, otf: { color: '#6B7280', icon: 'font' }, woff: { color: '#6B7280', icon: 'font' },
};

function getFileInfo(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const entry = EXT_INFO[ext];
  return {
    color:    entry?.color    ?? '#6B7280',
    iconPath: FILE_ICON_PATHS[entry?.icon ?? 'file'],
  };
}

const PREVIEW_EXTS = new Set(['pdf', 'txt', 'rtf', 'json', 'xml', 'html', 'htm']);

function canPreview(att) {
  if (att.is_image) return true;
  const ext = att.filename.split('.').pop().toLowerCase();
  return PREVIEW_EXTS.has(ext);
}

onMounted(load);
</script>