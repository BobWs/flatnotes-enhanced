// Patch: note title paths should NOT encode slashes since we use {title:path} on the server
// Replace encodeURIComponent(title) calls in api.js with this helper
export function encodeNotePath(title) {
  return title.split("/").map(encodeURIComponent).join("/");
}
