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

  // Image extensions that should stay as <img> — never convert these to cards
  const IMAGE_EXTS = new Set([
    'jpg','jpeg','png','gif','webp','svg','bmp','ico','avif','tiff','tif'
  ]);

  // Extensions that get a card with a Preview button (browser can open these inline)
  const PREVIEW_EXTS = new Set(['pdf', 'txt', 'rtf', 'json', 'xml', 'html', 'htm']);

  // Colour per file category — used for the icon background
  const colorMap = {
    // Documents
    'pdf': '#EF4444', 'doc': '#2B5797', 'docx': '#2B5797', 'odt': '#2B5797',
    // Spreadsheets
    'xls': '#217346', 'xlsx': '#217346', 'ods': '#217346', 'csv': '#217346',
    // Presentations
    'ppt': '#D04423', 'pptx': '#D04423', 'odp': '#D04423',
    // Apple iWork
    'numbers': '#FFA500', 'pages': '#FFA500', 'key': '#FFA500',
    // Plain text / markup
    'txt': '#6B7280', 'rtf': '#6B7280',
    // Structured web
    'html': '#3B82F6', 'htm': '#3B82F6',
    // Structured data
    'json': '#F59E0B', 'yaml': '#F59E0B', 'yml': '#F59E0B', 'xml': '#F59E0B', 'toml': '#F59E0B',
    // Archives
    'zip': '#8B5CF6', 'gz': '#8B5CF6', 'tar': '#8B5CF6', '7z': '#8B5CF6', 'rar': '#8B5CF6', 'bz2': '#8B5CF6', 'xz': '#8B5CF6',
    // Code
    'js': '#3776AB', 'ts': '#3776AB', 'py': '#3776AB', 'sh': '#3776AB', 'rb': '#3776AB', 'php': '#3776AB', 'vue': '#3776AB',
    // Audio
    'mp3': '#EC4899', 'm3u': '#EC4899', 'm4a': '#EC4899', 'ogg': '#EC4899', 'wav': '#EC4899', 'flac': '#EC4899', 'aac': '#EC4899',
    // Video
    'mp4': '#F97316', 'mkv': '#F97316', 'mov': '#F97316', 'avi': '#F97316', 'webm': '#F97316',
    // Fonts
    'ttf': '#6B7280', 'otf': '#6B7280', 'woff': '#6B7280',
  };

  // SVG icon paths per category — used inside the icon background circle
  const iconPaths = {
    // Generic document / file
    file:  'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z',
    
    // Archive / zip
    zip:   'M14,17H12V15H10V13H12V11H10V9H12V7H10V5H12V3H6A2,2 0 0,0 4,5V19A2,2 0 0,0 6,21H18A2,2 0 0,0 20,19V9L14,3V5H16V7H14V9H16V11H14V13H16V15H14V17M14,17',
    
    // Music note
    audio: 'M21,3V15.5A3.5,3.5 0 0,1 17.5,19A3.5,3.5 0 0,1 14,15.5A3.5,3.5 0 0,1 17.5,12C18.04,12 18.55,12.12 19,12.34V6.47L9,8.6V17.5A3.5,3.5 0 0,1 5.5,21A3.5,3.5 0 0,1 2,17.5A3.5,3.5 0 0,1 5.5,14C6.04,14 6.55,14.12 7,14.34V6L21,3Z',
    
    // Video camera
    video: 'M17,10.5V7A1,1 0 0,0 16,6H4A1,1 0 0,0 3,7V17A1,1 0 0,0 4,18H16A1,1 0 0,0 17,17V13.5L21,17.5V6.5L17,10.5Z',
    
    // Code files (angle brackets / braces)
    code:  'M8,3L16,3L20,7L20,21L4,21L4,7L8,3M8,5L6,7L6,19L18,19L18,9L14,9L14,5L8,5M9,11L7,13L9,15M13,11L15,13L13,15',
    
    // Web files (globe)
    web:   'M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12C4,14 4.8,15.8 6.1,17.1C7.1,15.6 8.6,14.5 10.3,14C9.5,13.2 9,12.2 9,11C9,9.6 9.8,8.4 10.8,7.6C10.3,6.9 9.5,6.3 8.6,6C9.6,5.1 10.8,4.5 12,4.3V5C12,6.1 11.1,7 10,7H9V9C9,9.6 8.6,10 8,10H6V12H8C8.6,12 9,12.4 9,13V15H11C11.6,15 12,15.4 12,16V18H14V16.9C14,15.7 14.9,14.8 16.1,14.8C16.8,14.8 17.5,15.2 17.8,15.9C18.7,14.8 19.2,13.5 19.2,12.1C19.2,10.6 18.7,9.2 17.8,8.1L17,9H15V7H13V5.3C14.2,5.5 15.4,6.1 16.4,7Z',
    
    // Data files (database cylinder)
    data:  'M12,2C8.13,2 5,4.69 5,8C5,11.31 8.13,14 12,14C15.87,14 19,11.31 19,8C19,4.69 15.87,2 12,2M12,4C14.21,4 16,5.79 16,8C16,10.21 14.21,12 12,12C9.79,12 8,10.21 8,8C8,5.79 9.79,4 12,4M5,16V19C5,22.31 8.13,25 12,25C15.87,25 19,22.31 19,19V16C17.5,17.6 14.9,18.5 12,18.5C9.1,18.5 6.5,17.6 5,16M7,19.5C7,17.6 9.2,16 12,16C14.8,16 17,17.6 17,19.5C17,21.4 14.8,23 12,23C9.2,23 7,21.4 7,19.5Z',
    
    // Spreadsheet (grid/chart)
    spreadsheet: 'M4,2H20A2,2 0 0,1 22,4V20A2,2 0 0,1 20,22H4A2,2 0 0,1 2,20V4A2,2 0 0,1 4,2M4,4V8H20V4H4M4,20H20V10H4V20M6,12H8V14H6V12M6,16H8V18H6V16M10,12H18V14H10V12M10,16H15V18H10V16Z',
    
    // Presentation (slides/chart)
    presentation: 'M8,4H16V2H8V4M18,8H20V18H18V8M4,8H6V18H4V8M2,20H22V22H2V20M12,4C15.3,4 18,6.7 18,10V18H6V10C6,6.7 8.7,4 12,4M12,6C9.8,6 8,7.8 8,10V16H16V10C16,7.8 14.2,6 12,6Z',
    
    // Text file
    text: 'M4,4H20V20H4V4M6,6V18H18V6H6M8,8H16V10H8V8M8,12H14V14H8V12M8,16H12V18H8V16Z',
    
    // Apple iWork
    iwork: 'M12,2C6.48,2 2,6.48 2,12C2,17.52 6.48,22 12,22C17.52,22 22,17.52 22,12C22,6.48 17.52,2 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M11,7V9H9V11H11V13H9V15H11V17H13V15H15V13H13V11H15V9H13V7H11Z',
    
    // Font file
    font: 'M9.5,7L8.9,5H6L10,18H12L16,5H13.1L12.5,7H9.5M10.5,9H11.5L13,14H9L10.5,9Z',   
  };

  function getIconPath(ext) {
    const archiveExts      = ['zip', 'gz', 'tar', '7z', 'rar', 'bz2', 'xz'];
    const audioExts        = ['mp3', 'm3u', 'm4a', 'ogg', 'wav', 'flac', 'aac'];
    const videoExts        = ['mp4', 'mkv', 'mov', 'avi', 'webm'];
    const codeExts         = ['js', 'ts', 'py', 'sh', 'rb', 'php', 'vue'];
    const webExts          = ['html', 'htm'];
    const dataExts         = ['json', 'yaml', 'yml', 'xml', 'toml'];
    const presentationExts = ['ppt', 'pptx', 'odp'];
    const spreadsheetExts  = ['xls', 'xlsx', 'ods', 'csv'];
    const iworkExts        = ['numbers', 'pages', 'key'];
    const fontExts         = ['ttf', 'otf', 'woff'];
    const textExts         = ['txt', 'rtf',];
    const docExts          = ['doc', 'docx', 'odt'];

    if (archiveExts.includes(ext))      return iconPaths.zip;
    if (audioExts.includes(ext))        return iconPaths.audio;
    if (videoExts.includes(ext))        return iconPaths.video;
    if (codeExts.includes(ext))         return iconPaths.code;
    if (webExts.includes(ext))          return iconPaths.web;
    if (dataExts.includes(ext))         return iconPaths.data;
    if (spreadsheetExts.includes(ext))  return iconPaths.spreadsheet;
    if (presentationExts.includes(ext)) return iconPaths.presentation;
    if (iworkExts.includes(ext))        return iconPaths.iwork;
    if (fontExts.includes(ext))         return iconPaths.font;
    if (textExts.includes(ext))         return iconPaths.text;
    if (docExts.includes(ext))          return iconPaths.file;  // Document files use generic file icon
    
    return iconPaths.file;  // Default fallback
  }

  imgs.forEach((img) => {
    const src = img.getAttribute("src") || "";
    // Match both relative ("attachments/file.ext") and absolute ("/attachments/file.ext") URLs
    if (!src.includes('attachments/')) return;
    // But exclude actual external URLs that happen to contain the word "attachments"
    if (src.startsWith('http') && !src.includes('/attachments/')) return;

    const rawExt = src.split('.').pop().split('?')[0].toLowerCase();
    // Leave actual images as <img> tags
    if (IMAGE_EXTS.has(rawExt)) return;

    const filename = decodeURIComponent(src.split("/").pop().split('?')[0]);
    const bgColor  = colorMap[rawExt] || '#6B7280';
    const iconPath = getIconPath(rawExt);
    const canPreview = PREVIEW_EXTS.has(rawExt);

    const buttonHtml = canPreview ? `
      <a class="pdf-preview-btn" href="${src}" target="_blank" rel="noopener" title="Preview in new tab">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"/>
        </svg>
        Preview
      </a>
    ` : `
      <a class="pdf-preview-btn" href="${src}" download title="Download ${filename}">
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
          <path d="${iconPath}"/>
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