<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center"
      style="background: rgba(0,0,0,0.55);"
      @click.self="dismiss"
    >
      <div
        class="relative w-full max-w-sm mx-4 rounded-xl border border-theme-border bg-theme-background shadow-2xl"
        style="max-height: 92vh; overflow-y: auto;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 pt-5 pb-3 border-b border-theme-border">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-brand">
              <path d="M3,11H5V13H3V11M11,5H13V9H11V5M9,11H13V15H11V13H9V11M15,11H17V13H19V11H21V13H19V15H21V19H19V21H17V19H13V21H11V17H13V15H15V11M19,15H17V19H19V15M15,17H13V19H15V17M5,3H9V7H5V3M3,3H5V5H3V3M5,5H9V7H5V5M13,3H17V7H13V3M11,3H13V5H11V3M13,5H17V7H13V5M3,13H7V17H3V13M5,15H7V17H5V15Z"/>
            </svg>
            <h2 class="text-base font-semibold text-theme-text">Set Up Two-Factor Authentication</h2>
          </div>
          <button
            @click="dismiss"
            class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
            title="Close"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="px-5 py-4 space-y-4">

          <!-- Loading state -->
          <div v-if="loading" class="flex flex-col items-center gap-3 py-6">
            <div class="w-8 h-8 border-2 border-theme-brand border-t-transparent rounded-full animate-spin"></div>
            <p class="text-sm text-theme-text-muted">Loading QR code…</p>
          </div>

          <!-- Error state -->
          <div v-else-if="error" class="flex flex-col items-center gap-3 py-4">
            <svg viewBox="0 0 24 24" class="w-10 h-10 fill-current text-red-400">
              <path d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/>
            </svg>
            <p class="text-sm text-theme-text-muted text-center">{{ error }}</p>
            <button
              @click="load"
              class="px-3 py-1.5 rounded text-sm bg-theme-background-elevated hover:bg-theme-border transition-colors text-theme-text"
            >Try again</button>
          </div>

          <!-- Success state -->
          <template v-else-if="data">
            <!-- Instruction -->
            <p class="text-sm text-theme-text-muted">
              Scan this QR code with your authenticator app
              (<span class="font-medium text-theme-text">Authy</span>,
              <span class="font-medium text-theme-text">Google Authenticator</span>, etc.)
              to set up two-factor authentication.
            </p>

            <!-- QR Code -->
            <div
              class="flex items-center justify-center p-4 rounded-lg border border-theme-border bg-white"
              v-html="data.svg"
              style="min-height: 200px;"
            ></div>

            <!-- Manual entry -->
            <div class="rounded-lg border border-theme-border bg-theme-background-elevated p-3">
              <p class="text-xs text-theme-text-muted mb-1.5">
                Can't scan? Enter this key manually:
              </p>
              <div class="flex items-center gap-2">
                <code
                  class="flex-1 text-sm font-mono text-theme-text tracking-widest break-all select-all"
                >{{ formattedSecret }}</code>
                <button
                  @click="copySecret"
                  class="shrink-0 p-1.5 rounded hover:bg-theme-border transition-colors text-theme-text-muted hover:text-theme-text"
                  :title="copied ? 'Copied!' : 'Copy to clipboard'"
                >
                  <svg v-if="!copied" viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                    <path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current text-green-500">
                    <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Note -->
            <p class="text-xs text-theme-text-very-muted">
              After scanning, open your authenticator app and enter the 6-digit code on the login page.
              You only need to scan this once.
            </p>
          </template>
        </div>

        <!-- Footer -->
        <div class="px-5 pb-5 pt-1">
          <button
            @click="dismiss"
            class="w-full px-4 py-2 rounded-lg text-sm font-medium
                   bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors"
          >
            {{ data ? "I've scanned it — close" : "Close" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { getTotpSetup } from "../api.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["close"]);

const loading = ref(false);
const error   = ref(null);
const data    = ref(null);
const copied  = ref(false);

// Format the secret in groups of 4 for readability: ABCD EFGH IJKL …
const formattedSecret = computed(() => {
  if (!data.value?.secret) return "";
  return data.value.secret.replace(/(.{4})/g, "$1 ").trim();
});

async function load() {
  loading.value = true;
  error.value   = null;
  data.value    = null;
  try {
    data.value = await getTotpSetup();
    // Make the SVG responsive — remove fixed width/height attributes
    if (data.value.svg) {
      data.value.svg = data.value.svg
        .replace(/width="[^"]*"/, 'width="100%"')
        .replace(/height="[^"]*"/, 'height="100%"')
        .replace(/<svg /, '<svg style="display:block;max-width:240px;margin:auto;" ');
    }
  } catch {
    error.value = "Could not load QR code. Make sure TOTP is enabled on the server.";
  } finally {
    loading.value = false;
  }
}

async function copySecret() {
  if (!data.value?.secret) return;
  try {
    await navigator.clipboard.writeText(data.value.secret);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch {
    // Clipboard API not available — silent fail, key is selectable
  }
}

function dismiss() {
  emit("close");
}

// Auto-load when the modal becomes visible
watch(() => props.show, (val) => {
  if (val && !data.value && !loading.value) load();
});
</script>
