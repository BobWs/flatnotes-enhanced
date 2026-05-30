<template>
  <div>
    <h3 class="text-lg font-medium text-theme-text mb-1">Account Preferences</h3>
    <p class="text-sm text-theme-text-muted mb-5">Customise your personal settings.</p>

    <!-- ── Row 1: Display name + Avatar ── -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
      <!-- Display name -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-sm font-medium text-theme-text mb-1">Display name</label>
        <input
          v-model="prefs.displayName"
          placeholder="Your name"
          class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                 outline-none focus:border-theme-brand text-theme-text"
        />
        <p class="text-xs text-theme-text-very-muted mt-1.5">Shown in the app header.</p>
      </div>

      <!-- Avatar -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-sm font-medium text-theme-text mb-2">Avatar</label>
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-theme-background-elevated border border-theme-border
                      flex items-center justify-center overflow-hidden shrink-0">
            <img v-if="avatarUrl" :src="avatarUrl" class="w-full h-full object-cover" alt="Avatar"/>
            <svg v-else viewBox="0 0 24 24" class="w-6 h-6 fill-current text-theme-text-very-muted">
              <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
            </svg>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="flex items-center gap-2 px-3 py-1.5 rounded text-xs border border-theme-border
                          bg-theme-background-elevated hover:bg-theme-border transition-colors cursor-pointer text-theme-text touch-manipulation">
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0"><path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z"/></svg>
              Upload image
              <input type="file" accept="image/*" class="hidden" @change="uploadAvatar"/>
            </label>
            <button
              v-if="prefs.avatarFilename"
              @click="removeAvatar"
              class="text-xs text-theme-text-muted hover:text-red-500 transition-colors text-left touch-manipulation"
            >Remove avatar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Row 2: Default sort + Default view ── -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
      <!-- Default sort -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-sm font-medium text-theme-text mb-1">Default note sort</label>
        <select
          v-model="prefs.notesDefaultSort"
          class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                 outline-none focus:border-theme-brand text-theme-text"
        >
          <option value="">App default</option>
          <option value="lastModified">Last modified</option>
          <option value="title">Title A–Z</option>
          <option value="score">Relevance</option>
        </select>
        <p class="text-xs text-theme-text-very-muted mt-1.5">Default sort order for note lists.</p>
      </div>

      <!-- Default view -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-sm font-medium text-theme-text mb-1">Default note view</label>
        <select
          v-model="prefs.notesDefaultView"
          class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                 outline-none focus:border-theme-brand text-theme-text"
        >
          <option value="normal">Normal (999px)</option>
          <option value="wide">Wide (1400px)</option>
          <option value="fullscreen">Full Screen</option>
        </select>
        <p class="text-xs text-theme-text-very-muted mt-1.5">
          Wide gives more room on large desktops without stretching to full screen. Full Screen uses all available width.
        </p>
      </div>
    </div>

    <!-- ── Row 3: Toggles ── -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
      <!-- Note preview on hover -->
      <div class="flex items-center justify-between p-4 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-3">
          <p class="text-sm font-medium text-theme-text">Note preview on hover</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
            Show preview popup when clicking the
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current inline-block align-text-bottom mx-0.5">
              <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"/>
            </svg>
            eye button.
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer shrink-0">
          <input type="checkbox" v-model="previewEnabled" class="sr-only peer" @change="savePreviewSetting" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <!-- Show button labels -->
      <div class="flex items-center justify-between p-4 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-3">
          <p class="text-sm font-medium text-theme-text">Show button labels</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
            When off, navbar buttons show icons only.
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer shrink-0">
          <input type="checkbox" v-model="prefs.showButtonLabels" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>
    </div>

    <!-- ── Row 4: Custom Home Note (full width) ── -->
    <div class="mb-5">
      <div class="rounded-lg border border-theme-border bg-theme-background overflow-hidden">
        <div class="flex items-start justify-between px-4 py-3" :class="prefs.homeNoteEnabled ? 'border-b border-theme-border' : ''">
          <div class="min-w-0 pr-4">
            <p class="text-sm font-medium text-theme-text">Custom home note</p>
            <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
              When enabled, the Home button opens a specific note instead of the quick-access page.
              The keyboard shortcut <kbd class="px-1 py-0.5 rounded text-xs bg-theme-background-elevated border border-theme-border">Ctrl+Alt+H</kbd> also respects this setting.
            </p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer shrink-0 mt-0.5">
            <input type="checkbox" v-model="prefs.homeNoteEnabled" class="sr-only peer" />
            <div class="w-11 h-6 bg-theme-border rounded-full peer
                        peer-checked:bg-theme-brand transition-colors
                        after:content-[''] after:absolute after:top-0.5 after:left-0.5
                        after:bg-white after:rounded-full after:h-5 after:w-5
                        after:transition-transform peer-checked:after:translate-x-5"></div>
          </label>
        </div>

        <div v-if="prefs.homeNoteEnabled" class="px-4 py-3 bg-theme-background-elevated/40">
          <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">Note title</label>
          <div class="flex items-center gap-2">
            <input
              v-model="prefs.homeNote"
              placeholder="e.g. Dashboard or Work/Weekly"
              class="flex-1 text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                     outline-none focus:border-theme-brand text-theme-text min-w-0"
            />
            <a
              v-if="prefs.homeNote && prefs.homeNote.trim()"
              :href="'/note/' + prefs.homeNote.split('/').map(encodeURIComponent).join('/')"
              target="_blank"
              rel="noopener"
              title="Open this note to verify it exists"
              class="shrink-0 px-3 py-2 rounded text-sm border border-theme-border
                     bg-theme-background-elevated hover:bg-theme-border transition-colors
                     text-theme-text-muted hover:text-theme-text inline-flex items-center gap-1.5 touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/>
              </svg>
              Open
            </a>
          </div>
          <p class="text-xs text-theme-text-very-muted mt-1.5">
            Enter the exact note title as it appears in the app. For notes in folders use the full path,
            e.g. <code class="bg-theme-background-elevated px-1 py-0.5 rounded">Work/Weekly</code>.
          </p>
        </div>
      </div>
    </div>

    <!-- ── Save ── -->
    <div class="flex items-center gap-3">
      <button
        @click="savePrefs"
        :disabled="prefsSaving"
        class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
               text-white transition-colors disabled:opacity-50 touch-manipulation"
      >{{ prefsSaving ? 'Saving…' : 'Save preferences' }}</button>
      <span v-if="prefsSaveMsg" class="text-sm" :class="prefsSaveOk ? 'text-green-500' : 'text-red-500'">
        {{ prefsSaveMsg }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { getPrefs, savePrefs as apiSavePrefs, createAttachment } from "../api.js";
import { useGlobalStore } from "../globalStore.js";

const globalStore = useGlobalStore();

// ── State ─────────────────────────────────────────────────────────────────────
const prefs = ref({
  displayName: "",
  avatarFilename: null,
  notesDefaultSort: "",
  notesDefaultView: "normal",
  showButtonLabels: true,
  homeNoteEnabled: false,
  homeNote: "",
});
const prefsSaving = ref(false);
const prefsSaveMsg = ref("");
const prefsSaveOk = ref(true);
const previewEnabled = ref(true);

// ── Computed ──────────────────────────────────────────────────────────────────
const avatarUrl = computed(() => {
  if (!prefs.value.avatarFilename) return null;
  return `attachments/${prefs.value.avatarFilename}`;
});

// ── Watchers — keep globalStore in sync for live preview ─────────────────────
watch(() => prefs.value.showButtonLabels, (val) => {
  globalStore.showButtonLabels = val;
}, { immediate: true });

watch(() => prefs.value.notesDefaultView, (val) => {
  globalStore.noteViewMode = (val === 'fullscreen' || val === 'wide') ? val : 'normal';
}, { immediate: true });

watch(() => prefs.value.homeNoteEnabled, (val) => {
  globalStore.homeNoteEnabled = val;
}, { immediate: true });

watch(() => prefs.value.homeNote, (val) => {
  globalStore.homeNote = val || '';
}, { immediate: true });

watch(() => prefs.value.notesDefaultSort, (val) => {
  globalStore.notesDefaultSort = val || '';
}, { immediate: true });

// ── Avatar helpers ────────────────────────────────────────────────────────────
async function uploadAvatar(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const result = await createAttachment(file);
    prefs.value.avatarFilename = result.filename;
  } catch {
    alert("Upload failed");
  }
}

