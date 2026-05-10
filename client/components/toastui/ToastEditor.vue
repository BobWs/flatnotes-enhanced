<template>
  <div class="flex flex-col h-full">
    <SearchReplace
      :isVisible="isSearchReplaceVisible"
      :getEditorContent="getMarkdown"
      :setEditorContent="setMarkdownContent"
      @close="isSearchReplaceVisible = false"
    />
    <div ref="editorElement" class="flex-1 min-h-0"></div>

    <TagAutocomplete
      :visible="acVisible"
      :matches="acMatches"
      :counts="acCounts"
      :activeIndex="acIndex"
      :anchorRect="acAnchorRect"
      :mode="acModeRef"
      @choose="insertTagCompletion"
      @hide="acVisible = false"
    />

    <HighlightColorPicker
      :visible="showColorPicker"
      :position="colorPickerPosition"
      @select="insertHighlightWithColor"
      @close="showColorPicker = false"
    />

    <WikilinkModal
      :show="showWikilinkModal"
      @insert="insertWikilink"
      @close="showWikilinkModal = false"
    />
  </div>
</template>

<script setup>
import Editor from "@toast-ui/editor";
import { onMounted, onUnmounted, ref, watch } from "vue";

import baseOptions from "./baseOptions.js";
import SearchReplace from "../SearchReplace.vue";
import TagAutocomplete from "../TagAutocomplete.vue";
import HighlightColorPicker from "./HighlightColorPicker.vue";
import { getTags } from "../../api.js";
import { loadCallouts, getCalloutTypes } from "../../calloutStore.js";
import { tagColorSettings } from "../../tagColorStore.js";
import { loadHeaderColors, loadHighlightColors } from "../../appearanceStore.js";
import { VARIABLES } from "../../variables.js";
import { TASK_ICONS } from "../../taskIcons.js";
import WikilinkModal from "../WikilinkModal.vue";

const props = defineProps({
  initialValue: String,
  initialEditType: { type: String, default: "markdown" },
  addImageBlobHook: Function,
});

const emit = defineEmits(["change", "keydown"]);

const editorElement = ref();
const isSearchReplaceVisible = ref(false);
const showWikilinkModal = ref(false);
let toastEditor;

const acVisible = ref(false);
const acMatches = ref([]);
const acCounts = ref({});
const acIndex = ref(0);
const acAnchorRect = ref(null);
let allTagsCache = null;

// Bust the tag cache whenever the user saves new tag color overrides,
// so the next autocomplete trigger picks up any newly-defined tags.
watch(
  () => tagColorSettings.value.tag_colors,
  () => { allTagsCache = null; },
  { deep: true }
);
let cmInputListener = null;
let cmEl = null;
let acStoredPartial = "";
let acMode = "tag";
const acModeRef = ref("tag");

const showColorPicker = ref(false);
const colorPickerPosition = ref({ top: 0, left: 0 });

function getCursorPosition() {
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0) {
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const top = rect.bottom + 5;
    // On mobile: centre horizontally and ensure we don't overflow viewport
    if (window.innerWidth <= 767) {
      const pickerWidth = 180; // approximate width of the 5-col colour grid
      const safeLeft = Math.min(
        Math.max(rect.left, 8),
        window.innerWidth - pickerWidth - 8
      );
      return { top, left: safeLeft };
    }
    return { top, left: rect.left };
  }
  return { top: 100, left: 100 };
}

function insertHighlightWithColor(color) {
  const BEFORE = "==";
  const AFTER = `==:${color.name.toLowerCase()}`;
  const sel = window.getSelection();
  const selectedText = sel && !sel.isCollapsed ? sel.toString() : "";

  if (selectedText) {
    toastEditor.replaceSelection(BEFORE + selectedText + AFTER);
  } else {
    toastEditor.insertText(BEFORE + AFTER);
  }
  showColorPicker.value = false;
  toastEditor.focus();
}

const wikilinkButton = {
  name: "wikilink",
  tooltip: "Insert note link ([[Note]])",
  command: "wikilink",
  text: "[[]]",
  className: "toastui-editor-toolbar-icons",
  style: {
    background: "none",
    color: "rgb(var(--theme-brand, 248 166 107))",
    fontSize: "13px",
    fontWeight: "800",
    fontFamily: "monospace",
    width: "36px",
    letterSpacing: "-1px",
  },
};

const highlightButton = {
  name: "highlight",
  tooltip: "Highlight selected text (==text==)",
  command: "highlight",
  text: "H̲",
  className: "toastui-editor-toolbar-icons",
  style: {
    background: "none",
    fontWeight: "800",
    color: "rgb(var(--theme-brand, 248 166 107))",
    fontSize: "16px",
    width: "32px",
  },
};

