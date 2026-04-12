<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="isDeleteModalVisible"
    title="Confirm Deletion"
    :message="`Move '${note.title}' to Trash? You can restore it from the Trash menu.`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="deleteConfirmedHandler"
  />

  <!-- Confirm Archive Modal -->
  <ConfirmModal
    v-model="isArchiveModalVisible"
    title="Archive Note"
    :message="`Move '${note.title}' to the archive?`"
    confirmButtonText="Archive"
    confirmButtonStyle="cta"
    @confirm="archiveConfirmedHandler"
  />

  <!-- Save Changes Modal -->
  <ConfirmModal
    v-model="isSaveChangesModalVisible"
    title="Save Changes"
    message="Do you want to save your changes?"
    confirmButtonText="Save"
    confirmButtonStyle="success"
    rejectButtonText="Discard"
    rejectButtonStyle="danger"
    @confirm="saveHandler((close = true))"
    @reject="closeNote"
  />

  <!-- Draft Modal -->
  <ConfirmModal
    v-model="isDraftModalVisible"
    title="Draft Detected"
    message="There is an unsaved draft of this note stored in this browser. Do you want to resume the draft version or delete it?"
    confirmButtonText="Resume Draft"
    confirmButtonStyle="cta"
    rejectButtonText="Delete Draft"
    rejectButtonStyle="danger"
    @confirm="setEditMode()"
    @reject="
      clearDraft();
      setEditMode();
    "
  />

  <LoadingIndicator ref="loadingIndicator" class="flex h-full flex-col">
    <!-- Edit Mode: full scrollable content -->
    <template v-if="editMode">
      <!-- Header (scrolls in edit mode) -->
      <div class="flex flex-col-reverse md:flex-row md:items-baseline shrink-0">
        <!-- Title area: breadcrumb + title -->
        <div class="grow truncate">
          <!-- Folder breadcrumb -->
          <div v-if="noteFolder" class="text-xs text-theme-text-very-muted mb-0.5 flex items-center gap-1">
            <span v-for="(part, i) in folderParts" :key="i" class="flex items-center gap-1">
              <RouterLink
                :to="{ name: 'search', query: { term: '*', folder: part.path, sortBy: 1 } }"
                class="hover:text-theme-brand transition-colors"
              >{{ part.name }}</RouterLink>
              <span v-if="i < folderParts.length - 1">/</span>
            </span>
            <span>/</span>
          </div>
          <div class="text-3xl leading-[1.6em] relative">
            <input
              ref="titleInputEl"
              v-model.trim="newTitle"
              class="w-full bg-theme-background outline-none"
              placeholder="Title (use / for folders, e.g. work/todo)"
              @input="onTitleInput"
              @keydown="onTitleKeydown"
            />
            <!-- Folder path autocomplete dropdown -->
            <TagAutocomplete
              :visible="folderAcVisible"
              :matches="folderAcMatches"
              :counts="{}"
              :activeIndex="folderAcIndex"
              :anchorRect="folderAcAnchorRect"
              mode="folder"
              @choose="selectFolder"
              @hide="folderAcVisible = false"
            />
          </div>
        </div>

        <!-- Buttons -->
        <div class="flex shrink-0 self-end md:self-baseline print:hidden">
          <!-- Save Button -->
          <CustomButton
            label="Save"
            :iconPath="mdilContentSave"
            @click="saveHandler((close = false))"
            class="relative ml-1"
          >
            <div
              v-show="unsavedChanges"
              class="absolute right-1 h-1.5 w-1.5 rounded-full bg-theme-brand"
            ></div>
          </CustomButton>
          <!-- Edit Toggle (shows "Cancel" in edit mode) -->
          <Toggle
            v-if="canModify"
            label="Cancel"
            :isOn="editMode"
            class="ml-1"
            @click="toggleEditModeHandler"
          />
        </div>
      </div>

      <hr class="my-4 border-theme-border" />

      <!-- Content -->
      <div class="flex-1 min-h-0">
        <ToastEditor
          ref="toastEditor"
          :initialValue="getInitialEditorValue()"
          :initialEditType="loadDefaultEditorMode()"
          :addImageBlobHook="addImageBlobHook"
          @change="startContentChangedTimeout"
          @keydown="keydownHandler"
        />
      </div>
    </template>

    <!-- View Mode: fixed header with scrollable content -->
    <template v-else>
      <!-- Fixed Header (does not scroll) -->
      <div class="shrink-0">
        <!-- Header -->
        <div class="flex flex-col-reverse md:flex-row md:items-baseline">
          <!-- Title area: breadcrumb + title -->
          <div class="grow truncate">
            <!-- Folder breadcrumb -->
            <div v-if="noteFolder" class="text-xs text-theme-text-very-muted mb-0.5 flex items-center gap-1">
              <span v-for="(part, i) in folderParts" :key="i" class="flex items-center gap-1">
                <RouterLink
                  :to="{ name: 'search', query: { term: '*', folder: part.path, sortBy: 1 } }"
                  class="hover:text-theme-brand transition-colors"
                >{{ part.name }}</RouterLink>
                <span v-if="i < folderParts.length - 1">/</span>
              </span>
              <span>/</span>
            </div>
            <div class="text-3xl leading-[1.6em]">
              <span :title="note.title">{{ noteBasename }}</span>
            </div>
          </div>

          <!-- Buttons -->
          <div class="flex shrink-0 self-end md:self-baseline print:hidden">
            <!-- Prev/Next navigation buttons (only in folders) -->
            <template v-if="noteFolder && folderNotes.length > 0 && !isArchivedNote && !note.title.startsWith('_trash/')">
              <button
                @click="goToPrevNote"
                :disabled="!hasPrevNote"
                class="p-1 rounded hover:bg-theme-background-elevated transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                :title="hasPrevNote ? `Previous: ${prevNoteTitle}` : 'No previous note'"
              >
                <svg viewBox="0 0 24 24" class="w-6 h-6 fill-current text-theme-text-muted">
                  <path d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z"/>
                </svg>
              </button>
              <button
                @click="goToNextNote"
                :disabled="!hasNextNote"
                class="p-1 rounded hover:bg-theme-background-elevated transition-colors disabled:opacity-30 disabled:cursor-not-allowed mr-1"
                :title="hasNextNote ? `Next: ${nextNoteTitle}` : 'No next note'"
              >
                <svg viewBox="0 0 24 24" class="w-6 h-6 fill-current text-theme-text-muted">
                  <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
                </svg>
              </button>
            </template>

            <!-- Pin/Unpin Button -->
            <CustomButton
              v-show="canModify && !isNewNote"
              :iconPath="isPinned ? mdiPin : mdiPinOutline"
              :label="isPinned ? 'Unpin' : 'Pin'"
              @click="togglePin"
              :class="isPinned ? 'pin-active' : ''"
            />
            <!-- Archive/Unarchive Button -->
            <CustomButton
              v-show="canModify && !isNewNote"
              :label="isArchivedNote ? 'Unarchive' : 'Archive'"
              :iconPath="mdiArchive"
              @click="isArchivedNote ? unarchiveHandler() : archiveHandler()"
            />
            <!-- Delete (Trash) Button -->
            <CustomButton
              v-show="canModify && !isNewNote"
              label=""
              :iconPath="mdilDelete"
              @click="deleteHandler" title="Move to Trash"
            />
            <!-- Edit Toggle -->
            <Toggle
              v-if="canModify"
              label="Edit"
              :isOn="editMode"
              class="ml-1"
              @click="toggleEditModeHandler" title="Edit Note"
            />
          </div>
        </div>

        <hr class="my-4 border-theme-border" />
      </div>

      <!-- Scrollable Content Area -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <ToastViewer
          :initialValue="note.content"
          :created="note.createdAsString"
          :updated="note.updatedAsString"
          :title="note.title"
          :folder="noteFolder"
          :tags="noteTags"
          class="toast-viewer pb-4"
        />

        <!-- Timestamps footer (scrolls with content) -->
        <div
          v-if="!isNewNote && (note.createdAsString || note.updatedAsString)"
          class="mt-4 pt-3 border-t border-theme-border flex flex-wrap gap-x-6 gap-y-2 print:hidden"
        >
          <span
            v-if="note.createdAsString"
            class="fn-timestamp flex items-center gap-1.5"
            title="Creation time"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current shrink-0">
              <path d="M19,3H18V1H16V3H8V1H6V3H5A2,2 0 0,0 3,5V21A2,2 0 0,0 5,23H19A2,2 0 0,0 21,21V5A2,2 0 0,0 19,3M19,21H5V8H19V21Z"/>
            </svg>
            Created: {{ note.createdAsString }}
          </span>
          <span
            v-if="note.updatedAsString"
            class="fn-timestamp flex items-center gap-1.5"
            title="Last updated"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current shrink-0">
              <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
            </svg>
            Updated: {{ note.updatedAsString }}
          </span>
        </div>
      </div>
    </template>
  </LoadingIndicator>
