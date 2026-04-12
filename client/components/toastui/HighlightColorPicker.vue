<template>
  <div
    v-if="visible"
    class="fixed z-50 bg-theme-background border border-theme-border rounded-lg shadow-lg p-2"
    :style="{ top: position.top + 'px', left: position.left + 'px' }"
  >
    <div class="grid grid-cols-5 gap-2">
      <button
        v-for="color in colors"
        :key="color.name"
        @click="selectColor(color)"
        class="w-8 h-8 rounded border border-theme-border transition-transform hover:scale-110"
        :style="{ backgroundColor: color.color }"
        :title="color.name"
      ></button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { getEnabledHighlightColors } from "../../appearanceStore.js";

const props = defineProps({
  visible: Boolean,
  position: { type: Object, default: () => ({ top: 0, left: 0 }) },
});

const emit = defineEmits(["select", "close"]);

const colors = computed(() => getEnabledHighlightColors());

function selectColor(color) {
  emit("select", color);
  emit("close");
}
</script>