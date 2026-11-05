/*
 * Official IPO Comparison — the trust-verification screen.
 *
 * One question: "Is my generated form ready to file?" It shows the form the way
 * the official IPO layout reads (field labels, in section order) beside the
 * completed values, so a patent professional can confirm, field by field, that
 * the generated form faithfully represents the official one.
 *
 * It is NOT a PDF diff and NOT a second form renderer. It is a read-only,
 * field-by-field projection of the SAME data the AI Review computed — the review
 * layer's snapshot — so the two screens can never disagree about what is filled,
 * edited, missing, or handled at filing. Nothing here is editable; correcting a
 * value means returning to Review.
 *
 * It never shows a vocabulary key, a sourceType, a confidence percentage, a
 * mapper path, or any internal identifier. Only human language.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var plural = ns.dom.plural;

  // How each field's review status reads on the comparison. The four visual
  // families match the spec: AI-filled (green), user (blue), missing (amber),
  // office/at-filing (grey).
  var STATUS_UI = {
    from_document:          { cls: "ai",      chip: "Filled automatically" },
    entered_by_you:         { cls: "user",    chip: "Entered by you" },
    edited_by_you:          { cls: "user",    chip: "Edited by you" },
    selected_during_review: { cls: "user",    chip: "Selected during review" },
    missing:                { cls: "missing", chip: "Return to Review" },
    empty_optional:         { cls: "neutral", chip: "" },
    exempt:                 { cls: "office",  chip: "Patent Office Use" },
  };

  // Grey ("office") fields get a more accurate sub-label from why they are exempt.
  var EXEMPT_CHIP = {
    office: "Patent Office Use",
    derived: "Patent Office Use",
    signature: "Signed at filing",
    signing_date: "Signed at filing",
  };

  function cellFor(field) {
    var ui = STATUS_UI[field.status] || STATUS_UI.neutral || { cls: "neutral", chip: "" };
    var cls = ui.cls;
    var chipText = ui.chip;
    var valueText;

    if (field.status === "missing") {
      valueText = "Missing";
    } else if (field.status === "exempt") {
      chipText = EXEMPT_CHIP[field.exemptReason] || "Patent Office Use";
      valueText = field.value && String(field.value).trim() ? field.value : "—";
    } else if (field.value && String(field.value).trim()) {
      valueText = field.value;
    } else {
      valueText = "—";
      cls = "neutral";
      chipText = "";
    }

    var cell = el("div", "cmp-cell cmp-generated cmp-" + cls);
    cell.appendChild(el("div", "cmp-value", String(valueText)));
    if (chipText) cell.appendChild(el("span", "cmp-chip cmp-chip-" + cls, chipText));
    return cell;
  }

  // Group the flat snapshot into sections, preserving first-seen order.
  function groupBySection(snapshot) {
    var order = [];
    var byTitle = {};
    snapshot.forEach(function (f) {
      var key = f.section || "";
      if (!(key in byTitle)) { byTitle[key] = []; order.push(key); }
      byTitle[key].push(f);
    });
    return order.map(function (title) { return { title: title, fields: byTitle[title] }; });
  }

  function renderGrid(snapshot) {
    var grid = el("div", "cmp-grid");
    grid.appendChild(el("div", "cmp-col-head cmp-col-official", "Official IPO Form"));
    grid.appendChild(el("div", "cmp-col-head cmp-col-generated", "Generated Form"));

    groupBySection(snapshot).forEach(function (section) {
      if (section.title) grid.appendChild(el("div", "cmp-section", section.title));
      section.fields.forEach(function (field) {
        grid.appendChild(el("div", "cmp-cell cmp-official", field.label));
        grid.appendChild(cellFor(field));
      });
    });
    return grid;
  }

  function renderHeader(opts) {
    var s = opts.summary || {};
    var missing = s.missing || 0;

    var head = el("div", "cmp-header");
    var top = el("div", "cmp-title");
    top.appendChild(el("div", "cmp-form-number", "Form " + opts.formNumber));
    top.appendChild(el("div", "cmp-form-name", opts.officialName || ""));
    top.appendChild(el("div", "cmp-verified", "✓ Official layout verified"));
    head.appendChild(top);

    var stats = el("div", "cmp-stats");
    stats.appendChild(stat(s.autoFilled || 0, (s.autoFilled === 1 ? "field completed automatically" : "fields completed automatically")));
    stats.appendChild(stat(s.edited || 0, "edited by you"));
    stats.appendChild(stat(missing, "missing", missing > 0 ? "warn" : null));
    head.appendChild(stats);

    // Trust line: ready, or a nudge back to Review.
    if (missing === 0) {
      head.appendChild(el("div", "cmp-ready", "Ready for export"));
    } else {
      head.appendChild(el("div", "cmp-notready",
        plural(missing, "field") + " still missing — return to Review to complete " +
        (missing === 1 ? "it" : "them") + "."));
    }

    // Navigation.
    var nav = el("div", "cmp-nav");
    var back = el("button", "app-btn ghost", "← Back to Review");
    back.type = "button";
    back.addEventListener("click", function () { if (opts.onBack) opts.onBack(); });
    nav.appendChild(back);

    var cont = el("button", "app-btn primary", "Continue to Export →");
    cont.type = "button";
    if (missing > 0) {
      cont.disabled = true;
      cont.title = "Complete the missing fields in Review first.";
      var why = el("span", "cmp-nav-why", "Complete the missing fields to continue.");
      nav.appendChild(cont);
      nav.appendChild(why);
    } else {
      cont.addEventListener("click", function () { if (opts.onContinueExport) opts.onContinueExport(); });
      nav.appendChild(cont);
    }
    head.appendChild(nav);
    return head;
  }

  function stat(n, label, cls) {
    var s = el("div", "cmp-stat" + (cls ? " cmp-stat-" + cls : ""));
    s.appendChild(el("span", "cmp-stat-n", String(n)));
    s.appendChild(el("span", "cmp-stat-l", " " + label));
    return s;
  }

  function renderEmpty(onBack) {
    var wrap = el("div", "cmp-empty");
    wrap.appendChild(el("div", "cmp-empty-icon", "🗎"));
    wrap.appendChild(el("h1", "cmp-empty-title", "Comparison unavailable"));
    wrap.appendChild(el("p", "cmp-empty-body",
      "The generated form could not be verified. Please return to Review and try again."));
    var back = el("button", "app-btn primary", "← Return to Review");
    back.type = "button";
    back.addEventListener("click", function () { if (onBack) onBack(); });
    wrap.appendChild(back);
    return wrap;
  }

  /**
   * @param {HTMLElement} container
   * @param {object} opts { formNumber, officialName, snapshot, summary, onBack, onContinueExport }
   */
  function render(container, opts) {
    opts = opts || {};
    container.innerHTML = "";
    var snapshot = opts.snapshot || [];

    if (!snapshot.length) {
      container.appendChild(renderEmpty(opts.onBack));
      return;
    }

    var root = el("div", "cmp");
    root.appendChild(renderHeader(opts));
    root.appendChild(renderGrid(snapshot));
    container.appendChild(root);
  }

  ns.comparisonView = { render: render };
})(window.PatentFormsApp);
