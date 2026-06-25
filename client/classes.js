import router from "./router.js";
import { formatDate, formatDateIso } from "./dateFormatter.js";

class Note {
  constructor(note) {
    this.title = note?.title;
    this.lastModified = note?.lastModified;
    this.content = note?.content;
    // ISO 8601 strings from sidecar metadata; null for pre-existing notes
    this.created = note?.created ?? null;
    this.updated = note?.updated ?? null;
  }

  get lastModifiedAsDate() {
    return new Date(this.lastModified * 1000);
  }

  /**
   * Human-readable last-modified string, respecting the user's locale/style
   * preferences from the global store.  Includes date + time.
   */
  get lastModifiedAsString() {
    return formatDate(this.lastModified, true);
  }

  /**
   * Format an ISO 8601 timestamp for display (e.g. created/updated metadata).
   * Respects the user's locale/style preferences.  Always includes time.
   *
   * Returns null for falsy input so callers can use v-if guards as before.
   */
  static formatTimestamp(iso) {
    if (!iso) return null;
    return formatDateIso(iso);
  }

  get createdAsString() {
    return Note.formatTimestamp(this.created);
  }

  get updatedAsString() {
    return Note.formatTimestamp(this.updated);
  }
}

class SearchResult extends Note {
  constructor(searchResult) {
    super(searchResult);
    this.score = searchResult.score;
    this.titleHighlights = searchResult.titleHighlights;
    this.contentHighlights = searchResult.contentHighlights;
    this.tagMatches = searchResult.tagMatches;
  }

  get titleHighlightsOrTitle() {
    return this.titleHighlights ? this.titleHighlights : this.title;
  }

  get includesHighlights() {
    if (
      this.titleHighlights ||
      this.contentHighlights ||
      (this.tagMatches != null && this.tagMatches.length)
    ) {
      return true;
    } else {
      return false;
    }
  }
}

export { Note, SearchResult };
