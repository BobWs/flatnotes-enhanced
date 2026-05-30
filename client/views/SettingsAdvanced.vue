<template>
  <div class="space-y-8">

    <!-- ── Table Styling Section ─────────────────────────────────────────── -->
    <div>
      <h3 class="text-lg font-medium text-theme-text mb-1">Table Styling</h3>
      <p class="text-sm text-theme-text-muted mb-4">Customize how tables appear in your notes.</p>

      <!-- Enable / disable slider -->
      <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div>
          <p class="text-sm font-medium text-theme-text">Enable custom table styling</p>
          <p class="text-xs text-theme-text-muted mt-0.5">Apply custom header colors and zebra-striped rows.</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
          <input type="checkbox" v-model="tableStyle.enabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <div class="space-y-4 p-4 rounded-lg border border-theme-border bg-theme-background">
        <!-- Header color picker -->
        <div class="flex flex-wrap items-center gap-4">
          <div class="w-24 text-sm text-theme-text">Header color</div>
          <input
            type="color"
            v-model="tableStyle.header_color"
            :disabled="!tableStyle.enabled"
            class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
          />
          <input
            v-model="tableStyle.header_color"
            :disabled="!tableStyle.enabled"
            class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
          />
        </div>

        <!-- Zebra striping toggle -->
        <div class="flex items-center gap-4">
          <div class="w-24 text-sm text-theme-text shrink-0">Zebra striping</div>
          <label class="relative inline-flex items-center cursor-pointer" :class="!tableStyle.enabled ? 'opacity-40 pointer-events-none' : ''">
            <input type="checkbox" v-model="tableStyle.zebra_striping" :disabled="!tableStyle.enabled" class="sr-only peer" />
            <div class="w-9 h-5 bg-theme-border rounded-full peer
                        peer-checked:bg-theme-brand transition-colors
                        after:content-[''] after:absolute after:top-0.5 after:left-0.5
                        after:bg-white after:rounded-full after:h-4 after:w-4
                        after:transition-transform peer-checked:after:translate-x-4"></div>
          </label>
          <span class="text-sm text-theme-text-muted">Alternate row colors</span>
        </div>

        <!-- Table preview -->
        <div class="mt-4 pt-4 border-t border-theme-border">
          <p class="text-xs text-theme-text-very-muted mb-3">Preview:</p>
          <div class="overflow-x-auto">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr>
                  <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 1</th>
                  <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 2</th>
                  <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 3</th>
                </tr>
              </thead>
              <tbody>
                <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? 'bg-theme-background-elevated' : ''">
                  <td class="border border-theme-border px-3 py-2">Row 1, Cell 1</td>
                  <td class="border border-theme-border px-3 py-2">Row 1, Cell 2</td>
                  <td class="border border-theme-border px-3 py-2">Row 1, Cell 3</td>
                </tr>
                <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? '' : 'bg-theme-background-elevated'">
                  <td class="border border-theme-border px-3 py-2">Row 2, Cell 1</td>
                  <td class="border border-theme-border px-3 py-2">Row 2, Cell 2</td>
                  <td class="border border-theme-border px-3 py-2">Row 2, Cell 3</td>
                </tr>
                <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? 'bg-theme-background-elevated' : ''">
                  <td class="border border-theme-border px-3 py-2">Row 3, Cell 1</td>
                  <td class="border border-theme-border px-3 py-2">Row 3, Cell 2</td>
                  <td class="border border-theme-border px-3 py-2">Row 3, Cell 3</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-3">
        <button
          @click="saveTableStyle"
          :disabled="tableSaving"
          class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
        >{{ tableSaving ? 'Saving…' : 'Save Table Style' }}</button>
        <span v-if="tableSaveMsg" class="text-sm" :class="tableSaveOk ? 'text-green-500' : 'text-red-500'">{{ tableSaveMsg }}</span>
      </div>
    </div>

    <!-- Divider -->
    <div class="border-t border-theme-border my-4"></div>

    <!-- ── Quote Styling Section ──────────────────────────────────────────── -->
    <div>
      <h3 class="text-lg font-medium text-theme-text mb-1">Quote Styling</h3>
      <p class="text-sm text-theme-text-muted mb-4">Customize how blockquotes appear in your notes.</p>

      <!-- Enable / disable slider -->
      <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div>
          <p class="text-sm font-medium text-theme-text">Enable custom quote styling</p>
          <p class="text-xs text-theme-text-muted mt-0.5">Apply custom border color and background to blockquotes.</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
          <input type="checkbox" v-model="quoteStyle.enabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <div class="space-y-4 p-4 rounded-lg border border-theme-border bg-theme-background">
        <!-- Border color picker -->
        <div class="flex flex-wrap items-center gap-4">
          <div class="w-24 text-sm text-theme-text">Border color</div>
          <input
            type="color"
            v-model="quoteStyle.border_color"
            :disabled="!quoteStyle.enabled"
            class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
          />
          <input
            v-model="quoteStyle.border_color"
            :disabled="!quoteStyle.enabled"
            class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
          />
        </div>

        <!-- Light mode background picker -->
        <div class="flex flex-wrap items-center gap-4">
          <div class="w-24 text-sm text-theme-text">Light background</div>
          <input
            type="color"
            v-model="quoteStyle.background_color"
            :disabled="!quoteStyle.enabled"
            class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
          />
          <input
            v-model="quoteStyle.background_color"
            :disabled="!quoteStyle.enabled"
            class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
          />
        </div>

        <!-- Dark mode background picker (color + opacity) -->
        <div class="flex flex-wrap items-center gap-4">
          <div class="w-24 text-sm text-theme-text">Dark background</div>
          <input
            type="color"
            v-model="darkBgHex"
            :disabled="!quoteStyle.enabled"
            class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
          />
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-2">
              <span class="text-xs text-theme-text-muted w-14">Opacity</span>
              <input
                type="range"
                v-model.number="darkBgOpacity"
                :disabled="!quoteStyle.enabled"
                min="0" max="100" step="1"
                class="w-24 accent-theme-brand disabled:opacity-50"
              />
              <span class="text-xs font-mono text-theme-text w-8">{{ darkBgOpacity }}%</span>
            </div>
            <p class="text-xs text-theme-text-very-muted">Applied only in dark mode</p>
          </div>
        </div>

        <!-- Quote preview — respects current dark/light theme -->
        <div class="mt-4 pt-4 border-t border-theme-border">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-theme-text-very-muted">Preview:</p>
            <span class="text-xs text-theme-text-very-muted italic">
              {{ isDark ? "dark theme" : "light theme" }}
            </span>
          </div>
          <div
            :style="quoteStyle.enabled ? {
              borderLeft: `6px solid ${quoteStyle.border_color}`,
              backgroundColor: isDark
                ? quoteStyle.dark_background_color
                : quoteStyle.background_color,
              color: isDark ? '#dadada' : '#085294',
              borderRadius: '4px',
              padding: '0.5em 1em',
            } : { borderLeft: '6px solid #e5e5e5', borderRadius: '4px', padding: '0.5em 1em' }"
          >
            <p class="text-sm">This is a sample blockquote — it will appear with your chosen colors.</p>
            <p class="text-sm mt-2" style="margin-bottom: 0">Quote styling adds visual emphasis to important information.</p>
          </div>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-3">
        <button
          @click="saveQuoteStyle"
          :disabled="quoteSaving"
          class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
        >{{ quoteSaving ? 'Saving…' : 'Save Quote Style' }}</button>
        <span v-if="quoteSaveMsg" class="text-sm" :class="quoteSaveOk ? 'text-green-500' : 'text-red-500'">{{ quoteSaveMsg }}</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import {
  getTableStyle, saveTableStyle as apiSaveTableStyle,
  getQuoteStyle, saveQuoteStyle as apiSaveQuoteStyle,
} from "../api.js";
import { loadTableStyle, loadQuoteStyle } from "../appearanceStore.js";

