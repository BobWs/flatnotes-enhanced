<template>
  <div class="relative w-full">
    <!-- Input -->
    <div
      class="flex w-full rounded-md border border-theme-border bg-theme-background dark:bg-theme-background-elevated"
      :class="{ 'px-3 py-2': !large, 'px-5 py-4': large }"
    >
      <IconLabel :iconPath="mdilMagnify" class="mr-2 shrink-0" />
      <input
        type="text"
        ref="input"
        v-model="searchTerm"
        v-focus
        class="w-full bg-transparent focus:outline-none"
        :placeholder="placeholder"
        @keydown="keydownHandler"
        @keyup="stateChangeHandler"
        @click="stateChangeHandler"
        @blur="tagMenuVisible = false"
        @keydown.down.prevent
        @keydown.up.prevent
      />
      <!-- Clear button — only visible when there's text -->
      <button
        v-if="searchTerm"
        @click="clearSearch"
        class="shrink-0 ml-1 text-theme-text-muted hover:text-theme-text transition-colors"
        title="Clear search"
        tabindex="-1"
      >
        <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
          <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
        </svg>
      </button>
    </div>

    <!-- Tag Menu -->
    <div
      v-if="tagMenuVisible"
      class="absolute z-10 mt-2 max-h-64 w-full overflow-scroll rounded-md border border-theme-border bg-theme-background p-1"
    >
      <p
        v-for="(tag, index) in tagMatches"
        ref="tagMenuItems"
        class="cursor-pointer rounded px-2 py-1 hover:bg-theme-background-elevated flex items-center gap-2"
        :class="{ 'bg-theme-background-elevated': index === tagMenuIndex }"
        @click="tagChosen(tag)"
        @mousedown.prevent
      >
        <!-- Colored dot for visual distinction -->
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :style="{ backgroundColor: tagToColor(tag) }"
        ></span>
        {{ tag.replace(/^#/, "") }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { mdilMagnify } from "@mdi/light-js";
import { useToast } from "primevue/usetoast";
import { ref, watch } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getTags } from "../api.js";
import { tagColor } from "../tagColor.js";
import IconLabel from "../components/IconLabel.vue";
import * as constants from "../constants.js";
import { getToastOptions } from "../helpers.js";

const props = defineProps({
  initialSearchTerm: { type: String, default: "" },
  large: Boolean,
  placeholder: { type: String, default: "Search..." },
});
const emit = defineEmits(["search"]);

const input = ref();
const router = useRouter();
const searchTerm = ref(props.initialSearchTerm);
const toast = useToast();
let tags = null;
const tagMatches = ref([]);
const tagMenuItems = ref([]);
const tagMenuIndex = ref(0);
const tagMenuVisible = ref(false);

function clearSearch() {
  searchTerm.value = "";
  tagMenuVisible.value = false;
  input.value?.focus();
}

function keydownHandler(event) {
  if (tagMenuVisible.value) {
    if (event.key === "ArrowDown") {
      tagMenuIndex.value = Math.min(tagMenuIndex.value + 1, tagMatches.value.length - 1);
      tagMenuItems.value[tagMenuIndex.value].scrollIntoView({ block: "nearest" });
    } else if (event.key === "ArrowUp") {
      tagMenuIndex.value = Math.max(tagMenuIndex.value - 1, 0);
      tagMenuItems.value[tagMenuIndex.value].scrollIntoView({ block: "nearest" });
    } else if (event.key === "Enter") {
      tagChosen(tagMatches.value[tagMenuIndex.value]);
    } else if (event.key === "Escape") {
      tagMenuVisible.value = false;
      event.stopPropagation();
    }
  } else if (event.key === "Enter") {
    search();
  }
}

function tagChosen(tag) {
  replaceWordOnCursor(tag);
  tagMenuVisible.value = false;
}

function search() {
  if (searchTerm.value) {
    router.push({
      name: "search",
      query: { [constants.params.searchTerm]: searchTerm.value },
    });
    emit("search");
  } else {
    toast.add(getToastOptions("Please enter a search term.", "Error", "error"));
  }
}

function stateChangeHandler() {
  const wordOnCursor = getWordOnCursor();
  if (wordOnCursor.charAt(0) !== "#") {
    tagMenuVisible.value = false;
    tagMatches.value = [];
  } else {
    filterTagMatches(wordOnCursor.toLowerCase());
  }
}

async function filterTagMatches(inputWord) {
  if (tags === null) {
    try {
      // getTags() now returns a {tag: count} dict — extract keys
      const data = await getTags();
      tags = Object.keys(data).map((t) => `#${t}`).sort();
    } catch (error) {
      tags = [];
      apiErrorHandler(error, toast);
    }
  }
  const prev = tagMatches.value.length;
  tagMatches.value = tags.filter((t) => t.startsWith(inputWord) && t !== inputWord);
  if (prev !== tagMatches.value.length && tagMatches.value.length > 0) {
    tagMenuIndex.value = 0;
    tagMenuVisible.value = true;
  } else if (tagMatches.value.length === 0) {
    tagMenuVisible.value = false;
  }
}

/** Delegate to shared tag color utility */
function tagToColor(tag) {
  return tagColor(tag.replace(/^#/, ""));
}

function getWordOnCursorPosition() {
  const cursorPosition = input.value.selectionStart;
  const wordStart = Math.max(searchTerm.value.lastIndexOf(" ", cursorPosition - 1) + 1, 0);
  let wordEnd = searchTerm.value.indexOf(" ", cursorPosition);
  if (wordEnd === -1) wordEnd = searchTerm.value.length;
  return { start: wordStart, end: wordEnd };
}

function getWordOnCursor() {
  const { start, end } = getWordOnCursorPosition();
  return searchTerm.value.substring(start, end);
}

function replaceWordOnCursor(replacement) {
  const { start, end } = getWordOnCursorPosition();
  searchTerm.value = searchTerm.value.substring(0, start) + replacement + searchTerm.value.substring(end);
}

watch(() => props.initialSearchTerm, () => {
  searchTerm.value = props.initialSearchTerm;
});
</script>
