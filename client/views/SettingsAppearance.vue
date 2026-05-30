<template>
  <div class="space-y-6">

    <!-- ── Header Colors Section ─────────────────────────────────────────── -->
    <div>
      <h3 class="text-lg font-medium text-theme-text mb-1">Header Colors</h3>
      <p class="text-sm text-theme-text-muted mb-4">Customize colors for headings H1 through H6.</p>

      <!-- Enable / disable slider -->
      <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div>
          <p class="text-sm font-medium text-theme-text">Enable custom header colors</p>
          <p class="text-xs text-theme-text-muted mt-0.5">Apply custom colors to H1–H6 headings.</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
          <input type="checkbox" v-model="headersEnabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <div class="space-y-2 p-4 rounded-lg border border-theme-border bg-theme-background"
           :class="!headersEnabled ? 'opacity-50 pointer-events-none' : ''">
        <div v-for="header in editableHeaders" :key="header.level"
             class="flex flex-wrap items-center gap-3 py-1">
          <!-- Level label -->
          <div class="w-8 text-sm font-semibold text-theme-text shrink-0">H{{ header.level }}</div>

          <!-- Color square -->
          <input
            type="color"
            v-model="header.color"
            :disabled="!header.enabled"
            class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent shrink-0 disabled:opacity-40"
          />

          <!-- Hex input -->
          <input
            v-model="header.color"
            :disabled="!header.enabled"
            class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                   rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text
                   uppercase disabled:opacity-40"
          />

          <!-- Live preview -->
          <span
            :style="{ color: header.enabled ? header.color : 'var(--theme-text-muted)' }"
            class="flex-1 min-w-[6rem] text-sm font-semibold truncate transition-colors"
          >
            Heading {{ header.level }} preview
          </span>

          <!-- Per-row enabled slider -->
          <label class="relative inline-flex items-center cursor-pointer shrink-0">
            <input type="checkbox" v-model="header.enabled" class="sr-only peer" />
            <div class="w-9 h-5 bg-theme-border rounded-full peer
                        peer-checked:bg-theme-brand transition-colors
                        after:content-[''] after:absolute after:top-0.5 after:left-0.5
                        after:bg-white after:rounded-full after:h-4 after:w-4
                        after:transition-transform peer-checked:after:translate-x-4"></div>
          </label>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-3">
        <button
          @click="saveHeaders"
          :disabled="headersSaving"
          class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
        >{{ headersSaving ? 'Saving…' : 'Save Header Colors' }}</button>
        <span v-if="headersSaveMsg" class="text-sm" :class="headersSaveOk ? 'text-green-500' : 'text-red-500'">{{ headersSaveMsg }}</span>
      </div>
    </div>

    <!-- Divider -->
    <div class="border-t border-theme-border my-4"></div>

    <!-- ── Highlight Colors Section ──────────────────────────────────────── -->
    <div>
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-lg font-medium text-theme-text">Highlight Colors</h3>
        <button
          @click="addHighlightColor"
          class="flex items-center gap-1.5 px-2 py-1 rounded text-xs
                 bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
        >
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
          Add color
        </button>
      </div>
      <p class="text-sm text-theme-text-muted mb-4">
        These colors appear in the highlight picker. The default color is used when highlighting text with the toolbar button.
      </p>

      <div class="space-y-3">
        <div v-for="(hc, idx) in editableHighlights" :key="hc._key"
             class="flex flex-wrap items-center gap-2 p-2 rounded-lg border border-theme-border bg-theme-background">
          <input type="color" v-model="hc.color" :disabled="!hc.enabled"
                 class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent shrink-0 disabled:opacity-40" />
          <input v-model="hc.name" placeholder="Name"
                 class="w-24 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text" />
          <input v-model="hc.color"
                 class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase" />
          <!-- Per-row enabled slider -->
          <label class="relative inline-flex items-center cursor-pointer shrink-0 ml-1">
            <input type="checkbox" v-model="hc.enabled" class="sr-only peer" />
            <div class="w-9 h-5 bg-theme-border rounded-full peer
                        peer-checked:bg-theme-brand transition-colors
                        after:content-[''] after:absolute after:top-0.5 after:left-0.5
                        after:bg-white after:rounded-full after:h-4 after:w-4
                        after:transition-transform peer-checked:after:translate-x-4"></div>
          </label>
          <button
            @click="setDefaultHighlight(hc.name)"
            class="px-2 py-1 rounded text-xs border border-theme-border bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors touch-manipulation"
            :class="{ 'bg-theme-brand/20 border-theme-brand': defaultHighlightName === hc.name }"
            title="Set as default"
          >
            Default
          </button>
          <button
            v-if="!hc.isDefault"
            @click="removeHighlightColor(idx)"
            class="text-theme-text-muted hover:text-red-500 transition-colors p-1 rounded shrink-0 touch-manipulation"
            title="Delete color"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
          </button>
          <span v-else class="text-theme-text-very-muted" title="Built-in color (cannot be deleted)">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
            </svg>
          </span>
        </div>
      </div>

      <div class="mt-4 p-3 rounded-lg bg-theme-background-elevated border border-theme-border">
        <p class="text-sm text-theme-text-muted mb-2">Preview with default highlight:</p>
        <mark :style="{ backgroundColor: defaultHighlightColor, padding: '0 4px', borderRadius: '2px' }">This is how highlighted text appears</mark>
      </div>

      <div class="mt-3 flex items-center gap-3">
        <button
          @click="saveHighlights"
          :disabled="highlightsSaving"
          class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
        >{{ highlightsSaving ? 'Saving…' : 'Save Highlight Colors' }}</button>
        <span v-if="highlightsSaveMsg" class="text-sm" :class="highlightsSaveOk ? 'text-green-500' : 'text-red-500'">{{ highlightsSaveMsg }}</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  getHeaderColors, saveHeaderColors,
  getHighlightColors, saveHighlightColors, getDefaultHighlight, saveDefaultHighlight,
} from "../api.js";
import { loadHeaderColors, loadHighlightColors } from "../appearanceStore.js";

