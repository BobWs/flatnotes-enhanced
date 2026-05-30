<template>
  <div>
    <h3 class="text-lg font-medium text-theme-text mb-1">Callout Styling</h3>
    <div class="flex flex-wrap items-start justify-between gap-2 mb-4">
      <p class="text-sm text-theme-text-muted flex-1 min-w-0">
        Define your callout types. Built-in types can be recolored but not deleted.
        Use <code class="bg-theme-background-elevated px-1 rounded text-xs">&gt; [!type] Title</code> in notes.
      </p>
      <button
        @click="addCallout"
        class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
               bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
        Add callout
      </button>
    </div>

    <!-- Callout list — scrollable locked frame -->
    <div class="border border-theme-border rounded-lg overflow-hidden mb-3">
      <div class="overflow-y-auto" style="max-height: 375px;">
        <div class="space-y-3 p-3">
          <div
            v-for="(c, i) in editableCallouts"
            :key="c._key"
            class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-lg border border-theme-border bg-theme-background"
          >
            <!-- Row 1 on mobile: preview chip + type name + delete -->
            <div class="flex items-center gap-2 sm:contents">
              <!-- Live preview chip -->
              <div
                class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold w-28"
                :style="previewStyle(c)"
              >
                <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current flex-shrink-0"><path :d="c.icon"/></svg>
                <span class="truncate">{{ c.label || c.type }}</span>
              </div>

              <!-- Type name -->
              <input
                v-model="c.type"
                :disabled="c.builtin"
                placeholder="type"
                class="w-28 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1.5
                       outline-none focus:border-theme-brand text-theme-text disabled:opacity-50 disabled:cursor-not-allowed"
                @input="c.type = c.type.toLowerCase().replace(/[^a-z0-9-]/g, '')"
              />

              <!-- Delete/Status — pushed to right on mobile row 1 -->
              <div class="ml-auto sm:hidden w-8 shrink-0 flex justify-end">
                <button
                  v-if="!c.builtin"
                  @click="removeCallout(i)"
                  class="text-theme-text-muted hover:text-red-500 transition-colors p-1.5 rounded touch-manipulation"
                  title="Delete callout"
                >
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                  </svg>
                </button>
                <span v-else class="text-theme-text-very-muted" title="Built-in callout (cannot be deleted)">
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                    <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                  </svg>
                </span>
              </div>
            </div>

            <!-- Row 2 on mobile: label + color picker group + icon + delete (desktop) -->
            <div class="flex flex-wrap items-center gap-2 sm:contents">
              <!-- Label -->
              <input
                v-model="c.label"
                placeholder="Label"
                class="w-32 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1.5
                       outline-none focus:border-theme-brand text-theme-text"
              />

              <!-- Color picker group -->
              <div class="flex items-center gap-2 shrink-0">
                <input
                  type="color"
                  v-model="c.color"
                  class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
                  title="Pick color"
                />
                <input
                  v-model="c.color"
                  placeholder="#337AB7"
                  class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                         rounded px-2 py-1.5 outline-none focus:border-theme-brand text-theme-text uppercase"
                  @input="c.color = normalizeHex($event.target.value)"
                />
              </div>

              <!-- Icon button -->
              <button
                @click="openIconPicker(i)"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm border border-theme-border
                       bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text-muted shrink-0 w-20 justify-center touch-manipulation"
                title="Change icon"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path :d="c.icon"/></svg>
                <span>Icon</span>
              </button>

              <!-- Delete/Status — desktop only -->
              <div class="hidden sm:flex w-20 shrink-0 justify-end">
                <button
                  v-if="!c.builtin"
                  @click="removeCallout(i)"
                  class="text-theme-text-muted hover:text-red-500 transition-colors p-1.5 rounded touch-manipulation"
                  title="Delete callout"
                >
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                  </svg>
                </button>
                <span v-else class="text-theme-text-very-muted" title="Built-in callout (cannot be deleted)">
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                    <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                  </svg>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- /Callout list scrollable frame -->

    <!-- Save / status -->
    <div class="mt-5 flex items-center gap-3">
      <button
        @click="saveCallouts"
        :disabled="calloutsaving"
        class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
               text-white transition-colors disabled:opacity-50 touch-manipulation"
      >
        {{ calloutsaving ? 'Saving…' : 'Save callouts' }}
      </button>
      <span v-if="calloutSaveMsg" class="text-sm" :class="calloutSaveOk ? 'text-green-500' : 'text-red-500'">
        {{ calloutSaveMsg }}
      </span>
    </div>

    <!-- ── Icon picker modal ──────────────────────────────────────────────── -->
    <div
      v-if="iconPickerOpen"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="iconPickerOpen = false"
    >
      <div class="bg-theme-background rounded-t-2xl sm:rounded-xl border border-theme-border shadow-xl
                  w-full sm:w-[480px] max-h-[85vh] sm:max-h-[70vh] flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border shrink-0">
          <span class="font-semibold text-theme-text">Choose icon</span>
          <button @click="iconPickerOpen = false"
                  class="text-theme-text-muted hover:text-theme-text p-1 touch-manipulation">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
          </button>
        </div>
        <div class="px-3 py-2 border-b border-theme-border shrink-0">
          <input v-model="iconSearch" placeholder="Search icons…"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-1.5
                   outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted"/>
        </div>
        <div class="overflow-y-auto p-3 grid grid-cols-6 sm:grid-cols-8 gap-1">
          <button
            v-for="icon in filteredIcons"
            :key="icon.name"
            @click="pickIcon(icon)"
            class="flex flex-col items-center justify-center p-2 rounded hover:bg-theme-background-elevated
                   active:bg-theme-background-elevated transition-colors group touch-manipulation"
            :title="icon.name"
          >
            <svg viewBox="0 0 24 24" class="w-6 h-6 sm:w-5 sm:h-5 fill-current text-theme-text-muted group-hover:text-theme-text">
              <path :d="icon.path"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getCallouts, saveCallouts as apiSaveCallouts } from "../api.js";
