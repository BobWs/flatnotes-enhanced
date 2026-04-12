<template>
  <div>
    <button
      @click="handleClick"
      class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm transition-all duration-150 text-left group"
      :style="buttonStyle"
    >
      <div class="flex items-center gap-1.5 min-w-0">
        <!-- Expand chevron -->
        <button
          v-if="group.children && group.children.length > 0"
          @click.stop="localExpanded = !localExpanded"
          class="shrink-0 p-0.5 rounded transition-transform duration-150"
          :class="isExpanded ? 'rotate-90' : ''"
        >
          <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
            <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
          </svg>
        </button>
        <span v-else class="w-4 shrink-0"></span>

        <!-- Tag icon (single tag, colored) -->
        <svg
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 shrink-0 fill-current"
          :style="{ color: isActive ? 'white' : color }"
        >
          <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
        </svg>

        <span class="truncate font-medium" :title="group.fullPath">{{ group.name }}</span>
      </div>

      <!-- Count badge: plain muted text, no colored background -->
      <span
        v-if="group.count > 0 || (group.children && group.children.length > 0)"
        class="text-xs shrink-0 ml-2 tabular-nums font-mono"
        :style="countStyle"
      >{{ group.count > 0 ? group.count : '' }}</span>
    </button>

    <!-- Children (nested tags) -->
    <div
      v-if="isExpanded && group.children && group.children.length > 0"
      class="ml-5 border-l-2 pl-1 mt-0.5 mb-0.5"
      :style="{ borderColor: color + '44' }"
    >
      <TagSidebarItem
        v-for="child in group.children"
        :key="child.fullPath"
        :group="child"
        :activeTags="activeTags"
        :forceExpand="forceExpand"
        @toggle="$emit('toggle', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, watchEffect } from "vue";
import { tagColor, tagColorLight } from "../tagColor.js";

const props = defineProps({
  group: Object,
  activeTags: Array,
  // null = no override, true = force expand all, false = force collapse all
  forceExpand: { type: Boolean, default: null },
});

const emit = defineEmits(["toggle"]);
const localExpanded = ref(false);

// The effective expanded state: forceExpand overrides local state when set
const isExpanded = computed(() => {
  if (props.forceExpand === true) return true;
  if (props.forceExpand === false) return false;
  return localExpanded.value;
});

// Auto-expand this node if any currently active tag is a child of it
watchEffect(() => {
  if (!localExpanded.value && props.activeTags.length > 0) {
    const hasActiveChild = props.activeTags.some(
      (t) => t !== props.group.fullPath && t.startsWith(props.group.fullPath + "/")
    );
    if (hasActiveChild) localExpanded.value = true;
  }
});

// Sync localExpanded when forceExpand changes so that after a force-expand/collapse
// the user can still toggle individual items freely (we sync on force change)
watch(() => props.forceExpand, (val) => {
  if (val === true) localExpanded.value = true;
  if (val === false) localExpanded.value = false;
});

const isActive = computed(() => props.activeTags.includes(props.group.fullPath));
const color = computed(() => tagColor(props.group.fullPath));

const buttonStyle = computed(() => {
  if (isActive.value) {
    return { backgroundColor: color.value, color: "white" };
  }
  return { color: `rgb(var(--theme-text))` };
});

const countStyle = computed(() => {
  if (isActive.value) {
    return { color: "rgba(255,255,255,0.85)" };
  }
  return { color: "rgb(var(--theme-text-muted))" };
});

function handleClick() {
  emit("toggle", props.group.fullPath);
}
</script>
