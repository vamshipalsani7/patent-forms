/*
 * Review layer — turns the rendered form into an AI review experience.
 *
 * It does NOT render form fields (the existing renderer does that). It decorates
 * the fields the renderer drew: for each field the AI filled in, it shows the
 * value in a read-mode review card with its provenance ("From Complete
 * Specification · Page 2 · High Confidence"), an Edit affordance that reveals
 * the renderer's OWN input — so no field type is re-implemented — a source
 * panel, and the edited/entered/selected/missing states. It computes the live
 * review summary and reports it to the host.
 *
 * The renderer rebuilds its DOM on every re-render, so decoration is fully
 * idempotent: clear() removes prior cards and un-hides controls, then decorate()
 * re-applies from scratch. The host re-runs it after every render (via the
 * renderer's onGapsChange seam) and after every edit.
 *
 * All presentation decisions come from reviewModel — this file is DOM plumbing.
 * It never renders a vocabulary key, a sourceType, a mapper path, a percentage,
 * or any JSON.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var model = ns.reviewModel;

  // ------------------------------------------------------------ DOM traversal
  // Walks work on both the real DOM and the test harness's element shim, so the
  // logic here is exercised the same way in Node and in the browser.
  function walkEls(node, fn) {
    if (!node) return;
    fn(node);
    var kids = node.children;
    if (!kids) return;
    for (var i = 0; i < kids.length; i++) walkEls(kids[i], fn);
  }

  function byClass(root, cls) {
    var found = null;
    walkEls(root, function (n) {
      if (!found && n.classList && n.classList.contains(cls)) found = n;
    });
    return found;
  }

  function findControl(node) {
    var ctrl = null;
    walkEls(node, function (n) {
      if (ctrl) return;
      var t = n.tagName;
      if (t === "INPUT" || t === "TEXTAREA" || t === "SELECT") ctrl = n;
    });
    return ctrl;
  }

  function containsTag(node, tag) {
    var found = false;
    walkEls(node, function (n) { if (n.tagName === tag) found = true; });
    return found;
  }

  function isRequiredNode(node) {
    var req = false;
    walkEls(node, function (n) {
      if (req) return;
      if (n.classList && n.classList.contains("req")) req = true;
      else if (n.classList && n.classList.contains("cap") &&
               /\*\s*$/.test(n.textContent || "")) req = true;
    });
    return req;
  }

  function hasDescendantDataPath(node) {
    var kids = node.children;
    if (!kids) return false;
    for (var i = 0; i < kids.length; i++) {
      var c = kids[i];
      if (c.getAttribute && c.getAttribute("data-path")) return true;
      if (hasDescendantDataPath(c)) return true;
    }
    return false;
  }

  // Leaf field nodes: carry a data-path and contain no nested data-path (so
  // section/group containers are skipped and only value fields are decorated).
  function eachLeafField(root, fn) {
    walkEls(root, function (n) {
      if (!n.getAttribute) return;
      var p = n.getAttribute("data-path");
      if (p && !hasDescendantDataPath(n)) fn(n, p);
    });
  }

  // ---------------------------------------------------------------- write-back
  // Push a value into the renderer's own control so its state updates — used by
  // Cancel and Revert. Dual-path so it works with a real Event or the shim.
  function writeBack(control, value) {
    if (!control) return;
    control.value = value == null ? "" : value;
    if (typeof control.dispatchEvent === "function" &&
        typeof window !== "undefined" && typeof window.Event === "function") {
      control.dispatchEvent(new window.Event("input", { bubbles: true }));
    } else if (typeof control.dispatch === "function") {
      control.dispatch("input"); // harness shim
    }
  }

  function hide(control) {
    if (!control) return;
    control.style.display = "none";
    control.setAttribute("data-rev-hidden", "1");
  }
  function show(control) {
    if (!control) return;
    control.style.display = "";
    control.setAttribute("data-rev-hidden", "0");
  }

  // ---------------------------------------------- label + section (for snapshot)
  function ancestorByClass(node, cls) {
    var n = node.parentNode;
    while (n) { if (n.classList && n.classList.contains(cls)) return n; n = n.parentNode; }
    return null;
  }

  // The field's human label as the renderer drew it — the "official layout"
  // text the comparison screen shows. Strips the required-marker asterisk.
  function fieldLabel(node) {
    var lab = byClass(node, "field-label");
    var text = lab ? lab.textContent : "";
    if (!text) { var cap = byClass(node, "cap"); text = cap ? cap.textContent : ""; }
    return String(text || "").replace(/\s*\*\s*$/, "").trim();
  }

  // The title of the renderer section this field sits in, so the comparison can
  // group fields the way the official form does.
  function sectionTitle(node) {
    var row = ancestorByClass(node, "section-row");
    if (!row) return "";
    var titleEl = byClass(row, "section-title");
    if (!titleEl) return "";
    var full = (titleEl.textContent || "").trim();
    var desc = byClass(titleEl, "section-desc");
    if (desc) full = full.slice(0, full.length - (desc.textContent || "").length).trim();
    return full;
  }

  // ------------------------------------------------------------------- attach
  function attach(container, opts) {
    opts = opts || {};
    var suggestions = opts.suggestions || {};
    var getValues = opts.getValues || function () { return {}; };
    var resolvedKeys = opts.resolvedKeys || {};
    var reviewedPaths = opts.reviewedPaths || {};
    var exemptPaths = opts.exemptPaths || {};
    var onReviewedChange = opts.onReviewedChange || function () {};
    var onSummary = opts.onSummary || function () {};

    // A repeatable group's child is at "sec.grp.0.child" in the DOM but keyed by
    // its definition path "sec.grp.child" in exemptPaths — strip instance indices.
    function exemptReason(path) {
      return exemptPaths[path.replace(/\.\d+(?=\.|$)/g, "")] || null;
    }
    function isExempt(path) { return !!exemptReason(path); }

    // The last computed field-by-field view, for the Comparison screen to read.
    var lastSnapshot = [];

    function root() { return byClass(container, "app") || container; }

    function clear(r) {
      var cards = [];
      walkEls(r, function (n) {
        if (n.classList && n.classList.contains("rev-card")) cards.push(n);
      });
      cards.forEach(function (c) { if (c.parentNode) c.parentNode.removeChild(c); });
      walkEls(r, function (n) {
        if (n.getAttribute && n.getAttribute("data-rev-hidden") === "1") show(n);
      });
    }

    function fieldStateFor(node, path, values) {
      return model.fieldState({
        suggestion: suggestions[path] || null,
        currentValue: values[path],
        resolvedKeys: resolvedKeys,
        required: isRequiredNode(node),
        reviewed: !!reviewedPaths[path],
        exempt: isExempt(path),
      });
    }

    function decorate() {
      var r = root();
      clear(r);
      var values = getValues();
      var states = [];
      lastSnapshot = [];

      eachLeafField(r, function (node, path) {
        var suggestion = suggestions[path] || null;
        var control = findControl(node);
        var state = fieldStateFor(node, path, values);
        states.push(state);

        // Capture the field for the Comparison screen BEFORE decorating (so the
        // label reads the renderer's own label, not an injected card).
        lastSnapshot.push({
          path: path,
          label: fieldLabel(node) || path.split(".").pop(),
          section: sectionTitle(node),
          status: state.status,
          value: state.current,
          original: state.original,
          sourceLabel: state.sourceLabel,
          page: state.page,
          confidenceWord: state.confidenceWord,
          exemptReason: exemptReason(path),
        });

        if (suggestion) {
          decorateAutofilled(node, path, control, suggestion, state);
        } else if (state.status === "missing") {
          decorateMissing(node);
        }
      });

      onSummary(model.summarize(states));
    }

    // Recompute the summary as the user types. Deliberately does NOT re-decorate
    // (that would tear down the field being edited), but it does keep the
    // "Missing" flag honest: a field the user has just completed must stop
    // saying Missing immediately, and one they have emptied must start saying it.
    // Anything else shows a typed value labelled "Missing", which is exactly the
    // kind of contradiction that costs a reviewer their trust.
    function recount() {
      var r = root();
      var values = getValues();
      var states = [];
      eachLeafField(r, function (node, path) {
        var state = fieldStateFor(node, path, values);
        states.push(state);
        if (!suggestions[path]) syncMissingCard(node, state);
      });
      onSummary(model.summarize(states));
    }

    function syncMissingCard(node, state) {
      var card = byClass(node, "rev-missing");
      if (state.status === "missing" && !card) {
        decorateMissing(node);
      } else if (state.status !== "missing" && card && card.parentNode) {
        card.parentNode.removeChild(card);
      }
    }

    // ---- autofilled field: read-mode card revealing the renderer's control ----
    function decorateAutofilled(node, path, control, suggestion, state) {
      var simple = control && !Array.isArray(suggestion.value) && !containsTag(node, "TABLE");

      var card = el("div", "rev-card rev-" + state.status);

      // The value the AI put in (read mode).
      if (simple) {
        card.appendChild(el("div", "rev-value", state.current || "—"));
      }

      // Provenance line. The label is a child span (not the button's own text)
      // so an appended caret never masks it.
      var chip = el("button", "rev-chip rev-chip-" + state.status);
      chip.type = "button";
      chip.appendChild(el("span", "rev-chip-text", provenanceLabel(state)));
      var panel = null;
      if (state.status === "from_document") {
        chip.appendChild(el("span", "rev-chip-caret", " ⌄"));
        chip.addEventListener("click", function () {
          if (!panel) { panel = buildSourcePanel(suggestion, state); card.appendChild(panel); }
          else { card.removeChild(panel); panel = null; }
        });
      }

      var chipRow = el("div", "rev-chip-row");
      chipRow.appendChild(chip);

      // Edited: original recoverable + revert.
      if (state.status === "edited_by_you") {
        var revert = el("button", "rev-linkbtn", "Revert to original");
        revert.type = "button";
        revert.addEventListener("click", function () {
          writeBack(control, suggestion.value);
          decorate();
        });
        chipRow.appendChild(revert);
        card.appendChild(el("div", "rev-original", "Originally: " + (state.original || "—")));
      }

      // Mark-reviewed toggle (only meaningful for an unedited AI value).
      if (state.hasSuggestion && !state.edited && state.filled) {
        var mark = el("button", "rev-review-toggle" + (state.reviewed ? " on" : ""),
          state.reviewed ? "✓ Reviewed" : "Mark reviewed");
        mark.type = "button";
        mark.addEventListener("click", function () {
          if (reviewedPaths[path]) delete reviewedPaths[path];
          else reviewedPaths[path] = true;
          onReviewedChange();
          decorate();
        });
        chipRow.appendChild(mark);
      }

      // Edit affordance (simple fields reveal the renderer's own input).
      if (simple) {
        var edit = el("button", "rev-edit", "Edit");
        edit.type = "button";
        edit.addEventListener("click", function () { enterEdit(node, control, card, suggestion); });
        chipRow.appendChild(edit);
        hide(control);
      }

      card.appendChild(chipRow);
      node.appendChild(card);
    }

    function enterEdit(node, control, card, suggestion) {
      var before = control.value;
      card.style.display = "none";
      show(control);
      if (control.focus) control.focus();

      var bar = el("div", "rev-edit-bar");
      var save = el("button", "app-btn primary", "Save"); save.type = "button";
      var cancel = el("button", "app-btn ghost", "Cancel"); cancel.type = "button";
      save.addEventListener("click", function () { decorate(); });
      cancel.addEventListener("click", function () { writeBack(control, before); decorate(); });
      if (control.addEventListener) {
        control.addEventListener("keydown", function (e) {
          if (e.key === "Enter") { if (e.preventDefault) e.preventDefault(); decorate(); }
          else if (e.key === "Escape") { writeBack(control, before); decorate(); }
        });
      }
      bar.appendChild(save); bar.appendChild(cancel);
      node.appendChild(bar);
    }

    function decorateMissing(node) {
      var card = el("div", "rev-card rev-missing");
      card.appendChild(el("div", "rev-missing-label", "Missing"));
      card.appendChild(el("div", "rev-missing-note", "Required for this form"));
      node.appendChild(card);
    }

    function provenanceLabel(state) {
      var t = state.provenanceText;
      if (state.status === "from_document") {
        var extra = [];
        if (state.page != null) extra.push("Page " + state.page);
        if (state.confidenceWord) extra.push(state.confidenceWord);
        if (extra.length) t += " · " + extra.join(" · ");
      }
      return t;
    }

    function buildSourcePanel(suggestion, state) {
      var panel = el("div", "rev-source-panel");
      panel.appendChild(el("div", "rev-source-head", "Source"));
      panel.appendChild(el("div", "rev-source-name", state.sourceLabel || "Document"));
      if (state.page != null) panel.appendChild(el("div", "rev-source-page", "Page " + state.page));
      panel.appendChild(el("div", "rev-source-head", "Extracted text"));
      panel.appendChild(el("div", "rev-source-text", model.displayValue(suggestion.value) || "—"));
      return panel;
    }

    return {
      refresh: decorate,
      decorate: decorate,
      recount: recount,
      // A copy of the field-by-field view for the Comparison screen. decorate()
      // must have run at least once (it always does on attach).
      snapshot: function () { return lastSnapshot.slice(); },
    };
  }

  ns.reviewLayer = { attach: attach };
})(window.PatentFormsApp);