function removeAvatar() {
  prefs.value.avatarFilename = null;
}

// ── Preview toggle ────────────────────────────────────────────────────────────
function loadPreviewSetting() {
  const stored = localStorage.getItem("fn_preview_enabled");
  previewEnabled.value = stored === null ? true : stored === "true";
}

function savePreviewSetting() {
  localStorage.setItem("fn_preview_enabled", String(previewEnabled.value));
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function savePrefs() {
  prefsSaving.value = true;
  prefsSaveMsg.value = "";
  try {
    const p = prefs.value;
    const toNull = (v) => (v === "" || v === undefined) ? null : v;
    await apiSavePrefs({
      display_name:        toNull(p.displayName),
      avatar_filename:     toNull(p.avatarFilename),
      notes_default_sort:  p.notesDefaultSort ?? "",
      notes_default_view:  (p.notesDefaultView === 'fullscreen' || p.notesDefaultView === 'wide') ? p.notesDefaultView : 'normal',
      show_button_labels:  p.showButtonLabels,
      home_note_enabled:   p.homeNoteEnabled,
      home_note:           p.homeNote ? p.homeNote.trim() : null,
    });
    prefsSaveOk.value = true;
    prefsSaveMsg.value = "Saved ✓";
  } catch {
    prefsSaveOk.value = false;
    prefsSaveMsg.value = "Save failed";
  } finally {
    prefsSaving.value = false;
    setTimeout(() => { prefsSaveMsg.value = ""; }, 3000);
  }
}

// ── Load on mount ─────────────────────────────────────────────────────────────
onMounted(async () => {
  loadPreviewSetting();
  try {
    const p = await getPrefs();
    prefs.value = {
      displayName:       p.display_name ?? "",
      avatarFilename:    p.avatar_filename ?? null,
      notesDefaultSort:  p.notes_default_sort ?? "",
      notesDefaultView:  (p.notes_default_view === 'fullscreen' || p.notes_default_view === 'wide') ? p.notes_default_view : 'normal',
      showButtonLabels:  p.show_button_labels !== false,
      homeNoteEnabled:   p.home_note_enabled === true,
      homeNote:          p.home_note || "",
    };
  } catch {
    // defaults already set
  }
});
</script>
