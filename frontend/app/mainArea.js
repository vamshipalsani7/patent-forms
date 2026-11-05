/*
 * Main area: welcome screen, loading/unavailable states, and the mounted
 * form editor (toolbar + renderer + Save Draft / Start Fresh).
 *
 * This is the ONLY module that calls window.FormRenderer.mount()/unmount().
 * It owns the bridge between application state (formState.js) and the
 * renderer's (definition, values, callbacks) contract — the renderer itself
 * never touches localStorage or knows a formId exists.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;
  var formState = ns.formState;

  /** Build a flat { path: value } map from the suggestions object. */
  function flattenSuggestions(suggestions) {
    var out = {};
    Object.keys(suggestions || {}).forEach(function (path) {
      out[path] = suggestions[path].value;
    });
    return out;
  }

  /** Return the source description string from a fact object. */
  function provenanceLabel(fact) {
    if (!fact) return "";
    // A value the user decided themselves in the Patent Workspace — not an
    // extraction — is shown as their own, not as a document with a confidence.
    if (fact.source_type === "user" || fact.method === "manual") {
      return "Entered by you";
    }
    var parts = [];
    if (fact.source_type) parts.push(fact.source_type);
    if (fact.page != null) parts.push("p." + fact.page);
    if (fact.method) parts.push(fact.method);
    var pct = fact.confidence != null ? Math.round(fact.confidence * 100) : null;
    if (pct != null) parts.push(pct + "% conf.");
    return parts.join(" · ");
  }

  /**
   * Paths the user should see listed as auto-filled.
   *
   * Structural suggestions (a repeatable group's `path#count`) travel on the
   * same channel because that is how state reaches the renderer, but they are
   * renderer bookkeeping rather than an extracted value. Listing them would
   * show the user a "field" called `inventors.inventor#count` with a value of
   * 2 and inflate the auto-filled count.
   */
  function userVisiblePaths(suggestions) {
    return Object.keys(suggestions || {}).filter(function (path) {
      return !suggestions[path].structural;
    });
  }

  /** Build a collapsible provenance banner for auto-filled fields. */
  function buildProvenanceBanner(suggestions) {
    var paths = userVisiblePaths(suggestions);
    if (!paths.length) return null;

    var banner = el("div", "provenance-banner");

    var summary = el("div", "provenance-summary");
    var count = el("span", "provenance-count", paths.length + " field" + (paths.length !== 1 ? "s" : "") + " auto-filled");
    var toggle = el("button", "provenance-toggle app-btn ghost", "Show sources");
    toggle.type = "button";
    summary.appendChild(count);
    summary.appendChild(toggle);
    banner.appendChild(summary);

    var detail = el("div", "provenance-detail");
    detail.style.display = "none";
    paths.forEach(function (path) {
      var s = suggestions[path];
      var row = el("div", "provenance-row");
      var field = el("span", "provenance-field", path);
      var val = el("span", "provenance-val", String(s.value || ""));
      var src = el("span", "provenance-src", provenanceLabel(s.fact));
      row.appendChild(field);
      row.appendChild(val);
      row.appendChild(src);
      detail.appendChild(row);
    });
    banner.appendChild(detail);

    toggle.addEventListener("click", function () {
      var open = detail.style.display !== "none";
      detail.style.display = open ? "none" : "block";
      toggle.textContent = open ? "Show sources" : "Hide sources";
    });

    return banner;
  }

  function formatTime(iso) {
    try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
  }

  /**
   * Value-equality for suggestion-vs-current diffing. Array/table field
   * values are plain-cloned by the renderer's snapshot() on every onChange,
   * so a strict `!==` would flag them as user-edited on the very first
   * render even with zero edits. Structural comparison avoids that.
   */
  function valuesEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== "object" || typeof b !== "object" || a == null || b == null) return false;
    return JSON.stringify(a) === JSON.stringify(b);
  }

  /**
   * @param {HTMLElement} container
   * @param {object} [opts] { onPrepareAnother } — host actions the main area
   *        offers but does not own (returning to the form list, for instance).
   */
  function mountMainArea(container, opts) {
    opts = opts || {};
    var root = el("div", "main-area");
    container.appendChild(root);

    var rendererController = null; // handle from the currently mounted FormRenderer instance

    function clear() {
      if (rendererController) { rendererController.unmount(); rendererController = null; }
      root.innerHTML = "";
    }

    function showWelcome() {
      clear();
      var wrap = el("div", "welcome");
      wrap.appendChild(el("h1", null, "Patent Forms"));
      wrap.appendChild(el("p", "welcome-sub", "From patent documents to a filing-ready IPO form."));
      wrap.appendChild(el("p", "welcome-hint", "Upload your patent documents on the left to begin."));
      root.appendChild(wrap);
    }

    /**
     * Render the Patent Workspace — the consolidated view of the matter. This
     * is the application's home screen once any document exists; its own empty
     * state covers the no-documents case, so app.js can always call it.
     *
     * @param {object} summary  the /api/workspace response
     * @param {object} [opts]    { workspaceId, onChooseForm }
     */
    function showWorkspace(summary, opts) {
      clear();
      ns.workspaceView.render(root, summary, opts);
    }

    function showLoading(meta) {
      clear();
      var wrap = el("div", "state-panel");
      wrap.appendChild(el("div", "state-title", "Form " + meta.formNumber + " — " + meta.officialName));
      wrap.appendChild(el("div", "state-body", "Loading form definition…"));
      root.appendChild(wrap);
    }

    function showUnavailable(meta, error) {
      clear();
      var wrap = el("div", "state-panel state-unavailable");
      wrap.appendChild(el("div", "state-title", "Form " + meta.formNumber + " — " + meta.officialName));
      wrap.appendChild(el("div", "state-body",
        "This form could not be opened. Its definition may be missing or failed to load. " +
        "You can go back to the Patent Workspace and try another form."));
      wrap.appendChild(el("div", "state-detail", error && error.message ? error.message : String(error)));
      root.appendChild(wrap);
    }

    /**
     * The AI Form Review experience: the generated form, presented as something
     * to verify rather than fill. A live summary sits above it, and every
     * autofilled field is decorated (by reviewLayer, over the renderer) with
     * where its value came from.
     *
     * @param {object} definition   parsed form definition JSON
     * @param {string} formId       e.g. 'form_03'
     * @param {object} [suggestions] { fieldPath: {value, fact, source_label} } from backend
     * @param {string} [workspaceId] the patent matter (for conflict-resolution provenance)
     */
    function showForm(definition, formId, suggestions, workspaceId) {
      clear();
      suggestions = suggestions || {};

      var suggestedValues = flattenSuggestions(suggestions);

      // --- draft (persisted user edits + reviewed marks) ---
      var draft = formState.loadDraft(formId);
      var draftValues = draft ? (draft.values || {}) : {};
      var savedUserEditedPaths = draft ? (draft.userEditedPaths || []) : [];

      var currentUserEditedPaths = {};
      savedUserEditedPaths.forEach(function (p) { currentUserEditedPaths[p] = true; });

      var reviewedPaths = {};
      (draft && draft.reviewedPaths ? draft.reviewedPaths : []).forEach(function (p) { reviewedPaths[p] = true; });

      // Base: suggestion values; override with draft values only where the user edited.
      var initialValues = Object.assign({}, suggestedValues);
      savedUserEditedPaths.forEach(function (p) {
        if (draftValues[p] !== undefined) initialValues[p] = draftValues[p];
      });

      // Which vocabulary keys the user resolved as conflicts — so a value chosen
      // during review reads "Selected during review", not as a plain extraction.
      var resolvedKeys = {};
      if (workspaceId && ns.workspaceOverrides) {
        var resolved = (ns.workspaceOverrides.load(workspaceId) || {}).resolved || {};
        Object.keys(resolved).forEach(function (k) { resolvedKeys[k] = true; });
      }

      // ------------------------------------------------------- review summary
      var header = el("div", "review-header");
      var titleWrap = el("div", "review-title");
      titleWrap.appendChild(el("div", "review-form-number", "Form " + definition.formNumber));
      titleWrap.appendChild(el("div", "review-form-name", definition.officialName));
      titleWrap.appendChild(el("div", "review-tagline", "Automatically completed — review each value below."));
      header.appendChild(titleWrap);

      var statRow = el("div", "review-stats");
      var stAuto = reviewStat("Auto-filled");
      var stReviewed = reviewStat("Reviewed");
      var stEdited = reviewStat("Edited by you");
      var stMissing = reviewStat("Missing", "warn");
      statRow.appendChild(stAuto.node);
      statRow.appendChild(stReviewed.node);
      statRow.appendChild(stEdited.node);
      statRow.appendChild(stMissing.node);
      header.appendChild(statRow);

      var actions = el("div", "review-actions");
      var status = el("span", "draft-status");
      var freshWrap = el("span", "review-fresh");
      var freshBtn = el("button", "app-btn ghost", "Start over");
      freshBtn.type = "button";
      var saveBtn = el("button", "app-btn ghost", "Save Draft");
      saveBtn.type = "button";
      var compareBtn = el("button", "app-btn primary", "Continue to comparison →");
      compareBtn.type = "button";
      actions.appendChild(status);
      freshWrap.appendChild(freshBtn);
      actions.appendChild(freshWrap);
      actions.appendChild(saveBtn);
      actions.appendChild(compareBtn);
      header.appendChild(actions);
      root.appendChild(header);

      // Completion banner (shown when every required field is filled).
      var completion = el("div", "review-completion");
      completion.style.display = "none";
      root.appendChild(completion);

      // --- renderer (review mode hides the renderer's developer completeness panel) ---
      var mountPoint = el("div", "renderer-mount review-mode");
      root.appendChild(mountPoint);

      var reviewCtl = null;

      function persistReviewed() {
        // Reviewed marks live with the draft so they survive a reload.
        formState.saveDraft(
          formId, rendererController.getValues(),
          Object.keys(currentUserEditedPaths), Object.keys(reviewedPaths)
        );
      }

      var latestSummary = {};
      function applySummary(summary) {
        latestSummary = summary;
        stAuto.set(summary.autoFilled);
        stReviewed.set(summary.reviewed);
        stEdited.set(summary.edited);
        stMissing.set(summary.missing);
        renderCompletion(summary);
      }

      // Save the draft, then hand the current field-by-field snapshot to the
      // Official IPO Comparison screen. Reachable whether or not the form is
      // complete — the comparison itself surfaces any remaining missing fields.
      function goToComparison() {
        persistReviewed();
        reviewCtl.refresh(); // ensure the snapshot + summary are current
        // Capture the renderer's values BEFORE leaving: the renderer is
        // unmounted when the view changes, and the filing package is built from
        // exactly these values.
        showComparison(definition, formId, suggestions, workspaceId,
          reviewCtl.snapshot(), latestSummary, rendererController.getValues());
      }
      compareBtn.addEventListener("click", goToComparison);

      function renderCompletion(summary) {
        completion.innerHTML = "";
        // Show "ready" when every substantive field is complete and the form has
        // real content — whether the AI filled it or the user did. (`tracked`
        // guards against celebrating a form with nothing substantive to do.)
        if (summary.complete && summary.tracked > 0) {
          completion.style.display = "";
          completion.appendChild(el("div", "review-completion-title", "Everything looks good."));
          completion.appendChild(el("div", "review-completion-body",
            "This form is ready for comparison with the official IPO layout."));
          var cont = el("button", "app-btn primary", "Continue to comparison →");
          cont.type = "button";
          cont.addEventListener("click", goToComparison);
          completion.appendChild(cont);
        } else {
          completion.style.display = "none";
        }
      }

      rendererController = window.FormRenderer.mount(mountPoint, definition, initialValues, {
        onChange: function (values) {
          status.textContent = "Unsaved changes";
          status.classList.add("dirty");
          Object.keys(values).forEach(function (path) {
            if (path in suggestedValues) {
              if (!valuesEqual(values[path], suggestedValues[path])) currentUserEditedPaths[path] = true;
              else delete currentUserEditedPaths[path];
            }
          });
          // Recount without re-decorating, so a field being edited is undisturbed.
          if (reviewCtl && reviewCtl.recount) reviewCtl.recount();
        },
        onGapsChange: function () {
          // The renderer rebuilt its DOM (e.g. a row was added or a choice
          // flipped visibility) — re-apply the review decoration over it.
          if (reviewCtl) reviewCtl.refresh();
        },
      });

      // Fields handled at filing (signatures, office-use, IPO-generated values,
      // signing dates) must not count as "missing" or the review can never read
      // as complete. Computed once from the definition.
      var exemptPaths = ns.reviewModel.exemptPaths(definition);

      // Attach the review overlay over the freshly rendered form.
      reviewCtl = ns.reviewLayer.attach(mountPoint, {
        suggestions: suggestions,
        getValues: function () { return rendererController.getValues(); },
        resolvedKeys: resolvedKeys,
        reviewedPaths: reviewedPaths,
        exemptPaths: exemptPaths,
        onReviewedChange: persistReviewed,
        onSummary: applySummary,
      });
      reviewCtl.refresh();

      saveBtn.addEventListener("click", function () {
        var record = formState.saveDraft(
          formId, rendererController.getValues(),
          Object.keys(currentUserEditedPaths), Object.keys(reviewedPaths)
        );
        status.textContent = "Draft saved · " + formatTime(record.savedAt);
        status.classList.remove("dirty");
      });

      // "Start over" is a two-step inline confirm — no browser dialog.
      function buildFreshButton() {
        freshWrap.innerHTML = "";
        var btn = el("button", "app-btn ghost", "Start over");
        btn.type = "button";
        btn.addEventListener("click", openFreshConfirm);
        freshWrap.appendChild(btn);
      }
      function openFreshConfirm() {
        freshWrap.innerHTML = "";
        freshWrap.appendChild(el("span", "review-fresh-q", "Discard your changes?"));
        var yes = el("button", "app-btn ghost danger", "Discard"); yes.type = "button";
        var no = el("button", "app-btn ghost", "Keep"); no.type = "button";
        yes.addEventListener("click", function () {
          formState.clearDraft(formId);
          currentUserEditedPaths = {};
          Object.keys(reviewedPaths).forEach(function (k) { delete reviewedPaths[k]; });
          rendererController.setValues(suggestedValues); // triggers onGapsChange → refresh
          status.textContent = "Reset to the auto-filled values";
          status.classList.remove("dirty");
          buildFreshButton();
        });
        no.addEventListener("click", buildFreshButton);
        freshWrap.appendChild(yes);
        freshWrap.appendChild(no);
      }
      freshBtn.addEventListener("click", openFreshConfirm);

      if (draft) {
        status.textContent = "Restored draft · saved " + formatTime(draft.savedAt);
      } else {
        status.textContent = "";
      }
    }

    function reviewStat(label, cls) {
      var node = el("div", "review-stat" + (cls ? " review-stat-" + cls : ""));
      var num = el("span", "review-stat-n", "0");
      node.appendChild(num);
      node.appendChild(el("span", "review-stat-l", " " + label));
      return {
        node: node,
        set: function (n) {
          num.textContent = String(n);
          if (cls === "warn") node.style.opacity = n > 0 ? "1" : "0.45";
        },
      };
    }

    /**
     * The Official IPO Comparison screen. Read-only; correcting anything means
     * "← Back to Review". Driven entirely by the review layer's snapshot, so it
     * reuses the review model, the renderer's labels, and the definition without
     * a second rendering engine or a duplicated definition.
     */
    function showComparison(definition, formId, suggestions, workspaceId, snapshot, summary, values) {
      clear();
      ns.comparisonView.render(root, {
        formNumber: definition.formNumber,
        officialName: definition.officialName,
        snapshot: snapshot,
        summary: summary,
        onBack: function () {
          showForm(definition, formId, suggestions, workspaceId);
        },
        onContinueExport: function () {
          showFilingPackage(definition, formId, suggestions, workspaceId,
            snapshot, summary, values);
        },
      });
    }

    /**
     * The Filing Package screen: the prepared documents, ready to download.
     *
     * The package is built by the backend from the values captured in review,
     * so the filed PDF contains exactly the form the user reviewed and compared.
     */
    function showFilingPackage(definition, formId, suggestions, workspaceId, snapshot, summary, values) {
      clear();
      var payload = {
        workspace_id: workspaceId || "default",
        values: values || {},
        // The fields the renderer actually drew — conditional fields the user
        // never saw must not appear on the filed document.
        visible_paths: (snapshot || []).map(function (f) { return f.path; }),
        counts: summary || {},
        overrides: (ns.workspaceOverrides && workspaceId)
          ? ns.workspaceOverrides.merged(workspaceId) : {},
      };

      ns.downloadView.render(root, {
        formNumber: definition.formNumber,
        onDownload: function (part, done) {
          ns.packageClient.download(formId, part, payload).then(done);
        },
        onBack: function () {
          showComparison(definition, formId, suggestions, workspaceId,
            snapshot, summary, values);
        },
        onAnother: opts.onPrepareAnother || null,
      });
    }

    return {
      showWelcome: showWelcome,
      showWorkspace: showWorkspace,
      showLoading: showLoading,
      showUnavailable: showUnavailable,
      showForm: showForm,
      showComparison: showComparison
    };
  }

  ns.mainArea = { mount: mountMainArea };
})(window.PatentFormsApp);