</template>

<style>
/* Disable checkboxes in view mode. See https://github.com/nhn/tui.editor/issues/1087. */
.toast-viewer li.task-list-item {
  pointer-events: none;
}
.toast-viewer li.task-list-item a {
  pointer-events: auto;
}
</style>

<style scoped>
/* Pin button: brand color when pinned, inherits muted grey from CustomButton when not */
.pin-active {
  color: rgb(var(--theme-brand));
}
</style>

<script setup>
import { mdiArchive, mdiNoteOffOutline, mdiPin, mdiPinOutline } from "@mdi/js";
import { mdilContentSave, mdilDelete } from "@mdi/light-js";
import Mousetrap from "mousetrap";
import { useToast } from "primevue/usetoast";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouterLink } from "vue-router";

import {
  apiErrorHandler,
  archiveNote,
  createAttachment,
  createNote,
  deleteNote,
  getNote,
  unarchiveNote,
  updateNote,
  pinNote,
  unpinNote,
  getFolders,
  getFolderNotes,
} from "../api.js";
import { Note } from "../classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomButton from "../components/CustomButton.vue";
import TagAutocomplete from "../components/TagAutocomplete.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import Toggle from "../components/Toggle.vue";
import ToastEditor from "../components/toastui/ToastEditor.vue";
import ToastViewer from "../components/toastui/ToastViewer.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions } from "../helpers.js";
import { isCurrentTokenStored } from "../tokenStorage.js";