const highlightColorButton = {
  name: "highlightColor",
  tooltip: "Highlight with color",
  command: "highlightColor",
  text: "🎨",
  className: "toastui-editor-toolbar-icons",
  style: {
    background: "none",
    fontSize: "16px",
    width: "32px",
  },
};

const searchReplaceButton = {
  name: "searchReplace",
  tooltip: "Search & Replace (Ctrl+H)",
  command: "searchReplace",
  text: "S/R",
  className: "toastui-editor-toolbar-icons",
  style: {
    background: "none",
    color: "rgb(var(--theme-brand, 248 166 107))",
    fontSize: "16px",
    fontWeight: "800",
    width: "32px",
  },
};

onMounted(async () => {
  await Promise.all([
    loadCallouts(),
    loadHeaderColors(),
    loadHighlightColors(),
  ]);

  // Detect mobile once at mount time (≤767px = same breakpoint as SCSS fix)
  const isMobile = window.innerWidth <= 767;

  // On mobile: collapse everything into two groups so the "..." overflow
  // dropdown is never needed. All items sit on the scrollable main toolbar.
  // On desktop: keep the original multi-group layout unchanged.
  const toolbarItems = isMobile
    ? [
        // Group 1 — text formatting (most used first)
        ["heading", "bold", "italic", "strike",
         "hr", "quote",
         "ul", "ol", "task", "indent", "outdent",
         "table", "image", "link",
         "code", "codeblock",
         highlightButton, searchReplaceButton, highlightColorButton,
        ],
      ]
    : [
        ["heading", "bold", "italic", "strike"],
        ["hr", "quote"],
        ["ul", "ol", "task", "indent", "outdent"],
        ["table", "image", "link"],
        ["code", "codeblock"],
        [highlightButton, searchReplaceButton, highlightColorButton, wikilinkButton],
      ];

  toastEditor = new Editor({
    ...baseOptions,
    el: editorElement.value,
    initialValue: props.initialValue,
    initialEditType: props.initialEditType,
    toolbarItems,
    events: {
      change: () => {
        emit("change");
      },
      keydown: (_, event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "h") {
          event.preventDefault();
          isSearchReplaceVisible.value = !isSearchReplaceVisible.value;
          return;
        }
        if (acVisible.value) {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            acIndex.value = Math.min(acIndex.value + 1, acMatches.value.length - 1);
            return;
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            acIndex.value = Math.max(acIndex.value - 1, 0);
            return;
          }
          if (event.key === "Tab" || event.key === "Enter") {
            event.preventDefault();
            insertTagCompletion(acMatches.value[acIndex.value]);
            return;
          }
          if (event.key === "Escape") {
            acVisible.value = false;
            return;
          }
        }
        if (event.key === " " || event.key === "Spacebar") {
          acVisible.value = false;
        }
        emit("keydown", event);
      },
    },
    hooks: props.addImageBlobHook ? { addImageBlobHook: props.addImageBlobHook } : {},
  });

  toastEditor.addCommand("markdown", "highlight", () => { doHighlight(); return true; });
  toastEditor.addCommand("wysiwyg", "highlight", () => { doHighlight(); return true; });
  toastEditor.addCommand("markdown", "searchReplace", () => {
    isSearchReplaceVisible.value = !isSearchReplaceVisible.value;
    return true;
  });
  toastEditor.addCommand("wysiwyg", "searchReplace", () => {
    isSearchReplaceVisible.value = !isSearchReplaceVisible.value;
    return true;
  });
  toastEditor.addCommand("markdown", "highlightColor", () => {
    colorPickerPosition.value = getCursorPosition();
    showColorPicker.value = true;
    return true;
  });
  toastEditor.addCommand("wysiwyg", "highlightColor", () => {
    colorPickerPosition.value = getCursorPosition();
    showColorPicker.value = true;
    return true;
  });
  toastEditor.addCommand("markdown", "wikilink", () => {
    showWikilinkModal.value = true;
    return true;
  });
  toastEditor.addCommand("wysiwyg", "wikilink", () => {
    showWikilinkModal.value = true;
    return true;
    return true;
  });

  attachInputListener();
});

onUnmounted(() => {
  detachInputListener();
});

function attachInputListener() {
  setTimeout(() => {
    if (!editorElement.value) return;
    cmEl = editorElement.value.querySelector(".cm-content");
    if (!cmEl) {
      cmEl = editorElement.value;
    }
    cmInputListener = handleNativeInput;
    cmEl.addEventListener("input", cmInputListener);
  }, 50);
}

function detachInputListener() {
  if (cmEl && cmInputListener) {
    cmEl.removeEventListener("input", cmInputListener);
    cmEl = null;
    cmInputListener = null;
  }
}

