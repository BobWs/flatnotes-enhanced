<template>
  <div>
    <h3 class="text-lg font-medium text-theme-text mb-1">Custom Task Icons</h3>
    <p class="text-sm text-theme-text-muted mb-4">
      Customize the colors for Obsidian-style task markers.
      Use <code class="bg-theme-background-elevated px-1 rounded text-xs">- [?] Question text</code> in your notes.
    </p>

    <!-- Global enable / disable toggle -->
    <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
      <div>
        <p class="text-sm font-medium text-theme-text">Enable custom task icons</p>
        <p class="text-xs text-theme-text-muted mt-0.5">Render task markers as icons instead of plain text in the note viewer.</p>
      </div>
      <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
        <input type="checkbox" v-model="taskIconsEnabled" class="sr-only peer" />
        <div class="w-11 h-6 bg-theme-border rounded-full peer
                    peer-checked:bg-theme-brand transition-colors
                    after:content-[''] after:absolute after:top-0.5 after:left-0.5
                    after:bg-white after:rounded-full after:h-5 after:w-5
                    after:transition-transform peer-checked:after:translate-x-5"></div>
      </label>
    </div>

    <!-- Icon color list -->
    <div
      class="border border-theme-border rounded-lg overflow-hidden mb-3"
      :class="!taskIconsEnabled ? 'opacity-50 pointer-events-none' : ''"
    >
      <!-- Column header — hidden on mobile, shown on sm+ -->
      <div class="hidden sm:grid px-3 py-2 bg-theme-background-elevated border-b border-theme-border
                  grid-cols-[1.75rem_7rem_1fr_9rem_1.75rem] gap-3 items-center sticky top-0 z-10">
        <span class="text-xs text-theme-text-very-muted font-medium">Icon</span>
        <span class="text-xs text-theme-text-very-muted font-medium">Syntax</span>
        <span class="text-xs text-theme-text-very-muted font-medium">Label</span>
        <span class="text-xs text-theme-text-very-muted font-medium">Color</span>
        <span></span>
      </div>

      <div class="overflow-y-auto" style="max-height: 380px;">
        <div
          v-for="row in taskIconColors"
          :key="row.marker"
          class="border-b border-theme-border last:border-b-0 bg-theme-background hover:bg-theme-background-elevated/40 transition-colors"
        >
          <!-- Desktop layout (sm and up) -->
          <div class="hidden sm:grid grid-cols-[1.75rem_7rem_1fr_9rem_1.75rem] gap-3 items-center px-3 py-2">
            <span class="flex items-center justify-center">
              <svg viewBox="0 0 24 24" width="18" height="18" :fill="row.color">
                <path :d="row.iconPath" />
              </svg>
            </span>
            <code class="text-xs font-mono bg-theme-background-elevated px-2 py-0.5 rounded text-theme-text-muted whitespace-nowrap">
              - [{{ row.marker }}] text
            </code>
            <span class="text-sm text-theme-text capitalize">{{ row.label }}</span>
            <div class="flex items-center gap-1.5">
              <input
                type="color"
                v-model="row.color"
                class="w-7 h-7 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
                :title="'Color for [' + row.marker + ']'"
              />
              <input
                v-model="row.color"
                class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                       rounded px-1.5 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
                @input="row.color = normalizeHex($event.target.value)"
              />
            </div>
            <button
              @click="resetTaskIconColor(row.marker)"
              class="text-theme-text-very-muted hover:text-theme-text-muted transition-colors p-0.5 rounded touch-manipulation"
              title="Reset to default color"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                <path d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
              </svg>
            </button>
          </div>

          <!-- Mobile layout (below sm) -->
          <div class="flex sm:hidden items-center gap-3 px-3 py-2.5">
            <svg viewBox="0 0 24 24" width="20" height="20" :fill="row.color" class="shrink-0">
              <path :d="row.iconPath" />
            </svg>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-theme-text capitalize">{{ row.label }}</p>
              <code class="text-xs font-mono text-theme-text-muted">- [{{ row.marker }}] text</code>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <input
                type="color"
                v-model="row.color"
                class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent"
                :title="'Color for [' + row.marker + ']'"
              />
              <input
                v-model="row.color"
                class="w-20 text-xs font-mono bg-theme-background-elevated border border-theme-border
                       rounded px-1.5 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
                @input="row.color = normalizeHex($event.target.value)"
              />
            </div>
            <button
              @click="resetTaskIconColor(row.marker)"
              class="text-theme-text-very-muted hover:text-theme-text-muted transition-colors p-1 rounded shrink-0 touch-manipulation"
              title="Reset to default color"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                <path d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Usage reference -->
    <div class="mb-4 p-3 rounded-lg bg-theme-background-elevated border border-theme-border">
      <p class="text-xs font-medium text-theme-text-muted mb-2">Quick reference — use these in your notes:</p>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-1.5">
        <div v-for="row in taskIconColors.slice(0, 9)" :key="'ref-' + row.marker" class="flex items-center gap-2 min-w-0">
          <svg viewBox="0 0 24 24" width="13" height="13" :fill="taskIconsEnabled ? row.color : 'currentColor'" class="shrink-0 text-theme-text-very-muted">
            <path :d="row.iconPath" />
          </svg>
          <code class="text-xs text-theme-text-muted font-mono shrink-0">- [{{ row.marker }}]</code>
          <span class="text-xs text-theme-text-very-muted capitalize truncate">{{ row.label }}</span>
        </div>
      </div>
      <p class="text-xs text-theme-text-very-muted mt-2 italic">
        … and {{ taskIconColors.length - 9 }} more. All markers are Obsidian-compatible.
      </p>
    </div>

    <!-- Actions row -->
    <div class="flex flex-wrap items-center gap-3">
      <button
        @click="saveTaskIconSettings"
        :disabled="taskIconsSaving"
        class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
               text-white transition-colors touch-manipulation"
      >{{ taskIconsSaving ? 'Saving…' : 'Save task icons' }}</button>
      <button
        @click="resetAllTaskIconColors"
        class="px-3 py-1.5 rounded text-sm border border-theme-border
               bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text-muted touch-manipulation"
      >Reset all colors</button>
      <span v-if="taskIconsSaveMsg" class="text-sm" :class="taskIconsSaveOk ? 'text-green-500' : 'text-red-500'">
        {{ taskIconsSaveMsg }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getTaskIcons, saveTaskIcons as apiSaveTaskIcons } from "../api.js";
