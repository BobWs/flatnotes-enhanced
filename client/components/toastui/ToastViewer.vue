<template>
  <div ref="viewerElement"></div>
</template>

<script setup>
import Viewer from "@toast-ui/editor/dist/toastui-editor-viewer";
import { onMounted, ref, watch } from "vue";

import baseOptions from "./baseOptions.js";
import extendedAutolinks from "./extendedAutolinks.js";
import { loadCallouts, getCalloutIcon, getCalloutColor, hexToRgb } from "../../calloutStore.js";
import { loadHeaderColors, loadHighlightColors, loadQuoteStyle } from "../../appearanceStore.js";
import { TASK_ICONS } from "../../taskIcons.js";
import { loadTaskIcons, getTaskIconColor, isTaskIconsEnabled } from "../../taskIconStore.js";
import { updateNote } from "../../api.js";

const props = defineProps({
  initialValue: String,
  created: { type: String, default: null },
  updated: { type: String, default: null },
  title: { type: String, default: null },
  folder: { type: String, default: null },
  tags: { type: Array, default: () => [] },
});

const viewerElement = ref();
let viewerInstance = null;

function formatTagDisplay(tag) {
  if (!tag) return tag;
  return tag.split("/").join(" › ");
}

function formatTitleDisplay(title, folder) {
  if (!title) return title;
  if (!folder) return title;
  const folderPrefix = folder + "/";
  if (title.startsWith(folderPrefix)) {
    return title.substring(folderPrefix.length);
  }
  return title;
}

const variables = {
  title: formatTitleDisplay(props.title || "", props.folder || ""),
  created: props.created || "",
  updated: props.updated || "",
  folder: props.folder || "",
  tags: props.tags ? props.tags.map(formatTagDisplay).join(", ") : "",
};

watch([() => props.title, () => props.created, () => props.updated, () => props.folder, () => props.tags], () => {
  variables.title = formatTitleDisplay(props.title || "", props.folder || "");
  variables.created = props.created || "";
  variables.updated = props.updated || "";
  variables.folder = props.folder || "";
  variables.tags = props.tags ? props.tags.map(formatTagDisplay).join(", ") : "";
  
  window.__flatnotes_variables = variables;
  
  if (viewerInstance) {
    const incoming = props.initialValue || '';
    // Skip re-render when the incoming content is exactly what we just saved.
    // This avoids a flash + unnecessary DOM rebuild after a checkbox toggle.
    if (incoming !== currentMarkdown) {
      currentMarkdown = incoming;
      viewerInstance.setMarkdown(incoming);
    }
    // Re-run post-processors (also re-binds checkboxes after any re-render)
    setTimeout(() => {
      processCallouts(viewerElement.value);
      processDocumentLinks(viewerElement.value);
      processTaskIcons(viewerElement.value);
      processCollapsibleGroups(viewerElement.value, props.title || '');
      processCheckboxes(viewerElement.value);
    }, 50);
  }
});

function processCallouts(el) {
  const blockquotes = el.querySelectorAll("blockquote");
  blockquotes.forEach((bq) => {
    const firstP = bq.querySelector("p");
    if (!firstP) return;
    const firstText = firstP.textContent || "";
    const match = firstText.match(/^\[!([^\]]+)\]\s*(.*)$/);
    if (!match) return;

    const calloutType = match[1].trim().toLowerCase();
    const titleText = match[2].trim() ||
      (calloutType.charAt(0).toUpperCase() + calloutType.slice(1).replace(/-/g, " "));

    const iconPath = getCalloutIcon(calloutType);
    const color = getCalloutColor(calloutType);
    const rgbVal = hexToRgb(color);

    const calloutDiv = document.createElement("div");
    calloutDiv.className = "callout";
    calloutDiv.dataset.callout = calloutType;
    calloutDiv.style.setProperty("--callout-color", rgbVal);

    calloutDiv.innerHTML =
      `<div class="callout-title">` +
        `<svg class="callout-icon" viewBox="0 0 24 24">` +
          `<path d="${iconPath}"/>` +
        `</svg>` +
        `<span class="callout-title-inner">${titleText}</span>` +
      `</div>`;

    const bodyParagraphs = Array.from(bq.querySelectorAll("p")).slice(1);
    if (bodyParagraphs.length > 0) {
      const bodyDiv = document.createElement("div");
      bodyDiv.className = "callout-content";
      bodyParagraphs.forEach((p) => { bodyDiv.appendChild(p.cloneNode(true)); });
      calloutDiv.appendChild(bodyDiv);
    }

    bq.replaceWith(calloutDiv);
  });
}

