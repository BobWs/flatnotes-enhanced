<template>
  <span
    class="fn-tag inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 font-medium"
    :style="chipStyle"
    :title="'#' + tag"
  >{{ displayTag }}</span>
</template>

<script setup>
import { computed } from "vue";
import { tagColor, tagColorLight } from "../tagColor.js";

const props = defineProps({
  tag: String,
});

const displayTag = computed(() =>
  (props.tag || "").includes("/")
    ? (props.tag || "").split("/").join(" › ")
    : (props.tag || "")
);

const chipStyle = computed(() => ({
  backgroundColor: tagColorLight(props.tag),
  color: tagColor(props.tag),
  border: `1px solid ${tagColor(props.tag)}44`,
}));
</script>
