/**
 * frontmatter.js
 *
 * Utilities for detecting and stripping YAML / TOML frontmatter in markdown.
 *
 * Frontmatter spec (Jekyll / Hugo / Obsidian convention):
 *   - Delimited by lines containing only "---" (YAML) or "+++" (TOML).
 *   - Ideally starts at byte offset 0, but in practice apps like Flatnotes
 *     may prepend system tags (#pin, #archived) or user tags before the block.
 *     We handle both cases: frontmatter at position 0 and frontmatter preceded
 *     by a short prefix of blank lines or #-prefixed lines.
 *
 * What these functions do NOT touch:
 *   - Horizontal rules ("---") that appear after real note content has begun.
 *   - Code blocks containing "---".
 *   - Any content with no valid frontmatter delimiters.
 *
 * The file on disk is never modified — all transforms are purely in-memory,
 * applied only for viewer / preview rendering. The editor always receives
 * the raw, unmodified content.
 *
 * Note: A collapsible <details>/<summary> variant was prototyped but removed.
 * Toast UI's markdown-it parser does not reliably pass raw HTML blocks through
 * verbatim across all edge cases (prefix lines, tags above/below, pin, archive),
 * making a stable collapse implementation impractical without patching Toast UI
 * internals. The hide toggle covers the primary use case.
 */

/**
 * Maximum number of lines before the opening fence that we accept as a
 * "prefix" (system tags, user tags, blank lines). Any fence found after
 * this many lines is treated as a mid-document horizontal rule, not frontmatter.
 */
const MAX_PREFIX_LINES = 10;

/**
 * Scans content for a frontmatter block. Accepts a short prefix of non-fence
 * lines before the opening fence (to handle #pin, #archived, tags-above, etc).
 *
 * Returns null if no valid frontmatter block is found.
 *
 * @param {string} content
 * @returns {{
 *   prefix: string,   // Everything before the opening fence (may be empty)
 *   body: string,     // Raw YAML/TOML lines between the fences
 *   rest: string,     // Everything after the closing fence
 *   fence: string,    // "---" or "+++"
 * } | null}
 */
function parseFrontmatter(content) {
  if (!content) return null;

  const lines = content.split(/\r?\n/);
  let fenceLineIdx = -1;
  let fence = '';

  // Scan up to MAX_PREFIX_LINES for an opening fence.
  // Allowed prefix lines: blank lines and lines starting with # (tags/headings).
  // Any other content before a fence means this is not a frontmatter block.
  for (let i = 0; i < Math.min(lines.length, MAX_PREFIX_LINES); i++) {
    const trimmed = lines[i].trim();
    if (trimmed === '---' || trimmed === '+++') {
      fenceLineIdx = i;
      fence = trimmed;
      break;
    }
    if (trimmed !== '' && !trimmed.startsWith('#')) break;
  }

  if (fenceLineIdx === -1) return null;

  // Find the closing fence — must match the opener type
  let closingLineIdx = -1;
  for (let i = fenceLineIdx + 1; i < lines.length; i++) {
    if (lines[i].trim() === fence) {
      closingLineIdx = i;
      break;
    }
  }

  if (closingLineIdx === -1) return null;

  const prefixLines = lines.slice(0, fenceLineIdx);
  const bodyLines   = lines.slice(fenceLineIdx + 1, closingLineIdx);
  const restLines   = lines.slice(closingLineIdx + 1);

  // Drop a single leading blank line from rest (common after the closing fence)
  if (restLines.length > 0 && restLines[0].trim() === '') {
    restLines.shift();
  }

  return {
    prefix: prefixLines.join('\n'),
    body:   bodyLines.join('\n').trim(),
    rest:   restLines.join('\n'),
    fence,
  };
}

/**
 * Returns true if the given markdown string contains valid frontmatter
 * within the first MAX_PREFIX_LINES lines.
 *
 * @param {string} content
 * @returns {boolean}
 */
export function hasFrontmatter(content) {
  return parseFrontmatter(content) !== null;
}

/**
 * Strips frontmatter from content. If a prefix exists (e.g. #pin on line 0),
 * the prefix is preserved and only the frontmatter block itself is removed.
 * Returns the original string unchanged if no valid frontmatter is found.
 *
 * @param {string} content - Raw markdown string.
 * @returns {string}
 */
export function stripFrontmatter(content) {
  const parsed = parseFrontmatter(content);
  if (!parsed) return content;

  const parts = [];
  if (parsed.prefix) parts.push(parsed.prefix);
  if (parsed.rest)   parts.push(parsed.rest);
  return parts.join('\n');
}
