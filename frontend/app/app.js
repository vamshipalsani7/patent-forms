/*
 * Top-level application wiring. Deliberately thin: it does not render
 * anything itself and does not touch the renderer, storage, or the DOM
 * beyond grabbing the shell containers. It only connects:
 *   - sidebar selection -> formLoader.loadDefinition -> mainArea state
 *   - the Document Workspace, mounted independently alongside the sidebar
 *
 * The Document Workspace and the forms sidebar/renderer do not call each
 * other directly — this file is the only place both are known at once, and
 * even here they are not wired together yet (Sprint 1 keeps them
 * independent, per the requirement). documentWorkspace's onChange callback
 * is intentionally left as a no-op seam for future coordination (e.g. an
 * Extraction Engine) rather than reaching into mainArea today.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  function boot() {
    var documentsEl = document.getElementById("documents-panel");
    var formsEl = document.getElementById("forms-panel");
    var mainEl = document.getElementById("main");

    var mainArea = ns.mainArea.mount(mainEl);
    mainArea.showWelcome();

    ns.documentWorkspace.mount(documentsEl, {
      onChange: function () {
        // Reserved for future coordination (see README.md "Adding a future
        // feature" — this is where an Extraction Engine would be notified
        // that a new document was added). No-op in Sprint 1.
      }
    });

    ns.sidebar.mount(formsEl, ns.formCatalog.FORMS, {
      onSelect: function (formId) {
        var meta = ns.formCatalog.FORMS.filter(function (f) { return f.formId === formId; })[0];
        mainArea.showLoading(meta);

        // Fetch definition and suggestions in parallel.
        // getSuggestions always resolves (graceful on backend-offline).
        // loadDefinition may reject (form definition file not found).
        Promise.all([
          ns.formLoader.loadDefinition(formId),
          ns.extractionClient.getSuggestions(formId),
        ]).then(function (results) {
          var definition = results[0];
          var suggestionResult = results[1];
          var suggestions = suggestionResult.suggestions || {};
          ns.suggestionStore.setSuggestions(formId, suggestions);
          mainArea.showForm(definition, formId, suggestions);
        }).catch(function (error) {
          mainArea.showUnavailable(meta, error);
        });
      }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})(window.PatentFormsApp);
