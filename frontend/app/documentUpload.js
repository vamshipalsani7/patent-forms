/*
 * Upload: turns raw File objects into validated document metadata, persists
 * them via documentStore, and ships their bytes to the backend for extraction.
 * Deliberately has no DOM/dropzone code of its own (that lives in
 * documentWorkspace.js).
 *
 * Never reads file bytes for storage (no FileReader/arrayBuffer) — only `.name`,
 * `.size`, `.type` — and never writes back to the File. The original file on the
 * user's device is untouched; only its metadata is stored. The bytes are handed
 * straight to the backend and not retained here.
 *
 * Extraction lifecycle recorded per document:
 *   pending        — bytes sent, awaiting the backend
 *   extracted      — backend found usable facts
 *   no_information — recognised document, but nothing we needed was in it
 *   unrecognised   — could not read the file / type not recognised
 *   failed         — the request itself failed (backend offline, network)
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var isSupported = ns.fileValidation.isSupported;
  var store = ns.documentStore;

  function makeId() {
    return "doc_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  /** Map a backend extraction result to one of our lifecycle status codes. */
  function statusFromResult(result) {
    if (!result || result.error) return "failed";
    var facts = result.facts || [];
    if (facts.length) return "extracted";
    // A recognised type that yielded nothing vs. an unreadable/unknown file.
    if (result.source_type && result.source_type !== "unknown" && result.source_type !== "generic") {
      return "no_information";
    }
    return "unrecognised";
  }

  /**
   * @param {FileList|File[]} files
   * @param {object} [opts]
   * @param {function} [opts.onExtracted]  called (documentId, status) after each
   *        document's extraction resolves, so the UI can refresh that row.
   * @returns {{ accepted: object[], rejected: {file: File, reason: string}[] }}
   */
  function ingestFiles(files, opts) {
    opts = opts || {};
    var onExtracted = opts.onExtracted || function () {};
    var accepted = [];
    var rejected = [];

    Array.prototype.forEach.call(files || [], function (file) {
      if (!isSupported(file)) {
        rejected.push({
          file: file,
          reason: "Unsupported file type. Upload a PDF, DOCX, DOC or TXT document.",
        });
        return;
      }
      var meta = {
        id: makeId(),
        originalFilename: file.name,
        displayTitle: file.name,
        size: file.size,
        uploadedAt: new Date().toISOString(),
        workspaceId: store.DEFAULT_WORKSPACE,
        extractionStatus: "pending",
        detectedType: null,
        detectedTypeLabel: null,
        factCount: 0,
      };
      store.add(meta);
      accepted.push(meta);

      // Fire-and-forget: send bytes to backend for extraction. The File object
      // is available only here (synchronous ingest loop) — localStorage cannot
      // hold bytes, so we ship them immediately. The workspace travels with the
      // document: the backend files it there and nowhere else.
      ns.extractionClient.uploadForExtraction(meta.id, file, meta.workspaceId)
        .then(function (result) {
          var status = statusFromResult(result);
          store.update(meta.id, {
            extractionStatus: status,
            detectedType: result && result.source_type ? result.source_type : null,
            detectedTypeLabel: result && result.source_type_label ? result.source_type_label : null,
            factCount: result && result.facts ? result.facts.length : 0,
          });
          onExtracted(meta.id, status);
        });
    });

    return { accepted: accepted, rejected: rejected };
  }

  ns.documentUpload = { ingestFiles: ingestFiles, statusFromResult: statusFromResult };
})(window.PatentFormsApp);
