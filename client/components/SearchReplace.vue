<template>
  <div v-if="isVisible" class="flex flex-wrap items-center gap-1 px-2 py-1.5 border-b border-theme-border bg-theme-background-elevated text-sm">
    <!-- Search -->
    <input
      ref="searchInputRef"
      v-model="searchText"
      @keydown.enter="findNext"
      @keydown.escape="close"
      placeholder="Search..."
      class="w-36 bg-theme-background border border-theme-border rounded px-2 py-0.5 outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted text-xs"
    />
    <!-- Replace -->
    <input
      v-model="replaceText"
      @keydown.enter="replaceNext"
      @keydown.escape="close"
      placeholder="Replace..."
      class="w-36 bg-theme-background border border-theme-border rounded px-2 py-0.5 outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted text-xs"
    />
    <!-- Match count -->
    <span class="text-xs text-theme-text-muted min-w-[4rem]">
      {{ matchInfo }}
    </span>
    <!-- Buttons -->
    <button @click="findNext" class="sr-btn" title="Find next (Enter)">Next</button>
    <button @click="findPrev" class="sr-btn" title="Find previous">Prev</button>
    <button @click="replaceNext" class="sr-btn" title="Replace next">Replace</button>
    <button @click="replaceAll" class="sr-btn" title="Replace all">All</button>
    <!-- Case sensitive toggle -->
    <button
      @click="caseSensitive = !caseSensitive"
      :class="['sr-btn', caseSensitive ? 'sr-btn-active' : '']"
      title="Toggle case sensitive"
    >Aa</button>
    <!-- Close -->
    <button @click="close" class="ml-auto text-theme-text-muted hover:text-theme-text" title="Close (Escape)">
      <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
        <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from "vue";

const props = defineProps({
  isVisible: Boolean,
  getEditorContent: Function,
  setEditorContent: Function,
  getEditorMode: Function, // returns 'markdown' or 'wysiwyg'
});

const emit = defineEmits(["close", "update:isVisible"]);

const searchText = ref("");
const replaceText = ref("");
const caseSensitive = ref(false);
const currentMatchIndex = ref(-1);
const allMatches = ref([]);
const searchInputRef = ref();

const matchInfo = computed(() => {
  if (!searchText.value) return "";
  if (allMatches.value.length === 0) return "No matches";
  return `${currentMatchIndex.value + 1} / ${allMatches.value.length}`;
});

watch(() => props.isVisible, (val) => {
  if (val) {
    nextTick(() => searchInputRef.value?.focus());
  }
});

watch([searchText, caseSensitive], () => {
  findAllMatches();
});

function getContent() {
  return props.getEditorContent ? props.getEditorContent() : "";
}

function setContent(content) {
  if (props.setEditorContent) props.setEditorContent(content);
}

function findAllMatches() {
  const content = getContent();
  if (!searchText.value || !content) {
    allMatches.value = [];
    currentMatchIndex.value = -1;
    return;
  }
  const flags = caseSensitive.value ? "g" : "gi";
  const re = new RegExp(escapeRegex(searchText.value), flags);
  const matches = [];
  let m;
  while ((m = re.exec(content)) !== null) {
    matches.push({ index: m.index, length: m[0].length });
  }
  allMatches.value = matches;
  currentMatchIndex.value = matches.length > 0 ? 0 : -1;
}

function findNext() {
  findAllMatches();
  if (allMatches.value.length === 0) return;
  currentMatchIndex.value = (currentMatchIndex.value + 1) % allMatches.value.length;
}

function findPrev() {
  findAllMatches();
  if (allMatches.value.length === 0) return;
  currentMatchIndex.value =
    (currentMatchIndex.value - 1 + allMatches.value.length) % allMatches.value.length;
}

function replaceNext() {
  findAllMatches();
  if (allMatches.value.length === 0 || currentMatchIndex.value === -1) return;
  const content = getContent();
  const match = allMatches.value[currentMatchIndex.value];
  const newContent =
    content.slice(0, match.index) +
    replaceText.value +
    content.slice(match.index + match.length);
  setContent(newContent);
  findAllMatches();
}

function replaceAll() {
  const content = getContent();
  if (!searchText.value || !content) return;
  const flags = caseSensitive.value ? "g" : "gi";
  const re = new RegExp(escapeRegex(searchText.value), flags);
  const newContent = content.replace(re, replaceText.value);
  setContent(newContent);
  findAllMatches();
}

function close() {
  emit("close");
  emit("update:isVisible", false);
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
</script>

<style scoped>
.sr-btn {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid rgb(var(--theme-border));
  background-color: rgb(var(--theme-background));
  color: rgb(var(--theme-text));
  transition: background-color 0.15s;
  cursor: pointer;
}
.sr-btn:hover {
  background-color: rgb(var(--theme-background-elevated));
}
.sr-btn-active {
  background-color: rgb(var(--theme-brand));
  color: white;
  border-color: rgb(var(--theme-brand));
}
</style>