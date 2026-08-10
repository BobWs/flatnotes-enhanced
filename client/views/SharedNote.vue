<template>
  <div class="flex h-screen flex-col pt-2 pb-4 px-2 md:px-4">

    <!-- Loading / error state -->
    <LoadingIndicator ref="loadingIndicator" class="flex h-full flex-col">

      <!-- ── Password gate ────────────────────────────────────────────────── -->
      <div
        v-if="requiresPassword"
        class="flex flex-1 flex-col items-center justify-center"
      >
        <div class="w-full max-w-sm px-4">
          <!-- Lock icon -->
          <div class="flex justify-center mb-5">
            <div class="w-16 h-16 rounded-full bg-theme-brand/10 flex items-center justify-center">
              <svg viewBox="0 0 24 24" class="w-8 h-8 fill-current text-theme-brand">
                <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
              </svg>
            </div>
          </div>

          <h2 class="text-xl font-semibold text-theme-text text-center mb-1">
            Password required
          </h2>
          <p class="text-sm text-theme-text-muted text-center mb-5">
            This shared note is password-protected.
          </p>

          <div class="space-y-3">
            <input
              ref="passwordInputEl"
              v-model="enteredPassword"
              type="password"
              placeholder="Enter password"
              autocomplete="current-password"
              class="w-full text-sm bg-theme-background-elevated border rounded-lg px-3 py-2.5
                     outline-none transition-colors text-theme-text
                     placeholder:text-theme-text-very-muted"
              :class="passwordError
                ? 'border-red-400 focus:border-red-500'
                : 'border-theme-border focus:border-theme-brand'"
              @keydown.enter="submitPassword"
            />
            <p v-if="passwordError" class="text-xs text-red-500">{{ passwordError }}</p>

            <button
              @click="submitPassword"
              :disabled="passwordChecking || !enteredPassword"
              class="w-full py-2.5 rounded-lg text-sm font-medium bg-theme-brand/90
                     hover:bg-theme-brand text-white transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ passwordChecking ? 'Checking…' : 'Continue' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ── Note content (after password cleared or no password) ────────── -->
      <template v-else-if="noteLoaded">
        <!-- Shared note header -->
        <div class="shrink-0 mb-2">

          <!-- Top bar: branding left, status right -->
          <div class="flex items-center justify-between min-h-[2rem]">
            <!-- Logo / home link -->
            <RouterLink to="/" class="flex items-center gap-2 text-theme-text-muted hover:text-theme-brand transition-colors">
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-brand">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
              </svg>
              <span class="text-sm font-semibold">flatnotes</span>
            </RouterLink>

            <!-- Permission badge + expiry -->
            <div class="flex items-center gap-2">
              <span
                v-if="share"
                class="text-xs font-medium px-2 py-0.5 rounded-full"
                :class="share.permission === 'write'
                  ? 'bg-theme-brand/15 text-theme-brand'
                  : 'bg-theme-background-elevated text-theme-text-muted border border-theme-border'"
              >
                {{ share.permission === 'write' ? 'Can edit' : 'Read only' }}
              </span>
              <span
                v-if="share && share.expires_at"
                class="text-xs text-theme-text-very-muted"
                :title="'Expires ' + formatExpiry(share.expires_at)"
              >
                Expires {{ formatExpiry(share.expires_at) }}
              </span>
            </div>
          </div>

          <!-- Note title -->
          <div class="text-3xl leading-[1.6em] mt-1 truncate text-theme-text" :title="noteBasename">
            {{ noteBasename }}
          </div>

          <!-- Folder breadcrumb -->
          <div v-if="noteFolder" class="flex items-center gap-1 text-xs text-theme-text-very-muted mt-0.5">
            <span v-for="(part, i) in folderParts" :key="i" class="flex items-center gap-1">
              <span>{{ part }}</span>
              <span v-if="i < folderParts.length - 1">/</span>
            </span>
            <span>/</span>
          </div>

          <!-- Edit mode toolbar (write permission only) -->
          <div v-if="share && share.permission === 'write'" class="flex items-center justify-end gap-1 mt-1">
            <template v-if="editMode">
              <CustomButton
                label="Save"
                :iconPath="mdilContentSave"
                @click="saveHandler"
                class="relative"
              >
                <div v-show="unsavedChanges" class="absolute right-1 h-1.5 w-1.5 rounded-full bg-theme-brand"></div>
              </CustomButton>
              <Toggle label="Cancel" :isOn="true" class="ml-1" @click="exitEdit" />
            </template>
            <Toggle v-else label="Edit" :isOn="false" class="ml-1" @click="enterEdit" />
          </div>

          <hr class="my-3 border-theme-border" />
        </div>

        <!-- View mode -->
        <div v-if="!editMode" class="flex-1 overflow-y-auto min-h-0">
          <ToastViewer
            v-if="note"
            :initialValue="note.content"
            :created="note.createdAsString"
            :updated="note.updatedAsString"
            :title="note.title"
            :folder="noteFolder"
            :tags="[]"
            class="pb-4"
          />
        </div>

        <!-- Edit mode -->
        <div v-else class="flex-1 min-h-0">
          <ToastEditor
            ref="toastEditor"
            :initialValue="note ? note.content : ''"
            initialEditType="markdown"
            @change="onContentChange"
            @keydown="onEditorKeydown"
          />
        </div>
      </template>

    </LoadingIndicator>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { RouterLink } from "vue-router";
