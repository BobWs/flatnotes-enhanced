<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="$emit('close')"
    >
      <div class="bg-theme-background rounded-t-2xl sm:rounded-xl border border-theme-border shadow-xl
                  w-full sm:w-[480px] sm:max-w-full">

        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-brand shrink-0">
              <path d="M18,16.08C17.24,16.08 16.56,16.38 16.04,16.85L8.91,12.7C8.96,12.47 9,12.24 9,12C9,11.76 8.96,11.53 8.91,11.3L15.96,7.19C16.5,7.69 17.21,8 18,8A3,3 0 0,0 21,5A3,3 0 0,0 18,2A3,3 0 0,0 15,5C15,5.24 15.04,5.47 15.09,5.7L8.04,9.81C7.5,9.31 6.79,9 6,9A3,3 0 0,0 3,12A3,3 0 0,0 6,15C6.79,15 7.5,14.69 8.04,14.19L15.16,18.34C15.11,18.55 15.08,18.77 15.08,19C15.08,20.61 16.39,21.91 18,21.91C19.61,21.91 20.92,20.61 20.92,19A2.92,2.92 0 0,0 18,16.08Z"/>
            </svg>
            <h3 class="text-base font-semibold text-theme-text">Share note</h3>
          </div>
          <button @click="$emit('close')"
            class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded touch-manipulation">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>

        <!-- Active share links -->
        <div class="px-4 pt-4 pb-2">
          <p class="text-xs font-bold uppercase tracking-wider text-theme-text-very-muted mb-2">
            Active share links
          </p>

          <!-- Loading -->
          <div v-if="loadingShares" class="py-4 text-center text-sm text-theme-text-very-muted">
            Loading…
          </div>

          <!-- Empty -->
          <div v-else-if="shares.length === 0"
            class="py-4 text-center text-sm text-theme-text-very-muted border border-dashed border-theme-border rounded-lg">
            No active share links yet.
          </div>

          <!-- List -->
          <div v-else class="space-y-2 max-h-56 overflow-y-auto">
            <div
              v-for="s in shares"
              :key="s.token_preview"
              class="px-3 py-2.5 rounded-lg border"
              :class="isExpired(s)
                ? 'bg-theme-background-elevated/50 border-theme-border opacity-60'
                : 'bg-theme-background-elevated border-theme-border'"
            >
              <!-- Top row: preview + badges + action buttons -->
              <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center gap-2 flex-wrap flex-1 min-w-0">
                  <code class="text-xs font-mono text-theme-text-muted">{{ s.token_preview }}…</code>
                  <!-- Expired badge -->
                  <span
                    v-if="isExpired(s)"
                    class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-500"
                  >Expired</span>
                  <template v-else>
                    <span
                      class="text-xs font-medium px-1.5 py-0.5 rounded-full"
                      :class="s.permission === 'write'
                        ? 'bg-theme-brand/15 text-theme-brand'
                        : 'bg-theme-background text-theme-text-muted border border-theme-border'"
                    >{{ s.permission === 'write' ? 'Can edit' : 'Read only' }}</span>
                    <span v-if="s.has_password" class="text-xs text-theme-text-very-muted flex items-center gap-0.5">
                      <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current"><path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/></svg>
                      Password
                    </span>
                  </template>
                </div>

                <!-- Copy button (hidden when expired) -->
                <button
                  v-if="!isExpired(s)"
                  @click="copyLink(s.token_preview)"
                  class="shrink-0 p-1.5 rounded text-theme-text-muted hover:text-theme-brand hover:bg-theme-background transition-colors touch-manipulation"
                  :title="copiedToken === s.token_preview ? 'Copied!' : 'Copy link'"
                >
                  <svg v-if="copiedToken !== s.token_preview" viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                    <path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current text-green-500">
                    <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
                  </svg>
                </button>

                <!-- Revoke button -->
                <button
                  @click="revokeHandler(s)"
                  class="shrink-0 p-1.5 rounded text-theme-text-muted hover:text-red-500 hover:bg-red-500/10 transition-colors touch-manipulation"
                  title="Revoke this link"
                >
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                    <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                  </svg>
                </button>
              </div>

              <!-- Activity + date meta row -->
              <div class="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-theme-text-very-muted">
                <span class="flex items-center gap-1">
                  <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
                    <path d="M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/>
                  </svg>
                  {{ s.access_count }} view{{ s.access_count !== 1 ? 's' : '' }}
                </span>
                <span v-if="s.last_accessed_at">
                  · last {{ formatRelativeTime(s.last_accessed_at) }}
                </span>
                <span v-if="s.expires_at">
                  · {{ isExpired(s) ? 'expired' : 'expires' }} {{ formatDate(s.expires_at) }}
                </span>
                <span v-else>· no expiry</span>
                <span v-if="s.created_at">· created {{ formatDate(s.created_at) }}</span>
              </div>
            </div>

            <!-- Revoke all button (2+ active shares) -->
            <div v-if="activeShareCount >= 2" class="pt-1">
              <template v-if="confirmRevokeAll">
                <div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-red-400/40 bg-red-500/5">
                  <p class="text-xs text-theme-text-muted flex-1">
                    Revoke all {{ activeShareCount }} links for this note?
                  </p>
                  <button
                    @click="doRevokeAll"
                    class="text-xs font-medium px-2.5 py-1 rounded text-red-500 border border-red-400/40
                           hover:bg-red-500/10 transition-colors touch-manipulation"
                  >Confirm</button>
                  <button
                    @click="confirmRevokeAll = false"
                    class="text-xs px-2.5 py-1 rounded text-theme-text-muted border border-theme-border
                           hover:bg-theme-background-elevated transition-colors touch-manipulation"
                  >Cancel</button>
                </div>
              </template>
              <button
                v-else
                @click="confirmRevokeAll = true"
                class="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium
                       text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors touch-manipulation"
              >
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
                Revoke all {{ activeShareCount }} links
              </button>
            </div>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-theme-border mx-4 my-2"></div>

        <!-- Create new link -->
        <div class="px-4 pb-4 space-y-3">
          <p class="text-xs font-bold uppercase tracking-wider text-theme-text-very-muted">
            Create new link
          </p>

          <!-- Permission toggle -->
          <div>
            <label class="block text-xs text-theme-text-muted mb-1.5">Permission</label>
            <div class="flex rounded-lg border border-theme-border overflow-hidden text-sm font-medium">
              <button
                @click="newPermission = 'read'"
                :class="[
                  'flex-1 py-2 px-3 transition-colors',
                  newPermission === 'read'
                    ? 'bg-theme-brand text-white'
                    : 'bg-theme-background-elevated text-theme-text-muted hover:bg-theme-border'
                ]"
              >Read only</button>
              <button
                @click="newPermission = 'write'"
                :class="[
                  'flex-1 py-2 px-3 transition-colors border-l border-theme-border',
                  newPermission === 'write'
                    ? 'bg-theme-brand text-white'
                    : 'bg-theme-background-elevated text-theme-text-muted hover:bg-theme-border'
                ]"
              >Can edit</button>
            </div>
          </div>

          <!-- Expiry selector -->
          <div>
            <label class="block text-xs text-theme-text-muted mb-1.5">Expires after</label>
            <div class="flex rounded-lg border border-theme-border overflow-hidden text-sm">
              <button
                v-for="opt in expiryOptions"
                :key="opt.value"
                @click="newExpiry = opt.value"
                :class="[
                  'flex-1 py-1.5 px-2 transition-colors text-center text-xs',
                  newExpiry === opt.value
                    ? 'bg-theme-brand text-white'
                    : 'bg-theme-background-elevated text-theme-text-muted hover:bg-theme-border',
                  'border-l border-theme-border first:border-l-0'
                ]"
              >{{ opt.label }}</button>
            </div>
          </div>

          <!-- Optional password -->
          <div>
            <label class="block text-xs text-theme-text-muted mb-1.5">
              Password protection
              <span class="text-theme-text-very-muted font-normal ml-1">(optional)</span>
            </label>
            <input
              v-model="newPassword"
              type="password"
              placeholder="Leave blank for no password"
              autocomplete="new-password"
              class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg
                     px-3 py-2 outline-none focus:border-theme-brand text-theme-text
                     placeholder:text-theme-text-very-muted transition-colors"
            />
          </div>

          <!-- Newly created link display -->
          <div
            v-if="newlyCreatedLink"
            class="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-green-500/8 border border-green-400/30"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current text-green-500 shrink-0">
              <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
            </svg>
            <input
              ref="linkInputEl"
              :value="newlyCreatedLink"
              readonly
              class="flex-1 min-w-0 text-xs font-mono bg-transparent outline-none text-theme-text truncate"
            />
            <button
              @click="copyNewLink"
              class="shrink-0 text-xs font-medium px-2 py-1 rounded bg-green-500/15 text-green-600
                     dark:text-green-400 hover:bg-green-500/25 transition-colors touch-manipulation"
            >{{ copiedNew ? 'Copied!' : 'Copy' }}</button>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-2 pt-1">
            <button
              @click="$emit('close')"
              class="px-3 py-1.5 rounded text-sm text-theme-text-muted border border-theme-border
                     hover:bg-theme-background-elevated transition-colors touch-manipulation"
            >Close</button>
            <button
              @click="createHandler"
              :disabled="creating"
              class="px-4 py-1.5 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                     text-white transition-colors disabled:opacity-50 touch-manipulation"
            >{{ creating ? 'Creating…' : 'Create link' }}</button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, nextTick } from "vue";
