/**
 * extractionClient.js — HTTP layer over the backend extraction API.
 *
 * All functions return Promises and never throw; callers get empty results
 * on failure so the form stays usable when the backend is offline.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var BACKEND_URL = "http://localhost:8000";

  /**
   * Upload a PDF file for extraction into one workspace.
   * @param {string} documentId   — the id stored in documentStore
   * @param {File}   file         — the raw File object from drag/drop
   * @param {string} workspaceId  — the patent matter this document belongs to
   * @returns {Promise<object|null>}  DocumentExtract JSON, or null on failure
   */
  function uploadForExtraction(documentId, file, workspaceId) {
    var body = new FormData();
    body.append("document_id", documentId);
    body.append("workspace_id", workspaceId);
    body.append("file", file);

    return fetch(BACKEND_URL + "/api/extract", { method: "POST", body: body })
      .then(function (res) {
        if (!res.ok) {
          console.warn("[extraction] POST /api/extract returned " + res.status);
          return null;
        }
        return res.json();
      })
      .catch(function (err) {
        // Backend not running or network error — fail silently
        console.warn("[extraction] uploadForExtraction failed:", err.message);
        return null;
      });
  }

  /**
   * Fetch autofill suggestions for a form, scoped to one workspace.
   * @param {string} formId       — e.g. 'form_03'
   * @param {string} workspaceId  — only this workspace's documents are consulted
   * @param {object} [overrides]  — the user's Patent Workspace decisions,
   *                                {vocabKey: value}; the form pre-fills with
   *                                these over the raw extractions.
   * @returns {Promise<object>}  { form_id, workspace_id, suggestions: {...} }
   *                             Always resolves (empty suggestions on failure).
   */
  function getSuggestions(formId, workspaceId, overrides) {
    var url = BACKEND_URL + "/api/suggestions/" + encodeURIComponent(formId) +
      "?workspace_id=" + encodeURIComponent(workspaceId);
    if (overrides && Object.keys(overrides).length) {
      url += "&overrides=" + encodeURIComponent(JSON.stringify(overrides));
    }
    var empty = { form_id: formId, workspace_id: workspaceId, suggestions: {} };

    return fetch(url)
      .then(function (res) {
        if (!res.ok) {
          console.warn("[extraction] GET /api/suggestions/" + formId + " returned " + res.status);
          return empty;
        }
        return res.json();
      })
      .catch(function (err) {
        console.warn("[extraction] getSuggestions failed:", err.message);
        return empty;
      });
  }

  /**
   * Fetch the consolidated Patent Workspace summary for one matter.
   * @param {string} workspaceId
   * @returns {Promise<object>}  the workspace summary, or an empty-but-valid
   *                             shape on failure (so the UI still renders).
   */
  function getWorkspace(workspaceId) {
    var url = BACKEND_URL + "/api/workspace/" + encodeURIComponent(workspaceId);
    var empty = {
      workspace_id: workspaceId, documents: [], sections: [], missing: [],
      stats: { document_count: 0, fact_count: 0, conflict_count: 0, missing_count: 0 },
      unavailable: true,
    };

    return fetch(url)
      .then(function (res) {
        if (!res.ok) {
          console.warn("[extraction] GET /api/workspace/" + workspaceId + " returned " + res.status);
          return empty;
        }
        return res.json();
      })
      .catch(function (err) {
        console.warn("[extraction] getWorkspace failed:", err.message);
        return empty;
      });
  }

  ns.extractionClient = {
    uploadForExtraction: uploadForExtraction,
    getSuggestions: getSuggestions,
    getWorkspace: getWorkspace,
  };
})(window.PatentFormsApp);