// ── Reactive dark-mode detection ──────────────────────────────────────────────
const isDark = ref(document.body.classList.contains("dark"));
let _themeObserver = null;

// ── Table Style ───────────────────────────────────────────────────────────────
const tableStyle = ref({
  header_color: "#085294",
  zebra_striping: true,
  enabled: true,
});
const tableSaving = ref(false);
const tableSaveMsg = ref("");
const tableSaveOk = ref(true);

async function loadTableStyleSettings() {
  try {
    const data = await getTableStyle();
    tableStyle.value = data;
  } catch {
    // Keep defaults
  }
}

async function saveTableStyle() {
  tableSaving.value = true;
  tableSaveMsg.value = "";
  try {
    await apiSaveTableStyle(tableStyle.value);
    await loadTableStyle(true);
    tableSaveOk.value = true;
    tableSaveMsg.value = "Saved ✓";
  } catch {
    tableSaveOk.value = false;
    tableSaveMsg.value = "Save failed";
  } finally {
    tableSaving.value = false;
    setTimeout(() => { tableSaveMsg.value = ""; }, 3000);
  }
}

// ── Quote Style ───────────────────────────────────────────────────────────────
const quoteStyle = ref({
  border_color: "#006633",
  background_color: "#f9f9f9",
  dark_background_color: "rgba(0, 102, 51, 0.17)",
  enabled: true,
});
const quoteSaving = ref(false);
const quoteSaveMsg = ref("");
const quoteSaveOk = ref(true);

