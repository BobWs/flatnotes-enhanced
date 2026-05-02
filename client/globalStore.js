import { defineStore } from "pinia";
import { ref } from "vue";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const pinnedVersion = ref(0); // increment to trigger re-check of pinned notes
  // Whether to show text labels next to nav/toolbar buttons.
  // true = labels visible (default), false = icons only.
  const showButtonLabels = ref(true);

  function bumpPinned() {
    pinnedVersion.value++;
  }

  return { config, pinnedVersion, bumpPinned, showButtonLabels };
});