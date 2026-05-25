<template>
  <!-- Mobile overlay -->
  <div
    v-if="isOpen"
    class="fixed inset-0 z-30 bg-black/40 md:hidden"
    @click="$emit('close')"
  ></div>

  <!-- Sidebar panel -->
  <aside
    :class="[
      'fixed top-0 left-0 z-40 h-full w-72 flex flex-col',
      'bg-theme-background border-r border-theme-border',
      'transition-transform duration-300 ease-in-out',
      isOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <!-- Header: title + refresh + expand/collapse + close -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border shrink-0">
      <span class="text-xs font-bold uppercase text-theme-text-very-muted tracking-wider">Tags</span>
      <div class="flex items-center gap-1">
        <!-- Expand / Collapse all button -->
        <button
          @click="toggleExpandAll"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :title="lastExpandDirection === true ? 'Collapse all' : 'Expand all'"
        >
          <svg v-if="lastExpandDirection !== true" viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M13,14L18,9L16.6,7.6L13,11.2L9.4,7.6L8,9L13,14Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M8,11L13,6L18,11L16.6,12.4L13,8.8L9.4,12.4L8,11Z"/>
          </svg>
        </button>
        <!-- Refresh button -->
        <button
          @click="loadTags"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :class="{ 'animate-spin': loading }"
          title="Refresh tags"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
        </button>
        <!-- Close button -->
        <button
          @click="$emit('close')"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          title="Close sidebar"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Search filter with clear button -->
    <div class="px-3 py-2 border-b border-theme-border shrink-0">
      <div class="relative">
        <input
          v-model="filterText"
          type="text"
          placeholder="Filter tags..."
          class="w-full text-sm bg-theme-background-elevated rounded px-3 py-1.5 pr-8 outline-none border border-theme-border focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted"
        />
        <!-- Clear (X) button — only visible when filter has text -->
        <button
          v-if="filterText"
          @click="filterText = ''"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-theme-text-muted hover:text-theme-text transition-colors"
          title="Clear filter"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Active filters indicator -->
    <div
      v-if="activeTags.length > 0"
      class="px-3 py-2 border-b border-theme-border shrink-0 flex items-center justify-between"
    >
      <span class="text-xs text-theme-brand font-semibold">
        {{ activeTags.length }} tag{{ activeTags.length > 1 ? 's' : '' }} active
      </span>
      <button
        @click="clearActiveTags"
        class="text-xs text-theme-text-muted hover:text-theme-text transition-colors"
      >Clear all</button>
    </div>

    <!-- Tag list -->
    <div class="flex-1 overflow-y-auto px-2 py-2">
      <div v-if="loading" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        Loading tags...
      </div>
      <div v-else-if="Object.keys(filteredTagCounts).length === 0" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        No tags found
      </div>
      <div v-else-if="filteredTagGroups.length === 0 && filterText" class="text-xs text-theme-text-very-muted px-2 py-2">
        No tags match "{{ filterText }}"
      </div>
      <TagSidebarItem
        v-for="group in filteredTagGroups"
        :key="group.fullPath"
        :group="group"
        :activeTags="activeTags"
        :forceExpand="expandAll"
        @toggle="toggleTag"
      />
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { getTags } from "../api.js";
import TagSidebarItem from "./TagSidebarItem.vue";

const props = defineProps({
  isOpen: Boolean,
});

const emit = defineEmits(["close", "tagsChanged"]);

const loading = ref(false);
const tagCounts = ref({});
const filterText = ref("");
const activeTags = ref([]);
// null = no override, true = expand all, false = collapse all
const expandAll = ref(null);
// Tracks which direction was last bulk-applied so the button icon/title
// stays correct after expandAll resets to null (the one-tick pulse approach).
const lastExpandDirection = ref(null);

// Filter out the "pin" tag from tagCounts
const filteredTagCounts = computed(() => {
  const { pin, ...rest } = tagCounts.value;
  return rest;
});

onMounted(() => {
  const saved = localStorage.getItem("fn_active_tags");
  if (saved) {
    try { activeTags.value = JSON.parse(saved); } catch {}
  }
  loadTags();
});

// Build a nested tree from the flat {tag: count} dict
const tagGroups = computed(() => {
  const root = [];
  const map = {};
  const sorted = Object.keys(filteredTagCounts.value).sort();

  for (const tag of sorted) {
    const parts = tag.split("/");
    let path = "";

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      path = path ? `${path}/${part}` : part;

      if (!map[path]) {
        const nodeCount = filteredTagCounts.value[path] || 0;
        const node = { name: part, fullPath: path, count: nodeCount, children: [] };
        map[path] = node;

        if (i === 0) {
          root.push(node);
        } else {
          const parentPath = parts.slice(0, i).join("/");
          if (map[parentPath]) {
            map[parentPath].children.push(node);
          }
        }
      }
    }
  }
  return root;
});

const filteredTagGroups = computed(() => {
  if (!filterText.value) return tagGroups.value;
  const q = filterText.value.toLowerCase();
  return deepFilter(tagGroups.value, q);
});

function deepFilter(groups, q) {
  return groups
    .map((g) => {
      const match = g.name.toLowerCase().includes(q) || g.fullPath.toLowerCase().includes(q);
      const filteredChildren = deepFilter(g.children, q);
      if (match || filteredChildren.length > 0) {
        return { ...g, children: filteredChildren };
      }
      return null;
    })
    .filter(Boolean);
}

function toggleTag(tagPath) {
  if (activeTags.value.length === 1 && activeTags.value[0] === tagPath) {
    activeTags.value = [];
  } else {
    activeTags.value = [tagPath];
  }
  localStorage.setItem("fn_active_tags", JSON.stringify(activeTags.value));
  emit("tagsChanged", activeTags.value);
  // Auto-close sidebar on mobile (below md breakpoint = 768px)
  if (window.innerWidth < 768) {
    emit("close");
  }
}

function toggleExpandAll() {
  // Set expandAll for exactly one tick (pulse). Because all TagSidebarItem
  // children are mounted via v-show (not v-if), every watcher at every depth
  // fires in the same tick and syncs localExpanded. nextTick then resets
  // expandAll to null so individual chevron clicks work freely afterwards.
  if (lastExpandDirection.value !== true) {
    expandAll.value = true;
    lastExpandDirection.value = true;
  } else {
    expandAll.value = false;
    lastExpandDirection.value = false;
  }
  nextTick(() => {
    expandAll.value = null;
  });
}

function clearActiveTags() {
  activeTags.value = [];
  localStorage.removeItem("fn_active_tags");
  emit("tagsChanged", []);
}

function loadTags() {
  loading.value = true;
  getTags()
    .then((data) => {
      if (Array.isArray(data)) {
        const d = {};
        data.forEach((t) => { d[t] = 1; });
        tagCounts.value = d;
      } else if (data && typeof data === "object") {
        tagCounts.value = { ...data };
      } else {
        tagCounts.value = {};
      }
      loading.value = false;
    })
    .catch((err) => {
      console.error("Failed to load tags:", err);
      loading.value = false;
    });
}

// Reload tags every time sidebar opens so counts stay fresh
watch(() => props.isOpen, (open) => {
  if (open) loadTags();
});
</script>