const props = defineProps({
  title: String,
});

const route = useRoute();
const canModify = computed(
  () => globalStore.config.authType != authTypes.readOnly,
);
let contentChangedTimeout = null;
const editMode = ref(false);
const globalStore = useGlobalStore();
const isSaveChangesModalVisible = ref(false);
const isDeleteModalVisible = ref(false);
const isArchiveModalVisible = ref(false);
const isDraftModalVisible = ref(false);
const isNewNote = computed(() => !props.title);
const isArchivedNote = computed(() => note.value.title?.startsWith("_archive/"));
const loadingIndicator = ref();
const note = ref({});
const reservedFilenameCharacters = /[<>"\\|?*]/; // slash allowed
const router = useRouter();
const newTitle = ref();
const toast = useToast();
const toastEditor = ref();
const unsavedChanges = ref(false);

// ── Folder navigation state ───────────────────────────────────────────────────
const folderNotes = ref([]);
const currentIndex = ref(-1);

// Computed navigation helpers
const hasPrevNote = computed(() => currentIndex.value > 0);
const hasNextNote = computed(() => currentIndex.value < folderNotes.value.length - 1 && currentIndex.value !== -1);
const prevNoteTitle = computed(() => hasPrevNote.value ? folderNotes.value[currentIndex.value - 1] : "");
const nextNoteTitle = computed(() => hasNextNote.value ? folderNotes.value[currentIndex.value + 1] : "");

// ── Folder autocomplete in the title input ────────────────────────────────────
const titleInputEl = ref(null);
const folderAcVisible = ref(false);
const folderAcMatches = ref([]);
const folderAcIndex = ref(0);
const folderAcAnchorRect = ref(null);
let folderListCache = null;

async function ensureFolderListLoaded() {
  if (folderListCache !== null) return;
  try {
    const data = await getFolders();
    folderListCache = Object.keys(data).sort();
  } catch {
    folderListCache = [];
  }
}

async function loadFolderNotes() {
  if (!noteFolder.value) {
    folderNotes.value = [];
    currentIndex.value = -1;
    return;
  }
  
  try {
    const notes = await getFolderNotes(noteFolder.value);
    folderNotes.value = notes;
    // Find current note's index
    const index = notes.findIndex(t => t === note.value.title);
    currentIndex.value = index;
  } catch {
    folderNotes.value = [];
    currentIndex.value = -1;
  }
}

function goToPrevNote() {
  if (hasPrevNote.value) {
    const prevTitle = folderNotes.value[currentIndex.value - 1];
    router.push({ name: "note", params: { title: prevTitle } });
  }
}

function goToNextNote() {
  if (hasNextNote.value) {
    const nextTitle = folderNotes.value[currentIndex.value + 1];
    router.push({ name: "note", params: { title: nextTitle } });
  }
}

function onTitleInput() {
  if (!editMode.value) return;
  
  const val = (newTitle.value || "");
  const slashIdx = val.indexOf("/");
  if (slashIdx === -1 || slashIdx === 0) {
    folderAcVisible.value = false;
    return;
  }
  const lower = val.toLowerCase();
  const matchPrefix = lower.endsWith("/") ? lower.slice(0, -1) : lower;
  ensureFolderListLoaded().then(() => {
    const matches = folderListCache
      .filter((f) => {
        const fl = f.toLowerCase();
        return fl.startsWith(matchPrefix) && fl !== lower.replace(/\/$/, "");
      })
      .slice(0, 10);
    if (matches.length === 0) {
      folderAcVisible.value = false;
      return;
    }
    folderAcMatches.value = matches;
    folderAcIndex.value = 0;
    folderAcVisible.value = true;
    if (titleInputEl.value) {
      folderAcAnchorRect.value = titleInputEl.value.getBoundingClientRect();
    }
  });
}

function onTitleKeydown(e) {
  if (!editMode.value) return;
  
  if (!folderAcVisible.value) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    folderAcIndex.value = Math.min(folderAcIndex.value + 1, folderAcMatches.value.length - 1);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    folderAcIndex.value = Math.max(folderAcIndex.value - 1, 0);
  } else if (e.key === "Tab" || e.key === "Enter") {
    if (folderAcVisible.value) {
      e.preventDefault();
      selectFolder(folderAcMatches.value[folderAcIndex.value]);
    }
  } else if (e.key === "Escape") {
    folderAcVisible.value = false;
  }
}