function doHighlight() {
  const BEFORE = "==";
  const AFTER = "==";
  const sel = window.getSelection();
  const selectedText = sel && !sel.isCollapsed ? sel.toString() : "";

  if (selectedText) {
    const isWrapped =
      selectedText.startsWith(BEFORE) &&
      selectedText.endsWith(AFTER) &&
      selectedText.length > BEFORE.length + AFTER.length;

    if (isWrapped) {
      toastEditor.replaceSelection(
        selectedText.slice(BEFORE.length, selectedText.length - AFTER.length)
      );
    } else {
      toastEditor.replaceSelection(BEFORE + selectedText + AFTER);
    }
  } else {
    toastEditor.insertText(BEFORE + AFTER);
  }
}

async function ensureTagsLoaded() {
  if (allTagsCache !== null) return;
  try {
    const data = await getTags();
    allTagsCache = data && typeof data === "object" && !Array.isArray(data) ? data : {};
  } catch {
    allTagsCache = {};
  }
  // Merge in any user-defined tag color overrides that may not exist in notes yet.
  // This ensures newly created tags in Settings are immediately available in autocomplete.
  const customTags = (tagColorSettings.value.tag_colors || [])
    .filter(t => t.tag && t.tag.trim())
    .map(t => t.tag.trim().toLowerCase());
  for (const tag of customTags) {
    if (!(tag in allTagsCache)) {
      allTagsCache[tag] = 0; // count 0 = exists but not yet in any note
    }
  }
  acCounts.value = { ...allTagsCache };
}

function handleNativeInput(event) {
  requestAnimationFrame(() => {
    checkTagAutocomplete();
  });
}

