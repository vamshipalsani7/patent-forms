/*
 * The Patent Workspace screen — the heart of the application.
 *
 * Renders the consolidated view of one patent matter that the backend
 * assembles (workspace.summary): what the uploaded documents say, grouped the
 * way a professional reads a matter, with every value traceable to its source;
 * what core information is still missing; and where the documents disagree.
 *
 * It overlays the user's own decisions (workspaceOverrides) on top of the
 * backend summary at render time — a value typed for a missing field, or the
 * chosen side of a conflict — without ever mutating the extracted facts. The
 * backend owns evidence; the user owns judgement; this view keeps them visibly
 * distinct.
 *
 * Interactions happen inline, in the page: entering a missing value, choosing
 * between conflicting values, and changing that choice are all done with real
 * in-page controls, never a browser prompt/confirm dialog. Pure presentation +
 * interaction: no knowledge of forms, the renderer, or extraction internals,
 * and it never shows a vocabulary key, a sourceType, or any other engine name.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var plural = ns.dom.plural;
  var overrides = ns.workspaceOverrides;

  // Confidence as language, not a bare percentage. A patent agent should not
  // have to decide what "0.72" means; the exact figure stays available on hover
  // for anyone who wants it.
  function confidenceWord(conf) {
    if (conf == null) return "";
    if (conf >= 0.8) return "High confidence";
    if (conf >= 0.6) return "Medium confidence";
    return "Low confidence";
  }

  function findValue(values, chosen) {
    for (var i = 0; i < values.length; i++) {
      if (String(values[i].value) === String(chosen)) return values[i];
    }
    return null;
  }

  /** The muted provenance line for one value, with the exact % kept on hover. */
  function srcEl(value) {
    var parts = [];
    if (value.source_type_label) parts.push(value.source_type_label);
    if (value.source_document) parts.push(value.source_document);
    if (value.page != null) parts.push("p." + value.page);
    if (value.confidence != null) parts.push(confidenceWord(value.confidence));
    var e = el("div", "wsp-value-src", parts.join(" · "));
    if (value.confidence != null) {
      e.setAttribute("title", Math.round(value.confidence * 100) + "% confidence");
    }
    return e;
  }

  function valueRow(value) {
    var row = el("div", "wsp-value");
    row.appendChild(el("div", "wsp-value-text", String(value.value)));
    row.appendChild(srcEl(value));
    return row;
  }

  // ---------------------------------------------------------------- one field

  function renderField(field, ctx) {
    var wrap = el("div", "wsp-field" + (field.conflict ? " wsp-field-conflict" : ""));

    if (!field.conflict) {
      var head = el("div", "wsp-field-head");
      head.appendChild(el("span", "wsp-field-label", field.label));
      wrap.appendChild(head);
      field.values.forEach(function (v) { wrap.appendChild(valueRow(v)); });
      return wrap;
    }

    var chosen = ctx.resolved[field.key];
    var chosenObj = chosen != null ? findValue(field.values, chosen) : null;
    if (chosenObj) {
      buildResolvedConflict(wrap, field, ctx, chosenObj);
    } else {
      buildConflictPicker(wrap, field, ctx);
    }
    return wrap;
  }

  // A field the documents disagree on, awaiting the user's decision.
  function buildConflictPicker(wrap, field, ctx) {
    wrap.innerHTML = "";
    var head = el("div", "wsp-field-head");
    head.appendChild(el("span", "wsp-field-label", field.label));
    head.appendChild(el("span", "wsp-flag wsp-flag-review", "Needs review"));
    wrap.appendChild(head);

    wrap.appendChild(el("div", "wsp-conflict-note",
      "Your documents give different values for this. Choose the one to use:"));

    field.values.forEach(function (v) {
      var opt = el("div", "wsp-conflict-opt");
      var body = el("div", "wsp-conflict-body");
      body.appendChild(el("div", "wsp-value-text", String(v.value)));
      body.appendChild(srcEl(v));

      var pick = el("button", "app-btn ghost", "Use this");
      pick.type = "button";
      pick.addEventListener("click", function () {
        overrides.setResolved(ctx.workspaceId, field.key, v.value);
        ctx.rerender();
      });

      opt.appendChild(body);
      opt.appendChild(pick);
      wrap.appendChild(opt);
    });
  }

  // A conflict the user has already settled — shown resolved, still changeable.
  function buildResolvedConflict(wrap, field, ctx, chosenObj) {
    wrap.innerHTML = "";
    var head = el("div", "wsp-field-head");
    head.appendChild(el("span", "wsp-field-label", field.label));
    head.appendChild(el("span", "wsp-flag wsp-flag-resolved", "Resolved"));
    wrap.appendChild(head);

    wrap.appendChild(valueRow(chosenObj));

    var change = el("button", "wsp-linkbtn", "Change");
    change.type = "button";
    // In-place: reopen the picker without disturbing the rest of the workspace.
    change.addEventListener("click", function () {
      buildConflictPicker(wrap, field, ctx);
    });
    wrap.appendChild(change);
  }

  // -------------------------------------------------------------- one section

  function renderSection(section, ctx) {
    var wrap = el("section", "wsp-section");
    wrap.appendChild(el("h3", "wsp-section-title", section.label));
    section.fields.forEach(function (field) {
      wrap.appendChild(renderField(field, ctx));
    });
    return wrap;
  }

  // ------------------------------------------------------- missing information

  function renderMissing(missing, ctx) {
    var wrap = el("section", "wsp-section wsp-missing");
    wrap.appendChild(el("h3", "wsp-section-title", "Information still needed"));
    wrap.appendChild(el("div", "wsp-missing-note",
      "These details weren’t in your documents. Add them here, or upload a document that has them."));
    missing.forEach(function (item) {
      wrap.appendChild(missingRow(item, ctx));
    });
    return wrap;
  }

  function missingRow(item, ctx) {
    var row = el("div", "wsp-missing-item");
    var provided = ctx.manual[item.key];
    if (provided != null) buildProvided(row, item, ctx, provided);
    else buildNeeded(row, item, ctx);
    return row;
  }

  function buildNeeded(row, item, ctx) {
    row.innerHTML = "";
    row.className = "wsp-missing-item";
    var info = el("div", "wsp-missing-info");
    info.appendChild(el("div", "wsp-field-label", item.label));
    info.appendChild(el("div", "wsp-missing-empty", "Not found in your documents."));
    row.appendChild(info);

    var btn = el("button", "app-btn primary", "Enter value");
    btn.type = "button";
    btn.addEventListener("click", function () { buildEditing(row, item, ctx, ""); });
    row.appendChild(btn);
  }

  function buildProvided(row, item, ctx, value) {
    row.innerHTML = "";
    row.className = "wsp-missing-item provided";
    var info = el("div", "wsp-missing-info");
    info.appendChild(el("div", "wsp-field-label", item.label));
    var v = el("div", "wsp-value");
    v.appendChild(el("div", "wsp-value-text", String(value)));
    v.appendChild(el("div", "wsp-value-src", "Entered by you"));
    info.appendChild(v);
    row.appendChild(info);

    var edit = el("button", "app-btn ghost", "Edit");
    edit.type = "button";
    edit.addEventListener("click", function () { buildEditing(row, item, ctx, value); });
    row.appendChild(edit);
  }

  // Inline entry — replaces the old window.prompt(). Enter saves, Escape cancels.
  function buildEditing(row, item, ctx, current) {
    row.innerHTML = "";
    row.className = "wsp-missing-item editing";
    var info = el("div", "wsp-missing-info");
    info.appendChild(el("div", "wsp-field-label", item.label));

    var input = el("input", "wsp-inline-input");
    input.type = "text";
    input.value = current || "";
    input.setAttribute("placeholder", "Type the value…");
    input.setAttribute("aria-label", item.label);
    info.appendChild(input);
    row.appendChild(info);

    function commit() {
      var val = (input.value || "").trim();
      if (val === "") overrides.clearManual(ctx.workspaceId, item.key);
      else overrides.setManual(ctx.workspaceId, item.key, val);
      ctx.rerender();
    }
    function cancel() {
      if (current) buildProvided(row, item, ctx, current);
      else buildNeeded(row, item, ctx);
    }

    var actions = el("div", "wsp-inline-actions");
    var save = el("button", "app-btn primary", "Save"); save.type = "button";
    var back = el("button", "app-btn ghost", "Cancel"); back.type = "button";
    save.addEventListener("click", commit);
    back.addEventListener("click", cancel);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { if (e.preventDefault) e.preventDefault(); commit(); }
      else if (e.key === "Escape") { cancel(); }
    });
    actions.appendChild(save);
    actions.appendChild(back);
    row.appendChild(actions);

    if (input.focus) input.focus();
  }

  // ----------------------------------------------------- uploaded documents

  var DOC_STATUS_UI = {
    extracted: { label: "Information found", cls: "ok",
      hint: "We read this document and pulled details from it." },
    no_information: { label: "No details found", cls: "warn",
      hint: "We read this document but didn’t find details we could use." },
    unrecognised: { label: "Couldn’t read", cls: "warn",
      hint: "We couldn’t read this file. Try uploading a PDF or DOCX version." },
  };

  function renderDocuments(documents) {
    var wrap = el("section", "wsp-section");
    wrap.appendChild(el("h3", "wsp-section-title", "Uploaded Documents"));
    var list = el("div", "wsp-doc-list");
    documents.forEach(function (doc) {
      var card = el("div", "wsp-doc");
      card.appendChild(el("div", "wsp-doc-icon", "📄"));
      var info = el("div", "wsp-doc-info");
      info.appendChild(el("div", "wsp-doc-name", doc.filename));
      info.appendChild(el("div", "wsp-doc-type", doc.document_type));
      info.appendChild(el("div", "wsp-doc-info-line",
        plural(doc.fact_count, "detail") + " · " + plural(doc.page_count, "page")));
      card.appendChild(info);

      var ui = DOC_STATUS_UI[doc.status] || DOC_STATUS_UI.unrecognised;
      var badge = el("span", "doc-status doc-status-" + ui.cls, ui.label);
      badge.setAttribute("title", ui.hint);
      card.appendChild(badge);
      list.appendChild(card);
    });
    wrap.appendChild(list);
    return wrap;
  }

  // ------------------------------------------------------------------ header

  function renderHeader(summary, unresolved) {
    var head = el("div", "wsp-header");
    head.appendChild(el("h1", "wsp-title", "Patent Workspace"));
    head.appendChild(el("p", "wsp-subtitle",
      "What your uploaded documents tell us about this patent. Review it, fill any gaps, then choose a form to prepare."));

    var s = summary.stats || {};
    var stats = el("div", "wsp-stats");
    stats.appendChild(stat(s.document_count || 0, (s.document_count === 1 ? "document" : "documents")));
    stats.appendChild(stat(s.fact_count || 0, (s.fact_count === 1 ? "detail found" : "details found")));
    if (unresolved > 0) {
      stats.appendChild(stat(unresolved, (unresolved === 1 ? "to review" : "to review"), "warn"));
    }
    if (s.missing_count > 0) {
      stats.appendChild(stat(s.missing_count, "still needed", "muted"));
    }
    head.appendChild(stats);
    return head;
  }

  function stat(n, label, cls) {
    var s = el("div", "wsp-stat" + (cls ? " wsp-stat-" + cls : ""));
    s.appendChild(el("span", "wsp-stat-n", String(n)));
    s.appendChild(el("span", "wsp-stat-l", " " + label));
    return s;
  }

  // ---------------------------------------------------------------- guidance

  // State-aware: unresolved conflicts are the one thing that makes a generated
  // form wrong, so they gate the "ready" message rather than being buried.
  function renderGuidance(state, opts) {
    var wrap = el("section", "wsp-guidance");
    var ctaLabel = "Choose a form";

    if (state.unresolved > 0) {
      wrap.appendChild(el("div", "wsp-guidance-title", "A few things to review first"));
      wrap.appendChild(el("div", "wsp-guidance-body",
        plural(state.unresolved, "field") + " above " +
        (state.unresolved === 1 ? "needs" : "need") +
        " a decision before your forms will be accurate. Resolve " +
        (state.unresolved === 1 ? "it" : "them") + ", then choose a form."));
      ctaLabel = "Choose a form anyway";
    } else {
      wrap.appendChild(el("div", "wsp-guidance-title", "Ready to prepare a form"));
      var body = "Choose an action to generate an IPO form pre-filled with the information above. " +
        "You can review and edit every field before downloading.";
      if (state.missing > 0) {
        body += " (" + plural(state.missing, "detail") + " still needed — you can add " +
          (state.missing === 1 ? "it" : "them") + " above or fill " +
          (state.missing === 1 ? "it" : "them") + " in on the form.)";
      }
      wrap.appendChild(el("div", "wsp-guidance-body", body));
    }

    if (opts && typeof opts.onChooseForm === "function") {
      var btn = el("button", "app-btn primary", ctaLabel);
      btn.type = "button";
      btn.addEventListener("click", function () { opts.onChooseForm(); });
      wrap.appendChild(btn);
    }
    return wrap;
  }

  // -------------------------------------------------------------- empty state

  function renderEmpty() {
    var wrap = el("div", "wsp-empty");
    wrap.appendChild(el("div", "wsp-empty-icon", "📂"));
    wrap.appendChild(el("h1", "wsp-empty-title", "Start a patent matter"));
    wrap.appendChild(el("p", "wsp-empty-body",
      "Upload your patent documents on the left. We read them and build one consolidated view here, ready to turn into filing-ready IPO forms."));

    wrap.appendChild(el("div", "wsp-empty-sub", "Documents you can upload"));
    var list = el("ul", "wsp-empty-list");
    [
      "A specification — complete or provisional",
      "A patent certificate",
      "An assignment deed",
      "A filed form — Form 1, 5, 26, and so on",
      "Priority or PCT documents",
    ].forEach(function (t) { list.appendChild(el("li", null, t)); });
    wrap.appendChild(list);

    wrap.appendChild(el("p", "wsp-empty-hint", "Supported formats: PDF · Word · Text"));
    return wrap;
  }

  // ------------------------------------------------------------------- render

  /**
   * @param {HTMLElement} container
   * @param {object} summary  the /api/workspace response
   * @param {object} [opts]   { workspaceId, onChooseForm }
   */
  function render(container, summary, opts) {
    opts = opts || {};
    var workspaceId = opts.workspaceId || "default";
    container.innerHTML = "";

    if (!summary || !summary.documents || !summary.documents.length) {
      container.appendChild(renderEmpty());
      return;
    }

    var ov = overrides.load(workspaceId);
    var ctx = {
      workspaceId: workspaceId,
      manual: ov.manual,
      resolved: ov.resolved,
      rerender: function () { render(container, summary, opts); },
    };

    // Conflicts the user has not yet resolved drive the header count, the review
    // banner, and whether the workspace reads as ready.
    var unresolved = 0;
    (summary.sections || []).forEach(function (s) {
      s.fields.forEach(function (f) {
        if (f.conflict && ctx.resolved[f.key] == null) unresolved += 1;
      });
    });

    var root = el("div", "wsp");
    root.appendChild(renderHeader(summary, unresolved));

    if (unresolved > 0) {
      root.appendChild(el("div", "wsp-review-banner",
        "Review needed — " + plural(unresolved, "field") +
        " where your documents disagree. Choose the correct value below."));
    }

    (summary.sections || []).forEach(function (section) {
      root.appendChild(renderSection(section, ctx));
    });

    if (summary.missing && summary.missing.length) {
      root.appendChild(renderMissing(summary.missing, ctx));
    }

    root.appendChild(renderDocuments(summary.documents));
    root.appendChild(renderGuidance(
      { unresolved: unresolved, missing: (summary.stats && summary.stats.missing_count) || 0 },
      opts
    ));

    container.appendChild(root);
  }

  ns.workspaceView = { render: render, renderEmpty: renderEmpty };
})(window.PatentFormsApp);