function selectFolder(folder) {
  if (!editMode.value) return;
  
  newTitle.value = folder + "/";
  folderAcVisible.value = false;
  folderListCache = null;
  nextTick(() => { if (titleInputEl.value) titleInputEl.value.focus(); });
}

// Pin state
const isPinned = computed(() => {
  return note.value.content && note.value.content.includes("#pin");
});

async function togglePin() {
  try {
    let updatedNote;
    if (isPinned.value) {
      updatedNote = await unpinNote(note.value.title);
    } else {
      updatedNote = await pinNote(note.value.title);
    }
    note.value = updatedNote;
    toast.add(getToastOptions(`Note ${isPinned.value ? 'unpinned' : 'pinned'} ✓`, "Success", "success"));
    globalStore.bumpPinned();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

// Folder-aware computed helpers
const noteFolder = computed(() => {
  const t = note.value.title || "";
  const idx = t.lastIndexOf("/");
  return idx > -1 ? t.slice(0, idx) : "";
});

const noteBasename = computed(() => {
  const t = note.value.title || "";
  const idx = t.lastIndexOf("/");
  return idx > -1 ? t.slice(idx + 1) : t;
});

const folderParts = computed(() => {
  const parts = noteFolder.value.split("/");
  return parts.map((name, i) => ({
    name,
    path: parts.slice(0, i + 1).join("/"),
  }));
});

const noteTags = computed(() => {
  if (!note.value.content) return [];
  const tags = [];
  const tagMatches = note.value.content.match(/(?:^|\s)#[a-zA-Z0-9_/-]+/g);
  if (tagMatches) {
    tags.push(...tagMatches.map(t => t.trim().substring(1)));
  }
  return tags;
});

async function init() {
  if (props.title && props.title == note.value.title) {
    return;
  }

  loadingIndicator.value.setLoading();
  if (props.title) {
    getNote(props.title)
  .then((data) => {
    note.value = data;
    loadingIndicator.value.setLoaded();
    loadFolderNotes();

    // 👇 NEW: Check for edit query and activate edit mode
    if (route.query.edit === "true" && canModify.value) {
      // Remove the edit query to prevent it from sticking on future navigations
      router.replace({ query: {} }).then(() => {
        editHandler(); // this will open the note in edit mode (handles drafts)
      });
    }
  })
      .catch((error) => {
        if (error.response?.status === 404) {
          loadingIndicator.value.setFailed("Note not found", mdiNoteOffOutline);
        } else {
          loadingIndicator.value.setFailed();
          apiErrorHandler(error, toast);
        }
      });
  } else {
    // New note – check for template query parameter
    newTitle.value = "";
    const templateName = route.query.template;
    let initialContent = "";
    if (templateName && typeof templateName === "string") {
      try {
        // Fetch the template note
        const templateNote = await getNote(`_templates/${templateName}`);
        initialContent = templateNote.content;
        toast.add(getToastOptions(`Loaded template "${templateName}"`, "Info", "info"));
        // Clear the query parameter so a page refresh doesn't reload the template
        router.replace({ query: {} });
      } catch (error) {
        console.warn("Failed to load template:", error);
        toast.add(getToastOptions("Could not load template, using empty note.", "Warning", "warn"));
      }
    }
    note.value = new Note();
    // Set content immediately for the editor
    note.value.content = initialContent;
    editMode.value = false;
    nextTick(() => {
      editHandler();
      loadingIndicator.value.setLoaded();
      // If we have initial content, ensure the editor gets it after mount
      if (initialContent && toastEditor.value) {
        // The editor will be mounted after the next tick; setMarkdownContent will be called when setEditMode runs
        // Actually, setEditMode() will call editHandler which will call setEditMode, and inside setEditMode we could set content,
        // but it's easier to set it in getInitialEditorValue() which returns note.value.content. That's already set above.
        // No extra action needed.
      }
    });
  }
}

function toggleEditModeHandler() {
  if (editMode.value) {
    closeHandler();
  } else {
    editHandler();
  }
}

function editHandler() {
  const draftContent = loadDraft();
  if (draftContent) {
    isDraftModalVisible.value = true;
  } else {
    setEditMode();
  }
}

function setEditMode() {
  newTitle.value = note.value.title;
  unsavedChanges.value = false;
  editMode.value = true;
}

function getInitialEditorValue() {
  const draftContent = loadDraft();
  return draftContent ? draftContent : note.value.content;
}

function deleteHandler() {
  isDeleteModalVisible.value = true;
}

function deleteConfirmedHandler() {
  deleteNote(note.value.title)
    .then(() => {
      toast.add(getToastOptions("Note moved to Trash ✓", "Success", "success"));
      router.push({ name: "home" });
    })
    .catch((error) => {
      apiErrorHandler(error, toast);
    });
}

function archiveHandler() {
  isArchiveModalVisible.value = true;
}

function archiveConfirmedHandler() {
  archiveNote(note.value.title)
    .then((data) => {
      toast.add(getToastOptions("Note archived ✓", "Success", "success"));
      note.value = data;
      router.replace({ name: "note", params: { title: data.title } });
      loadFolderNotes();
    })
    .catch((error) => {
      apiErrorHandler(error, toast);
    });
}

function unarchiveHandler() {
  unarchiveNote(note.value.title)
    .then((data) => {
      toast.add(getToastOptions("Note unarchived ✓", "Success", "success"));
      note.value = data;
      router.replace({ name: "note", params: { title: data.title } });
      loadFolderNotes();
    })
    .catch((error) => {
      apiErrorHandler(error, toast);
    });
}

function saveHandler(close = false) {
  saveDefaultEditorMode();

  if (!newTitle.value) {
    toast.add(
      getToastOptions("Cannot save note without a title.", "Invalid", "error"),
    );
    return;
  }

  if (reservedFilenameCharacters.test(newTitle.value)) {
    badFilenameToast("Title");
    return;
  }

  let newContent = toastEditor.value.getMarkdown();
  if (isNewNote.value) {
    saveNew(newTitle.value, newContent, close);
  } else {
    saveExisting(newTitle.value, newContent, close);
  }
}

function saveNew(newTitle, newContent, close = false) {
  createNote(newTitle, newContent)
    .then((data) => {
      clearDraft();
      note.value = data;
      router
        .push({
          name: "note",
          params: { title: note.value.title },
        })
        .then(() => {
          noteSaveSuccess(close);
          loadFolderNotes();
        });
    })
    .catch(noteSaveFailure);
}

function saveExisting(newTitle, newContent, close = false) {
  if (newTitle == note.value.title && newContent == note.value.content) {
    noteSaveSuccess(close);
    return;
  }

  updateNote(note.value.title, newTitle, newContent)
    .then((data) => {
      clearDraft();
      note.value = data;
      router.replace({ name: "note", params: { title: note.value.title } });
      noteSaveSuccess(close);
      loadFolderNotes();
    })
    .catch(noteSaveFailure);
}

function noteSaveFailure(error) {
  if (error.response?.status === 409) {
    toast.add(
      getToastOptions(
        "A note with this title already exists. Please try again with a new title.",
        "Duplicate",
        "error",
      ),
    );
  } else if (error.response?.status === 413) {
    entityTooLargeToast("note");
  } else {
    apiErrorHandler(error, toast);
  }
}

function noteSaveSuccess(close = false) {
  unsavedChanges.value = false;
  if (close) {
    closeNote();
  }
  setBeforeUnloadConfirmation(false);
  toast.add(getToastOptions("Note saved successfully ✓", "Success", "success"));
}

function closeHandler() {
  if (isContentChanged()) {
    isSaveChangesModalVisible.value = true;
  } else {
    closeNote();
  }
}

function closeNote() {
  clearDraft();
  editMode.value = false;
  if (isNewNote.value) {
    router.push({ name: "home" });
  } else {
    editMode.value = false;
  }
}

function addImageBlobHook(file, callback) {
  const altTextInputValue = document.getElementById(
    "toastuiAltTextInput",
  )?.value;

  postAttachment(file).then(function (data) {
    if (data) {
      const altText = altTextInputValue ? altTextInputValue : data.filename;
      callback(data.url, altText);
    }
  });
}

function postAttachment(file) {
  if (reservedFilenameCharacters.test(file.name)) {
    badFilenameToast("Title");
    return;
  }

  toast.add(getToastOptions("Uploading attachment..."));

  return createAttachment(file)
    .then((data) => {
      toast.add(
        getToastOptions(
          "Attachment uploaded successfully ✓",
          "Success",
          "success",
        ),
      );
      return data;
    })
    .catch((error) => {
      if (error.response?.status === 409) {
        toast.add(
          getToastOptions(
            "An attachment with this filename already exists.",
            "Duplicate",
            "error",
          ),
        );
      } else if (error.response?.status == 413) {
        entityTooLargeToast("attachment");
      } else {
        apiErrorHandler(error, toast);
      }
    });
}

function startContentChangedTimeout() {
  clearContentChangedTimeout();
  contentChangedTimeout = setTimeout(contentChangedHandler, 1000);
}

function clearContentChangedTimeout() {
  if (contentChangedTimeout != null) {
    clearTimeout(contentChangedTimeout);
  }
}

function contentChangedHandler() {
  if (isContentChanged()) {
    unsavedChanges.value = true;
    setBeforeUnloadConfirmation(true);
    saveDraft();
  } else {
    unsavedChanges.value = false;
    setBeforeUnloadConfirmation(false);
    clearDraft();
  }
}

function saveDraft() {
  const content = toastEditor.value.getMarkdown();
  const userHasPersistedToken = isCurrentTokenStored();
  if (content) {
    if (userHasPersistedToken) {
      localStorage.setItem(note.value.title, content);
    } else {
      sessionStorage.setItem(note.value.title, content);
    }
  }
}

function clearDraft() {
  localStorage.removeItem(note.value.title);
  sessionStorage.removeItem(note.value.title);
}

function loadDraft() {
  const localDraft = localStorage.getItem(note.value.title);
  const sessionDraft = sessionStorage.getItem(note.value.title);
  return localDraft || sessionDraft;
}

Mousetrap.bind("e", () => {
  if (editMode.value === false && canModify.value) {
    editHandler();
  }
});

function keydownHandler(event) {
  if ((event.ctrlKey || event.metaKey) && event.key == "Enter") {
    saveHandler((close = false));
  }
  if (event.key == "Escape") {
    closeHandler();
  }
}

function entityTooLargeToast(entityName) {
  toast.add(
    getToastOptions(
      `This ${entityName} is too large. Please try again with a smaller ${entityName} or adjust your server configuration.`,
      "Failure",
      "error",
    ),
  );
}

function badFilenameToast(entityName) {
  toast.add(
    getToastOptions(
      'Due to filename restrictions, the following characters are not allowed: <>:"/\\|?*',
      `Invalid ${entityName}`,
      "error",
    ),
  );
}

function setBeforeUnloadConfirmation(enable = true) {
  if (enable) {
    window.onbeforeunload = () => {
      return true;
    };
  } else {
    window.onbeforeunload = null;
  }
}

function saveDefaultEditorMode() {
  const isWysiwygMode = toastEditor.value.isWysiwygMode();
  localStorage.setItem(
    "defaultEditorMode",
    isWysiwygMode ? "wysiwyg" : "markdown",
  );
}

function loadDefaultEditorMode() {
  const defaultWysiwygMode = localStorage.getItem("defaultEditorMode");
  return defaultWysiwygMode || "markdown";
}

function isContentChanged() {
  return (
    newTitle.value != note.value.title ||
    toastEditor.value.getMarkdown() != note.value.content
  );
}

watch(() => props.title, init);
onMounted(init);
</script>