async function checkTagAutocomplete() {
  if (!toastEditor) return;

  // ── Derive current line from the markdown model (always reliable) ─────────
  // CodeMirror 6 renders each line as a series of syntax-highlighted <span>
  // elements inside a .cm-line div. Reading textContent from the cursor's
  // anchorNode only captures the current span fragment — the "- " prefix of a
  // task item often lives in a preceding sibling span, so the DOM read yields
  // just "[" or "[?" and the task-icon regex never matches on lines 2+.
  //
  // Fix: get the full current line from getMarkdown() split by the cursor's
  // line index, which is always correct regardless of how CodeMirror tokenises
  // the line. The DOM selection is kept only for dropdown positioning.
  let textBeforeCursor = "";
  let currentLineFromMd = "";

  try {
    const md = toastEditor.getMarkdown();
    const lines = md.split("\n");

    // Determine which line the cursor is on via the DOM selection.
    // Walk up from the anchorNode to find the .cm-line ancestor, then count
    // how many .cm-line siblings precede it — that gives us the line index.
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      let node = sel.getRangeAt(0).startContainer;
      // Walk up to the cm-line element
      while (node && node.nodeType !== Node.ELEMENT_NODE) node = node.parentNode;
      while (node && !(node.classList && node.classList.contains("cm-line"))) {
        node = node.parentNode;
      }
      if (node && node.classList && node.classList.contains("cm-line")) {
        // Count preceding cm-line siblings to determine 0-based line index
        let lineIndex = 0;
        let sib = node.previousElementSibling;
        while (sib) {
          if (sib.classList && sib.classList.contains("cm-line")) lineIndex++;
          sib = sib.previousElementSibling;
        }
        if (lineIndex < lines.length) {
          currentLineFromMd = lines[lineIndex];
        }
      }
    }

    // Fallback: if we couldn't resolve via DOM, use the last line of the
    // markdown (works correctly in single-line edits and WYSIWYG mode).
    if (!currentLineFromMd) {
      currentLineFromMd = lines[lines.length - 1] || "";
    }
  } catch {}

  // textBeforeCursor = the full current line from the markdown model.
  // This is always the complete line text, not a partial DOM span fragment.
  textBeforeCursor = currentLineFromMd;

  // ── Task icon autocomplete (Obsidian-style) ──────────────────────────────
  const taskIconMatch = textBeforeCursor.match(/- \[([a-zA-Z0-9*?!>"<\/\-]?)$/i);
  if (taskIconMatch) {
    const partial = taskIconMatch[1].toLowerCase();
    const matchingIcons = TASK_ICONS
      .filter(i => i.marker.toLowerCase().startsWith(partial))
      .map(i => i.marker)
      .slice(0, 10);
    if (matchingIcons.length === 0) {
      acVisible.value = false;
      return;
    }
    acMode = "taskicon";
    acModeRef.value = "taskicon";
    acStoredPartial = partial;
    acMatches.value = matchingIcons;
    acCounts.value = {};
    acIndex.value = 0;
    acVisible.value = true;
    positionDropdown();
    return;
  }

  // ── Callout autocomplete ────────────────────────────────────────────────
  const calloutMatch = textBeforeCursor.match(/\[!([a-zA-Z0-9_-]*)$/);
  if (calloutMatch) {
    const partial = calloutMatch[1].toLowerCase();

    const matchingCallouts = getCalloutTypes()
      .filter((t) => t.startsWith(partial))
      .sort()
      .slice(0, 10);

    if (matchingCallouts.length === 0) {
      acVisible.value = false;
      return;
    }

    acMode = "callout";
    acModeRef.value = "callout";
    acStoredPartial = partial;
    acMatches.value = matchingCallouts;
    acCounts.value = {};
    acIndex.value = 0;
    acVisible.value = true;
    positionDropdown();
    return;
  }

  // ── Variable autocomplete (Dataview style) ──────────────────────────────
  const varMatch = textBeforeCursor.match(/\{\{([a-zA-Z]*)$/);
  if (varMatch) {
    const partial = varMatch[1].toLowerCase();

    // Filter VARIABLES by prefix
    const matchingVars = VARIABLES
      .filter(v => v.startsWith(partial))
      .sort()
      .slice(0, 10);

    if (matchingVars.length === 0) {
      acVisible.value = false;
      return;
    }

    acMode = "variable";
    acModeRef.value = "variable";
    acStoredPartial = partial;
    acMatches.value = matchingVars;
    acCounts.value = {};
    acIndex.value = 0;
    acVisible.value = true;
    positionDropdown();
    return;
  }

  // ── Tag autocomplete ────────────────────────────────────────────────────
  const tagMatch = textBeforeCursor.match(/#([a-zA-Z0-9_/-]*)$/);
  if (!tagMatch) {
    acVisible.value = false;
    return;
  }

  const partial = tagMatch[1].toLowerCase();
  if (partial.length === 0) {
    acVisible.value = false;
    return;
  }

  await ensureTagsLoaded();

  const matchingTags = Object.keys(allTagsCache)
    .filter((t) => t.startsWith(partial) && t !== partial)
    .sort()
    .slice(0, 8);

  if (matchingTags.length === 0) {
    acVisible.value = false;
    return;
  }

  acMode = "tag";
  acStoredPartial = partial;
  acMatches.value = matchingTags;
  acIndex.value = 0;
  acVisible.value = true;
  positionDropdown();
}

function positionDropdown() {
  try {
    if (!editorElement.value) return;
    const cursor =
      editorElement.value.querySelector(".cm-cursor-primary") ||
      editorElement.value.querySelector(".cm-cursor");

    if (cursor) {
      const rect = cursor.getBoundingClientRect();
      if (rect.width > 0 || rect.height > 0 || rect.top > 0) {
        acAnchorRect.value = rect;
        return;
      }
    }

    const editorRect = editorElement.value.getBoundingClientRect();
    acAnchorRect.value = {
      top: editorRect.top + 40,
      bottom: editorRect.top + 56,
      left: editorRect.left + 20,
      right: editorRect.left + 260,
      width: 240,
      height: 16,
    };
  } catch {}
}

function insertTagCompletion(tag) {
  if (!tag) return;
  acVisible.value = false;
  detachInputListener();

  const partial = acStoredPartial || "";

  if (acMode === "callout") {
    const suffix = tag.slice(partial.length);
    toastEditor.insertText(suffix + "] ");
  } else if (acMode === "variable") {
    const suffix = tag.slice(partial.length);
    toastEditor.insertText(suffix + "}} ");
  } else if (acMode === "taskicon") {
    const suffix = tag.slice(partial.length);
    toastEditor.insertText(suffix + "] ");
  } else {
    // tag mode
    const suffix = tag.slice(partial.length);
    toastEditor.insertText(suffix + " ");
  }

  toastEditor.focus();
  acStoredPartial = "";
  acMode = "tag";
  acModeRef.value = "tag";

  setTimeout(() => { attachInputListener(); }, 50);
}

function insertWikilink({ target, display }) {
  const text = display ? `[[${target}|${display}]]` : `[[${target}]]`;
  toastEditor.insertText(text);
  showWikilinkModal.value = false;
  toastEditor.focus();
}

function getMarkdown() {
  return toastEditor.getMarkdown();
}

function setMarkdownContent(content) {
  toastEditor.setMarkdown(content);
  emit("change");
  detachInputListener();
  attachInputListener();
}

function isWysiwygMode() {
  return toastEditor.isWysiwygMode();
}

defineExpose({ getMarkdown, isWysiwygMode });
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./toastui-editor-overrides.scss";

.toastui-editor-contents mark,
.toastui-editor-ww-container mark {
  background-color: rgb(var(--theme-brand, 248 166 107) / 0.22);
  color: inherit;
  border-radius: 2px;
  padding: 0 2px;
}
</style>