// dark_background_color is stored as "rgba(r, g, b, a)" for CSS compatibility.
// The UI decomposes it into a 6-char hex + 0–100 opacity for the color picker.
function parseDarkBg() {
  const val = quoteStyle.value.dark_background_color || "rgba(0,102,51,0.17)";
  const m = val.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (m) {
    const r = parseInt(m[1]).toString(16).padStart(2, "0");
    const g = parseInt(m[2]).toString(16).padStart(2, "0");
    const b = parseInt(m[3]).toString(16).padStart(2, "0");
    const a = m[4] !== undefined ? Math.round(parseFloat(m[4]) * 100) : 100;
    return { hex: `#${r}${g}${b}`, opacity: a };
  }
  return { hex: val.startsWith("#") ? val.slice(0, 7) : "#006633", opacity: 17 };
}

function buildDarkBg(hex, opacityPct) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  const a = Math.round(opacityPct) / 100;
  return `rgba(${r}, ${g}, ${b}, ${a.toFixed(2)})`;
}

const darkBgHex = computed({
  get() { return parseDarkBg().hex; },
  set(hex) {
    const { opacity } = parseDarkBg();
    quoteStyle.value.dark_background_color = buildDarkBg(hex, opacity);
  },
});
const darkBgOpacity = computed({
  get() { return parseDarkBg().opacity; },
  set(pct) {
    const { hex } = parseDarkBg();
    quoteStyle.value.dark_background_color = buildDarkBg(hex, pct);
  },
});

async function loadQuoteStyleSettings() {
  try {
    const data = await getQuoteStyle();
    quoteStyle.value = data;
  } catch {
    // Keep defaults
  }
}

async function saveQuoteStyle() {
  quoteSaving.value = true;
  quoteSaveMsg.value = "";
  try {
    await apiSaveQuoteStyle(quoteStyle.value);
    await loadQuoteStyle(true);
    quoteSaveOk.value = true;
    quoteSaveMsg.value = "Saved ✓";
  } catch {
    quoteSaveOk.value = false;
    quoteSaveMsg.value = "Save failed";
  } finally {
    quoteSaving.value = false;
    setTimeout(() => { quoteSaveMsg.value = ""; }, 3000);
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  _themeObserver = new MutationObserver(() => {
    isDark.value = document.body.classList.contains("dark");
  });
  _themeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] });

  await loadTableStyleSettings();
  await loadQuoteStyleSettings();
});

onUnmounted(() => {
  if (_themeObserver) _themeObserver.disconnect();
});
</script>
