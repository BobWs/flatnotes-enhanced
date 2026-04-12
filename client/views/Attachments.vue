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
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text">Attachments</h1>
        <p class="text-sm text-theme-text-muted mt-0.5">
          {{ attachments.length }} file{{ attachments.length !== 1 ? 's' : '' }}
          · {{ formatSize(totalSize) }} total
        </p>
      </div>
      <button
        @click="load"
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

    <!-- Empty state -->
    <div
      v-if="!loading && attachments.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
      </svg>
      <p class="text-sm">No attachments yet.</p>
    </div>

    <!-- Attachment list - simplified to match Trash.vue structure -->
    <div v-else class="flex flex-col gap-3 overflow-y-auto flex-1 pb-4">
      <div
        v-for="att in attachments"
        :key="att.filename"
        class="rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <!-- Left side: thumbnail + info -->
        <div class="flex items-start gap-3 min-w-0 flex-1">
          <!-- Thumbnail - smaller and simpler -->
          <div class="shrink-0 w-12 h-12 rounded-lg bg-theme-background-elevated
                      border border-theme-border flex items-center justify-center overflow-hidden">
            <!-- Image -->
            <img
              v-if="att.is_image"
              :src="att.url"
              :alt="att.filename"
              class="w-full h-full object-cover"
              loading="lazy"
            />
            <!-- PDF -->
            <div v-else-if="att.is_pdf" class="flex items-center justify-center">
              <div class="w-8 h-8 rounded-lg bg-red-500 flex items-center justify-center">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-white">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
            </div>
            <!-- Document (Word, Excel, etc.) -->
            <div v-else-if="att.is_document" class="flex items-center justify-center">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                   :style="{ backgroundColor: getDocumentInfo(att.filename)?.color || '#6B7280' }">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-white">
                  <path :d="getDocumentInfo(att.filename)?.icon || 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z'" />
                </svg>
              </div>
            </div>
            <!-- Generic fallback -->
            <svg v-else viewBox="0 0 24 24" class="w-6 h-6 fill-current text-theme-text-very-muted">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
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

            <!-- Size + usage -->
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-theme-text-muted">
              <span>{{ formatSize(att.size_bytes) }}</span>
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

        <!-- Right side: smart buttons -->
        <div class="flex gap-2 shrink-0">
          <!-- Preview button for files that can be previewed in browser -->
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
          
          <!-- Download button for files that cannot be previewed in browser -->
          <a
            v-else-if="att.is_pdf || att.is_image || att.is_document"
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

          <!-- Delete button (unused attachments) - RED like Trash should be -->
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
       <!-- Delete -->
          </button>
          
          <!-- In-use indicator (used in notes) -->
          <span
            v-else
            class="inline-flex items-center gap-1 text-xs text-theme-text-very-muted"
            title="Remove references from notes before deleting"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
            </svg>
           <!-- In use -->
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

const totalSize = computed(() =>
  attachments.value.reduce((sum, a) => sum + a.size_bytes, 0)
);

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function noteName(title) {
  const parts = title.split("/");
  return parts[parts.length - 1];
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

// Helper for document icons and colors
function getDocumentInfo(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const map = {
    // Word
    doc:  { color: '#2B5797', label: 'DOC', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    docx: { color: '#2B5797', label: 'DOCX', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    // Excel
    xls:  { color: '#217346', label: 'XLS', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    xlsx: { color: '#217346', label: 'XLSX', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    // Numbers
    numbers: { color: '#FFA500', label: 'NUMBERS', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    // Pages
    pages:   { color: '#FFA500', label: 'PAGES', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    // Text
    txt:  { color: '#6B7280', label: 'TXT', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
    rtf:  { color: '#6B7280', label: 'RTF', icon: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' },
  };
  return map[ext] || null;
}

// Determine if a file can be previewed in the browser
function canPreview(att) {
  if (att.is_image) return true;  // Images can always be previewed
  if (att.is_pdf) return true;    // PDFs can be previewed in most browsers
  
  // For documents, check if it's a browser-viewable format
  if (att.is_document) {
    const ext = att.filename.split('.').pop().toLowerCase();
    // Only TXT and RTF might be viewable in some browsers
    // Most browsers will download Office files anyway
    return ['txt', 'rtf'].includes(ext);
  }
  
  return false;
}

onMounted(load);
</script>