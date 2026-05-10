import codeSyntaxHighlight from "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight-all.js";
import router from "../../router.js";
import {
  getHeaderColor,
  getDefaultHighlightColor,
  getEnabledHighlightColors,
  getTableHeaderColor,
  getZebraStriping,
  getQuoteBorderColor,
  getQuoteBackgroundColor,
  getQuoteDarkBackgroundColor,
} from "../../appearanceStore.js";
// ── Tag color — delegate to tagColor.js which respects user settings ─────────
import { tagColor as tagColorSolid, tagColorLight as tagColorLightFn } from "../../tagColor.js";
function tagColorFromStr(str) {
  return { solid: tagColorSolid(str), light: tagColorLightFn(str) };
}

function renderTagChip(tagName) {
  const { solid, light } = tagColorFromStr(tagName);
  const displayName = tagName.includes("/")
    ? tagName.split("/").join(" › ")
    : tagName;
  return (
    `<span class="fn-tag" style=` +
    `"background-color:${light};color:${solid};` +
    `border:1px solid ${solid}44;` +
    `border-radius:9999px;padding:0 0.5rem;font-size:1rem;` +
    `font-weight:500;white-space:nowrap;display:inline-flex;` +
    `align-items:center;line-height:1.6;" title="#${tagName}">${displayName}</span>`
  );
}

function getColorMap() {
  const colors = getEnabledHighlightColors();
  const colorMap = {};
  colors.forEach(c => { colorMap[c.name.toLowerCase()] = c.color; });
  return colorMap;
}

// ── Variable replacement for Dataview-style placeholders ─────────────────────
function replaceVariables(text, variables) {
  if (!variables || Object.keys(variables).length === 0) return text;
  
  let result = text;
  // Replace {{variable}} patterns
  for (const [key, value] of Object.entries(variables)) {
    const pattern = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
    result = result.replace(pattern, value || '');
  }
  return result;
}