function processDocumentLinks(el) {
  const imgs = el.querySelectorAll("img");
  const docExtensions = [
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".numbers", ".pages", ".txt", ".rtf"
  ];

  imgs.forEach((img) => {
    const src = img.getAttribute("src") || "";
    const ext = src.split('.').pop().toLowerCase();
    if (!docExtensions.includes('.' + ext)) return;

    const filename = decodeURIComponent(src.split("/").pop());

    const colorMap = {
      pdf: '#EF4444',
      docx: '#2B5797',
      doc: '#2B5797',
      xlsx: '#217346',
      xls: '#217346',
      numbers: '#FFA500',
      pages: '#FFA500',
      txt: '#6B7280',
      rtf: '#6B7280',
    };
    const bgColor = colorMap[ext] || '#6B7280';

    const canPreview = ext === 'pdf' || ext === 'txt' || ext === 'rtf';

    const buttonHtml = canPreview ? `
      <a class="pdf-preview-btn" href="${src}" target="_blank" rel="noopener" title="Preview in new tab">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
        </svg>
        Preview
      </a>
    ` : `
      <a class="pdf-preview-btn" href="${src}" download title="Download">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
        </svg>
        Download
      </a>
    `;

    const card = document.createElement("div");
    card.className = "pdf-attachment-card";
    card.innerHTML = `
      <div class="pdf-attachment-icon" style="background: ${bgColor}">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
      </div>
      <span class="pdf-attachment-name" title="${filename}">${filename}</span>
      ${buttonHtml}
    `;

    img.replaceWith(card);
  });
}

// ── Collapse state: Map<noteTitle, Set<groupKey>> ────────────────────────────
// Persists which groups are collapsed across re-renders of the same note.
// Keyed by note title so switching notes always starts fresh.
// groupKey = trimmed label text of the parent item (stable within a note).
const collapseState = new Map();

function _getCollapseSet(noteTitle) {
  if (!collapseState.has(noteTitle)) {
    collapseState.set(noteTitle, new Set());
  }
  return collapseState.get(noteTitle);
}

