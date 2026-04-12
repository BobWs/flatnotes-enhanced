<template>
  <Teleport to="body">
    <div
      v-if="visible && matches.length > 0"
      :style="positionStyle"
      class="fixed z-50 min-w-[160px] max-w-[240px] max-h-48 overflow-y-auto
             rounded-md border border-theme-border bg-theme-background shadow-lg py-1"
    >
      <button
        v-for="(tag, i) in matches"
        :key="tag"
        @mousedown.prevent="choose(tag)"
        class="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors cursor-pointer"
        :class="{ 'bg-theme-background-elevated': i === activeIndex }"
        :style="mode === 'tag' && i === activeIndex ? { backgroundColor: tagColorLight(tag) } : {}"
      >
        <!-- Tag mode: single tag icon -->
        <svg
          v-if="mode === 'tag'"
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 shrink-0 fill-current"
          :style="{ color: tagColor(tag) }"
        >
          <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
        </svg>
        <!-- Callout mode: small callout icon -->
        <svg
          v-else-if="mode === 'callout'"
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 fill-current shrink-0 text-theme-text-muted"
        >
          <path d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2Z"/>
        </svg>
        <!-- Variable mode: calendar/clock icon -->
        <svg
          v-else-if="mode === 'variable'"
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 fill-current shrink-0 text-theme-text-muted"
        >
          <path d="M12,20C8.13,20 5,16.87 5,13S8.13,6 12,6C15.87,6 19,9.13 19,13S15.87,20 12,20M19,10V8H5V10H19M12,4C7.58,4 4,7.58 4,12C4,16.42 7.58,20 12,20C16.42,20 20,16.42 20,12C20,7.58 16.42,4 12,4Z"/>
        </svg>
        <!-- Task icon mode: checkbox outline -->
        <svg
          v-else-if="mode === 'taskicon'"
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 fill-current shrink-0 text-theme-text-muted"
        >
          <path d="M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M19,5V7H5V5H19Z"/>
        </svg>
        <!-- Folder mode: folder icon -->
        <svg
          v-else
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 fill-current shrink-0 text-theme-text-muted"
        >
          <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
        </svg>

        <span class="truncate">
          <template v-if="mode === 'callout'">[!{{ tag }}]</template>
          <template v-else-if="mode === 'variable'">{{ '{' + '{' + tag + '}' + '}' }}</template>
          <template v-else-if="mode === 'taskicon'">[{{ tag }}]</template>
          <template v-else>{{ tag }}</template>
        </span>
        <span v-if="mode === 'tag'" class="ml-auto text-xs text-theme-text-very-muted tabular-nums">{{ counts[tag] || '' }}</span>
        <span v-else-if="mode === 'taskicon'" class="ml-auto text-xs text-theme-text">{{ getTaskIconLabel(tag) }}</span>
      </button>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from "vue";
import { tagColor, tagColorLight } from "../tagColor.js";
import { TASK_ICONS } from "../taskIcons.js";

const props = defineProps({
  visible: Boolean,
  matches: Array,
  counts: Object,
  activeIndex: { type: Number, default: 0 },
  anchorRect: Object,
  mode: { type: String, default: "tag" },
});

const emit = defineEmits(["choose", "hide"]);

function choose(tag) {
  emit("choose", tag);
}

function getTaskIconLabel(marker) {
  const icon = TASK_ICONS.find(i => i.marker === marker);
  return icon ? icon.label : '';
}

const positionStyle = computed(() => {
  const r = props.anchorRect;
  if (!r) return { display: "none" };
  const DROPDOWN_HEIGHT = 200;
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;

  let top = r.bottom + 4;
  if (top + DROPDOWN_HEIGHT > viewportHeight && r.top - DROPDOWN_HEIGHT > 0) {
    top = r.top - DROPDOWN_HEIGHT - 4;
  }

  const DROPDOWN_WIDTH = 240;
  let left = r.left;
  if (left + DROPDOWN_WIDTH > viewportWidth) {
    left = Math.max(4, viewportWidth - DROPDOWN_WIDTH - 8);
  }
  left = Math.max(4, left);

  return { top: `${top}px`, left: `${left}px` };
});
</script>