/*
 * UI: the Documents panel — upload dropzone + uploaded-document list. Wires user
 * actions to documentUpload.js (accepting files) and documentStore.js
 * (remove/rename/re-upload/list). Knows nothing about forms or the renderer.
 *
 * Each uploaded document shows its detected type and extraction status, and can
 * be renamed, removed, or re-uploaded — all inline, in the panel, never through
 * a browser prompt/confirm dialog. onChange fires when the set of documents
 * changes (add/remove) AND when an extraction result arrives, so the Patent
 * Workspace re-consolidates as facts land.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var plural = ns.dom.plural;
  var store = ns.documentStore;
  var upload = ns.documentUpload;
  var accept = ns.fileValidation.ACCEPT_ATTR;

  function formatSize(bytes) {
    if (bytes == null) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  // Extraction status → the badge the user sees, plus a plain-language hint that
  // says what to do about it. No status codes reach the interface.
  var STATUS_UI = {
    pending: { label: "Reading…", cls: "pending",
      hint: "Reading this document…" },
    extracted: { label: "Information found", cls: "ok",
      hint: "We read this document and pulled details from it." },
    no_information: { label: "No details found", cls: "warn",
      hint: "We read this document but didn’t find details we could use." },
    unrecognised: { label: "Couldn’t read", cls: "warn",
      hint: "We couldn’t read this file. Try uploading a PDF or DOCX version." },
    failed: { label: "Not processed", cls: "err",
      hint: "This document wasn’t processed. Check your connection and re-upload." },
  };

  function mountDocumentWorkspace(container, opts) {
    opts = opts || {};
    var onChange = opts.onChange || function () {};

    // Per-row inline UI state (which row is confirming removal / being renamed).
    var confirmingRemoveId = null;
    var editingRenameId = null;

    container.innerHTML = "";
    container.appendChild(el("div", "panel-heading", "Documents"));

    var dropzone = el("div", "upload-zone");
    dropzone.tabIndex = 0;
    dropzone.setAttribute("role", "button");
    dropzone.appendChild(el("div", "upload-zone-text", "Drag & drop documents here, or click to browse"));
    dropzone.appendChild(el("div", "upload-zone-hint", "PDF · Word · Text"));

    var fileInput = el("input");
    fileInput.type = "file";
    fileInput.accept = accept;
    fileInput.multiple = true;
    fileInput.hidden = true;
    dropzone.appendChild(fileInput);
    container.appendChild(dropzone);

    var feedback = el("div", "upload-feedback");
    container.appendChild(feedback);

    var listEl = el("div", "document-list");
    container.appendChild(listEl);

    function showRejects(rejected) {
      feedback.innerHTML = "";
      rejected.forEach(function (r) {
        feedback.appendChild(el("div", "upload-reject", "“" + r.file.name + "” was not added: " + r.reason));
      });
      if (rejected.length) setTimeout(function () { feedback.innerHTML = ""; }, 6000);
    }

    function showNote(message) {
      feedback.innerHTML = "";
      feedback.appendChild(el("div", "upload-note", message));
      setTimeout(function () {
        if (feedback.firstChild && feedback.textContent === message) feedback.innerHTML = "";
      }, 4000);
    }

    function statusBadge(doc) {
      var ui = STATUS_UI[doc.extractionStatus] || STATUS_UI.pending;
      var text = ui.label;
      if (doc.extractionStatus === "extracted" && doc.factCount) {
        text = ui.label + " (" + doc.factCount + ")";
      }
      var badge = el("span", "doc-status doc-status-" + ui.cls, text);
      badge.setAttribute("title", ui.hint);
      return badge;
    }

    function renderList() {
      var docs = store.list();
      listEl.innerHTML = "";
      if (!docs.length) {
        listEl.appendChild(el("div", "document-list-empty", "No documents uploaded yet."));
        return;
      }
      docs.forEach(function (doc) { listEl.appendChild(renderItem(doc)); });
    }

    function renderItem(doc) {
      var item = el("div", "document-item");
      item.appendChild(el("div", "document-icon", "📄"));

      var info = el("div", "document-info");

      if (doc.id === editingRenameId) {
        // Inline rename — replaces the old window.prompt().
        var input = el("input", "doc-rename-input");
        input.type = "text";
        input.value = doc.displayTitle || doc.originalFilename;
        input.setAttribute("aria-label", "Rename document");
        info.appendChild(input);
        item.appendChild(info);

        var save = el("button", "icon-btn", "✓");
        save.type = "button"; save.title = "Save name"; save.setAttribute("aria-label", "Save name");
        var cancel = el("button", "icon-btn", "✕");
        cancel.type = "button"; cancel.title = "Cancel"; cancel.setAttribute("aria-label", "Cancel rename");
        function commitRename() {
          var name = (input.value || "").trim();
          store.rename(doc.id, name || doc.originalFilename);
          editingRenameId = null;
          renderList();
          onChange();
        }
        save.addEventListener("click", commitRename);
        cancel.addEventListener("click", function () { editingRenameId = null; renderList(); });
        input.addEventListener("keydown", function (e) {
          if (e.key === "Enter") { if (e.preventDefault) e.preventDefault(); commitRename(); }
          else if (e.key === "Escape") { editingRenameId = null; renderList(); }
        });
        var editActions = el("div", "document-actions");
        editActions.appendChild(save); editActions.appendChild(cancel);
        item.appendChild(editActions);
        if (input.focus) input.focus();
        return item;
      }

      var title = el("div", "document-title", doc.displayTitle || doc.originalFilename);
      title.title = doc.originalFilename;
      info.appendChild(title);
      if (doc.detectedTypeLabel) info.appendChild(el("div", "document-type", doc.detectedTypeLabel));
      var metaRow = el("div", "document-meta");
      metaRow.appendChild(statusBadge(doc));
      metaRow.appendChild(el("span", "document-size", " · " + formatSize(doc.size)));
      info.appendChild(metaRow);
      item.appendChild(info);

      if (doc.id === confirmingRemoveId) {
        // Two-step inline confirm — replaces the old window.confirm().
        var confirm = el("div", "document-confirm");
        confirm.appendChild(el("span", "document-confirm-q", "Remove?"));
        var yes = el("button", "icon-btn danger", "Remove");
        yes.type = "button"; yes.title = "Remove from workspace";
        yes.addEventListener("click", function () {
          store.remove(doc.id);
          confirmingRemoveId = null;
          renderList();
          onChange();
        });
        var no = el("button", "icon-btn", "Keep");
        no.type = "button"; no.title = "Keep this document";
        no.addEventListener("click", function () { confirmingRemoveId = null; renderList(); });
        confirm.appendChild(yes);
        confirm.appendChild(no);
        item.appendChild(confirm);
        return item;
      }

      var actions = el("div", "document-actions");

      var reuploadBtn = el("button", "icon-btn", "⟳");
      reuploadBtn.type = "button";
      reuploadBtn.title = "Replace this document with a new file";
      reuploadBtn.setAttribute("aria-label", "Re-upload this document");
      reuploadBtn.addEventListener("click", function () { reuploadFor(doc); });

      var renameBtn = el("button", "icon-btn", "✎");
      renameBtn.type = "button";
      renameBtn.title = "Rename";
      renameBtn.setAttribute("aria-label", "Rename document");
      renameBtn.addEventListener("click", function () {
        editingRenameId = doc.id; confirmingRemoveId = null; renderList();
      });

      var removeBtn = el("button", "icon-btn danger", "✕");
      removeBtn.type = "button";
      removeBtn.title = "Remove from workspace";
      removeBtn.setAttribute("aria-label", "Remove from workspace");
      removeBtn.addEventListener("click", function () {
        confirmingRemoveId = doc.id; editingRenameId = null; renderList();
      });

      actions.appendChild(reuploadBtn);
      actions.appendChild(renameBtn);
      actions.appendChild(removeBtn);
      item.appendChild(actions);
      return item;
    }

    function handleFiles(fileList, isReupload) {
      if (!fileList || !fileList.length) return;
      var result = upload.ingestFiles(fileList, {
        onExtracted: function () {
          // A document's facts have landed — refresh its row and let the
          // Patent Workspace re-consolidate.
          renderList();
          onChange();
        },
      });
      showRejects(result.rejected);
      if (result.accepted.length) {
        showNote(isReupload
          ? "Replaced — re-reading the new file…"
          : plural(result.accepted.length, "document") + " added — reading…");
        onChange();
      }
      renderList();
    }

    // Re-upload replaces a document in place: the old record is removed and the
    // new file ingested, so extraction re-runs. A dedicated hidden input avoids
    // disturbing the main dropzone.
    function reuploadFor(doc) {
      var one = el("input");
      one.type = "file";
      one.accept = accept;
      one.hidden = true;
      container.appendChild(one);
      one.addEventListener("change", function () {
        if (one.files && one.files.length) {
          store.remove(doc.id);
          handleFiles(one.files, true);
        }
        container.removeChild(one);
      });
      one.click();
    }

    dropzone.addEventListener("click", function () { fileInput.click(); });
    dropzone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
    });
    fileInput.addEventListener("change", function () {
      handleFiles(fileInput.files, false);
      fileInput.value = "";
    });

    ["dragenter", "dragover"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) { e.preventDefault(); dropzone.classList.add("dragover"); });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) { e.preventDefault(); dropzone.classList.remove("dragover"); });
    });
    dropzone.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      handleFiles(files, false);
    });

    renderList();

    return { refresh: renderList };
  }

  ns.documentWorkspace = { mount: mountDocumentWorkspace };
})(window.PatentFormsApp);