// ── Process custom task icons ─────────────────────────────────────────────────
// Converts [marker] syntax to inline SVG icons.
// IMPORTANT: only inspects direct text content of the <li>, not its nested
// <ul> children. This prevents the TreeWalker from grabbing child item text
// and misidentifying non-parent items as parents.
function processTaskIcons(el) {
  const listItems = el.querySelectorAll('li');
  listItems.forEach(li => {
    if (li.querySelector('input[type="checkbox"]')) return;

    // Only look at direct children — stop before any nested <ul>/<ol>
    let textNode = null;
    for (const child of li.childNodes) {
      if (child.nodeType === Node.ELEMENT_NODE &&
          (child.tagName === 'UL' || child.tagName === 'OL')) break;
      if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
        textNode = child;
        break;
      }
      // Descend one level into inline elements (e.g. <p> wrapping the text)
      if (child.nodeType === Node.ELEMENT_NODE) {
        for (const grandchild of child.childNodes) {
          if (grandchild.nodeType === Node.TEXT_NODE && grandchild.textContent.trim()) {
            textNode = grandchild;
            break;
          }
        }
        if (textNode) break;
      }
    }
    if (!textNode) return;

    const text = textNode.textContent;
    const match = text.match(/^\[([a-zA-Z0-9*?!>"<\/\-])\]\s*(.*)$/);
    if (!match) return;

    const marker = match[1];
    const remainingText = match[2];
    const iconData = TASK_ICONS.find(i => i.marker === marker);
    if (!iconData) return;

    // Resolve color from store (falls back to currentColor if store unavailable)
    let fillColor = 'currentColor';
    try {
      const { getTaskIconColor, isTaskIconsEnabled } = window.__taskIconStore || {};
      if (isTaskIconsEnabled && isTaskIconsEnabled()) {
        fillColor = getTaskIconColor(marker) || '#6B7280';
      }
    } catch {}

    textNode.textContent = remainingText;

    const iconSpan = document.createElement('span');
    iconSpan.className = 'task-custom-icon';
    iconSpan.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="${fillColor}"><path d="${iconData.iconPath}"/></svg>`;
    textNode.parentNode.insertBefore(iconSpan, textNode);

    li.classList.add('task-custom');
    li.setAttribute('data-task-icon', marker);
  });
}

// ── Process collapsible task groups ──────────────────────────────────────────
// Runs after processTaskIcons(). Finds every .task-custom <li> that contains
// a nested <ul> or <ol> and converts it into a collapsible group.
//
// DOM before:
//   <li class="task-custom" data-task-icon="<">
//     <span class="task-custom-icon">…svg…</span>
//     Vacation
//     <ul>…child items…</ul>
//   </li>
//
// DOM after:
//   <li class="task-custom task-group" data-task-icon="<">
//     <button class="task-group-toggle" aria-expanded="true">…chevron…</button>
//     <span class="task-custom-icon">…svg…</span>
//     <span class="task-group-label">Vacation</span>
//     <ul class="task-group-children">…child items…</ul>
//   </li>
//
function processCollapsibleGroups(el, noteTitle) {
  const collapsed = _getCollapseSet(noteTitle);

  // Only process .task-custom items — plain list items are untouched
  const customItems = el.querySelectorAll('li.task-custom');
  customItems.forEach(li => {
    const childList = li.querySelector(':scope > ul, :scope > ol');
    if (!childList) return;  // no nested list → not a group

    // ── Derive a stable group key from marker + label text ─────────────────
    let labelText = '';
    for (const node of li.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        const t = node.textContent.trim();
        if (t) { labelText = t; break; }
      }
    }
    const groupKey = li.getAttribute('data-task-icon') + ':' + labelText;
    const isCollapsed = collapsed.has(groupKey);

    // ── Mark the li as a collapsible group ─────────────────────────────────
    li.classList.add('task-group');

    // ── Wrap the label text node in a <span> for clean styling ─────────────
    for (const node of [...li.childNodes]) {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
        const labelSpan = document.createElement('span');
        labelSpan.className = 'task-group-label';
        labelSpan.textContent = node.textContent;
        li.replaceChild(labelSpan, node);
        break;
      }
    }

    // ── Wrap the child <ul> in a grid-container div ─────────────────────────
    // The wrapper is the CSS grid container that animates grid-template-rows.
    // The <ul> itself is the single grid item (min-height:0, overflow:hidden).
    // This isolates the collapse clipping from the list's own children,
    // so checkboxes and bullets inside the nested list are never cut off.
    const wrapper = document.createElement('div');
    wrapper.className = 'task-group-children-wrapper' +
      (isCollapsed ? ' task-group-collapsed' : '');
    childList.classList.add('task-group-children');
    childList.parentNode.insertBefore(wrapper, childList);
    wrapper.appendChild(childList);

    // ── Build the chevron toggle button ────────────────────────────────────
    // Colored theme-brand (orange) via CSS; sits in the left gutter.
    const btn = document.createElement('button');
    btn.className = 'task-group-toggle';
    btn.setAttribute('aria-expanded', String(!isCollapsed));
    btn.setAttribute('title', isCollapsed ? 'Expand group' : 'Collapse group');
    btn.innerHTML =
      `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" ` +
      `class="task-group-chevron${isCollapsed ? ' task-group-chevron-collapsed' : ''}">` +
      `<path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>` +
      `</svg>`;

    // ── Toggle handler ──────────────────────────────────────────────────────
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const nowCollapsed = wrapper.classList.toggle('task-group-collapsed');
      const chevron = btn.querySelector('.task-group-chevron');
      chevron.classList.toggle('task-group-chevron-collapsed', nowCollapsed);
      btn.setAttribute('aria-expanded', String(!nowCollapsed));
      btn.setAttribute('title', nowCollapsed ? 'Expand group' : 'Collapse group');
      if (nowCollapsed) {
        collapsed.add(groupKey);
      } else {
        collapsed.delete(groupKey);
      }
    });

    // Prepend the chevron button as the very first child of the li
    li.insertBefore(btn, li.firstChild);
  });
}


// ── Process interactive checkboxes ───────────────────────────────────────────
// Removes the `disabled` attribute ToastUI adds to task-list checkboxes and
// attaches click handlers that toggle the markdown source and persist via API.
//
// Mapping strategy: DOM checkboxes and markdown task lines are always in the
// same sequential order (ToastUI renders them top-to-bottom without reordering).
// So checkbox[i] in the DOM corresponds to task line[i] in the markdown.
// This is simpler and more reliable than text-content matching (which breaks
// when two items have identical labels).
//
// Save strategy: optimistic — flip the checkbox immediately, save in the
// background, revert on failure. A `saving` flag serialises rapid clicks.

// Track the markdown the component currently considers canonical.
// Updated after every successful save so the watch doesn't re-render on
// the content it just wrote.
let currentMarkdown = '';
let isSaving = false;

// Task line regex — matches both unordered and ordered list task items
const TASK_LINE_RE = /^(\s*[-*+]|\s*\d+\.) \[[ xX]\]/;

function processCheckboxes(el) {
  if (!props.title) return;  // no title → no save target, skip

  // Collect all rendered checkboxes in DOM order
  const checkboxEls = Array.from(el.querySelectorAll(
    'li.task-list-item input[type="checkbox"]'
  ));
  if (checkboxEls.length === 0) return;

  // Sanity-check: DOM count must match markdown task-line count.
  // Computed here just for the guard; the handler always re-reads fresh markdown.
  const mdSnapshot = currentMarkdown || props.initialValue || '';
  const snapshotTaskCount = mdSnapshot.split('\n').filter(
    l => TASK_LINE_RE.test(l)
  ).length;
  if (snapshotTaskCount !== checkboxEls.length) return;

  checkboxEls.forEach((input, checkboxIndex) => {
    // Clone to remove any previously attached listeners (re-render safety)
    const fresh = input.cloneNode(true);
    fresh.removeAttribute('disabled');
    fresh.style.cursor = 'pointer';
    input.parentNode.replaceChild(fresh, input);

    fresh.addEventListener('click', async (e) => {
      e.stopPropagation();

      // Serialise — if a save is already in flight, ignore this click.
      // The re-render after the in-flight save re-binds all checkboxes with
      // up-to-date state, so nothing is permanently lost.
      if (isSaving) {
        e.preventDefault();
        return;
      }

      // ── Read the CURRENT markdown at click time (not the closure snapshot) ──
      // This is critical for correctness when two checkboxes are toggled in
      // quick succession: each handler must operate on the latest saved state,
      // not on the markdown that existed when processCheckboxes() ran.
      const liveMd = currentMarkdown || props.initialValue || '';
      const liveLines = liveMd.split('\n');
      const liveTaskIndices = liveLines.reduce((acc, line, idx) => {
        if (TASK_LINE_RE.test(line)) acc.push(idx);
        return acc;
      }, []);

      if (checkboxIndex >= liveTaskIndices.length) return; // safety guard

      const nowChecked = fresh.checked;
      const lineIdx = liveTaskIndices[checkboxIndex];
      const originalLine = liveLines[lineIdx];

      // Flip the marker
      const updatedLine = nowChecked
        ? originalLine.replace(/\[ \]/, '[x]')
        : originalLine.replace(/\[[xX]\]/, '[ ]');

      const updatedLines = [...liveLines];
      updatedLines[lineIdx] = updatedLine;
      const newMarkdown = updatedLines.join('\n');

      // Optimistic update — reflect the new state immediately
      currentMarkdown = newMarkdown;

      isSaving = true;
      viewerElement.value && viewerElement.value.classList.add('fn-saving');
      try {
        await updateNote(props.title, props.title, newMarkdown);
      } catch {
        // Revert on failure
        currentMarkdown = liveMd;
        fresh.checked = !nowChecked;
      } finally {
        isSaving = false;
        viewerElement.value && viewerElement.value.classList.remove('fn-saving');
      }
    });
  });
}

onMounted(async () => {
  await Promise.all([
    loadCallouts(),
    loadHeaderColors(),
    loadHighlightColors(),
    loadTaskIcons(),
  ]);

  // Expose task icon store to processTaskIcons() which runs in a DOM callback
  window.__taskIconStore = { getTaskIconColor, isTaskIconsEnabled };

  window.__flatnotes_variables = variables;

  currentMarkdown = props.initialValue || '';

  viewerInstance = new Viewer({
    ...baseOptions,
    extendedAutolinks,
    el: viewerElement.value,
    initialValue: props.initialValue,
  });

  setTimeout(() => {
    processCallouts(viewerElement.value);
    processDocumentLinks(viewerElement.value);
    processTaskIcons(viewerElement.value);
    processCollapsibleGroups(viewerElement.value, props.title || '');
    processCheckboxes(viewerElement.value);
  }, 50);
});
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor-viewer.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./toastui-editor-overrides.scss";

.toastui-editor-contents mark {
  background-color: rgb(var(--theme-brand) / 0.25);
  color: inherit;
  border-radius: 2px;
  padding: 0 2px;
}
</style>