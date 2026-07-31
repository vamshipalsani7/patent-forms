/*
 * Upload: turns raw File objects into validated document metadata and
 * persists them via documentStore. Deliberately has no DOM/dropzone code of
 * its own (that lives in documentWorkspace.js) — this module is the seam a
 * future Extraction Engine will hook into (see the "Future compatibility"
 * notes in README.md): it already has the raw File and the freshly-created
 * metadata id at the moment of ingest, before anything is rendered.
 *
 * Never reads file bytes (no FileReader/arrayBuffer) — only `.name`,
 * `.size`, `.type` — and never writes back to the File. The original file
 * on the user's device is untouched; only its metadata is stored.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var isPdf = ns.pdfValidation.isPdf;
  var store = ns.documentStore;

  function makeId() {
    return "doc_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  /**
   * @param {FileList|File[]} files
   * @returns {{ accepted: object[], rejected: {file: File, reason: string}[] }}
   */
  function ingestFiles(files) {
    var accepted = [];
    var rejected = [];

    Array.prototype.forEach.call(files || [], function (file) {
      if (!isPdf(file)) {
        rejected.push({ file: file, reason: "Only PDF files are accepted." });
        return;
      }
      var meta = {
        id: makeId(),
        originalFilename: file.name,
        displayTitle: file.name,
        size: file.size,
        uploadedAt: new Date().toISOString(),
        workspaceId: store.DEFAULT_WORKSPACE,
      };
      store.add(meta);
      accepted.push(meta);

      // Fire-and-forget: send bytes to backend for extraction.
      // The File object is available only here (synchronous ingest loop) —
      // localStorage cannot hold bytes, so we ship them immediately.
      // The workspace travels with the document: the backend files it there
      // and nowhere else. Failure is silent; the form remains fully usable.
      ns.extractionClient.uploadForExtraction(meta.id, file, meta.workspaceId)
        .then(function (result) {
          if (result && !result.error) {
            console.info("[upload] extraction complete:", meta.id, "→", result.source_type, "(" + (result.facts || []).length + " facts)");
          }
        });
    });

    return { accepted: accepted, rejected: rejected };
  }

  ns.documentUpload = { ingestFiles: ingestFiles };
})(window.PatentFormsApp);
