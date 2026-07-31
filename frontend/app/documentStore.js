/*
 * Storage: persistence for uploaded-document METADATA only. Never touches
 * file contents/bytes — only the small record shape below. No DOM, no
 * knowledge of the renderer, no knowledge of forms. Mirrors formState.js's
 * localStorage pattern for consistency with the rest of the app shell.
 *
 * Record shape:
 *   { id, originalFilename, displayTitle, size, uploadedAt, workspaceId }
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var STORAGE_KEY = "patentforms.documents";

  // The workspace every document lands in until the UI offers more than one.
  // Exported so documentUpload.js and app.js agree on the value rather than
  // each hardcoding it — a mismatch would silently split one patent's
  // documents across two workspaces and suppress its suggestions.
  var DEFAULT_WORKSPACE = "default";

  function loadAll() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.warn("[documentStore] failed to read stored documents", e);
      return [];
    }
  }

  function persist(list) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  function list() {
    return loadAll();
  }

  function add(meta) {
    var all = loadAll();
    all.push(meta);
    persist(all);
    return meta;
  }

  function remove(id) {
    var all = loadAll().filter(function (d) { return d.id !== id; });
    persist(all);
  }

  function rename(id, displayTitle) {
    var all = loadAll();
    var doc = all.filter(function (d) { return d.id === id; })[0];
    if (!doc) return null;
    doc.displayTitle = displayTitle;
    persist(all);
    return doc;
  }

  function get(id) {
    return loadAll().filter(function (d) { return d.id === id; })[0] || null;
  }

  function listByWorkspace(workspaceId) {
    return loadAll().filter(function (d) { return d.workspaceId === workspaceId; });
  }

  ns.documentStore = {
    list: list, add: add, remove: remove, rename: rename, get: get,
    listByWorkspace: listByWorkspace,
    DEFAULT_WORKSPACE: DEFAULT_WORKSPACE
  };
})(window.PatentFormsApp);
