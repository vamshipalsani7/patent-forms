/*
 * packageClient.js — requesting filing-package documents from the backend and
 * saving them to the user's device.
 *
 * The backend prepares the whole package on every request and returns the part
 * that was asked for, with the filename it should be saved as. This module only
 * carries the request and hands the returned file to the browser.
 *
 * It never throws: a failure resolves to { ok:false, error }, so the download
 * screen can say what went wrong instead of leaving a dead button.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var BACKEND_URL = "http://localhost:8000";

  /** Filename the server asked us to save as, from Content-Disposition. */
  function filenameFrom(response, fallback) {
    var header = response.headers && response.headers.get
      ? response.headers.get("Content-Disposition") : null;
    if (header) {
      var match = /filename\s*=\s*"?([^";]+)"?/i.exec(header);
      if (match && match[1]) return match[1].trim();
    }
    return fallback;
  }

  /** Hand a blob to the browser as a download. */
  function saveBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    // Firefox needs the anchor in the document for a programmatic click.
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    // Revoke on the next tick: revoking synchronously can cancel the download.
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  /**
   * Download one part of the filing package.
   * @param {string} formId   e.g. 'form_18'
   * @param {string} part     'zip' | 'pdf' | 'docx' | 'summary' | 'provenance'
   * @param {object} payload  { workspace_id, values, visible_paths, counts, overrides }
   * @returns {Promise<{ok:boolean, filename?:string, error?:string}>}
   */
  function download(formId, part, payload) {
    var url = BACKEND_URL + "/api/package/" + encodeURIComponent(formId) +
      "?part=" + encodeURIComponent(part);

    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }).then(function (response) {
      if (!response.ok) {
        return { ok: false, error: "The filing package could not be prepared (status " + response.status + ")." };
      }
      return response.blob().then(function (blob) {
        var filename = filenameFrom(response, formId + "." + part);
        saveBlob(blob, filename);
        return { ok: true, filename: filename };
      });
    }).catch(function (err) {
      return { ok: false, error: "Could not reach the service. " + (err && err.message ? err.message : "") };
    });
  }

  ns.packageClient = { download: download, saveBlob: saveBlob, filenameFrom: filenameFrom };
})(window.PatentFormsApp);
