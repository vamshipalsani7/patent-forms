/*
 * UI: the Documents panel — upload dropzone + uploaded-PDF list. Wires user
 * actions to documentUpload.js (accepting files) and documentStore.js
 * (remove/rename/list). Knows nothing about forms, the renderer, or
 * mainArea.js — completely independent, as required.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var store = ns.documentStore;
  var upload = ns.documentUpload;

  function formatSize(bytes) {
    if (bytes == null) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function formatTime(iso) {
    try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
  }

  function mountDocumentWorkspace(container, opts) {
    opts = opts || {};
    var onChange = opts.onChange || function () {};

    container.innerHTML = "";
    container.appendChild(el("div", "panel-heading", "Documents"));

    var dropzone = el("div", "upload-zone");
    dropzone.tabIndex = 0;
    dropzone.setAttribute("role", "button");
    dropzone.appendChild(el("div", "upload-zone-text", "Drag & drop PDFs here, or click to browse"));

    var fileInput = el("input");
    fileInput.type = "file";
    fileInput.accept = "application/pdf,.pdf";
    fileInput.multiple = true;
    fileInput.hidden = true;
    dropzone.appendChild(fileInput);
    container.appendChild(dropzone);

    var feedback = el("div", "upload-feedback");
    container.appendChild(feedback);

    var listEl = el("div", "document-list");
    container.appendChild(listEl);

    function showFeedback(rejected) {
      feedback.innerHTML = "";
      if (!rejected.length) return;
      rejected.forEach(function (r) {
        feedback.appendChild(el("div", "upload-reject", "“" + r.file.name + "” was not added: " + r.reason));
      });
      setTimeout(function () { feedback.innerHTML = ""; }, 6000);
    }

    function renderList() {
      var docs = store.list();
      listEl.innerHTML = "";
      if (!docs.length) {
        listEl.appendChild(el("div", "document-list-empty", "No documents uploaded yet."));
        return;
      }
      docs.forEach(function (doc) {
        var item = el("div", "document-item");
        item.appendChild(el("div", "document-icon", "📄")); // 📄

        var info = el("div", "document-info");
        var title = el("div", "document-title", doc.displayTitle || doc.originalFilename);
        title.title = doc.originalFilename;
        info.appendChild(title);
        info.appendChild(el("div", "document-meta", formatSize(doc.size) + " · " + formatTime(doc.uploadedAt)));
        item.appendChild(info);

        var actions = el("div", "document-actions");

        var renameBtn = el("button", "icon-btn", "✎"); // ✎
        renameBtn.type = "button";
        renameBtn.title = "Rename display title";
        renameBtn.setAttribute("aria-label", "Rename display title");
        renameBtn.addEventListener("click", function () {
          var next = window.prompt("Display title for this document:", doc.displayTitle || doc.originalFilename);
          if (next === null) return; // cancelled
          var trimmed = next.trim();
          store.rename(doc.id, trimmed || doc.originalFilename);
          renderList();
          onChange();
        });

        var removeBtn = el("button", "icon-btn danger", "✕"); // ✕
        removeBtn.type = "button";
        removeBtn.title = "Remove from workspace";
        removeBtn.setAttribute("aria-label", "Remove from workspace");
        removeBtn.addEventListener("click", function () {
          var label = doc.displayTitle || doc.originalFilename;
          if (!window.confirm(
            "Remove “" + label + "” from the workspace?\n\n" +
            "This only removes it from Patent Forms — the original file on your device is not affected."
          )) return;
          store.remove(doc.id);
          renderList();
          onChange();
        });

        actions.appendChild(renameBtn);
        actions.appendChild(removeBtn);
        item.appendChild(actions);

        listEl.appendChild(item);
      });
    }

    function handleFiles(fileList) {
      if (!fileList || !fileList.length) return;
      var result = upload.ingestFiles(fileList);
      showFeedback(result.rejected);
      renderList();
      if (result.accepted.length) onChange();
    }

    dropzone.addEventListener("click", function () { fileInput.click(); });
    dropzone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
    });
    fileInput.addEventListener("change", function () {
      handleFiles(fileInput.files);
      fileInput.value = ""; // allow re-selecting the same file later
    });

    ["dragenter", "dragover"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) { e.preventDefault(); dropzone.classList.add("dragover"); });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) { e.preventDefault(); dropzone.classList.remove("dragover"); });
    });
    dropzone.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      handleFiles(files);
    });

    renderList();

    return { refresh: renderList };
  }

  ns.documentWorkspace = { mount: mountDocumentWorkspace };
})(window.PatentFormsApp);
