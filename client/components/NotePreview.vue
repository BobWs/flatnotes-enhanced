<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="popupRef"
      class="fixed z-50 note-preview-popup"
      :style="popupStyle"
      @click.stop
    >
      <div class="bg-theme-background rounded-lg shadow-xl border border-theme-border overflow-hidden w-[480px] max-h-[560px] flex flex-col">
        <!-- Header -->
        <div class="flex items-start justify-between gap-2 px-4 py-3 border-b border-theme-border bg-theme-background-elevated">
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-theme-text truncate">
              {{ displayTitle }}
            </div>
            <div v-if="noteFolder" class="text-xs text-theme-text-very-muted mt-0.5">
              {{ noteFolder }}
            </div>
          </div>
          <button
            @click="close"
            class="shrink-0 text-xs px-2 py-1 rounded bg-theme-background-elevated hover:bg-theme-border transition-colors text-theme-text-muted"
            title="Close preview"
          >
            ✕
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-4 preview-content">
          <div v-if="loading" class="flex justify-center items-center py-12">
            <svg class="animate-spin w-6 h-6 text-theme-brand" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" fill="none"/>
              <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-linecap="round" fill="none"/>
            </svg>
          </div>

          <!-- Full-fidelity render via ToastViewer when content is ready -->
          <ToastViewer
            v-else-if="noteContent"
            :initialValue="truncatedContent"
            :title="props.noteTitle"
            :folder="noteFolder"
            :created="noteCreated"
            :updated="noteUpdated"
            :tags="tags"
          />

          <div
            v-else
            class="text-center py-12 text-theme-text-very-muted text-sm"
          >
            No preview available
          </div>
        </div>

        <!-- Footer with tags -->
        <div v-if="tags.length > 0" class="px-4 py-2 border-t border-theme-border">
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tag in tags.slice(0, 8)"
              :key="tag"
              class="fn-tag text-xs"
              :style="tagStyle(tag)"
            >
              {{ formatTagDisplay(tag) }}
            </span>
            <span v-if="tags.length > 8" class="text-xs text-theme-text-very-muted">
              +{{ tags.length - 8 }} more
            </span>
          </div>
        </div>

        <!-- Open full note button -->
        <div class="px-4 py-2 border-t border-theme-border bg-theme-background-elevated">
          <button
            @click="openFullNote"
            class="w-full text-center text-sm py-1.5 rounded bg-theme-brand/10 hover:bg-theme-brand/20 text-theme-brand transition-colors"
          >
            Open full note →
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { getNote } from "../api.js";
import { tagColor as tagColorSolid, tagColorLight as tagColorLightFn } from "../tagColor.js";
import ToastViewer from "./toastui/ToastViewer.vue";

// ── Props ─────────────────────────────────────────────────────────────────────
const props = defineProps({
  noteTitle: {
    type: String,
    required: true,
  },
  target: {
    type: Object,
    default: null,
  },
});

// ── State ─────────────────────────────────────────────────────────────────────
const router = useRouter();
const visible = ref(false);
const loading = ref(false);
const noteContent = ref("");
const noteFolder = ref("");
const noteCreated = ref("");
const noteUpdated = ref("");
const tags = ref([]);
const popupRef = ref(null);
const popupStyle = ref({});

// ── Computed ──────────────────────────────────────────────────────────────────

// Show just the note's base filename (without folder prefix) in the header
const displayTitle = computed(() => {
  if (!props.noteTitle) return "";
  const folder = noteFolder.value;
  if (folder && props.noteTitle.startsWith(folder + "/")) {
    return props.noteTitle.substring(folder.length + 1);
  }
  return props.noteTitle;
});