import { createShare, listShares, revokeShare, revokeShareByHash, revokeAllShares } from "../api.js";
import { getToastOptions } from "../helpers.js";
import { useToast } from "primevue/usetoast";

const props = defineProps({
  show:      { type: Boolean, default: false },
  noteTitle: { type: String,  required: true },
});

const emit = defineEmits(["close"]);

const toast            = useToast();
const shares           = ref([]);
const loadingShares    = ref(false);
const newPermission    = ref("read");
const newExpiry        = ref(null);   // null = no expiry
const newPassword      = ref("");     // optional password for new shares
const creating         = ref(false);
const newlyCreatedLink = ref("");
const copiedToken      = ref("");
const copiedNew        = ref(false);
const linkInputEl      = ref(null);
const confirmRevokeAll = ref(false);

// In-session token map: preview → raw token (cleared when modal closes)
// Raw tokens are never persisted — only held in memory for same-session revocation
const sessionTokens = ref({});

const expiryOptions = [
  { label: "7 days",  value: 7   },
  { label: "30 days", value: 30  },
  { label: "90 days", value: 90  },
  { label: "Never",   value: null },
];

const activeShareCount = computed(() =>
  shares.value.filter((s) => !isExpired(s)).length
);

// ── Helpers ───────────────────────────────────────────────────────────────────
function isExpired(share) {
  if (!share.expires_at) return false;
  try { return new Date(share.expires_at) < new Date(); } catch { return false; }
}

