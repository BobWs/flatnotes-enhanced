/**
 * variables.js — list of Dataview-style variables supported in notes.
 *
 * Variables are replaced in the viewer (ToastViewer) by looking at
 * the current note's metadata. In the editor, they are autocompleted
 * when the user types `{{` followed by the start of a variable name.
 */
export const VARIABLES = [
  'title',    // note title (filename without folder)
  'created',  // creation timestamp
  'updated',  // last modification timestamp
  'folder',   // folder path (relative to root)
  'tags',     // comma-separated list of tags
];