import { loadCallouts, hexToRgb } from "../calloutStore.js";
import { ICON_LIBRARY, searchIcons } from "../IconLibrary.js";

// ── Callout state ─────────────────────────────────────────────────────────────
const editableCallouts = ref([]);
let _keyCounter = 0;
const calloutsaving = ref(false);
const calloutSaveMsg = ref("");
const calloutSaveOk = ref(true);

// ── Icon picker state ─────────────────────────────────────────────────────────
const iconPickerOpen = ref(false);
const iconSearch = ref("");
let pickerTargetIndex = -1;

const filteredIcons = computed(() => searchIcons(iconSearch.value));

// ── Helpers ───────────────────────────────────────────────────────────────────
function previewStyle(c) {
  const rgb = hexToRgb(c.color || "#82D0D8");
  return {
    backgroundColor: `rgba(${rgb}, 0.12)`,
    color: c.color || "#82D0D8",
    borderLeft: `4px solid ${c.color || "#82D0D8"}`,
  };
}

function normalizeHex(val) {
  if (!val.startsWith("#")) val = "#" + val;
  return val.length <= 7 ? val : val.slice(0, 7);
}

// ── Callout CRUD ──────────────────────────────────────────────────────────────
function addCallout() {
  editableCallouts.value.push({
    _key: _keyCounter++,
    type: "custom",
    label: "Custom",
    color: "#82D0D8",
    icon: ICON_LIBRARY[0].path,
    builtin: false,
  });
}

function removeCallout(i) {
  editableCallouts.value.splice(i, 1);
}

async function saveCallouts() {
  calloutsaving.value = true;
  calloutSaveMsg.value = "";
  try {
    const payload = editableCallouts.value.map(({ _key, ...rest }) => rest);
    await apiSaveCallouts(payload);
    await loadCallouts(true);
    calloutSaveOk.value = true;
    calloutSaveMsg.value = "Saved ✓";
  } catch {
    calloutSaveOk.value = false;
    calloutSaveMsg.value = "Save failed";
  } finally {
    calloutsaving.value = false;
    setTimeout(() => { calloutSaveMsg.value = ""; }, 3000);
  }
}

// ── Icon picker ───────────────────────────────────────────────────────────────
function openIconPicker(index) {
  pickerTargetIndex = index;
  iconSearch.value = "";
  iconPickerOpen.value = true;
}

function pickIcon(icon) {
  if (pickerTargetIndex >= 0 && editableCallouts.value[pickerTargetIndex]) {
    editableCallouts.value[pickerTargetIndex].icon = icon.path;
  }
  iconPickerOpen.value = false;
}

// ── Load on mount ─────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const data = await getCallouts();
    editableCallouts.value = data.map(c => ({ ...c, _key: _keyCounter++ }));
  } catch {
    editableCallouts.value = [];
  }
});
</script>
