<template>
  <div>
    <h3 class="text-lg font-medium text-theme-text mb-1">Account Preferences</h3>
    <p class="text-sm text-theme-text-muted mb-5">Customise your personal settings.</p>

    <!-- ── Row 1: Display name + Avatar (combined) & Custom home note ── -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Combined: Display name + Avatar - Redesigned -->
      <div class="p-5 rounded-lg border border-theme-border bg-theme-background">
        <!-- Avatar section with buttons -->
        <div class="flex items-start gap-5">
          <!-- Avatar -->
          <div class="shrink-0">
            <div class="w-20 h-20 rounded-full bg-theme-background-elevated border-2 border-theme-border
                        flex items-center justify-center overflow-hidden">
              <img v-if="avatarUrl" :src="avatarUrl" class="w-full h-full object-cover" alt="Avatar"/>
              <svg v-else viewBox="0 0 24 24" class="w-10 h-10 fill-current text-theme-text-very-muted">
                <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
              </svg>
            </div>
          </div>

          <!-- Avatar action buttons -->
          <div class="flex flex-col gap-2 pt-1">
            <!-- Upload button with icon -->
            <label class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                          border border-theme-border bg-theme-background-elevated 
                          hover:bg-theme-border hover:border-theme-brand transition-all 
                          cursor-pointer text-theme-text touch-manipulation">
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                <path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z"/>
              </svg>
              Upload image
              <input type="file" accept="image/*" class="hidden" @change="uploadAvatar"/>
            </label>

            <!-- Remove button with icon (only shown when avatar exists) -->
            <button
              v-if="prefs.avatarFilename"
              @click="removeAvatar"
              class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                     border border-theme-border bg-theme-background-elevated
                     hover:bg-red-50 hover:border-red-300 hover:text-red-600 
                     dark:hover:bg-red-950/30 dark:hover:border-red-800 dark:hover:text-red-400
                     transition-all text-theme-text-muted touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
              Remove avatar
            </button>

            <!-- Empty state hint when no avatar -->
            <p v-else class="text-xs text-theme-text-very-muted leading-relaxed max-w-[180px]">
              Upload a photo to personalize your profile
            </p>
          </div>
        </div>

        <!-- Display name - positioned below avatar -->
        <div class="mt-4 pt-4 border-t border-theme-border/50">
          <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
            Display name
          </label>
          <input
            v-model="prefs.displayName"
            placeholder="Your name"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                   outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                   text-theme-text min-w-0 transition-all"
          />
          <p class="text-xs text-theme-text-very-muted mt-1.5 flex items-center gap-1.5">
            <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current shrink-0">
              <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M11,7H13V13H11V7M11,15H13V17H11V15Z"/>
            </svg>
            Shown in the app header
          </p>
        </div>
      </div>

      <!-- Custom Home Note -->
      <div class="rounded-lg border border-theme-border bg-theme-background overflow-hidden">
        <div class="flex items-start justify-between px-5 py-4" :class="prefs.homeNoteEnabled ? 'border-b border-theme-border' : ''">
          <div class="min-w-0 pr-4">
            <p class="text-sm font-medium text-theme-text">Custom home note</p>
            <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
              When enabled, the Home button opens a specific note instead of the quick-access page.
              The keyboard shortcut <kbd class="px-1.5 py-0.5 rounded text-xs bg-theme-background-elevated border border-theme-border font-mono">Ctrl+Alt+H</kbd> also respects this setting.
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

        <div v-if="prefs.homeNoteEnabled" class="px-5 py-4 bg-theme-background-elevated/40">
          <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">Note title</label>
          <div class="flex items-center gap-2">
            <input
              v-model="prefs.homeNote"
              placeholder="e.g. Dashboard or Work/Weekly"
              class="flex-1 text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                     outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                     text-theme-text min-w-0 transition-all"
            />
            <a
              v-if="prefs.homeNote && prefs.homeNote.trim()"
              :href="'/note/' + prefs.homeNote.split('/').map(encodeURIComponent).join('/')"
              target="_blank"
              rel="noopener"
              title="Open this note to verify it exists"
              class="shrink-0 px-3.5 py-2.5 rounded-lg text-sm border border-theme-border
                     bg-theme-background-elevated hover:bg-theme-border hover:border-theme-brand
                     transition-all text-theme-text-muted hover:text-theme-text 
                     inline-flex items-center gap-1.5 touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/>
              </svg>
              Open
            </a>
          </div>
          <p class="text-xs text-theme-text-very-muted mt-1.5">
            Enter the exact note title as it appears in the app. For notes in folders use the full path,
            e.g. <code class="bg-theme-background-elevated px-1.5 py-0.5 rounded text-xs font-mono">Work/Weekly</code>.
          </p>
        </div>
      </div>
    </div>

    <!-- ── Row 2: Default view & Default sort ── -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Default view -->
      <div class="p-5 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
          Default note view
        </label>
        <select
          v-model="prefs.notesDefaultView"
          class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                 outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                 text-theme-text transition-all appearance-none"
        >
          <option value="normal">Normal (999px)</option>
          <option value="wide">Wide (1400px)</option>
          <option value="fullscreen">Full Screen</option>
        </select>
        <p class="text-xs text-theme-text-very-muted mt-1.5 flex items-start gap-1.5">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current shrink-0 mt-0.5">
            <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M11,7H13V13H11V7M11,15H13V17H11V15Z"/>
          </svg>
          <span>Wide gives more room on large desktops without stretching to full screen. Full Screen uses all available width.</span>
        </p>
      </div>

      <!-- Default sort -->
      <div class="p-5 rounded-lg border border-theme-border bg-theme-background">
        <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
          Default note sort
        </label>
        <select
          v-model="prefs.notesDefaultSort"
          class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                 outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                 text-theme-text transition-all appearance-none"
        >
          <option value="">App default</option>
          <option value="lastModified">Last modified</option>
          <option value="title">Title A–Z</option>
          <option value="titleDesc">Title Z–A</option>
          <option value="score">Relevance</option>
        </select>
        <p class="text-xs text-theme-text-very-muted mt-1.5 flex items-center gap-1.5">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current shrink-0">
            <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M11,7H13V13H11V7M11,15H13V17H11V15Z"/>
          </svg>
          Default sort order for note lists
        </p>
      </div>
    </div>

    <!-- ── Row 3: Show button labels & Note preview on hover ── -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Show button labels -->
      <div class="flex items-center justify-between p-5 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-4">
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

      <!-- Note preview on hover -->
      <div class="flex items-center justify-between p-5 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-4">
          <p class="text-sm font-medium text-theme-text">Note preview on hover</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed flex items-center gap-1">
            Show preview popup when clicking the
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current inline-block align-text-bottom">
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
    </div>

    <!-- ── Row 4: Saved searches sidebar visibility & Offline caching (PWA) ── -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Saved searches sidebar visibility -->
      <div class="flex items-center justify-between p-5 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-4">
          <p class="text-sm font-medium text-theme-text">Show saved searches in sidebar</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
            Display a "Saved Searches" section in the folder sidebar for one-click access to saved queries.
            Manage saved searches in
            <button type="button" @click="$emit('switchTab', 'searches')" class="text-theme-brand hover:underline">Settings → Searches</button>.
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer shrink-0">
          <input type="checkbox" v-model="prefs.savedSearchesEnabled" class="sr-only peer" @change="onSavedSearchesToggle" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <!-- Offline caching (PWA) -->
      <div class="flex items-center justify-between p-5 rounded-lg border border-theme-border bg-theme-background">
        <div class="min-w-0 pr-4">
          <p class="text-sm font-medium text-theme-text">Enable offline caching</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
            Cache notes and assets so you can read them when the server is unreachable.
            Also enables installing Flatnotes as a standalone app.
            <span class="block mt-1 text-theme-text-very-muted">Notes are stored as markdown files and are not affected by this setting.</span>
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer shrink-0">
          <input type="checkbox" v-model="prefs.offlineCacheEnabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>
    </div>

    <!-- ── Row 5: Date Format (full width) ── -->
    <div class="mb-5">
      <div class="rounded-lg border border-theme-border bg-theme-background overflow-hidden">
        <div class="px-5 py-4 border-b border-theme-border">
          <p class="text-sm font-medium text-theme-text">Date Format</p>
          <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed">
            Choose how dates appear throughout the app — in note lists, search results, archive, and trash.
          </p>
        </div>

        <div class="px-5 py-4 space-y-4">
          <!-- Locale + Style row -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- Locale -->
            <div>
              <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">Language / Region</label>
              <select
                v-model="prefs.dateLocale"
                class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                       outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                       text-theme-text transition-all appearance-none"
              >
                <option value="system">System default</option>
                <option value="nl">Dutch (nl)</option>
                <option value="en-GB">English — United Kingdom (en-GB)</option>
                <option value="en-US">English — United States (en-US)</option>
                <option value="de">German (de)</option>
                <option value="fr">French (fr)</option>
                <option value="es">Spanish (es)</option>
                <option value="it">Italian (it)</option>
                <option value="pt">Portuguese (pt)</option>
                <option value="sv">Swedish (sv)</option>
                <option value="nb">Norwegian (nb)</option>
                <option value="da">Danish (da)</option>
                <option value="fi">Finnish (fi)</option>
                <option value="pl">Polish (pl)</option>
                <option value="ja">Japanese (ja)</option>
                <option value="zh-CN">Chinese Simplified (zh-CN)</option>
              </select>
            </div>

            <!-- Style -->
            <div>
              <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">Date Style</label>
              <select
                v-model="prefs.dateStyle"
                class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                       outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                       text-theme-text transition-all appearance-none"
              >
                <option value="short">Short (e.g. 24/06/2026)</option>
                <option value="medium">Medium (e.g. 24 Jun 2026) — Default</option>
                <option value="long">Long (e.g. 24 June 2026)</option>
              </select>
            </div>
          </div>

          <!-- Live preview -->
          <div class="px-4 py-3 rounded-lg bg-theme-background-elevated border border-theme-border">
            <p class="text-xs text-theme-text-muted mb-1.5">Preview:</p>
            <div class="flex flex-wrap gap-x-6 gap-y-1">
              <span class="text-sm text-theme-text">
                <span class="text-xs text-theme-text-very-muted mr-1">Date</span>
                {{ previewDate }}
              </span>
              <span class="text-sm text-theme-text">
                <span class="text-xs text-theme-text-very-muted mr-1">Date + time</span>
                {{ previewDateTime }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Save ── -->
    <div class="flex items-center gap-3">
      <button
        @click="savePrefs"
        :disabled="prefsSaving"
        class="px-5 py-2.5 rounded-lg text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
               text-white transition-all disabled:opacity-50 touch-manipulation
               focus:outline-none focus:ring-2 focus:ring-theme-brand/30"
      >{{ prefsSaving ? 'Saving…' : 'Save preferences' }}</button>
      <span v-if="prefsSaveMsg" class="text-sm" :class="prefsSaveOk ? 'text-green-500' : 'text-red-500'">
        {{ prefsSaveMsg }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { getPrefs, savePrefs as apiSavePrefs, createAttachment, getSavedSearches, saveSavedSearches } from "../api.js";
import { useGlobalStore } from "../globalStore.js";
import { setOfflineCache, unregisterAll, init as initPwa } from "../pwaService.js";
import { clearDateFormatterCache } from "../dateFormatter.js";

const globalStore = useGlobalStore();

// Emit for switching to Searches tab from link in toggle description
const emit = defineEmits(['switchTab']);

// ── State ─────────────────────────────────────────────────────────────────────
const prefs = ref({
  displayName: "",
  avatarFilename: null,
  notesDefaultSort: "",
  notesDefaultView: "normal",
  showButtonLabels: true,
  homeNoteEnabled: false,
  homeNote: "",
  offlineCacheEnabled: false,
  savedSearchesEnabled: false,
  dateLocale: "system",
  dateStyle: "medium",
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

// Live date preview — recomputed whenever locale or style changes
const _PREVIEW_TS = new Date(2026, 5, 24, 14, 5); // 24 Jun 2026, 14:05 (fixed sample)
const _DATE_OPTS = {
  short:  { year: 'numeric', month: '2-digit', day: '2-digit' },
  medium: { year: 'numeric', month: 'short',   day: 'numeric' },
  long:   { year: 'numeric', month: 'long',    day: 'numeric' },
};

function _buildPreview(includeTime) {
  const locale = prefs.value.dateLocale;
  const style  = prefs.value.dateStyle;
  const resolved = locale === 'system' ? undefined : locale;
  const opts = {
    ...(_DATE_OPTS[style] ?? _DATE_OPTS.medium),
    ...(includeTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  };
  try {
    return new Intl.DateTimeFormat(resolved, opts).format(_PREVIEW_TS);
  } catch {
    return new Intl.DateTimeFormat(undefined, opts).format(_PREVIEW_TS);
  }
}

const previewDate     = computed(() => _buildPreview(false));
const previewDateTime = computed(() => _buildPreview(true));

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

watch(() => prefs.value.offlineCacheEnabled, async (val) => {
  globalStore.offlineCacheEnabled = val;
  if (val) {
    await initPwa();
    setOfflineCache(true);
  } else {
    setOfflineCache(false);
    await unregisterAll();
  }
}, { immediate: false });

// ── Saved searches sidebar toggle ─────────────────────────────────────────────
// Immediately persists the enabled flag to the backend and syncs the store
// so the sidebar section appears/disappears without needing a full prefs save.
async function onSavedSearchesToggle() {
  const enabled = prefs.value.savedSearchesEnabled;
  globalStore.savedSearchesEnabled = enabled;
  try {
    const current = await getSavedSearches();
    await saveSavedSearches({ ...current, enabled });
  } catch {
    // Non-fatal; the main Save button will also persist it
  }
}

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
      display_name:          toNull(p.displayName),
      avatar_filename:       toNull(p.avatarFilename),
      notes_default_sort:    p.notesDefaultSort ?? "",
      notes_default_view:    (p.notesDefaultView === 'fullscreen' || p.notesDefaultView === 'wide') ? p.notesDefaultView : 'normal',
      show_button_labels:    p.showButtonLabels,
      home_note_enabled:     p.homeNoteEnabled,
      home_note:             p.homeNote ? p.homeNote.trim() : null,
      offline_cache_enabled: p.offlineCacheEnabled,
      date_locale:           p.dateLocale,
      date_style:            p.dateStyle,
    });
    // Persist to store and clear formatter cache so new preference takes
    // effect immediately across all components without a page reload.
    globalStore.dateLocale = p.dateLocale;
    globalStore.dateStyle  = p.dateStyle;
    clearDateFormatterCache();
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
      displayName:          p.display_name ?? "",
      avatarFilename:       p.avatar_filename ?? null,
      notesDefaultSort:     p.notes_default_sort ?? "",
      notesDefaultView:     (p.notes_default_view === 'fullscreen' || p.notes_default_view === 'wide') ? p.notes_default_view : 'normal',
      showButtonLabels:     p.show_button_labels !== false,
      homeNoteEnabled:      p.home_note_enabled === true,
      homeNote:             p.home_note || "",
      offlineCacheEnabled:  p.offline_cache_enabled === true,
      savedSearchesEnabled: globalStore.savedSearchesEnabled, // already loaded by App.vue
      dateLocale:           p.date_locale || "system",
      dateStyle:            p.date_style  || "medium",
    };
  } catch {
    // defaults already set
  }
});
</script>