/*
 * Top-level application wiring. Connects the three panels without any of them
 * knowing about each other:
 *
 *   Document Workspace (upload)  ──onChange──▶  refresh the Patent Workspace
 *   Patent Workspace (main area) ◀── the home screen; shows the consolidated
 *                                     view the backend assembles from uploads
 *   Forms list (sidebar)         ──onSelect──▶  open a pre-filled form
 *                                ──onHome────▶  back to the Patent Workspace
 *
 * The journey is document-first: the app opens on the Patent Workspace (empty
 * until documents are uploaded), never on a blank form. Preparing a specific
 * form is a deliberate step taken AFTER reviewing the consolidated matter — the
 * milestone ends here, at the workspace; form generation is the next one.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  function boot() {
    var documentsEl = document.getElementById("documents-panel");
    var formsEl = document.getElementById("forms-panel");
    var mainEl = document.getElementById("main");

    var mainArea = ns.mainArea.mount(mainEl);

    // One workspace for now (single patent matter). Taken from documentStore so
    // upload and retrieval cannot disagree about its name.
    var workspaceId = ns.documentStore.DEFAULT_WORKSPACE;

    function focusForms() {
      var search = formsEl.querySelector(".sidebar-search-input");
      if (search) search.focus();
    }

    // Fetch the consolidated summary and render the Patent Workspace. Always
    // safe to call — the view's own empty state covers "no documents yet".
    function refreshWorkspace() {
      ns.extractionClient.getWorkspace(workspaceId).then(function (summary) {
        mainArea.showWorkspace(summary, {
          workspaceId: workspaceId,
          onChooseForm: focusForms,
        });
      });
    }

    ns.documentWorkspace.mount(documentsEl, {
      // Fires when documents are added/removed AND when an extraction result
      // lands — either way the consolidated view may have changed.
      onChange: refreshWorkspace,
    });

    ns.sidebar.mount(formsEl, ns.formCatalog.FORMS, {
      onHome: refreshWorkspace,
      onSelect: function (formId) {
        var meta = ns.formCatalog.FORMS.filter(function (f) { return f.formId === formId; })[0];
        mainArea.showLoading(meta);

        // Suggestions are scoped to this workspace: only its documents contribute.
        // The user's Workspace decisions (resolved conflicts, typed-in values)
        // travel with the request so the form pre-fills with what they reviewed,
        // not just the raw extractions.
        var decisions = ns.workspaceOverrides.merged(workspaceId);
        Promise.all([
          ns.formLoader.loadDefinition(formId),
          ns.extractionClient.getSuggestions(formId, workspaceId, decisions),
        ]).then(function (results) {
          var definition = results[0];
          var suggestionResult = results[1];
          var suggestions = suggestionResult.suggestions || {};
          ns.suggestionStore.setSuggestions(formId, suggestions, workspaceId);
          mainArea.showForm(definition, formId, suggestions);
        }).catch(function (error) {
          mainArea.showUnavailable(meta, error);
        });
      }
    });

    // Open on the Patent Workspace, not a blank form.
    refreshWorkspace();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})(window.PatentFormsApp);