import { loadTaskIcons } from "../taskIconStore.js";
import { TASK_ICONS } from "../taskIcons.js";

// ── State ─────────────────────────────────────────────────────────────────────
const taskIconsEnabled = ref(true);
const taskIconColors = ref(
  TASK_ICONS.map(icon => ({ marker: icon.marker, label: icon.label, iconPath: icon.iconPath, color: "#6B7280" }))
);
const taskIconsSaving = ref(false);
const taskIconsSaveMsg = ref("");
const taskIconsSaveOk = ref(true);

// ── Helpers ───────────────────────────────────────────────────────────────────
function normalizeHex(val) {
  if (!val.startsWith("#")) val = "#" + val;
  return val.length <= 7 ? val : val.slice(0, 7);
}

function resetTaskIconColor(marker) {
  const row = taskIconColors.value.find(r => r.marker === marker);
  if (row) row.color = "#6B7280";
}

function resetAllTaskIconColors() {
  taskIconColors.value.forEach(r => { r.color = "#6B7280"; });
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadTaskIconSettings() {
  try {
    const data = await getTaskIcons();
    taskIconsEnabled.value = data.enabled ?? true;
    taskIconColors.value = TASK_ICONS.map(icon => {
      const stored = (data.colors || []).find(c => c.marker === icon.marker);
      return {
        marker: icon.marker,
        label: icon.label,
        iconPath: icon.iconPath,
        color: stored?.color ?? "#6B7280",
      };
    });
  } catch {
    // keep defaults
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveTaskIconSettings() {
  taskIconsSaving.value = true;
  taskIconsSaveMsg.value = "";
  try {
    const payload = {
      enabled: taskIconsEnabled.value,
      colors: taskIconColors.value.map(({ marker, color }) => ({ marker, color })),
    };
    await apiSaveTaskIcons(payload);
    await loadTaskIcons(true);
    taskIconsSaveOk.value = true;
    taskIconsSaveMsg.value = "Saved ✓";
  } catch {
    taskIconsSaveOk.value = false;
    taskIconsSaveMsg.value = "Save failed";
  } finally {
    taskIconsSaving.value = false;
    setTimeout(() => { taskIconsSaveMsg.value = ""; }, 3000);
  }
}

onMounted(loadTaskIconSettings);
</script>