function shareUrl(token) {
  return `${window.location.origin}/shared/${token}`;
}

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch { return iso; }
}

function formatRelativeTime(iso) {
  if (!iso) return "";
  try {
    const diff  = Date.now() - new Date(iso).getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days  = Math.floor(diff / 86400000);
    if (mins  <  1) return "just now";
    if (mins  < 60) return `${mins} minute${mins  !== 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours  !== 1 ? 's' : ''} ago`;
    if (days  <  7) return `${days} day${days     !== 1 ? 's' : ''} ago`;
    return formatDate(iso);
  } catch { return ""; }
}

// ── Load shares when modal opens ──────────────────────────────────────────────
async function loadShares() {
  loadingShares.value    = true;
  newlyCreatedLink.value = "";
  confirmRevokeAll.value = false;
  try {
    shares.value = await listShares(props.noteTitle);
  } catch {
    shares.value = [];
  } finally {
    loadingShares.value = false;
  }
}

watch(() => props.show, (val) => {
  if (val) {
    newPermission.value    = "read";
    newExpiry.value        = null;
    newPassword.value      = "";
    newlyCreatedLink.value = "";
    copiedNew.value        = false;
    confirmRevokeAll.value = false;
    sessionTokens.value    = {};
    loadShares();
  }
});

// ── Create ────────────────────────────────────────────────────────────────────
async function createHandler() {
  creating.value = true;
  try {
    const password = newPassword.value.trim() || null;
    const result   = await createShare(props.noteTitle, newPermission.value, newExpiry.value, password);
    newlyCreatedLink.value = shareUrl(result.token);
    // Store raw token keyed by preview for same-session revocation
    sessionTokens.value[result.token_preview] = result.token;
    newPassword.value = "";
    await loadShares();
    await nextTick();
    linkInputEl.value?.select();
  } catch {
    toast.add(getToastOptions("Failed to create share link.", "Error", "error"));
  } finally {
    creating.value = false;
  }
}

// ── Copy ──────────────────────────────────────────────────────────────────────
async function copyLink(tokenPreview) {
  const rawToken = sessionTokens.value[tokenPreview];
  if (rawToken) {
    await navigator.clipboard.writeText(shareUrl(rawToken));
    copiedToken.value = tokenPreview;
    setTimeout(() => { copiedToken.value = ""; }, 2000);
  } else {
    toast.add(getToastOptions(
      "The full link is only shown once at creation. Create a new link if you need to share it again.",
      "Link unavailable", "warn"
    ));
  }
}

async function copyNewLink() {
  await navigator.clipboard.writeText(newlyCreatedLink.value);
  copiedNew.value = true;
  setTimeout(() => { copiedNew.value = false; }, 2000);
}

// ── Revoke single ─────────────────────────────────────────────────────────────
// Now accepts the full share object. If a same-session raw token exists we use
// revokeShare(rawToken); otherwise we fall back to revokeShareByHash(s.id) which
// is now returned by list_shares so cross-session revocation always works.
async function revokeHandler(share) {
  const rawToken = sessionTokens.value[share.token_preview];
  try {
    if (rawToken) {
      await revokeShare(rawToken);
      delete sessionTokens.value[share.token_preview];
      if (newlyCreatedLink.value.includes(rawToken)) {
        newlyCreatedLink.value = "";
      }
    } else {
      // Cross-session: use the hash id returned by list_shares
      await revokeShareByHash(share.id);
    }
    toast.add(getToastOptions("Share link revoked ✓", "Success", "success"));
    await loadShares();
  } catch {
    toast.add(getToastOptions("Failed to revoke share link.", "Error", "error"));
  }
}

// ── Revoke all ────────────────────────────────────────────────────────────────
async function doRevokeAll() {
  confirmRevokeAll.value = false;
  try {
    const result = await revokeAllShares(props.noteTitle);
    const count  = result?.revoked ?? 0;
    sessionTokens.value = {};
    newlyCreatedLink.value = "";
    toast.add(getToastOptions(`Revoked ${count} link${count !== 1 ? 's' : ''} ✓`, "Success", "success"));
    await loadShares();
  } catch {
    toast.add(getToastOptions("Failed to revoke all links.", "Error", "error"));
  }
}
</script>
