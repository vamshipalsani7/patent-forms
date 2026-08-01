/*
 * Pure file-type validation for uploaded SOURCE documents. No DOM, no storage,
 * no upload orchestration — kept separate so anything that needs to ask "can we
 * accept this document?" can reuse it without pulling in persistence.
 *
 * The product accepts the formats patent professionals actually hold — PDF,
 * Word (.docx / .doc) and plain text — not only PDF. A patent specification is
 * as often a Word file as a PDF, and forcing a manual "print to PDF" step first
 * is exactly the friction this milestone removes.
 *
 * Validation is by file EXTENSION. Browsers report the MIME type of local Word
 * and text files inconsistently (often blank, or application/octet-stream), so
 * the extension is the authority and the type is not trusted on its own.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  // Kept in step with backend extractor.document_reader.SUPPORTED_EXTENSIONS.
  var SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt"];

  // The `accept` attribute for the hidden <input type=file>. Includes the MIME
  // types too so a compliant OS file picker filters helpfully, but acceptance is
  // still decided by isSupported() below.
  var ACCEPT_ATTR = [
    ".pdf", ".docx", ".doc", ".txt",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
  ].join(",");

  function extensionOf(file) {
    var name = (file && file.name ? file.name : "").toLowerCase();
    var dot = name.lastIndexOf(".");
    return dot >= 0 ? name.slice(dot) : "";
  }

  function isSupported(file) {
    if (!file) return false;
    return SUPPORTED_EXTENSIONS.indexOf(extensionOf(file)) >= 0;
  }

  // Retained so any caller still asking specifically "is this a PDF?" keeps
  // working; isSupported is the check the uploader now uses.
  function isPdf(file) {
    return extensionOf(file) === ".pdf" || (file && file.type === "application/pdf");
  }

  ns.fileValidation = {
    isSupported: isSupported,
    isPdf: isPdf,
    extensionOf: extensionOf,
    SUPPORTED_EXTENSIONS: SUPPORTED_EXTENSIONS,
    ACCEPT_ATTR: ACCEPT_ATTR,
  };
})(window.PatentFormsApp);