// Truncate to ~3000 chars for the popup — ToastViewer handles the rest
const truncatedContent = computed(() => {
  const content = noteContent.value;
  if (!content) return "";
  if (content.length <= 3000) return content;
  return content.substring(0, 3000) + "\n\n…";
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function extractFolder(title) {
  const lastSlash = title.lastIndexOf("/");
  return lastSlash > 0 ? title.substring(0, lastSlash) : "";
}

function extractTags(content) {
  const tagRegex = /(?:^|\s)#([a-zA-Z0-9_][a-zA-Z0-9_/-]*)/g;
  const matches = [];
  let match;
  while ((match = tagRegex.exec(content)) !== null) {
    matches.push(match[1]);
  }
  return [...new Set(matches)];
}

function formatTagDisplay(tag) {
  if (!tag) return tag;
  return tag.split("/").join(" › ");
}

function tagStyle(tagName) {
  const solid = tagColorSolid(tagName);
  const light = tagColorLightFn(tagName);
  return {
    backgroundColor: light,
    color: solid,
    border: `1px solid ${solid}44`,
    borderRadius: "9999px",
    padding: "0 0.5rem",
    fontSize: "0.75rem",
    fontWeight: "500",
    lineHeight: "1.6",
    display: "inline-flex",
    alignItems: "center",
  };
}

// ── API load ──────────────────────────────────────────────────────────────────

async function loadPreview() {
  if (!props.noteTitle) return;

  loading.value = true;
  noteContent.value = "";

  try {
    const note = await getNote(props.noteTitle);
    noteFolder.value = extractFolder(props.noteTitle);
    noteCreated.value = note.created || "";
    noteUpdated.value = note.updated || "";
    tags.value = extractTags(note.content || "");
    // Set content last so the ToastViewer mounts with everything ready
    noteContent.value = note.content || "";
  } catch (err) {
    console.error("Failed to load preview:", err);
    noteContent.value = "> Failed to load preview.";
  } finally {
    loading.value = false;
  }
}

// ── Position calculation ──────────────────────────────────────────────────────

function calculatePosition(targetElement) {
  if (!targetElement) {
    return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
  }

  const rect = targetElement.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const popupWidth = 480;
  const popupHeight = 560;

  let top = rect.top + rect.height / 2 - popupHeight / 2;
  let left = rect.right + 12;

  if (left + popupWidth > viewportWidth) {
    left = rect.left - popupWidth - 12;
  }
  if (left < 0) {
    left = Math.max(8, rect.right + 12);
  }
  if (top < 8) {
    top = 8;
  }
  if (top + popupHeight > viewportHeight - 8) {
    top = viewportHeight - popupHeight - 8;
  }

  return { top: `${top}px`, left: `${left}px`, transform: "none" };
}

// ── Show / close ──────────────────────────────────────────────────────────────

function show() {
  if (!props.noteTitle) return;

  popupStyle.value = props.target
    ? calculatePosition(props.target)
    : { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };

  visible.value = true;
  loadPreview();

  // Click-outside handler (deferred so the triggering click doesn't immediately close)
  setTimeout(() => {
    document.addEventListener("click", handleClickOutside);
  }, 100);
}

function close() {
  visible.value = false;
  noteContent.value = "";
  noteFolder.value = "";
  noteCreated.value = "";
  noteUpdated.value = "";
  tags.value = [];
  document.removeEventListener("click", handleClickOutside);
}

function handleClickOutside(event) {
  if (popupRef.value && !popupRef.value.contains(event.target)) {
    const previewButton = props.target;
    if (
      previewButton &&
      (previewButton === event.target || previewButton.contains(event.target))
    ) {
      return;
    }
    close();
  }
}

function openFullNote() {
  close();
  router.push({ name: "note", params: { title: props.noteTitle } });
}

defineExpose({ show, close });

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
.note-preview-popup {
  animation: previewFadeIn 0.15s ease-out;
}

@keyframes previewFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/*
  The ToastViewer mounts its own stylesheet and scoped class names.
  We use :deep() overrides here to tighten spacing and font sizes
  inside the constrained popup — without touching the real note view.
*/
.preview-content :deep(.toastui-editor-contents) {
  font-size: 0.875rem;
}

.preview-content :deep(h1) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.5em 0 0.25em;
}

.preview-content :deep(h2) {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0.5em 0 0.25em;
}

.preview-content :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.5em 0 0.25em;
}

.preview-content :deep(p) {
  margin: 0 0 0.5em;
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  margin: 0 0 0.5em;
  padding-left: 1.5em;
}

.preview-content :deep(li) {
  margin: 0.1em 0;
}

.preview-content :deep(code) {
  background-color: rgb(var(--theme-background-elevated));
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-size: 0.8em;
}

.preview-content :deep(pre) {
  background-color: rgb(var(--theme-background-elevated));
  padding: 0.5rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.75rem;
  margin: 0.5em 0;
}

.preview-content :deep(blockquote) {
  border-left: 3px solid var(--theme-border);
  margin: 0.5em 0;
  padding-left: 1em;
  color: var(--theme-text-muted);
}

.preview-content :deep(table) {
  font-size: 0.75rem;
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid var(--theme-border);
  padding: 0.25rem 0.5rem;
  text-align: left;
}

.preview-content :deep(th) {
  background-color: rgb(var(--theme-background-elevated));
  font-weight: 600;
}

.preview-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.preview-content :deep(a) {
  color: rgb(var(--theme-brand));
  text-decoration: none;
}

.preview-content :deep(a:hover) {
  text-decoration: underline;
}
</style>