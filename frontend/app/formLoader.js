/*
 * Dynamic form-definition loader. The single place in the application that
 * knows where .definition.json files live on disk.
 *
 * loadDefinition(formId) -> Promise<definition>
 *
 * On a missing/failed definition, the promise rejects with a descriptive
 * Error rather than the caller inventing placeholder content — mainArea.js
 * turns that rejection into an honest "not yet available" state.
 *
 * Path resolution: definition URLs are resolved RELATIVE to this page
 * (frontend/app/ → ../../docs/…), never root-absolute. A leading "/" is
 * resolved against the origin, which is the server root over http:// but the
 * filesystem/drive root under file:// — so "/docs/…" silently pointed outside
 * the project. Resolving against document.baseURI keeps the same target when
 * the repository root is served over HTTP and makes the URL correct when the
 * page is opened directly from disk.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var cache = {}; // formId -> Promise<definition> (successful loads only)

  // Relative to frontend/app/index.html; ../../ is the repository root.
  var DEFINITIONS_DIR = "../../docs/specifications/definitions/";

  function loadDefinition(formId) {
    if (cache[formId]) return cache[formId];

    var path = new URL(DEFINITIONS_DIR + formId + ".definition.json", document.baseURI).href;
    var promise = fetch(path)
      .then(function (res) {
        if (!res.ok) {
          throw new Error("No definition available for \"" + formId + "\" (HTTP " + res.status + " at " + path + ").");
        }
        return res.json();
      })
      .catch(function (err) {
        delete cache[formId]; // don't cache failures — allow retry once a definition is authored
        throw err;
      });

    cache[formId] = promise;
    return promise;
  }

  ns.formLoader = { loadDefinition: loadDefinition };
})(window.PatentFormsApp);
