<template>
  <div>
    <h3 class="text-lg font-medium text-theme-text mb-1">Tag Colors</h3>
    <p class="text-sm text-theme-text-muted mb-4">
      Customise how tag chips look across the app — in notes, sidebars, and search results.
    </p>

    <!-- Global enable / disable toggle -->
    <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
      <div>
        <p class="text-sm font-medium text-theme-text">Enable custom tag colors</p>
        <p class="text-xs text-theme-text-muted mt-0.5">
          When disabled, all tags use the default color below.
        </p>
      </div>
      <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
        <input type="checkbox" v-model="tagColorsEnabled" class="sr-only peer" />
        <div class="w-11 h-6 bg-theme-border rounded-full peer
                    peer-checked:bg-theme-brand transition-colors
                    after:content-[''] after:absolute after:top-0.5 after:left-0.5
                    after:bg-white after:rounded-full after:h-5 after:w-5
                    after:transition-transform peer-checked:after:translate-x-5"></div>
      </label>
    </div>

    <!-- Default color (always shown) -->
    <div class="flex flex-wrap items-center gap-3 p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-theme-text">Default tag color</p>
        <p class="text-xs text-theme-text-muted mt-0.5">
          Used for all tags when custom colors are disabled, and as the fallback for unassigned tags.
        </p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <input
          type="color"
          v-model="tagDefaultColor"
          class="w-9 h-9 rounded cursor-pointer border border-theme-border bg-transparent"
          title="Pick default color"
        />
        <input
          v-model="tagDefaultColor"
          class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                 rounded px-2 py-1.5 outline-none focus:border-theme-brand text-theme-text uppercase"
          placeholder="#006633"
        />
        <!-- Live preview chip -->
        <span :style="tagColorPreviewStyle(tagDefaultColor)">
          <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current" style="display:inline-block">
            <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
          </svg>
          example
        </span>
      </div>
    </div>

    <!-- Per-tag overrides (only when custom colors enabled) -->
    <div v-if="tagColorsEnabled">
      <div class="flex items-center justify-between mb-3">
        <p class="text-sm font-medium text-theme-text">Per-tag color overrides</p>
        <button
          @click="addTagColorRow()"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs
                 bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
        >
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
            <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
          </svg>
          Add row
        </button>
      </div>

      <!-- Scrollable locked frame for color rows -->
      <div class="border border-theme-border rounded-lg overflow-hidden mb-3">
        <div class="overflow-y-auto" style="max-height: 370px;">

          <!-- Empty state -->
          <div v-if="editableTagColors.length === 0"
               class="px-4 py-6 text-center text-xs text-theme-text-very-muted">
            No custom tag colors yet. Click "Add row" or click a tag name below.
          </div>

          <!-- Tag color rows -->
          <div
            v-for="(row, i) in editableTagColors"
            :key="row._key"
            class="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-theme-border last:border-b-0
                   bg-theme-background hover:bg-theme-background-elevated/50 transition-colors"
          >
            <!-- Tag name input: # [parent] / [child] for nested tag support -->
            <div class="flex items-center gap-1 min-w-0">
              <span class="text-sm text-theme-text-very-muted shrink-0 select-none">#</span>
              <input
                :value="row.tag.includes('/') ? row.tag.split('/')[0] : row.tag"
                @input="(e) => {
                  const parent = e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '');
                  const child = row.tag.includes('/') ? row.tag.split('/').slice(1).join('/') : '';
                  row.tag = child ? parent + '/' + child : parent;
                }"
                placeholder="parent"
                title="Parent tag name"
                class="w-28 text-sm bg-theme-background-elevated border border-theme-border
                       rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text"
              />
              <span class="text-theme-text-very-muted shrink-0 select-none text-sm">/</span>
              <input
                :value="row.tag.includes('/') ? row.tag.split('/').slice(1).join('/') : ''"
                @input="(e) => {
                  const child = e.target.value.toLowerCase().replace(/[^a-z0-9_/-]/g, '');
                  const parent = row.tag.includes('/') ? row.tag.split('/')[0] : row.tag;
                  row.tag = child ? (parent || 'tag') + '/' + child : parent;
                }"
                placeholder="child"
                title="Child tag name (optional — leave empty for top-level tag)"
                class="w-28 text-sm bg-theme-background-elevated border border-theme-border
                       rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text"
              />
            </div>

            <!-- Color picker -->
            <input
              type="color"
              v-model="row.color"
              class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
            />
            <input
              v-model="row.color"
              class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                     rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
            />

            <!-- Live preview chip -->
            <span :style="tagColorPreviewStyle(row.color)" class="shrink-0">
              <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current" style="display:inline-block">
                <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
              </svg>
              {{ (row.tag || "example").split("/").join(" › ") }}
            </span>

            <!-- Enabled toggle -->
            <label class="relative inline-flex items-center cursor-pointer shrink-0 ml-auto" title="Enable this tag color">
              <input type="checkbox" v-model="row.enabled" class="sr-only peer" />
              <div class="w-9 h-5 bg-theme-border rounded-full peer
                          peer-checked:bg-theme-brand transition-colors
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-4 after:w-4
                          after:transition-transform peer-checked:after:translate-x-4"></div>
            </label>

            <!-- Delete -->
            <button
              @click="removeTagColorRow(i)"
              class="text-theme-text-muted hover:text-red-500 transition-colors p-1 rounded shrink-0 touch-manipulation"
              title="Remove"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Your tags frame -->
      <div v-if="allTagsList.length > 0" class="border border-theme-border rounded-lg overflow-hidden mb-3">
        <div class="px-3 py-2 bg-theme-background-elevated border-b border-theme-border">
          <span class="text-xs font-medium text-theme-text-very-muted">Your tags — click to add a color override:</span>
        </div>
        <div class="overflow-y-auto" style="max-height: 120px;">
          <div class="px-3 py-2 flex flex-wrap gap-1">
            <button
              v-for="item in allTagsList"
              :key="item.tag"
              @click="addTagFromList(item.tag)"
              class="text-xs px-1.5 py-0.5 rounded-full border border-theme-border
                     bg-theme-background hover:bg-theme-background-elevated active:bg-theme-background-elevated
                     transition-colors text-theme-text-muted touch-manipulation"
              :title="`Add override for #${item.tag} (${item.count} notes)`"
            >
              #{{ item.tag }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Save button -->
    <div class="flex items-center gap-3 mt-2">
      <button
        @click="saveTagColors"
        :disabled="tagColorsSaving"
        class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand
               text-white transition-colors disabled:opacity-50 touch-manipulation"
      >{{ tagColorsSaving ? "Saving…" : "Save Tag Colors" }}</button>
      <span
        v-if="tagColorsSaveMsg"
        class="text-sm"
        :class="tagColorsSaveOk ? 'text-green-500' : 'text-red-500'"
      >{{ tagColorsSaveMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getTagColors as apiGetTagColors, saveTagColors as apiSaveTagColors, getTags } from "../api.js";
import { loadTagColors } from "../tagColorStore.js";

// ── State ─────────────────────────────────────────────────────────────────────
const tagColorsEnabled = ref(false);
const tagDefaultColor = ref("#006633");
const editableTagColors = ref([]);
let _tagKeyCounter = 0;
const tagColorsSaving = ref(false);
const tagColorsSaveMsg = ref("");
const tagColorsSaveOk = ref(true);
const allTagsList = ref([]);

// ── Helpers ───────────────────────────────────────────────────────────────────
function tagColorPreviewStyle(color) {
  const hex = color || tagDefaultColor.value || "#006633";
  return {
    backgroundColor: hexToLightBg(hex),
    color: hex,
    border: `1px solid ${hex}44`,
    borderRadius: "9999px",
    padding: "0 0.5rem",
    fontSize: "0.8rem",
    fontWeight: "500",
    display: "inline-flex",
    alignItems: "center",
    gap: "0.25rem",
    lineHeight: "1.6",
  };
}

function hexToLightBg(hex) {
  try {
    const clean = hex.replace("#", "");
    const r = parseInt(clean.substring(0, 2), 16) / 255;
    const g = parseInt(clean.substring(2, 4), 16) / 255;
    const b = parseInt(clean.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const d = max - min;
    let h = 0, s = 0;
    if (d) {
      s = (max + min) > 1 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }
    return `hsl(${Math.round(h * 360)}, ${Math.round(s * 100)}%, 92%)`;
  } catch {
    return "#f0f0f0";
  }
}

// ── Tag color CRUD ────────────────────────────────────────────────────────────
function addTagColorRow(tag = "", color = "") {
  editableTagColors.value.push({
    _key: _tagKeyCounter++,
    tag,
    color: color || tagDefaultColor.value || "#006633",
    enabled: true,
  });
}

function removeTagColorRow(i) {
  editableTagColors.value.splice(i, 1);
}

function addTagFromList(tag) {
  const exists = editableTagColors.value.some(
    t => t.tag.toLowerCase() === tag.toLowerCase()
  );
  if (!exists) {
    addTagColorRow(tag);
  }
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadTagColorSettings() {
  try {
    const data = await apiGetTagColors();
    tagColorsEnabled.value = data.custom_colors_enabled ?? false;
    tagDefaultColor.value = data.default_color ?? "#006633";
    editableTagColors.value = (data.tag_colors || []).map(t => ({
      ...t,
      _key: _tagKeyCounter++,
    }));
  } catch {
    tagColorsEnabled.value = false;
    tagDefaultColor.value = "#006633";
    editableTagColors.value = [];
  }
}

async function loadAllTagsList() {
  try {
    const data = await getTags();
    allTagsList.value = Object.entries(data)
      .filter(([t]) => t !== "pin")
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => a.tag.localeCompare(b.tag));
  } catch {
    allTagsList.value = [];
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveTagColors() {
  tagColorsSaving.value = true;
  tagColorsSaveMsg.value = "";
  try {
    const payload = {
      custom_colors_enabled: tagColorsEnabled.value,
      default_color: tagDefaultColor.value,
      tag_colors: editableTagColors.value
        .filter(t => t.tag.trim())
        .map(({ _key, ...rest }) => ({ ...rest, tag: rest.tag.trim() })),
    };
    await apiSaveTagColors(payload);
    await loadTagColors(true);
    tagColorsSaveOk.value = true;
    tagColorsSaveMsg.value = "Saved ✓";
  } catch {
    tagColorsSaveOk.value = false;
    tagColorsSaveMsg.value = "Save failed";
  } finally {
    tagColorsSaving.value = false;
    setTimeout(() => { tagColorsSaveMsg.value = ""; }, 3000);
  }
}

onMounted(async () => {
  await loadTagColorSettings();
  await loadAllTagsList();
});
</script>