import { useToast } from "primevue/usetoast";
import { mdilContentSave } from "@mdi/light-js";
import { mdiNoteOffOutline } from "@mdi/js";

import { getSharedNote, updateSharedNote, validateShare } from "../api.js";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import CustomButton from "../components/CustomButton.vue";
import Toggle from "../components/Toggle.vue";
import ToastViewer from "../components/toastui/ToastViewer.vue";
import ToastEditor from "../components/toastui/ToastEditor.vue";
import { getToastOptions } from "../helpers.js";

const props = defineProps({ token: { type: String, required: true } });

const loadingIndicator = ref();
const toast            = useToast();
const note             = ref(null);
const share            = ref(null);
const editMode         = ref(false);
const unsavedChanges   = ref(false);
const toastEditor      = ref();

// ── Password gate state ───────────────────────────────────────────────────────
const requiresPassword  = ref(false);
const noteLoaded        = ref(false);
const enteredPassword   = ref("");
const passwordError     = ref("");
const passwordChecking  = ref(false);
const passwordInputEl   = ref(null);
const sharePassword     = ref(null);

// ── Computed helpers ──────────────────────────────────────────────────────────
const noteFolder = computed(() => {
  const t = note.value?.title || "";
  const idx = t.lastIndexOf("/");
  return idx > -1 ? t.slice(0, idx) : "";
});

const noteBasename = computed(() => {
  const t = note.value?.title || "";
  const idx = t.lastIndexOf("/");
  return idx > -1 ? t.slice(idx + 1) : t;
});

const folderParts = computed(() => noteFolder.value.split("/").filter(Boolean));

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatExpiry(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function load(password = null) {
  try {
    // Validate token first to get permission level
    const shareData = await validateShare(props.token, password);

    // Password required — show gate
    if (shareData.requires_password) {
      requiresPassword.value = true;
      noteLoaded.value = false;
      loadingIndicator.value.setLoaded();
      await nextTick();
      passwordInputEl.value?.focus();
      return;
    }

    share.value = shareData;

    // Fetch note content (also sends password for server-side check)
    const noteData = await getSharedNote(props.token, password);
    note.value = noteData;

    requiresPassword.value = false;
    noteLoaded.value = true;
    loadingIndicator.value.setLoaded();
  } catch (err) {
    if (err.response?.status === 404) {
      loadingIndicator.value.setFailed("Share link not found or expired", mdiNoteOffOutline);
    } else {
      loadingIndicator.value.setFailed();
    }
  }
}

// ── Password gate ─────────────────────────────────────────────────────────────
async function submitPassword() {
  const pw = enteredPassword.value.trim();
  if (!pw) return;

  passwordChecking.value = true;
  passwordError.value    = "";

  try {
    const result = await validateShare(props.token, pw);
    if (result.requires_password || result === null) {
      passwordError.value = "Incorrect password. Please try again.";
      return;
    }
    // Store the password for future operations
    sharePassword.value = pw;
    // Load full note with the password
    await load(pw);
  } catch (err) {
    if (err.response?.status === 404) {
      passwordError.value = "Incorrect password. Please try again.";
    } else {
      passwordError.value = "Something went wrong. Please try again.";
    }
  } finally {
    passwordChecking.value = false;
  }
}

// ── Edit mode ─────────────────────────────────────────────────────────────────
function enterEdit() {
  editMode.value = true;
  unsavedChanges.value = false;
}

function exitEdit() {
  editMode.value = false;
  unsavedChanges.value = false;
}

function onContentChange() {
  unsavedChanges.value = true;
}

function onEditorKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    saveHandler();
  }
  if (event.key === "Escape") {
    exitEdit();
  }
}

async function saveHandler() {
  if (!toastEditor.value) return;
  const newContent = toastEditor.value.getMarkdown();
  try {
    // Pass the stored password if this is a password-protected share
    const updated = await updateSharedNote(props.token, newContent, sharePassword.value);
    note.value = updated;
    unsavedChanges.value = false;
    editMode.value = false;
    toast.add(getToastOptions("Note saved successfully ✓", "Success", "success"));
  } catch (err) {
    if (err.response?.status === 403) {
      toast.add(getToastOptions("This share link is read-only.", "Error", "error"));
    } else if (err.response?.status === 401) {
      toast.add(getToastOptions("Invalid password. Please refresh and try again.", "Error", "error"));
    } else {
      toast.add(getToastOptions("Failed to save note.", "Error", "error"));
    }
  }
}

onMounted(() => load(null));
</script>
