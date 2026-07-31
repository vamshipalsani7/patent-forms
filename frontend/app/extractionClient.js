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
   * @returns {Promise<object>}  { form_id, workspace_id, suggestions: {...} }
   *                             Always resolves (empty suggestions on failure).
   */
  function getSuggestions(formId, workspaceId) {
    var url = BACKEND_URL + "/api/suggestions/" + encodeURIComponent(formId) +
      "?workspace_id=" + encodeURIComponent(workspaceId);
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

  ns.extractionClient = { uploadForExtraction: uploadForExtraction, getSuggestions: getSuggestions };
})(window.PatentFormsApp);
