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

  function mountMainArea(container) {
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
     * @param {object} definition   parsed form definition JSON
     * @param {string} formId       e.g. 'form_03'
     * @param {object} [suggestions] { fieldPath: { value, fact } } from backend; may be omitted
     */
    function showForm(definition, formId, suggestions) {
      clear();
      suggestions = suggestions || {};

      // --- suggestion values (flat path→value) ---
      var suggestedValues = flattenSuggestions(suggestions);

      // --- draft (persisted user edits) ---
      var draft = formState.loadDraft(formId);
      var draftValues = draft ? (draft.values || {}) : {};
      // Paths the user has explicitly edited (saved across sessions)
      var savedUserEditedPaths = draft ? (draft.userEditedPaths || []) : [];

      // Runtime set of user-edited paths — starts from saved set; grows as user types
      var currentUserEditedPaths = {};
      savedUserEditedPaths.forEach(function (p) { currentUserEditedPaths[p] = true; });

      // --- build initialValues ---
      // Base: suggestion values (can be refreshed next session)
      // Override: draft values only for paths the user explicitly edited
      var initialValues = Object.assign({}, suggestedValues);
      savedUserEditedPaths.forEach(function (p) {
        if (draftValues[p] !== undefined) initialValues[p] = draftValues[p];
      });

      // --- toolbar ---
      var toolbar = el("div", "form-toolbar");
      var titleWrap = el("div", "form-toolbar-title");
      titleWrap.appendChild(el("div", "form-toolbar-number", "Form " + definition.formNumber));
      titleWrap.appendChild(el("div", "form-toolbar-name", definition.officialName));
      toolbar.appendChild(titleWrap);

      var actions = el("div", "form-toolbar-actions");
      var status = el("span", "draft-status");

      var freshBtn = el("button", "app-btn ghost", "Start Fresh");
      freshBtn.type = "button";
      var saveBtn = el("button", "app-btn primary", "Save Draft");
      saveBtn.type = "button";
      actions.appendChild(status);
      actions.appendChild(freshBtn);
      actions.appendChild(saveBtn);
      toolbar.appendChild(actions);
      root.appendChild(toolbar);

      // Set initial status message
      var hasSuggestions = Object.keys(suggestedValues).length > 0;
      if (draft) {
        status.textContent = "Restored draft · saved " + formatTime(draft.savedAt);
      } else if (hasSuggestions) {
        status.textContent = Object.keys(suggestedValues).length + " field(s) auto-filled";
      } else {
        status.textContent = "No saved draft yet";
      }

      // --- provenance banner ---
      var banner = buildProvenanceBanner(suggestions);
      if (banner) root.appendChild(banner);

      // --- renderer ---
      var mountPoint = el("div", "renderer-mount");
      root.appendChild(mountPoint);

      rendererController = window.FormRenderer.mount(mountPoint, definition, initialValues, {
        onChange: function (values) {
          status.textContent = "Unsaved changes";
          status.classList.add("dirty");

          // Track which paths differ from the suggestion (= user-edited).
          // The renderer passes `values` (flat path→value snapshot) so we can
          // diff precisely without any per-field instrumentation.
          Object.keys(values).forEach(function (path) {
            if (path in suggestedValues) {
              if (!valuesEqual(values[path], suggestedValues[path])) {
                currentUserEditedPaths[path] = true;
              } else {
                // User restored the suggestion — no longer sticky
                delete currentUserEditedPaths[path];
              }
            }
          });
        }
      });

      saveBtn.addEventListener("click", function () {
        var values = rendererController.getValues();
        var editedPaths = Object.keys(currentUserEditedPaths);
        var record = formState.saveDraft(formId, values, editedPaths);
        status.textContent = "Draft saved · " + formatTime(record.savedAt);
        status.classList.remove("dirty");
      });

      freshBtn.addEventListener("click", function () {
        if (!window.confirm("Discard the saved draft for Form " + definition.formNumber + " and start fresh?")) return;
        formState.clearDraft(formId);
        // Re-apply suggestions (if any) as the blank slate
        rendererController.setValues(suggestedValues);
        // Reset tracked edits — user cleared everything
        currentUserEditedPaths = {};
        status.textContent = hasSuggestions
          ? Object.keys(suggestedValues).length + " field(s) auto-filled"
          : "No saved draft yet";
        status.classList.remove("dirty");
      });
    }

    return {
      showWelcome: showWelcome,
      showWorkspace: showWorkspace,
      showLoading: showLoading,
      showUnavailable: showUnavailable,
      showForm: showForm
    };
  }

  ns.mainArea = { mount: mountMainArea };
})(window.PatentFormsApp);