// ── Custom HTML renderer ──────────────────────────────────────────────────────
const customHTMLRenderer = {
  // Add id attribute to headings with dynamic colors
  heading(node, { entering, getChildrenText, origin }) {
    const original = origin();
    
    if (entering) {
      let level = 1;
      if (node.attrs && node.attrs.level) {
        level = node.attrs.level;
      } else if (node.level) {
        level = node.level;
      }
      
      const color = getHeaderColor(level);
      const id = getChildrenText(node)
        .toLowerCase()
        .replace(/[^a-z0-9-\s]/g, "")
        .trim()
        .replace(/\s/g, "-");
      
      if (original.attributes) {
        original.attributes.id = id;
        if (color) {
          original.attributes.style = `color: ${color};`;
        }
      } else {
        original.attributes = { id: id };
        if (color) {
          original.attributes.style = `color: ${color};`;
        }
      }
    }
    
    return original;
  },

  // Convert relative hash links to absolute links
  link(_, { entering, origin }) {
    const original = origin();
    if (entering) {
      const href = original.attributes.href;
      if (href && href.startsWith("#")) {
        const targetRoute = {
          ...router.currentRoute.value,
          hash: href,
        };
        original.attributes.href = router.resolve(targetRoute).href;
      }
    }
    return original;
  },

  // Handle tables with custom styling
  table(node, { entering, origin }) {
    const original = origin();
    
    if (entering) {
      const headerColor = getTableHeaderColor();
      const zebraStriping = getZebraStriping();
      
      if (original.attributes) {
        if (headerColor) {
          original.attributes['data-custom-table'] = 'true';
        }
        if (zebraStriping) {
          original.attributes['data-zebra'] = 'true';
        }
        if (headerColor) {
          original.attributes.style = `--table-header-color: ${headerColor};`;
        }
      } else {
        original.attributes = {};
        if (headerColor) {
          original.attributes['data-custom-table'] = 'true';
          original.attributes.style = `--table-header-color: ${headerColor};`;
        }
        if (zebraStriping) {
          original.attributes['data-zebra'] = 'true';
        }
      }
    }
    
    return original;
  },

  // Handle blockquotes with custom styling
  blockQuote(node, { entering, origin }) {
    const original = origin();
    
    if (entering) {
      const borderColor = getQuoteBorderColor();
      const bgColor = getQuoteBackgroundColor();
      const darkBgColor = getQuoteDarkBackgroundColor();
      
      if (borderColor || bgColor || darkBgColor) {
        if (original.attributes) {
          original.attributes['data-custom-quote'] = 'true';
          let styleStr = '';
          if (borderColor) styleStr += `--quote-border-color: ${borderColor};`;
          if (bgColor) styleStr += `--quote-bg-color: ${bgColor};`;
          if (darkBgColor) styleStr += `--quote-dark-bg-color: ${darkBgColor};`;
          if (styleStr) original.attributes.style = styleStr;
        } else {
          original.attributes = { 'data-custom-quote': 'true' };
          let styleStr = '';
          if (borderColor) styleStr += `--quote-border-color: ${borderColor};`;
          if (bgColor) styleStr += `--quote-bg-color: ${bgColor};`;
          if (darkBgColor) styleStr += `--quote-dark-bg-color: ${darkBgColor};`;
          if (styleStr) original.attributes.style = styleStr;
        }
      }
    }
    
    return original;
  },

  // Handle inline text: render ==text==:color as colored highlights and #tag as colored chips
  text(node, { origin }) {
    const literal = node.literal || "";
    
    // Get variables from the context (passed via the renderer)
    // This is accessed through a closure; we'll set it in the Viewer
    const variables = window.__flatnotes_variables || {};
    
    // First replace variables in the literal text
    let processed = replaceVariables(literal, variables);
    
    // Use original renderer on the processed text
    const original = origin();
    
    // Check for highlight with color syntax: ==text==:color or ==text=={color}
    const hasHighlight = /==.+?==(?::[a-zA-Z]+|\{[a-zA-Z]+\})?/s.test(processed);
    const hasTag = /(?:^|\s)#[a-zA-Z0-9_-]+/.test(processed);
    const hasWikilink = /\[\[.+?\]\]/.test(processed);

    if (!hasHighlight && !hasTag && !hasWikilink) {
      return { type: "text", content: processed };
    }

    // Pattern: ==text== followed by optional :color or {color}
    const HIGHLIGHT_RE = /==((?:[^=]|=[^=])+?)==(?::([a-zA-Z]+)|\{([a-zA-Z]+)\})?/gs;
    const TAG_RE = /(?<![a-zA-Z0-9_-])#([a-zA-Z0-9_][a-zA-Z0-9_/-]*)/g;
    // [[Note Title]] — display text after | is used as label but title is always the link target
    const WIKILINK_RE = /\[\[([^\]]+?)(?:\|([^\]]+?))?\]\]/g;

    const matches = [];
    let m;

    const hl = new RegExp(HIGHLIGHT_RE.source, "gs");
    while ((m = hl.exec(processed)) !== null) {
      const colorName = m[2] || m[3] || null;
      matches.push({ 
        start: m.index, 
        end: m.index + m[0].length, 
        type: "highlight", 
        inner: m[1],
        color: colorName
      });
    }

    const tg = new RegExp(TAG_RE.source, "g");
    while ((m = tg.exec(processed)) !== null) {
      const overlaps = matches.some(
        (ex) => m.index >= ex.start && m.index < ex.end
      );
      if (!overlaps) {
        matches.push({ start: m.index, end: m.index + m[0].length, type: "tag", inner: m[1] });
      }
    }

    const wl = new RegExp(WIKILINK_RE.source, "g");
    while ((m = wl.exec(processed)) !== null) {
      const overlaps = matches.some(
        (ex) => m.index >= ex.start && m.index < ex.end
      );
      if (!overlaps) {
        // m[1] = note title (everything before | or end of [[]])
        // m[2] = display label (everything after |, optional)
        const target = m[1].trim();
        const label  = m[2] ? m[2].trim() : null;
        matches.push({
          start: m.index,
          end:   m.index + m[0].length,
          type:  "wikilink",
          target,
          label,
        });
      }
    }

    if (matches.length === 0) {
      return { type: "text", content: processed };
    }

    matches.sort((a, b) => a.start - b.start);

    const colorMap = getColorMap();
    const defaultColor = getDefaultHighlightColor();

    let out = "";
    let pos = 0;
    for (const match of matches) {
      if (match.start > pos) {
        out += escapeHtml(processed.slice(pos, match.start));
      }
      if (match.type === "highlight") {
        let bgColor = defaultColor;
        if (match.color && colorMap[match.color.toLowerCase()]) {
          bgColor = colorMap[match.color.toLowerCase()];
        }
        out += `<mark style="background-color: ${bgColor};">${escapeHtml(match.inner)}</mark>`;
      } else if (match.type === "tag") {
        out += renderTagChip(match.inner);
      } else if (match.type === "wikilink") {
        // Always route to match.target (the note title), never to the display label.
        // The href is built via router.resolve so it uses the app's hash routing.
        const href = router.resolve({
          name: "note",
          params: { title: match.target },
        }).href;
        // Display text: use label if provided, otherwise the note title.
        // The |pipe and everything after it is purely cosmetic — never part of the URL.
        const display = escapeHtml(match.label || match.target);
        const tooltip = match.label
          ? `[[${escapeHtml(match.target)}|${escapeHtml(match.label)}]]`
          : `[[${escapeHtml(match.target)}]]`;
        out += `<a href="${href}" class="fn-wikilink" title="${tooltip}">${display}</a>`;
      }
      pos = match.end;
    }
    if (pos < processed.length) {
      out += escapeHtml(processed.slice(pos));
    }

    return { type: "html", content: out };
  },

};

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const baseOptions = {
  height: "100%",
  plugins: [codeSyntaxHighlight],
  customHTMLRenderer: customHTMLRenderer,
  usageStatistics: false,
};

export default baseOptions;