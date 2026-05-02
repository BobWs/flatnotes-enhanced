<template>
  <div class="flex items-center">
    <SvgIcon
      v-if="iconPath"
      type="mdi"
      :path="iconPath"
      :size="iconSize"
      :class="{ 'mr-1': label && showLabel }"
    ></SvgIcon>
    <!-- forceLabel overrides the global setting (used in dropdown menus) -->
    <span v-if="label && showLabel">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed } from "vue";
import SvgIcon from "@jamescoyle/vue-icon";
import { useGlobalStore } from "../globalStore.js";

const globalStore = useGlobalStore();

const props = defineProps({
  iconPath: String,
  iconSize: {
    type: String,
    default: "1.25em",
  },
  label: String,
  forceLabel: {
    type: Boolean,
    default: false,
  },
});

// Show label if: forced (e.g. in dropdown menu) OR global setting allows it
const showLabel = computed(() => props.forceLabel || globalStore.showButtonLabels);
</script>
