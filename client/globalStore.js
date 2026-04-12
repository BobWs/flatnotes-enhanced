import { defineStore } from "pinia";
import { ref } from "vue";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const pinnedVersion = ref(0); // increment to trigger re-check of pinned notes

  function bumpPinned() {
    pinnedVersion.value++;
  }

  return { config, pinnedVersion, bumpPinned };
});