// ── Header Colors ─────────────────────────────────────────────────────────────
const editableHeaders = ref([]);
const headersSaving = ref(false);
const headersSaveMsg = ref("");
const headersSaveOk = ref(true);

const headersEnabled = computed({
  get() {
    return editableHeaders.value.some(h => h.enabled);
  },
  set(val) {
    editableHeaders.value.forEach(h => { h.enabled = val; });
  },
});

async function loadHeaders() {
  try {
    const data = await getHeaderColors();
    editableHeaders.value = data;
  } catch {
    editableHeaders.value = [
      { level: 1, color: "#ed7ea3", enabled: true },
      { level: 2, color: "#A3BE8C", enabled: true },
      { level: 3, color: "#66CCCC", enabled: true },
      { level: 4, color: "#95d5ea", enabled: true },
      { level: 5, color: "#999999", enabled: true },
      { level: 6, color: "#666666", enabled: true },
    ];
  }
}

async function saveHeaders() {
  headersSaving.value = true;
  headersSaveMsg.value = "";
  try {
    await saveHeaderColors(editableHeaders.value);
    await loadHeaderColors(true);
    headersSaveOk.value = true;
    headersSaveMsg.value = "Saved ✓";
  } catch {
    headersSaveOk.value = false;
    headersSaveMsg.value = "Save failed";
  } finally {
    headersSaving.value = false;
    setTimeout(() => { headersSaveMsg.value = ""; }, 3000);
  }
}

// ── Highlight Colors ──────────────────────────────────────────────────────────
const editableHighlights = ref([]);
const defaultHighlightName = ref("");
const defaultHighlightColor = ref("#ffffcc");
const highlightsSaving = ref(false);
const highlightsSaveMsg = ref("");
const highlightsSaveOk = ref(true);
let highlightKeyCounter = 100;

async function loadHighlights() {
  try {
    const data = await getHighlightColors();
    editableHighlights.value = data.map(h => ({ ...h, _key: h.isDefault ? h.name : highlightKeyCounter++ }));
    const defaultName = await getDefaultHighlight();
    defaultHighlightName.value = defaultName;
    const found = data.find(h => h.name === defaultName);
    defaultHighlightColor.value = found ? found.color : "#ffffcc";
  } catch {
    editableHighlights.value = [
      { name: "Red",    color: "#ffcccc", enabled: true, isDefault: true, _key: "Red" },
      { name: "Yellow", color: "#ffffcc", enabled: true, isDefault: true, _key: "Yellow" },
      { name: "Green",  color: "#ccffcc", enabled: true, isDefault: true, _key: "Green" },
      { name: "Blue",   color: "#ccccff", enabled: true, isDefault: true, _key: "Blue" },
      { name: "Orange", color: "#ffddcc", enabled: true, isDefault: true, _key: "Orange" },
    ];
    defaultHighlightName.value = "Yellow";
    defaultHighlightColor.value = "#ffffcc";
  }
}

function addHighlightColor() {
  editableHighlights.value.push({
    _key: highlightKeyCounter++,
    name: "Custom",
    color: "#dddddd",
    enabled: true,
    isDefault: false,
  });
}

function removeHighlightColor(idx) {
  editableHighlights.value.splice(idx, 1);
}

function setDefaultHighlight(name) {
  defaultHighlightName.value = name;
  const found = editableHighlights.value.find(h => h.name === name);
  if (found) {
    defaultHighlightColor.value = found.color;
  }
}

async function saveHighlights() {
  highlightsSaving.value = true;
  highlightsSaveMsg.value = "";
  try {
    const payload = editableHighlights.value.map(({ _key, ...rest }) => rest);
    await saveHighlightColors(payload);
    await saveDefaultHighlight(defaultHighlightName.value);
    await loadHighlightColors(true);
    highlightsSaveOk.value = true;
    highlightsSaveMsg.value = "Saved ✓";
  } catch {
    highlightsSaveOk.value = false;
    highlightsSaveMsg.value = "Save failed";
  } finally {
    highlightsSaving.value = false;
    setTimeout(() => { highlightsSaveMsg.value = ""; }, 3000);
  }
}

// ── Load on mount ─────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadHeaders();
  await loadHighlights();
});
</script>
