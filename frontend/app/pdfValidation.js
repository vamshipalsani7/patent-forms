/*
 * Pure file-type validation. No DOM, no storage, no upload orchestration —
 * kept separate so a future Extraction Engine (or anything else that needs
 * to check "is this an acceptable PDF") can reuse it without pulling in
 * documentUpload.js's persistence side effects.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  function isPdf(file) {
    if (!file) return false;
    var name = (file.name || "").toLowerCase();
    var typeOk = file.type === "application/pdf";
    var extOk = name.slice(-4) === ".pdf";
    // Some browsers/OSes report an empty `type` for local files, so the
    // extension is checked too rather than trusting MIME type alone.
    return typeOk || extOk;
  }

  ns.pdfValidation = { isPdf: isPdf };
})(window.PatentFormsApp);
