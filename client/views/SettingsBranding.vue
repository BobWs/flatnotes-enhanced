<template>
  <div class="space-y-6">
    <div>
      <h3 class="text-lg font-medium text-theme-text mb-1">Branding</h3>
      <p class="text-sm text-theme-text-muted mb-4">
        Customise the name, accent color, logo, and favicon shown across the app — including the login page.
      </p>

      <div class="space-y-4 p-4 rounded-lg border border-theme-border bg-theme-background">

        <!-- Name -->
        <div>
          <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
            Name
          </label>
          <input
            v-model="name"
            :disabled="nameFromEnv"
            placeholder="flatnotes"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg px-3 py-2.5
                   outline-none focus:border-theme-brand focus:ring-1 focus:ring-theme-brand/20
                   text-theme-text min-w-0 transition-all disabled:opacity-50"
          />
          <p v-if="nameFromEnv" class="text-xs text-theme-text-very-muted mt-1">
            Set by the FLATNOTES_BRAND_NAME environment variable — change it there to update this.
          </p>
        </div>

        <!-- Accent color -->
        <div>
          <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
            Accent color
          </label>
          <div class="flex flex-wrap items-center gap-2">
            <input
              type="color"
              v-model="accent"
              :disabled="accentFromEnv"
              class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent shrink-0 disabled:opacity-40"
            />
            <input
              v-model="accent"
              :disabled="accentFromEnv"
              class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border
                     rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text
                     uppercase disabled:opacity-40"
            />
            <button
              v-if="!accentFromEnv"
              @click="accent = DEFAULT_ACCENT"
              class="px-2 py-1 rounded text-xs border border-theme-border bg-theme-background-elevated
                     hover:bg-theme-border transition-colors touch-manipulation"
            >Use default</button>
          </div>
          <p v-if="accentFromEnv" class="text-xs text-theme-text-very-muted mt-1">
            Set by the FLATNOTES_BRAND_ACCENT environment variable — change it there to update this.
          </p>
        </div>

        <!-- Logo + Favicon -->
        <div class="border-t border-theme-border pt-4 grid grid-cols-1 sm:grid-cols-2 gap-6">

          <!-- Logo -->
          <div>
            <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
              Logo
            </label>
            <div class="flex items-center gap-4">
              <div class="min-w-[80px] max-w-full h-24 px-3 rounded-lg bg-theme-background-elevated border border-theme-border
                          flex items-center justify-center overflow-hidden shrink-0">
                <img v-if="logoPreviewUrl" :src="logoPreviewUrl" class="max-h-20 max-w-[200px] w-auto h-auto object-contain" alt="Logo preview" />
                <svg v-else viewBox="0 0 24 24" class="w-8 h-8 fill-current text-theme-text-very-muted">
                  <path d="M8.5,13.5L11,16.5L14.5,12L19,18H5M21,19V5C21,3.89 20.1,3 19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19Z"/>
                </svg>
              </div>
              <div class="flex flex-col gap-2">
                <label class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                              border border-theme-border bg-theme-background-elevated
                              hover:bg-theme-border hover:border-theme-brand transition-all
                              cursor-pointer text-theme-text touch-manipulation w-fit">
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                    <path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z"/>
                  </svg>
                  {{ hasStoredLogo || pickedLogo ? "Replace logo" : "Upload logo" }}
                  <input
                    type="file"
                    accept=".svg,.png,.jpg,.jpeg,.webp,.gif,.ico"
                    class="hidden"
                    @change="pickLogo"
                  />
                </label>
                <button
                  v-if="pickedLogo"
                  @click="discardPickedLogo"
                  class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                         border border-theme-border bg-theme-background-elevated hover:bg-theme-border
                         transition-all text-theme-text-muted touch-manipulation w-fit"
                >Discard chosen file</button>
                <button
                  v-else-if="hasStoredLogo && !removeLogoRequested"
                  @click="removeLogo"
                  class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                         border border-theme-border bg-theme-background-elevated
                         hover:bg-red-50 hover:border-red-300 hover:text-red-600
                         dark:hover:bg-red-950/30 dark:hover:border-red-800 dark:hover:text-red-400
                         transition-all text-theme-text-muted touch-manipulation w-fit"
                >Remove logo</button>
                <p v-else-if="removeLogoRequested" class="text-xs text-theme-text-very-muted">
                  Logo will be removed on save.
                </p>
                <p class="text-xs text-theme-text-very-muted">SVG, PNG, JPG, WebP, GIF, or ICO.</p>
              </div>
            </div>
          </div>

          <!-- Favicon -->
          <div>
            <label class="block text-xs font-medium text-theme-text-muted uppercase tracking-wide mb-1.5">
              Favicon
            </label>
            <div class="flex items-center gap-4">
              <div class="min-w-[80px] w-24 h-24 px-3 rounded-lg bg-theme-background-elevated border border-theme-border
                          flex items-center justify-center overflow-hidden shrink-0">
                <img v-if="iconPreviewUrl" :src="iconPreviewUrl" class="max-h-16 max-w-16 w-auto h-auto object-contain" alt="Favicon preview" />
                <svg v-else viewBox="0 0 24 24" class="w-8 h-8 fill-current text-theme-text-very-muted">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,7A5,5 0 0,0 7,12A5,5 0 0,0 12,17A5,5 0 0,0 17,12A5,5 0 0,0 12,7Z"/>
                </svg>
              </div>
              <div class="flex flex-col gap-2">
                <label class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                              border border-theme-border bg-theme-background-elevated
                              hover:bg-theme-border hover:border-theme-brand transition-all
                              cursor-pointer text-theme-text touch-manipulation w-fit">
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                    <path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z"/>
                  </svg>
                  {{ hasStoredIcon || pickedIcon ? "Replace favicon" : "Upload favicon" }}
                  <input
                    type="file"
                    accept=".svg,.png,.jpg,.jpeg,.webp,.gif,.ico"
                    class="hidden"
                    @change="pickIcon"
                  />
                </label>
                <button
                  v-if="pickedIcon"
                  @click="discardPickedIcon"
                  class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                         border border-theme-border bg-theme-background-elevated hover:bg-theme-border
                         transition-all text-theme-text-muted touch-manipulation w-fit"
                >Discard chosen file</button>
                <button
                  v-else-if="hasStoredIcon && !removeIconRequested"
                  @click="removeIcon"
                  class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                         border border-theme-border bg-theme-background-elevated
                         hover:bg-red-50 hover:border-red-300 hover:text-red-600
                         dark:hover:bg-red-950/30 dark:hover:border-red-800 dark:hover:text-red-400
                         transition-all text-theme-text-muted touch-manipulation w-fit"
                >Remove favicon</button>
                <p v-else-if="removeIconRequested" class="text-xs text-theme-text-very-muted">
                  Favicon will be removed on save.
                </p>
                <p class="text-xs text-theme-text-very-muted">SVG, PNG, JPG, WebP, GIF, or ICO.</p>
              </div>
            </div>
          </div>

        </div>
      </div>

      <div class="mt-3 flex items-center justify-between gap-3">
        <button
          @click="reset"
          :disabled="saving || !hasBranding"
          class="px-3 py-1.5 rounded text-sm border border-red-300 text-red-600 hover:bg-red-50
                 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950/30
                 transition-colors disabled:opacity-40 touch-manipulation"
        >Reset to defaults</button>
        <div class="flex items-center gap-3">
          <span v-if="saveMsg" class="text-sm" :class="saveOk ? 'text-green-500' : 'text-red-500'">{{ saveMsg }}</span>
          <button
            @click="save"
            :disabled="saving || !dirty"
            class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
          >{{ saving ? "Saving…" : "Save Branding" }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { getBranding, saveBranding } from "../api.js";
import { useGlobalStore } from "../globalStore.js";
import { applyBranding, applyBrandFavicon } from "../helpers.js";

// Matches style.css's own default --theme-brand (248 166 107), so "Use
// default" and the reset flow both land on the same built-in orange.
const DEFAULT_ACCENT = "#F8A66B";

// Starlette normalizes an empty-string form field to the endpoint's default
// before the backend ever sees it — an empty string can't reach the server
// as "please clear this". Sending this instead is how "" gets through, kept
// in sync with the same constant in user_settings.py.
const BRAND_CLEAR = "__flatnotes_brand_clear__";

const globalStore = useGlobalStore();

const name = ref("");
const accent = ref(DEFAULT_ACCENT);
const nameFromEnv = ref(false);
const accentFromEnv = ref(false);

const hasStoredLogo = ref(false);
const storedLogoVersion = ref(globalStore.brandVersion);
const pickedLogo = ref(null);
const pickedLogoUrl = ref(null);
const removeLogoRequested = ref(false);

const hasStoredIcon = ref(false);
const storedIconVersion = ref(globalStore.brandVersion);
const pickedIcon = ref(null);
const pickedIconUrl = ref(null);
const removeIconRequested = ref(false);

const saving = ref(false);
const saveMsg = ref("");
const saveOk = ref(true);

// Captured on load and after every successful save — what `dirty` compares against.
let baseline = { name: "", accent: DEFAULT_ACCENT };

const logoPreviewUrl = computed(() => {
  if (pickedLogoUrl.value) return pickedLogoUrl.value;
  if (hasStoredLogo.value && !removeLogoRequested.value) {
    return `api/brand/logo?v=${storedLogoVersion.value}`;
  }
  return null;
});

const iconPreviewUrl = computed(() => {
  if (pickedIconUrl.value) return pickedIconUrl.value;
  if (hasStoredIcon.value && !removeIconRequested.value) {
    return `api/brand/favicon?v=${storedIconVersion.value}`;
  }
  return null;
});

const hasBranding = computed(() => {
  return Boolean(
    name.value ||
    (accent.value && accent.value !== DEFAULT_ACCENT) ||
    hasStoredLogo.value ||
    hasStoredIcon.value
  );
});

const dirty = computed(() => {
  return (
    name.value !== baseline.name ||
    accent.value !== baseline.accent ||
    Boolean(pickedLogo.value) ||
    removeLogoRequested.value ||
    Boolean(pickedIcon.value) ||
    removeIconRequested.value
  );
});

async function load() {
  try {
    const data = await getBranding();
    name.value = data.brandName || "";
    accent.value = data.brandAccent || DEFAULT_ACCENT;
    nameFromEnv.value = Boolean(data.brandNameFromEnv);
    accentFromEnv.value = Boolean(data.brandAccentFromEnv);
    hasStoredLogo.value = Boolean(data.brandLogoFilename);
    hasStoredIcon.value = Boolean(data.brandIconFilename);
    baseline = { name: name.value, accent: accent.value };
  } catch {
    // Non-fatal — the form just falls back to the defaults set above.
  }
}

function pickLogo(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  if (pickedLogoUrl.value) URL.revokeObjectURL(pickedLogoUrl.value);
  pickedLogo.value = file;
  // Local object URL — the real /api/brand/logo URL would 404 until Save
  // actually persists the file, so the preview must not depend on it yet.
  pickedLogoUrl.value = URL.createObjectURL(file);
  removeLogoRequested.value = false;
  e.target.value = "";
}

function discardPickedLogo() {
  if (pickedLogoUrl.value) URL.revokeObjectURL(pickedLogoUrl.value);
  pickedLogo.value = null;
  pickedLogoUrl.value = null;
}

function removeLogo() {
  removeLogoRequested.value = true;
}

function pickIcon(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  if (pickedIconUrl.value) URL.revokeObjectURL(pickedIconUrl.value);
  pickedIcon.value = file;
  pickedIconUrl.value = URL.createObjectURL(file);
  removeIconRequested.value = false;
  e.target.value = "";
}

function discardPickedIcon() {
  if (pickedIconUrl.value) URL.revokeObjectURL(pickedIconUrl.value);
  pickedIcon.value = null;
  pickedIconUrl.value = null;
}

function removeIcon() {
  removeIconRequested.value = true;
}

function applyFresh(fresh) {
  globalStore.brandName = fresh.brandName || "";
  globalStore.brandAccent = fresh.brandAccent || "";
  globalStore.brandLogoFilename = fresh.brandLogoFilename || "";
  globalStore.brandIconFilename = fresh.brandIconFilename || "";
  globalStore.brandVersion = Date.now();
  applyBranding(globalStore.brandAccent);
  applyBrandFavicon(globalStore.brandIconFilename, globalStore.brandAccent, globalStore.brandVersion);
  if (globalStore.config && Object.keys(globalStore.config).length) {
    globalStore.config = {
      ...globalStore.config,
      brandName: fresh.brandName,
      brandAccent: fresh.brandAccent,
      brandLogoFilename: fresh.brandLogoFilename,
      brandIconFilename: fresh.brandIconFilename,
      brandNameFromEnv: fresh.brandNameFromEnv,
      brandAccentFromEnv: fresh.brandAccentFromEnv,
    };
  }

  name.value = fresh.brandName || "";
  accent.value = fresh.brandAccent || DEFAULT_ACCENT;
  nameFromEnv.value = Boolean(fresh.brandNameFromEnv);
  accentFromEnv.value = Boolean(fresh.brandAccentFromEnv);
  hasStoredLogo.value = Boolean(fresh.brandLogoFilename);
  hasStoredIcon.value = Boolean(fresh.brandIconFilename);
  storedLogoVersion.value = globalStore.brandVersion;
  storedIconVersion.value = globalStore.brandVersion;
  baseline = { name: name.value, accent: accent.value };
  discardPickedLogo();
  discardPickedIcon();
  removeLogoRequested.value = false;
  removeIconRequested.value = false;
}

async function save() {
  saving.value = true;
  saveMsg.value = "";
  try {
    const form = new FormData();
    if (!nameFromEnv.value && name.value !== baseline.name) {
      form.append("name", name.value === "" ? BRAND_CLEAR : name.value);
    }
    if (!accentFromEnv.value && accent.value !== baseline.accent) {
      form.append("accent", accent.value === "" ? BRAND_CLEAR : accent.value);
    }
    if (pickedLogo.value) form.append("logo", pickedLogo.value);
    if (removeLogoRequested.value) form.append("remove_logo", "true");
    if (pickedIcon.value) form.append("icon", pickedIcon.value);
    if (removeIconRequested.value) form.append("remove_icon", "true");

    const fresh = await saveBranding(form);
    applyFresh(fresh);
    saveOk.value = true;
    saveMsg.value = "Saved ✓";
  } catch {
    saveOk.value = false;
    saveMsg.value = "Save failed";
  } finally {
    saving.value = false;
    setTimeout(() => { saveMsg.value = ""; }, 3000);
  }
}

async function reset() {
  saving.value = true;
  saveMsg.value = "";
  try {
    const form = new FormData();
    if (!nameFromEnv.value) form.append("name", BRAND_CLEAR);
    if (!accentFromEnv.value) form.append("accent", BRAND_CLEAR);
    form.append("remove_logo", "true");
    form.append("remove_icon", "true");

    const fresh = await saveBranding(form);
    applyFresh(fresh);
    saveOk.value = true;
    saveMsg.value = "Reset ✓";
  } catch {
    saveOk.value = false;
    saveMsg.value = "Reset failed";
  } finally {
    saving.value = false;
    setTimeout(() => { saveMsg.value = ""; }, 3000);
  }
}

onMounted(load);

onBeforeUnmount(() => {
  if (pickedLogoUrl.value) URL.revokeObjectURL(pickedLogoUrl.value);
  if (pickedIconUrl.value) URL.revokeObjectURL(pickedIconUrl.value);
});
</script>
