/*
 * Storage: persistence for uploaded-document METADATA only. Never touches
 * file contents/bytes — only the small record shape below. No DOM, no
 * knowledge of the renderer, no knowledge of forms. Mirrors formState.js's
 * localStorage pattern for consistency with the rest of the app shell.
 *
 * Record shape:
 *   { id, originalFilename, displayTitle, size, uploadedAt, workspaceId,
 *     extractionStatus, detectedType, detectedTypeLabel, factCount }
 *
 * The extraction fields start empty and are filled in by documentUpload.js once
 * the backend responds — they let the Documents list show each document's
 * detected type and extraction status without re-querying. They are a cache of
 * the backend's answer, never the source of truth (the backend is).
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

  /**
   * Merge a partial patch into one document's record (e.g. extraction result).
   * Unknown ids are ignored — a document removed while its extraction was still
   * in flight must not be silently re-added by a late-arriving update.
   * @param {string} id
   * @param {object} patch  keys to overwrite on the record
   * @returns {object|null} the updated record, or null if the id is unknown
   */
  function update(id, patch) {
    var all = loadAll();
    var doc = all.filter(function (d) { return d.id === id; })[0];
    if (!doc) return null;
    Object.keys(patch || {}).forEach(function (k) { doc[k] = patch[k]; });
    persist(all);
    return doc;
  }

  function get(id) {
    return loadAll().filter(function (d) { return d.id === id; })[0] || null;
  }

  /**
   * Reconcile the local record set against the backend's list of documents for
   * this workspace, making the backend the single source of truth for WHICH
   * documents exist. Local records are a per-browser cache/annotation layer
   * (display titles, in-flight status) on top of it.
   *
   *   - A backend document not held locally is added, so it shows in the sidebar
   *     (e.g. uploaded from another browser, or after localStorage was cleared).
   *   - A document held both places has its detected type and extraction status
   *     refreshed from the backend, but keeps its local display title.
   *   - A local document the backend does not know is dropped — UNLESS it is
   *     still 'pending' (its upload/extraction is in flight and simply hasn't
   *     reached the backend yet). This is what removes the sidebar/workspace
   *     desync without deleting a document mid-upload.
   *
   * @param {object[]} backendDocs  the workspace summary's `documents` array:
   *        { document_id, filename, document_type, source_type, status, fact_count }
   * @returns {object[]} the reconciled local list
   */
  function reconcile(backendDocs) {
    var backend = Array.isArray(backendDocs) ? backendDocs : [];
    var backendById = {};
    backend.forEach(function (d) { backendById[d.document_id] = d; });

    var all = loadAll();
    var localById = {};
    all.forEach(function (d) { localById[d.id] = d; });

    // Upsert every backend document into the local set.
    backend.forEach(function (bd) {
      var existing = localById[bd.document_id];
      if (existing) {
        existing.extractionStatus = bd.status;
        existing.detectedType = bd.source_type || null;
        existing.detectedTypeLabel = bd.document_type || null;
        existing.factCount = bd.fact_count || 0;
        if (!existing.originalFilename) existing.originalFilename = bd.filename;
      } else {
        all.push({
          id: bd.document_id,
          originalFilename: bd.filename,
          displayTitle: bd.filename,
          size: null,
          uploadedAt: new Date().toISOString(),
          workspaceId: DEFAULT_WORKSPACE,
          extractionStatus: bd.status,
          detectedType: bd.source_type || null,
          detectedTypeLabel: bd.document_type || null,
          factCount: bd.fact_count || 0,
        });
      }
    });

    // Drop local records the backend does not have, unless still uploading.
    all = all.filter(function (d) {
      return backendById[d.id] || d.extractionStatus === "pending";
    });

    persist(all);
    return all;
  }

  function listByWorkspace(workspaceId) {
    return loadAll().filter(function (d) { return d.workspaceId === workspaceId; });
  }

  ns.documentStore = {
    list: list, add: add, remove: remove, rename: rename, update: update, get: get,
    reconcile: reconcile,
    listByWorkspace: listByWorkspace,
    DEFAULT_WORKSPACE: DEFAULT_WORKSPACE
  };
})(window.PatentFormsApp);
