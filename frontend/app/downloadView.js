/*
 * The Filing Package screen — the end of the journey.
 *
 * Everything a patent professional needs before filing is already prepared:
 * the official IPO PDF, an editable Word copy, a filing summary and a
 * provenance report. The user is never asked which file to generate — the
 * package exists, and this screen is where they take it.
 *
 * Pure presentation over packageClient. No form logic, no renderer, no internal
 * names: the four documents are described by what they are for, not by how they
 * were produced.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;

  // Order matches the ZIP, so the screen and the archive tell the same story.
  var ITEMS = [
    { part: "pdf", title: "Official IPO PDF",
      note: "The document you file with the Patent Office." },
    { part: "docx", title: "Editable Word document",
      note: "For internal review and any last-minute edits." },
    { part: "summary", title: "Filing Summary",
      note: "A one-page record of what was prepared, and from which documents." },
    { part: "provenance", title: "Provenance Report",
      note: "An audit trail of where each value came from. Not filed with the IPO." },
  ];

  function render(container, opts) {
    opts = opts || {};
    var formNumber = opts.formNumber || "";
    var onDownload = opts.onDownload || function () {};
    var onAnother = opts.onAnother || null;
    var onBack = opts.onBack || null;

    container.innerHTML = "";
    var root = el("div", "pkg");

    var head = el("div", "pkg-head");
    head.appendChild(el("div", "pkg-tick", "✓"));
    head.appendChild(el("h1", "pkg-title", "Filing Package Ready"));
    head.appendChild(el("p", "pkg-sub",
      "Form " + formNumber + " is prepared. Everything below is ready to download."));
    root.appendChild(head);

    // Live status line — what just happened, in plain language.
    var status = el("div", "pkg-status");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");

    function busy(label) {
      status.className = "pkg-status busy";
      status.textContent = "Preparing " + label + "…";
    }
    function done(filename) {
      status.className = "pkg-status ok";
      status.textContent = "Downloaded " + filename;
    }
    function failed(message) {
      status.className = "pkg-status err";
      status.textContent = message;
    }

    function request(part, label, button) {
      busy(label);
      if (button) button.disabled = true;
      onDownload(part, function (result) {
        if (button) button.disabled = false;
        if (result && result.ok) done(result.filename);
        else failed((result && result.error) || "Something went wrong preparing that file.");
      });
    }

    // Primary action: the whole package, which is what most users want.
    var allWrap = el("div", "pkg-all");
    var allBtn = el("button", "app-btn primary pkg-all-btn", "Download All (ZIP)");
    allBtn.type = "button";
    allBtn.addEventListener("click", function () {
      request("zip", "the complete package", allBtn);
    });
    allWrap.appendChild(allBtn);
    allWrap.appendChild(status);
    root.appendChild(allWrap);

    // The four documents, each downloadable on its own.
    var list = el("div", "pkg-list");
    list.appendChild(el("div", "pkg-list-head", "Included"));
    ITEMS.forEach(function (item) {
      var row = el("div", "pkg-item");
      row.appendChild(el("span", "pkg-item-tick", "✓"));
      var info = el("div", "pkg-item-info");
      info.appendChild(el("div", "pkg-item-title", item.title));
      info.appendChild(el("div", "pkg-item-note", item.note));
      row.appendChild(info);

      var btn = el("button", "app-btn ghost pkg-item-btn", "Download");
      btn.type = "button";
      btn.setAttribute("aria-label", "Download " + item.title);
      btn.addEventListener("click", function () { request(item.part, item.title, btn); });
      row.appendChild(btn);
      list.appendChild(row);
    });
    root.appendChild(list);

    var nav = el("div", "pkg-nav");
    if (onBack) {
      var back = el("button", "app-btn ghost", "← Back to comparison");
      back.type = "button";
      back.addEventListener("click", function () { onBack(); });
      nav.appendChild(back);
    }
    if (onAnother) {
      var another = el("button", "app-btn", "Prepare another form");
      another.type = "button";
      another.addEventListener("click", function () { onAnother(); });
      nav.appendChild(another);
    }
    root.appendChild(nav);

    root.appendChild(el("div", "pkg-footnote",
      "Check every value against your source documents before filing. The provenance report is for your records and is not filed with the Patent Office."));

    container.appendChild(root);
  }

  ns.downloadView = { render: render, ITEMS: ITEMS };
})(window.PatentFormsApp);
