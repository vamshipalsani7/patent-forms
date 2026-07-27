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
   * Upload a PDF file for extraction.
   * @param {string} documentId  — the id stored in documentStore
   * @param {File}   file        — the raw File object from drag/drop
   * @returns {Promise<object|null>}  DocumentExtract JSON, or null on failure
   */
  function uploadForExtraction(documentId, file) {
    var body = new FormData();
    body.append("document_id", documentId);
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
   * Fetch autofill suggestions for a form from the backend.
   * @param {string} formId  — e.g. 'form_03'
   * @returns {Promise<object>}  { form_id, suggestions: { fieldPath: { value, fact } } }
   *                             Always resolves (empty suggestions on failure).
   */
  function getSuggestions(formId) {
    return fetch(BACKEND_URL + "/api/suggestions/" + formId)
      .then(function (res) {
        if (!res.ok) {
          console.warn("[extraction] GET /api/suggestions/" + formId + " returned " + res.status);
          return { form_id: formId, suggestions: {} };
        }
        return res.json();
      })
      .catch(function (err) {
        console.warn("[extraction] getSuggestions failed:", err.message);
        return { form_id: formId, suggestions: {} };
      });
  }

  ns.extractionClient = { uploadForExtraction: uploadForExtraction, getSuggestions: getSuggestions };
})(window.PatentFormsApp);
