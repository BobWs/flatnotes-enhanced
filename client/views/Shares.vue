<template>
  <LoadingIndicator ref="loadingIndicator" class="mx-auto flex h-full max-w-[999px] flex-col">

    <!-- Header row -->
    <div class="flex items-center justify-between mb-4 gap-3 flex-wrap">
      <div class="shrink-0">
        <h1 class="text-2xl font-semibold text-theme-text">Shared Links</h1>
        <p class="text-sm text-theme-text-muted mt-0.5">
          {{ totalCount }} active share link{{ totalCount !== 1 ? 's' : '' }}
          across {{ noteGroups.length }} note{{ noteGroups.length !== 1 ? 's' : '' }}
        </p>
      </div>

      <!-- Refresh -->
      <button
        @click="loadShares"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
               bg-theme-background-elevated hover:bg-theme-border border border-theme-border transition-colors text-theme-text-muted"
        title="Refresh"
      >
        <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current" :class="{ 'animate-spin': loading }">
          <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
        </svg>
        Refresh
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && noteGroups.length === 0"
      class="flex flex-col items-center justify-center flex-1 text-theme-text-very-muted gap-3"
    >
      <svg viewBox="0 0 24 24" class="w-16 h-16 fill-current opacity-30">
        <path d="M18,16.08C17.24,16.08 16.56,16.38 16.04,16.85L8.91,12.7C8.96,12.47 9,12.24 9,12C9,11.76 8.96,11.53 8.91,11.3L15.96,7.19C16.5,7.69 17.21,8 18,8A3,3 0 0,0 21,5A3,3 0 0,0 18,2A3,3 0 0,0 15,5C15,5.24 15.04,5.47 15.09,5.7L8.04,9.81C7.5,9.31 6.79,9 6,9A3,3 0 0,0 3,12A3,3 0 0,0 6,15C6.79,15 7.5,14.69 8.04,14.19L15.16,18.34C15.11,18.55 15.08,18.77 15.08,19C15.08,20.61 16.39,21.91 18,21.91C19.61,21.91 20.92,20.61 20.92,19A2.92,2.92 0 0,0 18,16.08Z"/>
      </svg>
      <p class="text-sm">No active share links</p>
      <p class="text-xs text-theme-text-very-muted">Share links you create will appear here</p>
    </div>

    <!-- Per-note groups -->
    <div v-else class="flex flex-col gap-6 overflow-y-auto flex-1 pb-4">
      <div v-for="group in noteGroups" :key="group.noteTitle">

        <!-- Note heading row -->
        <div class="flex items-center justify-between gap-3 mb-2 flex-wrap">
          <button
            @click="openNote(group.noteTitle)"
            class="text-sm font-semibold text-theme-brand hover:underline truncate text-left"
            :title="group.noteTitle"
          >{{ group.noteTitle }}</button>

          <!-- Revoke all for this note -->
          <div class="flex items-center gap-2 shrink-0">
            <template v-if="group.shares.length >= 2">
              <span
                v-if="pendingRevokeAll === group.noteTitle"
                class="text-xs text-theme-text-muted"
              >
                Revoke all {{ group.shares.length }} links?
              </span>
              <button
                v-if="pendingRevokeAll === group.noteTitle"
                @click="doRevokeAll(group.noteTitle)"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium
                       text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors touch-manipulation"
              >Confirm</button>
              <button
                v-if="pendingRevokeAll === group.noteTitle"
                @click="pendingRevokeAll = ''"
                class="inline-flex items-center px-2.5 py-1 rounded text-xs
                       text-theme-text-muted border border-theme-border hover:bg-theme-background-elevated transition-colors touch-manipulation"
              >Cancel</button>
              <button
                v-else
                @click="pendingRevokeAll = group.noteTitle"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium
                       text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors touch-manipulation"
                title="Revoke all links for this note"
              >
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
                Revoke all
              </button>
            </template>
          </div>
        </div>

        <!-- Share cards for this note -->
        <div class="flex flex-col gap-2">
          <div
            v-for="s in group.shares"
            :key="s.id"
            class="rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3"
            :class="isExpired(s) ? 'opacity-60' : ''"
          >
            <!-- Top row: preview + badges -->
            <div class="flex items-start justify-between gap-3 flex-wrap">
              <div class="flex items-center gap-2 flex-wrap min-w-0">
                <code class="text-xs font-mono text-theme-text-muted shrink-0">{{ s.token_preview }}…</code>

                <!-- Expired badge -->
                <span
                  v-if="isExpired(s)"
                  class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-500"
                >Expired</span>

                <!-- Permission badge -->
                <span
                  class="text-xs font-medium px-1.5 py-0.5 rounded-full"
                  :class="s.permission === 'write'
                    ? 'bg-theme-brand/15 text-theme-brand'
                    : 'bg-theme-background text-theme-text-muted border border-theme-border'"
                >{{ s.permission === 'write' ? 'Can edit' : 'Read only' }}</span>

                <!-- Password badge -->
                <span v-if="s.has_password" class="text-xs text-theme-text-very-muted flex items-center gap-0.5">
                  <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
                    <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                  </svg>
                  Password
                </span>
              </div>

              <!-- Revoke button -->
              <button
                @click="promptRevoke(s)"
                class="shrink-0 inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                       text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors touch-manipulation"
                title="Revoke this link"
              >
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
                Revoke
              </button>
            </div>

            <!-- Meta row: activity + dates -->
            <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-theme-text-muted">
              <!-- Access count -->
              <span class="flex items-center gap-1">
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current text-theme-text-very-muted">
                  <path d="M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/>
                </svg>
                {{ s.access_count }} view{{ s.access_count !== 1 ? 's' : '' }}
              </span>

              <!-- Last accessed -->
              <span v-if="s.last_accessed_at" class="flex items-center gap-1">
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current text-theme-text-very-muted">
                  <path d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/>
                </svg>
                Last accessed {{ formatRelativeTime(s.last_accessed_at) }}
              </span>
              <span v-else class="text-theme-text-very-muted">Never accessed</span>

              <!-- Expiry -->
              <span v-if="s.expires_at" class="flex items-center gap-1">
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current text-theme-text-very-muted">
                  <path d="M6,2V8H6V8L10,12L6,16V16H6V22H18V16H18V16L14,12L18,8V8H18V2H6M16,16.5V20H8V16.5L12,12.5L16,16.5M12,11.5L8,7.5V4H16V7.5L12,11.5Z"/>
                </svg>
                {{ isExpired(s) ? 'Expired' : 'Expires' }} {{ formatDate(s.expires_at) }}
              </span>
              <span v-else class="text-theme-text-very-muted">No expiry</span>

              <!-- Created -->
              <span v-if="s.created_at" class="flex items-center gap-1 text-theme-text-very-muted">
                Created {{ formatDate(s.created_at) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Revoke single confirm inline toast-free confirm -->
    <div
      v-if="pendingRevoke"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="pendingRevoke = null"
    >
      <div class="bg-theme-background rounded-t-2xl sm:rounded-xl border border-theme-border shadow-xl
                  w-full sm:w-[400px] sm:max-w-full p-5">
        <h3 class="text-base font-semibold text-theme-text mb-1">Revoke share link?</h3>
        <p class="text-sm text-theme-text-muted mb-4">
          The link <code class="font-mono">{{ pendingRevoke.token_preview }}…</code> for
          <span class="font-medium">{{ pendingRevoke.note_title }}</span>
          will be permanently revoked. Anyone with the link will lose access.
        </p>
        <div class="flex justify-end gap-2">
          <button
            @click="pendingRevoke = null"
            class="px-4 py-1.5 rounded text-sm text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors touch-manipulation"
          >Cancel</button>
          <button
            @click="doRevoke"
            class="px-4 py-1.5 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors touch-manipulation"
          >Revoke</button>
        </div>
      </div>
    </div>

  </LoadingIndicator>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";

import { apiErrorHandler, listAllShares, revokeShareByHash, revokeAllShares } from "../api.js";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import { getToastOptions } from "../helpers.js";

const loadingIndicator = ref();
const loading          = ref(false);
const shares           = ref([]);
const pendingRevoke    = ref(null);   // share object awaiting single-revoke confirm
const pendingRevokeAll = ref("");     // noteTitle awaiting bulk-revoke confirm
const toast            = useToast();
const router           = useRouter();

// ── Derived data ──────────────────────────────────────────────────────────────

const noteGroups = computed(() => {
  // Group shares by note_title, preserving newest-first order within each group
  const map = new Map();
  for (const s of shares.value) {
    if (!map.has(s.note_title)) map.set(s.note_title, []);
    map.get(s.note_title).push(s);
  }
  // Convert to array; order of notes = first occurrence (server returns newest-first overall)
  return Array.from(map.entries()).map(([noteTitle, noteShares]) => ({
    noteTitle,
    shares: noteShares,
  }));
});

const totalCount = computed(() => shares.value.length);

// ── Helpers ───────────────────────────────────────────────────────────────────

function isExpired(share) {
  if (!share.expires_at) return false;
  try { return new Date(share.expires_at) < new Date(); } catch { return false; }
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
    const diff = Date.now() - new Date(iso).getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days  = Math.floor(diff / 86400000);
    if (mins  <  1)   return "just now";
    if (mins  < 60)   return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
    if (hours < 24)   return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    if (days  <  7)   return `${days} day${days  !== 1 ? 's' : ''} ago`;
    return formatDate(iso);
  } catch { return ""; }
}

function openNote(title) {
  router.push({ name: "note", params: { title } });
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadShares() {
  loading.value = true;
  loadingIndicator.value?.setLoading();
  try {
    shares.value = await listAllShares();
    loadingIndicator.value?.setLoaded();
  } catch (error) {
    loadingIndicator.value?.setFailed();
    apiErrorHandler(error, toast);
  } finally {
    loading.value = false;
  }
}

// ── Revoke single ─────────────────────────────────────────────────────────────

function promptRevoke(share) {
  pendingRevoke.value = share;
}

async function doRevoke() {
  if (!pendingRevoke.value) return;
  const share = pendingRevoke.value;
  pendingRevoke.value = null;
  try {
    await revokeShareByHash(share.id);
    toast.add(getToastOptions("Share link revoked ✓", "Success", "success"));
    await loadShares();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

// ── Revoke all for a note ─────────────────────────────────────────────────────

async function doRevokeAll(noteTitle) {
  pendingRevokeAll.value = "";
  try {
    const result = await revokeAllShares(noteTitle);
    const count  = result?.revoked ?? 0;
    toast.add(getToastOptions(`Revoked ${count} link${count !== 1 ? 's' : ''} for '${noteTitle}' ✓`, "Success", "success"));
    await loadShares();
  } catch (error) {
    apiErrorHandler(error, toast);
  }
}

onMounted(loadShares);
</script>
