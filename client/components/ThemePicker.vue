<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="close"
    >
      <div
        ref="panelEl"
        role="dialog"
        aria-modal="true"
        aria-label="Theme picker"
        class="flex max-h-[80vh] w-full flex-col rounded-t-2xl border border-theme-border
               bg-theme-background shadow-xl sm:w-[380px] sm:max-w-full sm:rounded-xl"
      >
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-theme-border px-4 py-3">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 fill-current text-theme-brand">
              <path :d="mdiPalette" />
            </svg>
            <h3 class="text-base font-semibold text-theme-text">Theme</h3>
          </div>
          <button
            ref="closeButtonEl"
            @click="close"
            title="Close"
            aria-label="Close theme picker"
            class="rounded p-1 text-theme-text-muted transition-colors hover:text-theme-text touch-manipulation"
          >
            <svg viewBox="0 0 24 24" class="h-5 w-5 fill-current">
              <path :d="mdiClose" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-2 py-2" role="listbox" aria-label="Available themes">
          <div v-for="group in groups" :key="group.label" class="mb-2 last:mb-0">
            <p class="px-2 pb-1 pt-2 text-xs font-bold uppercase tracking-wide text-theme-text-very-muted">
              {{ group.label }}
            </p>
            <button
              v-for="theme in group.themes"
              :key="theme.id"
              type="button"
              role="option"
              :aria-selected="theme.id === activeId"
              :class="[
                'theme-picker-item flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors touch-manipulation',
                theme.id === activeId
                  ? 'bg-theme-background-elevated text-theme-text'
                  : 'text-theme-text-muted hover:bg-theme-background-elevated hover:text-theme-text',
              ]"
              @click="choose(theme.id)"
            >
              <!-- Swatch: nested background / elevated squares + brand dot.
                   Only "System" has no fixed colors (see themes.js); it
                   falls back to an icon instead. -->
              <span
                v-if="theme.colors"
                class="relative inline-block h-6 w-6 shrink-0 overflow-hidden rounded-full border border-theme-border"
                :style="{ backgroundColor: `rgb(${theme.colors.background})` }"
              >
                <span
                  class="absolute inset-y-0 right-0 w-1/2"
                  :style="{ backgroundColor: `rgb(${theme.colors.backgroundElevated})` }"
                />
                <span
                  class="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border border-white/50"
                  :style="{ backgroundColor: `rgb(${theme.colors.brand})` }"
                />
              </span>
              <span
                v-else
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-theme-border"
              >
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 fill-current">
                  <path :d="mdiMonitor" />
                </svg>
              </span>

              <span class="min-w-0 flex-1 truncate text-sm">{{ theme.label }}</span>

              <svg
                v-if="theme.id === activeId"
                viewBox="0 0 24 24"
                class="h-4 w-4 shrink-0 fill-current text-theme-brand"
              >
                <path :d="mdiCheck" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { mdiCheck, mdiClose, mdiMonitor, mdiPalette } from "@mdi/js";
import { computed, nextTick, ref, watch } from "vue";

import { getAvailableThemes, getCurrentTheme, setTheme } from "../helpers.js";

const visible = defineModel({ type: Boolean });

const panelEl = ref(null);
const closeButtonEl = ref(null);
const activeId = ref(getCurrentTheme());

const { default: defaultThemes, colors: colorThemes } = getAvailableThemes();

// Color themes grouped by family (Dracula, Catppuccin, ...) so the list of
// 16+ entries stays scannable rather than one long flat list.
const colorGroups = computed(() => {
  const byFamily = new Map();
  for (const theme of colorThemes) {
    if (!byFamily.has(theme.family)) byFamily.set(theme.family, []);
    byFamily.get(theme.family).push(theme);
  }
  return Array.from(byFamily, ([label, themes]) => ({ label, themes }));
});

const groups = computed(() => [{ label: "Default", themes: defaultThemes }, ...colorGroups.value]);

function choose(id) {
  setTheme(id);
  activeId.value = id;
}

function close() {
  visible.value = false;
}

function onKeydown(event) {
  if (event.key === "Escape") {
    close();
    return;
  }
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const items = Array.from(panelEl.value?.querySelectorAll(".theme-picker-item") || []);
    if (!items.length) return;
    const currentIndex = items.indexOf(document.activeElement);
    const delta = event.key === "ArrowDown" ? 1 : -1;
    const nextIndex = currentIndex === -1 ? 0 : (currentIndex + delta + items.length) % items.length;
    items[nextIndex].focus();
  }
}

watch(visible, (isVisible) => {
  if (isVisible) {
    activeId.value = getCurrentTheme();
    window.addEventListener("keydown", onKeydown);
    nextTick(() => closeButtonEl.value?.focus());
  } else {
    window.removeEventListener("keydown", onKeydown);
  }
});
</script>
